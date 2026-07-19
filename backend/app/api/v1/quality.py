"""Gestión de parámetros de calidad y esquema dirigido por metadatos (RF-WEB-10, §6.4)."""
import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import enforce_un_scope, get_current_user, require_admin, scope_un_filter
from app.core.enums import AuditAction
from app.models.quality_novelty import QualityNovelty
from app.models.quality_params import QualityParamSet, SchemaDefinition
from app.models.user import User
from app.models.work import Work
from app.schemas.quality import (
    QualityParamCreate,
    QualityParamOut,
    SchemaDefinitionCreate,
    SchemaDefinitionOut,
)
from app.services import audit

router = APIRouter(prefix="/quality", tags=["quality"])


@router.get("/params", response_model=list[QualityParamOut])
def list_params(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(QualityParamSet).order_by(QualityParamSet.version.desc()).all()


@router.get("/params/active", response_model=QualityParamOut)
def active_params(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    qp = db.query(QualityParamSet).filter(QualityParamSet.is_active.is_(True)).first()
    if not qp:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No hay parámetros de calidad activos.")
    return qp


@router.post("/params", response_model=QualityParamOut, status_code=status.HTTP_201_CREATED)
def upload_params(payload: QualityParamCreate, db: Session = Depends(get_db),
                  admin: User = Depends(require_admin)):
    """Carga y versiona el archivo de parámetros de calidad (RF-WEB-10.1)."""
    next_version = (db.query(func.max(QualityParamSet.version)).scalar() or 0) + 1
    qp = QualityParamSet(version=next_version, description=payload.description,
                         rules_json=json.dumps(payload.rules_json, ensure_ascii=False),
                         uploaded_by_id=admin.id)
    if payload.activate:
        db.query(QualityParamSet).update({QualityParamSet.is_active: False})
        qp.is_active = True
    db.add(qp)
    db.flush()
    audit.record(db, action=AuditAction.QUALITY_PARAMS_UPLOAD.value, actor=admin,
                 entity_type="QualityParamSet", entity_id=qp.id,
                 new_values={"version": next_version, "active": qp.is_active})
    db.commit()
    db.refresh(qp)
    return qp


@router.get("/novelties")
def list_novelties(work_id: str | None = None, db: Session = Depends(get_db),
                   user: User = Depends(get_current_user)):
    """Detalle de novedades de calidad por elemento y por regla (RF-WEB-09.2)."""
    q = db.query(QualityNovelty)
    un = scope_un_filter(user)
    if un is not None:  # segregación (RN-05)
        q = q.filter(QualityNovelty.un_id == un)
    if work_id:
        work = db.get(Work, work_id)
        if work:
            enforce_un_scope(user, work.un_id)
        q = q.filter(QualityNovelty.work_id == work_id)
    rows = q.order_by(QualityNovelty.created_at.desc()).limit(1000).all()
    return [
        {"id": n.id, "work_id": n.work_id, "element_guid": n.element_guid,
         "element_type": n.element_type, "field": n.field, "rule_type": n.rule_type,
         "message": n.message, "expected": n.expected, "actual": n.actual}
        for n in rows
    ]


@router.get("/schema", response_model=list[SchemaDefinitionOut])
def list_schemas(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(SchemaDefinition).order_by(SchemaDefinition.version.desc()).all()


@router.post("/schema", response_model=SchemaDefinitionOut, status_code=status.HTTP_201_CREATED)
def upload_schema(payload: SchemaDefinitionCreate, db: Session = Depends(get_db),
                  admin: User = Depends(require_admin)):
    """Versiona la definición de esquema (capas/campos/dominios/formularios, §6.4/6.5)."""
    next_version = (db.query(func.max(SchemaDefinition.version)).scalar() or 0) + 1
    sd = SchemaDefinition(version=next_version, description=payload.description,
                          definition_json=json.dumps(payload.definition_json, ensure_ascii=False))
    if payload.activate:
        db.query(SchemaDefinition).update({SchemaDefinition.is_active: False})
        sd.is_active = True
    db.add(sd)
    db.flush()
    audit.record(db, action=AuditAction.CREATE.value, actor=admin, entity_type="SchemaDefinition",
                 entity_id=sd.id, new_values={"version": next_version})
    db.commit()
    db.refresh(sd)
    return sd
