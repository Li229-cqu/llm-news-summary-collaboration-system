from fastapi import APIRouter, HTTPException

from app.common.response import ApiResponse, success_response
from app.modules.ai.schema import (
    AIGenerateRequest,
    AIGenerateResponse,
    AIRecordListResponse,
    AIGenerateRecordDetail,
    DeleteAIRecordResult,
)
from app.modules.ai.service import (
    generate_title_summary,
    get_ai_records,
    get_ai_record_detail,
    delete_ai_record,
)

router = APIRouter(prefix="/api/ai", tags=["ai"])


@router.get("/ping", response_model=ApiResponse[str])
async def ping_ai() -> ApiResponse[str]:
    return success_response("ai module ok")


@router.post("/generate", response_model=ApiResponse[AIGenerateResponse])
async def generate_ai_content(request: AIGenerateRequest) -> ApiResponse[AIGenerateResponse]:
    """转发标题摘要生成请求至 ai-service。"""
    return success_response(await generate_title_summary(request))


@router.get("/records", response_model=ApiResponse[AIRecordListResponse])
async def get_ai_history() -> ApiResponse[AIRecordListResponse]:
    """获取 AI 生成历史列表。"""
    records = get_ai_records()
    return success_response(
        AIRecordListResponse(records=records, total=len(records))
    )


@router.get("/records/{record_id}", response_model=ApiResponse[AIGenerateRecordDetail])
async def get_history_detail(record_id: int | str) -> ApiResponse[AIGenerateRecordDetail]:
    """获取 AI 生成历史详情。"""
    record = get_ai_record_detail(record_id)
    return success_response(record)


@router.delete("/records/{record_id}", response_model=ApiResponse[DeleteAIRecordResult])
async def delete_history(record_id: int | str) -> ApiResponse[DeleteAIRecordResult]:
    """删除 AI 生成历史。"""
    success = delete_ai_record(record_id)
    if not success:
        raise HTTPException(status_code=404, detail="历史记录不存在")
    return success_response(
        DeleteAIRecordResult(success=True, message="历史记录已删除")
    )
