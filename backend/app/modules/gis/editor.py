"""Editor de la geodatabase corporativa (§7.2, PD-02).

Aísla la escritura física a ArcSDE/Oracle. La ruta PRIORITARIA es la edición vía
Python (ArcPy sobre una sesión de edición de la geodatabase, o `python-oracledb`
según el mecanismo que cierre PD-02). Aquí se define el contrato; `StubEditor`
lo simula para desarrollo y pruebas.

Contrato de una sesión de edición (equivalente a `arcpy.da.Editor`):
    begin_session(un_code) -> apply(op, element) * N -> commit()  |  abort()

La cola de edición (`edit_queue`) garantiza que solo UNA sesión esté activa a la
vez; este editor no necesita preocuparse por concurrencia.
"""
from __future__ import annotations

import abc
import threading
import time
from typing import Any, List, Tuple


class GeodatabaseEditor(abc.ABC):
    @abc.abstractmethod
    def begin_session(self, un_code: str) -> None: ...

    @abc.abstractmethod
    def apply(self, operation: str, element: Any) -> None:
        """Aplica CREATE/UPDATE/DELETE de un elemento preservando su GUID."""

    @abc.abstractmethod
    def commit(self) -> None: ...

    def abort(self) -> None:  # opcional
        pass


class StubEditor(GeodatabaseEditor):
    """Editor simulado. Registra las operaciones y vigila que nunca haya dos
    sesiones de edición simultáneas (invariante que la cola debe garantizar)."""

    # Estado de clase para poder observar la concurrencia en pruebas.
    _concurrency = 0
    _max_concurrency = 0
    _cc_lock = threading.Lock()
    applied: List[Tuple[str, str]] = []  # (operation, guid) en orden de proceso

    def __init__(self, work_seconds: float = 0.0):
        self._work_seconds = work_seconds

    def begin_session(self, un_code: str) -> None:
        with StubEditor._cc_lock:
            StubEditor._concurrency += 1
            StubEditor._max_concurrency = max(
                StubEditor._max_concurrency, StubEditor._concurrency
            )
        self._un_code = un_code

    def apply(self, operation: str, element: Any) -> None:
        if self._work_seconds:
            time.sleep(self._work_seconds)  # simula el costo de la edición
        StubEditor.applied.append((operation, element.guid))

    def commit(self) -> None:
        with StubEditor._cc_lock:
            StubEditor._concurrency -= 1

    def abort(self) -> None:
        with StubEditor._cc_lock:
            StubEditor._concurrency = max(0, StubEditor._concurrency - 1)

    @classmethod
    def reset(cls) -> None:
        cls._concurrency = 0
        cls._max_concurrency = 0
        cls.applied = []


def default_editor_factory() -> GeodatabaseEditor:
    """Selecciona el editor físico según la configuración (PD-02).

    El editor real (Oracle/ArcPy) se activa por variable de entorno; por defecto
    se usa el stub, para no exigir Oracle/ArcGIS en entornos donde no aplican.
    """
    from app.core.config import settings

    if settings.GIS_EDITOR == "oracle":
        from app.modules.gis.editors_real import OracleSdeEditor
        return OracleSdeEditor(settings.ORACLE_DSN, settings.ORACLE_USER, settings.ORACLE_PASSWORD)
    if settings.GIS_EDITOR == "arcpy":
        from app.modules.gis.editors_real import ArcPyEditor
        return ArcPyEditor(settings.ARCPY_WORKSPACE)
    return StubEditor()
