"""Editores físicos reales hacia la geodatabase corporativa (PD-02).

Estos editores implementan `GeodatabaseEditor` sobre las dos rutas prioritarias
de Python descritas en `docs/INTEGRACION_ARCSDE.md`:

- `OracleSdeEditor` — edición vía `python-oracledb` con SDO_GEOMETRY. Solo debe
  usarse contra vistas/tablas soportadas o un esquema de staging Oracle; escribir
  las tablas delta de SDE por debajo NO está soportado por Esri.
- `ArcPyEditor` — edición vía ArcPy con `arcpy.da.Editor` / InsertCursor /
  UpdateCursor, que respeta el versionado y las relationship classes.

Ambos se cargan de forma perezosa (import diferido) para que el resto del sistema
no dependa de que Oracle/ArcGIS estén instalados. La cola de edición garantiza
que solo una sesión esté activa a la vez, así que estos editores no gestionan
concurrencia.

El mapeo campo↔columna, la conversión de geometría (GeoJSON→SDO/Shape) y la
resolución de relaciones puesto/unidad dependen del esquema definitivo (PD-03) y
se completan cuando esa información esté disponible; los puntos exactos están
marcados con `TODO(PD-02/PD-03)`.
"""
from __future__ import annotations

import json
from typing import Any, Optional

from app.modules.gis.editor import GeodatabaseEditor


class OracleSdeEditor(GeodatabaseEditor):
    """Edición transaccional vía python-oracledb (una transacción por lote)."""

    # Tabla destino por tipo de elemento (se parametriza con el esquema real).
    TABLE_BY_TYPE = {"POSTE": "GDB.POSTES", "LUMINARIA": "GDB.LUMINARIAS"}

    def __init__(self, dsn: str, user: str, password: str):
        self._dsn, self._user, self._password = dsn, user, password
        self._conn: Any = None

    def begin_session(self, un_code: str) -> None:
        import oracledb  # import diferido (dependencia opcional)
        self._conn = oracledb.connect(user=self._user, password=self._password, dsn=self._dsn)
        self._conn.autocommit = False  # una transacción reversible por lote (§7.4)
        self._un_code = un_code

    def apply(self, operation: str, element: Any) -> None:
        cur = self._conn.cursor()
        table = self.TABLE_BY_TYPE.get(element.element_type, "GDB.ELEMENTOS")
        attrs = json.loads(element.attributes_json or "{}")
        geom = self._to_sdo(element.geometry_geojson)
        if operation == "DELETE":
            cur.execute(f"DELETE FROM {table} WHERE GLOBALID = :guid", guid=element.guid)
        elif operation == "CREATE":
            # TODO(PD-03): columnas reales del modelo eléctrico + SDO_GEOMETRY.
            cur.execute(
                f"INSERT INTO {table} (GLOBALID, PARENT_GUID, SHAPE) "
                f"VALUES (:guid, :parent, :shape)",
                guid=element.guid, parent=element.parent_guid, shape=geom,
            )
        else:  # UPDATE
            cur.execute(
                f"UPDATE {table} SET SHAPE = :shape WHERE GLOBALID = :guid",
                shape=geom, guid=element.guid,
            )
        cur.close()

    def commit(self) -> None:
        if self._conn:
            self._conn.commit()
            self._conn.close()
            self._conn = None

    def abort(self) -> None:
        if self._conn:
            self._conn.rollback()
            self._conn.close()
            self._conn = None

    @staticmethod
    def _to_sdo(geometry_geojson: Optional[str]):
        # TODO(PD-02): convertir GeoJSON -> SDO_GEOMETRY con el SRID corporativo.
        return None


class ArcPyEditor(GeodatabaseEditor):
    """Edición vía ArcPy respetando versionado y relationship classes."""

    def __init__(self, workspace: str):
        self._workspace = workspace  # conexión .sde
        self._editor: Any = None

    def begin_session(self, un_code: str) -> None:
        import arcpy  # import diferido (solo donde ArcGIS está licenciado)
        self._arcpy = arcpy
        self._editor = arcpy.da.Editor(self._workspace)
        self._editor.startEditing(False, True)  # with_undo, multiuser (versionado)
        self._editor.startOperation()
        self._un_code = un_code

    def apply(self, operation: str, element: Any) -> None:
        arcpy = self._arcpy
        fc = f"{self._workspace}/{element.element_type}"  # feature class por tipo
        if operation == "DELETE":
            with arcpy.da.UpdateCursor(fc, ["GlobalID"], f"GlobalID = '{element.guid}'") as cur:
                for _ in cur:
                    cur.deleteRow()
        elif operation == "CREATE":
            # TODO(PD-03): campos reales + geometría (GeoJSON -> arcpy.AsShape).
            with arcpy.da.InsertCursor(fc, ["GlobalID", "SHAPE@"]) as cur:
                cur.insertRow([element.guid, self._to_shape(element.geometry_geojson)])
        else:  # UPDATE
            with arcpy.da.UpdateCursor(fc, ["GlobalID", "SHAPE@"],
                                       f"GlobalID = '{element.guid}'") as cur:
                for row in cur:
                    row[1] = self._to_shape(element.geometry_geojson)
                    cur.updateRow(row)

    def commit(self) -> None:
        if self._editor:
            self._editor.stopOperation()
            self._editor.stopEditing(True)  # save_changes -> reconcile/post lo hace un job
            self._editor = None

    def abort(self) -> None:
        if self._editor:
            self._editor.abortOperation()
            self._editor.stopEditing(False)
            self._editor = None

    def _to_shape(self, geometry_geojson: Optional[str]):
        if not geometry_geojson:
            return None
        # TODO(PD-02): arcpy.AsShape(json.loads(geometry_geojson), esri_json=False)
        return self._arcpy.AsShape(json.loads(geometry_geojson))
