package com.empresa.levantamiento.core.geo

import kotlin.math.cos
import kotlin.math.hypot
import kotlin.math.max
import kotlin.math.min

/** Punto geográfico (lon, lat en grados). */
data class Point(val lon: Double, val lat: Double)

/**
 * Geometría candidata contra la cual ajustar (snapping): un vértice existente
 * (punto) o un tramo de red (segmento entre dos vértices).
 */
sealed interface SnapTarget {
    val guid: String

    data class Vertex(override val guid: String, val point: Point) : SnapTarget
    data class Segment(override val guid: String, val a: Point, val b: Point) : SnapTarget
}

data class SnapResult(
    val snapped: Point,
    val targetGuid: String,
    val distanceMeters: Double,
)

/**
 * Motor de snapping (RF-MOV-06.2): ajusta un punto capturado al elemento
 * existente más cercano dentro de una tolerancia parametrizable. Lógica pura y
 * probada; independiente de Android.
 *
 * Distancias en metros mediante una aproximación equirectangular local, válida
 * para las tolerancias pequeñas (metros) usadas en campo.
 */
class SnappingEngine(private val toleranceMeters: Double = 5.0) {

    fun snap(captured: Point, targets: List<SnapTarget>): SnapResult? {
        var best: SnapResult? = null
        for (t in targets) {
            val candidate = when (t) {
                is SnapTarget.Vertex -> SnapResult(t.point, t.guid, distance(captured, t.point))
                is SnapTarget.Segment -> {
                    val proj = projectOntoSegment(captured, t.a, t.b)
                    SnapResult(proj, t.guid, distance(captured, proj))
                }
            }
            if (candidate.distanceMeters <= toleranceMeters &&
                (best == null || candidate.distanceMeters < best.distanceMeters)
            ) {
                best = candidate
            }
        }
        return best
    }

    /** Distancia planar local en metros entre dos puntos. */
    fun distance(a: Point, b: Point): Double {
        val mPerDegLat = 111_320.0
        val mPerDegLon = 111_320.0 * cos(Math.toRadians((a.lat + b.lat) / 2.0))
        val dx = (a.lon - b.lon) * mPerDegLon
        val dy = (a.lat - b.lat) * mPerDegLat
        return hypot(dx, dy)
    }

    /** Proyección del punto p sobre el segmento a-b (en grados, con corrección de escala). */
    private fun projectOntoSegment(p: Point, a: Point, b: Point): Point {
        val kx = cos(Math.toRadians((a.lat + b.lat) / 2.0)) // corrección de longitud
        val ax = a.lon * kx; val ay = a.lat
        val bx = b.lon * kx; val by = b.lat
        val px = p.lon * kx; val py = p.lat
        val dx = bx - ax; val dy = by - ay
        val lenSq = dx * dx + dy * dy
        if (lenSq == 0.0) return a
        var t = ((px - ax) * dx + (py - ay) * dy) / lenSq
        t = max(0.0, min(1.0, t))
        val sx = ax + t * dx; val sy = ay + t * dy
        return Point(lon = sx / kx, lat = sy)
    }
}
