package com.empresa.levantamiento.core.quality

import com.empresa.levantamiento.core.model.ElementRecord
import com.empresa.levantamiento.core.model.ValidationResult

/** Una novedad de calidad, explicada de forma clara (RF-MOV-09.3). */
data class QualityIssue(
    val elementGuid: String,
    val elementType: String,
    val field: String?,
    val ruleType: String,
    val message: String,
    val expected: String?,
    val actual: String?,
)

data class QualityReport(
    val result: ValidationResult,
    val issues: List<QualityIssue>,
) {
    val approved: Boolean get() = result == ValidationResult.APPROVED
}

/**
 * Motor de validación que se ejecuta EN EL DISPOSITIVO antes de sincronizar
 * (RF-MOV-09, RN-09). No depende de Android: es lógica pura y probada.
 */
class QualityValidator(private val rules: List<QualityRule>) {

    constructor(rulesJson: String) : this(QualityRulesParser.parse(rulesJson))

    fun validate(elements: List<ElementRecord>): QualityReport {
        val issues = mutableListOf<QualityIssue>()
        for (element in elements) {
            for (rule in rules.filter { it.elementType == element.elementType }) {
                checkRule(rule, element)?.let(issues::add)
            }
        }
        val result = if (issues.isEmpty()) ValidationResult.APPROVED else ValidationResult.WITH_ISSUES
        return QualityReport(result, issues)
    }

    private fun checkRule(rule: QualityRule, e: ElementRecord): QualityIssue? = when (rule) {
        is QualityRule.Required -> {
            val v = e.attributes[rule.field]
            if (v.isNullOrBlank())
                issue(e, rule.field, "required", "El campo '${rule.field}' es obligatorio.", "un valor", v)
            else null
        }
        is QualityRule.Domain -> {
            val v = e.attributes[rule.field]
            if (v != null && v.isNotBlank() && v !in rule.values)
                issue(e, rule.field, "domain",
                    "El valor de '${rule.field}' no está en el dominio permitido.",
                    rule.values.joinToString(", "), v)
            else null
        }
        is QualityRule.Range -> {
            val raw = e.attributes[rule.field]
            val num = raw?.toDoubleOrNull()
            when {
                raw.isNullOrBlank() -> null // ausencia la cubre 'required' si aplica
                num == null -> issue(e, rule.field, "range",
                    "El campo '${rule.field}' debe ser numérico.", "número", raw)
                rule.min != null && num < rule.min -> issue(e, rule.field, "range",
                    "'${rule.field}' por debajo del mínimo.", ">= ${rule.min}", raw)
                rule.max != null && num > rule.max -> issue(e, rule.field, "range",
                    "'${rule.field}' por encima del máximo.", "<= ${rule.max}", raw)
                else -> null
            }
        }
        is QualityRule.MinPhotos ->
            if (e.photoCount < rule.count)
                issue(e, null, "min_photos",
                    "Faltan fotografías del elemento.", "al menos ${rule.count}", e.photoCount.toString())
            else null
        is QualityRule.RequiresParent ->
            if (e.parentGuid.isNullOrBlank())
                issue(e, null, "requires_parent",
                    "El elemento debe estar vinculado a su elemento padre (puesto/unidad).",
                    "elemento padre", "ninguno")
            else null
        is QualityRule.RequiresGeometry ->
            if (e.geometryGeoJson.isNullOrBlank())
                issue(e, null, "requires_geometry",
                    "El elemento requiere geometría capturada.", "geometría", "ninguna")
            else null
    }

    private fun issue(e: ElementRecord, field: String?, type: String,
                      message: String, expected: String?, actual: String?) =
        QualityIssue(e.guid, e.elementType, field, type, message, expected, actual)
}
