"""Bitácora por elemento (RF-WEB-07): todo lo que le ocurre a un GUID."""
from typing import Optional

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import Timestamps, UUIDPk


class ElementLog(UUIDPk, Timestamps, Base):
    __tablename__ = "element_logs"

    element_id: Mapped[str] = mapped_column(ForeignKey("elements.id"), index=True)
    element_guid: Mapped[str] = mapped_column(String(64), index=True)

    # Tipo de evento: ATTR_EDIT, GEOM_CHANGE, PHOTO, OBSERVATION, WORK, VALIDATION...
    event_type: Mapped[str] = mapped_column(String(48), index=True)
    detail: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Trazabilidad quién/cuándo (cuándo = created_at del mixin).
    work_id: Mapped[Optional[str]] = mapped_column(ForeignKey("works.id"), nullable=True)
    user_id: Mapped[Optional[str]] = mapped_column(ForeignKey("users.id"), nullable=True)
    device_id: Mapped[Optional[str]] = mapped_column(ForeignKey("devices.id"), nullable=True)

    element = relationship("Element", back_populates="logs")
