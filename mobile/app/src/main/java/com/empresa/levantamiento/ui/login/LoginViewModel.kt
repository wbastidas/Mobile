package com.empresa.levantamiento.ui.login

import androidx.compose.runtime.State
import androidx.compose.runtime.mutableStateOf
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.empresa.levantamiento.di.ServiceLocator
import kotlinx.coroutines.launch

data class LoginState(val loading: Boolean = false, val error: String? = null)

class LoginViewModel : ViewModel() {
    private val auth = ServiceLocator.authRepository
    private val _state = mutableStateOf(LoginState())
    val state: State<LoginState> = _state

    fun login(username: String, password: String, deviceUid: String, onSuccess: () -> Unit) {
        if (username.isBlank() || password.isBlank()) {
            _state.value = LoginState(error = "Ingrese usuario y contraseña.")
            return
        }
        _state.value = LoginState(loading = true)
        viewModelScope.launch {
            auth.login(username.trim(), password, deviceUid.trim())
                .onSuccess {
                    _state.value = LoginState()
                    onSuccess()
                }
                .onFailure {
                    _state.value = LoginState(error = "No se pudo iniciar sesión. Verifique credenciales y dispositivo.")
                }
        }
    }
}
