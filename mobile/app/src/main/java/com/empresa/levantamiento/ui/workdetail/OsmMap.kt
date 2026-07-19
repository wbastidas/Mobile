package com.empresa.levantamiento.ui.workdetail

import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.ui.Modifier
import androidx.compose.ui.viewinterop.AndroidView
import com.empresa.levantamiento.core.geo.GeoJson
import com.empresa.levantamiento.core.model.ElementRecord
import org.osmdroid.tileprovider.tilesource.TileSourceFactory
import org.osmdroid.util.GeoPoint
import org.osmdroid.views.MapView
import org.osmdroid.views.overlay.Marker
import org.osmdroid.views.overlay.Polygon

/**
 * Lienzo de mapa interactivo (osmdroid) que dibuja el sector del trabajo y los
 * elementos, y permite seleccionar un elemento tocando su marcador (RF-MOV-05).
 *
 * El parseo/centrado de geometría usa `core/geo/GeoJson` (lógica pura probada).
 */
@Composable
fun OsmMap(
    sectorGeoJson: String?,
    elements: List<ElementRecord>,
    onSelect: (String) -> Unit,
    modifier: Modifier = Modifier,
) {
    AndroidView(
        modifier = modifier,
        factory = { context ->
            MapView(context).apply {
                setTileSource(TileSourceFactory.MAPNIK)
                setMultiTouchControls(true)
                controller.setZoom(16.0)
            }
        },
        update = { map ->
            map.overlays.clear()

            // Polígono del sector (REVISION_RED).
            val ring = GeoJson.parsePolygon(sectorGeoJson)
            if (ring.isNotEmpty()) {
                val polygon = Polygon(map).apply {
                    points = ring.map { GeoPoint(it.lat, it.lon) }
                    fillPaint.color = 0x332563EB
                    outlinePaint.color = 0xFF2563EB.toInt()
                    outlinePaint.strokeWidth = 4f
                }
                map.overlays.add(polygon)
            }

            // Marcadores de elementos con geometría de punto.
            val pointElements = elements.mapNotNull { e ->
                GeoJson.parsePoint(e.geometryGeoJson)?.let { e to it }
            }
            for ((element, point) in pointElements) {
                val marker = Marker(map).apply {
                    position = GeoPoint(point.lat, point.lon)
                    title = "${element.elementType} · ${element.guid.take(8)}"
                    setAnchor(Marker.ANCHOR_CENTER, Marker.ANCHOR_BOTTOM)
                    setOnMarkerClickListener { _, _ -> onSelect(element.guid); true }
                }
                map.overlays.add(marker)
            }

            // Centrado: al centro del sector o al primer elemento disponible.
            val center = GeoJson.bbox(ring)?.center
                ?: pointElements.firstOrNull()?.second
            center?.let { map.controller.setCenter(GeoPoint(it.lat, it.lon)) }
            map.invalidate()
        },
    )

    // osmdroid necesita ciclo de vida; en un fragmento real se llamaría onResume/onPause.
    DisposableEffect(Unit) { onDispose { } }
}
