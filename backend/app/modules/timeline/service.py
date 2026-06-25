"""Timeline 模块服务层：数据库优先，mock 兜底。"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any, Optional

import httpx

from app.common.exceptions import AppException
from app.core.config import settings
from app.db.database import execute_one, execute_query, execute_update
from app.mock.news import MOCK_NEWS
from app.mock.timeline import MOCK_EVENT_TIMELINES, MOCK_NEWS_TOPICS
from app.modules.auth.schema import UserInfo
from app.modules.timeline.schema import (
    TimelineGenerateResult,
    TimelineNewsItem,
    TimelineNewsListResponse,
    TimelineNode,
    TimelineResponse,
    TimelineTopic,
)

logger = logging.getLogger(__name__)

AI_TIMELINE_ENDPOINT = f"{settings.ai_service_url.rstrip('/')}/ai/generate-timeline"
AI_SERVICE_UNAVAILABLE_MESSAGE = "AI 服务暂时不可用，请稍后重试"


def _now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _normalize_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    return str(value)


def _parse_json_list(value: Any, default: list[Any] | None = None) -> list[Any]:
    if default is None:
        default = []
    if value is None:
        return list(default)
    if isinstance(value, list):
        return value
    if isinstance(value, bytes):
        value = value.decode("utf-8", errors="ignore")
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return list(default)
        try:
            parsed = json.loads(text)
            if isinstance(parsed, list):
                return parsed
        except json.JSONDecodeError:
            return list(default)
    return list(default)


def _parse_json_dict(value: Any, default: dict[str, Any] | None = None) -> dict[str, Any]:
    if default is None:
        default = {}
    if value is None:
        return dict(default)
    if isinstance(value, dict):
        return value
    if isinstance(value, bytes):
        value = value.decode("utf-8", errors="ignore")
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return dict(default)
        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            return dict(default)
    return dict(default)


def _parse_publish_time(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    text = _normalize_text(value).replace("T", " ").strip()
    if not text:
        return datetime.min
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return datetime.min


def _format_publish_time(value: Any) -> str:
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    text = _normalize_text(value).replace("T", " ").strip()
    return text


def _topic_row_to_model(row: dict[str, Any], news_count: int) -> TimelineTopic:
    return TimelineTopic(
        topic_id=int(row["id"]),
        topic_name=_normalize_text(row["topic_name"]),
        keyword_list=[str(item) for item in _parse_json_list(row.get("keyword_list"), [])],
        heat_score=int(row.get("heat_score") or 0),
        summary=_normalize_text(row.get("summary")),
        news_count=news_count,
    )


def _mock_topics() -> list[TimelineTopic]:
    topic_rows = [
        dict(topic)
        for topic in MOCK_NEWS_TOPICS
        if int(topic.get("status", 0)) == 1
    ]
    topic_rows.sort(key=lambda item: (-int(item.get("heat_score", 0)), int(item.get("id", 0))))

    topic_to_count: dict[int, int] = {}
    for news in MOCK_NEWS:
        topic_id = news.get("topic_id")
        if topic_id:
            topic_to_count[int(topic_id)] = topic_to_count.get(int(topic_id), 0) + 1

    return [
        _topic_row_to_model(row, topic_to_count.get(int(row["id"]), 0))
        for row in topic_rows
    ]


def _normalize_generate_status(value: Any) -> str:
    status = _normalize_text(value, "cached")
    if status in {"cached", "generated", "mock"}:
        return status
    if status in {"success", "ok"}:
        return "cached"
    if status in {"ai-service", "ai"}:
        return "generated"
    return "cached"


def _db_topics() -> list[TimelineTopic] | None:
    rows = execute_query(
        """
        SELECT
            nt.id,
            nt.topic_name,
            nt.keyword_list,
            nt.heat_score,
            nt.summary,
            nt.status,
            COALESCE(COUNT(n.id), 0) AS news_count
        FROM news_topic nt
        LEFT JOIN news n
          ON n.topic_id = nt.id
         AND n.status = 1
        WHERE nt.status = 1
        GROUP BY nt.id, nt.topic_name, nt.keyword_list, nt.heat_score, nt.summary, nt.status
        ORDER BY nt.heat_score DESC, nt.id ASC
        """,
    )
    if not rows:
        return None

    return [
        TimelineTopic(
            topic_id=int(row["id"]),
            topic_name=_normalize_text(row["topic_name"]),
            keyword_list=[str(item) for item in _parse_json_list(row.get("keyword_list"), [])],
            heat_score=int(row.get("heat_score") or 0),
            summary=_normalize_text(row.get("summary")),
            news_count=int(row.get("news_count") or 0),
        )
        for row in rows
    ]


def _get_topic_from_db(topic_id: int) -> dict[str, Any] | None:
    return execute_one(
        """
        SELECT
            id,
            topic_name,
            keyword_list,
            heat_score,
            summary,
            status
        FROM news_topic
        WHERE id = %s AND status = 1
        LIMIT 1
        """,
        [topic_id],
    )


def _get_topic_from_mock(topic_id: int) -> dict[str, Any] | None:
    for topic in MOCK_NEWS_TOPICS:
        if int(topic.get("id", 0)) == topic_id and int(topic.get("status", 0)) == 1:
            return dict(topic)
    return None


def _get_topic(topic_id: int) -> dict[str, Any] | None:
    try:
        topic = _get_topic_from_db(topic_id)
        if topic is not None:
            return topic
    except Exception as exc:  # noqa: BLE001
        logger.warning("读取 Timeline 话题数据库失败，回退 mock：%s", exc)
    return _get_topic_from_mock(topic_id)


def _topic_news_from_db(topic_id: int) -> list[dict[str, Any]] | None:
    rows = execute_query(
        """
        SELECT
            n.id,
            n.title,
            n.summary,
            n.content,
            n.cover_image,
            n.category_id,
            COALESCE(nc.name, '') AS category_name,
            n.topic_id,
            n.source,
            n.author,
            n.publish_time,
            n.view_count,
            n.like_count,
            n.comment_count,
            n.favorite_count,
            n.status,
            n.tags
        FROM news n
        LEFT JOIN news_category nc ON nc.id = n.category_id
        WHERE n.status = 1
          AND n.topic_id = %s
        ORDER BY n.publish_time ASC, n.id ASC
        """,
        [topic_id],
    )
    if rows is None:
        return None

    return rows


def _topic_news_from_mock(topic_id: int) -> list[dict[str, Any]]:
    rows = [
        dict(news)
        for news in MOCK_NEWS
        if int(news.get("status", 0)) == 1 and int(news.get("topic_id") or 0) == topic_id
    ]
    rows.sort(key=lambda item: (_parse_publish_time(item.get("publish_time")), int(item.get("id", 0))))
    return rows


def _build_news_items(rows: list[dict[str, Any]]) -> list[TimelineNewsItem]:
    items: list[TimelineNewsItem] = []
    for row in rows:
        items.append(
            TimelineNewsItem(
                id=int(row["id"]),
                title=_normalize_text(row["title"]),
                content=_normalize_text(row["content"]),
                source=_normalize_text(row.get("source")),
                publish_time=_format_publish_time(row.get("publish_time")),
                summary=_normalize_text(row.get("summary")) or None,
                category_id=row.get("category_id"),
                category_name=_normalize_text(row.get("category_name")) or None,
                topic_id=row.get("topic_id"),
            )
        )
    return items


def _build_topic_news_response(topic: dict[str, Any], rows: list[dict[str, Any]]) -> TimelineNewsListResponse:
    return TimelineNewsListResponse(
        topic_id=int(topic["id"]),
        topic_name=_normalize_text(topic["topic_name"]),
        news_items=_build_news_items(rows),
    )


def _get_topic_news(topic_id: int) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    try:
        topic = _get_topic_from_db(topic_id)
        if topic is not None:
            rows = _topic_news_from_db(topic_id)
            if rows is not None:
                return topic, rows
    except Exception as exc:  # noqa: BLE001
        logger.warning("读取 Timeline 新闻数据库失败，回退 mock：%s", exc)

    topic = _get_topic_from_mock(topic_id)
    if topic is None:
        return None, []
    return topic, _topic_news_from_mock(topic_id)


def _cached_timeline_from_db(topic_id: int) -> dict[str, Any] | None:
    row = execute_one(
        """
        SELECT
            id,
            topic_id,
            timeline_json,
            source_news_ids,
            generate_status,
            generated_at,
            updated_at
        FROM event_timeline
        WHERE topic_id = %s
        LIMIT 1
        """,
        [topic_id],
    )
    if not row:
        return None
    return row


def _cached_timeline_from_mock(topic_id: int) -> dict[str, Any] | None:
    for item in MOCK_EVENT_TIMELINES:
        if int(item.get("topic_id", 0)) == topic_id:
            return dict(item)
    return None


def _cached_timeline(topic_id: int) -> dict[str, Any] | None:
    try:
        row = _cached_timeline_from_db(topic_id)
        if row is not None:
            return row
    except Exception as exc:  # noqa: BLE001
        logger.warning("读取 Timeline 缓存数据库失败，回退 mock：%s", exc)
    return _cached_timeline_from_mock(topic_id)


def _timeline_row_to_result(row: dict[str, Any], topic_name: str, source: str) -> TimelineGenerateResult:
    timeline_json = _parse_json_list(row.get("timeline_json"), [])
    timeline = [TimelineNode(**item) for item in timeline_json]
    return TimelineGenerateResult(
        topic_id=int(row["topic_id"]),
        topic_name=topic_name,
        timeline=timeline,
        source=source,
        generated_at=_normalize_text(row.get("generated_at")) or None,
        updated_at=_normalize_text(row.get("updated_at")) or None,
        generate_status=_normalize_generate_status(row.get("generate_status")),
    )


def _mock_result_to_cache_payload(result: TimelineGenerateResult) -> dict[str, Any]:
    return {
        "topic_id": result.topic_id,
        "timeline_json": [node.model_dump() for node in result.timeline],
        "source_news_ids": [node.source_news_id for node in result.timeline],
        "generate_status": result.generate_status,
        "generated_at": result.generated_at,
        "updated_at": result.updated_at,
    }


def _save_cache_to_db(result: TimelineGenerateResult) -> None:
    payload = _mock_result_to_cache_payload(result)
    now = _now_text()
    existing = _cached_timeline_from_db(result.topic_id)
    if existing is None:
        execute_update(
            """
            INSERT INTO event_timeline (
                topic_id, timeline_json, source_news_ids,
                generate_status, generated_at, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s)
            """,
            [
                payload["topic_id"],
                json.dumps(payload["timeline_json"], ensure_ascii=False),
                json.dumps(payload["source_news_ids"], ensure_ascii=False),
                payload["generate_status"],
                payload["generated_at"] or now,
                payload["updated_at"] or now,
            ],
        )
        return

    execute_update(
        """
        UPDATE event_timeline
           SET timeline_json = %s,
               source_news_ids = %s,
               generate_status = %s,
               generated_at = %s,
               updated_at = %s
         WHERE topic_id = %s
        """,
        [
            json.dumps(payload["timeline_json"], ensure_ascii=False),
            json.dumps(payload["source_news_ids"], ensure_ascii=False),
            payload["generate_status"],
            payload["generated_at"] or now,
            payload["updated_at"] or now,
            payload["topic_id"],
        ],
    )


def _save_cache_to_mock(result: TimelineGenerateResult) -> None:
    payload = _mock_result_to_cache_payload(result)
    now = result.updated_at or _now_text()
    cached = _cached_timeline_from_mock(result.topic_id)
    if cached is None:
        MOCK_EVENT_TIMELINES.append(
            {
                "id": max([item.get("id", 0) for item in MOCK_EVENT_TIMELINES], default=0) + 1,
                "topic_id": result.topic_id,
                **payload,
                "generated_at": result.generated_at or now,
                "updated_at": now,
            }
        )
        return

    cached.update(
        {
            **payload,
            "generated_at": result.generated_at or now,
            "updated_at": now,
        }
    )


def _build_ai_payload(topic: dict[str, Any], news_rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "topic_id": int(topic["id"]),
        "topic_name": _normalize_text(topic["topic_name"]),
        "news_items": [
            {
                "id": int(row["id"]),
                "title": _normalize_text(row["title"]),
                "content": _normalize_text(row["content"]),
                "source": _normalize_text(row.get("source")),
                "publish_time": _format_publish_time(row.get("publish_time")),
            }
            for row in news_rows
        ],
    }


def _build_local_timeline(topic: dict[str, Any], news_rows: list[dict[str, Any]]) -> TimelineGenerateResult:
    topic_name = _normalize_text(topic["topic_name"])
    nodes = []
    for index, row in enumerate(news_rows, start=1):
        summary = _normalize_text(row.get("summary")) or _normalize_text(row.get("content"))[:100]
        if len(summary) > 100:
            summary = f"{summary[:100]}..."
        nodes.append(
            TimelineNode(
                event_id=index,
                event_time=_format_publish_time(row.get("publish_time")),
                event_title=_normalize_text(row["title"]),
                event_summary=summary,
                source_news_id=int(row["id"]),
                source_title=_normalize_text(row["title"]),
                source_name=_normalize_text(row.get("source")),
            )
        )

    now = _now_text()
    return TimelineGenerateResult(
        topic_id=int(topic["id"]),
        topic_name=topic_name,
        timeline=nodes,
        source="mock",
        generated_at=now,
        updated_at=now,
        generate_status="mock",
    )


def _build_ai_result(topic: dict[str, Any], data: dict[str, Any]) -> TimelineGenerateResult | None:
    timeline_payload = data.get("timeline")
    if not isinstance(timeline_payload, list) or not timeline_payload:
        return None

    nodes: list[TimelineNode] = []
    for index, item in enumerate(timeline_payload, start=1):
        if not isinstance(item, dict):
            continue
        nodes.append(
            TimelineNode(
                event_id=int(item.get("event_id", index)),
                event_time=_normalize_text(item.get("event_time")),
                event_title=_normalize_text(item.get("event_title")),
                event_summary=_normalize_text(item.get("event_summary")),
                source_news_id=int(item.get("source_news_id") or 0),
                source_title=_normalize_text(item.get("source_title")),
                source_name=_normalize_text(item.get("source_name")),
            )
        )

    if not nodes:
        return None

    now = _now_text()
    return TimelineGenerateResult(
        topic_id=int(topic["id"]),
        topic_name=_normalize_text(data.get("topic_name") or topic["topic_name"]),
        timeline=nodes,
        source="ai-service",
        generated_at=_normalize_text(data.get("generated_at")) or now,
        updated_at=_normalize_text(data.get("updated_at")) or now,
        generate_status=_normalize_text(data.get("generate_status"), "generated"),
    )


def _fetch_topics() -> list[TimelineTopic]:
    try:
        topics = _db_topics()
        if topics is not None:
            return topics
    except Exception as exc:  # noqa: BLE001
        logger.warning("读取 Timeline 话题数据库失败，回退 mock：%s", exc)
    return _mock_topics()


def get_timeline_topics() -> list[TimelineTopic]:
    return _fetch_topics()


def get_timeline_topic_news(topic_id: int) -> TimelineNewsListResponse:
    topic, news_rows = _get_topic_news(topic_id)
    if topic is None:
        raise AppException(code=404, message="话题不存在")
    return _build_topic_news_response(topic, news_rows)


async def _generate_with_ai_or_fallback(topic: dict[str, Any], news_rows: list[dict[str, Any]]) -> TimelineGenerateResult:
    request_payload = _build_ai_payload(topic, news_rows)

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(AI_TIMELINE_ENDPOINT, json=request_payload)
            response.raise_for_status()
            payload = response.json()

        if payload.get("code") == 200 and isinstance(payload.get("data"), dict):
            ai_result = _build_ai_result(topic, payload["data"])
            if ai_result is not None:
                _save_cache_to_db(ai_result)
                return ai_result
    except (httpx.HTTPError, ValueError, KeyError, TypeError) as exc:
        logger.warning("AI Timeline 调用失败，回退本地规则：%s", exc)

    fallback = _build_local_timeline(topic, news_rows)
    try:
        _save_cache_to_db(fallback)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Timeline 缓存写入数据库失败，回退 mock：%s", exc)
        _save_cache_to_mock(fallback)
    return fallback


async def get_timeline_detail(topic_id: int) -> TimelineGenerateResult:
    topic = _get_topic(topic_id)
    if topic is None:
        raise AppException(code=404, message="话题不存在")

    news_rows = _get_topic_news(topic_id)[1]
    if len(news_rows) < 2:
        raise AppException(code=400, message="同一话题下至少需要 2 篇新闻才能生成事件脉络")

    cached = _cached_timeline(topic_id)
    if cached is not None and cached.get("timeline_json"):
        source = "cache"
        if cached.get("generate_status") == "mock":
            source = "mock"
        return _timeline_row_to_result(cached, _normalize_text(topic["topic_name"]), source=source)

    return await _generate_with_ai_or_fallback(topic, news_rows)


async def generate_timeline(topic_id: int, current_user: Optional[UserInfo] = None) -> TimelineGenerateResult:
    if current_user is None:
        raise AppException(code=401, message="未登录或登录状态已失效")

    return await get_timeline_detail(topic_id)
