package com.empresa.levantamiento.data.remote

import com.empresa.levantamiento.BuildConfig
import com.empresa.levantamiento.data.local.SessionStore
import com.jakewharton.retrofit2.converter.kotlinx.serialization.asConverterFactory
import kotlinx.serialization.json.Json
import okhttp3.CertificatePinner
import okhttp3.Interceptor
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import java.util.concurrent.TimeUnit

/**
 * Construcción del cliente HTTP y Retrofit. Cada petición autentica con el token
 * del funcionario y la identificación del dispositivo (RF-SYNC.2).
 */
object NetworkModule {

    private val json = Json {
        ignoreUnknownKeys = true
        encodeDefaults = true
    }

    fun createApi(session: SessionStore): ApiService {
        val authInterceptor = Interceptor { chain ->
            val builder = chain.request().newBuilder()
            session.accessToken?.let { builder.header("Authorization", "Bearer $it") }
            session.deviceUid?.let { builder.header("X-Device-Uid", it) }
            chain.proceed(builder.build())
        }

        val logging = HttpLoggingInterceptor().apply {
            level = if (BuildConfig.DEBUG) HttpLoggingInterceptor.Level.BASIC
            else HttpLoggingInterceptor.Level.NONE
        }

        val builder = OkHttpClient.Builder()
            .addInterceptor(authInterceptor)
            .addInterceptor(logging)
            .connectTimeout(20, TimeUnit.SECONDS)
            .readTimeout(60, TimeUnit.SECONDS)
            .writeTimeout(120, TimeUnit.SECONDS) // subidas de fotos

        // Certificate pinning opcional (RF-SYNC.1): se activa configurando el
        // host y el/los pins SHA-256 en BuildConfig. Sin configurar, no aplica.
        if (BuildConfig.CERT_PIN_HOST.isNotBlank() && BuildConfig.CERT_PIN_SHA256.isNotBlank()) {
            builder.certificatePinner(
                CertificatePinner.Builder()
                    .add(BuildConfig.CERT_PIN_HOST, "sha256/${BuildConfig.CERT_PIN_SHA256}")
                    .build()
            )
        }
        val client = builder.build()

        return Retrofit.Builder()
            .baseUrl(BuildConfig.API_BASE_URL)
            .client(client)
            .addConverterFactory(json.asConverterFactory("application/json".toMediaType()))
            .build()
            .create(ApiService::class.java)
    }
}
