package com.empresa.levantamiento.media

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import com.empresa.levantamiento.data.local.GeoPackageStore
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.io.File
import java.security.MessageDigest
import java.time.Instant
import java.util.UUID

/**
 * Gestión del ciclo de vida de las fotos (RF-MOV-08):
 *  - compresión automática (resolución/calidad configurables) — RF-MOV-08.3,
 *  - metadata obligatoria (GPS, fecha/hora, elemento, funcionario, dispositivo) — RN-08,
 *  - verificación de integridad por hash SHA-256 antes/después de transferir,
 *  - almacenamiento organizado por trabajo/elemento,
 *  - eliminación local SOLO tras confirmación de recepción (en SyncManager).
 *
 * El procesamiento pesado corre fuera del hilo de UI (RF-MOV-11).
 */
class PhotoManager(
    private val context: Context,
    private val store: GeoPackageStore,
    private val maxDimension: Int = 1600,
    private val jpegQuality: Int = 70,
) {

    data class Result(val photoId: String, val sha256: String, val sizeBytes: Long, val path: String)

    /**
     * Comprime la imagen de origen, calcula su hash y la registra con su metadata.
     * @param sourceBytes bytes de la foto capturada por la cámara.
     */
    suspend fun processAndStore(
        sourceBytes: ByteArray,
        workId: String,
        elementGuid: String?,
        gpsLat: Double,
        gpsLon: Double,
    ): Result = withContext(Dispatchers.IO) {
        val compressed = compress(sourceBytes)
        val photoId = UUID.randomUUID().toString()
        val dir = File(context.filesDir, "photos/$workId").apply { mkdirs() }
        val file = File(dir, "$photoId.jpg")
        file.writeBytes(compressed)

        val sha = sha256(compressed)
        val capturedAt = Instant.now().toString() // fecha/hora de captura (RN-08)

        store.addPhoto(
            id = photoId, workId = workId, elementGuid = elementGuid, path = file.absolutePath,
            lat = gpsLat, lon = gpsLon, capturedAt = capturedAt, sha256 = sha,
            size = compressed.size.toLong(), totalChunks = chunkCount(compressed.size),
        )
        Result(photoId, sha, compressed.size.toLong(), file.absolutePath)
    }

    /** Verifica la integridad de un archivo contra su hash esperado (RF-SYNC.4). */
    fun verifyIntegrity(path: String, expectedSha: String): Boolean =
        runCatching { sha256(File(path).readBytes()) == expectedSha }.getOrDefault(false)

    private fun compress(bytes: ByteArray): ByteArray {
        val bounds = BitmapFactory.Options().apply { inJustDecodeBounds = true }
        BitmapFactory.decodeByteArray(bytes, 0, bytes.size, bounds)
        val sample = calculateInSampleSize(bounds.outWidth, bounds.outHeight, maxDimension)
        val opts = BitmapFactory.Options().apply { inSampleSize = sample }
        val bitmap = BitmapFactory.decodeByteArray(bytes, 0, bytes.size, opts)
            ?: return bytes // si no decodifica, se conserva el original
        return java.io.ByteArrayOutputStream().use { out ->
            bitmap.compress(Bitmap.CompressFormat.JPEG, jpegQuality, out)
            bitmap.recycle()
            out.toByteArray()
        }
    }

    private fun calculateInSampleSize(width: Int, height: Int, maxDim: Int): Int {
        var sample = 1
        var w = width
        var h = height
        while (w / 2 >= maxDim || h / 2 >= maxDim) {
            w /= 2; h /= 2; sample *= 2
        }
        return sample
    }

    private fun chunkCount(size: Int, chunkBytes: Int = 512 * 1024): Int =
        ((size + chunkBytes - 1) / chunkBytes).coerceAtLeast(1)

    private fun sha256(data: ByteArray): String =
        MessageDigest.getInstance("SHA-256").digest(data).joinToString("") { "%02x".format(it) }
}
