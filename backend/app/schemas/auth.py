"""Esquemas de autenticación."""
from typing import Optional

from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class LoginRequest(BaseModel):
    username: str
    password: str


class MobileLoginRequest(BaseModel):
    """Login móvil: valida funcionario + dispositivo autorizado (RF-MOV-01.2)."""
    username: str
    password: str
    device_uid: str


class RefreshRequest(BaseModel):
    refresh_token: str


class CurrentUser(BaseModel):
    id: str
    username: str
    full_name: str
    role: str
    un_id: Optional[str] = None
    is_global_scope: bool

    model_config = {"from_attributes": True}
