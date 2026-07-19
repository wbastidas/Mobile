"""Pruebas de reportería y exportación (RF-WEB-11)."""
from tests.conftest import login


def test_report_catalog(client, seeded):
    headers = login(client, "op.matriz")
    r = client.get("/api/v1/reports", headers=headers)
    assert r.status_code == 200
    keys = {x["key"] for x in r.json()}
    assert {"works-summary", "productivity", "cycle-times", "quality-novelties"} <= keys


def test_works_summary_report(client, seeded):
    headers = login(client, "op.matriz")
    r = client.get("/api/v1/reports/works-summary", headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert body["count"] >= 1
    assert "total" in body["rows"][0]


def test_report_respects_un_segregation(client, seeded):
    # op.norte (UN Norte) solo ve filas de su UN en el resumen.
    headers = login(client, "op.norte")
    r = client.get("/api/v1/reports/works-summary", headers=headers)
    uns = {row["unidad_negocio"] for row in r.json()["rows"]}
    assert uns <= {"UN-NORTE"}


def test_export_xlsx(client, seeded):
    headers = login(client, "op.matriz")
    r = client.get("/api/v1/reports/works-summary/export", headers=headers, params={"fmt": "xlsx"})
    assert r.status_code == 200
    assert "spreadsheetml" in r.headers["content-type"]
    assert r.content[:2] == b"PK"  # los .xlsx son ZIP


def test_export_csv_and_pdf(client, seeded):
    headers = login(client, "op.matriz")
    csv_r = client.get("/api/v1/reports/productivity/export", headers=headers, params={"fmt": "csv"})
    assert csv_r.status_code == 200 and "csv" in csv_r.headers["content-type"]

    pdf_r = client.get("/api/v1/reports/cycle-times/export", headers=headers, params={"fmt": "pdf"})
    assert pdf_r.status_code == 200
    assert pdf_r.content[:4] == b"%PDF"


def test_unknown_report_404(client, seeded):
    headers = login(client, "op.matriz")
    r = client.get("/api/v1/reports/no-existe", headers=headers)
    assert r.status_code == 404
