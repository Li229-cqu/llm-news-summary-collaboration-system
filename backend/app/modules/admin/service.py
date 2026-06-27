from __future__ import annotations

import logging
from typing import Any, Dict, List

from app.common.utils import format_datetime, paginate
from app.mock.community import MOCK_COMMUNITY_POSTS
from app.mock.news import MOCK_NEWS
from app.mock.users import MOCK_USERS
from app.modules.admin.schema import AdminDashboard, AdminTestData, UserItem
from app.db.database import execute_one, execute_query

logger = logging.getLogger(__name__)


def get_test_data() -> AdminTestData:
    return AdminTestData(module="admin", description="管理后台基础接口占位")


def _safe_count(sql: str, default: int = 0) -> int:
    row = execute_one(sql)
    if not row:
        return default
    for key in ("total", "count", "cnt"):
        value = row.get(key)
        if value is not None:
            try:
                return int(value)
            except (TypeError, ValueError):
                break
    return default


def _build_user_item(row: Dict[str, Any]) -> Dict[str, Any]:
    return UserItem(
        id=int(row.get("id", 0)),
        username=str(row.get("username", "")),
        nickname=str(row.get("nickname", "")),
        role=str(row.get("role", "user")),
        status=int(row.get("status", 1)),
        create_time=format_datetime(row.get("create_time")) or None,
    ).model_dump()


def _build_pending_post_item(row: Dict[str, Any]) -> Dict[str, Any]:
    username = str(row.get("username") or row.get("author") or "")
    author = str(row.get("author") or row.get("nickname") or username)
    return {
        "id": int(row.get("id", 0)),
        "title": str(row.get("title", "")),
        "content": str(row.get("content", "")),
        "username": username,
        "author": author,
        "user_id": row.get("user_id"),
        "topic_id": row.get("topic_id"),
        "like_count": int(row.get("like_count", 0) or 0),
        "comment_count": int(row.get("comment_count", 0) or 0),
        "favorite_count": int(row.get("favorite_count", 0) or 0),
        "heat_score": int(row.get("heat_score", 0) or 0),
        "status": int(row.get("status", 0) or 0),
        "create_time": format_datetime(row.get("create_time")),
        "update_time": format_datetime(row.get("update_time")),
    }


def _mock_pending_posts() -> List[Dict[str, Any]]:
    pending_posts = [
        post
        for post in MOCK_COMMUNITY_POSTS
        if int(post.get("status", 0) or 0) in (0, 3)
    ]
    pending_posts.sort(key=lambda item: item.get("create_time", ""), reverse=True)
    return [
        {
            **post,
            "username": str(post.get("username") or post.get("author") or ""),
            "author": str(post.get("author") or post.get("nickname") or post.get("username") or ""),
        }
        for post in pending_posts
    ]


def get_dashboard() -> AdminDashboard:
    """获取后台概览数据，数据库优先，mock 兜底。"""
    try:
        user_count = _safe_count("SELECT COUNT(*) AS total FROM user")
        news_count = _safe_count("SELECT COUNT(*) AS total FROM news WHERE status = 1")
        post_count = _safe_count("SELECT COUNT(*) AS total FROM community_post")
        pending_count = _safe_count("SELECT COUNT(*) AS total FROM community_post WHERE status IN (0, 3)")
        return AdminDashboard(
            user_count=user_count,
            news_count=news_count,
            post_count=post_count,
            pending_count=pending_count,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("[DB FALLBACK] 管理员仪表盘读取数据库失败，回退 mock：%s", exc)
        user_count = len(MOCK_USERS)
        news_count = len([news for news in MOCK_NEWS if int(news.get("status", 1)) == 1])
        post_count = len(MOCK_COMMUNITY_POSTS)
        pending_count = len([post for post in MOCK_COMMUNITY_POSTS if int(post.get("status", 0) or 0) == 0])
        return AdminDashboard(
            user_count=user_count,
            news_count=news_count,
            post_count=post_count,
            pending_count=pending_count,
        )


def get_pending_posts(page: int = 1, page_size: int = 10) -> Dict[str, Any]:
    """获取待审核帖子列表，数据库优先，mock 兜底。"""
    try:
        sql = """
            SELECT
                p.id,
                p.title,
                p.content,
                p.user_id,
                p.topic_id,
                p.like_count,
                p.comment_count,
                p.favorite_count,
                p.heat_score,
                p.status,
                p.create_time,
                p.update_time,
                COALESCE(u.username, '') AS username,
                COALESCE(u.nickname, '') AS author
            FROM community_post p
            LEFT JOIN user u ON u.id = p.user_id
            WHERE p.status IN (0, 3)
            ORDER BY p.create_time DESC, p.id DESC
        """
        rows = execute_query(sql)
        items = [_build_pending_post_item(row) for row in rows]
        return paginate(items, page=page, page_size=page_size)
    except Exception as exc:  # noqa: BLE001
        logger.warning("[DB FALLBACK] 待审核帖子读取数据库失败，回退 mock：%s", exc)
        return paginate(_mock_pending_posts(), page=page, page_size=page_size)


def get_users(page: int = 1, page_size: int = 10) -> Dict[str, Any]:
    """获取用户列表，数据库优先，mock 兜底。"""
    try:
        rows = execute_query(
            """
            SELECT
                id,
                username,
                nickname,
                role,
                status,
                created_at AS create_time
            FROM user
            ORDER BY id ASC
            """
        )
        items = [_build_user_item(row) for row in rows]
        return paginate(items, page=page, page_size=page_size)
    except Exception as exc:  # noqa: BLE001
        logger.warning("[DB FALLBACK] 用户列表读取数据库失败，回退 mock：%s", exc)
        items = [_build_user_item(user) for user in MOCK_USERS]
        return paginate(items, page=page, page_size=page_size)


def get_system_config() -> Dict[str, Any]:
    """获取系统配置，当前仍使用 mock 数据。"""
    return {
        "site_name": "智能新闻摘要与协同互动系统",
        "site_description": "基于大语言模型的智能新闻摘要与协同互动系统",
        "max_upload_size": 10,
        "default_page_size": 10,
        "ai_service_enabled": True,
        "auto_approve_enabled": False,
    }
