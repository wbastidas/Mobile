package com.empresa.levantamiento.data.local

import android.content.Context

/**
 * Guarda los parámetros de calidad vigentes y la versión de esquema recibidos
 * en la descarga incremental (RF-WEB-10.3, RF-MOV-09.1). Se conservan localmente
 * para validar sin conexión.
 */
class ParamsStore(context: Context) {
    private val prefs = context.getSharedPreferences("le_params", Context.MODE_PRIVATE)

    var qualityRulesJson: String?
        get() = prefs.getString("rules_json", null)
        set(v) = prefs.edit().putString("rules_json", v).apply()

    var qualityVersion: Int
        get() = prefs.getInt("rules_version", 0)
        set(v) = prefs.edit().putInt("rules_version", v).apply()

    var schemaVersion: Int
        get() = prefs.getInt("schema_version", 1)
        set(v) = prefs.edit().putInt("schema_version", v).apply()

    /** Definición de esquema (capas/campos) para generar formularios (§6.4). */
    var schemaDefinitionJson: String?
        get() = prefs.getString("schema_definition", null)
        set(v) = prefs.edit().putString("schema_definition", v).apply()
}
