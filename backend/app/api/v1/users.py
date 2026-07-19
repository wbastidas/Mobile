"""CRUD de usuarios con asignación de rol y UN (RF-WEB-02.1)."""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import client_ip, require_admin
from app.core.enums import AuditAction, AuthType, GLOBAL_SCOPE_ROLES, Role
from app.core.security import hash_password, validate_password_policy
from app.models.user import User
from app.schemas.user import PasswordChange, UserCreate, UserOut, UserUpdate
from app.services import audit

router = APIRouter(prefix="/users", tags=["users"])


def _validate_scope(role: Role, un_id):
    """Coherencia rol/UN: roles globales sin UN obligatoria; roles UN la requieren."""
    if role in GLOBAL_SCOPE_ROLES:
        return
    if not un_id:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY,
                            "Los roles de ámbito UN requieren una unidad de negocio.")


@router.get("", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    return db.query(User).order_by(User.username).all()


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, request: Request,
                db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    if db.query(User).filter(User.username == payload.username).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "Nombre de usuario ya existe.")
    _validate_scope(payload.role, payload.un_id)

    hashed = None
    if payload.auth_type == AuthType.LOCAL:
        if not payload.password:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY,
                                "Contraseña requerida para usuarios locales.")
        err = validate_password_policy(payload.password)
        if err:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, err)
        hashed = hash_password(payload.password)

    data = payload.model_dump(exclude={"password"})
    user = User(**data, hashed_password=hashed)
    db.add(user)
    db.flush()
    audit.record(db, action=AuditAction.CREATE.value, actor=admin, entity_type="User",
                 entity_id=user.id, new_values={"username": user.username, "role": user.role},
                 ip_address=client_ip(request))
    db.commit()
    db.refresh(user)
    return user


@router.patch("/{user_id}", response_model=UserOut)
def update_user(user_id: str, payload: UserUpdate, request: Request,
                db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Usuario no encontrado.")
    updates = payload.model_dump(exclude_unset=True)
    new_role = updates.get("role", Role(user.role) if not isinstance(user.role, Role) else user.role)
    new_un = updates.get("un_id", user.un_id)
    _validate_scope(new_role if isinstance(new_role, Role) else Role(new_role), new_un)
    for k, v in updates.items():
        setattr(user, k, v)
    audit.record(db, action=AuditAction.UPDATE.value, actor=admin, entity_type="User",
                 entity_id=user.id, new_values=updates, ip_address=client_ip(request))
    db.commit()
    db.refresh(user)
    return user


@router.post("/{user_id}/password", status_code=status.HTTP_204_NO_CONTENT)
def set_password(user_id: str, payload: PasswordChange, request: Request,
                 db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Usuario no encontrado.")
    if user.auth_type != AuthType.LOCAL:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Solo usuarios locales tienen contraseña.")
    err = validate_password_policy(payload.new_password)
    if err:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, err)
    user.hashed_password = hash_password(payload.new_password)
    user.failed_login_attempts = 0
    user.locked_until = None
    audit.record(db, action=AuditAction.UPDATE.value, actor=admin, entity_type="User",
                 entity_id=user.id, new_values={"password": "***"}, ip_address=client_ip(request))
    db.commit()
