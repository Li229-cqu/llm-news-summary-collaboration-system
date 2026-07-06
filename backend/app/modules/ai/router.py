from __future__ import annotations

from typing import Optional, Union

from fastapi import APIRouter, Depends, File, Header, UploadFile

from app.common.response import ApiResponse, success_response
from app.modules.ai.schema import (
    AIGenerateRecordDetail,
    AIRecordListResponse,
    DeleteAIRecordResult,
    FileUploadResponse,
)
from app.modules.ai.service import (
    delete_ai_record,
    get_ai_record_detail,
    get_ai_records,
    handle_file_upload,
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


@router.get("/health", response_model=ApiResponse[dict])
async def health_ai() -> ApiResponse[dict]:
    """后端 AI 代理健康检查。"""
    return success_response(
        {
            "status": "ok",
            "service": "backend-ai-proxy",
            "upstream": "ai-service",
        }
    )


# ── 以下端点已移除（第一版直连 LLM 路径，已被 Agent 流水线取代） ──
# POST /api/ai/generate      → POST /api/news-editor-agent/run-text
# POST /api/ai/generate/async → POST /api/news-editor-agent/run-text
# GET  /api/ai/generate/async/{task_id}  → SSE /api/news-editor-agent/task/{id}/stream
#
# 保留端点：历史记录查询/详情/删除、文件上传、健康检查


@router.get("/records", response_model=ApiResponse[AIRecordListResponse])
async def get_ai_history(
    current_user: Optional[UserInfo] = Depends(_get_optional_current_user),
) -> ApiResponse[AIRecordListResponse]:
    """获取 AI 生成历史列表。"""
    records = get_ai_records(current_user=current_user)
    return success_response(AIRecordListResponse(records=records, total=len(records)))


@router.get("/records/{record_id}", response_model=ApiResponse[AIGenerateRecordDetail])
async def get_history_detail(
    record_id: Union[int, str],
    current_user: Optional[UserInfo] = Depends(_get_optional_current_user),
) -> ApiResponse[AIGenerateRecordDetail]:
    """获取 AI 生成历史详情。"""
    record = get_ai_record_detail(record_id, current_user=current_user)
    return success_response(record)


@router.delete("/records/{record_id}", response_model=ApiResponse[DeleteAIRecordResult])
async def delete_history(
    record_id: Union[int, str],
    current_user: Optional[UserInfo] = Depends(_get_optional_current_user),
) -> ApiResponse[DeleteAIRecordResult]:
    """删除 AI 生成历史。"""
    success = delete_ai_record(record_id, current_user=current_user)
    if not success:
        from app.common.exceptions import AppException

        raise AppException(code=404, message="历史记录不存在")

    return success_response(DeleteAIRecordResult(success=True, message="历史记录已删除"))


@router.post("/upload", response_model=ApiResponse[FileUploadResponse])
async def upload_file(
    file: UploadFile = File(...),
) -> ApiResponse[FileUploadResponse]:
    """上传文件并提取文本内容。"""
    content = await file.read()
    result = handle_file_upload(content, file.filename)
    return success_response(result)
