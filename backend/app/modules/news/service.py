"""新闻模块服务层：DB 优先，mock 兜底。"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any, Optional

from app.common.exceptions import AppException
from app.db.database import execute_one, execute_query, execute_update
from app.mock.news import (
    MOCK_BROWSE_HISTORY,
    MOCK_NEWS,
    MOCK_NEWS_FAVORITES,
    MOCK_NEWS_LIKES,
    NEWS_CATEGORIES,
)

logger = logging.getLogger(__name__)

_NEWS_SOURCE_URL_EXISTS: Optional[bool] = None


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


def _format_datetime(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    if hasattr(value, "strftime"):
        try:
            return value.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:  # noqa: BLE001
            return str(value)
    return str(value)


def _normalize_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


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
        "title": _normalize_text(row.get("title")),
        "summary": _normalize_text(row.get("summary")),
        "content": _normalize_text(row.get("content")),
        "cover_image": _normalize_text(row.get("cover_image")),
        "category_id": int(row.get("category_id") or 0),
        "category_name": _normalize_text(row.get("category_name")) or "未分类",
        "topic_id": row.get("topic_id"),
        "source": _normalize_text(row.get("source")),
        "editor": _normalize_text(row.get("editor")),
        "publish_time": _format_datetime(row.get("publish_time")),
        "view_count": int(row.get("view_count") or 0),
        "like_count": int(row.get("like_count") or 0),
        "comment_count": int(row.get("comment_count") or 0),
        "favorite_count": int(row.get("favorite_count") or 0),
        "status": int(row.get("status") or 0),
        "tags": _parse_json_field(row.get("tags"), default=[]),
        "source_url": _normalize_text(row.get("source_url")),
    }


def _format_category_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": int(row.get("id") or 0),
        "name": _normalize_text(row.get("name")),
        "code": _normalize_text(row.get("code")),
        "sort": int(row.get("sort") or 0),
        "status": int(row.get("status") or 0),
    }


def _format_hot_row(row: dict[str, Any], rank: int) -> dict[str, Any]:
    return {
        "id": int(row.get("id") or 0),
        "title": _normalize_text(row.get("title")),
        "category_name": _normalize_text(row.get("category_name")) or "未分类",
        "source": _normalize_text(row.get("source")),
        "view_count": int(row.get("view_count") or 0),
        "comment_count": int(row.get("comment_count") or 0),
        "like_count": int(row.get("like_count") or 0),
        "favorite_count": int(row.get("favorite_count") or 0),
        "cover_image": _normalize_text(row.get("cover_image")),
        "publish_time": _format_datetime(row.get("publish_time")),
        "heat_score": int(row.get("heat_score") or 0),
        "rank": rank,
    }


def _paginate(items: list[dict[str, Any]], page: int, page_size: int) -> dict[str, Any]:
    normalized_page = max(page, 1)
    normalized_page_size = max(page_size, 1)
    total = len(items)
    start = (normalized_page - 1) * normalized_page_size
    end = start + normalized_page_size
    return {
        "list": items[start:end],
        "total": total,
        "page": normalized_page,
        "page_size": normalized_page_size,
    }


def _mock_categories() -> list[dict[str, Any]]:
    return sorted(
        (_format_category_row(dict(item)) for item in NEWS_CATEGORIES if item.get("status") == 1),
        key=lambda item: (item["sort"], item["id"]),
    )


def _mock_news_rows() -> list[dict[str, Any]]:
    return [_format_news_row(dict(item)) for item in MOCK_NEWS if item.get("status") == 1]


def _mock_get_categories() -> list[dict[str, Any]]:
    return _mock_categories()


def _mock_get_news_list(
    category: Optional[str] = None,
    category_id: Optional[int] = None,
    keyword: Optional[str] = None,
    page: int = 1,
    page_size: int = 10,
) -> dict[str, Any]:
    items = _mock_news_rows()

    if category_id is not None:
        items = [item for item in items if item["category_id"] == category_id]
    else:
        normalized_category = (category or "").strip().casefold()
        if normalized_category:
            items = [
                item
                for item in items
                if item["category_name"].casefold() == normalized_category
                or any(
                    cat["id"] == item["category_id"]
                    and (cat["code"].casefold() == normalized_category or cat["name"].casefold() == normalized_category)
                    for cat in NEWS_CATEGORIES
                )
            ]

    normalized_keyword = (keyword or "").strip().casefold()
    if normalized_keyword:
        items = [
            item
            for item in items
            if normalized_keyword in item["title"].casefold()
            or normalized_keyword in item["summary"].casefold()
            or normalized_keyword in item["content"].casefold()
            or normalized_keyword in item["category_name"].casefold()
            or any(normalized_keyword in tag.casefold() for tag in item["tags"])
        ]

    items.sort(key=lambda item: (item["publish_time"], item["id"]), reverse=True)
    return _paginate(items, page=page, page_size=page_size)


def _mock_get_hot_news(limit: int = 10) -> list[dict[str, Any]]:
    items = _mock_news_rows()
    items.sort(
        key=lambda item: (
            item["view_count"] + item["like_count"] * 5 + item["favorite_count"] * 4 + item["comment_count"] * 6,
            item["view_count"],
            item["like_count"],
            item["favorite_count"],
            item["comment_count"],
            item["publish_time"],
            item["id"],
        ),
        reverse=True,
    )
    return [
        {
            "id": item["id"],
            "title": item["title"],
            "category_name": item["category_name"],
            "source": item["source"],
            "view_count": item["view_count"],
            "comment_count": item["comment_count"],
            "like_count": item["like_count"],
            "favorite_count": item["favorite_count"],
            "cover_image": item.get("cover_image", ""),
            "publish_time": item["publish_time"],
            "heat_score": item["view_count"] + item["like_count"] * 5 + item["favorite_count"] * 4 + item["comment_count"] * 6,
            "rank": index,
        }
        for index, item in enumerate(items[: max(limit, 0)], start=1)
    ]


def _find_mock_news_by_id(news_id: int) -> dict[str, Any] | None:
    for item in MOCK_NEWS:
        if int(item.get("id") or 0) == news_id and int(item.get("status") or 0) == 1:
            return _format_news_row(dict(item))
    return None


def _mock_get_news_detail(news_id: int, current_user: Optional[Any] = None) -> dict[str, Any]:
    news = _find_mock_news_by_id(news_id)
    if news is None:
        raise AppException(code=404, message="新闻不存在")

    current_user_id = _get_current_user_id(current_user)
    related_news = [
        _format_news_row(dict(item))
        for item in MOCK_NEWS
        if item.get("status") == 1
        and int(item.get("category_id") or 0) == news["category_id"]
        and int(item.get("id") or 0) != news["id"]
    ][:3]
    recommended_news = [
        _format_news_row(dict(item))
        for item in sorted(
            (
                item
                for item in MOCK_NEWS
                if item.get("status") == 1 and int(item.get("id") or 0) != news["id"]
            ),
            key=lambda item: int(item.get("view_count") or 0),
            reverse=True,
        )[:5]
    ]
    detail = dict(news)
    detail["related_news"] = related_news
    detail["recommended_news"] = recommended_news
    detail["is_liked"] = current_user_id is not None and any(
        like["user_id"] == current_user_id and like["news_id"] == news_id for like in MOCK_NEWS_LIKES
    )
    detail["is_favorited"] = current_user_id is not None and any(
        fav["user_id"] == current_user_id and fav["news_id"] == news_id for fav in MOCK_NEWS_FAVORITES
    )
    return detail


def _mock_record_browse(news_id: int, current_user: Optional[Any] = None) -> dict[str, Any]:
    news = _find_mock_news_by_id(news_id)
    if news is None:
        raise AppException(code=404, message="新闻不存在")

    for item in MOCK_NEWS:
        if int(item.get("id") or 0) == news_id:
            item["view_count"] = int(item.get("view_count") or 0) + 1
            break

    current_user_id = _get_current_user_id(current_user)
    if current_user_id is not None:
        MOCK_BROWSE_HISTORY.append(
            {
                "user_id": current_user_id,
                "news_id": news_id,
                "browse_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
        )

    return {"news_id": news_id, "recorded": True}


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
    recommended_rows = execute_query(
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
        WHERE n.status = 1 AND n.id <> %s
        ORDER BY n.view_count DESC, n.comment_count DESC, n.like_count DESC, n.publish_time DESC, n.id DESC
        LIMIT 5
        """,
        [news_id],
    )

    detail = _format_news_row(news)
    detail["content"] = _normalize_text(news.get("content"))
    detail["related_news"] = [_format_news_row(row) for row in related_rows]
    detail["recommended_news"] = [_format_news_row(row) for row in recommended_rows]

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

    return detail


def _db_record_browse(news_id: int, current_user: Optional[Any] = None) -> dict[str, Any] | None:
    news = execute_one(
        "SELECT id, view_count FROM news WHERE id = %s AND status = 1 LIMIT 1",
        [news_id],
    )
    if news is None:
        return None

    execute_update("UPDATE news SET view_count = view_count + 1, update_time = NOW() WHERE id = %s", [news_id])

    current_user_id = _get_current_user_id(current_user)
    if current_user_id is not None:
        try:
            execute_update(
                """
                INSERT INTO browse_history (user_id, news_id, browse_time, create_time)
                VALUES (%s, %s, NOW(), NOW())
                """,
                [current_user_id, news_id],
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("写入浏览历史失败，已忽略：%s", exc)

    return {"news_id": news_id, "recorded": True}


def get_categories() -> list[dict[str, Any]]:
    """获取新闻分类，优先数据库，失败时回退 mock。"""
    try:
        rows = _db_categories()
        if rows:
            return rows
    except Exception as exc:  # noqa: BLE001
        logger.warning("读取新闻分类失败，回退 mock：%s", exc)
    return _mock_get_categories()


def get_news_list(
    category: Optional[str] = None,
    keyword: Optional[str] = None,
    page: int = 1,
    page_size: int = 10,
    category_id: Optional[int] = None,
) -> dict[str, Any]:
    """获取新闻列表，优先数据库，必要时回退 mock。"""
    try:
        result = _db_news_list(
            category=category,
            category_id=category_id,
            keyword=keyword,
            page=page,
            page_size=page_size,
        )
        if result["list"]:
            return result
        if not (category or category_id or (keyword or "").strip()):
            return _mock_get_news_list(category=category, category_id=category_id, keyword=keyword, page=page, page_size=page_size)
        return result
    except Exception as exc:  # noqa: BLE001
        logger.warning("读取新闻列表失败，回退 mock：%s", exc)
        return _mock_get_news_list(category=category, category_id=category_id, keyword=keyword, page=page, page_size=page_size)


def get_hot_news(limit: int = 10) -> list[dict[str, Any]]:
    """获取新闻热榜，优先数据库，失败时回退 mock。"""
    try:
        rows = _db_hot_news(limit=limit)
        if rows:
            return rows
    except Exception as exc:  # noqa: BLE001
        logger.warning("读取新闻热榜失败，回退 mock：%s", exc)
    return _mock_get_hot_news(limit=limit)


def search_news(keyword: Optional[str], page: int = 1, page_size: int = 10) -> dict[str, Any]:
    """搜索新闻。"""
    if not keyword or not keyword.strip():
        return _paginate([], page=page, page_size=page_size)
    try:
        result = _db_news_list(keyword=keyword, page=page, page_size=page_size)
        return result
    except Exception as exc:  # noqa: BLE001
        logger.warning("搜索新闻失败，回退 mock：%s", exc)
        return _mock_get_news_list(keyword=keyword, page=page, page_size=page_size)


def get_news_detail(news_id: int, current_user: Optional[Any] = None) -> dict[str, Any]:
    """获取新闻详情，数据库优先，mock 兜底。"""
    try:
        detail = _db_news_detail(news_id=news_id, current_user=current_user)
        if detail is not None:
            return detail
    except Exception as exc:  # noqa: BLE001
        logger.warning("读取新闻详情失败，回退 mock：%s", exc)

    detail = _find_mock_news_by_id(news_id)
    if detail is not None:
        return _mock_get_news_detail(news_id=news_id, current_user=current_user)
    raise AppException(code=404, message="新闻不存在")


def record_browse(news_id: int, current_user: Optional[Any] = None) -> dict[str, Any]:
    """记录浏览行为，数据库优先，mock 兜底。"""
    try:
        result = _db_record_browse(news_id=news_id, current_user=current_user)
        if result is not None:
            return result
    except Exception as exc:  # noqa: BLE001
        logger.warning("记录浏览失败，回退 mock：%s", exc)

    return _mock_record_browse(news_id=news_id, current_user=current_user)
