"""Trabajo (unidad de asignación) — RF-WEB-03/04/05, RF-SYNC.6."""
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.enums import ValidationResult, WorkStatus, WorkType
from app.models.base import Timestamps, UUIDPk


class Work(UUIDPk, Timestamps, Base):
    __tablename__ = "works"

    code: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    work_type: Mapped[WorkType] = mapped_column(String(32), index=True)
    status: Mapped[WorkStatus] = mapped_column(String(32), default=WorkStatus.CREATED, index=True)

    # Segregación obligatoria (RN-05 / modelo de datos §6.6)
    un_id: Mapped[str] = mapped_column(ForeignKey("business_units.id"), index=True)

    # Versión de esquema con que se generó (modelo de datos §6.5)
    schema_version: Mapped[int] = mapped_column(Integer, default=1)

    # Ámbito geográfico:
    #  - REVISION_RED: polígono del sector (GeoJSON). En producción PostGIS geometry.
    #  - ORDEN_PUNTUAL: lista de GUIDs objetivo va en work_elements.
    sector_geojson: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Exclusividad de asignación (RN-01): un trabajo -> un dispositivo a la vez.
    device_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("devices.id"), nullable=True, index=True
    )
    assigned_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    assigned_by_id: Mapped[Optional[str]] = mapped_column(ForeignKey("users.id"), nullable=True)

    # Resultado de la validación de calidad reportada por el dispositivo (RF-MOV-09).
    validation_result: Mapped[ValidationResult] = mapped_column(
        String(16), default=ValidationResult.NOT_RUN
    )

    # Fechas de ciclo de vida para métricas (RF-WEB-11).
    downloaded_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    synced_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    business_unit = relationship("BusinessUnit", back_populates="works")
    device = relationship("Device", back_populates="works")
    elements = relationship("WorkElement", back_populates="work", cascade="all, delete-orphan")
