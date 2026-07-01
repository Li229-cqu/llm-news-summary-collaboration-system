"""个人中心模块服务层：数据库优先，mock 兜底。

当前阶段优先读取 MySQL 中的 browse_history、favorite、news_comment、
ai_generate_record 等表；当数据库不可用或尚未同步数据时，自动回退到
进程内 mock 数据，保证页面和演示流程可用。
"""

from __future__ import annotations

import hashlib
import json
import logging
import math
import re
from collections import Counter
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Union

import httpx

from app.common.utils import format_datetime as utils_format_datetime, normalize_text, paginate
from app.db.database import execute_one, execute_query, execute_update
from app.mock.ai_records import MOCK_AI_RECORDS
from app.mock.comments import MOCK_NEWS_COMMENTS
from app.mock.news import MOCK_BROWSE_HISTORY, MOCK_NEWS, MOCK_NEWS_FAVORITES, NEWS_CATEGORIES
from app.modules.profile.schema import (
    AiAnalysisResult,
    AIRecordItem,
    AnalysisTexts,
    PageAnalyses,
    BrowseHistoryItem,
    CommentRecordItem,
    DailyActivityItem,
    FavoriteItem,
    ProfileOverview,
    ProfileTestData,
    ReadingHeatmapCell,
    ReadingHeatmapResponse,
    ReadingHeatmapSummary,
    ReadingRecentNews,
    ReadingTimelineCategoryItem,
    ReadingTimelineDateItem,
    ReadingTimelineNewsItem,
    ReadingTimelineResponse,
    ReadingTimelineSummary,
    ReadingTimelineTopicItem,
    ReadingTopCategory,
    ReadingTopTopic,
    ReadingTrajectoryEdge,
    ReadingTrajectoryNode,
    ReadingTrajectoryResponse,
    ReadingTrajectorySummary,
    SubscriptionCategory,
    SubscriptionResponse,
    SubscriptionUpdateRequest,
    TopicRankItem,
    WeeklyReportHighlight,
    WeeklyReportOverview,
    WeeklyReportPersona,
    WeeklyReportRange,
    WeeklyReportResponse,
    WeeklyReportScores,
)

logger = logging.getLogger(__name__)


def _normalize_ai_record_source(value: Any) -> str:
    return str(value or "manual") if str(value or "manual") in {"manual", "news"} else "manual"


def _normalize_ai_risk_level(value: Any) -> str:
    return str(value or "low") if str(value or "low") in {"low", "medium", "high"} else "low"


def get_test_data() -> ProfileTestData:
    return ProfileTestData(module="profile", description="个人中心模块基础接口占位")


def _get_current_user_id(current_user: Optional[Any]) -> Optional[int]:
    if current_user is None:
        return None
    if isinstance(current_user, dict):
        return current_user.get("id")
    return getattr(current_user, "id", None)



def _parse_json_field(value: Any, default: Any = None) -> Any:
    if value is None:
        return [] if default is None else default
    if isinstance(value, (list, dict)):
        return value
    if isinstance(value, bytes):
        value = value.decode("utf-8", errors="ignore")
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return [] if default is None else default
        try:
            return json.loads(stripped)
        except json.JSONDecodeError:
            return [] if default is None else default
    return value


def parse_tags(value: Any) -> list[str]:
    """安全解析 tags 字段，始终返回 list[str]。"""

    if value is None:
        return []
    if isinstance(value, list):
        return [normalize_text(item) for item in value if normalize_text(item)]
    if isinstance(value, tuple):
        return [normalize_text(item) for item in list(value) if normalize_text(item)]
    if isinstance(value, dict):
        parsed_items = [normalize_text(item) for item in value.keys()]
        return [item for item in parsed_items if item]
    if isinstance(value, bytes):
        value = value.decode("utf-8", errors="ignore")
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return []
        try:
            parsed = json.loads(stripped)
        except json.JSONDecodeError:
            parsed = None

        if isinstance(parsed, list):
            return [normalize_text(item) for item in parsed if normalize_text(item)]
        if isinstance(parsed, dict):
            parsed_items = [normalize_text(item) for item in parsed.keys()]
            return [item for item in parsed_items if item]

        if "," in stripped:
            return [part for part in (normalize_text(item) for item in stripped.split(",")) if part]
        return [normalize_text(stripped)] if normalize_text(stripped) else []

    normalized = normalize_text(value)
    return [normalized] if normalized else []


def format_datetime(value: Any) -> str:
    """统一把数据库里的时间值转成字符串。"""

    if value is None:
        return ""
    if isinstance(value, bytes):
        value = value.decode("utf-8", errors="ignore")
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(value, date):
        return value.strftime("%Y-%m-%d")
    if isinstance(value, str):
        return value
    try:
        return utils_format_datetime(value)
    except Exception:  # noqa: BLE001
        return normalize_text(value)


def normalize_topic_name(record: Dict[str, Any]) -> str:
    """为阅读脉络兜底生成话题名称。"""

    topic_name = normalize_text(record.get("topic_name"))
    if topic_name:
        return topic_name

    tags = parse_tags(record.get("tags"))
    if tags:
        return tags[0]

    category_name = normalize_text(record.get("category_name"))
    if category_name:
        return category_name

    return "未分类话题"


def clamp_reading_params(days: int = 30, limit: int = 200) -> tuple[int, int]:
    """限制阅读脉络查询参数范围，避免一次性查询过多。"""

    try:
        days_value = int(days)
    except (TypeError, ValueError):
        days_value = 30

    try:
        limit_value = int(limit)
    except (TypeError, ValueError):
        limit_value = 200

    days_value = max(1, min(days_value, 365))
    limit_value = max(10, min(limit_value, 500))
    return days_value, limit_value


def get_user_reading_records(user_id: int, days: int = 30, limit: int = 200) -> list[dict]:
    """查询并整理用户最近的阅读记录（支持新闻和社区帖子）。"""

    if not user_id:
        return []

    safe_days, safe_limit = clamp_reading_params(days=days, limit=limit)
    try:
        rows = execute_query(
            """
            SELECT
                bh.id AS history_id,
                bh.user_id,
                bh.news_id,
                bh.target_type,
                bh.target_id,
                bh.browse_time,

                COALESCE(n.title, cp.title) AS title,
                COALESCE(n.summary, cp.content) AS summary,
                n.category_id,
                COALESCE(n.topic_id, cp.topic_id) AS topic_id,
                n.source,
                COALESCE(n.publish_time, cp.created_at) AS publish_time,
                COALESCE(n.tags, cp.tags) AS tags,
                COALESCE(n.view_count, cp.view_count) AS view_count,
                COALESCE(n.like_count, cp.like_count) AS like_count,
                COALESCE(n.comment_count, cp.comment_count) AS comment_count,
                COALESCE(n.favorite_count, cp.favorite_count) AS favorite_count,

                COALESCE(nc.name, '未分类') AS category_name,
                COALESCE(nc.code, '') AS category_code,

                COALESCE(nt.topic_name, '') AS topic_name,
                COALESCE(nt.summary, '') AS topic_summary
            FROM browse_history bh
            LEFT JOIN news n ON (bh.target_type = 'news' OR bh.target_type IS NULL OR bh.target_type = '') AND n.id = bh.news_id
            LEFT JOIN community_post cp ON bh.target_type = 'post' AND cp.id = bh.target_id
            LEFT JOIN news_category nc ON nc.id = n.category_id
            LEFT JOIN news_topic nt ON nt.id = COALESCE(n.topic_id, cp.topic_id)
            WHERE bh.user_id = %s
              AND bh.browse_time >= DATE_SUB(NOW(), INTERVAL %s DAY)
            ORDER BY bh.browse_time DESC, bh.id DESC
            LIMIT %s
            """,
            [int(user_id), safe_days, safe_limit],
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("读取用户阅读记录失败，返回空列表：%s", exc)
        return []

    if not rows:
        return []

    reading_records: list[dict] = []
    for row in rows:
        target_type = row.get("target_type") or "news"
        topic_id = row.get("topic_id")
        if target_type == "post" and topic_id is None:
            topic_id = row.get("cp_topic_id")
        item = {
            "history_id": int(row.get("history_id") or 0),
            "user_id": int(row.get("user_id") or 0),
            "news_id": int(row.get("news_id") or 0),
            "target_type": target_type,
            "target_id": int(row.get("target_id") or 0),
            "title": normalize_text(row.get("title")),
            "summary": normalize_text(row.get("summary")),
            "category_id": row.get("category_id"),
            "category_name": normalize_text(row.get("category_name")) or "未分类",
            "category_code": normalize_text(row.get("category_code")),
            "topic_id": topic_id,
            "topic_name": normalize_topic_name(
                {
                    "topic_name": row.get("topic_name"),
                    "tags": row.get("tags"),
                    "category_name": row.get("category_name"),
                }
            ),
            "topic_summary": normalize_text(row.get("topic_summary")),
            "source": normalize_text(row.get("source")) if target_type == "news" else "社区",
            "publish_time": format_datetime(row.get("publish_time")),
            "browse_time": format_datetime(row.get("browse_time")),
            "tags": parse_tags(row.get("tags")),
            "view_count": int(row.get("view_count") or 0),
            "like_count": int(row.get("like_count") or 0),
            "comment_count": int(row.get("comment_count") or 0),
            "favorite_count": int(row.get("favorite_count") or 0),
        }
        reading_records.append(item)

    return reading_records


def _safe_topic_slug(topic_name: str) -> str:
    normalized = normalize_text(topic_name)
    if not normalized:
        return "unknown"
    slug = re.sub(r"[^\w\u4e00-\u9fff]+", "_", normalized, flags=re.UNICODE)
    slug = re.sub(r"_+", "_", slug).strip("_")
    return slug or "unknown"


def get_reading_trajectory(user_id: int, days: int = 30, limit: int = 200) -> dict:
    """构建阅读脉络图所需的数据结构。"""

    safe_days, safe_limit = clamp_reading_params(days=days, limit=limit)
    records = get_user_reading_records(user_id, days=safe_days, limit=safe_limit)

    if not records:
        return ReadingTrajectoryResponse(
            summary=ReadingTrajectorySummary(
                total_reads=0,
                unique_news_count=0,
                category_count=0,
                topic_count=0,
                top_category="",
                top_topic="",
                date_range=f"最近{safe_days}天",
            )
        ).dict()

    category_counter: Counter[tuple[Any, str]] = Counter()
    topic_counter: Counter[tuple[Any, str]] = Counter()
    news_counter: Counter[int] = Counter()
    category_news_map: dict[tuple[Any, str], set[tuple[Any, str]]] = {}
    topic_news_map: dict[str, set[int]] = {}
    category_nodes: dict[str, ReadingTrajectoryNode] = {}
    topic_nodes: dict[str, ReadingTrajectoryNode] = {}
    news_nodes: dict[str, ReadingTrajectoryNode] = {}
    category_topic_edges: Counter[tuple[str, str]] = Counter()
    topic_news_edges: Counter[tuple[str, str]] = Counter()
    sequence_edges: Counter[tuple[str, str]] = Counter()
    recent_news_items: list[ReadingRecentNews] = []
    seen_recent_news: set[int] = set()
    previous_news_node_id: Optional[str] = None

    for record in records:
        category_id = record.get("category_id")
        category_name = normalize_text(record.get("category_name")) or "未分类"
        category_key = (category_id, category_name)
        category_counter[category_key] += 1
        category_news_map.setdefault(category_key, set()).add((record.get("news_id"), normalize_text(record.get("title"))))

        category_node_id = f"category_{category_id}" if category_id not in (None, "", 0) else "category_unknown"
        if category_node_id not in category_nodes:
            category_nodes[category_node_id] = ReadingTrajectoryNode(
                id=category_node_id,
                name=category_name,
                type="category",
                category_id=int(category_id) if category_id not in (None, "", 0) else None,
                category_name=category_name,
            )
        category_nodes[category_node_id].read_count += 1
        category_nodes[category_node_id].value += 1

        topic_id = record.get("topic_id")
        topic_name = normalize_topic_name(record)
        topic_node_id = (
            f"topic_{topic_id}"
            if topic_id not in (None, "", 0)
            else f"topic_virtual_{_safe_topic_slug(topic_name)}"
        )
        topic_counter[(topic_id, topic_name)] += 1
        topic_news_map.setdefault(topic_node_id, set()).add(int(record.get("news_id") or 0))
        if topic_node_id not in topic_nodes:
            topic_nodes[topic_node_id] = ReadingTrajectoryNode(
                id=topic_node_id,
                name=topic_name,
                type="topic",
                topic_id=int(topic_id) if topic_id not in (None, "", 0) else None,
                topic_name=topic_name,
            )
        topic_nodes[topic_node_id].read_count += 1
        topic_nodes[topic_node_id].value += 1

        news_id = int(record.get("news_id") or 0)
        news_node_id = f"news_{news_id}"
        news_counter[news_id] += 1
        if news_node_id not in news_nodes:
            news_nodes[news_node_id] = ReadingTrajectoryNode(
                id=news_node_id,
                name=normalize_text(record.get("title")),
                type="news",
                news_id=news_id,
                category_id=int(category_id) if category_id not in (None, "", 0) else None,
                topic_id=int(topic_id) if topic_id not in (None, "", 0) else None,
                category_name=category_name,
                topic_name=topic_name,
                browse_time=format_datetime(record.get("browse_time")),
            )
        else:
            current_time = format_datetime(record.get("browse_time"))
            if current_time > news_nodes[news_node_id].browse_time:
                news_nodes[news_node_id].browse_time = current_time

        news_nodes[news_node_id].read_count += 1
        news_nodes[news_node_id].value += 1

        category_topic_edges[(category_node_id, topic_node_id)] += 1
        topic_news_edges[(topic_node_id, news_node_id)] += 1

        if previous_news_node_id and previous_news_node_id != news_node_id:
            sequence_edges[(previous_news_node_id, news_node_id)] += 1
        previous_news_node_id = news_node_id

        if news_id not in seen_recent_news:
            seen_recent_news.add(news_id)
            recent_news_items.append(
                ReadingRecentNews(
                    news_id=news_id,
                    title=normalize_text(record.get("title")),
                    category_name=category_name,
                    topic_name=topic_name,
                    browse_time=format_datetime(record.get("browse_time")),
                )
            )

    summary = ReadingTrajectorySummary(
        total_reads=len(records),
        unique_news_count=len({int(record.get("news_id") or 0) for record in records if record.get("news_id")}),
        category_count=len(category_counter),
        topic_count=len(topic_counter),
        top_category=max(category_counter.items(), key=lambda item: (item[1], str(item[0][1])))[0][1]
        if category_counter
        else "",
        top_topic=max(topic_counter.items(), key=lambda item: (item[1], str(item[0][1])))[0][1]
        if topic_counter
        else "",
        date_range=f"最近{safe_days}天",
    )

    top_categories = [
        ReadingTopCategory(
            category_id=int(category_id) if category_id not in (None, "", 0) else None,
            category_name=category_name,
            read_count=count,
        )
        for (category_id, category_name), count in sorted(
            category_counter.items(), key=lambda item: (-item[1], str(item[0][1]))
        )[:5]
    ]

    top_topics = [
        ReadingTopTopic(
            topic_id=int(topic_id) if topic_id not in (None, "", 0) else None,
            topic_name=topic_name,
            read_count=count,
        )
        for (topic_id, topic_name), count in sorted(
            topic_counter.items(), key=lambda item: (-item[1], str(item[0][1]))
        )[:5]
    ]

    nodes = list(category_nodes.values()) + list(topic_nodes.values()) + list(news_nodes.values())
    edges = [
        ReadingTrajectoryEdge(source=source, target=target, value=value, type="category_topic")
        for (source, target), value in category_topic_edges.items()
    ]
    edges.extend(
        ReadingTrajectoryEdge(source=source, target=target, value=value, type="topic_news")
        for (source, target), value in topic_news_edges.items()
    )
    edges.extend(
        ReadingTrajectoryEdge(source=source, target=target, value=value, type="sequence")
        for (source, target), value in sequence_edges.items()
    )

    recent_news = recent_news_items[:10]

    return ReadingTrajectoryResponse(
        summary=summary,
        nodes=nodes,
        edges=edges,
        top_categories=top_categories,
        top_topics=top_topics,
        recent_news=recent_news,
    ).dict()




def get_reading_timeline(user_id: int, days: int = 30, group_by: str = "day") -> dict:
    """构建阅读时间线所需的数据结构。"""

    safe_days, safe_limit = clamp_reading_params(days=days, limit=500)
    if normalize_text(group_by).lower() != "day":
        group_by = "day"

    records = get_user_reading_records(user_id, days=safe_days, limit=safe_limit)
    if not records:
        return ReadingTimelineResponse(
            summary=ReadingTimelineSummary(
                total_days=0,
                total_reads=0,
                most_active_date="",
                most_active_category="",
            ),
            items=[],
        ).dict()

    grouped_records: dict[str, list[dict]] = {}
    date_counter: Counter[str] = Counter()
    category_counter: Counter[tuple[Any, str]] = Counter()

    for record in records:
        browse_time = normalize_text(record.get("browse_time"))
        read_date = browse_time[:10] if len(browse_time) >= 10 else browse_time
        if not read_date:
            continue

        grouped_records.setdefault(read_date, []).append(record)
        date_counter[read_date] += 1

        category_id = record.get("category_id")
        category_name = normalize_text(record.get("category_name")) or "未分类"
        category_counter[(category_id, category_name)] += 1

    if not grouped_records:
        return ReadingTimelineResponse(
            summary=ReadingTimelineSummary(
                total_days=0,
                total_reads=0,
                most_active_date="",
                most_active_category="",
            ),
            items=[],
        ).dict()

    items: list[ReadingTimelineDateItem] = []
    for read_date in sorted(grouped_records.keys(), reverse=True):
        day_records = grouped_records[read_date]
        day_category_counter: Counter[tuple[Any, str]] = Counter()
        day_topic_counter: Counter[tuple[Any, str]] = Counter()
        day_news_items: list[ReadingTimelineNewsItem] = []

        for record in day_records:
            category_id = record.get("category_id")
            category_name = normalize_text(record.get("category_name")) or "未分类"
            day_category_counter[(category_id, category_name)] += 1

            topic_id = record.get("topic_id")
            topic_name = normalize_topic_name(record)
            day_topic_counter[(topic_id, topic_name)] += 1

            day_news_items.append(
                ReadingTimelineNewsItem(
                    news_id=int(record.get("news_id") or 0),
                    title=normalize_text(record.get("title")),
                    category_name=category_name,
                    topic_name=topic_name,
                    browse_time=normalize_text(record.get("browse_time")),
                )
            )

        categories = [
            ReadingTimelineCategoryItem(
                category_id=int(category_id) if category_id not in (None, "", 0) else None,
                category_name=category_name if category_name else "未分类",
                read_count=count,
            )
            for (category_id, category_name), count in sorted(
                day_category_counter.items(), key=lambda item: (-item[1], str(item[0][1]))
            )
        ]

        topics = [
            ReadingTimelineTopicItem(
                topic_id=int(topic_id) if topic_id not in (None, "", 0) else None,
                topic_name=topic_name,
                read_count=count,
            )
            for (topic_id, topic_name), count in sorted(
                day_topic_counter.items(), key=lambda item: (-item[1], str(item[0][1]))
            )
        ]

        items.append(
            ReadingTimelineDateItem(
                date=read_date,
                total_reads=len(day_records),
                categories=categories,
                topics=topics,
                news=day_news_items,
            )
        )

    most_active_date = max(date_counter.items(), key=lambda item: (item[1], item[0]))[0]
    most_active_category = (
        sorted(category_counter.items(), key=lambda item: (-item[1], str(item[0][1])))[0][0][1]
        if category_counter
        else ""
    )

    summary = ReadingTimelineSummary(
        total_days=len(grouped_records),
        total_reads=len(records),
        most_active_date=most_active_date,
        most_active_category=most_active_category,
    )

    return ReadingTimelineResponse(summary=summary, items=items).dict()


def get_reading_heatmap(user_id: int, days: int = 30, dimension: str = "category") -> dict:
    """构建阅读热力图所需的数据结构。"""

    safe_days, _ = clamp_reading_params(days=days, limit=500)
    if normalize_text(dimension).lower() != "category":
        dimension = "category"

    records = get_user_reading_records(user_id, days=safe_days, limit=500)
    if not records:
        return ReadingHeatmapResponse(
            x_axis=[],
            y_axis=[],
            cells=[],
            summary=ReadingHeatmapSummary(
                max_value=0,
                most_active_category="",
                most_active_date="",
            ),
        ).dict()

    date_counter: dict[str, Counter[str]] = {}
    category_counter: Counter[str] = Counter()
    all_dates: set[str] = set()
    all_categories: set[str] = set()

    for record in records:
        browse_time = normalize_text(record.get("browse_time"))
        read_date = browse_time[:10] if len(browse_time) >= 10 else browse_time
        if not read_date:
            continue

        category_name = normalize_text(record.get("category_name")) or "未分类"
        all_dates.add(read_date)
        all_categories.add(category_name)
        category_counter[category_name] += 1
        date_counter.setdefault(read_date, Counter())[category_name] += 1

    if not all_dates or not all_categories:
        return ReadingHeatmapResponse(
            x_axis=[],
            y_axis=[],
            cells=[],
            summary=ReadingHeatmapSummary(
                max_value=0,
                most_active_category="",
                most_active_date="",
            ),
        ).dict()

    x_axis = sorted(all_dates)
    y_axis = [
        item[0]
        for item in sorted(category_counter.items(), key=lambda item: (-item[1], item[0]))
    ]

    cells: list[ReadingHeatmapCell] = []
    max_value = 0
    for read_date in x_axis:
        category_map = date_counter.get(read_date, Counter())
        for category_name in y_axis:
            value = int(category_map.get(category_name, 0))
            if value <= 0:
                continue
            max_value = max(max_value, value)
            cells.append(
                ReadingHeatmapCell(
                    x=read_date,
                    y=category_name,
                    value=value,
                    news_count=value,
                )
            )

    most_active_date = ""
    most_active_category = ""
    if cells:
        date_totals = Counter()
        for cell in cells:
            date_totals[cell.x] += cell.value
        most_active_date = max(date_totals.items(), key=lambda item: (item[1], item[0]))[0]
        most_active_category = (
            sorted(category_counter.items(), key=lambda item: (-item[1], item[0]))[0][0]
            if category_counter
            else ""
        )

    return ReadingHeatmapResponse(
        x_axis=x_axis,
        y_axis=y_axis,
        cells=cells,
        summary=ReadingHeatmapSummary(
            max_value=max_value,
            most_active_category=most_active_category,
            most_active_date=most_active_date,
        ),
    ).dict()


def _mock_profile_overview(current_user: Optional[Any] = None) -> ProfileOverview:
    user_id = _get_current_user_id(current_user)
    if user_id is None:
        return ProfileOverview(
            user_id=0,
            browse_count=0,
            favorite_count=0,
            comment_count=0,
            ai_generate_count=0,
        )

    browse_count = sum(1 for item in MOCK_BROWSE_HISTORY if item["user_id"] == user_id)
    favorite_count = sum(1 for item in MOCK_NEWS_FAVORITES if item["user_id"] == user_id)
    comment_count = sum(1 for item in MOCK_NEWS_COMMENTS if item["user_id"] == user_id)
    ai_generate_count = sum(1 for item in MOCK_AI_RECORDS if item.get("user_id", 1) == user_id)

    return ProfileOverview(
        user_id=user_id,
        browse_count=browse_count,
        favorite_count=favorite_count,
        comment_count=comment_count,
        ai_generate_count=ai_generate_count,
    )


def _db_profile_overview(current_user: Optional[Any] = None) -> ProfileOverview | None:
    user_id = _get_current_user_id(current_user)
    if user_id is None:
        return ProfileOverview(
            user_id=0,
            browse_count=0,
            favorite_count=0,
            comment_count=0,
            ai_generate_count=0,
        )

    # 浏览数：去重新闻浏览内容数 + 去重帖子浏览内容数
    # 与浏览记录 Tab 的新闻列表 total + 帖子列表 total 口径一致
    # 新闻：按 news_id 去重，兼容旧数据（target_type 为空或 NULL 视为 news）
    news_browse_row = execute_one(
        """
        SELECT COUNT(DISTINCT news_id) AS total
        FROM browse_history
        WHERE user_id = %s
          AND news_id > 0
          AND (target_type = 'news' OR target_type IS NULL OR target_type = '')
        """,
        [user_id],
    )
    # 帖子：按 target_id 去重
    post_browse_row = execute_one(
        """
        SELECT COUNT(DISTINCT target_id) AS total
        FROM browse_history
        WHERE user_id = %s
          AND target_type = 'post'
          AND target_id IS NOT NULL
        """,
        [user_id],
    )
    browse_count = (
        int((news_browse_row or {}).get("total") or 0) +
        int((post_browse_row or {}).get("total") or 0)
    )

    # 收藏数：有效新闻收藏 + 有效帖子收藏
    # 与收藏列表 Tab 口径一致：仅统计 target status = 1 的目标
    news_fav_row = execute_one(
        """
        SELECT COUNT(*) AS total
        FROM favorite f
        INNER JOIN news n ON n.id = f.target_id AND n.status = 1
        WHERE f.user_id = %s AND f.target_type = 'news'
        """,
        [user_id],
    )
    post_fav_row = execute_one(
        """
        SELECT COUNT(*) AS total
        FROM favorite f
        INNER JOIN community_post p ON p.id = f.target_id AND p.status = 1
        WHERE f.user_id = %s AND f.target_type = 'post'
        """,
        [user_id],
    )
    favorite_count = (
        int((news_fav_row or {}).get("total") or 0) +
        int((post_fav_row or {}).get("total") or 0)
    )

    # 评论数：新闻评论 + 帖子评论（均排除已删除 status = 4）
    news_comment_row = execute_one(
        """
        SELECT COUNT(*) AS total
        FROM news_comment
        WHERE user_id = %s AND status <> 4
        """,
        [user_id],
    )
    post_comment_row = execute_one(
        """
        SELECT COUNT(*) AS total
        FROM post_comment
        WHERE user_id = %s AND status <> 4
        """,
        [user_id],
    )
    comment_count = (
        int((news_comment_row or {}).get("total") or 0) +
        int((post_comment_row or {}).get("total") or 0)
    )

    # AI 生成数：统计有效 AI 生成记录
    ai_row = execute_one(
        """
        SELECT COUNT(*) AS total
        FROM ai_generate_record
        WHERE user_id = %s AND status = 1
        """,
        [user_id],
    )

    counts = [
        browse_count,
        favorite_count,
        comment_count,
        int((ai_row or {}).get("total") or 0),
    ]
    # 全部为 0 时也返回合法结果（让前端正常显示 0，不触发 mock fallback）
    if not any(counts):
        return ProfileOverview(
            user_id=user_id,
            browse_count=0,
            favorite_count=0,
            comment_count=0,
            ai_generate_count=0,
        )

    return ProfileOverview(
        user_id=user_id,
        browse_count=counts[0],
        favorite_count=counts[1],
        comment_count=counts[2],
        ai_generate_count=counts[3],
    )


def get_profile_overview(current_user: Optional[Any] = None) -> ProfileOverview:
    """获取个人中心概览数据。"""

    try:
        result = _db_profile_overview(current_user)
        if result is not None:
            return result
    except Exception as exc:  # noqa: BLE001
        logger.warning("读取个人中心概览失败，回退 mock：%s", exc)
    return _mock_profile_overview(current_user)


def _mock_browse_history(
    current_user: Optional[Any] = None,
    page: int = 1,
    page_size: int = 10,
    browse_type: str = "news",
) -> Dict[str, Any]:
    user_id = _get_current_user_id(current_user)
    if user_id is None:
        return paginate([], page=page, page_size=page_size)

    # 帖子浏览暂无 mock 数据，返回空列表
    if browse_type == "post":
        return paginate([], page=page, page_size=page_size)

    user_history = [item for item in MOCK_BROWSE_HISTORY if item["user_id"] == user_id]
    user_history.sort(key=lambda x: x["browse_time"], reverse=True)

    news_map = {news["id"]: news for news in MOCK_NEWS}
    history_items = []
    for record in user_history:
        news = news_map.get(record["news_id"])
        if news:
            history_items.append(
                BrowseHistoryItem(
                    news_id=news["id"],
                    title=news["title"],
                    category_name=news["category_name"],
                    browse_time=record["browse_time"],
                ).dict()
            )

    return paginate(history_items, page=page, page_size=page_size)


def _db_browse_history(
    current_user: Optional[Any] = None,
    page: int = 1,
    page_size: int = 10,
) -> Dict[str, Any] | None:
    user_id = _get_current_user_id(current_user)
    if user_id is None:
        return paginate([], page=page, page_size=page_size)

    # 子查询按 news_id 去重，取最新 browse_time
    rows = execute_query(
        """
        SELECT
            bh.news_id,
            n.title,
            COALESCE(nc.name, '未分类') AS category_name,
            bh.browse_time
        FROM (
            SELECT news_id, MAX(browse_time) AS browse_time
            FROM browse_history
            WHERE user_id = %s
              AND news_id > 0
              AND (target_type = 'news' OR target_type IS NULL OR target_type = '')
            GROUP BY news_id
        ) bh
        LEFT JOIN news n ON n.id = bh.news_id
        LEFT JOIN news_category nc ON nc.id = n.category_id
        ORDER BY bh.browse_time DESC
        """,
        [user_id],
    )
    if not rows:
        # 用户没有新闻浏览记录，返回空列表（不是 None，避免触发 mock fallback）
        return paginate([], page=page, page_size=page_size)

    history_items = []
    for row in rows:
        history_items.append(
            BrowseHistoryItem(
                news_id=int(row["news_id"]),
                title=normalize_text(row["title"]),
                category_name=normalize_text(row["category_name"]),
                browse_time=format_datetime(row["browse_time"]),
                type="news",
            ).dict()
        )

    return paginate(history_items, page=page, page_size=page_size)


def _db_post_browse_history(
    current_user: Optional[Any] = None,
    page: int = 1,
    page_size: int = 10,
) -> Dict[str, Any] | None:
    """查询用户社区帖子浏览历史。"""
    user_id = _get_current_user_id(current_user)
    if user_id is None:
        return paginate([], page=page, page_size=page_size)

    # 子查询按 target_id 去重，取最新 browse_time
    rows = execute_query(
        """
        SELECT
            cp.id AS post_id,
            cp.title,
            LEFT(cp.content, 80) AS summary,
            COALESCE(JSON_UNQUOTE(JSON_EXTRACT(cp.tags, '$[0]')), '社区帖子') AS category_name,
            bh.browse_time
        FROM (
            SELECT target_id, MAX(browse_time) AS browse_time
            FROM browse_history
            WHERE user_id = %s
              AND target_type = 'post'
              AND target_id IS NOT NULL
            GROUP BY target_id
        ) bh
        LEFT JOIN community_post cp ON cp.id = bh.target_id
        ORDER BY bh.browse_time DESC
        """,
        [user_id],
    )
    if not rows:
        # 用户没有帖子浏览记录，返回空列表（不是 None，避免触发 mock fallback）
        return paginate([], page=page, page_size=page_size)

    history_items = []
    for row in rows:
        history_items.append(
            BrowseHistoryItem(
                news_id=int(row["post_id"]),
                title=normalize_text(row["title"]),
                category_name=normalize_text(row["category_name"]) or "帖子浏览",
                browse_time=format_datetime(row["browse_time"]),
                type="post",
                target_id=int(row["post_id"]),
                target_title=normalize_text(row["title"]),
            ).dict()
        )

    return paginate(history_items, page=page, page_size=page_size)


def get_browse_history(
    current_user: Optional[Any] = None,
    page: int = 1,
    page_size: int = 10,
    browse_type: str = "news",
) -> Dict[str, Any]:
    """获取用户浏览历史，支持 type=news 或 type=post。"""

    try:
        if browse_type == "post":
            result = _db_post_browse_history(current_user, page=page, page_size=page_size)
        else:
            result = _db_browse_history(current_user, page=page, page_size=page_size)
        if result is not None:
            return result
    except Exception as exc:  # noqa: BLE001
        logger.warning("读取浏览历史失败，回退 mock：%s", exc)
    return _mock_browse_history(current_user, page=page, page_size=page_size, browse_type=browse_type)


def _mock_favorites(
    current_user: Optional[Any] = None, page: int = 1, page_size: int = 10
) -> Dict[str, Any]:
    user_id = _get_current_user_id(current_user)
    if user_id is None:
        return paginate([], page=page, page_size=page_size)

    user_favorites = [item for item in MOCK_NEWS_FAVORITES if item["user_id"] == user_id]
    news_map = {news["id"]: news for news in MOCK_NEWS}

    favorite_items = []
    for record in user_favorites:
        news = news_map.get(record["news_id"])
        if news:
            favorite_items.append(
                FavoriteItem(
                    news_id=news["id"],
                    title=news["title"],
                    summary=news["summary"],
                    category_name=news["category_name"],
                    source=news["source"],
                    publish_time=news["publish_time"],
                    favorited_at=format_datetime(record.get("favorited_at") or record.get("create_time")),
                ).dict()
            )

    favorite_items.sort(key=lambda x: x.get("favorited_at") or x["publish_time"], reverse=True)
    return paginate(favorite_items, page=page, page_size=page_size)


def _db_favorites(
    current_user: Optional[Any] = None, page: int = 1, page_size: int = 10,
    target_type: str = "news",
) -> Dict[str, Any] | None:
    user_id = _get_current_user_id(current_user)
    if user_id is None:
        return paginate([], page=page, page_size=page_size)

    if target_type not in ("news", "post"):
        return paginate([], page=page, page_size=page_size)

    if target_type == "post":
        rows = execute_query(
            """
            SELECT
                p.id AS post_id,
                p.title,
                LEFT(p.content, 80) AS summary,
                '' AS category_name,
                '社区帖子' AS source,
                COALESCE(p.created_at, p.create_time) AS publish_time,
                COALESCE(f.created_at, f.create_time) AS favorited_at
            FROM favorite f
            LEFT JOIN community_post p ON p.id = f.target_id
            WHERE f.user_id = %s
              AND f.target_type = 'post'
              AND p.status = 1
            ORDER BY favorited_at DESC, f.id DESC
            """,
            [user_id],
        )
        if not rows:
            # 用户没有帖子收藏，返回空列表（不是 None，避免触发 mock fallback）
            return paginate([], page=page, page_size=page_size)

        favorite_items = []
        for row in rows:
            favorite_items.append(
                FavoriteItem(
                    news_id=int(row["post_id"]),
                    title=normalize_text(row["title"]),
                    summary=normalize_text(row["summary"]),
                    category_name=normalize_text(row["category_name"]),
                    source=normalize_text(row["source"]) or "社区帖子",
                    publish_time=format_datetime(row["publish_time"]),
                    favorited_at=format_datetime(row.get("favorited_at")),
                    target_type="post",
                ).dict()
            )

        return paginate(favorite_items, page=page, page_size=page_size)

    # target_type = 'news'
    rows = execute_query(
        """
        SELECT
            n.id AS news_id,
            n.title,
            n.summary,
            COALESCE(nc.name, '未分类') AS category_name,
            n.source,
            n.publish_time,
            COALESCE(f.created_at, f.create_time) AS favorited_at
        FROM favorite f
        LEFT JOIN news n ON n.id = f.target_id
        LEFT JOIN news_category nc ON nc.id = n.category_id
        WHERE f.user_id = %s
          AND f.target_type = 'news'
          AND n.status = 1
        ORDER BY favorited_at DESC, f.id DESC
        """,
        [user_id],
    )
    if not rows:
        # 用户没有新闻收藏，返回空列表（不是 None，避免触发 mock fallback）
        return paginate([], page=page, page_size=page_size)

    favorite_items = []
    for row in rows:
        favorite_items.append(
            FavoriteItem(
                news_id=int(row["news_id"]),
                title=normalize_text(row["title"]),
                summary=normalize_text(row["summary"]),
                category_name=normalize_text(row["category_name"]),
                source=normalize_text(row["source"]),
                publish_time=format_datetime(row["publish_time"]),
                favorited_at=format_datetime(row.get("favorited_at")),
                target_type="news",
            ).dict()
        )

    return paginate(favorite_items, page=page, page_size=page_size)


def get_favorites(
    current_user: Optional[Any] = None, page: int = 1, page_size: int = 10,
    target_type: str = "news",
) -> Dict[str, Any]:
    """获取用户收藏列表，支持 target_type=news 或 post。"""

    try:
        result = _db_favorites(current_user, page=page, page_size=page_size, target_type=target_type)
        if result is not None:
            return result
    except Exception as exc:  # noqa: BLE001
        logger.warning("读取收藏列表失败，回退 mock：%s", exc)
    if target_type != "news":
        return paginate([], page=page, page_size=page_size)
    return _mock_favorites(current_user, page=page, page_size=page_size)


def _mock_comments(
    current_user: Optional[Any] = None,
    page: int = 1,
    page_size: int = 10,
    comment_type: str = "news",
) -> Dict[str, Any]:
    user_id = _get_current_user_id(current_user)
    if user_id is None:
        return paginate([], page=page, page_size=page_size)

    # 帖子评论暂无 mock 数据，返回空列表
    if comment_type == "post":
        return paginate([], page=page, page_size=page_size)

    user_comments = [
        item for item in MOCK_NEWS_COMMENTS if item["user_id"] == user_id and item["status"] != 4
    ]
    user_comments.sort(key=lambda x: x["create_time"], reverse=True)
    news_map = {news["id"]: news for news in MOCK_NEWS}

    comment_items = []
    for record in user_comments:
        news = news_map.get(record["news_id"])
        if news:
            comment_items.append(
                CommentRecordItem(
                    comment_id=record["id"],
                    news_id=news["id"],
                    news_title=news["title"],
                    category_name=news["category_name"],
                    content=record["content"],
                    like_count=record["like_count"],
                    status=record["status"],
                    create_time=record["create_time"],
                ).dict()
            )

    return paginate(comment_items, page=page, page_size=page_size)


def _db_comments(
    current_user: Optional[Any] = None,
    page: int = 1,
    page_size: int = 10,
) -> Dict[str, Any] | None:
    user_id = _get_current_user_id(current_user)
    if user_id is None:
        return paginate([], page=page, page_size=page_size)

    rows = execute_query(
        """
        SELECT
            c.id AS comment_id,
            c.news_id,
            n.title AS news_title,
            COALESCE(nc.name, '未分类') AS category_name,
            c.content,
            c.like_count,
            c.status,
            c.created_at AS create_time
        FROM news_comment c
        LEFT JOIN news n ON n.id = c.news_id
        LEFT JOIN news_category nc ON nc.id = n.category_id
        WHERE c.user_id = %s AND c.status <> 4
        ORDER BY c.created_at DESC, c.id DESC
        """,
        [user_id],
    )
    if not rows:
        # 用户没有新闻评论记录，返回空列表（不是 None，避免触发 mock fallback）
        return paginate([], page=page, page_size=page_size)

    comment_items = []
    for row in rows:
        comment_items.append(
            CommentRecordItem(
                comment_id=int(row["comment_id"]),
                news_id=int(row["news_id"]),
                news_title=normalize_text(row["news_title"]),
                category_name=normalize_text(row["category_name"]),
                content=normalize_text(row["content"]),
                like_count=int(row["like_count"] or 0),
                status=int(row["status"] or 0),
                create_time=format_datetime(row["create_time"]),
            ).dict()
        )

    return paginate(comment_items, page=page, page_size=page_size)


def _db_post_comments(
    current_user: Optional[Any] = None,
    page: int = 1,
    page_size: int = 10,
) -> Dict[str, Any] | None:
    """查询用户在社区帖子中的评论记录。"""
    user_id = _get_current_user_id(current_user)
    if user_id is None:
        return paginate([], page=page, page_size=page_size)

    rows = execute_query(
        """
        SELECT
            pc.id AS comment_id,
            pc.post_id,
            cp.title AS post_title,
            pc.content,
            pc.like_count,
            pc.status,
            pc.created_at AS create_time
        FROM post_comment pc
        LEFT JOIN community_post cp ON cp.id = pc.post_id
        WHERE pc.user_id = %s AND pc.status <> 4
        ORDER BY pc.created_at DESC, pc.id DESC
        """,
        [user_id],
    )
    if not rows:
        # 用户没有帖子评论记录，返回空列表（不是 None，避免触发 mock fallback）
        return paginate([], page=page, page_size=page_size)

    comment_items = []
    for row in rows:
        comment_items.append(
            CommentRecordItem(
                comment_id=int(row["comment_id"]),
                news_id=0,
                news_title="",
                category_name="帖子评论",
                content=normalize_text(row["content"]),
                like_count=int(row["like_count"] or 0),
                status=int(row["status"] or 0),
                create_time=format_datetime(row["create_time"]),
                type="post",
                target_id=int(row["post_id"]),
                target_title=normalize_text(row["post_title"]),
            ).dict()
        )

    return paginate(comment_items, page=page, page_size=page_size)


def get_comments(
    current_user: Optional[Any] = None,
    page: int = 1,
    page_size: int = 10,
    comment_type: str = "news",
) -> Dict[str, Any]:
    """获取用户评论记录，支持 type=news 或 type=post。"""

    try:
        if comment_type == "post":
            result = _db_post_comments(current_user, page=page, page_size=page_size)
        else:
            result = _db_comments(current_user, page=page, page_size=page_size)
        if result is not None:
            return result
    except Exception as exc:  # noqa: BLE001
        logger.warning("读取评论记录失败，回退 mock：%s", exc)
    return _mock_comments(current_user, page=page, page_size=page_size, comment_type=comment_type)


def _mock_ai_records(
    current_user: Optional[Any] = None, page: int = 1, page_size: int = 10
) -> Dict[str, Any]:
    user_id = _get_current_user_id(current_user)
    if user_id is None:
        return paginate([], page=page, page_size=page_size)

    user_records = [item for item in MOCK_AI_RECORDS if item.get("user_id", 1) == user_id]
    user_records.sort(key=lambda x: x.get("id", 0), reverse=True)

    record_items = []
    for record in user_records:
        result = record.get("result", record)
        record_items.append(
            AIRecordItem(
                id=record["id"],
                source=_normalize_ai_record_source(record.get("source")),
                source_news_id=record.get("source_news_id"),
                source_title=record.get("source_title", ""),
                input_text=record["input_text"],
                candidate_titles=result.get("candidate_titles", []),
                summary_short=result.get("summary_short", ""),
                summary_long=result.get("summary_long"),
                risk_level=_normalize_ai_risk_level(record.get("risk_level", result.get("consistency", {}).get("risk_level", "low"))),
                create_time=record.get("create_time") or record.get("created_at"),
            ).dict()
        )

    return paginate(record_items, page=page, page_size=page_size)


def _db_ai_records(
    current_user: Optional[Any] = None, page: int = 1, page_size: int = 10
) -> Dict[str, Any] | None:
    user_id = _get_current_user_id(current_user)
    if user_id is None:
        return paginate([], page=page, page_size=page_size)

    rows = execute_query(
        """
        SELECT
            id,
            source,
            source_news_id,
            source_title,
            input_text,
            title_count,
            candidate_titles,
            summary_short,
            summary_long,
            summary_points,
            keywords,
            news_elements,
            risk_level,
            check_result,
            created_at,
            user_id
        FROM ai_generate_record
        WHERE user_id = %s AND status = 1
        ORDER BY id DESC
        """,
        [user_id],
    )
    if not rows:
        # 用户没有 AI 生成记录，返回空列表（不是 None，避免触发 mock fallback）
        return paginate([], page=page, page_size=page_size)

    record_items = []
    for row in rows:
        record_items.append(
            AIRecordItem(
                id=int(row["id"]),
                source=_normalize_ai_record_source(normalize_text(row.get("source"))),
                source_news_id=row.get("source_news_id"),
                source_title=normalize_text(row.get("source_title")),
                input_text=normalize_text(row["input_text"]),
                title_count=int(row.get("title_count") or 3),
                candidate_titles=_parse_json_field(row.get("candidate_titles"), default=[]),
                summary_short=normalize_text(row.get("summary_short")),
                summary_long=normalize_text(row.get("summary_long")) or None,
                risk_level=_normalize_ai_risk_level(normalize_text(row.get("risk_level"))),
                create_time=format_datetime(row.get("created_at")),
            ).dict()
        )

    return paginate(record_items, page=page, page_size=page_size)


def get_ai_records(
    current_user: Optional[Any] = None, page: int = 1, page_size: int = 10
) -> Dict[str, Any]:
    """获取用户 AI 生成记录。"""

    try:
        result = _db_ai_records(current_user, page=page, page_size=page_size)
        if result is not None:
            return result
    except Exception as exc:  # noqa: BLE001
        logger.warning("读取 AI 记录失败，回退 mock：%s", exc)
    return _mock_ai_records(current_user, page=page, page_size=page_size)
def _mock_subscriptions(current_user: Optional[Any] = None) -> SubscriptionResponse:
    """订阅管理 mock 兜底：展示分类列表，默认未订阅。"""

    categories = [
        SubscriptionCategory(
            id=int(item.get("id") or 0),
            name=normalize_text(item.get("name")),
            code=normalize_text(item.get("code")),
            subscribed=False,
        )
        for item in sorted(NEWS_CATEGORIES, key=lambda item: (item.get("sort", 0), item.get("id", 0)))
        if int(item.get("status") or 0) == 1
    ]
    return SubscriptionResponse(subscribed_category_ids=[], categories=categories)


def get_subscriptions(current_user: Optional[Any] = None) -> SubscriptionResponse:
    """获取当前用户新闻分类订阅，数据库优先，失败时 mock 兜底。"""

    user_id = _get_current_user_id(current_user)
    if user_id is None:
        return _mock_subscriptions(current_user)

    try:
        rows = execute_query(
            """
            SELECT
                nc.id,
                nc.name,
                nc.code,
                CASE WHEN ucs.id IS NULL THEN 0 ELSE 1 END AS subscribed
            FROM news_category nc
            LEFT JOIN user_category_subscription ucs
              ON ucs.category_id = nc.id AND ucs.user_id = %s
            WHERE nc.status = 1
            ORDER BY nc.sort ASC, nc.id ASC
            """,
            [user_id],
        )
        categories = [
            SubscriptionCategory(
                id=int(row["id"]),
                name=normalize_text(row["name"]),
                code=normalize_text(row["code"]),
                subscribed=bool(row.get("subscribed")),
            )
            for row in rows
        ]
        subscribed_ids = [item.id for item in categories if item.subscribed]
        return SubscriptionResponse(
            subscribed_category_ids=subscribed_ids,
            categories=categories,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("读取订阅分类失败，回退 mock：%s", exc)
        return _mock_subscriptions(current_user)


def update_subscriptions(
    current_user: Optional[Any],
    request: SubscriptionUpdateRequest,
) -> SubscriptionResponse:
    """更新当前用户新闻分类订阅，数据库不可用时返回 mock 兜底数据。"""

    user_id = _get_current_user_id(current_user)
    if user_id is None:
        return _mock_subscriptions(current_user)

    category_ids = sorted({int(item) for item in request.category_ids if int(item) > 0})

    try:
        valid_rows = execute_query(
            """
            SELECT id
            FROM news_category
            WHERE status = 1
            """,
        )
        valid_ids = {int(row["id"]) for row in valid_rows}
        normalized_ids = [category_id for category_id in category_ids if category_id in valid_ids]

        execute_update(
            "DELETE FROM user_category_subscription WHERE user_id = %s",
            [user_id],
        )
        for category_id in normalized_ids:
            execute_update(
                """
                INSERT INTO user_category_subscription (user_id, category_id)
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE updated_at = CURRENT_TIMESTAMP
                """,
                [user_id, category_id],
            )

        return get_subscriptions(current_user)
    except Exception as exc:  # noqa: BLE001
        logger.warning("更新订阅分类失败，回退 mock：%s", exc)
        return _mock_subscriptions(current_user)


# ============================================================================
# 推荐系统（任务 E）
# ============================================================================


def _calculate_recency_score(publish_time: Any) -> float:
    """根据发布时间计算时间衰减分数（0.0-1.0）。"""
    if publish_time is None:
        return 0.1

    try:
        if isinstance(publish_time, datetime):
            pub_dt = publish_time
        else:
            pub_str = normalize_text(publish_time).replace("T", " ").strip()
            if not pub_str:
                return 0.1
            pub_dt = datetime.fromisoformat(pub_str)
    except (ValueError, AttributeError):
        return 0.1

    days_old = (datetime.now() - pub_dt).days

    if days_old <= 1:
        return 1.0
    elif days_old <= 3:
        return 0.8
    elif days_old <= 7:
        return 0.6
    elif days_old <= 30:
        return 0.3
    else:
        return 0.1


def _calculate_heat_score(
    view_count: int, like_count: int, comment_count: int, favorite_count: int
) -> float:
    """根据新闻互动数据计算热度（原始分数）。"""
    return (
        (view_count or 0) * 0.1
        + (like_count or 0) * 1.0
        + (comment_count or 0) * 2.0
        + (favorite_count or 0) * 2.0
    )


def _get_user_browse_news_ids(user_id: int) -> set[int]:
    """获取用户已浏览过的新闻 ID 集合。"""
    try:
        rows = execute_query(
            "SELECT DISTINCT news_id FROM browse_history WHERE user_id = %s",
            [user_id],
        )
        return {int(row["news_id"]) for row in rows if row.get("news_id")}
    except Exception:
        return set()


def _get_topic_name(topic_id: int) -> str:
    """获取话题名称。"""
    try:
        row = execute_one(
            "SELECT topic_name FROM news_topic WHERE id = %s LIMIT 1",
            [topic_id],
        )
        return normalize_text(row.get("topic_name"), "") if row else ""
    except Exception:
        return ""


def _generate_recommendation_reason(
    row: Dict[str, Any],
    topic_affinity: Dict[int, float],
    category_affinity: Dict[int, float],
    match_type: str,
) -> str:
    """生成推荐理由。"""
    # 优先话题推荐理由
    if match_type == "topic" and row.get("topic_id"):
        topic_id = int(row["topic_id"])
        if topic_id in topic_affinity:
            topic_name = normalize_text(row.get("topic_name"), "")
            if topic_name:
                return f'因为你最近关注了「{topic_name}」相关话题'

    # 其次分类推荐理由
    if row.get("category_id"):
        cat_id = int(row["category_id"])
        if cat_id in category_affinity:
            cat_name = normalize_text(row.get("category_name"), "")
            if cat_name:
                return f'因为你经常阅读「{cat_name}」分类新闻'

    # 兜底：热度或最新
    if match_type == "other":
        return "近期热度较高，推荐给你"

    return "为你推荐"


def _get_user_behavior_affinity(user_id: int) -> tuple[Dict[int, float], Dict[int, float]]:
    """
    计算用户对各个话题和分类的偏好分数。

    返回：
    - topic_affinity: {topic_id: affinity_score}
    - category_affinity: {category_id: affinity_score}
    """
    topic_affinity: Dict[int, float] = {}
    category_affinity: Dict[int, float] = {}

    try:
        # 浏览历史（权重 1）
        browse_rows = execute_query(
            """
            SELECT n.topic_id, n.category_id
            FROM browse_history bh
            JOIN news n ON n.id = bh.news_id
            WHERE bh.user_id = %s AND n.status = 1
            """,
            [user_id],
        )

        for row in browse_rows:
            if row.get("topic_id"):
                topic_id = int(row["topic_id"])
                topic_affinity[topic_id] = topic_affinity.get(topic_id, 0) + 1.0
            if row.get("category_id"):
                cat_id = int(row["category_id"])
                category_affinity[cat_id] = category_affinity.get(cat_id, 0) + 1.0

        # 点赞（权重 3）
        like_rows = execute_query(
            """
            SELECT n.topic_id, n.category_id
            FROM user_like ul
            JOIN news n ON n.id = ul.target_id
            WHERE ul.user_id = %s AND ul.target_type = 'news' AND n.status = 1
            """,
            [user_id],
        )

        for row in like_rows:
            if row.get("topic_id"):
                topic_id = int(row["topic_id"])
                topic_affinity[topic_id] = topic_affinity.get(topic_id, 0) + 3.0
            if row.get("category_id"):
                cat_id = int(row["category_id"])
                category_affinity[cat_id] = category_affinity.get(cat_id, 0) + 3.0

        # 收藏（权重 5）
        favorite_rows = execute_query(
            """
            SELECT n.topic_id, n.category_id
            FROM favorite f
            JOIN news n ON n.id = f.target_id
            WHERE f.user_id = %s AND f.target_type = 'news' AND n.status = 1
            """,
            [user_id],
        )

        for row in favorite_rows:
            if row.get("topic_id"):
                topic_id = int(row["topic_id"])
                topic_affinity[topic_id] = topic_affinity.get(topic_id, 0) + 5.0
            if row.get("category_id"):
                cat_id = int(row["category_id"])
                category_affinity[cat_id] = category_affinity.get(cat_id, 0) + 5.0

    except Exception as exc:
        logger.warning("计算用户偏好失败：%s", exc)

    return topic_affinity, category_affinity


def _db_recommendations(user_id: int, limit: int = 10) -> Dict[str, Any] | None:
    """从数据库获取个性化推荐新闻。"""
    try:
        # Step 1：获取用户偏好
        topic_affinity, category_affinity = _get_user_behavior_affinity(user_id)
        already_browsed = _get_user_browse_news_ids(user_id)

        if not topic_affinity and not category_affinity:
            # 冷启动：返回热门或最新新闻
            return _get_hot_or_latest_recommendations(limit, exclude_ids=already_browsed)

        # Step 2：生成候选新闻（优先按话题和分类）
        topic_ids = list(topic_affinity.keys()) if topic_affinity else []
        category_ids = list(category_affinity.keys()) if category_affinity else []

        # 构建 SQL：获取候选新闻
        placeholders_topic = ",".join(["%s"] * len(topic_ids)) if topic_ids else "NULL"
        placeholders_category = ",".join(["%s"] * len(category_ids)) if category_ids else "NULL"

        params = topic_ids + category_ids + [user_id, limit * 3]

        candidate_sql = f"""
            SELECT
                n.id, n.title, n.summary, n.content, n.cover_image,
                n.category_id, nc.name as category_name,
                n.topic_id, nt.topic_name,
                n.source, n.editor, n.publish_time,
                n.view_count, n.like_count, n.comment_count, n.favorite_count,
                n.status, n.tags, n.source_url,
                CASE
                    WHEN n.topic_id IN ({placeholders_topic}) THEN 'topic'
                    WHEN n.category_id IN ({placeholders_category}) THEN 'category'
                    ELSE 'other'
                END as match_type
            FROM news n
            LEFT JOIN news_category nc ON nc.id = n.category_id
            LEFT JOIN news_topic nt ON nt.id = n.topic_id
            WHERE n.status = 1
                AND n.id NOT IN (SELECT news_id FROM browse_history WHERE user_id = %s)
            ORDER BY match_type, n.publish_time DESC
            LIMIT %s
        """

        candidate_rows = execute_query(candidate_sql, params)

        if not candidate_rows:
            return _get_hot_or_latest_recommendations(limit, exclude_ids=already_browsed)

        # Step 3：计算推荐分数
        scored_items = []
        max_heat = 0.1  # 避免除零

        for row in candidate_rows:
            heat = _calculate_heat_score(
                row.get("view_count"),
                row.get("like_count"),
                row.get("comment_count"),
                row.get("favorite_count"),
            )
            max_heat = max(max_heat, heat)

        max_affinity = max(topic_affinity.values()) if topic_affinity else 1.0

        for row in candidate_rows:
            news_id = int(row["id"])

            # 计算 affinity_score
            if row.get("match_type") == "topic" and row.get("topic_id"):
                topic_id = int(row["topic_id"])
                affinity = topic_affinity.get(topic_id, 0) / max_affinity
            elif row.get("match_type") == "category" and row.get("category_id"):
                cat_id = int(row["category_id"])
                affinity = (category_affinity.get(cat_id, 0) * 0.6) / max_affinity
            else:
                affinity = 0.0

            # 计算 heat_score
            heat = _calculate_heat_score(
                row.get("view_count"),
                row.get("like_count"),
                row.get("comment_count"),
                row.get("favorite_count"),
            )
            heat_score = heat / max_heat if max_heat > 0 else 0.0

            # 计算 recency_score
            recency = _calculate_recency_score(row.get("publish_time"))

            # 组合分数
            score = 0.5 * affinity + 0.3 * heat_score + 0.2 * recency

            scored_items.append((score, row))

        # Step 4：排序并取 limit 条
        scored_items.sort(key=lambda x: x[0], reverse=True)

        recommendation_items = []
        for score, row in scored_items[:limit]:
            match_type = row.get("match_type", "other")
            recommendation_reason = _generate_recommendation_reason(
                row, topic_affinity, category_affinity, match_type
            )

            recommendation_items.append(
                {
                    "id": int(row["id"]),
                    "title": normalize_text(row["title"]),
                    "summary": normalize_text(row["summary"]),
                    "cover_image": normalize_text(row.get("cover_image"), ""),
                    "category_id": row.get("category_id"),
                    "category_name": normalize_text(row.get("category_name"), "未分类"),
                    "topic_id": row.get("topic_id"),
                    "topic_name": normalize_text(row.get("topic_name"), ""),
                    "source": normalize_text(row.get("source"), ""),
                    "editor": normalize_text(row.get("editor"), ""),
                    "publish_time": format_datetime(row.get("publish_time")),
                    "view_count": int(row.get("view_count") or 0),
                    "like_count": int(row.get("like_count") or 0),
                    "comment_count": int(row.get("comment_count") or 0),
                    "favorite_count": int(row.get("favorite_count") or 0),
                    "status": int(row.get("status") or 1),
                    "tags": _parse_json_field(row.get("tags"), []),
                    "source_url": normalize_text(row.get("source_url"), ""),
                    "recommendation_score": round(score, 3),
                    "recommendation_reason": recommendation_reason,
                }
            )

        return paginate(recommendation_items, page=1, page_size=limit)

    except Exception as exc:
        logger.warning("数据库推荐查询失败：%s", exc)
        return None


def _get_hot_or_latest_recommendations(limit: int, exclude_ids: set[int] | None = None) -> Dict[str, Any]:
    """获取热门或最新新闻作为兜底推荐。"""
    if exclude_ids is None:
        exclude_ids = set()

    try:
        # 优先：近 7 天热门新闻
        placeholders = ",".join(["%s"] * len(exclude_ids)) if exclude_ids else ""
        where_clause = f"WHERE n.status = 1 AND n.id NOT IN ({placeholders})" if exclude_ids else "WHERE n.status = 1"

        rows = execute_query(
            f"""
            SELECT
                n.id, n.title, n.summary, n.content, n.cover_image,
                n.category_id, nc.name as category_name,
                n.topic_id, nt.topic_name,
                n.source, n.editor, n.publish_time,
                n.view_count, n.like_count, n.comment_count, n.favorite_count,
                n.status, n.tags, n.source_url
            FROM news n
            LEFT JOIN news_category nc ON nc.id = n.category_id
            LEFT JOIN news_topic nt ON nt.id = n.topic_id
            {where_clause}
            ORDER BY n.publish_time DESC, n.id DESC
            LIMIT %s
            """,
            list(exclude_ids) + [limit],
        )

        if not rows:
            return paginate([], page=1, page_size=limit)

        recommendation_items = []
        for row in rows:
            recommendation_items.append(
                {
                    "id": int(row["id"]),
                    "title": normalize_text(row["title"]),
                    "summary": normalize_text(row["summary"]),
                    "cover_image": normalize_text(row.get("cover_image"), ""),
                    "category_id": row.get("category_id"),
                    "category_name": normalize_text(row.get("category_name"), "未分类"),
                    "topic_id": row.get("topic_id"),
                    "topic_name": normalize_text(row.get("topic_name"), ""),
                    "source": normalize_text(row.get("source"), ""),
                    "editor": normalize_text(row.get("editor"), ""),
                    "publish_time": format_datetime(row.get("publish_time")),
                    "view_count": int(row.get("view_count") or 0),
                    "like_count": int(row.get("like_count") or 0),
                    "comment_count": int(row.get("comment_count") or 0),
                    "favorite_count": int(row.get("favorite_count") or 0),
                    "status": int(row.get("status") or 1),
                    "tags": _parse_json_field(row.get("tags"), []),
                    "source_url": normalize_text(row.get("source_url"), ""),
                    "recommendation_score": 0.5,
                    "recommendation_reason": "近期热度较高，推荐给你",
                }
            )

        return paginate(recommendation_items, page=1, page_size=limit)

    except Exception as exc:
        logger.warning("获取热门或最新新闻失败：%s", exc)
        return paginate([], page=1, page_size=limit)


def _mock_recommendations(limit: int = 10) -> Dict[str, Any]:
    """从 mock 数据返回推荐新闻。"""
    recommendation_items = []

    for news in MOCK_NEWS[:limit]:
        recommendation_items.append(
            {
                "id": news["id"],
                "title": normalize_text(news.get("title")),
                "summary": normalize_text(news.get("summary")),
                "cover_image": normalize_text(news.get("cover_image"), ""),
                "category_id": news.get("category_id"),
                "category_name": news.get("category_name", "未分类"),
                "topic_id": news.get("topic_id"),
                "topic_name": "",
                "source": normalize_text(news.get("source"), ""),
                "editor": normalize_text(news.get("editor"), ""),
                "publish_time": news.get("publish_time", ""),
                "view_count": news.get("view_count", 0),
                "like_count": news.get("like_count", 0),
                "comment_count": news.get("comment_count", 0),
                "favorite_count": news.get("favorite_count", 0),
                "status": news.get("status", 1),
                "tags": news.get("tags", []),
                "source_url": news.get("source_url", ""),
                "recommendation_score": 0.5,
                "recommendation_reason": "系统推荐内容",
            }
        )

    return paginate(recommendation_items, page=1, page_size=limit)


def get_recommendations(current_user: Optional[Any] = None, limit: int = 10) -> Dict[str, Any]:
    """获取用户个性化推荐新闻。"""
    user_id = _get_current_user_id(current_user)
    if user_id is None:
        return paginate([], page=1, page_size=limit)

    # 限制 limit 参数
    limit = max(1, min(limit, 50))

    try:
        result = _db_recommendations(user_id, limit=limit)
        if result is not None:
            return result
    except Exception as exc:
        logger.warning("数据库推荐查询异常，回退 mock：%s", exc)

    return _mock_recommendations(limit=limit)


# ============================================================
# 近 7 天阅读报告
# ============================================================

AI_SERVICE_URL = "http://127.0.0.1:8001"
PROFILE_REPORT_AI_TIMEOUT = 60.0  # 长文本 LLM 生成可能需 30~50 秒
PROMPT_VERSION = "v3_complete_7days_exclude_today"  # 修改口径/prompt 时更新，旧缓存自动失效


def _validate_ai_analysis(ai: AiAnalysisResult, overview: dict, top_topics: list[dict]) -> tuple[bool, list[str]]:
    """二次校验 AI 分析结果，返回 (通过, issues)。失败时上层应 fallback。"""
    issues: list[str] = []

    # 1. 字段完整性
    if not ai.summary or not ai.summary.strip():
        issues.append("ai_summary 为空")
    if not isinstance(ai.insights, list) or len(ai.insights) != 3:
        issues.append(f"ai_insights 数量异常: {len(ai.insights) if isinstance(ai.insights, list) else type(ai.insights)}")
    if not isinstance(ai.suggestions, list) or len(ai.suggestions) != 2:
        issues.append(f"ai_suggestions 数量异常: {len(ai.suggestions) if isinstance(ai.suggestions, list) else type(ai.suggestions)}")
    if ai.quality_score < 0 or ai.quality_score > 1:
        issues.append(f"quality_score 越界: {ai.quality_score}")

    # 2. 长度校验
    if ai.summary and (len(ai.summary) < 20 or len(ai.summary) > 400):
        issues.append(f"ai_summary 长度异常: {len(ai.summary)}")
    for i, ins in enumerate(ai.insights or []):
        if len(ins) < 5 or len(ins) > 120:
            issues.append(f"ai_insights[{i}] 长度异常: {len(ins)}")

    # 3. 数字一致性弱校验
    browse_count = overview.get("browse_count", 0)
    favorite_count = overview.get("favorite_count", 0)
    ai_count = overview.get("ai_count", 0)
    all_text = f"{ai.summary} {' '.join(ai.insights or [])} {' '.join(ai.suggestions or [])}"
    # 简单检查：如果出现差距很大的数字
    import re
    nums = re.findall(r'\d+', all_text)
    for n_str in nums:
        n = int(n_str)
        if n > 0 and n <= 50:
            # 可能是计数，不是浏览数就是收藏数或AI数，简单检查
            pass  # 不做过于激进的数字匹配
    if browse_count > 0:
        if f"{browse_count + 5}" in all_text or f"{browse_count + 10}" in all_text:
            issues.append("ai_summary 中疑似出现与 browse_count 不一致的数字")

    # 4. 主题一致性弱校验
    valid_topic_names = {t.get("name", "") for t in top_topics}
    for pattern in ["最关注", "主要关注", "最常关注"]:
        if pattern in all_text:
            # 简单的主题名检查（不做复杂NLP）
            for tname in valid_topic_names:
                if tname and len(tname) >= 2 and tname in all_text:
                    break
            else:
                issues.append("ai_summary 中提到'关注'但未匹配到已知主题")

    # 5. 格式校验
    for marker in ["###", "```", "作为一个 AI", "作为一个人工智能", "根据您提供的数据", "Based on the data"]:
        if marker in all_text:
            issues.append(f"ai_summary 包含禁用格式: {marker}")

    passed = len(issues) == 0
    if not passed:
        logger.warning("AI 二次校验未通过: %s", "; ".join(issues))
    return passed, issues


def _compute_input_hash(overview: dict, daily_summary: dict, top_topics: list[dict]) -> str:
    """基于聚合数据计算 input_hash，数据变化时自动失效缓存。"""
    raw = json.dumps({
        "pv": PROMPT_VERSION,
        "ov": {k: overview.get(k, 0) for k in ["browse_count","favorite_count","comment_count","ai_count","active_days"]},
        "ds": {k: daily_summary.get(k, "") for k in ["most_active_date","max_daily_count"]},
        "tt": [(t.get("name",""), t.get("count",0)) for t in top_topics[:5]],
    }, sort_keys=True)
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def _get_cached_ai(user_id: int, input_hash: str) -> AiAnalysisResult | None:
    """从缓存表读取 AI 分析结果。"""
    row = execute_one(
        "SELECT ai_summary, ai_insights, ai_suggestions, ai_source, quality_score, page_analyses_overview, page_analyses_trajectory, page_analyses_conclusion, reading_style, closing FROM profile_weekly_report_cache WHERE user_id=%s AND range_days=7 AND report_date=CURDATE() AND input_hash=%s",
        [user_id, input_hash],
    )
    if not row:
        return None
    insights = json.loads(row["ai_insights"]) if isinstance(row["ai_insights"], str) else (row["ai_insights"] or [])
    suggestions = json.loads(row["ai_suggestions"]) if isinstance(row["ai_suggestions"], str) else (row["ai_suggestions"] or [])
    logger.info("Cache HIT for user %d", user_id)
    return AiAnalysisResult(
        enabled=True, source="cache",
        summary=row["ai_summary"] or "",
        insights=insights if isinstance(insights, list) else [],
        suggestions=suggestions if isinstance(suggestions, list) else [],
        page_analyses=PageAnalyses(
            overview=row.get("page_analyses_overview") or "",
            trajectory=row.get("page_analyses_trajectory") or "",
            conclusion=row.get("page_analyses_conclusion") or "",
        ),
        reading_style=row.get("reading_style") or "",
        closing=row.get("closing") or "",
        quality_score=float(row["quality_score"] or 0),
    )


def _save_cached_ai(user_id: int, input_hash: str, ai: AiAnalysisResult):
    """写入缓存。"""
    try:
        execute_update(
            """INSERT INTO profile_weekly_report_cache (user_id, range_days, report_date, input_hash, ai_summary, ai_insights, ai_suggestions, ai_source, quality_score, page_analyses_overview, page_analyses_trajectory, page_analyses_conclusion, reading_style, closing)
               VALUES (%s,7,CURDATE(),%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
               ON DUPLICATE KEY UPDATE ai_summary=VALUES(ai_summary), ai_insights=VALUES(ai_insights), ai_suggestions=VALUES(ai_suggestions), ai_source=VALUES(ai_source), quality_score=VALUES(quality_score), page_analyses_overview=VALUES(page_analyses_overview), page_analyses_trajectory=VALUES(page_analyses_trajectory), page_analyses_conclusion=VALUES(page_analyses_conclusion), reading_style=VALUES(reading_style), closing=VALUES(closing), updated_at=NOW()""",
            [user_id, input_hash, ai.summary, json.dumps(ai.insights, ensure_ascii=False), json.dumps(ai.suggestions, ensure_ascii=False), ai.source, ai.quality_score, ai.page_analyses.overview, ai.page_analyses.trajectory, ai.page_analyses.conclusion, ai.reading_style, ai.closing],
        )
    except Exception as e:
        logger.warning("Cache write failed: %s", e)


def _call_ai_weekly_report(
    user_id: int, overview: dict, scores: dict, persona_title: str,
    daily_summary: dict, top_topics: list[dict], highlights: list[dict],
    force_refresh: bool = False,
) -> AiAnalysisResult:
    """调用 ai-service 生成个性化周报文案，优先读缓存。"""
    input_hash = _compute_input_hash(overview, daily_summary, top_topics)

    # 1. 尝试读缓存（force_refresh 时跳过）
    if not force_refresh:
        cached = _get_cached_ai(user_id, input_hash)
        if cached is not None:
            return cached

    # 2. 调用 ai-service（使用长超时 60s）
    payload = {
        "task_type": "profile_weekly_report", "range_days": 7,
        "overview": overview, "behavior_scores": scores, "persona_title": persona_title,
        "daily_summary": daily_summary, "top_topics": top_topics, "highlights": highlights,
    }
    try:
        with httpx.Client(timeout=PROFILE_REPORT_AI_TIMEOUT) as client:
            resp = client.post(f"{AI_SERVICE_URL}/ai/profile-weekly-report", json=payload, headers={"Content-Type": "application/json"})
            if resp.status_code != 200:
                logger.warning("AI service HTTP %d: %s", resp.status_code, resp.text[:100])
                return _ai_fallback(overview, daily_summary, top_topics, persona_title, scores)
            data = resp.json().get("data", {})
            quality = data.get("quality", {})
            pa = data.get("page_analyses", {}) or {}
            result = AiAnalysisResult(
                enabled=True, source=data.get("source", "llm"),
                summary=data.get("ai_summary", ""),
                insights=data.get("ai_insights", []),
                suggestions=data.get("ai_suggestions", []),
                page_analyses=PageAnalyses(
                    overview=str(pa.get("overview", "")).strip(),
                    trajectory=str(pa.get("trajectory", "")).strip(),
                    conclusion=str(pa.get("conclusion", "")).strip(),
                ),
                reading_style=str(data.get("reading_style", "")).strip(),
                closing=str(data.get("closing", "")).strip(),
                quality_score=quality.get("score", 0.0) if isinstance(quality, dict) else 0.0,
            )
            passed, issues = _validate_ai_analysis(result, overview, top_topics)
            if passed:
                _save_cached_ai(user_id, input_hash, result)
                return result
            else:
                logger.warning("AI validation failed, fallback: %s", "; ".join(issues))
                return _ai_fallback(overview, daily_summary, top_topics, persona_title, scores)
    except Exception as e:
        logger.warning("AI service failed: %s", e)
        return _ai_fallback(overview, daily_summary, top_topics, persona_title, scores)


def _generate_analysis_texts(overview: dict, scores: dict, daily_summary: dict, topic_rank: list, active_days: int) -> dict:
    """规则生成图表解读文字。"""
    reading = scores.get("reading", 0)
    collecting = scores.get("collecting", 0)
    interaction = scores.get("interaction", 0)
    ai = scores.get("ai_usage", 0)
    max_dim = max(reading, collecting, interaction, ai)

    if max_dim == reading and reading >= 60:
        behavior_text = "你的阅读探索得分最高，说明你习惯主动获取信息，保持了对世界的好奇心。"
    elif max_dim == collecting and collecting >= 60:
        behavior_text = "你的内容沉淀得分最高，善于发现并保存有价值的信息，收藏夹是你的知识库。"
    elif max_dim == interaction and interaction >= 60:
        behavior_text = "你的社区互动得分最高，喜欢通过评论和他人交流，这让阅读更有深度。"
    elif max_dim == ai and ai >= 60:
        behavior_text = "你的 AI 使用得分最高，智能摘要已经成为你高效处理信息的得力工具。"
    else:
        behavior_text = "你的各项行为较为均衡，正在逐步建立自己的阅读节奏。"

    if reading >= 60 and ai >= 60:
        behavior_text += " 同时你积极使用 AI 工具辅助理解，是典型的智能阅读者。"

    most_active = daily_summary.get("most_active_date", "")
    activity_text = f'近 7 天中你有 {active_days} 天保持阅读'
    if most_active:
        activity_text += f'，{most_active} 达到本周峰值'
    activity_text += '。' if active_days >= 5 else '，可以尝试更稳定的阅读节奏。'

    topic_text = ""
    if topic_rank:
        top1 = topic_rank[0]
        topic_text = f'你最关注「{top1.name}」类内容'
        if len(topic_rank) >= 3:
            names = [t.name for t in topic_rank[:3] if t.name != "其他"]
            if names:
                topic_text += f'，兴趣集中在{"、".join(names)}'
        topic_text += '。'

    return {
        "profile_analysis": behavior_text,
        "behavior_analysis": behavior_text,
        "activity_analysis": activity_text,
        "topic_analysis": topic_text,
    }


def _build_narrative_highlights(overview: dict, daily_summary: dict, topic_rank: list, highlights: list) -> list[dict]:
    """生成叙事化高光记录。"""
    result = []
    most_active = daily_summary.get("most_active_date", "")
    max_count = daily_summary.get("max_daily_count", 0)

    if most_active:
        result.append({"icon": "🔥", "label": "阅读高峰", "value": most_active, "desc": f"是你本周最活跃的一天", "narrative": f"{most_active} 是你本周最活跃的一天，单日浏览 {max_count} 次。"})

    if topic_rank:
        top = topic_rank[0]
        if top.name != "其他":
            result.append({"icon": "📌", "label": "关注主题", "value": top.name, "desc": f"浏览 {top.count} 个相关内容", "narrative": f'你本周最关注「{top.name}」类内容，共浏览 {top.count} 个相关新闻与帖子。'})

    ai_count = overview.get("ai_count", 0)
    if ai_count > 0:
        result.append({"icon": "🤖", "label": "AI 使用", "value": f"{ai_count} 次", "desc": "AI 已成为你的信息处理助手", "narrative": f"你本周使用 AI 摘要 {ai_count} 次，AI 已成为你高效处理信息的得力助手。"})

    fav_count = overview.get("favorite_count", 0)
    if fav_count > 0:
        if fav_count >= 5:
            result.append({"icon": "⭐", "label": "内容沉淀", "value": f"{fav_count} 条", "desc": "体现出较强的内容沉淀习惯", "narrative": f"你本周收藏了 {fav_count} 条内容，体现出较强的内容沉淀习惯，这些内容值得反复回顾。"})
        else:
            result.append({"icon": "⭐", "label": "内容收藏", "value": f"{fav_count} 条", "desc": "继续收藏感兴趣的内容吧", "narrative": f"你本周收藏了 {fav_count} 条内容，继续收藏感兴趣的内容，知识库会越来越丰富。"})

    return result[:4]


def _ai_fallback(
    overview: dict, daily_summary: dict, top_topics: list[dict],
    persona_title: str, scores: dict,
) -> AiAnalysisResult:
    """AI 服务不可用时，用规则生成 AI 分析结果（含长文本）。"""
    topics = [t.get("name", "") for t in top_topics[:3] if t.get("name")]
    topics_str = "、".join(topics) if topics else "多种内容"
    r = scores.get("reading", 0); a = scores.get("ai_usage", 0)
    c = scores.get("collecting", 0); i = scores.get("interaction", 0)

    return AiAnalysisResult(
        enabled=True, source="fallback",
        summary=f"过去 7 天，你有 {daily_summary.get('active_days', 0)} 天留下阅读足迹，共浏览 {overview.get('browse_count', 0)} 个内容，最常关注 {topics_str}，并使用 AI 生成了 {overview.get('ai_count', 0)} 次摘要。",
        insights=[f"你本周阅读了 {overview.get('browse_count', 0)} 个内容，探索欲很强，保持这份好奇心吧。" if r >= 60 else "继续关注感兴趣的主题，阅读量会逐步提升。", f"你已经习惯使用 AI 摘要来辅助阅读，这是处理信息的聪明方式。" if a >= 60 else "试试用 AI 摘要来快速了解长文章的核心内容。", f"你收藏了 {overview.get('favorite_count', 0)} 条内容，善于沉淀有价值的信息。" if c >= 50 else "遇到感兴趣的内容可以收藏起来方便回顾。"],
        suggestions=["试试用 AI 摘要来快速了解长文章的核心内容，节省阅读时间。" if a < 50 else "继续借助 AI 工具提升阅读效率，了解更多领域的新闻。", "遇到感兴趣的内容可以收藏起来，方便以后回顾，构建自己的知识库。" if c < 50 else "继续保持内容沉淀习惯，你的收藏夹正在成为有价值的知识库。"],
        page_analyses=PageAnalyses(
            overview=f"本周你共浏览了 {overview.get('browse_count', 0)} 个内容，活跃 {daily_summary.get('active_days', 0)} 天。{'你的阅读探索欲很强，' if r >= 60 else ''}{'同时积极使用 AI 工具辅助理解，' if a >= 60 else ''}展现出主动获取信息与借助智能工具提升效率的阅读风格。从行为画像来看，你在平台上正在建立清晰的个人阅读节奏。",
            trajectory=f"近 7 天中你有 {daily_summary.get('active_days', 0)} 天保持阅读，{daily_summary.get('most_active_date', '')} 达到本周峰值，单日浏览 {daily_summary.get('max_daily_count', 0)} 次。你最关注 {topics_str}，体现出对现实议题和行业趋势的持续兴趣。阅读节奏比较稳定，建议继续保持每日浏览的习惯。",
            conclusion=f"这一周你在平台上留下了清晰的阅读轨迹：共浏览 {overview.get('browse_count', 0)} 个内容，收藏 {overview.get('favorite_count', 0)} 条，发表 {overview.get('comment_count', 0)} 次评论，使用 AI 摘要 {overview.get('ai_count', 0)} 次。这些行为构成了你本周的阅读画像。继续保持好奇心，系统会为你沉淀更完整的个人阅读档案。",
        ),
        reading_style="你更像一位以主动探索为主、善于借助 AI 工具提升信息处理效率的读者。" if r >= 60 and a >= 60 else "你正在逐步建立自己的阅读节奏，是一位有潜力的成长型读者。",
        closing=f"作为「{persona_title}」，你在 {topics_str} 等方向留下了本周的阅读足迹。每一篇新闻、每一次收藏和每一条评论，都在丰富你的阅读画像。下周继续探索，系统会为你生成更完整的个人阅读报告。",
        quality_score=0.5,
    )


def get_weekly_report(current_user: Optional[Any] = None, force_refresh: bool = False) -> WeeklyReportResponse:
    """Generate a weekly reading report for the last 7 days.

    Args:
        force_refresh: 跳过缓存，强制重新调用 ai-service（仅测试阶段使用）
    """
    user_id = _get_current_user_id(current_user)
    if user_id is None:
        return WeeklyReportResponse(empty=True)

    # 统计范围：截至昨日的最近完整 7 天，不包含今天
    today = date.today()
    start_date = today - timedelta(days=7)          # e.g. 2026-06-24
    end_date = today - timedelta(days=1)             # e.g. 2026-06-30
    end_date_str = end_date.isoformat()
    start_date_str = start_date.isoformat()
    end_exclusive = today.isoformat()                # < today = < 2026-07-01 00:00:00

    # ---- 查询近 7 天行为数据 ----
    daily_rows = execute_query(
        """
        SELECT DATE(browse_time) AS dt, COUNT(*) AS cnt
        FROM browse_history
        WHERE user_id = %s AND browse_time >= %s AND browse_time < %s
        GROUP BY DATE(browse_time) ORDER BY dt
        """,
        [user_id, start_date_str, end_exclusive],
    )

    # 浏览内容数（去重）
    news_browse = execute_one(
        """SELECT COUNT(DISTINCT news_id) AS cnt FROM browse_history
           WHERE user_id=%s AND news_id>0 AND browse_time>=%s
             AND (target_type='news' OR target_type IS NULL OR target_type='')""",
        [user_id, start_date_str],
    )
    post_browse = execute_one(
        """SELECT COUNT(DISTINCT target_id) AS cnt FROM browse_history
           WHERE user_id=%s AND target_type='post' AND target_id IS NOT NULL AND browse_time>=%s AND browse_time<%s""",
        [user_id, start_date_str, end_exclusive],
    )
    browse_count = int((news_browse or {}).get("cnt") or 0) + int((post_browse or {}).get("cnt") or 0)

    # 收藏数（有效目标）
    fav_news = execute_one(
        """SELECT COUNT(*) AS cnt FROM favorite f INNER JOIN news n ON n.id=f.target_id AND n.status=1
           WHERE f.user_id=%s AND f.target_type='news' AND f.created_at>=%s AND f.created_at<%s""",
        [user_id, start_date_str, end_exclusive],
    )
    fav_post = execute_one(
        """SELECT COUNT(*) AS cnt FROM favorite f INNER JOIN community_post p ON p.id=f.target_id AND p.status=1
           WHERE f.user_id=%s AND f.target_type='post' AND f.created_at>=%s AND f.created_at<%s""",
        [user_id, start_date_str, end_exclusive],
    )
    favorite_count = int((fav_news or {}).get("cnt") or 0) + int((fav_post or {}).get("cnt") or 0)

    # 评论数
    nc = execute_one(
        "SELECT COUNT(*) AS cnt FROM news_comment WHERE user_id=%s AND status<>4 AND created_at>=%s AND created_at<%s",
        [user_id, start_date_str, end_exclusive],
    )
    pc = execute_one(
        "SELECT COUNT(*) AS cnt FROM post_comment WHERE user_id=%s AND status<>4 AND created_at>=%s AND created_at<%s",
        [user_id, start_date_str, end_exclusive],
    )
    comment_count = int((nc or {}).get("cnt") or 0) + int((pc or {}).get("cnt") or 0)

    # AI 记录
    ai_row = execute_one(
        "SELECT COUNT(*) AS cnt FROM ai_generate_record WHERE user_id=%s AND status=1 AND created_at>=%s AND created_at<%s",
        [user_id, start_date_str, end_exclusive],
    )
    ai_count = int((ai_row or {}).get("cnt") or 0)

    total_browse_actions = sum(int(r["cnt"]) for r in daily_rows)
    active_days = len(daily_rows)

    # 空报告
    if total_browse_actions == 0 and favorite_count == 0 and comment_count == 0 and ai_count == 0:
        return WeeklyReportResponse(
            range=WeeklyReportRange(days=7, start_date=start_date_str, end_date=end_date_str),
            empty=True,
        )

    # ---- 连续阅读天数 ----
    date_set = {r["dt"].isoformat() if hasattr(r["dt"], "isoformat") else str(r["dt"]) for r in daily_rows}
    max_streak = 0
    streak = 0
    for i in range(7):
        d = (today - timedelta(days=i)).isoformat()
        if d in date_set:
            streak += 1
            max_streak = max(max_streak, streak)
        else:
            streak = 0

    # 最活跃日期
    daily_list = []
    max_count = 0
    max_date = ""
    for i in range(6, -1, -1):
        d = (end_date - timedelta(days=i)).isoformat()
        found = next((r for r in daily_rows if (r["dt"].isoformat() if hasattr(r["dt"], "isoformat") else str(r["dt"])) == d), None)
        cnt = int(found["cnt"]) if found else 0
        daily_list.append({"date": d, "count": cnt})
        if cnt > max_count:
            max_count = cnt
            max_date = d

    # ---- 行为评分 ----
    reading_score = min(100, int(browse_count / 25 * 100))
    collect_score = min(100, int(favorite_count / 10 * 100))
    interaction_score = min(100, int(comment_count / 12 * 100))
    ai_score = min(100, int(ai_count / 6 * 100))

    # ---- 用户称号 ----
    scores_for_persona = {
        "reading": reading_score,
        "collecting": collect_score,
        "interaction": interaction_score,
        "ai_usage": ai_score,
    }
    max_score = max(scores_for_persona.values())
    if max_score < 20:
        persona_title = "新晋观察者"
        persona_desc = "你刚开始探索平台，继续保持好奇，未来会生成更丰富的阅读画像。"
    elif ai_score >= 70 and reading_score >= 60:
        persona_title = "AI驱动型新闻探索者"
        persona_desc = "你的阅读探索和 AI 使用较突出，说明你更倾向于主动获取信息并借助智能工具提升阅读效率。"
    elif max_score == reading_score:
        persona_title = "新闻探索者"
        persona_desc = "你热衷于浏览各类新闻内容，保持对世界的好奇心是你的标签。"
    elif max_score == scores_for_persona["collecting"]:
        persona_title = "内容收藏家"
        persona_desc = "你善于发现并保存有价值的内容，收藏夹是你的知识库。"
    elif max_score == scores_for_persona["interaction"]:
        persona_title = "社区互动者"
        persona_desc = "你喜欢在社区中表达观点，通过评论与其他用户交流想法。"
    elif all(v >= 60 for v in scores_for_persona.values()):
        persona_title = "全能型信息管理者"
        persona_desc = "你在阅读、收藏、互动和 AI 使用上都表现活跃，是平台的全能型用户。"
    else:
        persona_title = "新闻探索者"
        persona_desc = "你热衷于浏览各类新闻内容，保持对世界的好奇心是你的标签。"

    # ---- 一句话总结 ----
    most_active_display = max_date[-5:] if max_date else ""
    summary_parts = [f"过去 7 天，你有 {active_days} 天留下阅读足迹"]
    if browse_count > 0:
        summary_parts.append(f"共浏览 {browse_count} 个内容")
    if favorite_count > 0:
        summary_parts.append(f"收藏 {favorite_count} 条")
    if ai_count > 0:
        summary_parts.append(f"使用 AI 生成 {ai_count} 次摘要")
    summary_text = "，".join(summary_parts) + "。"

    # ---- 主题排行 ----
    topic_rows = execute_query(
        """
        SELECT COALESCE(nc.name, '未分类') AS name, COUNT(DISTINCT bh.news_id) AS cnt
        FROM browse_history bh
        LEFT JOIN news n ON n.id=bh.news_id
        LEFT JOIN news_category nc ON nc.id=n.category_id
        WHERE bh.user_id=%s AND bh.news_id>0 AND bh.browse_time>=%s AND bh.browse_time<%s
          AND (bh.target_type='news' OR bh.target_type IS NULL OR bh.target_type='')
        GROUP BY nc.id, nc.name ORDER BY cnt DESC LIMIT 10
        """,
        [user_id, start_date_str, end_exclusive],
    )
    # Add post tags
    post_topic_rows = execute_query(
        """
        SELECT COALESCE(JSON_UNQUOTE(JSON_EXTRACT(cp.tags, '$[0]')), '社区帖子') AS name,
               COUNT(DISTINCT bh.target_id) AS cnt
        FROM browse_history bh
        JOIN community_post cp ON cp.id=bh.target_id
        WHERE bh.user_id=%s AND bh.target_type='post' AND bh.browse_time>=%s AND bh.browse_time<%s
        GROUP BY name ORDER BY cnt DESC
        """,
        [user_id, start_date_str, end_exclusive],
    )

    # Merge and rank
    topic_map: dict[str, int] = {}
    for r in topic_rows:
        topic_map[normalize_text(r["name"]) or "未分类"] = int(r["cnt"])
    for r in post_topic_rows:
        name = normalize_text(r["name"]) or "社区帖子"
        topic_map[name] = topic_map.get(name, 0) + int(r["cnt"])

    sorted_topics = sorted(topic_map.items(), key=lambda x: x[1], reverse=True)
    topic_total = sum(c for _, c in sorted_topics)
    top5 = sorted_topics[:5]
    others_count = sum(c for _, c in sorted_topics[5:])

    topic_rank = []
    pct_sum = 0
    for i, (name, cnt) in enumerate(top5):
        pct = int(round(cnt / topic_total * 100)) if topic_total > 0 else 0
        topic_rank.append(TopicRankItem(name=name, count=cnt, percent=pct))
        pct_sum += pct

    # Adjust last percentage
    if topic_rank and topic_total > 0 and others_count == 0:
        topic_rank[-1].percent = 100 - sum(t.percent for t in topic_rank[:-1])

    if others_count > 0:
        other_pct = 100 - pct_sum
        topic_rank.append(TopicRankItem(name="其他", count=others_count, percent=max(0, other_pct)))

    # ---- 高光记录 ----
    highlights = []
    if max_date:
        month_day = f"{int(max_date[5:7])}月{int(max_date[8:10])}日"
        highlights.append(WeeklyReportHighlight(
            label="最活跃日期", value=month_day, desc=f"浏览 {max_count} 次"
        ))
    if topic_rank:
        top_topic = topic_rank[0]
        highlights.append(WeeklyReportHighlight(
            label="最关注主题", value=top_topic.name,
            desc=f"浏览 {top_topic.count} 个内容" if top_topic.count > 0 else ""
        ))
    if ai_count > 0:
        highlights.append(WeeklyReportHighlight(
            label="AI 使用", value=f"{ai_count} 次",
            desc="你本周使用了 AI 摘要工具" if ai_count > 0 else ""
        ))
    if favorite_count > 0:
        highlights.append(WeeklyReportHighlight(
            label="内容收藏", value=f"{favorite_count} 条",
            desc="你有较强的内容沉淀习惯" if favorite_count >= 5 else "继续收藏感兴趣的内容吧"
        ))

    # 调用 AI 服务生成个性化文案（失败时自动回退规则文案）
    ai_analysis = _call_ai_weekly_report(
        user_id=user_id, force_refresh=force_refresh,
        overview={"browse_count": browse_count, "favorite_count": favorite_count, "comment_count": comment_count, "ai_count": ai_count, "active_days": active_days},
        scores={"reading": reading_score, "collecting": collect_score, "interaction": interaction_score, "ai_usage": ai_score},
        persona_title=persona_title,
        daily_summary={"active_days": active_days, "most_active_date": max_date, "max_daily_count": max_count},
        top_topics=[{"name": t.name, "count": t.count, "percent": t.percent} for t in topic_rank[:5]],
        highlights=[{"label": h.label, "value": h.value, "desc": h.desc} for h in highlights],
    )

    # 生成图表解读文字
    analysis_texts_data = _generate_analysis_texts(
        overview={"browse_count": browse_count, "favorite_count": favorite_count, "comment_count": comment_count, "ai_count": ai_count, "active_days": active_days},
        scores={"reading": reading_score, "collecting": collect_score, "interaction": interaction_score, "ai_usage": ai_score},
        daily_summary={"most_active_date": max_date, "max_daily_count": max_count},
        topic_rank=topic_rank,
        active_days=active_days,
    )
    analysis_texts = AnalysisTexts(
        profile_analysis=analysis_texts_data["profile_analysis"],
        behavior_analysis=analysis_texts_data["behavior_analysis"],
        activity_analysis=analysis_texts_data["activity_analysis"],
        topic_analysis=analysis_texts_data["topic_analysis"],
    )

    # 生成叙事化高光
    narrative_highlights = _build_narrative_highlights(
        overview={"browse_count": browse_count, "favorite_count": favorite_count, "comment_count": comment_count, "ai_count": ai_count, "active_days": active_days},
        daily_summary={"most_active_date": max_date, "max_daily_count": max_count},
        topic_rank=topic_rank,
        highlights=highlights,
    )

    return WeeklyReportResponse(
        range=WeeklyReportRange(days=7, start_date=start_date_str, end_date=end_date_str),
        persona=WeeklyReportPersona(title=persona_title, description=persona_desc),
        summary=ai_analysis.summary if ai_analysis.enabled else summary_text,
        overview=WeeklyReportOverview(
            browse_count=browse_count, favorite_count=favorite_count,
            comment_count=comment_count, ai_count=ai_count, active_days=active_days,
        ),
        behavior_scores=WeeklyReportScores(
            reading=reading_score, collecting=collect_score,
            interaction=interaction_score, ai_usage=ai_score,
        ),
        daily_activity=[DailyActivityItem(date=d["date"], count=d["count"]) for d in daily_list],
        topic_rank=topic_rank,
        highlights=[
            WeeklyReportHighlight(icon=h["icon"], label=h["label"], value=h["value"], desc=h["desc"], narrative=h["narrative"])
            for h in narrative_highlights
        ],
        ai_analysis=ai_analysis,
        analysis_texts=analysis_texts,
        empty=False,
    )
