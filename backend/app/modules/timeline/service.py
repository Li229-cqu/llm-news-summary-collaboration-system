"""Timeline 模块服务层。"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Iterable, Optional

import httpx

from app.common.exceptions import AppException
from app.core.config import settings
from app.mock.news import MOCK_NEWS
from app.mock.timeline import MOCK_EVENT_TIMELINES, MOCK_NEWS_TOPICS
from app.modules.timeline.schema import (
    TimelineGenerateResult,
    TimelineNode,
    TimelineNewsItem,
    TimelineNewsListResponse,
    TimelineTopic,
)

AI_TIMELINE_ENDPOINT = f"{settings.ai_service_url.rstrip('/')}/ai/generate-timeline"
AI_SERVICE_UNAVAILABLE_MESSAGE = "AI 服务暂时不可用，请稍后重试"


def _parse_publish_time(publish_time: str) -> datetime:
    normalized = publish_time.replace("T", " ").strip()
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        return datetime.min


def _format_publish_time(publish_time: str) -> str:
    return publish_time.replace("T", " ").strip()


def _get_topic(topic_id: int) -> dict[str, Any] | None:
    for topic in MOCK_NEWS_TOPICS:
        if topic["id"] == topic_id and topic["status"] == 1:
            return topic
    return None


def _get_topic_news(topic_id: int) -> list[dict[str, Any]]:
    topic_news = [
        dict(news)
        for news in MOCK_NEWS
        if news.get("status") == 1 and news.get("topic_id") == topic_id
    ]
    topic_news.sort(key=lambda item: (_parse_publish_time(item["publish_time"]), item["id"]))
    return topic_news


def _get_cached_timeline(topic_id: int) -> dict[str, Any] | None:
    for timeline in MOCK_EVENT_TIMELINES:
        if timeline.get("topic_id") == topic_id:
            return timeline
    return None


def _to_topic_response(topic: dict[str, Any], news_count: int) -> TimelineTopic:
    return TimelineTopic(
        topic_id=topic["id"],
        topic_name=topic["topic_name"],
        keyword_list=list(topic.get("keyword_list", [])),
        heat_score=topic["heat_score"],
        summary=topic["summary"],
        news_count=news_count,
    )


def _to_timeline_nodes(news_items: Iterable[dict[str, Any]], topic_name: str) -> list[TimelineNode]:
    nodes: list[TimelineNode] = []
    for index, news in enumerate(news_items, start=1):
        summary = news.get("summary") or news.get("content", "")[:100]
        if len(summary) > 100:
            summary = f"{summary[:100]}..."
        nodes.append(
            TimelineNode(
                event_id=index,
                event_time=_format_publish_time(news["publish_time"]),
                event_title=news["title"],
                event_summary=f"围绕“{topic_name}”的报道，{summary}",
                source_news_id=news["id"],
                source_title=news["title"],
                source_name=news["source"],
            )
        )
    return nodes


def get_timeline_topics() -> list[TimelineTopic]:
    topics = sorted(
        (dict(topic) for topic in MOCK_NEWS_TOPICS if topic.get("status") == 1),
        key=lambda topic: (-topic.get("heat_score", 0), topic.get("id", 0)),
    )
    return [_to_topic_response(topic, len(_get_topic_news(topic["id"]))) for topic in topics]


def get_timeline_topic_news(topic_id: int) -> TimelineNewsListResponse:
    topic = _get_topic(topic_id)
    if topic is None:
        raise AppException(code=404, message="话题不存在")

    news_items = _get_topic_news(topic_id)
    return TimelineNewsListResponse(
        topic_id=topic["id"],
        topic_name=topic["topic_name"],
        news_items=[
            TimelineNewsItem(
                id=news["id"],
                title=news["title"],
                content=news["content"],
                source=news["source"],
                publish_time=_format_publish_time(news["publish_time"]),
                summary=news.get("summary"),
                category_id=news.get("category_id"),
                category_name=news.get("category_name"),
                topic_id=news.get("topic_id"),
            )
            for news in news_items
        ],
    )


def _build_ai_payload(topic: dict[str, Any], news_items: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "topic_id": topic["id"],
        "topic_name": topic["topic_name"],
        "news_items": [
            {
                "id": news["id"],
                "title": news["title"],
                "content": news["content"],
                "source": news["source"],
                "publish_time": _format_publish_time(news["publish_time"]),
            }
            for news in news_items
        ],
    }


def _build_result_from_ai(topic_id: int, topic_name: str, data: dict[str, Any]) -> TimelineGenerateResult:
    timeline_payload = data.get("timeline", [])
    timeline = [
        TimelineNode(
            event_id=int(item.get("event_id", index)),
            event_time=str(item.get("event_time", "")),
            event_title=str(item.get("event_title", "")),
            event_summary=str(item.get("event_summary", "")),
            source_news_id=int(item.get("source_news_id", 0)),
            source_title=str(item.get("source_title", "")),
            source_name=str(item.get("source_name", "")),
        )
        for index, item in enumerate(timeline_payload, start=1)
    ]
    return TimelineGenerateResult(
        topic_id=topic_id,
        topic_name=topic_name,
        timeline=timeline,
        source="ai-service",
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        updated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        generate_status="generated",
    )


def _build_result_from_news(topic_id: int, topic_name: str, news_items: list[dict[str, Any]], source: str) -> TimelineGenerateResult:
    timeline = _to_timeline_nodes(news_items, topic_name)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return TimelineGenerateResult(
        topic_id=topic_id,
        topic_name=topic_name,
        timeline=timeline,
        source=source,
        generated_at=now,
        updated_at=now,
        generate_status="mock" if source == "mock" else "generated",
    )


def _cache_timeline(result: TimelineGenerateResult) -> None:
    cached = _get_cached_timeline(result.topic_id)
    cache_payload = {
        "id": cached["id"] if cached else len(MOCK_EVENT_TIMELINES) + 1,
        "topic_id": result.topic_id,
        "timeline_json": [node.model_dump() for node in result.timeline],
        "source_news_ids": [node.source_news_id for node in result.timeline],
        "generate_status": result.generate_status,
        "generated_at": result.generated_at,
        "updated_at": result.updated_at,
    }
    if cached is None:
        MOCK_EVENT_TIMELINES.append(cache_payload)
    else:
        cached.update(cache_payload)


async def get_timeline_detail(topic_id: int) -> TimelineGenerateResult:
    topic = _get_topic(topic_id)
    if topic is None:
        raise AppException(code=404, message="话题不存在")

    news_items = _get_topic_news(topic_id)
    if len(news_items) < 2:
        raise AppException(code=400, message="同一话题下至少需要 2 篇新闻才能生成事件脉络")

    cached = _get_cached_timeline(topic_id)
    if cached is not None and cached.get("timeline_json"):
        return TimelineGenerateResult(
            topic_id=topic_id,
            topic_name=topic["topic_name"],
            timeline=[TimelineNode(**item) for item in cached["timeline_json"]],
            source="cache",
            generated_at=cached.get("generated_at"),
            updated_at=cached.get("updated_at"),
            generate_status=cached.get("generate_status", "cached"),
        )

    return await _generate_timeline_with_fallback(topic, news_items)


async def _generate_timeline_with_fallback(
    topic: dict[str, Any],
    news_items: list[dict[str, Any]],
) -> TimelineGenerateResult:
    topic_name = topic["topic_name"]
    request_payload = _build_ai_payload(topic, news_items)

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(AI_TIMELINE_ENDPOINT, json=request_payload)
            response.raise_for_status()
            result = response.json()
        if result.get("code") == 200 and isinstance(result.get("data"), dict):
            timeline_result = _build_result_from_ai(topic["id"], topic_name, result["data"])
            _cache_timeline(timeline_result)
            return timeline_result
    except (httpx.HTTPError, ValueError, KeyError, TypeError):
        pass

    fallback_result = _build_result_from_news(topic["id"], topic_name, news_items, source="mock")
    _cache_timeline(fallback_result)
    return fallback_result


async def generate_timeline(topic_id: int, current_user: Optional[Any] = None) -> TimelineGenerateResult:
    if current_user is None:
        raise AppException(code=401, message="未登录或登录状态已失效")

    topic = _get_topic(topic_id)
    if topic is None:
        raise AppException(code=404, message="话题不存在")

    news_items = _get_topic_news(topic_id)
    if len(news_items) < 2:
        raise AppException(code=400, message="同一话题下至少需要 2 篇新闻才能生成事件脉络")

    cached = _get_cached_timeline(topic_id)
    topic_name = topic["topic_name"]

    if cached is not None and cached.get("timeline_json"):
        return TimelineGenerateResult(
            topic_id=topic_id,
            topic_name=topic_name,
            timeline=[TimelineNode(**item) for item in cached["timeline_json"]],
            source="cache",
            generated_at=cached.get("generated_at"),
            updated_at=cached.get("updated_at"),
            generate_status=cached.get("generate_status", "cached"),
        )

    return await _generate_timeline_with_fallback(topic, news_items)
