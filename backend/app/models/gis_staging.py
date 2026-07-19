"""Staging reversible para la consolidación hacia ArcSDE/Oracle (§7.2/7.4).

Los cambios verificados NO se escriben directamente en la geodatabase
corporativa: se materializan como un LOTE de staging que un operador puede
revisar, aprobar (dispara la carga real vía ArcPy/REST según PD-02) o revertir.
Esto hace la consolidación auditada y reversible, como exige el documento.
"""
from typing import Optional

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import Timestamps, UUIDPk


class GISStagingBatch(UUIDPk, Timestamps, Base):
    __tablename__ = "gis_staging_batches"

    un_code: Mapped[str] = mapped_column(String(32), index=True)
    work_id: Mapped[Optional[str]] = mapped_column(ForeignKey("works.id"), nullable=True, index=True)

    # PENDING_REVIEW -> QUEUED -> PROCESSING -> LOADED | FAILED | ROLLED_BACK
    status: Mapped[str] = mapped_column(String(24), default="PENDING_REVIEW", index=True)
    element_count: Mapped[int] = mapped_column(Integer, default=0)
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # motivo si FAILED

    # Orden de encolado para procesamiento FIFO (una edición a la vez).
    queue_seq: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)

    # Quién decidió (aprobó/revirtió) y cuándo (updated_at del mixin).
    decided_by_id: Mapped[Optional[str]] = mapped_column(ForeignKey("users.id"), nullable=True)

    elements = relationship("GISStagingElement", back_populates="batch",
                            cascade="all, delete-orphan")


class GISStagingElement(UUIDPk, Timestamps, Base):
    __tablename__ = "gis_staging_elements"

    batch_id: Mapped[str] = mapped_column(ForeignKey("gis_staging_batches.id"), index=True)

    # Operación a aplicar en la geodatabase: CREATE | UPDATE | DELETE.
    operation: Mapped[str] = mapped_column(String(8), default="UPDATE")

    # Preservación de GUID y relación puesto/unidad (§7.2, RN-06/07).
    guid: Mapped[str] = mapped_column(String(64), index=True)
    element_type: Mapped[str] = mapped_column(String(64))
    parent_guid: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    geometry_geojson: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    attributes_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    batch = relationship("GISStagingBatch", back_populates="elements")
