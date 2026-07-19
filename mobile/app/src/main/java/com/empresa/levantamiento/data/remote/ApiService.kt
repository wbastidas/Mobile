package com.empresa.levantamiento.data.remote

import com.empresa.levantamiento.core.sync.LoginRequest
import com.empresa.levantamiento.core.sync.SyncUploadRequest
import com.empresa.levantamiento.core.sync.SyncUploadResponse
import com.empresa.levantamiento.core.sync.SyncVerifyResponse
import com.empresa.levantamiento.core.sync.TokenResponse
import kotlinx.serialization.json.JsonObject
import okhttp3.MultipartBody
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.Multipart
import retrofit2.http.POST
import retrofit2.http.Part
import retrofit2.http.Path
import retrofit2.http.Query

/**
 * Contrato REST con el backend, espejo de `app/api/v1` del servidor.
 * Toda transferencia va sobre HTTPS/TLS en producción (RF-SYNC.1).
 */
interface ApiService {

    @POST("auth/mobile/login")
    suspend fun mobileLogin(@Body body: LoginRequest): TokenResponse

    /** Descarga incremental: trabajos nuevos, borrados, parámetros de calidad (RF-SYNC.7). */
    @GET("sync/pull")
    suspend fun pull(@Query("device_uid") deviceUid: String): JsonObject

    /** Sube el paquete de sincronización (idempotente, RF-SYNC.5). */
    @POST("sync/upload")
    suspend fun upload(@Body body: SyncUploadRequest): SyncUploadResponse

    /** Sube un chunk de una foto (subida reanudable por lotes, RF-SYNC.3). */
    @Multipart
    @POST("sync/photo/{sha256}/chunk")
    suspend fun uploadPhotoChunk(
        @Path("sha256") sha256: String,
        @Query("index") index: Int,
        @Query("total") total: Int,
        @Part chunk: MultipartBody.Part,
    ): JsonObject

    /** Verificación de completitud + consolidación (RF-MOV-10.2). */
    @POST("sync/verify/{packageId}")
    suspend fun verify(@Path("packageId") packageId: String): SyncVerifyResponse

    /** Confirma la ejecución de un borrado remoto (RF-WEB-05.2). */
    @POST("sync/confirm-delete/{workId}")
    suspend fun confirmDelete(
        @Path("workId") workId: String,
        @Query("device_uid") deviceUid: String,
    ): JsonObject
}
