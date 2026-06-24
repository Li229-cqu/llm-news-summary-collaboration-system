import httpx

from app.common.exceptions import AppException
from app.core.config import settings
from app.modules.ai.schema import AIGenerateRequest, AIGenerateResponse

AI_SERVICE_UNAVAILABLE_MESSAGE = "AI 服务暂时不可用，请稍后重试"


async def generate_title_summary(request: AIGenerateRequest) -> AIGenerateResponse:
    """调用 ai-service 的固定 Mock 标题摘要接口。"""
    endpoint = f"{settings.ai_service_url.rstrip('/')}/ai/generate-title-summary"

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(endpoint, json=request.model_dump())
            response.raise_for_status()
            result = response.json()
    except (httpx.HTTPError, ValueError):
        raise AppException(code=503, message=AI_SERVICE_UNAVAILABLE_MESSAGE)

    if result.get("code") != 200:
        raise AppException(
            code=result.get("code", 503),
            message=result.get("message", AI_SERVICE_UNAVAILABLE_MESSAGE),
        )

    try:
        return AIGenerateResponse(**result["data"])
    except (KeyError, TypeError, ValueError):
        raise AppException(code=503, message=AI_SERVICE_UNAVAILABLE_MESSAGE)
