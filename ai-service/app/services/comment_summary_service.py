import logging
import re

from app.common.exceptions import AIServiceException
from app.core.config import settings
from app.schemas.comment_summary import CommentSummaryRequest, CommentSummaryResponse
from app.services.llm_client import call_llm

logger = logging.getLogger(__name__)


def _extract_keywords(text: str, max_keywords: int = 5) -> list[str]:
    words = re.findall(r'[一-鿿]{2,}', text)
    keyword_freq = {}
    for word in words:
        keyword_freq[word] = keyword_freq.get(word, 0) + 1
    sorted_keywords = sorted(keyword_freq.items(), key=lambda x: (-x[1], -len(x[0])))
    return [word for word, _ in sorted_keywords[:max_keywords]]


def _analyze_sentiment(text: str) -> str:
    positive_words = ["支持", "赞同", "好", "棒", "赞", "喜欢", "满意", "精彩", "优秀", "不错", "推荐", "认可", "肯定"]
    negative_words = ["反对", "不赞同", "差", "垃圾", "烂", "讨厌", "失望", "糟糕", "问题", "不满", "投诉", "批评"]
    pos_count = sum(1 for word in positive_words if word in text)
    neg_count = sum(1 for word in negative_words if word in text)
    if pos_count > neg_count:
        return "positive"
    elif neg_count > pos_count:
        return "negative"
    return "neutral"


def summarize_comments_mock(request: CommentSummaryRequest) -> CommentSummaryResponse:
    if not request.comments:
        return CommentSummaryResponse(
            summary="暂无评论可总结",
            sentiment="neutral",
            keywords=[],
            key_points=[],
            source="fallback"
        )

    all_text = "\n".join(request.comments)
    sentiment = _analyze_sentiment(all_text)
    keywords = _extract_keywords(all_text)

    key_points = []
    for i, comment in enumerate(request.comments[:3], 1):
        if comment.strip():
            key_points.append(f"观点{i}：{comment[:50]}")

    summary = f"该话题共有 {len(request.comments)} 条评论。整体情感倾向为{'正面' if sentiment == 'positive' else '负面' if sentiment == 'negative' else '中立'}。主要讨论热点包括：{('、'.join(keywords)) if keywords else '暂无明显热点'}。建议查看完整评论了解详细观点。"

    return CommentSummaryResponse(
        summary=summary,
        sentiment=sentiment,
        keywords=keywords,
        key_points=key_points,
        source="fallback"
    )


def summarize_comments(request: CommentSummaryRequest) -> CommentSummaryResponse:
    if not request.comments:
        raise AIServiceException(code=400, message="评论列表不能为空")

    if not settings.llm_enabled:
        logger.info("LLM 未启用，使用 mock 生成评论总结")
        return summarize_comments_mock(request)

    comments_text = "\n".join([f"{i+1}. {comment}" for i, comment in enumerate(request.comments)])

    messages = [
        {
            "role": "system",
            "content": """你是一个专业的评论区分析师。请对以下用户评论进行总结分析。

要求：
1. 总结主要观点（不超过3点）
2. 判断整体情感倾向（正面/负面/中立）
3. 提取讨论热点关键词（不超过5个）
4. 生成一段200字以内的评论摘要
5. 输出格式为JSON，包含以下字段：summary, sentiment, keywords, key_points
6. sentiment的值只能是：positive, negative, neutral
7. keywords是字符串数组
8. key_points是字符串数组"""
        },
        {
            "role": "user",
            "content": f"请分析以下评论：\n\n{comments_text}"
        }
    ]

    try:
        logger.info("调用 LLM 生成评论总结")
        llm_response = call_llm(messages)
        logger.info("LLM 调用成功")

        try:
            import json
            response_text = llm_response.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:-3].strip()
            elif response_text.startswith("```"):
                response_text = response_text[3:-3].strip()
            data = json.loads(response_text)

            return CommentSummaryResponse(
                summary=data.get("summary", ""),
                sentiment=data.get("sentiment", "neutral"),
                keywords=data.get("keywords", []),
                key_points=data.get("key_points", []),
                source="llm"
            )
        except json.JSONDecodeError:
            logger.warning("LLM 返回非 JSON 格式，fallback 到 mock")
            return summarize_comments_mock(request)

    except Exception as e:
        logger.warning(f"LLM 调用失败，fallback 到 mock: {type(e).__name__}: {str(e)}")
        return summarize_comments_mock(request)