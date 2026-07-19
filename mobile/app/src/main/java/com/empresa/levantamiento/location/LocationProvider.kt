package com.empresa.levantamiento.location

import android.annotation.SuppressLint
import android.content.Context
import android.location.LocationManager
import kotlinx.coroutines.suspendCancellableCoroutine
import kotlin.coroutines.resume

data class LatLon(val lat: Double, val lon: Double)

/**
 * Proveedor de posición para sellar la metadata de fotos y capturar puntos
 * (RF-MOV-07, RF-MOV-08). Interfaz simple para poder sustituir por FusedLocation
 * o un mock en pruebas.
 */
interface LocationProvider {
    suspend fun current(): LatLon?
}

class AndroidLocationProvider(private val context: Context) : LocationProvider {

    @SuppressLint("MissingPermission") // el permiso se solicita en la capa de UI
    override suspend fun current(): LatLon? = suspendCancellableCoroutine { cont ->
        val lm = context.getSystemService(Context.LOCATION_SERVICE) as LocationManager
        val provider = when {
            lm.isProviderEnabled(LocationManager.GPS_PROVIDER) -> LocationManager.GPS_PROVIDER
            lm.isProviderEnabled(LocationManager.NETWORK_PROVIDER) -> LocationManager.NETWORK_PROVIDER
            else -> null
        }
        if (provider == null) {
            cont.resume(null)
            return@suspendCancellableCoroutine
        }
        val last = lm.getLastKnownLocation(provider)
        if (last != null) {
            cont.resume(LatLon(last.latitude, last.longitude))
            return@suspendCancellableCoroutine
        }
        val listener = android.location.LocationListener { loc ->
            cont.resume(LatLon(loc.latitude, loc.longitude))
        }
        lm.requestSingleUpdate(provider, listener, context.mainLooper)
        cont.invokeOnCancellation { lm.removeUpdates(listener) }
    }
}
