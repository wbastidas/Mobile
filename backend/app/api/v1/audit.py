"""Consulta de auditoría con filtros (RF-WEB-08.3)."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, scope_un_filter
from app.models.audit_log import AuditLog
from app.models.user import User
from app.schemas.audit import AuditLogOut

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("", response_model=list[AuditLogOut])
def list_audit(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    action: str | None = None,
    entity_type: str | None = None,
    entity_id: str | None = None,
    limit: int = Query(200, le=1000),
):
    q = db.query(AuditLog)
    un = scope_un_filter(user)
    if un is not None:  # segregación: roles UN solo ven auditoría de su UN
        q = q.filter(AuditLog.un_id == un)
    if action:
        q = q.filter(AuditLog.action == action)
    if entity_type:
        q = q.filter(AuditLog.entity_type == entity_type)
    if entity_id:
        q = q.filter(AuditLog.entity_id == entity_id)
    return q.order_by(AuditLog.created_at.desc()).limit(limit).all()
