"""Esquemas de usuario."""
from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from app.core.enums import AuthType, Role


class UserBase(BaseModel):
    username: str = Field(min_length=3, max_length=80)
    full_name: str
    email: Optional[EmailStr] = None
    role: Role
    auth_type: AuthType = AuthType.LOCAL
    un_id: Optional[str] = None
    active: bool = True


class UserCreate(UserBase):
    # Requerido solo para usuarios LOCAL.
    password: Optional[str] = None


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[Role] = None
    un_id: Optional[str] = None
    active: Optional[bool] = None


class PasswordChange(BaseModel):
    new_password: str


class UserOut(BaseModel):
    id: str
    username: str
    full_name: str
    email: Optional[str] = None
    role: str
    auth_type: str
    un_id: Optional[str] = None
    active: bool
    model_config = {"from_attributes": True}
