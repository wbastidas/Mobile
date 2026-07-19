package com.empresa.levantamiento.core

import com.empresa.levantamiento.core.schema.FieldType
import com.empresa.levantamiento.core.schema.SchemaFields
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertTrue

class SchemaFieldsTest {

    private val schema = """
        { "layers": [
          { "name": "POSTE", "fields": [
              { "name": "material", "type": "domain", "values": ["HORMIGON","MADERA","METAL"] },
              { "name": "altura_m", "type": "number" },
              { "name": "observado", "type": "boolean" }
          ] },
          { "name": "LUMINARIA", "fields": [ { "name": "potencia_w", "type": "number" } ] }
        ] }
    """.trimIndent()

    @Test
    fun `deriva campos del tipo de elemento`() {
        val fields = SchemaFields.fieldsFor(schema, "POSTE")
        assertEquals(3, fields.size)
        val material = fields.first { it.name == "material" }
        assertEquals(FieldType.DOMAIN, material.type)
        assertEquals(listOf("HORMIGON", "MADERA", "METAL"), material.domain)
        assertEquals(FieldType.NUMBER, fields.first { it.name == "altura_m" }.type)
        assertEquals(FieldType.BOOLEAN, fields.first { it.name == "observado" }.type)
    }

    @Test
    fun `tipo sin capa devuelve vacio`() {
        assertTrue(SchemaFields.fieldsFor(schema, "TRANSFORMADOR").isEmpty())
    }

    @Test
    fun `esquema nulo o invalido no rompe`() {
        assertTrue(SchemaFields.fieldsFor(null, "POSTE").isEmpty())
        assertTrue(SchemaFields.fieldsFor("no-json", "POSTE").isEmpty())
    }
}
