package com.empresa.levantamiento.core.sync

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

/**
 * DTOs de sincronización (serializables), espejo de los esquemas del backend
 * (`app/schemas/sync.py`). Al ser Kotlin puro se comparten y se prueban sin Android.
 */

@Serializable
data class LoginRequest(
    val username: String,
    val password: String,
    @SerialName("device_uid") val deviceUid: String,
)

@Serializable
data class TokenResponse(
    @SerialName("access_token") val accessToken: String,
    @SerialName("refresh_token") val refreshToken: String,
    @SerialName("expires_in") val expiresIn: Int,
)

@Serializable
data class PhotoMetaDto(
    @SerialName("element_guid") val elementGuid: String? = null,
    @SerialName("gps_lat") val gpsLat: Double,
    @SerialName("gps_lon") val gpsLon: Double,
    @SerialName("captured_at") val capturedAt: String,
    val sha256: String,
    @SerialName("size_bytes") val sizeBytes: Long = 0,
    @SerialName("total_chunks") val totalChunks: Int = 1,
)

@Serializable
data class SyncUploadRequest(
    @SerialName("idempotency_key") val idempotencyKey: String,
    @SerialName("work_id") val workId: String,
    @SerialName("device_uid") val deviceUid: String,
    @SerialName("schema_version") val schemaVersion: Int = 1,
    val checksum: String? = null,
    @SerialName("payload_json") val payloadJson: String,
    @SerialName("validation_result") val validationResult: String = "NOT_RUN",
    @SerialName("validation_report_json") val validationReportJson: String? = null,
    val photos: List<PhotoMetaDto> = emptyList(),
)

@Serializable
data class SyncUploadResponse(
    @SerialName("package_id") val packageId: String,
    val accepted: Boolean,
    val duplicate: Boolean,
    @SerialName("missing_photos") val missingPhotos: List<String> = emptyList(),
    val detail: String = "",
)

@Serializable
data class SyncVerifyResponse(
    @SerialName("work_id") val workId: String,
    val verified: Boolean,
    val status: String,
    val detail: String = "",
)

/**
 * Reporte detallado de validación de calidad que viaja en el paquete de sync,
 * para que la web muestre las novedades por elemento y por regla (RF-WEB-09.2)
 * y agregue las más frecuentes (RF-WEB-11.1).
 */
@Serializable
data class ValidationIssueDto(
    @SerialName("element_guid") val elementGuid: String,
    @SerialName("element_type") val elementType: String,
    val field: String? = null,
    @SerialName("rule_type") val ruleType: String,
    val message: String,
    val expected: String? = null,
    val actual: String? = null,
)

@Serializable
data class ValidationReportDto(
    val result: String,
    val issues: List<ValidationIssueDto> = emptyList(),
)
