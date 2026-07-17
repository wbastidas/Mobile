"""Punto de entrada de la aplicación FastAPI.

Sistema de Gestión y Levantamiento de Datos Eléctricos en Campo — Backend API.
Base compartida por la Plataforma Web (WEB-ADMIN) y la App Móvil (APP-CAMPO).
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import Base, engine

# Importa los modelos para que se registren en el metadata antes de create_all.
import app.models  # noqa: F401


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version="1.0.0",
        description="API del Sistema de Levantamiento Eléctrico en Campo.",
        openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
        docs_url="/docs",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # En desarrollo se crean las tablas automáticamente. En producción se usan
    # migraciones (Alembic) contra PostgreSQL/PostGIS.
    if settings.DATABASE_URL.startswith("sqlite"):
        Base.metadata.create_all(bind=engine)

    app.include_router(api_router, prefix=settings.API_V1_PREFIX)

    @app.get("/health", tags=["health"])
    def health():
        return {"status": "ok", "app": settings.APP_NAME, "env": settings.APP_ENV}

    return app


app = create_app()
