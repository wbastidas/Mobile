"""Servicio de auditoría append-only (RF-WEB-08, RN-10)."""
import json
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.user import User


def _dump(value: Any) -> Optional[str]:
    if value is None:
        return None
    return json.dumps(value, default=str, ensure_ascii=False)


def record(
    db: Session,
    *,
    action: str,
    actor: Optional[User] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    old_values: Any = None,
    new_values: Any = None,
    un_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    device_id: Optional[str] = None,
    username: Optional[str] = None,
) -> AuditLog:
    """Crea un registro de auditoría. No hace commit (lo hace el llamador)."""
    entry = AuditLog(
        user_id=actor.id if actor else None,
        username=(actor.username if actor else username),
        role=(actor.role if actor else None),
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        old_values=_dump(old_values),
        new_values=_dump(new_values),
        un_id=un_id or (actor.un_id if actor else None),
        ip_address=ip_address,
        device_id=device_id,
    )
    db.add(entry)
    return entry
