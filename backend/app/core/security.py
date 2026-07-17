"""Utilidades de seguridad: hashing de contraseñas y tokens JWT."""
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# pbkdf2_sha256: robusto y sin dependencias C frágiles. Se listan otros esquemas
# como verificables para permitir migración de hashes existentes.
pwd_context = CryptContext(schemes=["pbkdf2_sha256", "bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def validate_password_policy(password: str) -> Optional[str]:
    """Valida la política de contraseñas (RF-WEB-01.2).

    Devuelve un mensaje de error si no cumple, o None si es válida.
    """
    if len(password) < settings.PASSWORD_MIN_LENGTH:
        return f"La contraseña debe tener al menos {settings.PASSWORD_MIN_LENGTH} caracteres."
    if not any(c.islower() for c in password):
        return "La contraseña debe incluir al menos una minúscula."
    if not any(c.isupper() for c in password):
        return "La contraseña debe incluir al menos una mayúscula."
    if not any(c.isdigit() for c in password):
        return "La contraseña debe incluir al menos un dígito."
    if all(c.isalnum() for c in password):
        return "La contraseña debe incluir al menos un carácter especial."
    return None


def create_access_token(subject: str, extra_claims: Optional[dict[str, Any]] = None,
                        expires_minutes: Optional[int] = None) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=expires_minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload: dict[str, Any] = {"sub": str(subject), "exp": expire, "type": "access"}
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(subject: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(subject), "exp": expire, "type": "refresh"}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> Optional[dict[str, Any]]:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return None
