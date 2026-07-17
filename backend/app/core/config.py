"""Configuración central de la aplicación.

Carga variables de entorno con Pydantic Settings. En producción la base de
datos objetivo es PostgreSQL + PostGIS; para desarrollo/pruebas se usa SQLite
por defecto para poder ejecutar sin infraestructura externa.
"""
from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- Aplicación ---
    APP_NAME: str = "Sistema de Levantamiento Eléctrico - API"
    APP_ENV: str = "development"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = True

    # --- Base de datos ---
    # Producción: postgresql+psycopg://user:pass@host:5432/levantamiento
    DATABASE_URL: str = "sqlite:///./levantamiento.db"

    # --- Seguridad / JWT ---
    SECRET_KEY: str = "CHANGE_ME_IN_PRODUCTION_use_a_long_random_secret"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 8  # 8 horas, configurable
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7

    # --- Política de contraseñas (login local, RF-WEB-01.2) ---
    PASSWORD_MIN_LENGTH: int = 10
    MAX_FAILED_LOGIN_ATTEMPTS: int = 5
    LOCKOUT_MINUTES: int = 15

    # --- Autenticación corporativa (RF-WEB-01.1) ---
    # Placeholders; el mecanismo real (LDAP/SAML/OIDC) se define en PD-05.
    CORPORATE_AUTH_ENABLED: bool = False
    LDAP_SERVER_URI: str = ""

    # --- CORS ---
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    # --- Sincronización ---
    UPLOAD_CHUNK_MAX_BYTES: int = 5 * 1024 * 1024  # 5 MB por chunk


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
