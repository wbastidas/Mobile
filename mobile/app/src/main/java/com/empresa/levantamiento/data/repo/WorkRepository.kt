package com.empresa.levantamiento.data.repo

import com.empresa.levantamiento.core.model.ElementRecord
import com.empresa.levantamiento.data.local.GeoPackageStore

/**
 * Acceso a trabajos y elementos almacenados localmente en GeoPackage.
 * Toda edición se persiste de inmediato (offline por defecto, RF-MOV-02/RNF-05).
 */
class WorkRepository(private val store: GeoPackageStore) {

    fun works(): List<GeoPackageStore.WorkRow> = store.getWorks()

    fun elements(workId: String): List<ElementRecord> = store.getElements(workId)

    fun progress(workId: String): Pair<Int, Int> = store.countCompleted(workId)

    /** Crea o edita un elemento, marcándolo como pendiente de sincronizar (dirty). */
    fun saveElement(workId: String, element: ElementRecord, observations: String?, completed: Boolean) {
        store.upsertElement(workId, element, observations, completed, dirty = true)
        if (store.getWorks().firstOrNull { it.id == workId }?.status == "DOWNLOADED") {
            store.updateWorkStatus(workId, "IN_PROGRESS")
        }
    }

    fun photos(workId: String) = store.getPhotos(workId)
}
