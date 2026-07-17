"""Esquemas de parámetros de calidad y definición de esquema."""
from typing import Any, Optional

from pydantic import BaseModel


class QualityParamCreate(BaseModel):
    description: Optional[str] = None
    rules_json: Any  # objeto JSON con las reglas
    activate: bool = True


class QualityParamOut(BaseModel):
    id: str
    version: int
    description: Optional[str] = None
    is_active: bool
    model_config = {"from_attributes": True}


class SchemaDefinitionCreate(BaseModel):
    description: Optional[str] = None
    definition_json: Any
    activate: bool = True


class SchemaDefinitionOut(BaseModel):
    id: str
    version: int
    description: Optional[str] = None
    is_active: bool
    model_config = {"from_attributes": True}
