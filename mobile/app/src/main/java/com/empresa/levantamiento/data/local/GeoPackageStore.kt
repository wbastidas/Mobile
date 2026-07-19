package com.empresa.levantamiento.data.local

import android.content.ContentValues
import android.content.Context
import android.database.sqlite.SQLiteDatabase
import android.database.sqlite.SQLiteOpenHelper
import com.empresa.levantamiento.core.model.ElementRecord

/**
 * Almacenamiento local en GeoPackage (RF-MOV-03).
 *
 * Un GeoPackage es SQLite con la extensión espacial OGC. Este store crea las
 * tablas de metadatos GPKG (`gpkg_*`) para ser un contenedor GPKG válido y las
 * tablas de aplicación por dispositivo. En esta iteración la geometría se guarda
 * como GeoJSON de texto (equivalente al backend); la evolución a blobs GPKG con
 * índice espacial RTree es directa y no cambia la interfaz pública.
 *
 * La operación es 100% offline (RF-MOV-02): todo se persiste de inmediato para
 * no perder datos ante cierres inesperados (RNF-05).
 */
class GeoPackageStore(context: Context) : SQLiteOpenHelper(context, DB_NAME, null, DB_VERSION) {

    override fun onConfigure(db: SQLiteDatabase) {
        db.setForeignKeyConstraintsEnabled(true)
    }

    override fun onCreate(db: SQLiteDatabase) {
        // Metadatos mínimos GeoPackage (contenedor válido).
        db.execSQL(
            """CREATE TABLE IF NOT EXISTS gpkg_contents(
                 table_name TEXT PRIMARY KEY, data_type TEXT, identifier TEXT,
                 min_x REAL, min_y REAL, max_x REAL, max_y REAL, srs_id INTEGER)"""
        )
        db.execSQL(
            """CREATE TABLE IF NOT EXISTS gpkg_geometry_columns(
                 table_name TEXT, column_name TEXT, geometry_type_name TEXT,
                 srs_id INTEGER, z INTEGER, m INTEGER)"""
        )

        // Trabajos asignados al dispositivo.
        db.execSQL(
            """CREATE TABLE works(
                 id TEXT PRIMARY KEY, code TEXT, title TEXT, work_type TEXT,
                 status TEXT, schema_version INTEGER, sector_geojson TEXT,
                 un_id TEXT)"""
        )

        // Elementos del modelo eléctrico (capa de features). Índices para
        // carga eficiente (RF-MOV-11). En producción: índice espacial RTree.
        db.execSQL(
            """CREATE TABLE elements(
                 guid TEXT PRIMARY KEY, work_id TEXT, element_type TEXT,
                 attributes_json TEXT, geometry_geojson TEXT, parent_guid TEXT,
                 observations TEXT, photo_count INTEGER DEFAULT 0,
                 is_new INTEGER DEFAULT 0, completed INTEGER DEFAULT 0,
                 dirty INTEGER DEFAULT 0, deleted INTEGER DEFAULT 0,
                 FOREIGN KEY(work_id) REFERENCES works(id) ON DELETE CASCADE)"""
        )
        db.execSQL("CREATE INDEX idx_elements_work ON elements(work_id)")
        db.execSQL("CREATE INDEX idx_elements_type ON elements(element_type)")
        db.execSQL("CREATE INDEX idx_elements_parent ON elements(parent_guid)")

        // Fotos capturadas, con metadata de trazabilidad (RF-MOV-08, RN-08).
        db.execSQL(
            """CREATE TABLE photos(
                 id TEXT PRIMARY KEY, work_id TEXT, element_guid TEXT,
                 path TEXT, gps_lat REAL, gps_lon REAL, captured_at TEXT,
                 sha256 TEXT, size_bytes INTEGER, total_chunks INTEGER DEFAULT 1,
                 uploaded INTEGER DEFAULT 0)"""
        )
        db.execSQL("CREATE INDEX idx_photos_work ON photos(work_id)")
    }

    override fun onUpgrade(db: SQLiteDatabase, oldVersion: Int, newVersion: Int) {
        // Esquema evolutivo (§6.4): migraciones aditivas. Placeholder inicial.
    }

    // ---- Trabajos ----

    fun upsertWork(id: String, code: String, title: String, type: String,
                   status: String, schemaVersion: Int, sectorGeoJson: String?, unId: String) {
        writableDatabase.insertWithOnConflict("works", null, ContentValues().apply {
            put("id", id); put("code", code); put("title", title); put("work_type", type)
            put("status", status); put("schema_version", schemaVersion)
            put("sector_geojson", sectorGeoJson); put("un_id", unId)
        }, SQLiteDatabase.CONFLICT_REPLACE)
    }

    fun updateWorkStatus(id: String, status: String) {
        writableDatabase.execSQL("UPDATE works SET status=? WHERE id=?", arrayOf(status, id))
    }

    data class WorkRow(
        val id: String, val code: String, val title: String, val type: String,
        val status: String, val schemaVersion: Int, val sectorGeoJson: String?, val unId: String,
    )

    fun getWorks(): List<WorkRow> = readableDatabase.rawQuery(
        "SELECT id,code,title,work_type,status,schema_version,sector_geojson,un_id FROM works ORDER BY code", null
    ).use { c ->
        buildList {
            while (c.moveToNext()) add(
                WorkRow(c.getString(0), c.getString(1), c.getString(2), c.getString(3),
                    c.getString(4), c.getInt(5), c.getStringOrNull(6), c.getString(7))
            )
        }
    }

    fun deleteWork(id: String) {
        // Solo tras sincronización confirmada o borrado remoto (RF-MOV-10.3, RN-03).
        writableDatabase.execSQL("DELETE FROM works WHERE id=?", arrayOf(id))
        writableDatabase.execSQL("DELETE FROM photos WHERE work_id=?", arrayOf(id))
    }

    // ---- Elementos ----

    fun upsertElement(workId: String, e: ElementRecord, observations: String?, completed: Boolean, dirty: Boolean) {
        writableDatabase.insertWithOnConflict("elements", null, ContentValues().apply {
            put("guid", e.guid); put("work_id", workId); put("element_type", e.elementType)
            put("attributes_json", attributesToJson(e.attributes))
            put("geometry_geojson", e.geometryGeoJson); put("parent_guid", e.parentGuid)
            put("observations", observations); put("photo_count", e.photoCount)
            put("is_new", if (e.isNew) 1 else 0); put("completed", if (completed) 1 else 0)
            put("dirty", if (dirty) 1 else 0); put("deleted", if (e.deleted) 1 else 0)
        }, SQLiteDatabase.CONFLICT_REPLACE)
    }

    fun getElements(workId: String): List<ElementRecord> = readableDatabase.rawQuery(
        "SELECT guid,element_type,attributes_json,geometry_geojson,parent_guid,photo_count,is_new,deleted FROM elements WHERE work_id=?",
        arrayOf(workId)
    ).use { c ->
        buildList {
            while (c.moveToNext()) add(
                ElementRecord(
                    guid = c.getString(0), elementType = c.getString(1),
                    attributes = attributesFromJson(c.getStringOrNull(2)),
                    geometryGeoJson = c.getStringOrNull(3), parentGuid = c.getStringOrNull(4),
                    photoCount = c.getInt(5), isNew = c.getInt(6) == 1,
                    deleted = c.getInt(7) == 1,
                )
            )
        }
    }

    fun countCompleted(workId: String): Pair<Int, Int> {
        readableDatabase.rawQuery(
            "SELECT COUNT(*), SUM(completed) FROM elements WHERE work_id=?", arrayOf(workId)
        ).use { c ->
            c.moveToFirst()
            return (c.getIntOrNull(1) ?: 0) to c.getInt(0)
        }
    }

    // ---- Fotos ----

    fun addPhoto(id: String, workId: String, elementGuid: String?, path: String,
                 lat: Double, lon: Double, capturedAt: String, sha256: String,
                 size: Long, totalChunks: Int) {
        writableDatabase.insert("photos", null, ContentValues().apply {
            put("id", id); put("work_id", workId); put("element_guid", elementGuid)
            put("path", path); put("gps_lat", lat); put("gps_lon", lon)
            put("captured_at", capturedAt); put("sha256", sha256); put("size_bytes", size)
            put("total_chunks", totalChunks); put("uploaded", 0)
        })
        elementGuid?.let {
            writableDatabase.execSQL(
                "UPDATE elements SET photo_count = photo_count + 1 WHERE guid=?", arrayOf(it)
            )
        }
    }

    data class PhotoRow(
        val id: String, val workId: String, val elementGuid: String?, val path: String,
        val lat: Double, val lon: Double, val capturedAt: String, val sha256: String,
        val size: Long, val totalChunks: Int, val uploaded: Boolean,
    )

    fun getPhotos(workId: String, onlyPending: Boolean = false): List<PhotoRow> {
        val where = if (onlyPending) " AND uploaded=0" else ""
        return readableDatabase.rawQuery(
            "SELECT id,work_id,element_guid,path,gps_lat,gps_lon,captured_at,sha256,size_bytes,total_chunks,uploaded FROM photos WHERE work_id=?$where",
            arrayOf(workId)
        ).use { c ->
            buildList {
                while (c.moveToNext()) add(
                    PhotoRow(c.getString(0), c.getString(1), c.getStringOrNull(2), c.getString(3),
                        c.getDouble(4), c.getDouble(5), c.getString(6), c.getString(7),
                        c.getLong(8), c.getInt(9), c.getInt(10) == 1)
                )
            }
        }
    }

    fun markPhotoUploaded(id: String) {
        writableDatabase.execSQL("UPDATE photos SET uploaded=1 WHERE id=?", arrayOf(id))
    }

    companion object {
        const val DB_NAME = "levantamiento.gpkg"
        const val DB_VERSION = 1
    }
}
