"""Novedad de calidad a nivel de regla (RF-WEB-09.2).

Cada incumplimiento reportado por la validación del dispositivo se persiste como
una fila, permitiendo el detalle por elemento y por regla, y la agregación de las
novedades más frecuentes (RF-WEB-11.1).
"""
from typing import Optional

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import Timestamps, UUIDPk


class QualityNovelty(UUIDPk, Timestamps, Base):
    __tablename__ = "quality_novelties"

    package_id: Mapped[str] = mapped_column(ForeignKey("sync_packages.id"), index=True)
    work_id: Mapped[str] = mapped_column(ForeignKey("works.id"), index=True)
    un_id: Mapped[str] = mapped_column(String(36), index=True)

    element_guid: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    element_type: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    field: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    rule_type: Mapped[str] = mapped_column(String(48), index=True)
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    expected: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    actual: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
