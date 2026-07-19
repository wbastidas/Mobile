"""Adaptador GIS de staging: consolidación reversible con revisión (§7.2/7.4).

`consolidate()` NO escribe en ArcSDE/Oracle directamente: materializa el cambio
como un lote (`GISStagingBatch` + `GISStagingElement`) en estado PENDING_REVIEW.
Un operador lo aprueba (dispara la carga real — ArcPy/REST según PD-02, ver
`docs/INTEGRACION_ARCSDE.md`) o lo revierte. Los GUIDs y la relación
puesto/unidad se preservan tal cual (RN-06/07).

La extracción (origen) se hereda del stub hasta que PD-02 defina el mecanismo
de lectura (vistas Oracle / servicios ArcGIS).
"""
from __future__ import annotations

import json
from typing import Any, List, Optional

from app.models.gis_staging import GISStagingBatch, GISStagingElement
from app.modules.gis.adapter import ConsolidationResult, ExtractedElement, StubGISAdapter


class StagingGISAdapter(StubGISAdapter):

    def consolidate(self, un_code: str, elements: List[ExtractedElement],
                    db: Any = None, work_id: Optional[str] = None) -> ConsolidationResult:
        if db is None:
            # Sin sesión no hay dónde persistir el lote de forma atómica.
            return ConsolidationResult(ok=False, consolidated_guids=[],
                                       message="Adaptador de staging requiere sesión de BD.")

        batch = GISStagingBatch(
            un_code=un_code,
            work_id=work_id,
            status="PENDING_REVIEW",
            element_count=len(elements),
            message=f"Lote de consolidación para {un_code} ({len(elements)} elementos).",
        )
        db.add(batch)
        db.flush()

        for e in elements:
            db.add(GISStagingElement(
                batch_id=batch.id,
                guid=e.guid,
                element_type=e.element_type,
                parent_guid=e.parent_guid,
                geometry_geojson=e.geometry_geojson,
                attributes_json=json.dumps(e.attributes, ensure_ascii=False),
            ))

        return ConsolidationResult(
            ok=True,
            consolidated_guids=[e.guid for e in elements],
            staging_ref=batch.id,
            message=f"Lote {batch.id} en revisión ({len(elements)} elementos).",
        )
