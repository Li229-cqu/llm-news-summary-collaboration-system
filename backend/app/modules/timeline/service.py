"""Timeline 模块服务层：数据库优先，mock 兜底。"""

from __future__ import annotations

import json
import logging
import re
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
        source_type=normalize_text(row.get("source_type")) or "manual",
        auto_generated_at=normalize_text(row.get("auto_generated_at")) or None,
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


def _normalize_timeline_event_type(value: Any) -> Literal["policy", "reaction", "breakthrough", "outcome", "background", "other"]:
    event_type = normalize_text(value, "other")
    allowed = {"policy", "reaction", "breakthrough", "outcome", "background", "other"}
    if event_type in allowed:
        return event_type  # type: ignore[return-value]
    return "other"


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
            nt.source_type,
            nt.auto_generated_at,
            COALESCE(COUNT(n.id), 0) AS news_count
        FROM news_topic nt
        LEFT JOIN news n
          ON n.topic_id = nt.id
         AND n.status = 1
        WHERE nt.status = 1
        GROUP BY nt.id, nt.topic_name, nt.keyword_list, nt.heat_score, nt.summary, nt.status, nt.source_type, nt.auto_generated_at
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
            source_type=normalize_text(row.get("source_type")) or "manual",
            auto_generated_at=normalize_text(row.get("auto_generated_at")) or None,
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
    if _event_timeline_supports_metadata_json():
        row = execute_one(
            """
            SELECT
                id,
                topic_id,
                timeline_json,
                source_news_ids,
                metadata_json,
                generate_status,
                generated_at,
                updated_at
            FROM event_timeline
            WHERE topic_id = %s
            LIMIT 1
            """,
            [topic_id],
        )
    else:
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
    row.setdefault("metadata_json", "{}")
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


def _cached_timeline_matches_news(cached: dict[str, Any], news_rows: list[dict[str, Any]] | list[int]) -> bool:
    cached_ids: list[int] = []
    for item in _parse_json_list(cached.get("source_news_ids"), []):
        try:
            cached_ids.append(int(item))
        except (TypeError, ValueError):
            continue

    current_ids: list[int] = []
    for row in news_rows:
        try:
            current_ids.append(int(row["id"] if isinstance(row, dict) else row))
        except (TypeError, ValueError, KeyError):
            continue

    return bool(cached_ids) and cached_ids == current_ids


def _cached_timeline_metadata(cached: dict[str, Any] | None) -> dict[str, Any]:
    if not cached:
        return {}
    return _parse_json_dict(cached.get("metadata_json"), {})


def _is_low_quality_cached_timeline(cached: dict[str, Any] | None) -> bool:
    if not cached:
        return False
    status = normalize_text(cached.get("generate_status")).lower()
    metadata = _cached_timeline_metadata(cached)
    mode = normalize_text(metadata.get("generate_mode")).lower()
    return status in {"mock", "fallback", "auto"} or mode in {"local_fallback", "mock", "auto", "auto_cluster"}


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
    timeline = [
        TimelineNode(**{**item, "event_type": _normalize_timeline_event_type(item.get("event_type"))})
        for item in timeline_json
        if isinstance(item, dict)
    ]
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


def _event_timeline_supports_metadata_json() -> bool:
    try:
        cols = execute_query("SHOW COLUMNS FROM event_timeline LIKE 'metadata_json'")
        return bool(cols)
    except Exception:
        return False


def _save_cache_to_db(result: TimelineGenerateResult, metadata: dict[str, Any] | None = None) -> None:
    payload = _mock_result_to_cache_payload(result)
    now = _now_text()
    existing = _cached_timeline_from_db(result.topic_id)
    metadata_json = json.dumps(metadata or {}, ensure_ascii=False)
    metadata_supported = _event_timeline_supports_metadata_json()
    if existing is None:
        if metadata_supported:
            execute_update(
                """
                INSERT INTO event_timeline (
                    topic_id, timeline_json, source_news_ids,
                    metadata_json, generate_status, generated_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                [
                    payload["topic_id"],
                    json.dumps(payload["timeline_json"], ensure_ascii=False),
                    json.dumps(payload["source_news_ids"], ensure_ascii=False),
                    metadata_json,
                    payload["generate_status"],
                    payload["generated_at"] or now,
                    payload["updated_at"] or now,
                ],
            )
        else:
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

    if metadata_supported:
        execute_update(
            """
            UPDATE event_timeline
               SET timeline_json = %s,
                   source_news_ids = %s,
                   metadata_json = %s,
                   generate_status = %s,
                   generated_at = %s,
                   updated_at = %s
             WHERE topic_id = %s
            """,
            [
                json.dumps(payload["timeline_json"], ensure_ascii=False),
                json.dumps(payload["source_news_ids"], ensure_ascii=False),
                metadata_json,
                payload["generate_status"],
                payload["generated_at"] or now,
                payload["updated_at"] or now,
                payload["topic_id"],
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


_FALLBACK_ACTION_WORDS = [
    "宣布", "发布", "回应", "确认", "否认", "警告", "呼吁", "举行", "启动", "推进",
    "调整", "公布", "签署", "达成", "调查", "逮捕", "撤离", "升级", "打击", "袭击",
    "谴责", "制裁", "会晤", "访问", "批准", "通过", "开放", "关闭", "暂停", "恢复",
    "聚焦", "讨论", "关注", "晋级", "夺冠", "胜出", "出线", "落败", "开幕", "闭幕",
    "审议", "出台", "亮相", "提速", "展开", "对决", "出炉", "上线", "联动",
    "举办", "召开发布", "展出", "演讲", "高峰", "揭幕", "入驻", "研发", "开通",
]

_MECHANICAL_TITLE_SUFFIXES = ["相关消息", "持续关注", "最新动态", "热点新闻", "相关动态", "最新消息"]

_TITLE_NOISE_PREFIX = re.compile(
    r"^(中新社|新华社|人民日报|中新网|央视新闻|快讯[：:]|速览[：:]|一分钟[：:]"
    r"|最新消息[：:]|相关报道[：:]|综合消息[：:]|（[^）]*）|【[^】]*】"
    r"|\"[^\"]*\"|'[^']*')"
)

_ENTITY_COMPRESS_MAP: dict[str, str] = {
    "人工智能安全": "AI安全",
    "人工智能": "AI",
    "网络安全": "网安",
    "国家网络安全宣传周": "网安周",
    "国家网安周": "网安周",
    "网络安全宣传周": "网安周",
    "网信事业": "网信",
    "美加墨世界杯": "世界杯",
    "世界杯": "世界杯",
    "世界乒乓球职业大联盟": "WTT",
    "国际足联": "FIFA",
}

_BROAD_TOPIC_CLASS_WORDS = {
    "国际", "国内", "社会", "财经", "体育", "科技", "娱乐", "军事", "教育", "健康",
}

_BROAD_TOPIC_WEAK_WORDS = {
    "热点", "动态", "进展", "聚焦", "观察", "关注", "最新", "消息", "新闻", "局势",
    "发展", "趋势", "综合", "速览", "事件", "相关", "持续", "更新", "报道", "市场",
}

# 泛主体黑名单 — 这些词永远不能作为主体
_FORBIDDEN_SUBJECTS = {
    "国家", "中国", "全国", "相关", "事件", "问题", "消息", "新闻",
    "动态", "进展", "聚焦", "热点", "发展", "工作", "情况", "方面",
    "领域", "人民", "记者", "报道", "消息称",
}

_WEAK_SUBJECT_WORDS = _BROAD_TOPIC_CLASS_WORDS | _BROAD_TOPIC_WEAK_WORDS | _FORBIDDEN_SUBJECTS

_CATEGORY_ACTION_MAP: dict[str, str] = {
    "体育": "对决",
    "时政": "发布",
    "科技": "发布",
    "财经": "调整",
    "国际": "升级",
}

# 场景 → 动作映射（标题中出现这些线索词就找对应动作）
_SCENE_ACTION_HINTS: list[tuple[list[str], str]] = [
    (["案例", "发布"], "发布"),
    (["案例"], "出炉"),
    (["博览会", "博览"], "举办"),
    (["论坛", "峰会"], "举行"),
    (["安全周", "网安周"], "展开"),
    (["高质量", "发展", "助力"], "提速"),
    (["比赛", "赛事", "对决", "大满贯", "锦标赛"], "对决"),
    (["开幕", "揭幕"], "开幕"),
    (["博览会"], "开幕"),
    (["上线", "亮相"], "亮相"),
    (["宣布", "通告"], "宣布"),
    (["打击", "袭击"], "打击"),
]

# 标点 / 分隔符（在此处可以安全切分）
_SAFE_SPLIT_RE = re.compile(r"[，。：:；;｜|—\-…]+")

# 不能截断的中文字符对（前开后闭）
_OPEN_QUOTES = {'"', '"', ''', ''', '（', '(', '【', '[', '《', '<'}
_CLOSE_QUOTES = {'"', '"', ''', ''', '）', ')', '】', ']', '》', '>'}


def _is_weak_event_title(title: str) -> bool:
    """判定标题是否太泛，缺乏信息量。"""
    if not title:
        return True
    if len(title) <= 3:
        return True
    if title in _FORBIDDEN_SUBJECTS or title in _BROAD_TOPIC_WEAK_WORDS or title in _BROAD_TOPIC_CLASS_WORDS:
        return True
    # 仅含弱词不包含任何具体实体的标题
    _weak_patterns = [
        "国家", "中国", "相关", "事件", "最新",
    ]
    has_any = any(kw in title for kw in _weak_patterns)
    # 如果只由弱词组成（不含长词 3+ char 的专有名词）
    long_tokens = [c for c in _TOKENIZE_CJK(title) if len(c) >= 3 and c not in _WEAK_SUBJECT_WORDS]
    if not long_tokens and len(title) <= 6:
        return True
    if has_any and not long_tokens:
        return True
    return False


def _TOKENIZE_CJK(text: str) -> list[str]:
    """简单 CJK 分片：按单字切分后，合并连续的 CJK 字符为词。"""
    result: list[str] = []
    buf = ""
    for ch in text:
        if "一" <= ch <= "鿿" or "㐀" <= ch <= "䶿":
            buf += ch
        else:
            if buf:
                result.append(buf)
                buf = ""
    if buf:
        result.append(buf)
    return result


def _safe_phrase_trim(text: str, max_len: int = 18) -> str:
    """按短语边界安全裁剪，禁止截断在引号/括号/英文词中间。

    返回裁剪后的文本，不加省略号。
    """
    if not text:
        return text
    if len(text) <= max_len:
        return text

    # 策略 1：在安全分隔符处切分，取第一个完整短语
    parts = _SAFE_SPLIT_RE.split(text)
    # 收集前缀直到最大长度
    result = ""
    for part in parts:
        part = part.strip()
        if not part:
            continue
        if part in _FORBIDDEN_SUBJECTS or part in _BROAD_TOPIC_WEAK_WORDS:
            continue
        candidate = (result + part) if not result else f"{result}·{part}"
        if len(candidate) <= max_len:
            result = candidate if not result else f"{result}·{part}"
        else:
            if result and len(result) >= 4:
                return result
            # 单个 part 太长，做安全裁剪
            if part and len(part) <= max_len:
                return part
            if part:
                return _safe_phrase_trim(part, max_len)
            break
    if result and len(result) >= 4:
        return result

    # 策略 2：在标题末尾的不完整段前截断
    last_ok = max_len
    for quote_char in _OPEN_QUOTES:
        pos = text.rfind(quote_char, 0, max_len)
        if pos > 0:
            last_ok = min(last_ok, pos)
    # 不要在英文字母中间截断
    for i in range(max_len, max_len - 4, -1):
        if i < len(text) and text[i].isascii() and text[i].isalpha():
            j = i
            while j > 0 and text[j].isalpha():
                j -= 1
            if j > 0:
                last_ok = min(last_ok, j + 1)

    # 策略 3：在 CJK 字符边界截断（不在非 CJK 字符中间）
    for i in range(min(max_len, len(text)), max_len - 8, -1):
        ch = text[i - 1] if i <= len(text) else ""
        if ch and ("一" <= ch <= "鿿" or ch in "，。；;：:！!？?"):
            return text[:i]

    return text[:last_ok]


def _extract_info_segment(text: str, max_len: int = 16) -> str:
    """从清洗后的标题中提取最有信息量的连续片段（安全裁剪）。"""
    temp = text
    for word in sorted(_FORBIDDEN_SUBJECTS | _BROAD_TOPIC_WEAK_WORDS, key=len, reverse=True):
        temp = temp.replace(word, "")
    temp = re.sub(r"\s+", "", temp).strip(" -_，。；;：:")
    if temp and len(temp) <= max_len:
        return temp
    if temp:
        return _safe_phrase_trim(temp, max_len)
    return _safe_phrase_trim(text, max_len)


# ═══════════════════════════════════════════════════════════════════════
# 事件化短标题生成
# ═══════════════════════════════════════════════════════════════════════

def build_short_event_title(
    raw_title: str,
    topic_name: str | None = None,
    core_entities: list[str] | None = None,
    category_name: str | None = None,
) -> str:
    """生成 8～14 字（最多 20 字）的事件化短标题。禁止机械截断。"""
    MAX_TITLE = 14
    MAX_EXTENDED = 20  # 宁可稍长也不截成半句话

    # ── 1. 清洗 ──
    cleaned = _TITLE_NOISE_PREFIX.sub("", normalize_text(raw_title))
    cleaned = cleaned.strip(" -_，。；;：:\"'「」『』《》、|!！?？\n\r\t\v")
    for suffix in _MECHANICAL_TITLE_SUFFIXES:
        cleaned = cleaned.replace(suffix, "")
    cleaned = re.sub(r"\s+", "", cleaned)
    cleaned = cleaned.strip(" -_，。；;：:")
    if not cleaned:
        cleaned = normalize_text(raw_title).strip()

    # ── 2. 如果清洗后天然 ≤MAX_TITLE 且不弱，直接返回 ──
    if len(cleaned) <= MAX_TITLE and not _is_weak_event_title(cleaned):
        return cleaned

    # ── 3. 压缩长实体 ──
    compressed = cleaned
    for long_name, short_name in sorted(_ENTITY_COMPRESS_MAP.items(), key=lambda x: -len(x[0])):
        if long_name in compressed:
            compressed = compressed.replace(long_name, short_name)

    # ── 4. 候选实体 ──
    entities: list[str] = []
    if core_entities:
        for e in core_entities:
            e_compressed = _ENTITY_COMPRESS_MAP.get(e, e)
            if e_compressed and e_compressed not in _WEAK_SUBJECT_WORDS and e_compressed not in _FORBIDDEN_SUBJECTS:
                if e_compressed not in entities:
                    entities.append(e_compressed)
    if topic_name:
        tn = _ENTITY_COMPRESS_MAP.get(topic_name, topic_name)
        if tn not in entities and tn not in _WEAK_SUBJECT_WORDS and tn not in _FORBIDDEN_SUBJECTS:
            entities.append(tn)

    # ── 5. 识别动作词 ──
    action = ""
    for word in _FALLBACK_ACTION_WORDS:
        if word in cleaned or word in compressed:
            action = word
            break
    if not action:
        for hints, default_act in _SCENE_ACTION_HINTS:
            for hint in hints:
                if hint in cleaned or hint in compressed:
                    action = default_act
                    break
            if action:
                break

    # ── 6. 提取主体 ──
    subject = ""
    if entities:
        for e in entities:
            if e and (e in compressed or e in cleaned):
                subject = e
                break
        if not subject and entities:
            subject = entities[0]
    if not subject:
        temp = compressed
        for w in _FALLBACK_ACTION_WORDS:
            temp = temp.replace(w, "")
        for bad in _FORBIDDEN_SUBJECTS | _BROAD_TOPIC_WEAK_WORDS:
            temp = temp.replace(bad, "")
        temp = re.sub(r"\s+", "", temp).strip(" -_，。；;：:")
        if temp and len(temp) >= 2:
            subject = temp[:8]
    if not subject or subject in _FORBIDDEN_SUBJECTS or subject in _WEAK_SUBJECT_WORDS:
        if topic_name:
            tn_compressed = _ENTITY_COMPRESS_MAP.get(topic_name, topic_name)
            if tn_compressed not in _FORBIDDEN_SUBJECTS and tn_compressed not in _WEAK_SUBJECT_WORDS:
                subject = tn_compressed[:8]
    for entity in (core_entities or []):
        if entity and entity in cleaned and len(entity) <= 8:
            entity_compressed = _ENTITY_COMPRESS_MAP.get(entity, entity)
            if entity_compressed not in _FORBIDDEN_SUBJECTS and entity not in _WEAK_SUBJECT_WORDS:
                subject = entity_compressed
                break
    if not subject:
        subject = _extract_info_segment(compressed, 8)

    if not action:
        action = "推进"
        if category_name:
            action = _CATEGORY_ACTION_MAP.get(category_name, action)

    # ── 7. 优先走事件模板 ──
    special = _apply_event_template_rules(cleaned, compressed, subject)
    if special:
        return special

    # ── 8. 拼合：主体 + 动作 ──
    if subject and action:
        combined = f"{subject}{action}"
        if len(combined) <= MAX_TITLE and not _is_weak_event_title(combined):
            return combined
        max_sub = MAX_TITLE - len(action)
        if max_sub >= 2:
            trimmed = f"{subject[:max_sub]}{action}"
            if not _is_weak_event_title(trimmed):
                return trimmed

    # ── 9. 安全短语提取 ──
    segment = _extract_info_segment(cleaned, MAX_EXTENDED)
    if segment and not _is_weak_event_title(segment):
        return segment

    # ── 10. 最终兜底：宁可返回完整清洗标题（安全裁剪） ──
    if cleaned and len(cleaned) <= MAX_EXTENDED * 2 and not _is_weak_event_title(cleaned):
        return _safe_phrase_trim(cleaned, MAX_EXTENDED)

    return _safe_phrase_trim(cleaned, MAX_EXTENDED) if cleaned else "事件节点"


def _apply_event_template_rules(cleaned: str, compressed: str, subject: str = "") -> str | None:
    """应用常见标题模板规则，返回生成结果或 None。"""

    # ── 发布 + 平台 / 算法 ──
    if "发布" in cleaned:
        if any(kw in cleaned for kw in ("平台", "全栈")):
            return "异算方舟平台发布" if "异算方舟" in cleaned else "算法平台发布"
        if any(kw in cleaned for kw in ("AI", "人工智能")):
            return "AI平台发布"
        if "杭州" in cleaned:
            return "杭州发布AI平台"
        return "案例成果发布"

    # ── 调研 ──
    if "调研" in cleaned:
        if "智能算柜" in cleaned or "算柜" in cleaned:
            return "智能算柜调研"
        if "算力" in cleaned:
            return "算力建设调研"
        return "产业调研报告"

    # ── 新能源 ──
    if any(kw in cleaned for kw in ("新能源", "新能源汽车", "新能源车")):
        if any(kw in cleaned for kw in ("动能", "发展")):
            return "新能源车添动能"
        return "新能源车发展提速"

    # ── 网络安全 → 网安 ──
    if any(kw in cleaned for kw in ("网络安全", "网安")):
        if any(kw in cleaned for kw in ("博览会", "博览")):
            return "网安博览会举办"
        if any(kw in cleaned for kw in ("论坛", "高峰")):
            return "网安论坛举行"
        if any(kw in cleaned for kw in ("宣传周", "网安周")):
            return "网安周议题展开"
        if any(kw in cleaned for kw in ("专家", "大咖")):
            return "专家聚焦网安"
        return "网安议题展开"

    # ── 网信事业 ──
    if any(kw in cleaned for kw in ("网信", "网信事业")):
        if any(kw in cleaned for kw in ("高质量", "发展", "助力")):
            return "网信发展提速"
        return "网信议题推进"

    # ── AI 安全 ──
    if any(kw in cleaned for kw in ("人工智能安全", "AI安全")):
        if any(kw in cleaned for kw in ("案例", "实践")):
            return "AI安全案例发布"
        return "AI安全议题推进"

    # ── 世界杯 ──
    if any(kw in cleaned for kw in ("世界杯", "美加墨")):
        if any(kw in cleaned for kw in ("筹备", "准备", "推进")):
            return "世界杯筹备推进"
        if any(kw in cleaned for kw in ("开幕", "揭幕")):
            return "世界杯开幕"
        return "世界杯赛事进展"

    # ── WTT / 乒乓球 ──
    if any(kw in cleaned for kw in ("WTT", "乒乓球", "大满贯")):
        if any(kw in cleaned for kw in ("晋级", "胜出", "夺冠")):
            return "王楚钦晋级" if "王楚钦" in cleaned else "WTT赛事晋级"
        return "WTT赛事焦点"

    # ── 伊朗 / 以色列 ──
    if any(kw in cleaned for kw in ("伊朗", "以色列")):
        if any(kw in cleaned for kw in ("打击", "袭击")):
            return "伊朗打击升级"
        if any(kw in cleaned for kw in ("导弹", "军事")):
            return "伊以冲突升级"
        return "伊以局势升温"

    # ── 委内瑞拉 ──
    if "委内瑞拉" in cleaned:
        return "委内瑞拉局势进展"

    # ── 案例 ──
    if "案例" in cleaned:
        if "发布" in cleaned:
            return "典型案例发布"
        return "实践案例出炉"

    # ── 博览会 ──
    if any(kw in cleaned for kw in ("博览会", "博览")):
        return "博览会主题活动"

    # ── 广东 + 发改委 ──
    if any(kw in cleaned for kw in ("广东", "广东省")):
        if any(kw in cleaned for kw in ("发改委", "创新")):
            return "广东发改委谈创新"

    # ── 办公租赁 ──
    if "办公租赁" in cleaned:
        return "办公租赁需求增长"

    # ── 韩国 + AI / 芯片 ──
    if "韩国" in cleaned:
        if any(kw in cleaned for kw in ("AI", "人工智能", "芯片", "半导体")):
            return "韩国AI芯片布局"
        return "韩国科技产业布局"

    # ── 使命感 / 创作 ──
    if any(kw in cleaned for kw in ("使命感", "创作")):
        if "创作" in cleaned:
            return "创作使命感引热议"
        return "创作议题引关注"

    # ── 超级个体 ──
    if "超级个体" in cleaned:
        return "超级个体平台发布"

    return None


def _strip_mechanical_title(text: str) -> str:
    title = normalize_text(text)
    for suffix in _MECHANICAL_TITLE_SUFFIXES:
        title = title.replace(suffix, "")
    return title.strip(" -_，。；;：:")


def _shorten_text(text: str, max_len: int) -> str:
    value = normalize_text(text)
    if len(value) <= max_len:
        return value
    return f"{value[:max_len - 3]}..."


def _topic_keywords(topic: dict[str, Any]) -> list[str]:
    keywords = _parse_json_list(topic.get("keyword_list"), [])
    return [normalize_text(k) for k in keywords if normalize_text(k)]


def _build_validation_metadata(validation: dict[str, Any], generate_mode: str) -> dict[str, Any]:
    return {
        "generate_mode": generate_mode,
        "core_entities": validation.get("core_entities", []),
        "entity_purity": validation.get("entity_purity", 0),
        "quality_flags": validation.get("quality_flags", []),
        "quality_reasons": validation.get("quality_reasons", []),
        "removed_news_ids": validation.get("removed_news_ids", []),
        "removed_news_titles": validation.get("removed_news_titles", []),
        "removed_count": len(validation.get("removed_news_ids", [])),
        "effective_news_count": len(validation.get("kept_news", [])),
        "raw_news_count": validation.get("raw_news_count", 0),
    }


def _validate_and_filter_topic_news(topic: dict[str, Any], news_rows: list[dict[str, Any]]) -> dict[str, Any]:
    from app.modules.timeline.cluster_service import (
        _compute_entity_purity,
        _extract_core_entities_from_news,
        _filter_outlier_news,
        _is_broad_topic_name,
    )

    topic_name = normalize_text(topic.get("topic_name"))
    topic_seed = {
        "id": 0,
        "title": topic_name,
        "summary": normalize_text(topic.get("summary")),
        "content": " ".join(_topic_keywords(topic)),
        "tags": _topic_keywords(topic),
        "category_name": "",
    }
    entity_source = [topic_seed] + list(news_rows)
    core_entities = _extract_core_entities_from_news(entity_source)
    broad, broad_reasons = _is_broad_topic_name(topic_name, core_entities)

    quality_flags: list[str] = []
    quality_reasons: list[str] = []
    if broad:
        quality_flags.append("broad_topic")
        quality_reasons.extend(broad_reasons)

    outlier_result = _filter_outlier_news(news_rows, core_entities, topic_name)
    kept_news = outlier_result.get("kept_news_items", list(news_rows))
    removed_news = outlier_result.get("removed_news_items", [])
    removed_news_ids = outlier_result.get("removed_news_ids", [])
    removed_news_titles = outlier_result.get("removed_news_titles", [])
    entity_purity, entity_hits = _compute_entity_purity(kept_news, core_entities)

    raw_count = len(news_rows)
    removed_ratio = len(removed_news_ids) / max(raw_count, 1)
    valid = True
    error_message = ""
    if broad:
        valid = False
        error_message = "当前话题覆盖范围过宽，暂不适合生成事件脉络，请在后台拆分为更具体的话题后再生成。"
    elif len(kept_news) < 2:
        valid = False
        quality_flags.append("too_small_after_filter")
        quality_reasons.append("effective_news_count_lt_2")
        error_message = "有效相关新闻不足，无法生成事件脉络。"
    elif entity_purity < 0.45 and removed_ratio > 0.4:
        valid = False
        quality_flags.append("low_coherence")
        quality_reasons.append(f"entity_purity:{entity_purity}")
        quality_reasons.append(f"removed_ratio:{removed_ratio:.2f}")
        error_message = "当前话题下新闻关联度较低，建议重新聚类或手动调整话题归类。"
    elif removed_news_ids:
        quality_flags.append("outlier_removed")
        quality_reasons.append(f"removed_outliers:{len(removed_news_ids)}")

    return {
        "kept_news": kept_news,
        "removed_news": removed_news,
        "removed_news_ids": removed_news_ids,
        "removed_news_titles": removed_news_titles,
        "core_entities": core_entities,
        "entity_purity": entity_purity,
        "entity_hits": entity_hits,
        "quality_flags": quality_flags,
        "quality_reasons": quality_reasons,
        "is_broad_topic": broad,
        "valid": valid,
        "error_message": error_message,
        "raw_news_count": raw_count,
    }


def _raise_if_invalid_topic_news(validation: dict[str, Any]) -> None:
    if not validation.get("valid", True):
        raise AppException(code=400, message=validation.get("error_message") or "当前话题暂不适合生成事件脉络。")


def _build_fallback_event_title(
    news_item: dict[str, Any],
    topic_name: str,
    core_entities: list[str] | None = None,
) -> str:
    """使用 build_short_event_title 生成 8～14 字事件化短标题。"""
    raw_title = normalize_text(news_item.get("title", ""))
    cat_name = normalize_text(news_item.get("category_name", ""))
    source_title = normalize_text(news_item.get("title", ""))
    return build_short_event_title(
        raw_title=source_title,
        topic_name=topic_name,
        core_entities=core_entities,
        category_name=cat_name or None,
    )


def _build_fallback_event_summary(
    news_item: dict[str, Any],
    topic_name: str,
    core_entities: list[str] | None = None,
) -> str:
    summary = normalize_text(news_item.get("summary"))
    if not summary or len(summary) < 10:
        content = normalize_text(news_item.get("content"))
        parts = re.split(r"[。！？!?；;]\s*", content)
        summary = normalize_text(parts[0] if parts else content)
    summary = re.sub(r"^(本文|这篇文章|该文)(介绍了|讲述了|报道了)?", "", summary).strip()
    entity_text = "、".join((core_entities or [])[:3])
    if summary:
        base = f"根据报道，{_shorten_text(summary, 72)}。"
        if entity_text:
            base += f"该进展与“{topic_name}”中的{entity_text}等要素相关。"
    else:
        base = f"该节点反映了“{topic_name}”在该时间点的新进展。"
        if entity_text:
            base += f"相关报道主要围绕{entity_text}展开。"
    return _shorten_text(base, 120)


def _build_local_timeline(
    topic: dict[str, Any],
    news_rows: list[dict[str, Any]],
    validation: dict[str, Any] | None = None,
) -> TimelineGenerateResult:
    topic_name = normalize_text(topic["topic_name"])
    core_entities = (validation or {}).get("core_entities", [])

    # Event type assignment based on position in timeline
    _event_types = ["background", "policy", "reaction", "breakthrough", "outcome"]

    # Collect all source names for key figures
    source_names: list[str] = []

    nodes = []
    for index, row in enumerate(news_rows, start=1):
        summary = _build_fallback_event_summary(row, topic_name, core_entities)
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
            row_topic_name = normalize_text(row.get("topic_name") or "")
            if row_topic_name:
                keywords = [row_topic_name]
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
                event_title=_build_fallback_event_title(row, topic_name, core_entities),
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
                event_title=build_short_event_title(
                    raw_title=normalize_text(item.get("source_title", item.get("event_title", ""))),
                    topic_name=normalize_text(topic.get("topic_name", data.get("topic_name", ""))),
                    core_entities=None,
                    category_name=normalize_text(item.get("category_name", "")),
                ),
                event_summary=normalize_text(item.get("event_summary")),
                source_news_id=int(item.get("source_news_id") or 0),
                source_title=normalize_text(item.get("source_title")),
                source_name=normalize_text(item.get("source_name")),
                event_type=_normalize_timeline_event_type(item.get("event_type")),
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


async def _generate_with_ai_or_fallback(
    topic: dict[str, Any],
    news_rows: list[dict[str, Any]],
    validation: dict[str, Any] | None = None,
) -> TimelineGenerateResult:
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
                metadata = _build_validation_metadata(validation or {"kept_news": news_rows}, "ai")
                try:
                    _save_cache_to_db(ai_result, metadata=metadata)
                except Exception as exc:  # noqa: BLE001
                    logger.warning("Timeline AI 缓存写入数据库失败，回退 mock：%s", exc)
                    _save_cache_to_mock(ai_result)
                return ai_result
    except (httpx.HTTPError, ValueError, KeyError, TypeError) as exc:
        logger.warning("AI Timeline 调用失败，回退本地规则：%s", exc)

    fallback = _build_local_timeline(topic, news_rows, validation=validation)
    metadata = _build_validation_metadata(validation or {"kept_news": news_rows}, "local_fallback")
    try:
        _save_cache_to_db(fallback, metadata=metadata)
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

    validation = _validate_and_filter_topic_news(topic, news_rows)
    _raise_if_invalid_topic_news(validation)
    kept_news = validation["kept_news"]
    kept_news_ids = [int(row["id"]) for row in kept_news]

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
        if cached.get("timeline_json") and _cached_timeline_matches_news(cached, kept_news_ids):
            source = "cache"
            if cached.get("generate_status") == "mock":
                source = "mock"
            result = _timeline_row_to_result(cached, topic, source=source)
            # 运行时常态化旧缓存中的 event_title 为短标题（不改数据库）
            for node in result.timeline:
                node.event_title = build_short_event_title(
                    raw_title=normalize_text(node.source_title or node.event_title),
                    topic_name=normalize_text(topic.get("topic_name")),
                    core_entities=validation.get("core_entities"),
                    category_name=None,
                )
            return result

        logger.info(
            "Timeline 缓存与当前数据库新闻不一致，忽略旧缓存并重新生成：topic_id=%s",
            topic_id,
        )

    return await _generate_with_ai_or_fallback(topic, kept_news, validation=validation)


async def generate_timeline(topic_id: int, current_user: Optional[UserInfo] = None) -> TimelineGenerateResult:
    if current_user is None:
        raise AppException(code=401, message="未登录或登录状态已失效")

    topic = _get_topic(topic_id)
    if topic is None:
        raise AppException(code=404, message="话题不存在")

    news_rows = _get_topic_news(topic_id)[1]
    if len(news_rows) < 2:
        raise AppException(code=400, message="同一话题下至少需要 2 篇新闻才能生成事件脉络")

    validation = _validate_and_filter_topic_news(topic, news_rows)
    _raise_if_invalid_topic_news(validation)
    kept_news = validation["kept_news"]

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

    return await _generate_with_ai_or_fallback(topic, kept_news, validation=validation)


def auto_cluster_timeline_topics(request) -> dict[str, Any]:
    """后台批量自动聚类生成事件脉络话题。"""
    from app.modules.timeline.cluster_service import apply_auto_cluster_write

    if request.dry_run is False and request.confirm is not True:
        return {
            "success": False, "dry_run": False,
            "message": "正式发布自动话题需要 confirm=true，请先预览确认后再发布。",
        }

    result = apply_auto_cluster_write(
        days=request.days, max_news=request.max_news,
        use_llm_polish=request.use_llm_polish,
        max_write_topics=request.max_write_topics,
        dry_run=request.dry_run,
        confirmed_topics=getattr(request, "confirmed_topics", None),
    )

    if result.get("success"):
        manual_count = execute_one("SELECT COUNT(*) as c FROM news_topic WHERE source_type='manual' AND status=1")
        auto_active = execute_one("SELECT COUNT(*) as c FROM news_topic WHERE source_type='auto' AND status=1")
        result.update({
            "message": "预览完成，未写入数据库。" if request.dry_run else "自动话题已发布，用户端 /timeline 可查看。",
            "summary": {
                "manual_topic_count": int((manual_count or {}).get("c", 0)),
                "auto_active_count": int((auto_active or {}).get("c", 0)),
                "updated_news_count": result.get("updated_news_topic_id", 0),
                "timeline_count": result.get("written_timelines", 0),
            },
            "warnings": list(dict.fromkeys(
                result.get("warnings", [])
                + ["自动聚类结果可能存在偏差，建议管理员审核后再发布。", "当前未覆盖任何人工话题和人工绑定。"]
            )),
        })
    else:
        result["dry_run"] = request.dry_run
        result["message"] = result.get("message", "自动话题生成失败。")
    return result
