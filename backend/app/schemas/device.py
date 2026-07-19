"""Esquemas de dispositivo."""
from typing import Optional

from pydantic import BaseModel


class DeviceBase(BaseModel):
    device_uid: str
    alias: str
    un_id: str
    assigned_user_id: Optional[str] = None
    active: bool = True


class DeviceCreate(DeviceBase):
    pass


class DeviceUpdate(BaseModel):
    alias: Optional[str] = None
    assigned_user_id: Optional[str] = None
    active: Optional[bool] = None


class DeviceOut(BaseModel):
    id: str
    device_uid: str
    alias: str
    un_id: str
    assigned_user_id: Optional[str] = None
    active: bool
    quality_params_version: Optional[int] = None
    model_config = {"from_attributes": True}
