"""Router agregador de la API v1."""
from fastapi import APIRouter

from app.api.v1 import (
    audit,
    auth,
    business_units,
    dashboard,
    devices,
    elements,
    quality,
    sync,
    users,
    works,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(business_units.router)
api_router.include_router(users.router)
api_router.include_router(devices.router)
api_router.include_router(works.router)
api_router.include_router(sync.router)
api_router.include_router(quality.router)
api_router.include_router(elements.router)
api_router.include_router(audit.router)
api_router.include_router(dashboard.router)
