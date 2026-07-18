package com.empresa.levantamiento.core

import com.empresa.levantamiento.core.model.ElementRecord
import com.empresa.levantamiento.core.quality.QualityValidator
import com.empresa.levantamiento.core.quality.toDto
import kotlinx.serialization.json.Json
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertTrue

class ReportMapperTest {

    private val rules = """
        { "rules": { "POSTE": [
            { "field": "material", "type": "required" },
            { "field": "altura_m", "type": "range", "min": 6, "max": 20 }
        ] } }
    """.trimIndent()

    @Test
    fun `el reporte se mapea a DTO serializable con el detalle por regla`() {
        val validator = QualityValidator(rules)
        val report = validator.validate(
            listOf(ElementRecord("P1", "POSTE", mapOf("altura_m" to "40")))
        )
        val dto = report.toDto()

        assertEquals("WITH_ISSUES", dto.result)
        assertTrue(dto.issues.any { it.ruleType == "required" && it.field == "material" })
        assertTrue(dto.issues.any { it.ruleType == "range" && it.field == "altura_m" })

        // Round-trip JSON (mismo formato que consumirá el backend).
        val json = Json.encodeToString(
            com.empresa.levantamiento.core.sync.ValidationReportDto.serializer(), dto
        )
        val back = Json.decodeFromString(
            com.empresa.levantamiento.core.sync.ValidationReportDto.serializer(), json
        )
        assertEquals(dto.issues.size, back.issues.size)
        assertTrue(json.contains("rule_type"))
    }
}
