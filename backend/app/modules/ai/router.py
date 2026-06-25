from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Header

from app.common.response import ApiResponse, success_response
from app.modules.ai.schema import (
    AIGenerateRecordDetail,
    AIGenerateRequest,
    AIGenerateResponse,
    AIRecordListResponse,
    DeleteAIRecordResult,
)
from app.modules.ai.service import (
    delete_ai_record,
    generate_title_summary,
    get_ai_record_detail,
    get_ai_records,
)
from app.modules.auth.schema import UserInfo
from app.modules.auth.service import get_mock_user_by_token

router = APIRouter(prefix="/api/ai", tags=["ai"])


async def _get_optional_current_user(
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
) -> Optional[UserInfo]:
    if not authorization or not authorization.startswith("Bearer "):
        return None

    token = authorization.removeprefix("Bearer ").strip()
    return get_mock_user_by_token(token)


@router.get("/ping", response_model=ApiResponse[str])
async def ping_ai() -> ApiResponse[str]:
    return success_response("ai module ok")


@router.post("/generate", response_model=ApiResponse[AIGenerateResponse])
async def generate_ai_content(
    request: AIGenerateRequest,
    current_user: Optional[UserInfo] = Depends(_get_optional_current_user),
) -> ApiResponse[AIGenerateResponse]:
    """转发标题摘要生成请求到 ai-service，并在后端保存生成记录。"""
    return success_response(await generate_title_summary(request, current_user=current_user))


@router.get("/records", response_model=ApiResponse[AIRecordListResponse])
async def get_ai_history(
    current_user: Optional[UserInfo] = Depends(_get_optional_current_user),
) -> ApiResponse[AIRecordListResponse]:
    """获取 AI 生成历史列表。"""
    records = get_ai_records(current_user=current_user)
    return success_response(AIRecordListResponse(records=records, total=len(records)))


@router.get("/records/{record_id}", response_model=ApiResponse[AIGenerateRecordDetail])
async def get_history_detail(
    record_id: int | str,
    current_user: Optional[UserInfo] = Depends(_get_optional_current_user),
) -> ApiResponse[AIGenerateRecordDetail]:
    """获取 AI 生成历史详情。"""
    record = get_ai_record_detail(record_id, current_user=current_user)
    return success_response(record)


@router.delete("/records/{record_id}", response_model=ApiResponse[DeleteAIRecordResult])
async def delete_history(
    record_id: int | str,
    current_user: Optional[UserInfo] = Depends(_get_optional_current_user),
) -> ApiResponse[DeleteAIRecordResult]:
    """删除 AI 生成历史。"""
    success = delete_ai_record(record_id, current_user=current_user)
    if not success:
        from app.common.exceptions import AppException

        raise AppException(code=404, message="历史记录不存在")

    return success_response(DeleteAIRecordResult(success=True, message="历史记录已删除"))
