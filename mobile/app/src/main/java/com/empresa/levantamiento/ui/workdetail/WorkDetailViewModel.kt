package com.empresa.levantamiento.ui.workdetail

import androidx.compose.runtime.State
import androidx.compose.runtime.mutableStateOf
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.empresa.levantamiento.core.geo.Point
import com.empresa.levantamiento.core.geo.SnapTarget
import com.empresa.levantamiento.core.geo.SnappingEngine
import com.empresa.levantamiento.core.model.ElementRecord
import com.empresa.levantamiento.core.model.Ids
import com.empresa.levantamiento.data.local.GeoPackageStore
import com.empresa.levantamiento.di.ServiceLocator
import com.empresa.levantamiento.sync.SyncManager
import kotlinx.coroutines.launch
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.doubleOrNull
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive

data class WorkDetailState(
    val work: GeoPackageStore.WorkRow? = null,
    val elements: List<ElementRecord> = emptyList(),
    val selectedGuid: String? = null,
    val completed: Int = 0,
    val total: Int = 0,
    val busy: Boolean = false,
    val message: String? = null,
)

class WorkDetailViewModel(private val workId: String) : ViewModel() {
    private val repo = ServiceLocator.workRepository
    private val sync = ServiceLocator.syncManager
    private val location = ServiceLocator.locationProvider
    private val photoManager = ServiceLocator.photoManager

    private val _state = mutableStateOf(WorkDetailState())
    val state: State<WorkDetailState> = _state

    init { reload() }

    private fun reload() {
        val work = repo.works().firstOrNull { it.id == workId }
        val elements = repo.elements(workId)
        val (completed, total) = repo.progress(workId)
        _state.value = _state.value.copy(
            work = work, elements = elements, completed = completed, total = total,
        )
    }

    fun select(guid: String?) {
        _state.value = _state.value.copy(selectedGuid = guid)
    }

    val selectedElement: ElementRecord?
        get() = _state.value.elements.firstOrNull { it.guid == _state.value.selectedGuid }

    /** Crea un elemento nuevo con GUID generado en el dispositivo (RF-MOV-06.5). */
    fun newElement(elementType: String, parentGuid: String?) {
        val record = ElementRecord(
            guid = Ids.newElementGuid(), elementType = elementType,
            parentGuid = parentGuid, isNew = true,
        )
        repo.saveElement(workId, record, observations = null, completed = false)
        reload()
        select(record.guid)
    }

    /** Marca un elemento para eliminación; se consolidará como DELETE (§7). */
    fun markDeleted(element: ElementRecord) {
        repo.saveElement(workId, element.copy(deleted = true), observations = null, completed = true)
        reload()
        select(null)
        _state.value = _state.value.copy(message = "Elemento marcado para eliminación.")
    }

    fun saveElement(
        element: ElementRecord,
        attributes: Map<String, String?>,
        observations: String?,
        completed: Boolean,
    ) {
        repo.saveElement(workId, element.copy(attributes = attributes), observations, completed)
        reload()
    }

    /**
     * Modo "solo punto + fotos": sella la posición actual como geometría (RF-MOV-07),
     * aplicando snapping al elemento existente más cercano dentro de la tolerancia
     * (RF-MOV-06.2).
     */
    fun capturePoint(element: ElementRecord, snapToleranceMeters: Double = 5.0) {
        viewModelScope.launch {
            val pos = location.current()
            if (pos == null) {
                _state.value = _state.value.copy(message = "No se pudo obtener la ubicación.")
                return@launch
            }
            var captured = Point(pos.lon, pos.lat)
            var snappedMsg = "Punto capturado."

            // Candidatos: vértices de otros elementos del trabajo con geometría de punto.
            val targets = _state.value.elements
                .filter { it.guid != element.guid }
                .mapNotNull { e -> parsePoint(e.geometryGeoJson)?.let { SnapTarget.Vertex(e.guid, it) } }
            SnappingEngine(snapToleranceMeters).snap(captured, targets)?.let { snap ->
                captured = snap.snapped
                snappedMsg = "Punto ajustado a ${snap.targetGuid} (%.1f m).".format(snap.distanceMeters)
            }

            val geom = """{"type":"Point","coordinates":[${captured.lon},${captured.lat}]}"""
            repo.saveElement(workId, element.copy(geometryGeoJson = geom), null, false)
            reload()
            _state.value = _state.value.copy(message = snappedMsg)
        }
    }

    /** Captura una foto (bytes desde la cámara) con metadata GPS/fecha (RF-MOV-08). */
    fun addPhoto(elementGuid: String?, bytes: ByteArray) {
        viewModelScope.launch {
            val pos = location.current()
            photoManager.processAndStore(
                sourceBytes = bytes, workId = workId, elementGuid = elementGuid,
                gpsLat = pos?.lat ?: 0.0, gpsLon = pos?.lon ?: 0.0,
            )
            reload()
            _state.value = _state.value.copy(message = "Foto guardada con metadata.")
        }
    }

    fun sync(onResult: (SyncManager.SyncOutcome) -> Unit) {
        _state.value = _state.value.copy(busy = true, message = null)
        viewModelScope.launch {
            val outcome = sync.syncWork(workId)
            reload()
            _state.value = _state.value.copy(busy = false)
            onResult(outcome)
        }
    }

    /** Elimina el trabajo del dispositivo; solo se invoca tras sync verificada (RN-03). */
    fun deleteLocal(onDone: () -> Unit) {
        sync.deleteLocal(workId)
        onDone()
    }

    /** Extrae [lon, lat] de una geometría GeoJSON de tipo Point; null si no aplica. */
    private fun parsePoint(geoJson: String?): Point? {
        if (geoJson.isNullOrBlank()) return null
        return runCatching {
            val obj = Json.parseToJsonElement(geoJson).jsonObject
            if (obj["type"]?.jsonPrimitive?.content != "Point") return null
            val coords = obj["coordinates"]!!.jsonArray
            Point(
                lon = coords[0].jsonPrimitive.doubleOrNull ?: return null,
                lat = coords[1].jsonPrimitive.doubleOrNull ?: return null,
            )
        }.getOrNull()
    }
}
