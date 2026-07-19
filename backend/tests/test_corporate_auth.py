"""Autenticación corporativa (RF-WEB-01.1, PD-05)."""
from app.core.config import settings
from app.core.enums import AuthType, Role
from app.core.security import hash_password
from app.models.user import User
from app.modules.corporate_auth import (
    DisabledAuthenticator,
    LdapAuthenticator,
    get_corporate_authenticator,
)


def _make_corp_user(db_session):
    db = db_session()
    try:
        u = User(username="corp.user", full_name="Corporativo", role=Role.OPERATOR_MATRIZ,
                 auth_type=AuthType.CORPORATE, hashed_password=None)
        db.add(u)
        db.commit()
    finally:
        db.close()


def test_disabled_by_default():
    assert isinstance(get_corporate_authenticator(), DisabledAuthenticator)


def test_selects_ldap_when_configured():
    settings.CORPORATE_AUTH_ENABLED = True
    settings.LDAP_SERVER_URI = "ldaps://ad.empresa.com"
    try:
        auth = get_corporate_authenticator()
        assert isinstance(auth, LdapAuthenticator)
        assert auth.enabled is True
    finally:
        settings.CORPORATE_AUTH_ENABLED = False
        settings.LDAP_SERVER_URI = ""


def test_corporate_login_501_when_not_configured(client, seeded, db_session):
    _make_corp_user(db_session)
    r = client.post("/api/v1/auth/login", json={"username": "corp.user", "password": "x"})
    assert r.status_code == 501


def test_corporate_login_delegates_to_authenticator(client, seeded, db_session, monkeypatch):
    _make_corp_user(db_session)
    settings.CORPORATE_AUTH_ENABLED = True
    settings.LDAP_SERVER_URI = "ldaps://ad.empresa.com"

    # Simula un bind LDAP exitoso sin servidor real.
    from app.modules import corporate_auth

    class OkAuth(corporate_auth.CorporateAuthenticator):
        @property
        def enabled(self):
            return True

        def authenticate(self, username, password):
            return corporate_auth.CorporateAuthResult(password == "correcta")

    monkeypatch.setattr(corporate_auth, "get_corporate_authenticator", lambda: OkAuth())
    monkeypatch.setattr("app.api.v1.auth.get_corporate_authenticator", lambda: OkAuth())
    try:
        bad = client.post("/api/v1/auth/login", json={"username": "corp.user", "password": "mala"})
        assert bad.status_code == 401
        ok = client.post("/api/v1/auth/login", json={"username": "corp.user", "password": "correcta"})
        assert ok.status_code == 200
        assert "access_token" in ok.json()
    finally:
        settings.CORPORATE_AUTH_ENABLED = False
        settings.LDAP_SERVER_URI = ""
