"""时间线适配服务 — Phase 5: 接入 LLM 真实调用。"""
from __future__ import annotations
import json
import logging

from app.common.exceptions import AIServiceException
from app.core.config import settings
from app.schemas.judge_timeline import JudgeTimelineRequest, JudgeTimelineResponse
from app.services.llm_client import call_summary_llm

logger = logging.getLogger(__name__)

MOCK_TIMELINE = {
    "is_timely": True,
    "recommended_position": "要闻区/科技频道",
    "time_sensitivity": "高",
    "related_events": ["2026年1月AI座谈会", "2025年12月科技工作会议"],
}


def _build_timeline_prompt(text: str, when: str, title: str) -> str:
    return f"""你是一个新闻编辑，请判断以下新闻是否适合加入当前时间线/事件脉络。

新闻标题：{title or "未知"}
事件时间：{when or "未知"}
正文片段：{text[:800]}

请严格返回 JSON 格式：
{{"is_timely": true/false, "recommended_position": "推荐发布位置", "time_sensitivity": "高/中/低", "related_events": ["相关事件1", "相关事件2"]}}"""


def _parse_timeline_response(raw: str) -> dict:
    raw = raw.strip()
    if "```json" in raw:
        raw = raw.split("```json")[1].split("```")[0]
    elif "```" in raw:
        raw = raw.split("```")[1].split("```")[0]
    try:
        data = json.loads(raw)
        return {
            "is_timely": bool(data.get("is_timely", True)),
            "recommended_position": data.get("recommended_position", "要闻区"),
            "time_sensitivity": data.get("time_sensitivity", "中"),
            "related_events": data.get("related_events", []),
        }
    except (json.JSONDecodeError, ValueError, KeyError):
        import re
        timely = re.search(r'"is_timely"\s*:\s*(true|false)', raw, re.IGNORECASE)
        return {
            "is_timely": timely.group(1).lower() == "true" if timely else True,
            "recommended_position": "要闻区",
            "time_sensitivity": "中",
            "related_events": [],
        }


async def judge_timeline(request: JudgeTimelineRequest) -> JudgeTimelineResponse:
    if not request.text.strip():
        raise AIServiceException(code=400, message="新闻文本不能为空")

    if settings.summary_llm_enabled:
        try:
            prompt = _build_timeline_prompt(request.text, request.when, request.title)
            messages = [{"role": "user", "content": prompt}]
            raw_response = await call_summary_llm(messages, temperature=0.2, max_tokens=512)
            logger.info(f"时间线适配 LLM 原始响应: {raw_response[:200]}")
            result = _parse_timeline_response(raw_response)
            return JudgeTimelineResponse(**result)
        except Exception as e:
            logger.warning(f"时间线适配 LLM 调用失败，fallback 到 mock: {e}")

    return JudgeTimelineResponse(**MOCK_TIMELINE)
