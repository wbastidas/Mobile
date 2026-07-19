"""Histórico de cambios de campo por usuario y por trabajo.

Registro append-only de cada CREATE/UPDATE/DELETE que un funcionario realiza
sobre un elemento durante un trabajo. Permite responder "¿qué hizo cada usuario
en cada trabajo de campo?" de forma directa (complementa la bitácora por
elemento de RF-WEB-07, que es centrada en el GUID).
"""
from typing import Optional

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import Timestamps, UUIDPk


class FieldChange(UUIDPk, Timestamps, Base):
    __tablename__ = "field_changes"

    # Quién y en qué trabajo (desnormalizado para consulta e histórico estable).
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    username: Mapped[str] = mapped_column(String(80), index=True)
    device_id: Mapped[Optional[str]] = mapped_column(ForeignKey("devices.id"), nullable=True)

    work_id: Mapped[str] = mapped_column(ForeignKey("works.id"), index=True)
    work_code: Mapped[str] = mapped_column(String(64), index=True)
    un_id: Mapped[str] = mapped_column(String(36), index=True)

    # Qué elemento y qué operación.
    element_guid: Mapped[str] = mapped_column(String(64), index=True)
    element_type: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    operation: Mapped[str] = mapped_column(String(8), index=True)  # CREATE|UPDATE|DELETE

    # Valores antes/después (JSON) para trazabilidad completa (cuándo = created_at).
    attributes_before: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    attributes_after: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
