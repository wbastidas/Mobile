package com.empresa.levantamiento

import android.app.Application
import com.empresa.levantamiento.di.ServiceLocator

class LevantamientoApp : Application() {
    override fun onCreate() {
        super.onCreate()
        ServiceLocator.init(this)
    }
}
