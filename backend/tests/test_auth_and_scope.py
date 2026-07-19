"""Pruebas de autenticación y segregación Matriz/UN (RF-WEB-01, RN-05)."""
from tests.conftest import login


def test_login_and_me(client, seeded):
    headers = login(client, "admin")
    r = client.get("/api/v1/auth/me", headers=headers)
    assert r.status_code == 200
    assert r.json()["role"] == "ADMIN"
    assert r.json()["is_global_scope"] is True


def test_login_wrong_password(client, seeded):
    r = client.post("/api/v1/auth/login", json={"username": "admin", "password": "malo"})
    assert r.status_code == 401


def test_account_lockout_after_failures(client, seeded):
    for _ in range(5):
        client.post("/api/v1/auth/login", json={"username": "op.norte", "password": "x"})
    # Sexto intento con la clave correcta debe estar bloqueado.
    r = client.post("/api/v1/auth/login", json={"username": "op.norte", "password": "Campo2026!"})
    assert r.status_code == 423


def test_un_scope_segregation_on_works(client, seeded):
    # op.norte (UN Norte) no debe ver trabajos de UN Sur.
    headers = login(client, "op.norte")
    r = client.get("/api/v1/works", headers=headers)
    assert r.status_code == 200
    uns = {w["un_id"] for w in r.json()}
    # Todos los trabajos visibles pertenecen a su UN.
    r_me = client.get("/api/v1/auth/me", headers=headers)
    my_un = r_me.json()["un_id"]
    assert uns <= {my_un}


def test_matriz_sees_all_works(client, seeded):
    headers = login(client, "op.matriz")
    r = client.get("/api/v1/works", headers=headers)
    assert r.status_code == 200
    # Matriz ve trabajos de más de una UN (Norte y Sur en el seed).
    uns = {w["un_id"] for w in r.json()}
    assert len(uns) >= 2


def test_viewer_cannot_create_work(client, seeded):
    headers = login(client, "view.sur")
    r = client.post("/api/v1/works", headers=headers, json={
        "code": "X-1", "title": "t", "work_type": "ORDEN_PUNTUAL", "un_id": "abc"})
    assert r.status_code == 403
