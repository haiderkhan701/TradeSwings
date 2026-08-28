from fastapi import APIRouter

from app.api.routes.health import router as health_router
from app.api.routes.instruments import router as instruments_router
from app.api.routes.upstox import router as upstox_router

api_router = APIRouter()
api_router.include_router(health_router, prefix="/health", tags=["health"])
api_router.include_router(upstox_router, prefix="/upstox", tags=["upstox"])
api_router.include_router(instruments_router, prefix="/instruments", tags=["instruments"])
