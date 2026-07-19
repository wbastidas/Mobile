"""Esquemas de trabajo y asignación."""
from typing import Any, List, Optional

from pydantic import BaseModel

from app.core.enums import WorkStatus, WorkType


class WorkElementIn(BaseModel):
    element_guid: str
    geometry_geojson: Optional[str] = None
    attributes_json: Optional[str] = None


class WorkCreate(BaseModel):
    code: str
    title: str
    description: Optional[str] = None
    work_type: WorkType
    un_id: str
    schema_version: int = 1
    sector_geojson: Optional[str] = None
    # Elementos objetivo (para ORDEN_PUNTUAL) o incluidos en el sector.
    elements: List[WorkElementIn] = []


class WorkUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    sector_geojson: Optional[str] = None


class AssignRequest(BaseModel):
    """Asignación de uno o varios trabajos a un dispositivo (RF-WEB-04)."""
    device_id: str
    work_ids: List[str]


class RemoteDeleteRequest(BaseModel):
    """Borrado remoto de uno o varios trabajos en un dispositivo (RF-WEB-05)."""
    device_id: str
    work_ids: List[str]


class WorkElementOut(BaseModel):
    id: str
    element_guid: str
    completed: bool
    geometry_geojson: Optional[str] = None
    attributes_json: Optional[str] = None
    model_config = {"from_attributes": True}


class WorkOut(BaseModel):
    id: str
    code: str
    title: str
    description: Optional[str] = None
    work_type: str
    status: str
    un_id: str
    schema_version: int
    sector_geojson: Optional[str] = None
    device_id: Optional[str] = None
    validation_result: str
    model_config = {"from_attributes": True}


class WorkDetailOut(WorkOut):
    elements: List[WorkElementOut] = []


class WorkTimelineEvent(BaseModel):
    """Evento de la línea de tiempo del trabajo (RF-WEB-06.4)."""
    at: Any
    action: str
    detail: Optional[str] = None
    username: Optional[str] = None
