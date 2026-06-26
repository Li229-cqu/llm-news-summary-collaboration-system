from __future__ import annotations

from typing import List

from datetime import datetime

from app.common.exceptions import AIServiceException
from app.schemas.timeline import TimelineGenerateRequest, TimelineGenerateResponse, TimelineItem


def _parse_publish_time(publish_time: str) -> datetime:
    """将发布时间解析为排序用的 datetime。"""
    normalized = publish_time.replace("T", " ").strip()
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        return datetime.min


def _build_event_title(title: str) -> str:
    clean_title = title.strip()
    if len(clean_title) <= 12:
        return clean_title
    return f"{clean_title[:12]}..."


def _build_event_summary(topic_name: str, title: str, content: str) -> str:
    text = content.strip().replace("\n", " ")
    if "。" in text:
        text = text.split("。", 1)[0]
    if len(text) > 90:
        text = f"{text[:90]}..."
    return f"围绕“{title}”的报道，聚焦{topic_name}相关进展。{text}"


def generate_timeline(request: TimelineGenerateRequest) -> TimelineGenerateResponse:
    if len(request.news_items) < 2:
        raise AIServiceException(
            code=400,
            message="同一话题下至少需要 2 篇新闻才能生成事件脉络",
        )

    sorted_news = sorted(request.news_items, key=lambda item: _parse_publish_time(item.publish_time))

    timeline: list[TimelineItem] = []
    for index, news in enumerate(sorted_news, start=1):
        timeline.append(
            TimelineItem(
                event_id=index,
                event_time=news.publish_time,
                event_title=_build_event_title(news.title),
                event_summary=_build_event_summary(request.topic_name, news.title, news.content),
                source_news_id=news.id,
                source_title=news.title,
                source_name=news.source,
            )
        )

    return TimelineGenerateResponse(
        topic_id=request.topic_id,
        topic_name=request.topic_name,
        timeline=timeline,
    )
