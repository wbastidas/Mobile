"""Registro de todos los modelos ORM (importa para que SQLAlchemy los conozca)."""
from app.models.audit_log import AuditLog
from app.models.business_unit import BusinessUnit
from app.models.device import Device
from app.models.element import Element, WorkElement
from app.models.element_log import ElementLog
from app.models.field_change import FieldChange
from app.models.gis_staging import GISStagingBatch, GISStagingElement
from app.models.quality_novelty import QualityNovelty
from app.models.refresh_token import RefreshToken
from app.models.quality_params import QualityParamSet, SchemaDefinition
from app.models.sync import Photo, RemoteDeleteOrder, SyncPackage
from app.models.user import User
from app.models.work import Work

__all__ = [
    "AuditLog",
    "BusinessUnit",
    "Device",
    "Element",
    "WorkElement",
    "ElementLog",
    "FieldChange",
    "GISStagingBatch",
    "GISStagingElement",
    "QualityNovelty",
    "QualityParamSet",
    "RefreshToken",
    "SchemaDefinition",
    "Photo",
    "RemoteDeleteOrder",
    "SyncPackage",
    "User",
    "Work",
]
