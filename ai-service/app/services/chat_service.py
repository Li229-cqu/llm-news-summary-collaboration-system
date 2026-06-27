import logging
from app.common.exceptions import AIServiceException
from app.core.config import settings
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.llm_client import call_llm

logger = logging.getLogger(__name__)


def chat(request: ChatRequest) -> ChatResponse:
    """调用 AI 模型回答新闻相关问题。"""
    if not request.question.strip():
        raise AIServiceException(code=400, message="问题不能为空")

    # 如果 LLM 未启用，返回 mock 数据
    if not settings.llm_enabled:
        logger.info("🤖 [MOCK MODE] 返回模拟 AI 回答（LLM 未启用）")
        from app.mock.sample_outputs import CHAT_OUTPUT
        return ChatResponse(**CHAT_OUTPUT)

    # 构造消息列表
    messages = [
        {
            "role": "system",
            "content": request.context or "你是一个专业的AI新闻助手，专注于回答新闻相关问题。请根据用户的问题提供简洁、准确、有价值的回答。如果用户的问题与新闻无关，请礼貌地引导他们回到新闻话题。"
        },
        {
            "role": "user",
            "content": request.question
        }
    ]

    try:
        # 调用 LLM
        logger.info("🚀 [REAL API] 调用真实大语言模型 API...")
        answer = call_llm(messages)
        logger.info("✅ [REAL API] 大模型 API 调用成功")
        return ChatResponse(
            answer=answer,
            recommended_questions=[
                "请问有什么新闻热点吗？",
                "如何获取新闻摘要？",
                "推荐相关新闻内容"
            ]
        )
    except Exception as e:
        # LLM 调用失败，返回默认回答
        logger.error(f"❌ [REAL API] 大模型 API 调用失败: {str(e)}")
        return ChatResponse(
            answer=f"抱歉，AI 服务暂时无法回答。错误信息：{str(e)}",
            recommended_questions=[
                "请问有什么新闻热点吗？",
                "如何获取新闻摘要？",
                "推荐相关新闻内容"
            ]
        )
