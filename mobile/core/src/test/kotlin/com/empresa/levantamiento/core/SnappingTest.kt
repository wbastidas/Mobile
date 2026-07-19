package com.empresa.levantamiento.core

import com.empresa.levantamiento.core.geo.Point
import com.empresa.levantamiento.core.geo.SnapTarget
import com.empresa.levantamiento.core.geo.SnappingEngine
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertNotNull
import kotlin.test.assertNull
import kotlin.test.assertTrue

class SnappingTest {

    // ~0.2 km al norte de un poste base; usamos coordenadas cercanas para metros pequeños.
    private val base = Point(lon = -78.5000000, lat = -0.2000000)

    @Test
    fun `ajusta al vertice mas cercano dentro de la tolerancia`() {
        val engine = SnappingEngine(toleranceMeters = 5.0)
        // Punto capturado ~2 m al este del poste (aprox 0.00002 grados de lon).
        val captured = Point(lon = -78.4999820, lat = -0.2000000)
        val target = SnapTarget.Vertex("POSTE-1", base)

        val result = engine.snap(captured, listOf(target))
        assertNotNull(result)
        assertEquals("POSTE-1", result.targetGuid)
        // Se ajusta exactamente al vértice existente.
        assertEquals(base.lon, result.snapped.lon, 1e-9)
        assertEquals(base.lat, result.snapped.lat, 1e-9)
        assertTrue(result.distanceMeters < 5.0)
    }

    @Test
    fun `no ajusta si esta fuera de la tolerancia`() {
        val engine = SnappingEngine(toleranceMeters = 1.0)
        val captured = Point(lon = -78.4999820, lat = -0.2000000) // ~2 m
        val result = engine.snap(captured, listOf(SnapTarget.Vertex("POSTE-1", base)))
        assertNull(result)
    }

    @Test
    fun `proyecta sobre un tramo de red`() {
        val engine = SnappingEngine(toleranceMeters = 10.0)
        // Segmento horizontal (misma latitud), punto capturado ligeramente al norte.
        val a = Point(lon = -78.5001000, lat = -0.2000000)
        val b = Point(lon = -78.4999000, lat = -0.2000000)
        val captured = Point(lon = -78.5000000, lat = -0.1999950) // ~0.5 m al norte del medio

        val result = engine.snap(captured, listOf(SnapTarget.Segment("TRAMO-1", a, b)))
        assertNotNull(result)
        assertEquals("TRAMO-1", result.targetGuid)
        // La proyección cae sobre la línea (misma latitud del segmento).
        assertEquals(-0.2000000, result.snapped.lat, 1e-6)
        assertTrue(result.snapped.lon in -78.5001000..-78.4999000)
    }

    @Test
    fun `elige el candidato mas cercano entre varios`() {
        val engine = SnappingEngine(toleranceMeters = 50.0)
        val cerca = SnapTarget.Vertex("CERCA", Point(-78.5000100, -0.2000000))
        val lejos = SnapTarget.Vertex("LEJOS", Point(-78.5003000, -0.2000000))
        val captured = Point(-78.5000000, -0.2000000)
        val result = engine.snap(captured, listOf(lejos, cerca))
        assertNotNull(result)
        assertEquals("CERCA", result.targetGuid)
    }
}
