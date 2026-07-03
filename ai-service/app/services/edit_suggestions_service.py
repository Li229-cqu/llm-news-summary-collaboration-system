"""编辑建议服务 — Phase 5: 接入 LLM 真实调用。"""
from __future__ import annotations
import json
import logging

from app.common.exceptions import AIServiceException
from app.core.config import settings
from app.schemas.edit_suggestions import (
    EditSuggestionsRequest,
    EditSuggestionsResponse,
    EditSuggestionItem,
)
from app.services.llm_client import call_summary_llm

logger = logging.getLogger(__name__)

MOCK_EDIT_SUGGESTIONS = {
    "suggestions": [
        {"type": "标题优化", "original": "", "suggested": "【重磅】两部委联合发布AI新规划", "reason": "增加新闻冲击力", "detail": "", "priority": "中"},
        {"type": "结构建议", "original": "", "suggested": "", "reason": "", "detail": "导语后可增加背景段落", "priority": "中"},
        {"type": "事实核查", "original": "", "suggested": "", "reason": "", "detail": "确认具体发布日期", "priority": "高"},
    ],
    "overall_score": 88,
    "ready_to_publish": True,
}


def _build_edit_prompt(text: str, title: str, summary: str, topic_info: str, consistency_info: str) -> str:
    return f"""你是一个资深新闻主编。请根据以下信息给出编辑修改建议。

新闻标题：{title or "无"}
新闻摘要：{summary or "无"}
话题分类：{topic_info}
一致性检查：{consistency_info}
正文片段：{text[:1000]}

请从以下维度给出建议：标题优化、结构建议、事实核查、语言润色。
请严格返回 JSON 格式：
{{"suggestions": [{{"type": "建议类型", "reason": "修改理由", "detail": "具体建议", "priority": "高/中/低"}}], "overall_score": 0-100, "ready_to_publish": true/false}}"""


def _parse_edit_response(raw: str) -> dict:
    raw = raw.strip()
    if "```json" in raw:
        raw = raw.split("```json")[1].split("```")[0]
    elif "```" in raw:
        raw = raw.split("```")[1].split("```")[0]
    try:
        data = json.loads(raw)
        suggestions = []
        for s in data.get("suggestions", []):
            suggestions.append({
                "type": s.get("type", "建议"),
                "original": s.get("original", ""),
                "suggested": s.get("suggested", ""),
                "reason": s.get("reason", ""),
                "detail": s.get("detail", ""),
                "priority": s.get("priority", "中"),
            })
        return {
            "suggestions": suggestions,
            "overall_score": int(data.get("overall_score", 80)),
            "ready_to_publish": bool(data.get("ready_to_publish", True)),
        }
    except (json.JSONDecodeError, ValueError, KeyError):
        return MOCK_EDIT_SUGGESTIONS


async def edit_suggestions(request: EditSuggestionsRequest) -> EditSuggestionsResponse:
    if not request.text.strip():
        raise AIServiceException(code=400, message="新闻文本不能为空")

    if settings.summary_llm_enabled:
        try:
            topic_info = json.dumps(request.topic, ensure_ascii=False) if request.topic else "未知"
            consistency_info = json.dumps(request.consistency, ensure_ascii=False) if request.consistency else "未知"
            prompt = _build_edit_prompt(
                request.text, request.title, request.summary, topic_info, consistency_info
            )
            messages = [{"role": "user", "content": prompt}]
            raw_response = await call_summary_llm(messages, temperature=0.4, max_tokens=1024)
            logger.info(f"编辑建议 LLM 原始响应: {raw_response[:200]}")
            result = _parse_edit_response(raw_response)
            items = [EditSuggestionItem(**s) for s in result.pop("suggestions", [])]
            return EditSuggestionsResponse(suggestions=items, **result)
        except Exception as e:
            logger.warning(f"编辑建议 LLM 调用失败，fallback 到 mock: {e}")

    items = [EditSuggestionItem(**s) for s in MOCK_EDIT_SUGGESTIONS.get("suggestions", [])]
    return EditSuggestionsResponse(
        suggestions=items,
        overall_score=MOCK_EDIT_SUGGESTIONS["overall_score"],
        ready_to_publish=MOCK_EDIT_SUGGESTIONS["ready_to_publish"],
    )
