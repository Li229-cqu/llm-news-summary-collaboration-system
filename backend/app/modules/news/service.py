"""新闻模块服务层：只读取数据库，避免新闻数据与 mock 混用。"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional, Tuple

from app.common.exceptions import AppException
from app.common.utils import format_datetime, normalize_text, paginate
from app.db.database import execute_one, execute_query, execute_update

logger = logging.getLogger(__name__)

_NEWS_SOURCE_URL_EXISTS: Optional[bool] = None
_NEWS_FULLTEXT_INDEX_EXISTS: Optional[bool] = None


def _news_has_fulltext_index() -> bool:
    global _NEWS_FULLTEXT_INDEX_EXISTS
    if _NEWS_FULLTEXT_INDEX_EXISTS is None:
        try:
            row = execute_one(
                """
                SELECT COUNT(*) AS total
                FROM information_schema.STATISTICS
                WHERE TABLE_SCHEMA = DATABASE()
                  AND TABLE_NAME = 'news'
                  AND INDEX_TYPE = 'FULLTEXT'
                  AND INDEX_NAME = 'ft_news_search'
                """
            )
            _NEWS_FULLTEXT_INDEX_EXISTS = int((row or {}).get("total") or 0) > 0
        except Exception:  # noqa: BLE001
            _NEWS_FULLTEXT_INDEX_EXISTS = False
    return _NEWS_FULLTEXT_INDEX_EXISTS


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



def _news_source_url_select() -> str:
    """Return a compatible SELECT expression for optional news.source_url."""
    global _NEWS_SOURCE_URL_EXISTS
    if _NEWS_SOURCE_URL_EXISTS is None:
        try:
            row = execute_one(
                """
                SELECT COUNT(*) AS total
                FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                  AND TABLE_NAME = 'news'
                  AND COLUMN_NAME = 'source_url'
                """
            )
            _NEWS_SOURCE_URL_EXISTS = int((row or {}).get("total") or 0) > 0
        except Exception as exc:  # noqa: BLE001
            logger.warning("检查 news.source_url 字段失败，按不存在处理：%s", exc)
            _NEWS_SOURCE_URL_EXISTS = False
    return "n.source_url" if _NEWS_SOURCE_URL_EXISTS else "'' AS source_url"


def _format_news_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": int(row.get("id") or 0),
        "title": normalize_text(row.get("title")),
        "summary": normalize_text(row.get("summary")),
        "content": normalize_text(row.get("content")),
        "cover_image": normalize_text(row.get("cover_image")),
        "category_id": int(row.get("category_id") or 0),
        "category_name": normalize_text(row.get("category_name")) or "未分类",
        "topic_id": row.get("topic_id"),
        "source": normalize_text(row.get("source")),
        "editor": normalize_text(row.get("editor")),
        "publish_time": format_datetime(row.get("publish_time")),
        "view_count": int(row.get("view_count") or 0),
        "like_count": int(row.get("like_count") or 0),
        "comment_count": int(row.get("comment_count") or 0),
        "favorite_count": int(row.get("favorite_count") or 0),
        "status": int(row.get("status") or 0),
        "tags": _parse_json_field(row.get("tags"), default=[]),
        "source_url": normalize_text(row.get("source_url")),
    }


def _format_category_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": int(row.get("id") or 0),
        "name": normalize_text(row.get("name")),
        "code": normalize_text(row.get("code")),
        "sort": int(row.get("sort") or 0),
        "status": int(row.get("status") or 0),
    }


def _format_hot_row(row: dict[str, Any], rank: int) -> dict[str, Any]:
    return {
        "id": int(row.get("id") or 0),
        "title": normalize_text(row.get("title")),
        "category_name": normalize_text(row.get("category_name")) or "未分类",
        "source": normalize_text(row.get("source")),
        "view_count": int(row.get("view_count") or 0),
        "comment_count": int(row.get("comment_count") or 0),
        "like_count": int(row.get("like_count") or 0),
        "favorite_count": int(row.get("favorite_count") or 0),
        "cover_image": normalize_text(row.get("cover_image")),
        "publish_time": format_datetime(row.get("publish_time")),
        "heat_score": int(row.get("heat_score") or 0),
        "rank": rank,
    }




def _db_categories() -> list[dict[str, Any]]:
    rows = execute_query(
        """
        SELECT id, name, code, sort, status
        FROM news_category
        WHERE status = 1
        ORDER BY sort ASC, id ASC
        """
    )
    return [_format_category_row(row) for row in rows]


def _db_news_filters(
    category: Optional[str] = None,
    category_id: Optional[int] = None,
    keyword: Optional[str] = None,
) -> tuple[str, list[Any]]:
    clauses = ["n.status = 1"]
    params: list[Any] = []

    normalized_category = (category or "").strip()
    if category_id is not None:
        clauses.append("n.category_id = %s")
        params.append(category_id)
    elif normalized_category:
        if normalized_category.isdigit():
            clauses.append("n.category_id = %s")
            params.append(int(normalized_category))
        else:
            clauses.append("(LOWER(COALESCE(nc.code, '')) = LOWER(%s) OR LOWER(COALESCE(nc.name, '')) = LOWER(%s))")
            params.extend([normalized_category, normalized_category])

    normalized_keyword = (keyword or "").strip()
    if normalized_keyword:
        if _news_has_fulltext_index() and len(normalized_keyword) >= 2:
            clauses.append("MATCH(n.title, n.summary, n.content) AGAINST(%s IN BOOLEAN MODE)")
            params.append(normalized_keyword)
        else:
            like_value = f"%{normalized_keyword}%"
            clauses.append(
                "(n.title LIKE %s OR n.summary LIKE %s OR n.content LIKE %s OR COALESCE(nc.name, '') LIKE %s OR COALESCE(nc.code, '') LIKE %s)"
            )
            params.extend([like_value, like_value, like_value, like_value, like_value])

    return " AND ".join(clauses), params


def _db_news_count(
    category: Optional[str] = None,
    category_id: Optional[int] = None,
    keyword: Optional[str] = None,
) -> int:
    where_sql, params = _db_news_filters(category=category, category_id=category_id, keyword=keyword)
    row = execute_one(
        f"""
        SELECT COUNT(*) AS total
        FROM news n
        LEFT JOIN news_category nc ON nc.id = n.category_id
        WHERE {where_sql}
        """,
        params,
    )
    return int((row or {}).get("total") or 0)


def _db_news_list(
    category: Optional[str] = None,
    category_id: Optional[int] = None,
    keyword: Optional[str] = None,
    page: int = 1,
    page_size: int = 10,
) -> dict[str, Any]:
    normalized_page = max(page, 1)
    normalized_page_size = max(page_size, 1)
    where_sql, params = _db_news_filters(category=category, category_id=category_id, keyword=keyword)
    total = _db_news_count(category=category, category_id=category_id, keyword=keyword)
    rows = execute_query(
        f"""
        SELECT
            n.id,
            n.title,
            n.summary,
            n.content,
            n.cover_image,
            n.category_id,
            COALESCE(nc.name, '未分类') AS category_name,
            n.topic_id,
            n.source,
            n.editor,
            n.publish_time,
            n.view_count,
            n.like_count,
            n.comment_count,
            n.favorite_count,
            n.status,
            n.tags,
            {_news_source_url_select()}
        FROM news n
        LEFT JOIN news_category nc ON nc.id = n.category_id
        WHERE {where_sql}
        ORDER BY n.publish_time DESC, n.id DESC
        LIMIT %s OFFSET %s
        """,
        params + [normalized_page_size, (normalized_page - 1) * normalized_page_size],
    )
    items = [_format_news_row(row) for row in rows]
    return {
        "list": items,
        "total": total,
        "page": normalized_page,
        "page_size": normalized_page_size,
    }

def _db_subscribed_news(
    current_user: Optional[Any],
    page: int = 1,
    page_size: int = 10,
) -> dict[str, Any]:
    current_user_id = _get_current_user_id(current_user)
    if current_user_id is None:
        raise AppException(code=401, message="请先登录后查看订阅新闻")

    normalized_page = max(page, 1)
    normalized_page_size = max(page_size, 1)
    subscription_count = execute_one(
        """
        SELECT COUNT(*) AS total
        FROM user_category_subscription
        WHERE user_id = %s
        """,
        [current_user_id],
    )
    if int((subscription_count or {}).get("total") or 0) == 0:
        return {
            "list": [],
            "total": 0,
            "page": normalized_page,
            "page_size": normalized_page_size,
        }

    total_row = execute_one(
        """
        SELECT COUNT(*) AS total
        FROM news n
        INNER JOIN user_category_subscription ucs
          ON ucs.category_id = n.category_id AND ucs.user_id = %s
        WHERE n.status = 1
        """,
        [current_user_id],
    )
    total = int((total_row or {}).get("total") or 0)
    rows = execute_query(
        f"""
        SELECT
            n.id,
            n.title,
            n.summary,
            n.content,
            n.cover_image,
            n.category_id,
            COALESCE(nc.name, '未分类') AS category_name,
            n.topic_id,
            n.source,
            n.editor,
            n.publish_time,
            n.view_count,
            n.like_count,
            n.comment_count,
            n.favorite_count,
            n.status,
            n.tags,
            {_news_source_url_select()}
        FROM news n
        INNER JOIN user_category_subscription ucs
          ON ucs.category_id = n.category_id AND ucs.user_id = %s
        LEFT JOIN news_category nc ON nc.id = n.category_id
        WHERE n.status = 1
        ORDER BY n.publish_time DESC, n.updated_at DESC, n.id DESC
        LIMIT %s OFFSET %s
        """,
        [current_user_id, normalized_page_size, (normalized_page - 1) * normalized_page_size],
    )
    return {
        "list": [_format_news_row(row) for row in rows],
        "total": total,
        "page": normalized_page,
        "page_size": normalized_page_size,
    }

def _db_hot_news(limit: int = 10) -> list[dict[str, Any]]:
    normalized_limit = max(limit, 0)
    if normalized_limit == 0:
        return []
    rows = execute_query(
        """
        SELECT
            n.id,
            n.title,
            n.cover_image,
            COALESCE(nc.name, '未分类') AS category_name,
            n.source,
            n.view_count,
            n.comment_count,
            n.like_count,
            n.favorite_count,
            n.publish_time,
            (
                COALESCE(n.view_count, 0)
                + COALESCE(n.like_count, 0) * 5
                + COALESCE(n.favorite_count, 0) * 4
                + COALESCE(n.comment_count, 0) * 6
            ) AS heat_score
        FROM news n
        LEFT JOIN news_category nc ON nc.id = n.category_id
        WHERE n.status = 1
        ORDER BY heat_score DESC,
                 n.view_count DESC,
                 n.like_count DESC,
                 n.favorite_count DESC,
                 n.comment_count DESC,
                 n.publish_time DESC,
                 n.id DESC
        LIMIT %s
        """,
        [normalized_limit],
    )
    return [
        _format_hot_row(row, rank=index)
        for index, row in enumerate(rows, start=1)
    ]

def _db_news_detail(news_id: int, current_user: Optional[Any] = None) -> dict[str, Any] | None:
    news = execute_one(
        f"""
        SELECT
            n.id,
            n.title,
            n.summary,
            n.content,
            n.cover_image,
            n.category_id,
            COALESCE(nc.name, '未分类') AS category_name,
            n.topic_id,
            n.source,
            n.editor,
            n.publish_time,
            n.view_count,
            n.like_count,
            n.comment_count,
            n.favorite_count,
            n.status,
            n.tags,
            {_news_source_url_select()}
        FROM news n
        LEFT JOIN news_category nc ON nc.id = n.category_id
        WHERE n.id = %s AND n.status = 1
        LIMIT 1
        """,
        [news_id],
    )
    if news is None:
        return None

    topic_id = news.get("topic_id")
    timeline_news_count = 0
    if topic_id is not None:
        count_row = execute_one(
            "SELECT COUNT(*) AS total FROM news WHERE topic_id = %s AND status = 1",
            [topic_id],
        )
        timeline_news_count = int((count_row or {}).get("total") or 0)

    current_user_id = _get_current_user_id(current_user)
    related_rows = execute_query(
        f"""
        SELECT
            n.id,
            n.title,
            n.summary,
            n.content,
            n.cover_image,
            n.category_id,
            COALESCE(nc.name, '未分类') AS category_name,
            n.topic_id,
            n.source,
            n.editor,
            n.publish_time,
            n.view_count,
            n.like_count,
            n.comment_count,
            n.favorite_count,
            n.status,
            n.tags,
            {_news_source_url_select()}
        FROM news n
        LEFT JOIN news_category nc ON nc.id = n.category_id
        WHERE n.status = 1 AND n.category_id = %s AND n.id <> %s
        ORDER BY n.publish_time DESC, n.id DESC
        LIMIT 3
        """,
        [news.get("category_id"), news_id],
    )
    # Build recommended_news with 3-tier fallback: same topic → same category → hot
    _RECOMMEND_SELECT = f"""
        SELECT
            n.id,
            n.title,
            n.summary,
            n.content,
            n.cover_image,
            n.category_id,
            COALESCE(nc.name, '未分类') AS category_name,
            n.topic_id,
            n.source,
            n.editor,
            n.publish_time,
            n.view_count,
            n.like_count,
            n.comment_count,
            n.favorite_count,
            n.status,
            n.tags,
            {_news_source_url_select()}
        FROM news n
        LEFT JOIN news_category nc ON nc.id = n.category_id
        WHERE n.status = 1
    """
    _RECOMMEND_ORDER = "ORDER BY n.view_count DESC, n.comment_count DESC, n.like_count DESC, n.publish_time DESC, n.id DESC"

    recommended_news: list[dict[str, Any]] = []
    used_ids: set[int] = {news_id}

    category_id = news.get("category_id")
    if topic_id is not None:
        topic_rows = execute_query(
            _RECOMMEND_SELECT + " AND n.topic_id = %s AND n.id <> %s " + _RECOMMEND_ORDER + " LIMIT 5",
            [topic_id, news_id],
        )
        for row in topic_rows:
            row_id = int(row["id"])
            if row_id not in used_ids:
                item = _format_news_row(row)
                item["recommend_source"] = "related"
                recommended_news.append(item)
                used_ids.add(row_id)
        logger.info("[recommended_news] same topic_id=%d: got %d items", topic_id, len(recommended_news))

    if len(recommended_news) < 5 and category_id is not None:
        remaining = 5 - len(recommended_news)
        exclude_ids = list(used_ids)
        placeholders = ",".join(["%s"] * len(exclude_ids))
        category_rows = execute_query(
            _RECOMMEND_SELECT + f" AND n.category_id = %s AND n.id NOT IN ({placeholders}) " + _RECOMMEND_ORDER + f" LIMIT {remaining}",
            [category_id] + exclude_ids,
        )
        for row in category_rows:
            item = _format_news_row(row)
            item["recommend_source"] = "related"
            recommended_news.append(item)
            used_ids.add(int(row["id"]))
        logger.info("[recommended_news] same category_id=%d: got %d items (total=%d)", category_id, len(category_rows), len(recommended_news))

    if len(recommended_news) < 5:
        remaining = 5 - len(recommended_news)
        exclude_ids = list(used_ids)
        placeholders = ",".join(["%s"] * len(exclude_ids))
        hot_rows = execute_query(
            _RECOMMEND_SELECT + f" AND n.id NOT IN ({placeholders}) " + _RECOMMEND_ORDER + f" LIMIT {remaining}",
            exclude_ids,
        )
        for row in hot_rows:
            item = _format_news_row(row)
            item["recommend_source"] = "hot"
            recommended_news.append(item)
        logger.info("[recommended_news] hot fallback: got %d items (total=%d)", len(hot_rows), len(recommended_news))

    detail = _format_news_row(news)
    detail["content"] = normalize_text(news.get("content"))
    detail["related_news"] = [_format_news_row(row) for row in related_rows]
    detail["recommended_news"] = recommended_news

    if current_user_id is None:
        detail["is_liked"] = False
        detail["is_favorited"] = False
    else:
        liked = execute_one(
            """
            SELECT id
            FROM user_like
            WHERE user_id = %s AND target_id = %s AND target_type = 'news'
            LIMIT 1
            """,
            [current_user_id, news_id],
        )
        favorited = execute_one(
            """
            SELECT id
            FROM favorite
            WHERE user_id = %s AND target_id = %s AND target_type = 'news'
            LIMIT 1
            """,
            [current_user_id, news_id],
        )
        detail["is_liked"] = liked is not None
        detail["is_favorited"] = favorited is not None

    detail["timeline_news_count"] = timeline_news_count

    execute_update("UPDATE news SET view_count = view_count + 1, updated_at = NOW() WHERE id = %s", [news_id])
    detail["view_count"] = int(detail.get("view_count") or 0) + 1

    return detail


def _db_record_browse(news_id: int, current_user: Optional[Any] = None) -> dict[str, Any] | None:
    news = execute_one(
        "SELECT id, view_count FROM news WHERE id = %s AND status = 1 LIMIT 1",
        [news_id],
    )
    if news is None:
        return None

    current_user_id = _get_current_user_id(current_user)
    if current_user_id is not None:
        try:
            existing = execute_one(
                """
                SELECT id FROM browse_history
                WHERE user_id = %s
                  AND news_id = %s
                  AND (target_type = 'news' OR target_type IS NULL OR target_type = '')
                LIMIT 1
                """,
                [current_user_id, news_id],
            )
            if existing:
                execute_update(
                    """
                    UPDATE browse_history
                    SET browse_time = NOW(), target_type = 'news', target_id = %s
                    WHERE id = %s
                    """,
                    [news_id, int(existing["id"])],
                )
            else:
                execute_update(
                    """
                    INSERT INTO browse_history (user_id, news_id, target_type, target_id, browse_time, created_at)
                    VALUES (%s, %s, 'news', %s, NOW(), NOW())
                    """,
                    [current_user_id, news_id, news_id],
                )
        except Exception as exc:  # noqa: BLE001
            logger.warning("写入浏览历史失败，已忽略：%s", exc)

    return {"news_id": news_id, "recorded": True}


def get_categories() -> list[dict[str, Any]]:
    """获取新闻分类，只读取数据库。"""
    return _db_categories()


def get_news_list(
    category: Optional[str] = None,
    keyword: Optional[str] = None,
    page: int = 1,
    page_size: int = 10,
    category_id: Optional[int] = None,
) -> dict[str, Any]:
    """获取新闻列表，只读取数据库。"""
    return _db_news_list(
        category=category,
        category_id=category_id,
        keyword=keyword,
        page=page,
        page_size=page_size,
    )

def get_subscribed_news(
    current_user: Optional[Any],
    page: int = 1,
    page_size: int = 10,
) -> dict[str, Any]:
    """获取当前登录用户订阅分类下的新闻，只读取数据库。"""
    return _db_subscribed_news(current_user=current_user, page=page, page_size=page_size)

def get_hot_news(limit: int = 10) -> list[dict[str, Any]]:
    """获取新闻热榜，只读取数据库。"""
    rows = _db_hot_news(limit=limit)
    return rows or []


def search_news(keyword: Optional[str], page: int = 1, page_size: int = 10) -> dict[str, Any]:
    """搜索新闻，只读取数据库。"""
    if not keyword or not keyword.strip():
        return paginate([], page=page, page_size=page_size)
    return _db_news_list(keyword=keyword, page=page, page_size=page_size)


def get_news_detail(news_id: int, current_user: Optional[Any] = None) -> dict[str, Any]:
    """获取新闻详情，只读取数据库。"""
    detail = _db_news_detail(news_id=news_id, current_user=current_user)
    if detail is not None:
        return detail
    raise AppException(code=404, message="新闻不存在")


def record_browse(news_id: int, current_user: Optional[Any] = None) -> dict[str, Any]:
    """记录浏览行为，只读取数据库。"""
    result = _db_record_browse(news_id=news_id, current_user=current_user)
    if result is not None:
        return result
    raise AppException(code=404, message="新闻不存在")
