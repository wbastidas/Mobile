"""Dispositivo móvil autorizado (RF-WEB-02.3)."""
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import Timestamps, UUIDPk


class Device(UUIDPk, Timestamps, Base):
    __tablename__ = "devices"

    # Identificador de hardware/instalación reportado por la app.
    device_uid: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    alias: Mapped[str] = mapped_column(String(120))
    active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Vinculación a funcionario y UN (RF-WEB-02.3 / RF-MOV-01.2)
    un_id: Mapped[str] = mapped_column(ForeignKey("business_units.id"), index=True)
    assigned_user_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("users.id"), nullable=True, index=True
    )

    last_seen_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    quality_params_version: Mapped[Optional[int]] = mapped_column(nullable=True)

    business_unit = relationship("BusinessUnit", back_populates="devices")
    assigned_user = relationship("User")
    works = relationship("Work", back_populates="device")
