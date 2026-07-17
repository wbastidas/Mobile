package com.empresa.levantamiento.di

import android.content.Context
import com.empresa.levantamiento.data.local.GeoPackageStore
import com.empresa.levantamiento.data.local.ParamsStore
import com.empresa.levantamiento.data.local.SessionStore
import com.empresa.levantamiento.data.remote.ApiService
import com.empresa.levantamiento.data.remote.NetworkModule
import com.empresa.levantamiento.data.repo.AuthRepository
import com.empresa.levantamiento.data.repo.WorkRepository
import com.empresa.levantamiento.location.AndroidLocationProvider
import com.empresa.levantamiento.location.LocationProvider
import com.empresa.levantamiento.media.PhotoManager
import com.empresa.levantamiento.sync.SyncManager

/**
 * Contenedor de dependencias sencillo (sin framework de DI). Inicializa una sola
 * vez las dependencias compartidas. La arquitectura modular (RNF-06) facilita
 * sustituirlo por Hilt/Koin más adelante sin tocar los consumidores.
 */
object ServiceLocator {
    private lateinit var appContext: Context

    val session: SessionStore by lazy { SessionStore(appContext) }
    val params: ParamsStore by lazy { ParamsStore(appContext) }
    val store: GeoPackageStore by lazy { GeoPackageStore(appContext) }
    val api: ApiService by lazy { NetworkModule.createApi(session) }
    val locationProvider: LocationProvider by lazy { AndroidLocationProvider(appContext) }
    val photoManager: PhotoManager by lazy { PhotoManager(appContext, store) }

    val authRepository: AuthRepository by lazy { AuthRepository(api, session) }
    val workRepository: WorkRepository by lazy { WorkRepository(store) }
    val syncManager: SyncManager by lazy { SyncManager(api, store, params, session, photoManager) }

    fun init(context: Context) {
        appContext = context.applicationContext
    }
}
