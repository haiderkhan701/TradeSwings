from fastapi import APIRouter

from app.core.config import settings

router = APIRouter()


@router.get("")
def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "service": settings.app_name,
        "environment": settings.app_env,
        "mode": "read-only",
    }
