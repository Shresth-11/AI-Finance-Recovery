from fastapi import APIRouter
from app.api.v1.endpoints import health, datasets, reconciliation, dashboard, exceptions, copilot

api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(datasets.router)
api_router.include_router(reconciliation.router)
api_router.include_router(dashboard.router)
api_router.include_router(exceptions.router)
api_router.include_router(copilot.router, prefix="/copilot", tags=["Copilot"])
