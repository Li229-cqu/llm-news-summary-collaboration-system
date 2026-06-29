from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from app.common.exceptions import AppException
from app.common.utils import format_datetime, paginate
from app.mock.community import MOCK_COMMUNITY_POSTS
from app.mock.news import MOCK_NEWS
from app.mock.users import MOCK_USERS
from app.modules.admin.schema import (
    AdminDashboard,
    AdminTestData,
    AuditResponse,
    HotTopicCreate,
    HotTopicItem,
    HotTopicUpdate,
    SimpleHotTopicCreate,
    SimpleHotTopicItem,
    SimpleHotTopicUpdate,
    UserItem,
)
from app.db.database import execute_one, execute_query, execute_update, get_connection

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


# ==================== 帖子审核 ====================

def approve_post(post_id: int) -> AuditResponse:
    """审核通过帖子：status 0/3 → 1"""
    try:
        post = execute_one(
            "SELECT id, status, title FROM community_post WHERE id = %s",
            [post_id],
        )
        if post is None:
            raise AppException(code=404, message="帖子不存在")
        current_status = int(post.get("status") or 0)
        if current_status not in (0, 3):
            raise AppException(code=400, message=f"帖子当前状态不可审核（status={current_status}）")

        execute_update(
            "UPDATE community_post SET status = 1, update_time = NOW() WHERE id = %s",
            [post_id],
        )
        logger.info("帖子审核通过：id=%s, title=%s", post_id, post.get("title"))
        return AuditResponse(id=post_id, status=1, message="审核通过，帖子已发布")
    except AppException:
        raise
    except Exception as exc:
        logger.error("审核通过帖子失败：%s", exc)
        raise AppException(code=500, message="审核操作失败，请稍后重试")


def reject_post(post_id: int, reason: Optional[str] = None) -> AuditResponse:
    """驳回帖子：status 0/3 → 2"""
    try:
        post = execute_one(
            "SELECT id, status, title FROM community_post WHERE id = %s",
            [post_id],
        )
        if post is None:
            raise AppException(code=404, message="帖子不存在")
        current_status = int(post.get("status") or 0)
        if current_status not in (0, 3):
            raise AppException(code=400, message=f"帖子当前状态不可审核（status={current_status}）")

        execute_update(
            "UPDATE community_post SET status = 2, update_time = NOW() WHERE id = %s",
            [post_id],
        )
        logger.info("帖子驳回：id=%s, title=%s, reason=%s", post_id, post.get("title"), reason)
        return AuditResponse(id=post_id, status=2, message="帖子已驳回", reason=reason)
    except AppException:
        raise
    except Exception as exc:
        logger.error("驳回帖子失败：%s", exc)
        raise AppException(code=500, message="驳回操作失败，请稍后重试")


# ==================== 新闻热搜榜 ====================

def get_hot_news(limit: int = 20) -> List[Dict[str, Any]]:
    """获取新闻热搜榜（管理员视图），合并 hot_topic 手动管理项 + news 计算项。"""
    try:
        rows = execute_query(
            """
            SELECT * FROM (
                -- 手动管理的新闻热搜（hot_topic 表，优先级最高）
                SELECT
                    COALESCE(n.id, ht.target_id) AS id,
                    ht.title,
                    COALESCE(nc.name, '未分类') AS category_name,
                    n.source,
                    COALESCE(n.view_count, 0) AS view_count,
                    COALESCE(n.comment_count, 0) AS comment_count,
                    COALESCE(n.like_count, 0) AS like_count,
                    COALESCE(n.favorite_count, 0) AS favorite_count,
                    (ht.heat_score + 100000) AS heat_score,
                    1 AS managed,
                    ht.id AS topic_id
                FROM hot_topic ht
                LEFT JOIN news n ON n.id = ht.target_id AND n.status = 1
                LEFT JOIN news_category nc ON nc.id = n.category_id
                WHERE ht.target_type = 'news' AND ht.status = 1

                UNION ALL

                -- 自动计算的新闻热度
                SELECT
                    n.id,
                    n.title,
                    COALESCE(nc.name, '未分类') AS category_name,
                    n.source,
                    n.view_count,
                    n.comment_count,
                    n.like_count,
                    n.favorite_count,
                    (
                        COALESCE(n.view_count, 0)
                        + COALESCE(n.like_count, 0) * 5
                        + COALESCE(n.favorite_count, 0) * 4
                        + COALESCE(n.comment_count, 0) * 6
                    ) AS heat_score,
                    0 AS managed,
                    NULL AS topic_id
                FROM news n
                LEFT JOIN news_category nc ON nc.id = n.category_id
                WHERE n.status = 1
                  AND n.id NOT IN (
                      SELECT target_id FROM hot_topic
                      WHERE target_type = 'news' AND status = 1 AND target_id IS NOT NULL
                  )
            ) combined
            ORDER BY heat_score DESC, view_count DESC, id DESC
            LIMIT %s
            """,
            [max(limit, 1)],
        )
        items = []
        for index, row in enumerate(rows, start=1):
            items.append({
                "id": int(row.get("id", 0)),
                "title": str(row.get("title", "")),
                "category_name": str(row.get("category_name", "")),
                "source": str(row.get("source", "")),
                "view_count": int(row.get("view_count", 0) or 0),
                "comment_count": int(row.get("comment_count", 0) or 0),
                "like_count": int(row.get("like_count", 0) or 0),
                "favorite_count": int(row.get("favorite_count", 0) or 0),
                "heat_score": int(row.get("heat_score", 0) or 0),
                "rank": index,
                "publish_time": format_datetime(row.get("publish_time")),
                "managed": bool(int(row.get("managed") or 0)),
                "topic_id": int(row.get("topic_id") or 0) if row.get("topic_id") is not None else None,
            })
        return items
    except Exception as exc:
        logger.error("获取新闻热搜榜失败：%s", exc)
        raise AppException(code=500, message="获取新闻热搜榜失败")


def promote_news_to_hot_topic(news_id: int) -> Dict[str, Any]:
    """将新闻推送到 hot_topic 表（上社区热搜榜）。"""
    try:
        news = execute_one(
            "SELECT id, title, category_id FROM news WHERE id = %s AND status = 1",
            [news_id],
        )
        if news is None:
            raise AppException(code=404, message="新闻不存在或已下架")

        # 检查是否已在热搜表中
        existing = execute_one(
            "SELECT id FROM hot_topic WHERE target_type = 'news' AND target_id = %s",
            [news_id],
        )
        if existing:
            raise AppException(code=400, message="该新闻已在热搜榜中")

        title = str(news.get("title", ""))
        connection = get_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO hot_topic (title, heat_score, target_type, target_id,
                                           tag, rank_no, status, create_time, update_time)
                    VALUES (%s, 100, 'news', %s, '热搜', 99, 1, NOW(), NOW())
                    """,
                    [title, news_id],
                )
                new_id = cursor.lastrowid or 0
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

        return {"id": new_id, "news_id": news_id, "title": title, "promoted": True}
    except AppException:
        raise
    except Exception as exc:
        logger.error("推送新闻到热搜失败：%s", exc)
        raise AppException(code=500, message="推送新闻到热搜失败")


# ==================== 热搜管理（hot_topic 表 CRUD） ====================

def _build_hot_topic_item(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": int(row.get("id", 0)),
        "title": str(row.get("title", "")),
        "heat_score": int(row.get("heat_score", 0) or 0),
        "target_type": str(row.get("target_type") or "") or None,
        "target_id": int(row.get("target_id") or 0) if row.get("target_id") is not None else None,
        "tag": str(row.get("tag") or "") or None,
        "rank_no": int(row.get("rank_no", 0) or 0),
        "status": int(row.get("status", 1)),
        "create_time": format_datetime(row.get("create_time")),
        "update_time": format_datetime(row.get("update_time")),
    }


def get_hot_topics(target_type: Optional[str] = None, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
    """获取热搜话题列表。
    target_type='news' → 新闻热搜榜
    target_type='community' → 社区热搜（排除 news 类型）
    target_type=None → 全部
    """
    try:
        if target_type == 'news':
            rows = execute_query(
                """
                SELECT id, title, heat_score, target_type, target_id, tag,
                       rank_no, status, create_time, update_time
                FROM hot_topic
                WHERE target_type = 'news'
                ORDER BY rank_no ASC, heat_score DESC, id ASC
                """
            )
        elif target_type == 'community':
            rows = execute_query(
                """
                SELECT id, title, heat_score, target_type, target_id, tag,
                       rank_no, status, create_time, update_time
                FROM hot_topic
                WHERE target_type != 'news'
                ORDER BY rank_no ASC, heat_score DESC, id ASC
                """
            )
        else:
            rows = execute_query(
                """
                SELECT id, title, heat_score, target_type, target_id, tag,
                       rank_no, status, create_time, update_time
                FROM hot_topic
                ORDER BY rank_no ASC, heat_score DESC, id ASC
                """
            )
        items = [_build_hot_topic_item(row) for row in rows]
        return paginate(items, page=page, page_size=page_size)
    except Exception as exc:
        logger.error("获取热搜列表失败：%s", exc)
        raise AppException(code=500, message="获取热搜列表失败")


def create_hot_topic(data: HotTopicCreate) -> Dict[str, Any]:
    """手动添加热搜话题。"""
    try:
        connection = get_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO hot_topic (title, heat_score, target_type, target_id,
                                           tag, rank_no, status, create_time, update_time)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                    """,
                    [
                        data.title,
                        data.heat_score,
                        data.target_type,
                        data.target_id,
                        data.tag,
                        data.rank_no,
                        data.status,
                    ],
                )
                new_id = cursor.lastrowid or 0
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

        row = execute_one("SELECT * FROM hot_topic WHERE id = %s", [new_id])
        if row:
            return _build_hot_topic_item(row)
        return _build_hot_topic_item({
            "id": new_id,
            "title": data.title,
            "heat_score": data.heat_score,
            "target_type": data.target_type,
            "target_id": data.target_id,
            "tag": data.tag,
            "rank_no": data.rank_no,
            "status": data.status,
            "create_time": None,
            "update_time": None,
        })
    except AppException:
        raise
    except Exception as exc:
        logger.error("添加热搜话题失败：%s", exc)
        raise AppException(code=500, message="添加热搜话题失败")


def update_hot_topic(topic_id: int, data: HotTopicUpdate) -> Dict[str, Any]:
    """编辑热搜话题。"""
    try:
        existing = execute_one("SELECT id FROM hot_topic WHERE id = %s", [topic_id])
        if existing is None:
            raise AppException(code=404, message="热搜话题不存在")

        fields = []
        params: List[Any] = []
        update_data = data.model_dump(exclude_none=True)
        if not update_data:
            raise AppException(code=400, message="没有需要更新的字段")

        for key, value in update_data.items():
            fields.append(f"{key} = %s")
            params.append(value)
        fields.append("update_time = NOW()")
        params.append(topic_id)

        execute_update(
            f"UPDATE hot_topic SET {', '.join(fields)} WHERE id = %s",
            params,
        )
        row = execute_one("SELECT * FROM hot_topic WHERE id = %s", [topic_id])
        if row:
            return _build_hot_topic_item(row)
        raise AppException(code=500, message="更新后读取话题失败")
    except AppException:
        raise
    except Exception as exc:
        logger.error("编辑热搜话题失败：%s", exc)
        raise AppException(code=500, message="编辑热搜话题失败")


def delete_hot_topic(topic_id: int) -> Dict[str, Any]:
    """删除热搜话题。"""
    try:
        existing = execute_one("SELECT id FROM hot_topic WHERE id = %s", [topic_id])
        if existing is None:
            raise AppException(code=404, message="热搜话题不存在")

        execute_update("DELETE FROM hot_topic WHERE id = %s", [topic_id])
        return {"id": topic_id, "deleted": True}
    except AppException:
        raise
    except Exception as exc:
        logger.error("删除热搜话题失败：%s", exc)
        raise AppException(code=500, message="删除热搜话题失败")


# ==================== 简化热搜管理（E2） ====================

def _build_simple_hot_topic_item(row: Dict[str, Any]) -> Dict[str, Any]:
    """将 hot_topic 表行转为简化热搜响应格式。"""
    return {
        "id": int(row.get("id", 0)),
        "keyword": str(row.get("title", "")),
        "heat": int(row.get("heat_score", 0) or 0),
        "is_pinned": bool(int(row.get("is_pinned", 0) or 0)),
        "status": int(row.get("status", 1)),
        "create_time": format_datetime(row.get("create_time")),
        "update_time": format_datetime(row.get("update_time")),
    }


def get_simple_hot_topics(page: int = 1, page_size: int = 20) -> Dict[str, Any]:
    """获取热搜话题列表（简化版）。
    置顶话题优先，再按热度降序排列。
    """
    try:
        rows = execute_query(
            """
            SELECT id, title, heat_score, is_pinned, status, create_time, update_time
            FROM hot_topic
            ORDER BY is_pinned DESC, heat_score DESC, id DESC
            """
        )
        items = [_build_simple_hot_topic_item(row) for row in rows]
        return paginate(items, page=page, page_size=page_size)
    except Exception as exc:
        logger.error("获取热搜列表失败：%s", exc)
        raise AppException(code=500, message="获取热搜列表失败")


def create_simple_hot_topic(data: SimpleHotTopicCreate) -> Dict[str, Any]:
    """手动添加热搜关键词。"""
    try:
        connection = get_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO hot_topic (title, heat_score, target_type, target_id,
                                           tag, rank_no, status, is_pinned, create_time, update_time)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                    """,
                    [
                        data.keyword,
                        data.heat,
                        "keyword",
                        None,
                        "",
                        0,
                        1,
                        0,
                    ],
                )
                new_id = cursor.lastrowid or 0
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

        row = execute_one("SELECT * FROM hot_topic WHERE id = %s", [new_id])
        if row:
            return _build_simple_hot_topic_item(row)
        return _build_simple_hot_topic_item({
            "id": new_id,
            "title": data.keyword,
            "heat_score": data.heat,
            "is_pinned": 0,
            "status": 1,
            "create_time": None,
            "update_time": None,
        })
    except AppException:
        raise
    except Exception as exc:
        logger.error("添加热搜话题失败：%s", exc)
        raise AppException(code=500, message="添加热搜话题失败")


def update_simple_hot_topic(topic_id: int, data: SimpleHotTopicUpdate) -> Dict[str, Any]:
    """编辑热搜话题（关键词、热度、置顶状态、上下架）。"""
    try:
        existing = execute_one("SELECT id FROM hot_topic WHERE id = %s", [topic_id])
        if existing is None:
            raise AppException(code=404, message="热搜话题不存在")

        fields: List[str] = []
        params: List[Any] = []
        update_data = data.model_dump(exclude_none=True)
        if not update_data:
            raise AppException(code=400, message="没有需要更新的字段")

        # 映射前端字段名到数据库列名
        field_mapping = {
            "keyword": "title",
            "heat": "heat_score",
            "is_pinned": "is_pinned",
            "status": "status",
        }
        for key, value in update_data.items():
            db_key = field_mapping.get(key, key)
            # is_pinned 从 bool 转为 int
            if key == "is_pinned":
                value = 1 if value else 0
            fields.append(f"{db_key} = %s")
            params.append(value)
        fields.append("update_time = NOW()")
        params.append(topic_id)

        execute_update(
            f"UPDATE hot_topic SET {', '.join(fields)} WHERE id = %s",
            params,
        )
        row = execute_one("SELECT * FROM hot_topic WHERE id = %s", [topic_id])
        if row:
            return _build_simple_hot_topic_item(row)
        raise AppException(code=500, message="更新后读取话题失败")
    except AppException:
        raise
    except Exception as exc:
        logger.error("编辑热搜话题失败：%s", exc)
        raise AppException(code=500, message="编辑热搜话题失败")


def delete_simple_hot_topic(topic_id: int) -> Dict[str, Any]:
    """删除热搜话题。"""
    try:
        existing = execute_one("SELECT id FROM hot_topic WHERE id = %s", [topic_id])
        if existing is None:
            raise AppException(code=404, message="热搜话题不存在")

        execute_update("DELETE FROM hot_topic WHERE id = %s", [topic_id])
        return {"id": topic_id, "deleted": True}
    except AppException:
        raise
    except Exception as exc:
        logger.error("删除热搜话题失败：%s", exc)
        raise AppException(code=500, message="删除热搜话题失败")


# ==================== 用户管理 ====================

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
