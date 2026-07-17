"""CRUD de unidades de negocio (RF-WEB-02.2)."""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import client_ip, get_current_user, require_admin, scope_un_filter
from app.core.enums import AuditAction
from app.models.business_unit import BusinessUnit
from app.models.user import User
from app.schemas.business_unit import BusinessUnitCreate, BusinessUnitOut, BusinessUnitUpdate
from app.services import audit

router = APIRouter(prefix="/business-units", tags=["business-units"])


@router.get("", response_model=list[BusinessUnitOut])
def list_units(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    q = db.query(BusinessUnit)
    un = scope_un_filter(user)
    if un is not None:  # rol UN solo ve su propia UN
        q = q.filter(BusinessUnit.id == un)
    return q.order_by(BusinessUnit.code).all()


@router.post("", response_model=BusinessUnitOut, status_code=status.HTTP_201_CREATED)
def create_unit(payload: BusinessUnitCreate, request: Request,
                db: Session = Depends(get_db), user: User = Depends(require_admin)):
    if db.query(BusinessUnit).filter(BusinessUnit.code == payload.code).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "Código de UN ya existe.")
    unit = BusinessUnit(**payload.model_dump())
    db.add(unit)
    db.flush()
    audit.record(db, action=AuditAction.CREATE.value, actor=user, entity_type="BusinessUnit",
                 entity_id=unit.id, new_values=payload.model_dump(), ip_address=client_ip(request))
    db.commit()
    db.refresh(unit)
    return unit


@router.patch("/{unit_id}", response_model=BusinessUnitOut)
def update_unit(unit_id: str, payload: BusinessUnitUpdate, request: Request,
                db: Session = Depends(get_db), user: User = Depends(require_admin)):
    unit = db.get(BusinessUnit, unit_id)
    if not unit:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "UN no encontrada.")
    old = {"name": unit.name, "active": unit.active}
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(unit, k, v)
    audit.record(db, action=AuditAction.UPDATE.value, actor=user, entity_type="BusinessUnit",
                 entity_id=unit.id, old_values=old, new_values=payload.model_dump(exclude_unset=True),
                 ip_address=client_ip(request))
    db.commit()
    db.refresh(unit)
    return unit
