"""Histórico de cambios de campo por usuario y por trabajo.

Responde "¿qué hizo cada funcionario en cada trabajo?" con el detalle de las
operaciones CREATE/UPDATE/DELETE. Respeta la segregación Matriz/UN (RN-05).
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, scope_un_filter
from app.models.field_change import FieldChange
from app.models.user import User

router = APIRouter(prefix="/history", tags=["history"])


@router.get("/changes")
def list_changes(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    user_id: str | None = None,
    work_id: str | None = None,
    operation: str | None = None,
    limit: int = Query(500, le=2000),
):
    """Detalle de cambios de campo, filtrable por usuario, trabajo y operación."""
    q = db.query(FieldChange)
    un = scope_un_filter(user)
    if un is not None:  # segregación Matriz/UN
        q = q.filter(FieldChange.un_id == un)
    if user_id:
        q = q.filter(FieldChange.user_id == user_id)
    if work_id:
        q = q.filter(FieldChange.work_id == work_id)
    if operation:
        q = q.filter(FieldChange.operation == operation)
    rows = q.order_by(FieldChange.created_at.desc()).limit(limit).all()
    return [
        {"id": c.id, "username": c.username, "work_code": c.work_code, "work_id": c.work_id,
         "element_guid": c.element_guid, "element_type": c.element_type,
         "operation": c.operation, "attributes_before": c.attributes_before,
         "attributes_after": c.attributes_after, "created_at": c.created_at}
        for c in rows
    ]


@router.get("/summary")
def summary(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    work_id: str | None = None,
):
    """Resumen por funcionario: conteo de creados/modificados/eliminados."""
    q = db.query(
        FieldChange.username, FieldChange.operation, func.count(FieldChange.id)
    )
    un = scope_un_filter(user)
    if un is not None:
        q = q.filter(FieldChange.un_id == un)
    if work_id:
        q = q.filter(FieldChange.work_id == work_id)
    rows = q.group_by(FieldChange.username, FieldChange.operation).all()

    agg: dict[str, dict] = {}
    for username, operation, count in rows:
        r = agg.setdefault(username, {"funcionario": username, "CREATE": 0, "UPDATE": 0, "DELETE": 0})
        r[operation] = count
    return sorted(agg.values(), key=lambda x: x["funcionario"])
