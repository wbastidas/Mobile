package com.empresa.levantamiento.ui.works

import androidx.compose.runtime.State
import androidx.compose.runtime.mutableStateOf
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.empresa.levantamiento.data.local.GeoPackageStore
import com.empresa.levantamiento.di.ServiceLocator
import com.empresa.levantamiento.sync.SyncManager
import kotlinx.coroutines.launch

data class WorksState(
    val works: List<GeoPackageStore.WorkRow> = emptyList(),
    val syncing: Boolean = false,
    val message: String? = null,
)

class WorksViewModel : ViewModel() {
    private val repo = ServiceLocator.workRepository
    private val sync = ServiceLocator.syncManager

    private val _state = mutableStateOf(WorksState())
    val state: State<WorksState> = _state

    init { refresh() }

    fun refresh() {
        _state.value = _state.value.copy(works = repo.works())
    }

    /** Descarga incremental al detectar conexión (RF-MOV-02.2). */
    fun pull() {
        _state.value = _state.value.copy(syncing = true, message = null)
        viewModelScope.launch {
            val result = runCatching { sync.pull() }
            result.onSuccess { toDelete ->
                // Ejecuta órdenes de borrado remoto recibidas (RF-WEB-05).
                toDelete.forEach { sync.confirmRemoteDelete(it) }
                _state.value = _state.value.copy(
                    syncing = false, works = repo.works(),
                    message = "Sincronización de bajada completada.",
                )
            }.onFailure {
                _state.value = _state.value.copy(syncing = false, message = "Sin conexión o error al descargar.")
            }
        }
    }

    /** Sincroniza (sube) un trabajo y reporta el resultado (RF-MOV-10). */
    fun syncWork(workId: String, onResult: (SyncManager.SyncOutcome) -> Unit) {
        _state.value = _state.value.copy(syncing = true, message = null)
        viewModelScope.launch {
            val outcome = sync.syncWork(workId)
            _state.value = _state.value.copy(syncing = false, works = repo.works())
            onResult(outcome)
        }
    }
}
