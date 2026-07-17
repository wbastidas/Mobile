"""Pruebas de asignación, borrado remoto y sincronización (RF-WEB-04/05/09, RF-SYNC)."""
import hashlib
import json

from app.core.config import settings
from tests.conftest import login


def _un_norte_id(client, headers):
    r = client.get("/api/v1/business-units", headers=headers)
    return next(u["id"] for u in r.json() if u["code"] == "UN-NORTE")


def _work_by_code(client, headers, code):
    r = client.get("/api/v1/works", headers=headers)
    return next(w for w in r.json() if w["code"] == code)


def _device_id(client, headers):
    r = client.get("/api/v1/devices", headers=headers)
    return r.json()[0]["id"]


def test_assignment_exclusivity_rn01(client, seeded):
    """RN-01: un trabajo no puede asignarse a dos dispositivos a la vez."""
    admin = login(client, "admin")
    un_norte = _un_norte_id(client, admin)
    device1 = _device_id(client, admin)
    # Segundo dispositivo en la misma UN.
    r = client.post("/api/v1/devices", headers=admin, json={
        "device_uid": "ANDROID-DEMO-002", "alias": "Tel Campo 02", "un_id": un_norte})
    device2 = r.json()["id"]

    work = _work_by_code(client, admin, "REV-2026-001")
    r = client.post("/api/v1/works/assign", headers=admin,
                    json={"device_id": device1, "work_ids": [work["id"]]})
    assert r.status_code == 200
    assert r.json()[0]["status"] == "ASSIGNED"

    # Reasignar a otro dispositivo sin retirar primero -> conflicto.
    r = client.post("/api/v1/works/assign", headers=admin,
                    json={"device_id": device2, "work_ids": [work["id"]]})
    assert r.status_code == 409


def test_multiple_works_one_device_rn02(client, seeded):
    """RN-02: un dispositivo puede tener múltiples trabajos."""
    admin = login(client, "admin")
    device = _device_id(client, admin)
    w1 = _work_by_code(client, admin, "REV-2026-001")
    w2 = _work_by_code(client, admin, "ORD-2026-014")
    r = client.post("/api/v1/works/assign", headers=admin,
                    json={"device_id": device, "work_ids": [w1["id"], w2["id"]]})
    assert r.status_code == 200
    assert len(r.json()) == 2


def test_remote_delete_frees_work_for_reassignment(client, seeded):
    """RF-WEB-05 + RF-WEB-04.7: borrado remoto confirmado libera el trabajo."""
    admin = login(client, "admin")
    device = _device_id(client, admin)
    work = _work_by_code(client, admin, "REV-2026-001")
    client.post("/api/v1/works/assign", headers=admin,
                json={"device_id": device, "work_ids": [work["id"]]})

    r = client.post("/api/v1/works/remote-delete", headers=admin,
                    json={"device_id": device, "work_ids": [work["id"]]})
    assert r.status_code == 202

    # El dispositivo (funcionario de campo) confirma el borrado.
    field = login(client, "campo.norte")
    r = client.post(f"/api/v1/sync/confirm-delete/{work['id']}?device_uid=ANDROID-DEMO-001",
                    headers=field)
    assert r.status_code == 200

    # El trabajo queda liberado (device_id nulo) y puede reasignarse.
    w = client.get(f"/api/v1/works/{work['id']}", headers=admin).json()
    assert w["device_id"] is None


def test_full_sync_flow(client, seeded):
    """Flujo pull -> upload -> verify -> consolidación (RF-SYNC, RF-MOV-10)."""
    admin = login(client, "admin")
    device = _device_id(client, admin)
    work = _work_by_code(client, admin, "REV-2026-001")
    client.post("/api/v1/works/assign", headers=admin,
                json={"device_id": device, "work_ids": [work["id"]]})

    field = login(client, "campo.norte")

    # Pull: el dispositivo descarga el trabajo y parámetros de calidad.
    r = client.get("/api/v1/sync/pull?device_uid=ANDROID-DEMO-001", headers=field)
    assert r.status_code == 200
    body = r.json()
    assert any(w["code"] == "REV-2026-001" for w in body["new_works"])
    assert body["quality_params_version"] == 1

    # Upload: sube el paquete con un elemento editado, sin fotos pendientes.
    payload = {
        "idempotency_key": "pkg-001",
        "work_id": work["id"],
        "device_uid": "ANDROID-DEMO-001",
        "schema_version": 1,
        "payload_json": json.dumps({"elements": [
            {"guid": "UN-NORTE-POSTE-0001", "element_type": "POSTE",
             "geometry_geojson": '{"type":"Point","coordinates":[-78.5,-0.2]}',
             "attributes": {"material": "HORMIGON", "altura_m": 12}}
        ]}),
        "validation_result": "APPROVED",
        "photos": [],
    }
    r = client.post("/api/v1/sync/upload", headers=field, json=payload)
    assert r.status_code == 200
    pkg_id = r.json()["package_id"]
    assert r.json()["duplicate"] is False

    # Idempotencia: reenviar el mismo paquete no duplica.
    r_dup = client.post("/api/v1/sync/upload", headers=field, json=payload)
    assert r_dup.json()["duplicate"] is True

    # Verify: verifica completitud y consolida.
    r = client.post(f"/api/v1/sync/verify/{pkg_id}", headers=field)
    assert r.status_code == 200, r.text
    assert r.json()["verified"] is True
    assert r.json()["status"] == "COMPLETED"

    # La bitácora del elemento registra la sincronización (RF-WEB-07).
    r = client.get("/api/v1/elements/UN-NORTE-POSTE-0001/log", headers=admin)
    assert r.status_code == 200
    assert any(e["event_type"] == "SYNC" for e in r.json())


def test_photo_chunk_upload_completes_sync(client, seeded, tmp_path):
    """RF-SYNC.3/4: subida por chunks + verificación de integridad por hash."""
    settings.PHOTO_STORAGE_DIR = str(tmp_path)  # aísla el almacenamiento en la prueba

    admin = login(client, "admin")
    device = _device_id(client, admin)
    work = _work_by_code(client, admin, "REV-2026-001")
    client.post("/api/v1/works/assign", headers=admin,
                json={"device_id": device, "work_ids": [work["id"]]})
    field = login(client, "campo.norte")

    content = b"contenido-de-foto-binaria-de-prueba-1234567890"
    half = len(content) // 2
    chunks = [content[:half], content[half:]]
    sha = hashlib.sha256(content).hexdigest()

    payload = {
        "idempotency_key": "pkg-chunks",
        "work_id": work["id"],
        "device_uid": "ANDROID-DEMO-001",
        "payload_json": json.dumps({"elements": []}),
        "validation_result": "APPROVED",
        "photos": [{"element_guid": "UN-NORTE-POSTE-0001", "gps_lat": -0.2, "gps_lon": -78.5,
                    "captured_at": "2026-07-17T10:00:00Z", "sha256": sha,
                    "size_bytes": len(content), "total_chunks": 2}],
    }
    r = client.post("/api/v1/sync/upload", headers=field, json=payload)
    pkg_id = r.json()["package_id"]
    assert sha in r.json()["missing_photos"]

    # Subir los dos chunks.
    for i, ch in enumerate(chunks):
        r = client.post(f"/api/v1/sync/photo/{sha}/chunk", headers=field,
                        params={"index": i, "total": 2},
                        files={"chunk": (f"part{i}", ch, "application/octet-stream")})
        assert r.status_code == 200, r.text
    assert r.json()["verified"] is True

    # Ahora la verificación del paquete debe completar y consolidar.
    r = client.post(f"/api/v1/sync/verify/{pkg_id}", headers=field)
    assert r.json()["verified"] is True
    assert r.json()["status"] == "COMPLETED"


def test_photo_chunk_integrity_failure(client, seeded, tmp_path):
    """RN-04: si el hash no coincide, la foto no se da por recibida."""
    settings.PHOTO_STORAGE_DIR = str(tmp_path)
    admin = login(client, "admin")
    device = _device_id(client, admin)
    work = _work_by_code(client, admin, "REV-2026-001")
    client.post("/api/v1/works/assign", headers=admin,
                json={"device_id": device, "work_ids": [work["id"]]})
    field = login(client, "campo.norte")

    declared_sha = hashlib.sha256(b"lo-esperado").hexdigest()
    payload = {
        "idempotency_key": "pkg-bad",
        "work_id": work["id"],
        "device_uid": "ANDROID-DEMO-001",
        "payload_json": json.dumps({"elements": []}),
        "validation_result": "APPROVED",
        "photos": [{"gps_lat": -0.2, "gps_lon": -78.5, "captured_at": "2026-07-17T10:00:00Z",
                    "sha256": declared_sha, "size_bytes": 10, "total_chunks": 1}],
    }
    pkg_id = client.post("/api/v1/sync/upload", headers=field, json=payload).json()["package_id"]

    # Se sube un contenido distinto al declarado -> integridad falla.
    r = client.post(f"/api/v1/sync/photo/{declared_sha}/chunk", headers=field,
                    params={"index": 0, "total": 1},
                    files={"chunk": ("part0", b"otro-contenido", "application/octet-stream")})
    assert r.json()["verified"] is False

    r = client.post(f"/api/v1/sync/verify/{pkg_id}", headers=field)
    assert r.json()["verified"] is False
    assert r.json()["status"] == "SYNC_PENDING"


def test_sync_pending_when_photo_missing(client, seeded):
    """RN-04: foto no recibida -> trabajo queda pendiente, no se termina."""
    admin = login(client, "admin")
    device = _device_id(client, admin)
    work = _work_by_code(client, admin, "REV-2026-001")
    client.post("/api/v1/works/assign", headers=admin,
                json={"device_id": device, "work_ids": [work["id"]]})
    field = login(client, "campo.norte")

    payload = {
        "idempotency_key": "pkg-photo",
        "work_id": work["id"],
        "device_uid": "ANDROID-DEMO-001",
        "payload_json": json.dumps({"elements": []}),
        "validation_result": "APPROVED",
        "photos": [{"element_guid": "UN-NORTE-POSTE-0001", "gps_lat": -0.2, "gps_lon": -78.5,
                    "captured_at": "2026-07-17T10:00:00Z", "sha256": "abc123",
                    "size_bytes": 2048, "total_chunks": 3}],
    }
    r = client.post("/api/v1/sync/upload", headers=field, json=payload)
    assert "abc123" in r.json()["missing_photos"]

    pkg_id = r.json()["package_id"]
    r = client.post(f"/api/v1/sync/verify/{pkg_id}", headers=field)
    assert r.json()["verified"] is False
    assert r.json()["status"] == "SYNC_PENDING"
