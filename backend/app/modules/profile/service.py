"""个人中心模块服务层：数据库优先，mock 兜底。

当前阶段优先读取 MySQL 中的 browse_history、favorite、news_comment、
ai_generate_record 等表；当数据库不可用或尚未同步数据时，自动回退到
进程内 mock 数据，保证页面和演示流程可用。
"""

from __future__ import annotations

import json
import logging
import math
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from app.common.utils import format_datetime, normalize_text, paginate
from app.db.database import execute_one, execute_query, execute_update
from app.mock.ai_records import MOCK_AI_RECORDS
from app.mock.comments import MOCK_NEWS_COMMENTS
from app.mock.news import MOCK_BROWSE_HISTORY, MOCK_NEWS, MOCK_NEWS_FAVORITES, NEWS_CATEGORIES
from app.modules.profile.schema import (
    AIRecordItem,
    BrowseHistoryItem,
    CommentRecordItem,
    FavoriteItem,
    ProfileOverview,
    ProfileTestData,
    SubscriptionCategory,
    SubscriptionResponse,
    SubscriptionUpdateRequest,
)

logger = logging.getLogger(__name__)


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

    browse_row = execute_one(
        "SELECT COUNT(*) AS total FROM browse_history WHERE user_id = %s",
        [user_id],
    )
    favorite_row = execute_one(
        """
        SELECT COUNT(*) AS total
        FROM favorite
        WHERE user_id = %s AND target_type = 'news'
        """,
        [user_id],
    )
    comment_row = execute_one(
        """
        SELECT COUNT(*) AS total
        FROM news_comment
        WHERE user_id = %s AND status <> 4
        """,
        [user_id],
    )
    ai_row = execute_one(
        """
        SELECT COUNT(*) AS total
        FROM ai_generate_record
        WHERE user_id = %s AND status = 1
        """,
        [user_id],
    )

    counts = [
        int((browse_row or {}).get("total") or 0),
        int((favorite_row or {}).get("total") or 0),
        int((comment_row or {}).get("total") or 0),
        int((ai_row or {}).get("total") or 0),
    ]
    if not any(counts):
        return None

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
) -> Dict[str, Any]:
    user_id = _get_current_user_id(current_user)
    if user_id is None:
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

    rows = execute_query(
        """
        SELECT
            bh.news_id,
            n.title,
            COALESCE(nc.name, '未分类') AS category_name,
            bh.browse_time
        FROM browse_history bh
        LEFT JOIN news n ON n.id = bh.news_id
        LEFT JOIN news_category nc ON nc.id = n.category_id
        WHERE bh.user_id = %s
        ORDER BY bh.browse_time DESC, bh.id DESC
        """,
        [user_id],
    )
    if not rows:
        return None

    history_items = []
    for row in rows:
        history_items.append(
            BrowseHistoryItem(
                news_id=int(row["news_id"]),
                title=normalize_text(row["title"]),
                category_name=normalize_text(row["category_name"]),
                browse_time=format_datetime(row["browse_time"]),
            ).dict()
        )

    return paginate(history_items, page=page, page_size=page_size)


def get_browse_history(
    current_user: Optional[Any] = None, page: int = 1, page_size: int = 10
) -> Dict[str, Any]:
    """获取用户浏览历史。"""

    try:
        result = _db_browse_history(current_user, page=page, page_size=page_size)
        if result is not None:
            return result
    except Exception as exc:  # noqa: BLE001
        logger.warning("读取浏览历史失败，回退 mock：%s", exc)
    return _mock_browse_history(current_user, page=page, page_size=page_size)


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
                ).dict()
            )

    favorite_items.sort(key=lambda x: x["publish_time"], reverse=True)
    return paginate(favorite_items, page=page, page_size=page_size)


def _db_favorites(
    current_user: Optional[Any] = None, page: int = 1, page_size: int = 10
) -> Dict[str, Any] | None:
    user_id = _get_current_user_id(current_user)
    if user_id is None:
        return paginate([], page=page, page_size=page_size)

    rows = execute_query(
        """
        SELECT
            n.id AS news_id,
            n.title,
            n.summary,
            COALESCE(nc.name, '未分类') AS category_name,
            n.source,
            n.publish_time
        FROM favorite f
        LEFT JOIN news n ON n.id = f.target_id
        LEFT JOIN news_category nc ON nc.id = n.category_id
        WHERE f.user_id = %s
          AND f.target_type = 'news'
          AND n.status = 1
        ORDER BY n.publish_time DESC, f.id DESC
        """,
        [user_id],
    )
    if not rows:
        return None

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
            ).dict()
        )

    return paginate(favorite_items, page=page, page_size=page_size)


def get_favorites(
    current_user: Optional[Any] = None, page: int = 1, page_size: int = 10
) -> Dict[str, Any]:
    """获取用户收藏列表。"""

    try:
        result = _db_favorites(current_user, page=page, page_size=page_size)
        if result is not None:
            return result
    except Exception as exc:  # noqa: BLE001
        logger.warning("读取收藏列表失败，回退 mock：%s", exc)
    return _mock_favorites(current_user, page=page, page_size=page_size)


def _mock_comments(
    current_user: Optional[Any] = None,
    page: int = 1,
    page_size: int = 10,
) -> Dict[str, Any]:
    user_id = _get_current_user_id(current_user)
    if user_id is None:
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
            c.create_time
        FROM news_comment c
        LEFT JOIN news n ON n.id = c.news_id
        LEFT JOIN news_category nc ON nc.id = n.category_id
        WHERE c.user_id = %s AND c.status <> 4
        ORDER BY c.create_time DESC, c.id DESC
        """,
        [user_id],
    )
    if not rows:
        return None

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


def get_comments(
    current_user: Optional[Any] = None,
    page: int = 1,
    page_size: int = 10,
) -> Dict[str, Any]:
    """获取用户评论记录。"""

    try:
        result = _db_comments(current_user, page=page, page_size=page_size)
        if result is not None:
            return result
    except Exception as exc:  # noqa: BLE001
        logger.warning("读取评论记录失败，回退 mock：%s", exc)
    return _mock_comments(current_user, page=page, page_size=page_size)


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
                source=record.get("source", "manual"),
                source_news_id=record.get("source_news_id"),
                source_title=record.get("source_title", ""),
                input_text=record["input_text"],
                candidate_titles=result.get("candidate_titles", []),
                summary_short=result.get("summary_short", ""),
                summary_long=result.get("summary_long"),
                risk_level=record.get("risk_level", result.get("consistency", {}).get("risk_level", "low")),
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
        return None

    record_items = []
    for row in rows:
        record_items.append(
            AIRecordItem(
                id=int(row["id"]),
                source=normalize_text(row.get("source")) or "manual",
                source_news_id=row.get("source_news_id"),
                source_title=normalize_text(row.get("source_title")),
                input_text=normalize_text(row["input_text"]),
                candidate_titles=_parse_json_field(row.get("candidate_titles"), default=[]),
                summary_short=normalize_text(row.get("summary_short")),
                summary_long=normalize_text(row.get("summary_long")) or None,
                risk_level=normalize_text(row.get("risk_level")) or "low",
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
        if result is not None and result.get("list"):
            return result
    except Exception as exc:
        logger.warning("数据库推荐查询异常，回退 mock：%s", exc)

    return _mock_recommendations(limit=limit)
