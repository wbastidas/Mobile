"""Trabajos: creación, listado, asignación y borrado remoto (RF-WEB-03/04/05)."""
import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import (
    client_ip,
    enforce_un_scope,
    get_current_user,
    require_operator,
    scope_un_filter,
)
from app.core.enums import AuditAction, RemoteDeleteStatus, WorkStatus, WorkType
from app.models.business_unit import BusinessUnit
from app.models.device import Device
from app.models.element import WorkElement
from app.models.sync import RemoteDeleteOrder
from app.models.user import User
from app.models.work import Work
from app.modules.gis.adapter import get_gis_adapter
from app.schemas.work import (
    AssignRequest,
    RemoteDeleteRequest,
    WorkCreate,
    WorkDetailOut,
    WorkOut,
    WorkUpdate,
)
from app.services import audit

router = APIRouter(prefix="/works", tags=["works"])


def _get_work_or_404(db: Session, work_id: str) -> Work:
    work = db.get(Work, work_id)
    if not work:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Trabajo no encontrado.")
    return work


@router.get("", response_model=list[WorkOut])
def list_works(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    status_filter: str | None = Query(None, alias="status"),
    work_type: WorkType | None = None,
    device_id: str | None = None,
):
    q = db.query(Work)
    un = scope_un_filter(user)
    if un is not None:  # segregación (RN-05)
        q = q.filter(Work.un_id == un)
    if status_filter:
        q = q.filter(Work.status == status_filter)
    if work_type:
        q = q.filter(Work.work_type == work_type)
    if device_id:
        q = q.filter(Work.device_id == device_id)
    return q.order_by(Work.created_at.desc()).all()


@router.get("/{work_id}", response_model=WorkDetailOut)
def get_work(work_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    work = _get_work_or_404(db, work_id)
    enforce_un_scope(user, work.un_id)
    return work


@router.post("", response_model=WorkDetailOut, status_code=status.HTTP_201_CREATED)
def create_work(payload: WorkCreate, request: Request,
                db: Session = Depends(get_db), user: User = Depends(require_operator)):
    """Crea un trabajo. Extrae geometría+atributos desde la geodatabase (§7.1)."""
    enforce_un_scope(user, payload.un_id)
    un = db.get(BusinessUnit, payload.un_id)
    if not un:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "UN inválida.")
    if db.query(Work).filter(Work.code == payload.code).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "Código de trabajo ya existe.")

    work = Work(
        code=payload.code,
        title=payload.title,
        description=payload.description,
        work_type=payload.work_type,
        un_id=payload.un_id,
        schema_version=payload.schema_version,
        sector_geojson=payload.sector_geojson,
        status=WorkStatus.CREATED,
    )
    db.add(work)
    db.flush()

    # Empaquetado de elementos (RF-WEB-04.5): explícitos o extraídos del GIS.
    gis = get_gis_adapter()
    if payload.elements:
        for el in payload.elements:
            db.add(WorkElement(work_id=work.id, element_guid=el.element_guid,
                               geometry_geojson=el.geometry_geojson,
                               attributes_json=el.attributes_json))
    elif payload.work_type == WorkType.REVISION_RED and payload.sector_geojson:
        for e in gis.extract_by_sector(un.code, payload.sector_geojson):
            db.add(WorkElement(work_id=work.id, element_guid=e.guid,
                               geometry_geojson=e.geometry_geojson,
                               attributes_json=json.dumps(e.attributes, ensure_ascii=False)))

    audit.record(db, action=AuditAction.CREATE.value, actor=user, entity_type="Work",
                 entity_id=work.id, new_values={"code": work.code, "type": work.work_type},
                 un_id=work.un_id, ip_address=client_ip(request))
    db.commit()
    db.refresh(work)
    return work


@router.patch("/{work_id}", response_model=WorkOut)
def update_work(work_id: str, payload: WorkUpdate, request: Request,
                db: Session = Depends(get_db), user: User = Depends(require_operator)):
    work = _get_work_or_404(db, work_id)
    enforce_un_scope(user, work.un_id)
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(work, k, v)
    audit.record(db, action=AuditAction.UPDATE.value, actor=user, entity_type="Work",
                 entity_id=work.id, un_id=work.un_id, ip_address=client_ip(request))
    db.commit()
    db.refresh(work)
    return work


@router.post("/assign", response_model=list[WorkOut])
def assign_works(payload: AssignRequest, request: Request,
                 db: Session = Depends(get_db), user: User = Depends(require_operator)):
    """Asigna uno o varios trabajos a un dispositivo (RF-WEB-04).

    RN-01: un trabajo solo puede estar asignado a un dispositivo a la vez.
    RN-02: un dispositivo puede tener múltiples trabajos.
    """
    device = db.get(Device, payload.device_id)
    if not device or not device.active:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Dispositivo no encontrado o inactivo.")
    enforce_un_scope(user, device.un_id)

    result = []
    for work_id in payload.work_ids:
        work = _get_work_or_404(db, work_id)
        enforce_un_scope(user, work.un_id)
        if work.un_id != device.un_id:
            raise HTTPException(status.HTTP_409_CONFLICT,
                                f"Trabajo {work.code} y dispositivo son de distinta UN.")
        # RN-01 / RF-WEB-04.7: exclusividad. Un trabajo ya asignado a otro
        # dispositivo debe retirarse (borrado remoto confirmado) antes de reasignar.
        if work.device_id and work.device_id != device.id:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                f"Trabajo {work.code} ya asignado a otro dispositivo; retírelo primero.",
            )
        work.device_id = device.id
        work.assigned_by_id = user.id
        work.assigned_at = datetime.now(timezone.utc)
        work.status = WorkStatus.ASSIGNED
        audit.record(db, action=AuditAction.ASSIGN.value, actor=user, entity_type="Work",
                     entity_id=work.id, new_values={"device_id": device.id},
                     un_id=work.un_id, device_id=device.id, ip_address=client_ip(request))
        result.append(work)

    db.commit()
    for w in result:
        db.refresh(w)
    return result


@router.post("/remote-delete", status_code=status.HTTP_202_ACCEPTED)
def remote_delete(payload: RemoteDeleteRequest, request: Request,
                  db: Session = Depends(get_db), user: User = Depends(require_operator)):
    """Ordena el borrado remoto de trabajos en un dispositivo (RF-WEB-05).

    La orden queda en cola y se ejecuta cuando el dispositivo se conecta.
    """
    device = db.get(Device, payload.device_id)
    if not device:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Dispositivo no encontrado.")
    enforce_un_scope(user, device.un_id)

    orders = []
    for work_id in payload.work_ids:
        work = _get_work_or_404(db, work_id)
        enforce_un_scope(user, work.un_id)
        if work.device_id != device.id:
            raise HTTPException(status.HTTP_409_CONFLICT,
                                f"Trabajo {work.code} no está asignado a ese dispositivo.")
        order = RemoteDeleteOrder(device_id=device.id, work_id=work.id, un_id=work.un_id,
                                  ordered_by_id=user.id, status=RemoteDeleteStatus.QUEUED)
        db.add(order)
        audit.record(db, action=AuditAction.REMOTE_DELETE_ORDER.value, actor=user,
                     entity_type="Work", entity_id=work.id, un_id=work.un_id,
                     device_id=device.id, ip_address=client_ip(request))
        orders.append(work.code)

    db.commit()
    return {"detail": f"Órdenes de borrado en cola para: {', '.join(orders)}"}
