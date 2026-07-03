import logging
import sys
from app.common.exceptions import AIServiceException
from app.core.config import settings
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.llm_client import call_summary_llm, call_summary_llm_stream

logger = logging.getLogger(__name__)


async def chat(request: ChatRequest) -> ChatResponse:
    """调用 AI 模型回答新闻相关问题。"""
    if not request.question.strip():
        raise AIServiceException(code=400, message="问题不能为空")

    print(f"[CHAT SERVICE] Request received: question={request.question[:20]}...", file=sys.stderr)
    
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
        print(f"[CHAT SERVICE] Calling LLM...", file=sys.stderr)
        answer = await call_summary_llm(messages)
        print(f"[CHAT SERVICE] LLM response: {answer[:50]}...", file=sys.stderr)
        return ChatResponse(
            answer=answer,
            recommended_questions=[
                "请问有什么新闻热点吗？",
                "如何获取新闻摘要？",
                "推荐相关新闻内容"
            ],
            source="llm"
        )
    except Exception as e:
        print(f"[CHAT SERVICE] LLM error: {type(e).__name__}: {e}", file=sys.stderr)
        from app.mock.sample_outputs import CHAT_OUTPUT
        return ChatResponse(**CHAT_OUTPUT, source="mock")


async def chat_stream(request: ChatRequest):
    """流式调用 AI 模型回答问题，逐 token yield。

    返回 dict 流，每个 dict 可能是：
    - {"token": "字"}  -- 单个 token
    - {"done": True}   -- 流结束
    - {"error": "..."} -- 异常
    """
    if not request.question.strip():
        yield {"error": "问题不能为空", "done": True}
        return

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
        logger.info("🚀 [CHAT SERVICE STREAM] 调用流式 LLM...")
        async for token in call_summary_llm_stream(messages):
            if token:
                yield {"token": token}
        yield {"done": True}
        logger.info("✅ [CHAT SERVICE STREAM] 流式调用完成")
    except Exception as e:
        logger.error(f"❌ [CHAT SERVICE STREAM] 流式调用失败: {str(e)}")
        yield {"error": str(e), "done": True}
