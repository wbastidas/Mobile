package com.empresa.levantamiento.core.model

/**
 * Modelos de dominio compartidos, sin dependencias de Android.
 * Alineados con los contratos del backend (esquemas Pydantic).
 */

enum class WorkType { REVISION_RED, ORDEN_PUNTUAL, MANTENIMIENTO }

/** Protocolo de estados por trabajo (RF-SYNC.6). */
enum class WorkStatus {
    CREATED, ASSIGNED, DOWNLOADED, IN_PROGRESS, SYNCING,
    SYNCED, WITH_ISSUES, COMPLETED, SYNC_PENDING
}

enum class ValidationResult { APPROVED, WITH_ISSUES, NOT_RUN }

/** Registro de un elemento eléctrico editado/capturado en campo. */
data class ElementRecord(
    val guid: String,
    val elementType: String,
    /** Atributos del elemento (valor como texto; los numéricos se parsean al validar). */
    val attributes: Map<String, String?> = emptyMap(),
    /** Relación puesto/unidad (RN-07): GUID del elemento padre, si aplica. */
    val parentGuid: String? = null,
    /** Geometría GeoJSON; null en modo "solo punto + fotos" salvo el punto. */
    val geometryGeoJson: String? = null,
    val photoCount: Int = 0,
    val isNew: Boolean = false,
    /** Marcado para eliminación en campo; se consolida como DELETE (§7). */
    val deleted: Boolean = false,
)

/** Metadata obligatoria de una foto (RN-08). */
data class PhotoMetadata(
    val elementGuid: String?,
    val gpsLat: Double,
    val gpsLon: Double,
    val capturedAtIso: String,
    val sha256: String,
    val sizeBytes: Long,
    val totalChunks: Int = 1,
)
