package com.empresa.levantamiento.core.schema

import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive

/** Tipo de campo de captura, derivado del esquema (§6.4). */
enum class FieldType { TEXT, NUMBER, DOMAIN, BOOLEAN }

/** Definición de un campo de captura generado a partir del esquema versionado. */
data class FieldDef(
    val name: String,
    val type: FieldType,
    val domain: List<String> = emptyList(),
)

/**
 * Deriva los campos de captura de un tipo de elemento a partir de la definición
 * de esquema (`SchemaDefinition.definition_json`) entregada por el backend. Así
 * los formularios se generan por metadatos, no por código rígido (§6.4).
 *
 * Formato esperado:
 * ```
 * { "layers": [
 *     { "name": "POSTE", "fields": [
 *         { "name": "material", "type": "domain", "values": ["HORMIGON","MADERA"] },
 *         { "name": "altura_m", "type": "number" }
 *     ] }
 * ] }
 * ```
 */
object SchemaFields {
    private val json = Json { ignoreUnknownKeys = true }

    fun fieldsFor(schemaJson: String?, elementType: String): List<FieldDef> {
        if (schemaJson.isNullOrBlank()) return emptyList()
        val root = runCatching { json.parseToJsonElement(schemaJson).jsonObject }.getOrNull()
            ?: return emptyList()
        val layers = (root["layers"] as? JsonArray) ?: return emptyList()
        val layer = layers.map { it.jsonObject }
            .firstOrNull { it["name"]?.jsonPrimitive?.content == elementType }
            ?: return emptyList()
        val fields = (layer["fields"] as? JsonArray) ?: return emptyList()
        return fields.mapNotNull { parseField(it.jsonObject) }
    }

    private fun parseField(obj: JsonObject): FieldDef? {
        val name = obj["name"]?.jsonPrimitive?.content ?: return null
        val values = (obj["values"] as? JsonArray)?.map { it.jsonPrimitive.content }.orEmpty()
        val type = when (obj["type"]?.jsonPrimitive?.content) {
            "number" -> FieldType.NUMBER
            "domain" -> FieldType.DOMAIN
            "boolean" -> FieldType.BOOLEAN
            else -> FieldType.TEXT
        }
        return FieldDef(name, type, values)
    }
}
