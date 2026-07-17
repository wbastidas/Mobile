package com.empresa.levantamiento.data.local

import android.database.Cursor
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive

// Extensiones seguras para columnas potencialmente nulas.
fun Cursor.getStringOrNull(index: Int): String? = if (isNull(index)) null else getString(index)
fun Cursor.getIntOrNull(index: Int): Int? = if (isNull(index)) null else getInt(index)

private val json = Json { ignoreUnknownKeys = true }

/** Serializa el mapa de atributos a un objeto JSON de texto. */
fun attributesToJson(attributes: Map<String, String?>): String =
    buildJsonObject {
        attributes.forEach { (k, v) -> put(k, JsonPrimitive(v)) }
    }.toString()

/** Deserializa un objeto JSON de texto al mapa de atributos. */
fun attributesFromJson(text: String?): Map<String, String?> {
    if (text.isNullOrBlank()) return emptyMap()
    return runCatching {
        json.parseToJsonElement(text).jsonObject.mapValues { (_, v) ->
            (v as? JsonPrimitive)?.let { if (it.toString() == "null") null else it.content }
        }
    }.getOrDefault(emptyMap())
}
