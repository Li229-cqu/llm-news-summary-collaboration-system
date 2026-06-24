from fastapi import APIRouter

from app.common.response import success_response
from app.core.config import settings

router = APIRouter(prefix=settings.api_prefix, tags=["系统"])


@router.get("/health")
async def health_check():
    return success_response(
        {
            "status": "ok",
            "service": "ai-service",
            "mode": settings.ai_mode,
            "project": settings.project_name,
        }
    )
