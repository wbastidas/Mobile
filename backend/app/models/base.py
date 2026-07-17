"""Mixins comunes para los modelos ORM."""
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


class UUIDPk:
    """Clave primaria tipo GUID (RN-06: identificador único e inmutable)."""
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)


class Timestamps:
    """Marcas de tiempo de creación/actualización."""
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now
    )
