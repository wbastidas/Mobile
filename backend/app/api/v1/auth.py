"""Autenticación web y móvil (RF-WEB-01, RF-MOV-01)."""
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import client_ip, get_current_user, is_global_scope
from app.core.enums import AuditAction, AuthType, Role
from app.core.ratelimit import login_limiter
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)
from app.models.device import Device
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.schemas.auth import (
    CurrentUser,
    LoginRequest,
    MobileLoginRequest,
    RefreshRequest,
    Token,
)
from app.services import audit

router = APIRouter(prefix="/auth", tags=["auth"])


def _issue_tokens(db: Session, user: User) -> Token:
    """Emite access + refresh; el refresh se persiste (jti) para rotación."""
    claims = {"role": user.role, "un_id": user.un_id}
    record = RefreshToken(
        user_id=user.id,
        expires_at=datetime.now(timezone.utc)
        + timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES),
    )
    db.add(record)
    db.flush()
    return Token(
        access_token=create_access_token(user.id, extra_claims=claims),
        refresh_token=create_refresh_token(user.id, jti=record.id),
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


def _check_lock(user: User) -> None:
    locked_until = user.locked_until
    # Algunos backends (SQLite) devuelven datetimes naive; se asume UTC.
    if locked_until and locked_until.tzinfo is None:
        locked_until = locked_until.replace(tzinfo=timezone.utc)
    if locked_until and locked_until > datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="Cuenta bloqueada temporalmente por intentos fallidos.",
        )


def _register_failure(db: Session, user: User, request: Request) -> None:
    user.failed_login_attempts += 1
    if user.failed_login_attempts >= settings.MAX_FAILED_LOGIN_ATTEMPTS:
        user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=settings.LOCKOUT_MINUTES)
        user.failed_login_attempts = 0
    audit.record(db, action=AuditAction.LOGIN_FAILED.value, username=user.username,
                 entity_type="User", entity_id=user.id, ip_address=client_ip(request))
    db.commit()


@router.post("/login", response_model=Token)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    """Login web. Soporta LOCAL (usuario/clave) y CORPORATE (delegado)."""
    login_limiter.check(client_ip(request))  # límite por IP (RNF-01)
    user = db.query(User).filter(User.username == payload.username).first()
    if not user or not user.active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Usuario o contraseña inválidos.")
    _check_lock(user)

    if user.auth_type == AuthType.CORPORATE:
        # RF-WEB-01.1 / PD-05: delegar a AD/LDAP/SSO. Placeholder configurable.
        if not settings.CORPORATE_AUTH_ENABLED:
            raise HTTPException(
                status.HTTP_501_NOT_IMPLEMENTED,
                "Autenticación corporativa no configurada (PD-05).",
            )
        raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Delegación corporativa pendiente.")

    if not user.hashed_password or not verify_password(payload.password, user.hashed_password):
        _register_failure(db, user, request)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Usuario o contraseña inválidos.")

    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login_at = datetime.now(timezone.utc)
    audit.record(db, action=AuditAction.LOGIN.value, actor=user,
                 entity_type="User", entity_id=user.id, ip_address=client_ip(request))
    tokens = _issue_tokens(db, user)
    db.commit()
    return tokens


@router.post("/mobile/login", response_model=Token)
def mobile_login(payload: MobileLoginRequest, request: Request, db: Session = Depends(get_db)):
    """Login móvil: funcionario de campo + dispositivo autorizado (RF-MOV-01.2)."""
    login_limiter.check(client_ip(request))  # límite por IP (RNF-01)
    user = db.query(User).filter(User.username == payload.username).first()
    if not user or not user.active or user.role != Role.FIELD.value:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Credenciales de campo inválidas.")
    _check_lock(user)

    if not user.hashed_password or not verify_password(payload.password, user.hashed_password):
        _register_failure(db, user, request)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Credenciales de campo inválidas.")

    device = db.query(Device).filter(Device.device_uid == payload.device_uid).first()
    if not device or not device.active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Dispositivo no registrado o inactivo.")
    # La combinación funcionario+dispositivo debe estar vinculada y en la misma UN.
    if device.un_id != user.un_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Dispositivo no pertenece a su unidad de negocio.")
    if device.assigned_user_id not in (None, user.id):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Dispositivo vinculado a otro funcionario.")

    if device.assigned_user_id is None:
        device.assigned_user_id = user.id
    device.last_seen_at = datetime.now(timezone.utc)
    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login_at = datetime.now(timezone.utc)
    audit.record(db, action=AuditAction.LOGIN.value, actor=user, entity_type="Device",
                 entity_id=device.id, device_id=device.id, ip_address=client_ip(request))
    tokens = _issue_tokens(db, user)
    db.commit()
    return tokens


@router.post("/refresh", response_model=Token)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)):
    """Rotación de refresh tokens con detección de reuso (RNF-01).

    Cada refresh token es de un solo uso: al canjearlo se revoca y se emite uno
    nuevo. Presentar un token ya revocado se trata como robo/replay y revoca
    todos los tokens vigentes del usuario.
    """
    data = decode_token(payload.refresh_token)
    if not data or data.get("type") != "refresh" or not data.get("jti"):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Refresh token inválido.")

    record = db.get(RefreshToken, data["jti"])
    if not record or record.user_id != data.get("sub"):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Refresh token inválido.")

    if record.revoked:
        # Reuso detectado: revocar toda la familia de tokens del usuario.
        db.query(RefreshToken).filter(
            RefreshToken.user_id == record.user_id, RefreshToken.revoked.is_(False)
        ).update({RefreshToken.revoked: True})
        db.commit()
        raise HTTPException(status.HTTP_401_UNAUTHORIZED,
                            "Refresh token reutilizado; sesiones revocadas.")

    expires_at = record.expires_at
    if expires_at.tzinfo is None:  # SQLite devuelve naive; se asume UTC
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Refresh token expirado.")

    user = db.get(User, record.user_id)
    if not user or not user.active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Usuario inválido.")

    record.revoked = True
    tokens = _issue_tokens(db, user)
    new_data = decode_token(tokens.refresh_token) or {}
    record.replaced_by = new_data.get("jti")
    db.commit()
    return tokens


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(payload: RefreshRequest, db: Session = Depends(get_db)):
    """Cierre de sesión explícito (RF-WEB-01.4): revoca el refresh token."""
    data = decode_token(payload.refresh_token)
    if data and data.get("type") == "refresh" and data.get("jti"):
        record = db.get(RefreshToken, data["jti"])
        if record:
            record.revoked = True
            db.commit()


@router.get("/me", response_model=CurrentUser)
def me(user: User = Depends(get_current_user)):
    out = CurrentUser.model_validate(user)
    out.is_global_scope = is_global_scope(user)
    return out
