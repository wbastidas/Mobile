"""Dependencias de FastAPI: sesión, usuario actual y control de acceso (RBAC).

Implementa la segregación Matriz/UN a nivel de backend (RN-05, regla obligatoria
de la sección 2.1): los roles de ámbito UN nunca pueden ver ni operar datos de
otra UN.
"""
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.enums import GLOBAL_SCOPE_ROLES, OPERATOR_ROLES, Role
from app.core.security import decode_token
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_PREFIX}/auth/login", auto_error=False)


def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales inválidas o sesión expirada.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_exc
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise credentials_exc
    user_id = payload.get("sub")
    if not user_id:
        raise credentials_exc
    user = db.get(User, user_id)
    if not user or not user.active:
        raise credentials_exc
    return user


def _role(user: User) -> Role:
    return user.role if isinstance(user.role, Role) else Role(user.role)


def is_global_scope(user: User) -> bool:
    return _role(user) in GLOBAL_SCOPE_ROLES


def require_roles(*roles: Role):
    """Factory de dependencia que exige que el usuario tenga uno de los roles."""
    allowed = set(roles)

    def checker(user: User = Depends(get_current_user)) -> User:
        if _role(user) not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permisos para esta operación.",
            )
        return user

    return checker


def require_operator(user: User = Depends(get_current_user)) -> User:
    """Operadores/editores (Matriz o UN) y admin."""
    if _role(user) not in OPERATOR_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Requiere rol de operador/editor.",
        )
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if _role(user) != Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Requiere rol de Administrador del Sistema.",
        )
    return user


def enforce_un_scope(user: User, target_un_id: Optional[str]) -> None:
    """Verifica que un usuario de ámbito UN solo acceda a datos de su UN (RN-05).

    Lanza 403 si un rol UN intenta acceder a otra UN. Los roles Matriz pasan.
    """
    if is_global_scope(user):
        return
    if target_un_id is not None and target_un_id != user.un_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Fuera del ámbito de su unidad de negocio.",
        )


def scope_un_filter(user: User) -> Optional[str]:
    """UN a filtrar en consultas de lista: None para Matriz (ve todo)."""
    return None if is_global_scope(user) else user.un_id


def client_ip(request: Request) -> Optional[str]:
    if request.client:
        return request.client.host
    return None
