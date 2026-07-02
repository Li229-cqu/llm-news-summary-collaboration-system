"""Timeline 模块服务层：数据库优先，mock 兜底。"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, Tuple, Union

import httpx

from app.common.exceptions import AppException
from app.common.utils import normalize_text
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
    TimelinePhase,
    TimelineRelationship,
    TimelineResponse,
    TimelineTopic,
)

logger = logging.getLogger(__name__)

AI_TIMELINE_ENDPOINT = f"{settings.ai_service_url.rstrip('/')}/ai/generate-timeline"
AI_SERVICE_UNAVAILABLE_MESSAGE = "AI 服务暂时不可用，请稍后重试"


def _now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")



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
    text = normalize_text(value).replace("T", " ").strip()
    if not text:
        return datetime.min
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return datetime.min


def _format_publish_time(value: Any) -> str:
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    text = normalize_text(value).replace("T", " ").strip()
    return text


def _topic_row_to_model(row: dict[str, Any], news_count: int) -> TimelineTopic:
    return TimelineTopic(
        topic_id=int(row["id"]),
        topic_name=normalize_text(row["topic_name"]),
        keyword_list=[str(item) for item in _parse_json_list(row.get("keyword_list"), [])],
        heat_score=int(row.get("heat_score") or 0),
        summary=normalize_text(row.get("summary")),
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
    status = normalize_text(value, "cached")
    if status in {"cached", "generated", "mock", "generating"}:
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
    # 数据库连接正常，即使没有话题也返回空列表（不回退 mock）
    if rows is None:
        return None  # execute_query 本身失败才返回 None
    return [
        TimelineTopic(
            topic_id=int(row["id"]),
            topic_name=normalize_text(row["topic_name"]),
            keyword_list=[str(item) for item in _parse_json_list(row.get("keyword_list"), [])],
            heat_score=int(row.get("heat_score") or 0),
            summary=normalize_text(row.get("summary")),
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
            n.editor,
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
                title=normalize_text(row["title"]),
                content=normalize_text(row["content"]),
                source=normalize_text(row.get("source")),
                publish_time=_format_publish_time(row.get("publish_time")),
                summary=normalize_text(row.get("summary")) or None,
                category_id=row.get("category_id"),
                category_name=normalize_text(row.get("category_name")) or None,
                topic_id=row.get("topic_id"),
            )
        )
    return items


def _build_topic_news_response(topic: dict[str, Any], rows: list[dict[str, Any]]) -> TimelineNewsListResponse:
    return TimelineNewsListResponse(
        topic_id=int(topic["id"]),
        topic_name=normalize_text(topic["topic_name"]),
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


def _cached_timeline_matches_news(cached: dict[str, Any], news_rows: list[dict[str, Any]]) -> bool:
    cached_ids: list[int] = []
    for item in _parse_json_list(cached.get("source_news_ids"), []):
        try:
            cached_ids.append(int(item))
        except (TypeError, ValueError):
            continue

    current_ids: list[int] = []
    for row in news_rows:
        try:
            current_ids.append(int(row["id"]))
        except (TypeError, ValueError, KeyError):
            continue

    return bool(cached_ids) and cached_ids == current_ids


def _build_timeline_extras(nodes: list[TimelineNode], overview_seed: str = "") -> tuple[str, list[str], list[TimelinePhase], list[TimelineRelationship]]:
    overview = normalize_text(overview_seed)
    if not overview and nodes:
        overview = f"围绕“{nodes[0].source_title}”等新闻梳理形成的事件脉络，共包含 {len(nodes)} 个节点。"

    key_figures = list(
        dict.fromkeys([normalize_text(node.source_name) for node in nodes if normalize_text(node.source_name)])
    )[:5]

    phases: list[TimelinePhase] = []
    n = len(nodes)
    if n >= 4:
        third = max(n // 3, 1)
        phases = [
            TimelinePhase(name="初始阶段", start_event_id=1, end_event_id=third),
            TimelinePhase(name="发展阶段", start_event_id=third + 1, end_event_id=third * 2),
            TimelinePhase(name="当前阶段", start_event_id=third * 2 + 1, end_event_id=n),
        ]
    elif n >= 2:
        phases = [
            TimelinePhase(name="起始阶段", start_event_id=1, end_event_id=max(1, n // 2)),
            TimelinePhase(name="后续发展", start_event_id=max(2, n // 2 + 1), end_event_id=n),
        ]

    relationships: list[TimelineRelationship] = []
    for index in range(1, n):
        relationships.append(TimelineRelationship(from_id=index, to_id=index + 1, type="follows"))

    return overview, key_figures, phases, relationships


def _timeline_row_to_result(row: dict[str, Any], topic: dict[str, Any], source: str) -> TimelineGenerateResult:
    timeline_json = _parse_json_list(row.get("timeline_json"), [])
    timeline = [TimelineNode(**item) for item in timeline_json]
    overview, key_figures, phases, relationships = _build_timeline_extras(timeline, normalize_text(topic.get("summary", "")))

    return TimelineGenerateResult(
        topic_id=int(row["topic_id"]),
        topic_name=normalize_text(topic["topic_name"]),
        timeline=timeline,
        source=source,
        generated_at=normalize_text(row.get("generated_at")) or None,
        updated_at=normalize_text(row.get("updated_at")) or None,
        generate_status=_normalize_generate_status(row.get("generate_status")),
        schema_version="1.0",
        overview=overview,
        key_figures=key_figures,
        phases=phases,
        relationships=relationships,
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
        "topic_name": normalize_text(topic["topic_name"]),
        "news_items": [
            {
                "id": int(row["id"]),
                "title": normalize_text(row["title"]),
                "content": normalize_text(row["content"]),
                "source": normalize_text(row.get("source")),
                "publish_time": _format_publish_time(row.get("publish_time")),
            }
            for row in news_rows
        ],
    }


def _build_local_timeline(topic: dict[str, Any], news_rows: list[dict[str, Any]]) -> TimelineGenerateResult:
    topic_name = normalize_text(topic["topic_name"])

    # Event type assignment based on position in timeline
    _event_types = ["background", "policy", "reaction", "breakthrough", "outcome"]

    # Collect all source names for key figures
    source_names: list[str] = []

    nodes = []
    for index, row in enumerate(news_rows, start=1):
        summary = normalize_text(row.get("summary")) or normalize_text(row.get("content"))[:100]
        if len(summary) > 100:
            summary = f"{summary[:100]}..."
        detail = normalize_text(row.get("content"))[:300]
        if len(detail) > 300:
            detail = f"{detail[:300]}..."

        # Extract keywords from tags if available
        tags = row.get("tags")
        if isinstance(tags, str):
            try:
                tags = json.loads(tags)
            except (json.JSONDecodeError, TypeError):
                tags = []
        # 优先使用清洗后的 tags；如果 tags 为空，fallback 到 topic_name，再 fallback 到 category_name
        if isinstance(tags, list) and tags:
            keywords = list(tags[:4])
        else:
            topic_name = normalize_text(row.get("topic_name") or "")
            if topic_name:
                keywords = [topic_name]
            else:
                cat_name = normalize_text(row.get("category_name") or "")
                keywords = [cat_name] if cat_name else []

        # Varied event type
        event_type = _event_types[min(index - 1, len(_event_types) - 1)]

        # Varied importance based on position (first and last events more important)
        n = len(news_rows)
        if n <= 2:
            importance = 4
        elif index == 1:
            importance = 4
        elif index == n:
            importance = 5
        else:
            importance = 3

        # Related events: previous and next
        related = []
        if index > 1:
            related.append(index - 1)
        if index < len(news_rows):
            related.append(index + 1)

        source_name = normalize_text(row.get("source"))
        if source_name:
            source_names.append(source_name)

        nodes.append(
            TimelineNode(
                event_id=index,
                event_time=_format_publish_time(row.get("publish_time")),
                event_title=normalize_text(row["title"]),
                event_summary=summary,
                source_news_id=int(row["id"]),
                source_title=normalize_text(row["title"]),
                source_name=source_name,
                event_type=event_type,
                importance=importance,
                event_detail=detail,
                related_event_ids=related,
                keywords=keywords,
            )
        )

    now = _now_text()

    # Build phases as proper model objects
    phases: list[TimelinePhase] = []
    n = len(nodes)
    if n >= 4:
        third = max(n // 3, 1)
        phases = [
            TimelinePhase(name="初期阶段", start_event_id=1, end_event_id=third),
            TimelinePhase(name="发展阶段", start_event_id=third + 1, end_event_id=third * 2),
            TimelinePhase(name="当前阶段", start_event_id=third * 2 + 1, end_event_id=n),
        ]
    elif n >= 2:
        phases = [
            TimelinePhase(name="起始阶段", start_event_id=1, end_event_id=max(1, n // 2)),
            TimelinePhase(name="后续发展", start_event_id=max(2, n // 2 + 1), end_event_id=n),
        ]

    # Build relationships as proper model objects
    relationships: list[TimelineRelationship] = []
    for i in range(1, n):
        edge_type: Literal["causes", "follows", "parallel"] = "follows"
        if n >= 3 and i <= n // 3:
            edge_type = "causes"
        relationships.append(TimelineRelationship(from_id=i, to_id=i + 1, type=edge_type))

    # Key figures from unique source names
    key_figures = list(dict.fromkeys(source_names))[:5]

    return TimelineGenerateResult(
        topic_id=int(topic["id"]),
        topic_name=topic_name,
        timeline=nodes,
        source="mock",
        generated_at=now,
        updated_at=now,
        generate_status="mock",
        schema_version="1.0",
        overview=f"本事件脉络涵盖「{topic_name}」的主要发展过程，共包含{len(nodes)}个关键事件节点，由{len(key_figures)}个信息来源提供报道。",
        key_figures=key_figures,
        phases=phases,
        relationships=relationships,
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
                event_time=normalize_text(item.get("event_time")),
                event_title=normalize_text(item.get("event_title")),
                event_summary=normalize_text(item.get("event_summary")),
                source_news_id=int(item.get("source_news_id") or 0),
                source_title=normalize_text(item.get("source_title")),
                source_name=normalize_text(item.get("source_name")),
                event_type=normalize_text(item.get("event_type", "other")),
                importance=int(item.get("importance", 3)),
                event_detail=normalize_text(item.get("event_detail", "")),
                related_event_ids=[int(eid) for eid in item.get("related_event_ids", [])],
                keywords=[str(k) for k in item.get("keywords", [])],
            )
        )

    if not nodes:
        return None

    now = _now_text()
    
    metadata = data.get("metadata", {})
    if not isinstance(metadata, dict):
        metadata = {}
    
    phases_data = data.get("phases", metadata.get("phases", []))
    phases = [
        TimelinePhase(
            name=normalize_text(p.get("name")),
            start_event_id=int(p.get("start_event_id", 0)),
            end_event_id=int(p.get("end_event_id", 0)),
        )
        for p in phases_data
        if isinstance(p, dict)
    ]

    relationships_data = data.get("relationships", [])
    relationships = [
        TimelineRelationship(
            from_id=int(r.get("from_id", 0)),
            to_id=int(r.get("to_id", 0)),
            type=normalize_text(r.get("type", "follows")),
        )
        for r in relationships_data
        if isinstance(r, dict)
    ]

    return TimelineGenerateResult(
        topic_id=int(topic["id"]),
        topic_name=normalize_text(data.get("topic_name") or topic["topic_name"]),
        timeline=nodes,
        source="ai-service",
        generated_at=normalize_text(data.get("generated_at")) or now,
        updated_at=normalize_text(data.get("updated_at")) or now,
        generate_status=normalize_text(data.get("generate_status"), "generated"),
        schema_version="1.0",
        overview=normalize_text(data.get("overview", metadata.get("overview", ""))),
        key_figures=[str(kf) for kf in data.get("key_figures", metadata.get("key_figures", []))],
        phases=phases,
        relationships=relationships,
    )


def _fetch_topics() -> list[TimelineTopic]:
    try:
        topics = _db_topics()
        if topics is not None:
            return topics
    except Exception as exc:  # noqa: BLE001
        logger.warning("读取 Timeline 话题数据库失败，回退 mock：%s", exc)
    # 仅在数据库异常时才回退 mock
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
                ai_result.generate_status = "generated"
                try:
                    _save_cache_to_db(ai_result)
                except Exception as exc:  # noqa: BLE001
                    logger.warning("Timeline AI 缓存写入数据库失败，回退 mock：%s", exc)
                    _save_cache_to_mock(ai_result)
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
    if cached is not None:
        if cached.get("generate_status") == "generating":
            return TimelineGenerateResult(
                topic_id=topic_id,
                topic_name=normalize_text(topic["topic_name"]),
                timeline=[],
                source="cache",
                generate_status="generating",
                schema_version="1.0",
                overview="",
                key_figures=[],
                phases=[],
                relationships=[],
            )
        if cached.get("timeline_json") and _cached_timeline_matches_news(cached, news_rows):
            source = "cache"
            if cached.get("generate_status") == "mock":
                source = "mock"
            return _timeline_row_to_result(cached, topic, source=source)

        logger.info(
            "Timeline 缓存与当前数据库新闻不一致，忽略旧缓存并重新生成：topic_id=%s",
            topic_id,
        )

    return await _generate_with_ai_or_fallback(topic, news_rows)


async def generate_timeline(topic_id: int, current_user: Optional[UserInfo] = None) -> TimelineGenerateResult:
    if current_user is None:
        raise AppException(code=401, message="未登录或登录状态已失效")

    topic = _get_topic(topic_id)
    if topic is None:
        raise AppException(code=404, message="话题不存在")

    news_rows = _get_topic_news(topic_id)[1]
    if len(news_rows) < 2:
        raise AppException(code=400, message="同一话题下至少需要 2 篇新闻才能生成事件脉络")

    try:
        now = _now_text()
        existing = _cached_timeline_from_db(topic_id)
        if existing is None:
            execute_update(
                """
                INSERT INTO event_timeline (
                    topic_id, timeline_json, source_news_ids,
                    generate_status, generated_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s)
                """,
                [
                    topic_id,
                    json.dumps([], ensure_ascii=False),
                    json.dumps([], ensure_ascii=False),
                    "generating",
                    now,
                    now,
                ],
            )
        else:
            execute_update(
                """
                UPDATE event_timeline
                   SET timeline_json = %s,
                       source_news_ids = %s,
                       generate_status = %s,
                       generated_at = %s,
                       updated_at = %s
                 WHERE id = %s
                """,
                [
                    json.dumps([], ensure_ascii=False),
                    json.dumps([], ensure_ascii=False),
                    "generating",
                    now,
                    now,
                    int(existing["id"]),
                ],
            )
    except Exception as exc:
        logger.warning("设置生成中状态失败：%s", exc)

    return await _generate_with_ai_or_fallback(topic, news_rows)
