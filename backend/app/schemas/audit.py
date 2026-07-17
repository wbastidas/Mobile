"""Esquema de salida de auditoría."""
from typing import Any, Optional

from pydantic import BaseModel


class AuditLogOut(BaseModel):
    id: str
    user_id: Optional[str] = None
    username: Optional[str] = None
    role: Optional[str] = None
    action: str
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    old_values: Optional[str] = None
    new_values: Optional[str] = None
    un_id: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: Any
    model_config = {"from_attributes": True}
