"""Usuario del sistema (web y funcionarios de campo)."""
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.enums import AuthType, Role
from app.models.base import Timestamps, UUIDPk


class User(UUIDPk, Timestamps, Base):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    email: Mapped[Optional[str]] = mapped_column(String(160), nullable=True)
    full_name: Mapped[str] = mapped_column(String(160))
    role: Mapped[Role] = mapped_column(String(32))
    auth_type: Mapped[AuthType] = mapped_column(String(16), default=AuthType.LOCAL)

    # Nulo para usuarios corporativos (SSO); requerido para login local.
    hashed_password: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Segregación: UN propietaria. Nulo permitido para roles Matriz globales.
    un_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("business_units.id"), nullable=True, index=True
    )

    # Control de bloqueo por intentos fallidos (RF-WEB-01.2)
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0)
    locked_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    business_unit = relationship("BusinessUnit", back_populates="users")

    @property
    def is_global_scope(self) -> bool:
        from app.core.enums import GLOBAL_SCOPE_ROLES
        return self.role in {r.value for r in GLOBAL_SCOPE_ROLES} or self.role in GLOBAL_SCOPE_ROLES
