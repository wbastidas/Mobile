package com.empresa.levantamiento.data.local

import android.content.Context
import android.content.SharedPreferences
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey

/**
 * Almacenamiento cifrado de credenciales y sesión offline (RF-MOV-01.3, RNF-01).
 *
 * Usa EncryptedSharedPreferences respaldado por el Android Keystore. La sesión
 * persiste tras el primer login exitoso para operar sin conectividad; se
 * revalida al reconectar.
 */
class SessionStore(context: Context) {

    private val prefs: SharedPreferences by lazy {
        val masterKey = MasterKey.Builder(context)
            .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
            .build()
        EncryptedSharedPreferences.create(
            context,
            "le_secure_session",
            masterKey,
            EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
            EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM,
        )
    }

    var accessToken: String?
        get() = prefs.getString(KEY_ACCESS, null)
        set(v) = prefs.edit().putString(KEY_ACCESS, v).apply()

    var refreshToken: String?
        get() = prefs.getString(KEY_REFRESH, null)
        set(v) = prefs.edit().putString(KEY_REFRESH, v).apply()

    var deviceUid: String?
        get() = prefs.getString(KEY_DEVICE, null)
        set(v) = prefs.edit().putString(KEY_DEVICE, v).apply()

    var username: String?
        get() = prefs.getString(KEY_USER, null)
        set(v) = prefs.edit().putString(KEY_USER, v).apply()

    var unId: String?
        get() = prefs.getString(KEY_UN, null)
        set(v) = prefs.edit().putString(KEY_UN, v).apply()

    /** Última expiración (epoch millis) para revalidación configurable. */
    var expiresAt: Long
        get() = prefs.getLong(KEY_EXPIRES, 0L)
        set(v) = prefs.edit().putLong(KEY_EXPIRES, v).apply()

    val isLoggedIn: Boolean get() = accessToken != null && username != null

    fun clear() = prefs.edit().clear().apply()

    private companion object {
        const val KEY_ACCESS = "access_token"
        const val KEY_REFRESH = "refresh_token"
        const val KEY_DEVICE = "device_uid"
        const val KEY_USER = "username"
        const val KEY_UN = "un_id"
        const val KEY_EXPIRES = "expires_at"
    }
}
