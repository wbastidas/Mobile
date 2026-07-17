"""Adaptador de integración con la geodatabase corporativa (sección 7).

La integración con ArcSDE/Oracle se AÍSLA en este módulo para no acoplar el
resto del sistema (RNF-06). El mecanismo concreto (ArcPy, servicios REST de
ArcGIS, staging en tablas Oracle con aprobación) queda pendiente de definición
(PD-02) y se implementa detrás de esta interfaz.

Se provee una implementación `StubGISAdapter` para desarrollo/pruebas que
simula la extracción y consolidación sin infraestructura ArcGIS.
"""
from __future__ import annotations

import abc
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ExtractedElement:
    guid: str
    element_type: str
    geometry_geojson: Optional[str]
    attributes: Dict[str, Any] = field(default_factory=dict)
    parent_guid: Optional[str] = None


@dataclass
class ConsolidationResult:
    ok: bool
    consolidated_guids: List[str]
    staging_ref: Optional[str] = None  # referencia al respaldo/staging previo (§7.4)
    message: str = ""


class GISAdapter(abc.ABC):
    """Interfaz del adaptador GIS. Origen y destino de los datos (§7.1/7.2)."""

    @abc.abstractmethod
    def extract_by_sector(self, un_code: str, sector_geojson: str) -> List[ExtractedElement]:
        """Extrae elementos dentro de un polígono de sector (REVISION_RED)."""

    @abc.abstractmethod
    def extract_by_guids(self, un_code: str, guids: List[str]) -> List[ExtractedElement]:
        """Extrae elementos específicos por GUID (ORDEN_PUNTUAL)."""

    @abc.abstractmethod
    def consolidate(self, un_code: str, elements: List[ExtractedElement]) -> ConsolidationResult:
        """Consolida cambios verificados hacia ArcSDE/Oracle preservando GUIDs y
        relaciones puesto/unidad (§7.2). Debe ser reversible (staging, §7.4)."""


class StubGISAdapter(GISAdapter):
    """Implementación simulada para desarrollo y pruebas (sin ArcGIS)."""

    def extract_by_sector(self, un_code: str, sector_geojson: str) -> List[ExtractedElement]:
        # Simula dos postes con una luminaria hija dentro del sector.
        return [
            ExtractedElement(
                guid=f"{un_code}-POSTE-0001",
                element_type="POSTE",
                geometry_geojson='{"type":"Point","coordinates":[-78.5,-0.2]}',
                attributes={"material": "HORMIGON", "altura_m": 12},
            ),
            ExtractedElement(
                guid=f"{un_code}-LUM-0001",
                element_type="LUMINARIA",
                geometry_geojson='{"type":"Point","coordinates":[-78.5,-0.2]}',
                attributes={"potencia_w": 150},
                parent_guid=f"{un_code}-POSTE-0001",
            ),
        ]

    def extract_by_guids(self, un_code: str, guids: List[str]) -> List[ExtractedElement]:
        return [
            ExtractedElement(
                guid=g,
                element_type="POSTE",
                geometry_geojson='{"type":"Point","coordinates":[-78.5,-0.2]}',
                attributes={},
            )
            for g in guids
        ]

    def consolidate(self, un_code: str, elements: List[ExtractedElement]) -> ConsolidationResult:
        guids = [e.guid for e in elements]
        return ConsolidationResult(
            ok=True,
            consolidated_guids=guids,
            staging_ref=f"stage://{un_code}/{len(guids)}",
            message=f"Consolidados {len(guids)} elementos (simulado) para {un_code}.",
        )


_adapter: GISAdapter = StubGISAdapter()


def get_gis_adapter() -> GISAdapter:
    """Punto único de acceso al adaptador GIS (inyectable/reemplazable)."""
    return _adapter
