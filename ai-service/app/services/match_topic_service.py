"""话题匹配服务 — Phase 5: 接入 LLM 真实调用。"""
from __future__ import annotations
import json
import logging

from app.common.exceptions import AIServiceException
from app.core.config import settings
from app.schemas.match_topic import MatchTopicRequest, MatchTopicResponse
from app.services.llm_client import call_summary_llm

logger = logging.getLogger(__name__)

MOCK_TOPIC = {
    "primary_topic": "科技政策",
    "secondary_topics": ["人工智能", "产业经济"],
    "confidence": 0.92,
    "matched_from": "预定义话题库",
}

TOPIC_CATEGORIES = [
    "科技政策", "国际经济", "社会民生", "文化教育",
    "军事安全", "体育竞技", "娱乐影视", "医疗健康",
    "环境保护", "法律法规", "金融财经", "其他",
]


def _build_topic_prompt(text: str, keywords: list[str], elements_what: str, title: str) -> str:
    cats = "、".join(TOPIC_CATEGORIES)
    kw = "、".join(keywords) if keywords else "无"
    return f"""你是一个新闻分类专家。请根据以下信息将新闻归类到最匹配的话题。

可选话题类别：{cats}

关键词：{kw}
核心事件：{elements_what or "未知"}
候选标题：{title or "未知"}
正文片段：{text[:800]}

请严格返回 JSON 格式：
{{"primary_topic": "主话题", "secondary_topics": ["次话题1", "次话题2"], "confidence": 0.0-1.0}}"""


def _parse_topic_response(raw: str) -> dict:
    """解析 LLM 返回的话题 JSON。"""
    raw = raw.strip()
    # 尝试提取 JSON 块
    if "```json" in raw:
        raw = raw.split("```json")[1].split("```")[0]
    elif "```" in raw:
        raw = raw.split("```")[1].split("```")[0]
    try:
        data = json.loads(raw)
        return {
            "primary_topic": data.get("primary_topic", "未分类"),
            "secondary_topics": data.get("secondary_topics", []),
            "confidence": float(data.get("confidence", 0.7)),
            "matched_from": "LLM 实时分类",
        }
    except (json.JSONDecodeError, ValueError, KeyError):
        # 正则提取
        import re
        pt = re.search(r'"primary_topic"\s*:\s*"([^"]+)"', raw)
        conf = re.search(r'"confidence"\s*:\s*([\d.]+)', raw)
        return {
            "primary_topic": pt.group(1) if pt else "未分类",
            "secondary_topics": [],
            "confidence": float(conf.group(1)) if conf else 0.7,
            "matched_from": "LLM 实时分类（fallback 解析）",
        }


async def match_topic(request: MatchTopicRequest) -> MatchTopicResponse:
    if not request.text.strip():
        raise AIServiceException(code=400, message="新闻文本不能为空")

    # 如果 LLM 启用，调用真实模型
    if settings.summary_llm_enabled:
        try:
            prompt = _build_topic_prompt(
                request.text, request.keywords, request.elements_what, request.title
            )
            messages = [{"role": "user", "content": prompt}]
            raw_response = await call_summary_llm(messages, temperature=0.2, max_tokens=512)
            logger.info(f"话题匹配 LLM 原始响应: {raw_response[:200]}")
            result = _parse_topic_response(raw_response)
            return MatchTopicResponse(**result)
        except Exception as e:
            logger.warning(f"话题匹配 LLM 调用失败，fallback 到 mock: {e}")

    return MatchTopicResponse(**MOCK_TOPIC)
