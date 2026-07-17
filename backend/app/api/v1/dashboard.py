"""Dashboard geográfico y línea de tiempo (RF-WEB-06)."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import enforce_un_scope, get_current_user, scope_un_filter
from app.core.enums import WorkStatus
from app.models.audit_log import AuditLog
from app.models.user import User
from app.models.work import Work
from app.schemas.work import WorkTimelineEvent

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

_ACTIVE = [WorkStatus.ASSIGNED, WorkStatus.DOWNLOADED, WorkStatus.IN_PROGRESS,
           WorkStatus.SYNCING, WorkStatus.SYNC_PENDING]


@router.get("/summary")
def summary(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Conteos por estado/tipo respetando la segregación Matriz/UN (RF-WEB-06.5)."""
    q = db.query(Work)
    un = scope_un_filter(user)
    if un is not None:
        q = q.filter(Work.un_id == un)

    by_status = dict(
        q.with_entities(Work.status, func.count(Work.id)).group_by(Work.status).all()
    )
    by_type = dict(
        q.with_entities(Work.work_type, func.count(Work.id)).group_by(Work.work_type).all()
    )
    active = q.filter(Work.status.in_(_ACTIVE)).count()
    return {"total": q.count(), "active": active, "by_status": by_status, "by_type": by_type}


@router.get("/map")
def map_works(history: bool = False, db: Session = Depends(get_db),
              user: User = Depends(get_current_user)):
    """Trabajos activos (o histórico) con su ubicación/extensión para el mapa."""
    q = db.query(Work)
    un = scope_un_filter(user)
    if un is not None:
        q = q.filter(Work.un_id == un)
    if history:
        q = q.filter(Work.status.in_([WorkStatus.COMPLETED, WorkStatus.WITH_ISSUES]))
    else:
        q = q.filter(Work.status.in_(_ACTIVE))
    return [
        {"id": w.id, "code": w.code, "title": w.title, "work_type": w.work_type,
         "status": w.status, "un_id": w.un_id, "device_id": w.device_id,
         "sector_geojson": w.sector_geojson, "created_at": w.created_at}
        for w in q.all()
    ]


@router.get("/works/{work_id}/timeline", response_model=list[WorkTimelineEvent])
def timeline(work_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Línea de tiempo de eventos del trabajo (RF-WEB-06.4)."""
    work = db.get(Work, work_id)
    if not work:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Trabajo no encontrado.")
    enforce_un_scope(user, work.un_id)
    logs = (db.query(AuditLog)
            .filter(AuditLog.entity_type == "Work", AuditLog.entity_id == work_id)
            .order_by(AuditLog.created_at.asc())
            .all())
    return [WorkTimelineEvent(at=l.created_at, action=l.action, detail=l.new_values,
                              username=l.username) for l in logs]
