from fastapi import APIRouter

from app.common.response import success_response
from app.core.config import reload_settings_from_env, settings

router = APIRouter(prefix=settings.api_prefix, tags=["系统"])


@router.get("/health")
async def health_check():
    return success_response(
        {
            "status": "ok",
            "service": "ai-service",
            "mode": settings.ai_mode,
            "project": settings.project_name,
            "summary_llm_enabled": settings.summary_llm_enabled,
            "evidence_llm_enabled": settings.evidence_llm_enabled,
            "llm_enabled": settings.summary_llm_enabled,
            "timeout": settings.summary_llm_timeout,
        }
    )


@router.post("/config/reload")
async def reload_config():
    """重新从后端加载 AI 配置，支持运行时动态更新。"""
    reload_settings_from_env(settings)
    return success_response(
        {
            "message": "配置已重新加载",
            "summary_llm_enabled": settings.summary_llm_enabled,
            "evidence_llm_enabled": settings.evidence_llm_enabled,
            "llm_enabled": settings.summary_llm_enabled,
            "timeout": settings.summary_llm_timeout,
        }
    )
