"""Elementos y bitácora por GUID (RF-WEB-07)."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import enforce_un_scope, get_current_user, scope_un_filter
from app.models.element import Element
from app.models.element_log import ElementLog
from app.models.user import User
from app.schemas.element import ElementLogOut, ElementOut

router = APIRouter(prefix="/elements", tags=["elements"])


@router.get("", response_model=list[ElementOut])
def list_elements(element_type: str | None = None, db: Session = Depends(get_db),
                  user: User = Depends(get_current_user)):
    q = db.query(Element)
    un = scope_un_filter(user)
    if un is not None:
        q = q.filter(Element.un_id == un)
    if element_type:
        q = q.filter(Element.element_type == element_type)
    return q.order_by(Element.element_type, Element.guid).limit(500).all()


@router.get("/{guid}", response_model=ElementOut)
def get_element(guid: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    el = db.query(Element).filter(Element.guid == guid).first()
    if not el:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Elemento no encontrado.")
    enforce_un_scope(user, el.un_id)
    return el


@router.get("/{guid}/log", response_model=list[ElementLogOut])
def element_log(guid: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Bitácora completa del elemento: todo lo ocurrido con ese GUID (RF-WEB-07)."""
    el = db.query(Element).filter(Element.guid == guid).first()
    if not el:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Elemento no encontrado.")
    enforce_un_scope(user, el.un_id)
    return (db.query(ElementLog)
            .filter(ElementLog.element_guid == guid)
            .order_by(ElementLog.created_at.desc())
            .all())
