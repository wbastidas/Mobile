"""Novedades de calidad a nivel de regla (RF-WEB-09.2, RF-WEB-11.1)."""
import json

from tests.conftest import login


def _setup_assigned(client, admin):
    dev = client.get("/api/v1/devices", headers=admin).json()[0]["id"]
    work = next(w for w in client.get("/api/v1/works", headers=admin).json()
                if w["code"] == "REV-2026-001")
    client.post("/api/v1/works/assign", headers=admin,
                json={"device_id": dev, "work_ids": [work["id"]]})
    return work


def _report(n_required=1, n_range=1):
    issues = []
    for i in range(n_required):
        issues.append({"element_guid": f"P{i}", "element_type": "POSTE", "field": "material",
                       "rule_type": "required", "message": "obligatorio",
                       "expected": "un valor", "actual": None})
    for i in range(n_range):
        issues.append({"element_guid": f"P{i}", "element_type": "POSTE", "field": "altura_m",
                       "rule_type": "range", "message": "fuera de rango",
                       "expected": "<= 20", "actual": "40"})
    return {"result": "WITH_ISSUES", "issues": issues}


def _upload_with_issues(client, field, work_id, report, key="pkg-nov"):
    payload = {
        "idempotency_key": key, "work_id": work_id, "device_uid": "ANDROID-DEMO-001",
        "payload_json": json.dumps({"elements": []}),
        "validation_result": "WITH_ISSUES",
        "validation_report_json": json.dumps(report), "photos": [],
    }
    return client.post("/api/v1/sync/upload", headers=field, json=payload)


def test_novelties_persisted_and_listed(client, seeded):
    admin = login(client, "admin")
    work = _setup_assigned(client, admin)
    field = login(client, "campo.norte")

    r = _upload_with_issues(client, field, work["id"], _report(n_required=2, n_range=1))
    assert r.status_code == 200

    detail = client.get(f"/api/v1/quality/novelties?work_id={work['id']}", headers=admin)
    assert detail.status_code == 200
    rows = detail.json()
    assert len(rows) == 3
    assert {row["rule_type"] for row in rows} == {"required", "range"}


def test_novelties_by_rule_report_aggregates(client, seeded):
    admin = login(client, "admin")
    work = _setup_assigned(client, admin)
    field = login(client, "campo.norte")
    _upload_with_issues(client, field, work["id"], _report(n_required=3, n_range=1))

    rep = client.get("/api/v1/reports/quality-by-rule", headers=admin)
    assert rep.status_code == 200
    rows = rep.json()["rows"]
    required_row = next(r for r in rows if r["regla"] == "required")
    assert required_row["ocurrencias"] == 3
    # El reporte se ordena por ocurrencias descendente.
    assert rows[0]["ocurrencias"] >= rows[-1]["ocurrencias"]


def test_novelties_respect_un_segregation(client, seeded):
    admin = login(client, "admin")
    work = _setup_assigned(client, admin)
    field = login(client, "campo.norte")
    _upload_with_issues(client, field, work["id"], _report())

    # Un visualizador de UN Sur no debe ver novedades de UN Norte.
    sur = login(client, "view.sur")
    rows = client.get("/api/v1/quality/novelties", headers=sur).json()
    assert rows == []


def test_export_quality_by_rule(client, seeded):
    admin = login(client, "admin")
    work = _setup_assigned(client, admin)
    field = login(client, "campo.norte")
    _upload_with_issues(client, field, work["id"], _report(n_required=2, n_range=2))

    r = client.get("/api/v1/reports/quality-by-rule/export", headers=admin, params={"fmt": "xlsx"})
    assert r.status_code == 200
    assert r.content[:2] == b"PK"
