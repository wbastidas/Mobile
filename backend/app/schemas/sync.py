"""Esquemas de sincronización (RF-SYNC, RF-MOV-09/10)."""
from typing import Any, List, Optional

from pydantic import BaseModel

from app.core.enums import ValidationResult


class PhotoMeta(BaseModel):
    """Metadata obligatoria de foto (RN-08)."""
    element_guid: Optional[str] = None
    gps_lat: float
    gps_lon: float
    captured_at: str
    sha256: str
    size_bytes: int = 0
    total_chunks: int = 1


class SyncUploadRequest(BaseModel):
    """Paquete de sincronización subido por el dispositivo (RF-WEB-09)."""
    idempotency_key: str
    work_id: str
    device_uid: str
    schema_version: int = 1
    checksum: Optional[str] = None
    payload_json: str  # elementos/atributos/geometrías
    validation_result: ValidationResult = ValidationResult.NOT_RUN
    validation_report_json: Optional[str] = None
    photos: List[PhotoMeta] = []


class SyncUploadResponse(BaseModel):
    package_id: str
    accepted: bool
    duplicate: bool
    missing_photos: List[str]  # sha256 de fotos aún no recibidas completas
    detail: str


class SyncVerifyResponse(BaseModel):
    work_id: str
    verified: bool
    status: str
    detail: str


class PullResponse(BaseModel):
    """Descarga incremental para el dispositivo (RF-MOV-02, RF-SYNC.7)."""
    new_works: List[Any]
    remote_delete_work_ids: List[str]
    quality_params_version: Optional[int]
    quality_params_rules: Optional[Any]
    schema_version: Optional[int]
