import json
import sys
import logging

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.common.response import ApiResponse, success_response
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import chat_stream
from app.services.llm_client import call_summary_llm

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["AI对话"])


@router.post("/chat", response_model=ApiResponse[ChatResponse])
async def chat_route(request: ChatRequest) -> ApiResponse[ChatResponse]:
    print(f"[DEBUG] chat_route called: question={request.question[:20]}...", file=sys.stderr)
    
    messages = [
        {
            "role": "system",
            "content": request.context or "你是一个专业的AI新闻助手，专注于回答新闻相关问题。请根据用户的问题提供简洁、准确、有价值的回答。"
        },
        {
            "role": "user",
            "content": request.question
        }
    ]

    try:
        print(f"[DEBUG] Calling call_summary_llm...", file=sys.stderr)
        answer = await call_summary_llm(messages)
        print(f"[DEBUG] LLM response: {answer[:50]}...", file=sys.stderr)
        return success_response(ChatResponse(
            answer=answer,
            recommended_questions=[
                "请问有什么新闻热点吗？",
                "如何获取新闻摘要？",
                "推荐相关新闻内容"
            ],
            source="llm"
        ))
    except Exception as e:
        print(f"[DEBUG] LLM error: {type(e).__name__}: {e}", file=sys.stderr)
        from app.mock.sample_outputs import CHAT_OUTPUT
        return success_response(ChatResponse(**CHAT_OUTPUT, source="mock"))


@router.post("/chat/stream")
async def chat_stream_route(request: ChatRequest):
    """SSE 流式对话：逐 token 返回 AI 回答。"""

    async def event_generator():
        async for chunk in chat_stream(request):
            yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
