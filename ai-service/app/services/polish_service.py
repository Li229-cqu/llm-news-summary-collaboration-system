"""事件脉络话题润色服务。

复用现有 call_summary_llm() 调用智谱 GLM-4-Flash 对本地聚类结果进行文本润色。
LLM 不可用时自动 fallback 到原始本地规则结果。
"""

from __future__ import annotations

import json
import logging
import re

from app.core.config import settings
from app.schemas.polish import (
    PolishTimelineTopicRequest,
    PolishTimelineTopicResponse,
)
from app.services.llm_client import call_summary_llm

logger = logging.getLogger(__name__)

# 用于从 LLM 返回中提取 JSON 的正则
_JSON_BLOCK_RE = re.compile(r"\{[\s\S]*\}", re.MULTILINE)


def _extract_json(text: str) -> str | None:
    """从 LLM 返回文本中提取 JSON 对象。"""
    m = _JSON_BLOCK_RE.search(text)
    if m:
        return m.group(0)
    return None


def _validate_response(data: dict) -> str | None:
    """校验 LLM 返回的 JSON 是否可用。返回错误原因或 None（通过）。"""
    topic_name = (data.get("topic_name") or "").strip()
    if not topic_name:
        return "LLM 返回的 topic_name 为空"
    if len(topic_name) > 30:
        return f"LLM 返回的 topic_name 过长 ({len(topic_name)} 字符)"
    return None


def build_fallback_response(
    request: PolishTimelineTopicRequest,
    reason: str,
) -> PolishTimelineTopicResponse:
    """构建 fallback 响应，直接使用本地规则生成的原始结果。"""
    summary = request.summary or f"围绕{request.topic_name}形成的热点话题。"
    return PolishTimelineTopicResponse(
        topic_name=request.topic_name,
        summary=summary,
        keywords=list(request.keywords),
        event_title_map={},
        event_summary_map={},
        source="fallback",
        fallback_reason=reason,
    )


def _build_polish_prompt(request: PolishTimelineTopicRequest) -> str:
    """构造润色 prompt。"""
    parts: list[str] = []
    parts.append("你是一个新闻事件脉络编辑助手。请对以下自动聚类生成的话题信息进行文本润色，使其更自然、更像新闻专题名称。")
    parts.append("")
    parts.append("【输入信息】")
    parts.append(f"原始话题名：{request.topic_name}")
    if request.category_name:
        parts.append(f"所属分类：{request.category_name}")
    if request.keywords:
        parts.append(f"关键词：{', '.join(request.keywords[:6])}")
    if request.representative_titles:
        parts.append("代表新闻标题：")
        for t in request.representative_titles[:5]:
            parts.append(f"  - {t}")
    if request.event_points:
        parts.append("事件点列表：")
        for ep in request.event_points:
            parts.append(f"  事件{ep.event_id}：{ep.event_title}")
            if ep.related_titles:
                parts.append(f"    关联新闻：{' / '.join(ep.related_titles[:3])}")

    parts.append("")
    parts.append("【输出要求】")
    parts.append("你是保守的新闻编辑，只做必要的语言精简和措辞调整，不做创意改写。")
    parts.append("请严格返回 JSON（不要 Markdown、不要代码块、不要多余文字）：")
    parts.append("{")
    parts.append('  "topic_name": "话题名",')
    parts.append('  "summary": "话题摘要",')
    parts.append('  "keywords": ["关键词"],')
    parts.append('  "event_title_map": {"事件ID": "事件标题"},')
    parts.append('  "event_summary_map": {"事件ID": "事件摘要"}')
    parts.append("}")
    parts.append("")
    parts.append("【严格约束 - 必须遵守】")
    parts.append("1. 严禁引入输入中没有出现的事实、地名、灾害、主体、赛事结果、人物。")
    parts.append("2. 话题名必须基于输入的 topic_name/keywords/代表新闻标题/事件标题，不得凭空创造。")
    parts.append("3. 如果原始话题名已经足够清晰（如\"墨西哥世界杯赛事进展\"\"纪委监委审查调查\"），请尽量保留原样或仅微调措辞。")
    parts.append("4. 话题名应为新闻专题名，像新闻标题，不要像栏目名或宣传语。")
    parts.append("5. 严禁使用以下风格化词：风云录、脉动、盛事、聚焦、风暴、浪潮、纵横、速递、观察、追踪、热点新闻、最新动态、事件聚焦。")
    parts.append("6. topic_name 控制在 6-20 个中文字符，summary 30-80 字符，event_title 10-24 字符，event_summary 30-80 字符。")
    parts.append("7. 优先保留强关键词（如委内瑞拉、导弹、袭击、世界杯、纪委监委、人大常委会、高铁等），不要用泛指词替换它们。")
    parts.append("8. 如果无法在不违反上述约束的前提下优化，请直接返回原始输入值，不要强行改写。")

    return "\n".join(parts)


async def polish_timeline_topic(
    request: PolishTimelineTopicRequest,
) -> PolishTimelineTopicResponse:
    """对话题候选结果进行 LLM 文本润色。"""

    # 1. LLM 未启用 → 直接 fallback
    if not settings.summary_llm_enabled:
        logger.info("SUMMARY_LLM_ENABLED=false，使用 fallback")
        return build_fallback_response(request, "LLM 未启用")

    # 2. 构建 prompt 并调用 LLM
    prompt = _build_polish_prompt(request)
    messages = [
        {"role": "system", "content": "你是一个专业的中文新闻编辑助手，擅长润色新闻专题名称和事件描述。你只返回 JSON，不返回其他内容。"},
        {"role": "user", "content": prompt},
    ]

    try:
        raw_response = await call_summary_llm(messages)
        logger.info("LLM 润色原始响应长度: %d", len(raw_response))

        # 3. 提取 JSON
        json_text = _extract_json(raw_response)
        if not json_text:
            logger.warning("LLM 返回中未找到 JSON，fallback")
            return build_fallback_response(request, "LLM 返回格式异常：未找到 JSON")

        data = json.loads(json_text)
        if not isinstance(data, dict):
            return build_fallback_response(request, "LLM 返回不是 JSON 对象")

        # 4. 校验
        error = _validate_response(data)
        if error:
            logger.warning("LLM 响应校验失败: %s", error)
            return build_fallback_response(request, error)

        # 5. 构建成功响应
        result = PolishTimelineTopicResponse(
            topic_name=data.get("topic_name", request.topic_name).strip(),
            summary=data.get("summary", request.summary or "").strip(),
            keywords=data.get("keywords", list(request.keywords)),
            event_title_map=data.get("event_title_map", {}),
            event_summary_map=data.get("event_summary_map", {}),
            source="llm",
            fallback_reason=None,
        )

        logger.info(
            "LLM 润色成功: topic_name '%s' → '%s'",
            request.topic_name,
            result.topic_name,
        )
        return result

    except json.JSONDecodeError as e:
        logger.warning("LLM 返回 JSON 解析失败: %s", e)
        return build_fallback_response(request, f"JSON 解析失败: {e}")
    except Exception as e:
        logger.warning("LLM 润色异常: %s", e)
        return build_fallback_response(request, f"LLM 调用异常: {type(e).__name__}")
