package com.empresa.levantamiento.data.repo

import com.empresa.levantamiento.core.sync.LoginRequest
import com.empresa.levantamiento.data.local.SessionStore
import com.empresa.levantamiento.data.remote.ApiService
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

/**
 * Autenticación del funcionario de campo (RF-MOV-01).
 * Valida funcionario + dispositivo autorizado en el primer login con conexión;
 * mantiene sesión offline persistente después.
 */
class AuthRepository(
    private val api: ApiService,
    private val session: SessionStore,
) {
    val isLoggedIn: Boolean get() = session.isLoggedIn

    suspend fun login(username: String, password: String, deviceUid: String): Result<Unit> =
        withContext(Dispatchers.IO) {
            runCatching {
                val token = api.mobileLogin(LoginRequest(username, password, deviceUid))
                session.accessToken = token.accessToken
                session.refreshToken = token.refreshToken
                session.username = username
                session.deviceUid = deviceUid
                session.expiresAt = System.currentTimeMillis() + token.expiresIn * 1000L
            }
        }

    fun logout() = session.clear()
}
