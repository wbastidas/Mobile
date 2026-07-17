"""Parámetros de calidad versionados (RF-WEB-10) y esquema dirigido por metadatos.

- QualityParamSet: archivo de reglas de validación (JSON) versionado que la app
  móvil descarga y ejecuta localmente (RF-MOV-09).
- SchemaDefinition: definición versionada del modelo eléctrico (capas, campos,
  dominios, formularios) que dirige la generación de GPKG/formularios (§6.4).
"""
from typing import Optional

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import Timestamps, UUIDPk


class QualityParamSet(UUIDPk, Timestamps, Base):
    __tablename__ = "quality_param_sets"

    version: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Reglas por tipo de trabajo/elemento en JSON (RF-WEB-10.2).
    rules_json: Mapped[str] = mapped_column(Text)

    is_active: Mapped[bool] = mapped_column(Boolean, default=False)  # versión vigente
    uploaded_by_id: Mapped[Optional[str]] = mapped_column(ForeignKey("users.id"), nullable=True)


class SchemaDefinition(UUIDPk, Timestamps, Base):
    """Modelado dirigido por metadatos (modelo de datos §6.4)."""
    __tablename__ = "schema_definitions"

    version: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Definición de capas/campos/dominios/formularios/relaciones puesto-unidad.
    definition_json: Mapped[str] = mapped_column(Text)

    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
