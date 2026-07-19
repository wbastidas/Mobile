"""Cola de edición secuencial hacia la geodatabase corporativa (§7.2/7.4).

Motivación: varios trabajos pueden aprobarse casi al mismo tiempo, pero a una
geodatabase versionada (ArcSDE/Oracle) NO se le puede escribir en paralelo — una
sesión de edición bloquea la versión. Por eso los lotes aprobados se procesan
**uno tras otro** en una única cola FIFO.

Implementación: un worker en un hilo dedicado consume los lotes en orden de
encolado (`queue_seq`). Un lock de sesión (`_session_lock`) garantiza que, incluso
en modo síncrono (procesar en el hilo de la petición), solo una edición esté
activa a la vez.

En despliegue multi-nodo, este worker debe ejecutarse en UN solo proceso (o
respaldarse por un lock distribuido); la cola en BD (`queue_seq`) ya provee el
orden global.
"""
from __future__ import annotations

import queue
import threading
from typing import Callable, Optional

from app.core import database
from app.core.enums import BatchStatus
from app.models.gis_staging import GISStagingBatch


class EditQueue:
    def __init__(self, editor_factory: Optional[Callable[[], object]] = None):
        self._editor_factory = editor_factory
        self._q: "queue.Queue[Optional[str]]" = queue.Queue()
        self._session_lock = threading.Lock()  # una edición a la vez
        self._seq_lock = threading.Lock()
        self._seq = 0
        self._worker: Optional[threading.Thread] = None
        self._stop = threading.Event()
        self._idle = threading.Event()
        self._idle.set()

    def configure(self, editor_factory: Callable[[], object]) -> None:
        self._editor_factory = editor_factory

    def next_seq(self) -> int:
        with self._seq_lock:
            self._seq += 1
            return self._seq

    def start(self) -> None:
        if self._worker and self._worker.is_alive():
            return
        self._stop.clear()
        self._worker = threading.Thread(target=self._run, name="gis-edit-queue", daemon=True)
        self._worker.start()

    def stop(self) -> None:
        self._stop.set()
        self._q.put(None)
        if self._worker:
            self._worker.join(timeout=2)

    def submit(self, batch_id: str) -> None:
        """Encola un lote ya marcado QUEUED. En modo síncrono, lo procesa ya."""
        from app.core.config import settings
        if settings.GIS_EDIT_QUEUE_SYNC:
            self._process(batch_id)
        else:
            self._idle.clear()
            self._q.put(batch_id)

    def wait_idle(self, timeout: float = 10.0) -> bool:
        return self._idle.wait(timeout)

    def _run(self) -> None:
        while not self._stop.is_set():
            try:
                batch_id = self._q.get(timeout=0.2)
            except queue.Empty:
                if self._q.unfinished_tasks == 0:
                    self._idle.set()
                continue
            if batch_id is None:
                break
            try:
                self._process(batch_id)
            finally:
                self._q.task_done()
                if self._q.unfinished_tasks == 0:
                    self._idle.set()

    def _process(self, batch_id: str) -> None:
        # El lock serializa la sesión de edición contra la geodatabase.
        with self._session_lock:
            db = database.SessionLocal()
            try:
                batch = db.get(GISStagingBatch, batch_id)
                if not batch or batch.status != BatchStatus.QUEUED.value:
                    return
                batch.status = BatchStatus.PROCESSING.value
                db.commit()

                editor = (self._editor_factory or _fallback_factory)()
                editor.begin_session(batch.un_code)
                for el in sorted(batch.elements, key=lambda e: e.created_at):
                    editor.apply(el.operation, el)
                editor.commit()

                batch.status = BatchStatus.LOADED.value
                batch.error = None
                db.commit()
            except Exception as exc:  # noqa: BLE001 — se persiste el motivo
                db.rollback()
                failed = db.get(GISStagingBatch, batch_id)
                if failed:
                    failed.status = BatchStatus.FAILED.value
                    failed.error = str(exc)[:500]
                    db.commit()
            finally:
                db.close()


def _fallback_factory() -> object:
    from app.modules.gis.editor import default_editor_factory
    return default_editor_factory()


# Instancia global usada por la app (un único worker por proceso).
edit_queue = EditQueue()
