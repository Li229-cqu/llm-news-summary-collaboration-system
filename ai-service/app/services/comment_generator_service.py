import logging
from app.common.exceptions import AIServiceException
from app.core.config import settings
from app.services.llm_client import call_summary_llm

logger = logging.getLogger(__name__)


def generate_comment_mock(topic: str, context: str = "", sentiment: str = "neutral") -> str:
    mock_comments = {
        "positive": [
            "非常赞同！这个观点很有见地，希望能看到更多相关讨论。",
            "说得太好了，完全支持！",
            "分析得很透彻，受益匪浅。",
            "很有价值的分享，谢谢！",
        ],
        "negative": [
            "不太认同这个观点，有不同看法。",
            "这个说法有待商榷，实际情况可能更复杂。",
            "不同意以上观点，理由如下：",
            "这种说法过于片面了。",
        ],
        "neutral": [
            "这个话题很有意思，可以进一步讨论。",
            "感谢分享，了解了很多新信息。",
            "从不同角度看都有道理。",
            "期待更多相关内容。",
        ],
    }
    return mock_comments.get(sentiment, mock_comments["neutral"])[0]


async def generate_comment(topic: str, context: str = "", sentiment: str = "neutral") -> str:
    if not topic or not topic.strip():
        raise AIServiceException(code=400, message="评论主题不能为空")

    if not settings.summary_llm_enabled:
        logger.info("LLM 未启用，使用 mock 生成评论")
        return generate_comment_mock(topic, context, sentiment)

    sentiment_prompt = {
        "positive": "正面、支持、赞赏的",
        "negative": "负面、质疑、批评的",
        "neutral": "中立、客观、理性的",
    }

    messages = [
        {
            "role": "system",
            "content": """你是一个专业的评论助手。请根据用户提供的话题和上下文，生成一条合适的评论。

要求：
1. 评论要自然、真实，像普通用户发表的
2. 长度在50-150字之间
3. 语气要符合指定的情感倾向
4. 不要使用过于正式或生硬的语言
5. 如果有上下文，请结合上下文内容进行评论"""
        },
        {
            "role": "user",
            "content": f"""请帮我生成一条{sentiment_prompt.get(sentiment, "中立")}评论。

话题：{topic}

上下文（可选）：{context if context else "无"}"""
        }
    ]

    try:
        logger.info("调用 LLM 生成评论")
        llm_response = await call_summary_llm(messages)
        logger.info("LLM 调用成功")
        return llm_response.strip()
    except Exception as e:
        logger.warning(f"LLM 调用失败，fallback 到 mock: {type(e).__name__}: {str(e)}")
        return generate_comment_mock(topic, context, sentiment)
