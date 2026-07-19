package com.empresa.levantamiento.core.geo

import kotlinx.serialization.json.Json
import kotlinx.serialization.json.doubleOrNull
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive

/** Caja envolvente (bounding box) en grados. */
data class Bbox(val minLon: Double, val minLat: Double, val maxLon: Double, val maxLat: Double) {
    val center: Point get() = Point((minLon + maxLon) / 2.0, (minLat + maxLat) / 2.0)
}

/**
 * Utilidades GeoJSON puras (sin Android), usadas para dibujar y centrar el mapa
 * a partir del sector del trabajo y las geometrías de los elementos (RF-MOV-05).
 */
object GeoJson {
    private val json = Json { ignoreUnknownKeys = true }

    /** Parsea un `{"type":"Point","coordinates":[lon,lat]}`. */
    fun parsePoint(geoJson: String?): Point? {
        val obj = geoJson.toObjOrNull() ?: return null
        if (obj["type"]?.jsonPrimitive?.content != "Point") return null
        val c = obj["coordinates"]?.jsonArray ?: return null
        return coord(c)
    }

    /** Parsea el anillo exterior de un `Polygon`; lista vacía si no aplica. */
    fun parsePolygon(geoJson: String?): List<Point> {
        val obj = geoJson.toObjOrNull() ?: return emptyList()
        if (obj["type"]?.jsonPrimitive?.content != "Polygon") return emptyList()
        val rings = obj["coordinates"]?.jsonArray ?: return emptyList()
        val outer = rings.firstOrNull()?.jsonArray ?: return emptyList()
        return outer.mapNotNull { coord(it.jsonArray) }
    }

    /** Caja envolvente de un conjunto de puntos; null si está vacío. */
    fun bbox(points: List<Point>): Bbox? {
        if (points.isEmpty()) return null
        var minLon = Double.MAX_VALUE; var minLat = Double.MAX_VALUE
        var maxLon = -Double.MAX_VALUE; var maxLat = -Double.MAX_VALUE
        for (p in points) {
            if (p.lon < minLon) minLon = p.lon
            if (p.lat < minLat) minLat = p.lat
            if (p.lon > maxLon) maxLon = p.lon
            if (p.lat > maxLat) maxLat = p.lat
        }
        return Bbox(minLon, minLat, maxLon, maxLat)
    }

    private fun coord(arr: kotlinx.serialization.json.JsonArray): Point? {
        val lon = arr.getOrNull(0)?.jsonPrimitive?.doubleOrNull ?: return null
        val lat = arr.getOrNull(1)?.jsonPrimitive?.doubleOrNull ?: return null
        return Point(lon, lat)
    }

    private fun String?.toObjOrNull() =
        if (isNullOrBlank()) null
        else runCatching { json.parseToJsonElement(this).jsonObject }.getOrNull()
}
