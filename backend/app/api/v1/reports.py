"""Reportería con exportación a Excel/PDF/CSV (RF-WEB-11)."""
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, scope_un_filter
from app.models.user import User
from app.services import exporters, reports

router = APIRouter(prefix="/reports", tags=["reports"])


def _filters(un_id, work_type, status_, date_from, date_to) -> dict:
    return {
        "un_id": un_id, "work_type": work_type, "status": status_,
        "date_from": reports.parse_date(date_from), "date_to": reports.parse_date(date_to),
    }


@router.get("")
def list_reports(user: User = Depends(get_current_user)):
    """Catálogo de reportes disponibles."""
    return [{"key": k, "name": name} for k, (name, _) in reports.REPORTS.items()]


@router.get("/{report_key}")
def get_report(
    report_key: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    un_id: str | None = None,
    work_type: str | None = None,
    status_: str | None = Query(None, alias="status"),
    date_from: str | None = None,
    date_to: str | None = None,
):
    """Datos de un reporte en JSON, respetando la segregación Matriz/UN."""
    entry = reports.REPORTS.get(report_key)
    if not entry:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Reporte no encontrado.")
    name, fn = entry
    rows = fn(db, scope_un_filter(user), _filters(un_id, work_type, status_, date_from, date_to))
    return {"key": report_key, "name": name, "rows": rows, "count": len(rows)}


@router.get("/{report_key}/export")
def export_report(
    report_key: str,
    fmt: str = Query("xlsx", pattern="^(xlsx|csv|pdf)$"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    un_id: str | None = None,
    work_type: str | None = None,
    status_: str | None = Query(None, alias="status"),
    date_from: str | None = None,
    date_to: str | None = None,
):
    """Exporta el reporte a Excel, PDF o CSV (RF-WEB-11.2)."""
    entry = reports.REPORTS.get(report_key)
    if not entry:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Reporte no encontrado.")
    name, fn = entry
    rows = fn(db, scope_un_filter(user), _filters(un_id, work_type, status_, date_from, date_to))

    exporter, media_type, ext = exporters.EXPORTERS[fmt]
    content = exporter(name, rows)
    filename = f"{report_key}.{ext}"
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
