package com.empresa.levantamiento.core.model

import java.util.UUID

/** Generación de identificadores (RN-06: GUID único e inmutable por elemento). */
object Ids {
    /** GUID para un elemento nuevo capturado en el dispositivo (RF-MOV-06.5). */
    fun newElementGuid(): String = UUID.randomUUID().toString()

    /**
     * Clave de idempotencia por paquete de sincronización (RF-SYNC.5):
     * combina trabajo + versión + dispositivo para que los reintentos no dupliquen.
     */
    fun idempotencyKey(workId: String, deviceUid: String, version: Long): String =
        "$workId:$deviceUid:v$version"
}
