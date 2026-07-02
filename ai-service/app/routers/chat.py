from fastapi import APIRouter

from app.common.response import ApiResponse, success_response
from app.core.config import settings
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import chat

router = APIRouter(prefix=settings.api_prefix, tags=["AI 新闻助手"])


@router.post("/chat", response_model=ApiResponse[ChatResponse])
async def chat_with_assistant(request: ChatRequest) -> ApiResponse[ChatResponse]:
    return success_response(await chat(request))
