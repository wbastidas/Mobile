package com.empresa.levantamiento.core

import com.empresa.levantamiento.core.model.ElementRecord
import com.empresa.levantamiento.core.model.Ids
import com.empresa.levantamiento.core.model.ValidationResult
import com.empresa.levantamiento.core.quality.QualityValidator
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertNotNull
import kotlin.test.assertTrue

class QualityValidatorTest {

    private val rulesJson = """
        { "rules": {
            "POSTE": [
              { "field": "material", "type": "domain", "values": ["HORMIGON","MADERA","METAL"] },
              { "field": "altura_m", "type": "range", "min": 6, "max": 20 },
              { "field": "material", "type": "required" },
              { "rule": "min_photos", "value": 2 }
            ],
            "LUMINARIA": [
              { "field": "potencia_w", "type": "required" }
            ]
        } }
    """.trimIndent()

    private val validator = QualityValidator(rulesJson)

    @Test
    fun `elemento valido no genera novedades`() {
        val poste = ElementRecord(
            guid = "P1", elementType = "POSTE",
            attributes = mapOf("material" to "HORMIGON", "altura_m" to "12"),
            photoCount = 2,
        )
        val report = validator.validate(listOf(poste))
        assertEquals(ValidationResult.APPROVED, report.result)
        assertTrue(report.issues.isEmpty())
        assertTrue(report.approved)
    }

    @Test
    fun `campo obligatorio ausente genera novedad required`() {
        val poste = ElementRecord(
            guid = "P2", elementType = "POSTE",
            attributes = mapOf("altura_m" to "12"), photoCount = 2,
        )
        val report = validator.validate(listOf(poste))
        assertEquals(ValidationResult.WITH_ISSUES, report.result)
        val issue = report.issues.firstOrNull { it.ruleType == "required" }
        assertNotNull(issue)
        assertEquals("material", issue.field)
    }

    @Test
    fun `valor fuera de dominio genera novedad`() {
        val poste = ElementRecord(
            guid = "P3", elementType = "POSTE",
            attributes = mapOf("material" to "PLASTICO", "altura_m" to "12"), photoCount = 2,
        )
        val report = validator.validate(listOf(poste))
        assertTrue(report.issues.any { it.ruleType == "domain" && it.field == "material" })
    }

    @Test
    fun `valor fuera de rango genera novedad`() {
        val bajo = ElementRecord("P4", "POSTE", mapOf("material" to "MADERA", "altura_m" to "3"), photoCount = 2)
        val alto = ElementRecord("P5", "POSTE", mapOf("material" to "MADERA", "altura_m" to "40"), photoCount = 2)
        assertTrue(validator.validate(listOf(bajo)).issues.any { it.ruleType == "range" })
        assertTrue(validator.validate(listOf(alto)).issues.any { it.ruleType == "range" })
    }

    @Test
    fun `campo no numerico en regla range genera novedad`() {
        val poste = ElementRecord("P6", "POSTE", mapOf("material" to "METAL", "altura_m" to "doce"), photoCount = 2)
        assertTrue(validator.validate(listOf(poste)).issues.any { it.ruleType == "range" })
    }

    @Test
    fun `faltan fotos genera novedad min_photos`() {
        val poste = ElementRecord("P7", "POSTE", mapOf("material" to "METAL", "altura_m" to "10"), photoCount = 1)
        val report = validator.validate(listOf(poste))
        val issue = report.issues.firstOrNull { it.ruleType == "min_photos" }
        assertNotNull(issue)
        assertEquals("al menos 2", issue.expected)
    }

    @Test
    fun `reglas solo aplican al tipo de elemento correspondiente`() {
        // Una LUMINARIA sin potencia_w falla; un POSTE no es afectado por reglas de LUMINARIA.
        val lum = ElementRecord("L1", "LUMINARIA", emptyMap(), photoCount = 0)
        val report = validator.validate(listOf(lum))
        assertTrue(report.issues.all { it.elementType == "LUMINARIA" })
        assertTrue(report.issues.any { it.field == "potencia_w" })
    }

    @Test
    fun `idempotency key es estable y unica por version`() {
        val k1 = Ids.idempotencyKey("W1", "DEV1", 3)
        val k2 = Ids.idempotencyKey("W1", "DEV1", 3)
        val k3 = Ids.idempotencyKey("W1", "DEV1", 4)
        assertEquals(k1, k2)
        assertTrue(k1 != k3)
    }
}
