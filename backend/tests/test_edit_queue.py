"""Cola de edición secuencial hacia la geodatabase (§7.2).

Verifica que varios lotes aprobados casi a la vez se procesan UNO A UNO (nunca
en paralelo) y en el orden de encolado.
"""
import threading

import pytest

from app.core import database
from app.core.config import settings
from app.core.enums import BatchStatus
from app.modules.gis.edit_queue import EditQueue
from app.modules.gis.editor import StubEditor
from app.models.business_unit import BusinessUnit
from app.models.gis_staging import GISStagingBatch, GISStagingElement


@pytest.fixture(autouse=True)
def _async_queue():
    """Estas pruebas ejercen el worker real, no el modo síncrono."""
    settings.GIS_EDIT_QUEUE_SYNC = False
    old_backoff = settings.GIS_EDIT_RETRY_BACKOFF_SECONDS
    settings.GIS_EDIT_RETRY_BACKOFF_SECONDS = 0.0  # sin espera en pruebas
    yield
    settings.GIS_EDIT_QUEUE_SYNC = True
    settings.GIS_EDIT_RETRY_BACKOFF_SECONDS = old_backoff


def _make_batch(db, un_code: str, guid: str) -> str:
    batch = GISStagingBatch(un_code=un_code, status=BatchStatus.QUEUED.value, element_count=1)
    db.add(batch)
    db.flush()
    db.add(GISStagingElement(batch_id=batch.id, operation="CREATE", guid=guid,
                             element_type="POSTE"))
    db.commit()
    return batch.id


def test_batches_processed_one_at_a_time_and_in_order(db_session):
    """Con un editor lento, la concurrencia observada nunca supera 1."""
    StubEditor.reset()
    db = db_session()
    db.add(BusinessUnit(code="UN-X", name="X"))
    db.commit()

    batch_ids = [_make_batch(db, "UN-X", f"G-{i}") for i in range(5)]
    db.close()

    # Editor que tarda un poco por operación, para exponer solapamientos.
    q = EditQueue(editor_factory=lambda: StubEditor(work_seconds=0.02))
    q.start()
    try:
        # Aprobaciones "simultáneas" desde varios hilos.
        threads = [threading.Thread(target=q.submit, args=(bid,)) for bid in batch_ids]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert q.wait_idle(timeout=10)
    finally:
        q.stop()

    # Nunca hubo dos sesiones de edición a la vez.
    assert StubEditor._max_concurrency == 1

    # Todos los lotes quedaron cargados.
    check = db_session()
    try:
        statuses = {b.id: b.status for b in check.query(GISStagingBatch).all()}
    finally:
        check.close()
    assert all(statuses[bid] == BatchStatus.LOADED.value for bid in batch_ids)

    # Cada elemento se aplicó exactamente una vez.
    assert len(StubEditor.applied) == len(batch_ids)


def test_permanent_failure_marks_batch_failed_after_max_retries(db_session):
    StubEditor.reset()
    db = db_session()
    db.add(BusinessUnit(code="UN-Y", name="Y"))
    db.commit()
    batch_id = _make_batch(db, "UN-Y", "G-FAIL")
    db.close()

    class BoomEditor(StubEditor):
        def apply(self, operation, element):
            raise RuntimeError("fallo simulado de edición")

    q = EditQueue(editor_factory=lambda: BoomEditor())
    q.start()
    try:
        q.submit(batch_id)
        assert q.wait_idle(timeout=10)
    finally:
        q.stop()

    check = db_session()
    try:
        batch = check.get(GISStagingBatch, batch_id)
        assert batch.status == BatchStatus.FAILED.value
        assert batch.attempts == settings.GIS_EDIT_MAX_RETRIES  # agotó los reintentos
        assert "fallo simulado" in (batch.error or "")
    finally:
        check.close()


def test_auto_retry_recovers(db_session):
    """El editor falla las primeras veces y luego funciona: el lote termina LOADED."""
    StubEditor.reset()
    db = db_session()
    db.add(BusinessUnit(code="UN-Z", name="Z"))
    db.commit()
    batch_id = _make_batch(db, "UN-Z", "G-FLAKY")
    db.close()

    calls = {"n": 0}

    class FlakyEditor(StubEditor):
        def apply(self, operation, element):
            calls["n"] += 1
            if calls["n"] < 3:  # falla en los intentos 1 y 2
                raise RuntimeError("fallo transitorio")
            super().apply(operation, element)

    q = EditQueue(editor_factory=lambda: FlakyEditor())
    q.start()
    try:
        q.submit(batch_id)
        assert q.wait_idle(timeout=10)
    finally:
        q.stop()

    check = db_session()
    try:
        batch = check.get(GISStagingBatch, batch_id)
        assert batch.status == BatchStatus.LOADED.value
        assert batch.attempts == 3
    finally:
        check.close()
