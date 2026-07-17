package com.empresa.levantamiento.core.quality

import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive

/**
 * Modelo y parser del archivo de parámetros de calidad (RF-WEB-10 / RF-MOV-09).
 *
 * Formato esperado (versionable y dirigido por metadatos, §6.4):
 * ```
 * { "rules": {
 *     "POSTE": [
 *       { "field": "material", "type": "domain", "values": ["HORMIGON","MADERA"] },
 *       { "field": "altura_m", "type": "range", "min": 6, "max": 20 },
 *       { "rule": "min_photos", "value": 2 }
 *     ]
 * } }
 * ```
 * El pendiente PD-04 (formato definitivo) se absorbe aquí sin tocar el resto.
 */
sealed interface QualityRule {
    val elementType: String

    data class Required(override val elementType: String, val field: String) : QualityRule
    data class Domain(override val elementType: String, val field: String, val values: Set<String>) : QualityRule
    data class Range(
        override val elementType: String,
        val field: String,
        val min: Double?,
        val max: Double?,
    ) : QualityRule
    data class MinPhotos(override val elementType: String, val count: Int) : QualityRule
    /** Exige que el elemento tenga un elemento padre (relación puesto/unidad, RN-07). */
    data class RequiresParent(override val elementType: String) : QualityRule
    /** Exige geometría presente. */
    data class RequiresGeometry(override val elementType: String) : QualityRule
}

object QualityRulesParser {
    private val json = Json { ignoreUnknownKeys = true }

    /** Parsea el JSON de reglas a una lista tipada. Ignora entradas malformadas. */
    fun parse(rulesJson: String): List<QualityRule> {
        val root = runCatching { json.parseToJsonElement(rulesJson).jsonObject }.getOrNull() ?: return emptyList()
        val rulesObj = (root["rules"] as? JsonObject) ?: return emptyList()
        val out = mutableListOf<QualityRule>()
        for ((elementType, arr) in rulesObj) {
            val list = (arr as? JsonArray) ?: continue
            for (item in list) {
                val obj = (item as? JsonObject) ?: continue
                parseRule(elementType, obj)?.let(out::add)
            }
        }
        return out
    }

    private fun JsonObject.str(key: String): String? =
        this[key]?.jsonPrimitive?.contentOrNullSafe()

    private fun JsonObject.dbl(key: String): Double? =
        this[key]?.jsonPrimitive?.contentOrNullSafe()?.toDoubleOrNull()

    private fun parseRule(elementType: String, obj: JsonObject): QualityRule? {
        val field = obj.str("field")
        return when (obj.str("type") ?: obj.str("rule")) {
            "required" -> field?.let { QualityRule.Required(elementType, it) }
            "domain" -> {
                val values = (obj["values"] as? JsonArray)
                    ?.mapNotNull { it.jsonPrimitive.contentOrNullSafe() }?.toSet().orEmpty()
                field?.let { QualityRule.Domain(elementType, it, values) }
            }
            "range" -> field?.let { QualityRule.Range(elementType, it, obj.dbl("min"), obj.dbl("max")) }
            "min_photos" -> QualityRule.MinPhotos(elementType, obj.dbl("value")?.toInt() ?: 1)
            "requires_parent" -> QualityRule.RequiresParent(elementType)
            "requires_geometry" -> QualityRule.RequiresGeometry(elementType)
            else -> null
        }
    }
}

private fun kotlinx.serialization.json.JsonPrimitive.contentOrNullSafe(): String? =
    if (this.toString() == "null") null else this.content
