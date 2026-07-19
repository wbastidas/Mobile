"""Elemento del modelo eléctrico y su vínculo con los trabajos.

- Element: entidad del modelo eléctrico (poste, transformador, luminaria, ...),
  identificada por GUID (RN-06) y con relación puesto/unidad padre-hijo (RN-07).
- WorkElement: los elementos involucrados en un trabajo (empaque geometría +
  atributos, RF-WEB-04.5), con estado de captura en campo.
"""
from typing import Optional

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import Timestamps, UUIDPk


class Element(UUIDPk, Timestamps, Base):
    __tablename__ = "elements"

    # GUID único e inmutable del modelo eléctrico (RN-06). Coincide con id.
    guid: Mapped[str] = mapped_column(String(64), unique=True, index=True)

    # Tipo/capa del modelo eléctrico vigente (dirigido por metadatos, §6.4).
    element_type: Mapped[str] = mapped_column(String(64), index=True)

    un_id: Mapped[str] = mapped_column(ForeignKey("business_units.id"), index=True)

    # Relación puesto/unidad: elemento padre (RN-07).
    parent_guid: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)

    # Geometría en GeoJSON (producción: PostGIS geometry). Puede ser solo punto
    # en el modo "solo punto + fotos" (RF-MOV-07).
    geometry_geojson: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Atributos dinámicos según el esquema versionado (§6.4), como JSON serializado.
    attributes_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    is_new: Mapped[bool] = mapped_column(Boolean, default=False)  # capturado en campo
    # Marca de baja lógica: el elemento fue eliminado en campo (la eliminación
    # física en la geodatabase la aplica el editor). Preserva la bitácora/FK.
    deleted: Mapped[bool] = mapped_column(Boolean, default=False)

    logs = relationship("ElementLog", back_populates="element", cascade="all, delete-orphan")


class WorkElement(UUIDPk, Timestamps, Base):
    """Elemento incluido en un trabajo (paquete de asignación)."""
    __tablename__ = "work_elements"

    work_id: Mapped[str] = mapped_column(ForeignKey("works.id"), index=True)
    element_guid: Mapped[str] = mapped_column(String(64), index=True)

    # Estado de captura en el trabajo.
    completed: Mapped[bool] = mapped_column(Boolean, default=False)

    # Snapshot de geometría + atributos empaquetados para el dispositivo.
    geometry_geojson: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    attributes_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    work = relationship("Work", back_populates="elements")
