"""Revisión y aprobación de lotes de consolidación GIS (§7.2/7.4, RF-WEB-09.4)."""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import client_ip, get_current_user, require_operator, scope_un_filter
from app.core.enums import AuditAction
from app.models.business_unit import BusinessUnit
from app.models.gis_staging import GISStagingBatch
from app.models.user import User
from app.services import audit

router = APIRouter(prefix="/gis", tags=["gis"])


def _un_code_scope(db: Session, user: User) -> str | None:
    """Código de UN del usuario para filtrar lotes; None si es ámbito global."""
    un_id = scope_un_filter(user)
    if un_id is None:
        return None
    un = db.get(BusinessUnit, un_id)
    return un.code if un else "__sin_un__"


def _get_batch_scoped(db: Session, user: User, batch_id: str) -> GISStagingBatch:
    batch = db.get(GISStagingBatch, batch_id)
    if not batch:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Lote no encontrado.")
    scope = _un_code_scope(db, user)
    if scope is not None and batch.un_code != scope:
        raise HTTPException(status.HTTP_403_FORBIDDEN,
                            "Fuera del ámbito de su unidad de negocio.")
    return batch


@router.get("/staging")
def list_batches(status_filter: str | None = None,
                 db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Lotes de consolidación, respetando la segregación Matriz/UN (RN-05)."""
    q = db.query(GISStagingBatch)
    scope = _un_code_scope(db, user)
    if scope is not None:
        q = q.filter(GISStagingBatch.un_code == scope)
    if status_filter:
        q = q.filter(GISStagingBatch.status == status_filter)
    return [
        {"id": b.id, "un_code": b.un_code, "work_id": b.work_id, "status": b.status,
         "element_count": b.element_count, "message": b.message,
         "created_at": b.created_at}
        for b in q.order_by(GISStagingBatch.created_at.desc()).limit(500).all()
    ]


@router.get("/staging/{batch_id}")
def batch_detail(batch_id: str, db: Session = Depends(get_db),
                 user: User = Depends(get_current_user)):
    batch = _get_batch_scoped(db, user, batch_id)
    return {
        "id": batch.id, "un_code": batch.un_code, "work_id": batch.work_id,
        "status": batch.status, "element_count": batch.element_count,
        "elements": [
            {"guid": e.guid, "element_type": e.element_type, "parent_guid": e.parent_guid,
             "geometry_geojson": e.geometry_geojson, "attributes_json": e.attributes_json}
            for e in batch.elements
        ],
    }


@router.post("/staging/{batch_id}/approve")
def approve_batch(batch_id: str, request: Request, db: Session = Depends(get_db),
                  user: User = Depends(require_operator)):
    """Aprueba el lote y dispara la carga a ArcSDE/Oracle (RN-11).

    El mecanismo físico de carga (ArcPy / servicios REST / job Oracle) se
    conecta aquí cuando PD-02 quede definido; el estado LOADED representa la
    carga corporativa completada.
    """
    batch = _get_batch_scoped(db, user, batch_id)
    if batch.status != "PENDING_REVIEW":
        raise HTTPException(status.HTTP_409_CONFLICT,
                            f"El lote está en estado {batch.status}; no puede aprobarse.")
    batch.status = "LOADED"
    batch.decided_by_id = user.id
    audit.record(db, action=AuditAction.CONSOLIDATE.value, actor=user,
                 entity_type="GISStagingBatch", entity_id=batch.id,
                 new_values={"status": "LOADED", "elements": batch.element_count},
                 ip_address=client_ip(request))
    db.commit()
    return {"id": batch.id, "status": batch.status,
            "detail": "Lote aprobado y cargado a la geodatabase corporativa."}


@router.post("/staging/{batch_id}/rollback")
def rollback_batch(batch_id: str, request: Request, db: Session = Depends(get_db),
                   user: User = Depends(require_operator)):
    """Revierte un lote (respaldo/staging previo, §7.4)."""
    batch = _get_batch_scoped(db, user, batch_id)
    if batch.status == "ROLLED_BACK":
        raise HTTPException(status.HTTP_409_CONFLICT, "El lote ya fue revertido.")
    batch.status = "ROLLED_BACK"
    batch.decided_by_id = user.id
    audit.record(db, action=AuditAction.CONSOLIDATE.value, actor=user,
                 entity_type="GISStagingBatch", entity_id=batch.id,
                 new_values={"status": "ROLLED_BACK"}, ip_address=client_ip(request))
    db.commit()
    return {"id": batch.id, "status": batch.status, "detail": "Lote revertido."}
