import httpx

from app.common.exceptions import AppException
from app.core.config import settings
from app.modules.ai.schema import (
    AIGenerateRequest,
    AIGenerateResponse,
    AIGenerateRecordItem,
    AIGenerateRecordDetail,
)
from app.mock.ai_records import get_all_records, get_record_by_id, delete_record

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


def get_ai_records() -> list[AIGenerateRecordItem]:
    """获取 AI 生成历史列表。"""
    all_records = get_all_records()
    return [
        AIGenerateRecordItem(
            id=record["id"],
            source=record["source"],
            source_news_id=record.get("source_news_id"),
            source_title=record["source_title"],
            title_count=record["title_count"],
            risk_level=record["risk_level"],
            created_at=record["created_at"],
        )
        for record in all_records
    ]


def get_ai_record_detail(record_id: int | str) -> AIGenerateRecordDetail:
    """获取 AI 生成历史详情。"""
    record = get_record_by_id(record_id)
    if not record:
        raise AppException(code=404, message="历史记录不存在")

    return AIGenerateRecordDetail(
        id=record["id"],
        source=record["source"],
        source_news_id=record.get("source_news_id"),
        source_title=record["source_title"],
        input_text=record["input_text"],
        params=record["params"],
        result=AIGenerateResponse(**record["result"]),
        created_at=record["created_at"],
    )


def delete_ai_record(record_id: int | str) -> bool:
    """删除 AI 生成历史。"""
    return delete_record(record_id)
