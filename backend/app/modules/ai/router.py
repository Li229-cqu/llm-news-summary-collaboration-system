from fastapi import APIRouter

from app.common.response import ApiResponse, success_response
from app.modules.ai.schema import AIGenerateRequest, AIGenerateResponse
from app.modules.ai.service import generate_title_summary

router = APIRouter(prefix="/api/ai", tags=["ai"])


@router.get("/ping", response_model=ApiResponse[str])
async def ping_ai() -> ApiResponse[str]:
    return success_response("ai module ok")


@router.post("/generate", response_model=ApiResponse[AIGenerateResponse])
async def generate_ai_content(request: AIGenerateRequest) -> ApiResponse[AIGenerateResponse]:
    """转发标题摘要生成请求至 ai-service。"""
    return success_response(await generate_title_summary(request))
