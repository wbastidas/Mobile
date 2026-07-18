package com.empresa.levantamiento

import android.app.Application
import com.empresa.levantamiento.di.ServiceLocator
import org.osmdroid.config.Configuration

class LevantamientoApp : Application() {
    override fun onCreate() {
        super.onCreate()
        ServiceLocator.init(this)
        // osmdroid requiere un user-agent y un directorio de caché de tiles.
        Configuration.getInstance().apply {
            userAgentValue = packageName
            osmdroidBasePath = filesDir
            osmdroidTileCache = filesDir.resolve("tiles")
        }
    }
}
