"""Operaciones CRUD de campo e histórico por usuario/trabajo."""
import json

from tests.conftest import login


def _assign(client, admin):
    dev = client.get("/api/v1/devices", headers=admin).json()[0]["id"]
    work = next(w for w in client.get("/api/v1/works", headers=admin).json()
                if w["code"] == "REV-2026-001")
    client.post("/api/v1/works/assign", headers=admin,
                json={"device_id": dev, "work_ids": [work["id"]]})
    return work


def _sync(client, field, work_id, elements, key="pk"):
    payload = {
        "idempotency_key": key, "work_id": work_id, "device_uid": "ANDROID-DEMO-001",
        "payload_json": json.dumps({"elements": elements}),
        "validation_result": "APPROVED", "photos": [],
    }
    pkg = client.post("/api/v1/sync/upload", headers=field, json=payload).json()["package_id"]
    return client.post(f"/api/v1/sync/verify/{pkg}", headers=field).json()


def test_create_update_delete_recorded_in_history(client, seeded):
    admin = login(client, "admin")
    work = _assign(client, admin)
    field = login(client, "campo.norte")

    elements = [
        # UN-NORTE-POSTE-0001 ya existe (venía del sector) -> UPDATE.
        {"guid": "UN-NORTE-POSTE-0001", "element_type": "POSTE",
         "attributes": {"material": "METAL"}},
        # nuevo -> CREATE.
        {"guid": "UN-NORTE-POSTE-NEW", "element_type": "POSTE", "is_new": True,
         "attributes": {"material": "MADERA"}},
        # marcado eliminado -> DELETE.
        {"guid": "UN-NORTE-LUM-0001", "element_type": "LUMINARIA", "deleted": True,
         "attributes": {}},
    ]
    r = _sync(client, field, work["id"], elements)
    assert r["verified"] is True

    changes = client.get("/api/v1/history/changes", headers=admin,
                         params={"work_id": work["id"]}).json()
    by_op = {c["element_guid"]: c["operation"] for c in changes}
    assert by_op["UN-NORTE-POSTE-0001"] == "UPDATE"
    assert by_op["UN-NORTE-POSTE-NEW"] == "CREATE"
    assert by_op["UN-NORTE-LUM-0001"] == "DELETE"
    # Todas atribuidas al funcionario que las hizo.
    assert all(c["username"] == "campo.norte" for c in changes)


def test_history_summary_counts_per_user(client, seeded):
    admin = login(client, "admin")
    work = _assign(client, admin)
    field = login(client, "campo.norte")
    _sync(client, field, work["id"], [
        {"guid": "A", "element_type": "POSTE", "is_new": True, "attributes": {}},
        {"guid": "B", "element_type": "POSTE", "is_new": True, "attributes": {}},
        {"guid": "UN-NORTE-POSTE-0001", "element_type": "POSTE", "attributes": {"material": "METAL"}},
    ])
    summary = client.get("/api/v1/history/summary", headers=admin,
                         params={"work_id": work["id"]}).json()
    row = next(r for r in summary if r["funcionario"] == "campo.norte")
    assert row["CREATE"] == 2
    assert row["UPDATE"] == 1


def test_delete_marks_element_and_stages_delete_operation(client, seeded):
    admin = login(client, "admin")
    work = _assign(client, admin)
    field = login(client, "campo.norte")
    _sync(client, field, work["id"], [
        {"guid": "UN-NORTE-POSTE-0001", "element_type": "POSTE", "deleted": True, "attributes": {}},
    ])
    # El lote de staging registra la operación DELETE.
    batch = client.get("/api/v1/gis/staging", headers=admin).json()[0]
    detail = client.get(f"/api/v1/gis/staging/{batch['id']}", headers=admin).json()
    ops = {e["guid"]: e["operation"] for e in detail["elements"]}
    assert ops["UN-NORTE-POSTE-0001"] == "DELETE"


def test_history_respects_un_segregation(client, seeded):
    admin = login(client, "admin")
    work = _assign(client, admin)
    field = login(client, "campo.norte")
    _sync(client, field, work["id"], [
        {"guid": "UN-NORTE-POSTE-0001", "element_type": "POSTE", "attributes": {}},
    ])
    sur = login(client, "view.sur")  # UN Sur no ve cambios de UN Norte
    assert client.get("/api/v1/history/changes", headers=sur).json() == []
