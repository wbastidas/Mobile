"""Pruebas de endurecimiento de seguridad (RNF-01)."""
import hashlib
import json

import pytest

from app.core.config import settings
from tests.conftest import login


def _assigned_work(client, admin):
    dev = client.get("/api/v1/devices", headers=admin).json()[0]["id"]
    work = next(w for w in client.get("/api/v1/works", headers=admin).json()
                if w["code"] == "REV-2026-001")
    client.post("/api/v1/works/assign", headers=admin,
                json={"device_id": dev, "work_ids": [work["id"]]})
    return work


def test_upload_rejects_malformed_sha256(client, seeded):
    """El esquema rechaza hashes que no sean SHA-256 hex (vector de traversal)."""
    admin = login(client, "admin")
    work = _assigned_work(client, admin)
    field = login(client, "campo.norte")

    payload = {
        "idempotency_key": "pkg-evil",
        "work_id": work["id"],
        "device_uid": "ANDROID-DEMO-001",
        "payload_json": json.dumps({"elements": []}),
        "validation_result": "APPROVED",
        "photos": [{"gps_lat": -0.2, "gps_lon": -78.5,
                    "captured_at": "2026-07-17T10:00:00Z",
                    "sha256": "../../../../etc/passwd",
                    "size_bytes": 10, "total_chunks": 1}],
    }
    r = client.post("/api/v1/sync/upload", headers=field, json=payload)
    assert r.status_code == 422


def test_chunk_endpoint_rejects_traversal_and_bad_indexes(client, seeded, tmp_path):
    settings.PHOTO_STORAGE_DIR = str(tmp_path)
    admin = login(client, "admin")
    _assigned_work(client, admin)
    field = login(client, "campo.norte")

    # Hash malformado en la URL -> 422 sin tocar disco.
    r = client.post("/api/v1/sync/photo/..%2F..%2Fetc/chunk", headers=field,
                    params={"index": 0, "total": 1},
                    files={"chunk": ("p", b"x", "application/octet-stream")})
    assert r.status_code in (404, 422)  # ruta inválida o formato rechazado

    good_sha = hashlib.sha256(b"x").hexdigest()
    # Índices fuera de rango -> 422.
    for index, total in [(-1, 2), (2, 2), (0, 0), (0, 10_001)]:
        r = client.post(f"/api/v1/sync/photo/{good_sha}/chunk", headers=field,
                        params={"index": index, "total": total},
                        files={"chunk": ("p", b"x", "application/octet-stream")})
        assert r.status_code == 422, (index, total)


def test_chunk_size_limit(client, seeded, tmp_path):
    """Un chunk mayor al máximo configurado se rechaza con 413."""
    settings.PHOTO_STORAGE_DIR = str(tmp_path)
    old_max = settings.UPLOAD_CHUNK_MAX_BYTES
    settings.UPLOAD_CHUNK_MAX_BYTES = 1024  # 1 KB para la prueba
    try:
        admin = login(client, "admin")
        work = _assigned_work(client, admin)
        field = login(client, "campo.norte")

        content = b"z" * 4096
        sha = hashlib.sha256(content).hexdigest()
        payload = {
            "idempotency_key": "pkg-big",
            "work_id": work["id"],
            "device_uid": "ANDROID-DEMO-001",
            "payload_json": json.dumps({"elements": []}),
            "validation_result": "APPROVED",
            "photos": [{"gps_lat": -0.2, "gps_lon": -78.5,
                        "captured_at": "2026-07-17T10:00:00Z", "sha256": sha,
                        "size_bytes": len(content), "total_chunks": 1}],
        }
        client.post("/api/v1/sync/upload", headers=field, json=payload)

        r = client.post(f"/api/v1/sync/photo/{sha}/chunk", headers=field,
                        params={"index": 0, "total": 1},
                        files={"chunk": ("p", content, "application/octet-stream")})
        assert r.status_code == 413
    finally:
        settings.UPLOAD_CHUNK_MAX_BYTES = old_max


def test_security_headers_present(client, seeded):
    r = client.get("/health")
    assert r.headers.get("X-Content-Type-Options") == "nosniff"
    assert r.headers.get("X-Frame-Options") == "DENY"
    assert r.headers.get("Referrer-Policy") == "no-referrer"


def test_refuses_default_secret_in_production():
    """La app no arranca en producción con el SECRET_KEY por defecto."""
    from app.main import create_app

    old_env = settings.APP_ENV
    settings.APP_ENV = "production"
    try:
        with pytest.raises(RuntimeError):
            create_app()
    finally:
        settings.APP_ENV = old_env


def test_storage_layer_rejects_bad_keys(tmp_path):
    """Defensa en profundidad: la capa de almacenamiento valida por sí misma."""
    from app.services import photo_storage

    settings.PHOTO_STORAGE_DIR = str(tmp_path)
    with pytest.raises(photo_storage.InvalidStorageKey):
        photo_storage.save_chunk("../escape", 0, 1, b"x")
    with pytest.raises(photo_storage.InvalidStorageKey):
        photo_storage.final_path("..", "a" * 64)
