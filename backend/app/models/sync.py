"""Sincronización: paquetes, fotos y órdenes de borrado remoto (RF-SYNC, RF-WEB-05/09)."""
from typing import Optional

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.enums import RemoteDeleteStatus, ValidationResult
from app.models.base import Timestamps, UUIDPk


class SyncPackage(UUIDPk, Timestamps, Base):
    """Paquete de sincronización recibido desde la app móvil (RF-WEB-09)."""
    __tablename__ = "sync_packages"

    # Clave de idempotencia por paquete (RF-SYNC.5).
    idempotency_key: Mapped[str] = mapped_column(String(128), unique=True, index=True)

    work_id: Mapped[str] = mapped_column(ForeignKey("works.id"), index=True)
    device_id: Mapped[str] = mapped_column(ForeignKey("devices.id"), index=True)
    un_id: Mapped[str] = mapped_column(String(36), index=True)

    schema_version: Mapped[int] = mapped_column(Integer, default=1)
    checksum: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)  # RF-SYNC.4

    # Contenido: elementos/atributos/geometrías (JSON serializado).
    payload_json: Mapped[str] = mapped_column(Text)

    validation_result: Mapped[ValidationResult] = mapped_column(
        String(16), default=ValidationResult.NOT_RUN
    )
    validation_report_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    verified: Mapped[bool] = mapped_column(Boolean, default=False)  # completitud (RF-MOV-10.2)
    consolidated: Mapped[bool] = mapped_column(Boolean, default=False)  # cargado a ArcSDE

    photos = relationship("Photo", back_populates="package", cascade="all, delete-orphan")


class Photo(UUIDPk, Timestamps, Base):
    """Foto con metadata obligatoria de trazabilidad (RF-MOV-08, RN-08)."""
    __tablename__ = "photos"

    package_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("sync_packages.id"), nullable=True, index=True
    )
    element_guid: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    work_id: Mapped[Optional[str]] = mapped_column(ForeignKey("works.id"), nullable=True)

    # Metadata obligatoria (RN-08): coordenadas, fecha/hora.
    gps_lat: Mapped[float] = mapped_column()
    gps_lon: Mapped[float] = mapped_column()
    captured_at: Mapped[str] = mapped_column(String(40))  # ISO-8601 del dispositivo

    user_id: Mapped[Optional[str]] = mapped_column(ForeignKey("users.id"), nullable=True)
    device_id: Mapped[Optional[str]] = mapped_column(ForeignKey("devices.id"), nullable=True)

    # Integridad y subida reanudable por chunks (RF-SYNC.3/4).
    sha256: Mapped[str] = mapped_column(String(64), index=True)
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    received_chunks: Mapped[int] = mapped_column(Integer, default=0)
    total_chunks: Mapped[int] = mapped_column(Integer, default=1)
    storage_path: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    fully_received: Mapped[bool] = mapped_column(Boolean, default=False)

    package = relationship("SyncPackage", back_populates="photos")


class RemoteDeleteOrder(UUIDPk, Timestamps, Base):
    """Orden de borrado remoto de trabajos en un dispositivo (RF-WEB-05)."""
    __tablename__ = "remote_delete_orders"

    device_id: Mapped[str] = mapped_column(ForeignKey("devices.id"), index=True)
    work_id: Mapped[str] = mapped_column(ForeignKey("works.id"), index=True)
    un_id: Mapped[str] = mapped_column(String(36), index=True)

    status: Mapped[RemoteDeleteStatus] = mapped_column(
        String(16), default=RemoteDeleteStatus.QUEUED, index=True
    )
    ordered_by_id: Mapped[Optional[str]] = mapped_column(ForeignKey("users.id"), nullable=True)
    confirmed_at: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
