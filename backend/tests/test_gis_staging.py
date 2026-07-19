"""Consolidación por staging reversible hacia ArcSDE/Oracle (§7.2/7.4)."""
import json

from tests.conftest import login


def _sync_a_work(client):
    """Asigna y sincroniza REV-2026-001 con un elemento; devuelve (admin, work)."""
    admin = login(client, "admin")
    dev = client.get("/api/v1/devices", headers=admin).json()[0]["id"]
    work = next(w for w in client.get("/api/v1/works", headers=admin).json()
                if w["code"] == "REV-2026-001")
    client.post("/api/v1/works/assign", headers=admin,
                json={"device_id": dev, "work_ids": [work["id"]]})
    field = login(client, "campo.norte")
    payload = {
        "idempotency_key": "pkg-gis",
        "work_id": work["id"],
        "device_uid": "ANDROID-DEMO-001",
        "payload_json": json.dumps({"elements": [
            {"guid": "UN-NORTE-POSTE-0001", "element_type": "POSTE",
             "geometry_geojson": '{"type":"Point","coordinates":[-78.5,-0.2]}',
             "attributes": {"material": "HORMIGON", "altura_m": 12}}
        ]}),
        "validation_result": "APPROVED",
        "photos": [],
    }
    pkg = client.post("/api/v1/sync/upload", headers=field, json=payload).json()["package_id"]
    r = client.post(f"/api/v1/sync/verify/{pkg}", headers=field)
    assert r.json()["verified"] is True
    return admin, work


def test_sync_creates_pending_staging_batch(client, seeded):
    admin, work = _sync_a_work(client)
    batches = client.get("/api/v1/gis/staging", headers=admin).json()
    assert len(batches) == 1
    b = batches[0]
    assert b["status"] == "PENDING_REVIEW"
    assert b["work_id"] == work["id"]
    assert b["element_count"] == 1

    detail = client.get(f"/api/v1/gis/staging/{b['id']}", headers=admin).json()
    # GUID y atributos preservados en el lote (§7.2).
    assert detail["elements"][0]["guid"] == "UN-NORTE-POSTE-0001"
    assert "HORMIGON" in detail["elements"][0]["attributes_json"]


def test_approve_batch_enqueues_and_loads(client, seeded):
    admin, _ = _sync_a_work(client)
    batch_id = client.get("/api/v1/gis/staging", headers=admin).json()[0]["id"]

    # En pruebas la cola procesa en línea: aprobar deja el lote LOADED.
    r = client.post(f"/api/v1/gis/staging/{batch_id}/approve", headers=admin)
    assert r.status_code == 200
    detail = client.get(f"/api/v1/gis/staging/{batch_id}", headers=admin).json()
    assert detail["status"] == "LOADED"

    # Un lote ya cargado no puede reaprobarse.
    r = client.post(f"/api/v1/gis/staging/{batch_id}/approve", headers=admin)
    assert r.status_code == 409

    # Queda auditado como CONSOLIDATE sobre el lote.
    audit_rows = client.get("/api/v1/audit", headers=admin,
                            params={"entity_type": "GISStagingBatch"}).json()
    assert any(a["entity_id"] == batch_id for a in audit_rows)


def test_retry_only_allowed_on_failed(client, seeded):
    admin, _ = _sync_a_work(client)
    batch_id = client.get("/api/v1/gis/staging", headers=admin).json()[0]["id"]
    client.post(f"/api/v1/gis/staging/{batch_id}/approve", headers=admin)  # -> LOADED
    r = client.post(f"/api/v1/gis/staging/{batch_id}/retry", headers=admin)
    assert r.status_code == 409  # un lote cargado no se reintenta


def test_rollback_batch(client, seeded):
    admin, _ = _sync_a_work(client)
    batch_id = client.get("/api/v1/gis/staging", headers=admin).json()[0]["id"]
    r = client.post(f"/api/v1/gis/staging/{batch_id}/rollback", headers=admin)
    assert r.json()["status"] == "ROLLED_BACK"


def test_staging_respects_un_segregation(client, seeded):
    _sync_a_work(client)  # lote de UN-NORTE
    sur = login(client, "view.sur")
    assert client.get("/api/v1/gis/staging", headers=sur).json() == []
