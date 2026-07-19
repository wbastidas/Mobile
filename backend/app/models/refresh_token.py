"""Refresh tokens persistidos para rotación y revocación (RNF-01).

Cada refresh token emitido lleva un `jti` (el id de esta fila). Al usarse se
revoca y se emite uno nuevo (rotación). Si se presenta un token ya revocado se
asume robo/replay y se revocan TODOS los tokens del usuario (detección de reuso).
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import Timestamps, UUIDPk


class RefreshToken(UUIDPk, Timestamps, Base):
    __tablename__ = "refresh_tokens"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    # jti del token que lo reemplazó al rotar (trazabilidad de la cadena).
    replaced_by: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
