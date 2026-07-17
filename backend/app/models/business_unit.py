"""Unidad de Negocio (UN) y Matriz — base de la segregación de datos (RN-05)."""
from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import Timestamps, UUIDPk


class BusinessUnit(UUIDPk, Timestamps, Base):
    __tablename__ = "business_units"

    code: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(160))
    is_headquarters: Mapped[bool] = mapped_column(Boolean, default=False)  # True para la Matriz
    active: Mapped[bool] = mapped_column(Boolean, default=True)

    users = relationship("User", back_populates="business_unit")
    devices = relationship("Device", back_populates="business_unit")
    works = relationship("Work", back_populates="business_unit")
