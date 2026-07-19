package com.empresa.levantamiento.core

import com.empresa.levantamiento.core.geo.GeoJson
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertNotNull
import kotlin.test.assertNull
import kotlin.test.assertTrue

class GeoJsonTest {

    @Test
    fun `parsea un punto`() {
        val p = GeoJson.parsePoint("""{"type":"Point","coordinates":[-78.5,-0.2]}""")
        assertNotNull(p)
        assertEquals(-78.5, p.lon, 1e-9)
        assertEquals(-0.2, p.lat, 1e-9)
    }

    @Test
    fun `un no-punto devuelve null`() {
        assertNull(GeoJson.parsePoint("""{"type":"LineString","coordinates":[]}"""))
        assertNull(GeoJson.parsePoint(null))
        assertNull(GeoJson.parsePoint("no-json"))
    }

    @Test
    fun `parsea el anillo exterior de un poligono`() {
        val poly = GeoJson.parsePolygon(
            """{"type":"Polygon","coordinates":[[[-78.51,-0.21],[-78.49,-0.21],[-78.49,-0.19],[-78.51,-0.19],[-78.51,-0.21]]]}"""
        )
        assertEquals(5, poly.size)
        assertEquals(-78.51, poly.first().lon, 1e-9)
    }

    @Test
    fun `bbox y centro de un poligono`() {
        val poly = GeoJson.parsePolygon(
            """{"type":"Polygon","coordinates":[[[-78.51,-0.21],[-78.49,-0.21],[-78.49,-0.19],[-78.51,-0.19],[-78.51,-0.21]]]}"""
        )
        val bbox = GeoJson.bbox(poly)
        assertNotNull(bbox)
        assertEquals(-78.51, bbox.minLon, 1e-9)
        assertEquals(-78.49, bbox.maxLon, 1e-9)
        assertEquals(-0.21, bbox.minLat, 1e-9)
        assertEquals(-0.19, bbox.maxLat, 1e-9)
        // El centro del sector cae en el medio.
        assertEquals(-78.50, bbox.center.lon, 1e-9)
        assertEquals(-0.20, bbox.center.lat, 1e-9)
    }

    @Test
    fun `bbox de lista vacia es null`() {
        assertNull(GeoJson.bbox(emptyList()))
    }

    @Test
    fun `tolera coordenadas malformadas`() {
        val poly = GeoJson.parsePolygon("""{"type":"Polygon","coordinates":[[[-78.5]]]}""")
        assertTrue(poly.isEmpty())
    }
}
