"""Esquemas de Unidad de Negocio."""
from typing import Optional

from pydantic import BaseModel


class BusinessUnitBase(BaseModel):
    code: str
    name: str
    is_headquarters: bool = False
    active: bool = True


class BusinessUnitCreate(BusinessUnitBase):
    pass


class BusinessUnitUpdate(BaseModel):
    name: Optional[str] = None
    active: Optional[bool] = None


class BusinessUnitOut(BusinessUnitBase):
    id: str
    model_config = {"from_attributes": True}
