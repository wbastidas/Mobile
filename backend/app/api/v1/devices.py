"""Registro y gestión de dispositivos móviles autorizados (RF-WEB-02.3)."""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import (
    client_ip,
    enforce_un_scope,
    get_current_user,
    require_operator,
    scope_un_filter,
)
from app.core.enums import AuditAction
from app.models.device import Device
from app.models.user import User
from app.schemas.device import DeviceCreate, DeviceOut, DeviceUpdate
from app.services import audit

router = APIRouter(prefix="/devices", tags=["devices"])


@router.get("", response_model=list[DeviceOut])
def list_devices(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    q = db.query(Device)
    un = scope_un_filter(user)
    if un is not None:
        q = q.filter(Device.un_id == un)
    return q.order_by(Device.alias).all()


@router.post("", response_model=DeviceOut, status_code=status.HTTP_201_CREATED)
def register_device(payload: DeviceCreate, request: Request,
                    db: Session = Depends(get_db), user: User = Depends(require_operator)):
    enforce_un_scope(user, payload.un_id)
    if db.query(Device).filter(Device.device_uid == payload.device_uid).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "Dispositivo ya registrado.")
    device = Device(**payload.model_dump())
    db.add(device)
    db.flush()
    audit.record(db, action=AuditAction.CREATE.value, actor=user, entity_type="Device",
                 entity_id=device.id, new_values=payload.model_dump(), un_id=device.un_id,
                 ip_address=client_ip(request))
    db.commit()
    db.refresh(device)
    return device


@router.patch("/{device_id}", response_model=DeviceOut)
def update_device(device_id: str, payload: DeviceUpdate, request: Request,
                  db: Session = Depends(get_db), user: User = Depends(require_operator)):
    device = db.get(Device, device_id)
    if not device:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Dispositivo no encontrado.")
    enforce_un_scope(user, device.un_id)
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(device, k, v)
    audit.record(db, action=AuditAction.UPDATE.value, actor=user, entity_type="Device",
                 entity_id=device.id, new_values=payload.model_dump(exclude_unset=True),
                 un_id=device.un_id, ip_address=client_ip(request))
    db.commit()
    db.refresh(device)
    return device
