"""Autenticación corporativa (RF-WEB-01.1, PD-05).

El mecanismo real (AD/LDAP vs. SSO federado) depende de la infraestructura
disponible (pendiente PD-05). Se aísla tras la interfaz `CorporateAuthenticator`
para que el endpoint de login no dependa del proveedor concreto.

- `LdapAuthenticator`: valida usuario/clave contra Active Directory por LDAP(S)
  usando `ldap3` (dependencia opcional, import diferido).
- `DisabledAuthenticator`: por defecto; indica que la auth corporativa no está
  configurada (el login corporativo responde 501 hasta cerrar PD-05).

Para SSO (SAML/OIDC) el flujo es por redirección y se añade como otro
`CorporateAuthenticator` + endpoints de callback, sin tocar el login local.
"""
from __future__ import annotations

import abc


class CorporateAuthResult:
    def __init__(self, ok: bool, detail: str = ""):
        self.ok = ok
        self.detail = detail


class CorporateAuthenticator(abc.ABC):
    @property
    @abc.abstractmethod
    def enabled(self) -> bool: ...

    @abc.abstractmethod
    def authenticate(self, username: str, password: str) -> CorporateAuthResult: ...


class DisabledAuthenticator(CorporateAuthenticator):
    @property
    def enabled(self) -> bool:
        return False

    def authenticate(self, username: str, password: str) -> CorporateAuthResult:
        return CorporateAuthResult(False, "Autenticación corporativa no configurada (PD-05).")


class LdapAuthenticator(CorporateAuthenticator):
    """Valida credenciales contra AD/LDAP haciendo un bind con el usuario."""

    def __init__(self, server_uri: str, user_dn_template: str):
        # user_dn_template p.ej. "{username}@empresa.com" o
        # "uid={username},ou=usuarios,dc=empresa,dc=com".
        self._server_uri = server_uri
        self._user_dn_template = user_dn_template

    @property
    def enabled(self) -> bool:
        return bool(self._server_uri)

    def authenticate(self, username: str, password: str) -> CorporateAuthResult:
        if not password:
            return CorporateAuthResult(False, "Contraseña vacía.")
        try:
            import ldap3  # import diferido (dependencia opcional)
        except ImportError:
            return CorporateAuthResult(False, "Cliente LDAP no instalado en el servidor.")

        server = ldap3.Server(self._server_uri, use_ssl=self._server_uri.startswith("ldaps"))
        user_dn = self._user_dn_template.format(username=username)
        try:
            conn = ldap3.Connection(server, user=user_dn, password=password, auto_bind=True)
            conn.unbind()
            return CorporateAuthResult(True, "Autenticado contra el dominio.")
        except Exception:  # noqa: BLE001 — no filtrar detalle del bind fallido
            return CorporateAuthResult(False, "Credenciales corporativas inválidas.")


def get_corporate_authenticator() -> CorporateAuthenticator:
    from app.core.config import settings
    if settings.CORPORATE_AUTH_ENABLED and settings.LDAP_SERVER_URI:
        return LdapAuthenticator(settings.LDAP_SERVER_URI, settings.LDAP_USER_DN_TEMPLATE)
    return DisabledAuthenticator()
