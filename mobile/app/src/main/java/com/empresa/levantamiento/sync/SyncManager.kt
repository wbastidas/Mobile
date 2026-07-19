package com.empresa.levantamiento.sync

import com.empresa.levantamiento.core.model.Ids
import com.empresa.levantamiento.core.quality.QualityReport
import com.empresa.levantamiento.core.quality.QualityValidator
import com.empresa.levantamiento.core.quality.toDto
import com.empresa.levantamiento.core.sync.PhotoMetaDto
import com.empresa.levantamiento.core.sync.ValidationReportDto
import com.empresa.levantamiento.core.sync.SyncUploadRequest
import com.empresa.levantamiento.data.local.GeoPackageStore
import com.empresa.levantamiento.data.local.ParamsStore
import com.empresa.levantamiento.data.local.SessionStore
import com.empresa.levantamiento.data.remote.ApiService
import com.empresa.levantamiento.media.PhotoManager
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.RequestBody.Companion.toRequestBody
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.buildJsonArray
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.intOrNull
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import kotlinx.serialization.json.put

/**
 * Orquesta la sincronización bidireccional (RF-SYNC, RF-MOV-10).
 *
 * pull(): descarga incremental de trabajos, órdenes de borrado y parámetros de
 *         calidad, guardándolos en el GeoPackage local.
 * syncWork(): valida localmente, sube el paquete (idempotente) y las fotos por
 *         chunks, verifica la completitud y — solo si todo se confirma — deja el
 *         trabajo listo para eliminación local. Ante cualquier fallo, el trabajo
 *         queda pendiente y todo el proceso se reintenta (RN-04).
 */
class SyncManager(
    private val api: ApiService,
    private val store: GeoPackageStore,
    private val params: ParamsStore,
    private val session: SessionStore,
    private val photoManager: PhotoManager,
) {
    private val json = Json { ignoreUnknownKeys = true; encodeDefaults = true }

    sealed interface SyncOutcome {
        data class Verified(val workId: String, val status: String) : SyncOutcome
        data class WithIssues(val report: QualityReport) : SyncOutcome
        data class Pending(val reason: String) : SyncOutcome
    }

    /** Descarga incremental (RF-SYNC.7). Devuelve los IDs a borrar localmente. */
    suspend fun pull(): List<String> = withContext(Dispatchers.IO) {
        val deviceUid = session.deviceUid ?: return@withContext emptyList()
        val body = api.pull(deviceUid)

        // Trabajos nuevos/actualizados.
        body["new_works"]?.jsonArray?.forEach { w ->
            val o = w.jsonObject
            val id = o["id"]!!.jsonPrimitive.content
            store.upsertWork(
                id = id,
                code = o["code"]!!.jsonPrimitive.content,
                title = o["title"]!!.jsonPrimitive.content,
                type = o["work_type"]!!.jsonPrimitive.content,
                status = o["status"]!!.jsonPrimitive.content,
                schemaVersion = o["schema_version"]?.jsonPrimitive?.intOrNull ?: 1,
                sectorGeoJson = o["sector_geojson"]?.jsonPrimitive?.contentOrNull(),
                unId = session.unId ?: "",
            )
            o["elements"]?.jsonArray?.forEach { e ->
                val eo = e.jsonObject
                store.upsertElement(
                    workId = id,
                    e = com.empresa.levantamiento.core.model.ElementRecord(
                        guid = eo["element_guid"]!!.jsonPrimitive.content,
                        elementType = eo["element_type"]?.jsonPrimitive?.contentOrNull() ?: "DESCONOCIDO",
                        geometryGeoJson = eo["geometry_geojson"]?.jsonPrimitive?.contentOrNull(),
                    ),
                    observations = null,
                    completed = eo["completed"]?.jsonPrimitive?.let { it.content == "true" } ?: false,
                    dirty = false,
                )
            }
        }

        // Parámetros de calidad vigentes (para validar offline).
        body["quality_params_version"]?.jsonPrimitive?.intOrNull?.let { params.qualityVersion = it }
        body["quality_params_rules"]?.let { params.qualityRulesJson = it.toString() }
        body["schema_version"]?.jsonPrimitive?.intOrNull?.let { params.schemaVersion = it }
        body["schema_definition"]?.let { params.schemaDefinitionJson = it.toString() }

        body["remote_delete_work_ids"]?.jsonArray?.map { it.jsonPrimitive.content } ?: emptyList()
    }

    /** Valida y sincroniza un trabajo completo. */
    suspend fun syncWork(workId: String): SyncOutcome = withContext(Dispatchers.IO) {
        val deviceUid = session.deviceUid ?: return@withContext SyncOutcome.Pending("Sin dispositivo.")
        val elements = store.getElements(workId)

        // 1) Validación de calidad EN el dispositivo (RF-MOV-09, RN-09).
        val validator = QualityValidator(params.qualityRulesJson ?: "{}")
        val report = validator.validate(elements)

        store.updateWorkStatus(workId, "SYNCING")

        // 2) Construir payload de elementos.
        val payloadJson = buildJsonObject {
            put("elements", buildJsonArray {
                elements.forEach { el ->
                    add(buildJsonObject {
                        put("guid", el.guid)
                        put("element_type", el.elementType)
                        put("geometry_geojson", el.geometryGeoJson)
                        put("parent_guid", el.parentGuid)
                        put("is_new", el.isNew)
                        put("deleted", el.deleted)  // consolida como DELETE (§7)
                        put("attributes", buildJsonObject {
                            el.attributes.forEach { (k, v) -> put(k, v) }
                        })
                    })
                }
            })
        }.toString()

        // 3) Metadata de fotos pendientes.
        val pendingPhotos = store.getPhotos(workId, onlyPending = true)
        val photoMetas = pendingPhotos.map {
            PhotoMetaDto(
                elementGuid = it.elementGuid, gpsLat = it.lat, gpsLon = it.lon,
                capturedAt = it.capturedAt, sha256 = it.sha256, sizeBytes = it.size,
                totalChunks = it.totalChunks,
            )
        }

        val idempotencyKey = Ids.idempotencyKey(workId, deviceUid, params.qualityVersion.toLong())

        // 4) Subir el paquete (idempotente, RF-SYNC.5).
        val uploadResp = runCatching {
            api.upload(
                SyncUploadRequest(
                    idempotencyKey = idempotencyKey,
                    workId = workId,
                    deviceUid = deviceUid,
                    schemaVersion = params.schemaVersion,
                    payloadJson = payloadJson,
                    validationResult = report.result.name,
                    // Reporte detallado por elemento y por regla (RF-WEB-09.2).
                    validationReportJson = json.encodeToString(
                        ValidationReportDto.serializer(), report.toDto()
                    ),
                    photos = photoMetas,
                )
            )
        }.getOrElse { return@withContext pending(workId, "Fallo al subir el paquete: ${it.message}") }

        // 5) Subir las fotos por chunks, verificando integridad (RF-SYNC.3/4).
        for (photo in pendingPhotos) {
            if (photo.sha256 !in uploadResp.missingPhotos) {
                store.markPhotoUploaded(photo.id); continue
            }
            val ok = runCatching { uploadPhoto(photo) }.getOrDefault(false)
            if (!ok) return@withContext pending(workId, "Foto no confirmada: ${photo.sha256}")
            store.markPhotoUploaded(photo.id)
        }

        // 6) Verificación de completitud + consolidación (RF-MOV-10.2).
        val verifyResp = runCatching { api.verify(uploadResp.packageId) }
            .getOrElse { return@withContext pending(workId, "Fallo al verificar: ${it.message}") }

        if (!verifyResp.verified) {
            return@withContext pending(workId, verifyResp.detail)
        }
        store.updateWorkStatus(workId, verifyResp.status)
        if (report.result == com.empresa.levantamiento.core.model.ValidationResult.WITH_ISSUES) {
            SyncOutcome.WithIssues(report)
        } else {
            SyncOutcome.Verified(workId, verifyResp.status)
        }
    }

    /** Elimina el trabajo del dispositivo (solo tras sync confirmada, RN-03). */
    fun deleteLocal(workId: String) = store.deleteWork(workId)

    /** Confirma un borrado remoto y elimina localmente (RF-WEB-05.2). */
    suspend fun confirmRemoteDelete(workId: String) = withContext(Dispatchers.IO) {
        val deviceUid = session.deviceUid ?: return@withContext
        runCatching { api.confirmDelete(workId, deviceUid) }
        store.deleteWork(workId)
    }

    private suspend fun uploadPhoto(photo: GeoPackageStore.PhotoRow): Boolean {
        if (!photoManager.verifyIntegrity(photo.path, photo.sha256)) return false
        val bytes = java.io.File(photo.path).readBytes()
        val chunkSize = 512 * 1024
        val total = photo.totalChunks
        for (i in 0 until total) {
            val start = i * chunkSize
            val end = minOf(start + chunkSize, bytes.size)
            val slice = bytes.copyOfRange(start, end)
            val mediaType = "application/octet-stream".toMediaTypeOrNull()
            val part = okhttp3.MultipartBody.Part.createFormData(
                "chunk", "${photo.sha256}.part$i", slice.toRequestBody(mediaType)
            )
            runCatching { api.uploadPhotoChunk(photo.sha256, i, total, part) }
                .getOrElse { return false }
        }
        return true
    }

    private fun pending(workId: String, reason: String): SyncOutcome {
        store.updateWorkStatus(workId, "SYNC_PENDING")
        return SyncOutcome.Pending(reason)
    }
}

private fun kotlinx.serialization.json.JsonPrimitive.contentOrNull(): String? =
    if (this.toString() == "null") null else this.content
