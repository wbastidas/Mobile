"""Generación de datos de reportes (RF-WEB-11), respetando la segregación Matriz/UN.

Cada función devuelve una lista de filas (dicts) lista para exportar o serializar.
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.enums import ValidationResult, WorkStatus
from app.models.business_unit import BusinessUnit
from app.models.device import Device
from app.models.quality_novelty import QualityNovelty
from app.models.work import Work

_ACTIVE = [WorkStatus.ASSIGNED, WorkStatus.DOWNLOADED, WorkStatus.IN_PROGRESS,
           WorkStatus.SYNCING, WorkStatus.SYNC_PENDING]
_CLOSED = [WorkStatus.COMPLETED, WorkStatus.WITH_ISSUES]


def _base_query(db: Session, un_scope: Optional[str], filters: dict):
    q = db.query(Work)
    if un_scope is not None:  # roles UN: solo su UN (RN-05)
        q = q.filter(Work.un_id == un_scope)
    if filters.get("un_id"):
        q = q.filter(Work.un_id == filters["un_id"])
    if filters.get("work_type"):
        q = q.filter(Work.work_type == filters["work_type"])
    if filters.get("status"):
        q = q.filter(Work.status == filters["status"])
    if filters.get("date_from"):
        q = q.filter(Work.created_at >= filters["date_from"])
    if filters.get("date_to"):
        q = q.filter(Work.created_at <= filters["date_to"])
    return q


def works_summary(db: Session, un_scope: Optional[str], filters: dict) -> list[dict]:
    """Trabajos agregados por UN y tipo, con conteos por estado."""
    q = _base_query(db, un_scope, filters)
    un_names = {u.id: u.code for u in db.query(BusinessUnit).all()}
    rows: dict[tuple, dict] = {}
    for w in q.all():
        key = (w.un_id, w.work_type)
        r = rows.setdefault(key, {
            "unidad_negocio": un_names.get(w.un_id, w.un_id),
            "tipo_trabajo": w.work_type,
            "total": 0, "activos": 0, "terminados": 0, "con_novedades": 0,
        })
        r["total"] += 1
        if w.status in _ACTIVE:
            r["activos"] += 1
        if w.status in _CLOSED:
            r["terminados"] += 1
        if w.validation_result == ValidationResult.WITH_ISSUES:
            r["con_novedades"] += 1
    return sorted(rows.values(), key=lambda x: (x["unidad_negocio"], x["tipo_trabajo"]))


def productivity(db: Session, un_scope: Optional[str], filters: dict) -> list[dict]:
    """Productividad por dispositivo/funcionario: asignados vs. terminados."""
    q = _base_query(db, un_scope, filters).filter(Work.device_id.isnot(None))
    devices = {d.id: d for d in db.query(Device).all()}
    rows: dict[str, dict] = {}
    for w in q.all():
        dev = devices.get(w.device_id)
        r = rows.setdefault(w.device_id, {
            "dispositivo": dev.alias if dev else w.device_id,
            "funcionario": (dev.assigned_user_id if dev else None) or "—",
            "asignados": 0, "terminados": 0,
        })
        r["asignados"] += 1
        if w.status in _CLOSED:
            r["terminados"] += 1
    return sorted(rows.values(), key=lambda x: x["dispositivo"])


def cycle_times(db: Session, un_scope: Optional[str], filters: dict) -> list[dict]:
    """Tiempos de ciclo (asignación → cierre) por tipo de trabajo, en horas."""
    q = _base_query(db, un_scope, filters).filter(Work.status.in_(_CLOSED))
    acc: dict[str, list[float]] = {}
    for w in q.all():
        if w.assigned_at and w.completed_at:
            hours = (w.completed_at - w.assigned_at).total_seconds() / 3600.0
            acc.setdefault(w.work_type, []).append(hours)
    rows = []
    for work_type, hours in acc.items():
        rows.append({
            "tipo_trabajo": work_type,
            "trabajos_cerrados": len(hours),
            "horas_promedio": round(sum(hours) / len(hours), 2) if hours else 0,
            "horas_min": round(min(hours), 2) if hours else 0,
            "horas_max": round(max(hours), 2) if hours else 0,
        })
    return sorted(rows, key=lambda x: x["tipo_trabajo"])


def quality_novelties(db: Session, un_scope: Optional[str], filters: dict) -> list[dict]:
    """Novedades de calidad por UN y tipo (trabajos marcados WITH_ISSUES)."""
    q = _base_query(db, un_scope, filters).filter(
        Work.validation_result == ValidationResult.WITH_ISSUES
    )
    un_names = {u.id: u.code for u in db.query(BusinessUnit).all()}
    rows: dict[tuple, dict] = {}
    for w in q.all():
        key = (w.un_id, w.work_type)
        r = rows.setdefault(key, {
            "unidad_negocio": un_names.get(w.un_id, w.un_id),
            "tipo_trabajo": w.work_type, "trabajos_con_novedades": 0,
        })
        r["trabajos_con_novedades"] += 1
    return sorted(rows.values(), key=lambda x: (x["unidad_negocio"], x["tipo_trabajo"]))


def quality_novelties_by_rule(db: Session, un_scope: Optional[str], filters: dict) -> list[dict]:
    """Novedades de calidad más frecuentes por regla/campo/tipo (RF-WEB-11.1).

    Se agrega desde el detalle persistido (QualityNovelty), no desde el trabajo,
    permitiendo ver qué reglas se incumplen con más frecuencia.
    """
    q = db.query(QualityNovelty)
    if un_scope is not None:
        q = q.filter(QualityNovelty.un_id == un_scope)
    if filters.get("un_id"):
        q = q.filter(QualityNovelty.un_id == filters["un_id"])
    if filters.get("date_from"):
        q = q.filter(QualityNovelty.created_at >= filters["date_from"])
    if filters.get("date_to"):
        q = q.filter(QualityNovelty.created_at <= filters["date_to"])

    rows: dict[tuple, dict] = {}
    for n in q.all():
        key = (n.element_type, n.field, n.rule_type)
        r = rows.setdefault(key, {
            "tipo_elemento": n.element_type or "—",
            "campo": n.field or "—",
            "regla": n.rule_type,
            "ocurrencias": 0,
        })
        r["ocurrencias"] += 1
    return sorted(rows.values(), key=lambda x: x["ocurrencias"], reverse=True)


REPORTS = {
    "works-summary": ("Resumen de trabajos", works_summary),
    "productivity": ("Productividad por dispositivo", productivity),
    "cycle-times": ("Tiempos de ciclo", cycle_times),
    "quality-novelties": ("Novedades de calidad (por trabajo)", quality_novelties),
    "quality-by-rule": ("Novedades de calidad más frecuentes (por regla)", quality_novelties_by_rule),
}


def parse_date(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None
