"""Rotación/revocación de refresh tokens y límite por IP (RNF-01)."""
from app.core.ratelimit import login_limiter


def _login(client, username="admin", password="Campo2026!"):
    r = client.post("/api/v1/auth/login", json={"username": username, "password": password})
    assert r.status_code == 200, r.text
    return r.json()


def test_refresh_rotates_and_old_token_is_single_use(client, seeded):
    tokens = _login(client)

    # Primer canje: OK y entrega un refresh distinto.
    r1 = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert r1.status_code == 200
    assert r1.json()["refresh_token"] != tokens["refresh_token"]

    # Reusar el token ya canjeado: 401 (detección de reuso).
    r2 = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert r2.status_code == 401


def test_reuse_revokes_whole_family(client, seeded):
    """Tras detectar reuso, incluso el token nuevo de la cadena queda revocado."""
    tokens = _login(client)
    rotated = client.post("/api/v1/auth/refresh",
                          json={"refresh_token": tokens["refresh_token"]}).json()
    # Ataque: replay del token viejo -> revoca la familia completa.
    client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    # El token "bueno" más reciente también queda inservible.
    r = client.post("/api/v1/auth/refresh", json={"refresh_token": rotated["refresh_token"]})
    assert r.status_code == 401


def test_logout_revokes_refresh(client, seeded):
    tokens = _login(client)
    r = client.post("/api/v1/auth/logout", json={"refresh_token": tokens["refresh_token"]})
    assert r.status_code == 204
    r = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert r.status_code == 401


def test_login_rate_limit_per_ip(client, seeded):
    login_limiter.reset()
    old_max = login_limiter.max_requests
    login_limiter.max_requests = 3
    try:
        for _ in range(3):
            client.post("/api/v1/auth/login", json={"username": "nadie", "password": "x"})
        r = client.post("/api/v1/auth/login", json={"username": "nadie", "password": "x"})
        assert r.status_code == 429
    finally:
        login_limiter.max_requests = old_max
        login_limiter.reset()
