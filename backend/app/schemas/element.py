"""Esquemas de elemento y bitácora (RF-WEB-07)."""
from typing import Any, Optional

from pydantic import BaseModel


class ElementOut(BaseModel):
    id: str
    guid: str
    element_type: str
    un_id: str
    parent_guid: Optional[str] = None
    geometry_geojson: Optional[str] = None
    attributes_json: Optional[str] = None
    is_new: bool
    model_config = {"from_attributes": True}


class ElementLogOut(BaseModel):
    id: str
    element_guid: str
    event_type: str
    detail: Optional[str] = None
    work_id: Optional[str] = None
    user_id: Optional[str] = None
    device_id: Optional[str] = None
    created_at: Any
    model_config = {"from_attributes": True}
