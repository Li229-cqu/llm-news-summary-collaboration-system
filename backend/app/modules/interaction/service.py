"""新闻互动模块服务层：数据库优先，mock 兜底。

当前阶段优先读写 MySQL 中的 news_comment、user_like、favorite 等表；
当数据库不可用、查询异常或目标数据尚未同步时，自动回退到进程内 mock 数据，
保证课程演示期间接口仍可用。
"""

from __future__ import annotations

import json
import logging
import json
from datetime import datetime
from functools import lru_cache
from typing import Any, Dict, List, Optional, Sequence, Set, Union

from app.common.exceptions import AppException
from app.common.utils import format_datetime, normalize_text
from app.db.database import execute_one, execute_query, execute_update, get_connection
from app.mock.comments import MOCK_COMMENT_LIKES, MOCK_NEWS_COMMENTS
from app.mock.news import MOCK_NEWS, MOCK_NEWS_FAVORITES, MOCK_NEWS_LIKES
from app.modules.interaction.schema import (
    CommentCreateRequest,
    CommentItem,
    CommentLikeResult,
    CommentListResponse,
    CommentReplyRequest,
    InteractionResult,
    InteractionTestData,
)

logger = logging.getLogger(__name__)


def get_test_data() -> InteractionTestData:
    """保留模块连通性测试的占位数据。"""

    return InteractionTestData(module="interaction", description="新闻互动模块基础接口占位")


def _get_current_user_id(current_user: Optional[Any]) -> Optional[int]:
    if current_user is None:
        return None
    if isinstance(current_user, dict):
        return current_user.get("id")
    return getattr(current_user, "id", None)


def _get_current_user_value(current_user: Any, field: str, default: Any = "") -> Any:
    if isinstance(current_user, dict):
        return current_user.get(field, default)
    return getattr(current_user, field, default)



def _normalize_comment_media_json(value: Any) -> Optional[dict[str, Any]]:
    if value is None:
        return None
    if hasattr(value, "model_dump"):
        value = value.model_dump(exclude_none=True)
    elif hasattr(value, "dict"):
        value = value.dict(exclude_none=True)
    elif isinstance(value, str):
        try:
            value = json.loads(value)
        except Exception:  # noqa: BLE001
            return None

    if not isinstance(value, dict):
        return None

    normalized: dict[str, Any] = {}
    images = value.get("images")
    if isinstance(images, list):
        normalized_images = [normalize_text(item) for item in images if normalize_text(item)]
        if normalized_images:
            normalized["images"] = normalized_images

    emojis = value.get("emojis")
    if isinstance(emojis, list):
        normalized_emojis = [normalize_text(item) for item in emojis if normalize_text(item)]
        if normalized_emojis:
            normalized["emojis"] = normalized_emojis

    return normalized or None


def _serialize_comment_media_json(value: Any) -> Optional[str]:
    normalized = _normalize_comment_media_json(value)
    if normalized is None:
        return None
    return json.dumps(normalized, ensure_ascii=False)


def _comment_row_to_item_payload(
    row: Dict[str, Any],
    current_user: Optional[Any] = None,
    liked_comment_ids: Optional[set[int]] = None,
) -> dict[str, Any]:
    comment_id = int(row.get("id") or 0)
    status = int(row.get("status") or 0)
    if liked_comment_ids is None:
        is_liked = is_comment_liked(comment_id, current_user)
    else:
        is_liked = comment_id in liked_comment_ids

    if status == 4:
        content = "该评论已删除"
    elif status == 2:
        content = "该评论已被折叠"
    else:
        content = normalize_text(row.get("content"))

    media_json_raw = row.get("media_json")
    media_json = None
    if media_json_raw:
        if isinstance(media_json_raw, str):
            media_json_raw = media_json_raw.strip()
            if media_json_raw:
                try:
                    media_json = json.loads(media_json_raw)
                except (json.JSONDecodeError, TypeError):
                    media_json = None
        elif isinstance(media_json_raw, (dict, list)):
            media_json = media_json_raw

    return {
        "id": comment_id,
        "news_id": int(row.get("news_id") or 0),
        "user_id": int(row.get("user_id") or 0),
        "username": normalize_text(row.get("username")),
        "nickname": normalize_text(row.get("nickname")),
        "avatar": normalize_text(row.get("avatar")),
        "parent_id": None if row.get("parent_id") is None else int(row.get("parent_id") or 0),
        "content": content,
        "like_count": int(row.get("like_count") or 0),
        "status": status,
        "create_time": format_datetime(row.get("create_time")),
        "is_liked": is_liked,
        "media_json": _normalize_comment_media_json(row.get("media_json")),
        "replies": [],
        "reply_to_user_id": row.get("reply_to_user_id"),
        "reply_to_username": normalize_text(row.get("reply_to_username") or ""),
        "reply_to_nickname": normalize_text(row.get("reply_to_nickname") or ""),
        "reply_to_content": normalize_text(row.get("reply_to_content") or ""),
    }


def _assemble_comment_tree(
    comment_rows: Sequence[Dict[str, Any]],
    current_user: Optional[Any] = None,
    liked_comment_ids: Optional[set[int]] = None,
) -> CommentListResponse:
    comment_map: dict[int, dict[str, Any]] = {}
    for row in comment_rows:
        payload = _comment_row_to_item_payload(dict(row), current_user=current_user, liked_comment_ids=liked_comment_ids)
        comment_map[payload["id"]] = payload

    root_comments: list[dict[str, Any]] = []
    for item in comment_map.values():
        parent_id = item["parent_id"]
        if parent_id is None or parent_id not in comment_map:
            root_comments.append(item)
        else:
            comment_map[parent_id]["replies"].append(item)

    root_comments.sort(key=lambda item: (-item["like_count"], item["create_time"], item["id"]))
    for item in comment_map.values():
        item["replies"].sort(key=lambda reply: (-reply["like_count"], reply["create_time"], reply["id"]))

    return CommentListResponse(
        list=[CommentItem(**item) for item in root_comments],
        total=len(comment_rows),
    )


def _mock_news_row(news_id: int) -> dict[str, Any] | None:
    for news in MOCK_NEWS:
        if int(news.get("id") or 0) == news_id and int(news.get("status") or 0) == 1:
            return dict(news)
    return None


def _mock_comment_row(comment_id: int) -> dict[str, Any] | None:
    for comment in MOCK_NEWS_COMMENTS:
        if int(comment.get("id") or 0) == comment_id and int(comment.get("status") or 0) != 4:
            return dict(comment)
    return None


def require_current_user(current_user: Optional[Any]) -> Any:
    """校验互动写操作的当前用户。"""

    user_id = _get_current_user_id(current_user)
    if current_user is None or user_id is None:
        raise AppException(code=401, message="未登录或登录状态已失效")
    return current_user


def _can_delete_comment(current_user: Any, comment_user_id: int) -> bool:
    current_user_id = _get_current_user_id(current_user)
    if current_user_id is None:
        return False
    if current_user_id == comment_user_id:
        return True
    role = str(_get_current_user_value(current_user, "role", "") or "").lower()
    return role in {"admin", "editor"}


def get_news_by_id(news_id: int) -> Dict[str, Any]:
    """获取可参与互动的已发布新闻。"""

    try:
        row = execute_one(
            "SELECT id, like_count, favorite_count, comment_count FROM news WHERE id = %s AND status = 1 LIMIT 1",
            [news_id],
        )
        if row is not None:
            return row
    except Exception as exc:  # noqa: BLE001
        logger.warning("读取新闻数据失败，准备回退 mock：%s", exc)

    news = _mock_news_row(news_id)
    if news is not None:
        return news
    raise AppException(code=404, message="新闻不存在")


def get_comment_by_id(comment_id: int) -> Dict[str, Any]:
    """获取未删除的评论。"""

    try:
        row = execute_one(
            """
            SELECT id, news_id, user_id, parent_id, content, media_json, like_count, status
            FROM news_comment
            WHERE id = %s AND status <> 4
            LIMIT 1
            """,
            [comment_id],
        )
        if row is not None:
            return row
    except Exception as exc:  # noqa: BLE001
        logger.warning("读取评论数据失败，准备回退 mock：%s", exc)

    comment = _mock_comment_row(comment_id)
    if comment is not None:
        return comment
    raise AppException(code=404, message="评论不存在")


def get_next_comment_id() -> int:
    """生成当前 mock 数据中的下一个评论 ID。"""

    return max((int(comment["id"]) for comment in MOCK_NEWS_COMMENTS), default=0) + 1


def _has_news_relation(relations: List[Dict[str, int]], user_id: int, news_id: int) -> bool:
    return any(item["user_id"] == user_id and item["news_id"] == news_id for item in relations)


def _remove_news_relation(relations: List[Dict[str, int]], user_id: int, news_id: int) -> bool:
    for index, item in enumerate(relations):
        if item["user_id"] == user_id and item["news_id"] == news_id:
            relations.pop(index)
            return True
    return False


def is_comment_liked(comment_id: int, current_user: Optional[Any]) -> bool:
    """判断当前用户是否已点赞指定评论。"""

    if current_user is None:
        return False
    user_id = _get_current_user_value(current_user, "id", None)
    if user_id is None:
        return False
    return any(
        item["user_id"] == user_id and item["comment_id"] == comment_id
        for item in MOCK_COMMENT_LIKES
    )


def _db_user_like_exists(user_id: int, target_id: int, target_type: str, connection=None) -> bool:
    sql = """
        SELECT id
        FROM user_like
        WHERE user_id = %s AND target_id = %s AND target_type = %s
        LIMIT 1
    """
    if connection is None:
        return execute_one(sql, [user_id, target_id, target_type]) is not None
    with connection.cursor() as cursor:
        cursor.execute(sql, [user_id, target_id, target_type])
        return cursor.fetchone() is not None


def _db_favorite_exists(user_id: int, news_id: int, connection=None) -> bool:
    sql = """
        SELECT id
        FROM favorite
        WHERE user_id = %s AND target_id = %s AND target_type = 'news'
        LIMIT 1
    """
    if connection is None:
        return execute_one(sql, [user_id, news_id]) is not None
    with connection.cursor() as cursor:
        cursor.execute(sql, [user_id, news_id])
        return cursor.fetchone() is not None


def _db_news_row(news_id: int, connection=None) -> dict[str, Any] | None:
    sql = "SELECT id, like_count, favorite_count, comment_count FROM news WHERE id = %s AND status = 1 LIMIT 1"
    if connection is None:
        return execute_one(sql, [news_id])
    with connection.cursor() as cursor:
        cursor.execute(sql, [news_id])
        row = cursor.fetchone()
        return dict(row) if row is not None else None


def _db_comment_row(comment_id: int, connection=None) -> dict[str, Any] | None:
    sql = """
        SELECT id, news_id, user_id, parent_id, content, media_json, like_count, status
        FROM news_comment
        WHERE id = %s AND status <> 4
        LIMIT 1
    """
    if connection is None:
        return execute_one(sql, [comment_id])
    with connection.cursor() as cursor:
        cursor.execute(sql, [comment_id])
        row = cursor.fetchone()
        return dict(row) if row is not None else None


def _db_liked_comment_ids(user_id: int) -> set[int]:
    rows = execute_query(
        """
        SELECT target_id
        FROM user_like
        WHERE user_id = %s AND target_type = 'news_comment'
        """,
        [user_id],
    )
    return {int(row["target_id"]) for row in rows}


@lru_cache(maxsize=1)
def _db_news_comment_has_media_json() -> bool:
    try:
        row = execute_one(
            """
            SELECT COUNT(*) AS cnt
            FROM information_schema.columns
            WHERE table_schema = DATABASE()
              AND table_name = 'news_comment'
              AND column_name = 'media_json'
            """,
        )
        return bool(int(row.get("cnt") or 0)) if row else False
    except Exception:
        return False


def _db_comment_rows(news_id: int) -> list[dict[str, Any]]:
    media_json_column = "c.media_json" if _db_news_comment_has_media_json() else "NULL AS media_json"
    sql = f"""
        SELECT
            c.id,
            c.news_id,
            c.user_id,
            COALESCE(u.username, '') AS username,
            COALESCE(u.nickname, '') AS nickname,
            COALESCE(u.avatar, '') AS avatar,
            c.parent_id,
            c.content,
            {media_json_column},
            c.like_count,
            c.status,
            c.created_at AS create_time,
            COALESCE(ru.id, NULL) AS reply_to_user_id,
            COALESCE(ru.username, '') AS reply_to_username,
            COALESCE(ru.nickname, '') AS reply_to_nickname,
            COALESCE(parent_c.content, '') AS reply_to_content
        FROM news_comment c
        LEFT JOIN user u ON u.id = c.user_id
        LEFT JOIN news_comment parent_c ON parent_c.id = c.parent_id
        LEFT JOIN user ru ON ru.id = parent_c.user_id
        WHERE c.news_id = %s AND c.status IN (1, 2, 4)
        ORDER BY c.created_at ASC, c.id ASC
        """
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(sql, [news_id])
            rows = cursor.fetchall()
            return [dict(row) for row in rows] if rows else []
    finally:
        connection.close()


def _db_like_news(news_id: int, current_user: Optional[Any]) -> InteractionResult | None:
    user = require_current_user(current_user)
    user_id = _get_current_user_value(user, "id")
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id, like_count FROM news WHERE id = %s AND status = 1 LIMIT 1",
                [news_id],
            )
            news = cursor.fetchone()
            if news is None:
                return None

            cursor.execute(
                """
                SELECT id
                FROM user_like
                WHERE user_id = %s AND target_id = %s AND target_type = 'news'
                LIMIT 1
                """,
                [user_id, news_id],
            )
            exists = cursor.fetchone() is not None
            if exists:
                return InteractionResult(
                    target_id=news_id,
                    target_type="news",
                    action="like",
                    status=True,
                    like_count=int(news["like_count"]),
                    message="已点赞",
                )

            cursor.execute(
                """
                INSERT INTO user_like (user_id, target_id, target_type, created_at)
                VALUES (%s, %s, 'news', NOW())
                """,
                [user_id, news_id],
            )
            cursor.execute(
                """
                UPDATE news
                SET like_count = like_count + 1, updated_at = NOW()
                WHERE id = %s
                """,
                [news_id],
            )
            cursor.execute("SELECT like_count FROM news WHERE id = %s LIMIT 1", [news_id])
            updated = cursor.fetchone()
        connection.commit()
        return InteractionResult(
            target_id=news_id,
            target_type="news",
            action="like",
            status=True,
            like_count=int(updated["like_count"]) if updated else int(news["like_count"]) + 1,
            message="点赞成功",
        )
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def _db_unlike_news(news_id: int, current_user: Optional[Any]) -> InteractionResult | None:
    user = require_current_user(current_user)
    user_id = _get_current_user_value(user, "id")
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id, like_count FROM news WHERE id = %s AND status = 1 LIMIT 1",
                [news_id],
            )
            news = cursor.fetchone()
            if news is None:
                return None

            cursor.execute(
                """
                SELECT id
                FROM user_like
                WHERE user_id = %s AND target_id = %s AND target_type = 'news'
                LIMIT 1
                """,
                [user_id, news_id],
            )
            exists = cursor.fetchone()
            if not exists:
                return InteractionResult(
                    target_id=news_id,
                    target_type="news",
                    action="unlike",
                    status=False,
                    like_count=int(news["like_count"]),
                    message="当前未点赞",
                )

            cursor.execute(
                """
                DELETE FROM user_like
                WHERE user_id = %s AND target_id = %s AND target_type = 'news'
                """,
                [user_id, news_id],
            )
            cursor.execute(
                """
                UPDATE news
                SET like_count = GREATEST(like_count - 1, 0), updated_at = NOW()
                WHERE id = %s
                """,
                [news_id],
            )
            cursor.execute("SELECT like_count FROM news WHERE id = %s LIMIT 1", [news_id])
            updated = cursor.fetchone()
        connection.commit()
        return InteractionResult(
            target_id=news_id,
            target_type="news",
            action="unlike",
            status=False,
            like_count=int(updated["like_count"]) if updated else max(int(news["like_count"]) - 1, 0),
            message="已取消点赞",
        )
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def _db_favorite_news(news_id: int, current_user: Optional[Any]) -> InteractionResult | None:
    user = require_current_user(current_user)
    user_id = _get_current_user_value(user, "id")
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id, favorite_count FROM news WHERE id = %s AND status = 1 LIMIT 1",
                [news_id],
            )
            news = cursor.fetchone()
            if news is None:
                return None

            cursor.execute(
                """
                SELECT id
                FROM favorite
                WHERE user_id = %s AND target_id = %s AND target_type = 'news'
                LIMIT 1
                """,
                [user_id, news_id],
            )
            exists = cursor.fetchone() is not None
            if exists:
                return InteractionResult(
                    target_id=news_id,
                    target_type="news",
                    action="favorite",
                    status=True,
                    favorite_count=int(news["favorite_count"]),
                    message="已收藏",
                )

            cursor.execute(
                """
                INSERT INTO favorite (user_id, target_id, target_type, created_at)
                VALUES (%s, %s, 'news', NOW())
                """,
                [user_id, news_id],
            )
            cursor.execute(
                """
                UPDATE news
                SET favorite_count = favorite_count + 1, updated_at = NOW()
                WHERE id = %s
                """,
                [news_id],
            )
            cursor.execute("SELECT favorite_count FROM news WHERE id = %s LIMIT 1", [news_id])
            updated = cursor.fetchone()
        connection.commit()
        return InteractionResult(
            target_id=news_id,
            target_type="news",
            action="favorite",
            status=True,
            favorite_count=int(updated["favorite_count"]) if updated else int(news["favorite_count"]) + 1,
            message="收藏成功",
        )
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def _db_unfavorite_news(news_id: int, current_user: Optional[Any]) -> InteractionResult | None:
    user = require_current_user(current_user)
    user_id = _get_current_user_value(user, "id")
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id, favorite_count FROM news WHERE id = %s AND status = 1 LIMIT 1",
                [news_id],
            )
            news = cursor.fetchone()
            if news is None:
                return None

            cursor.execute(
                """
                SELECT id
                FROM favorite
                WHERE user_id = %s AND target_id = %s AND target_type = 'news'
                LIMIT 1
                """,
                [user_id, news_id],
            )
            exists = cursor.fetchone()
            if not exists:
                return InteractionResult(
                    target_id=news_id,
                    target_type="news",
                    action="unfavorite",
                    status=False,
                    favorite_count=int(news["favorite_count"]),
                    message="当前未收藏",
                )

            cursor.execute(
                """
                DELETE FROM favorite
                WHERE user_id = %s AND target_id = %s AND target_type = 'news'
                """,
                [user_id, news_id],
            )
            cursor.execute(
                """
                UPDATE news
                SET favorite_count = GREATEST(favorite_count - 1, 0), updated_at = NOW()
                WHERE id = %s
                """,
                [news_id],
            )
            cursor.execute("SELECT favorite_count FROM news WHERE id = %s LIMIT 1", [news_id])
            updated = cursor.fetchone()
        connection.commit()
        return InteractionResult(
            target_id=news_id,
            target_type="news",
            action="unfavorite",
            status=False,
            favorite_count=int(updated["favorite_count"]) if updated else max(int(news["favorite_count"]) - 1, 0),
            message="已取消收藏",
        )
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def _db_get_news_comments(
    news_id: int,
    current_user: Optional[Any] = None,
) -> CommentListResponse | None:
    news = _db_news_row(news_id)
    if news is None:
        return None

    rows = _db_comment_rows(news_id)
    if not rows:
        return CommentListResponse(list=[], total=0)

    current_user_id = _get_current_user_id(current_user)
    liked_comment_ids: set[int] = set()
    if current_user_id is not None:
        liked_comment_ids = _db_liked_comment_ids(current_user_id)

    return _assemble_comment_tree(rows, current_user=current_user, liked_comment_ids=liked_comment_ids)


def _db_create_news_comment(
    news_id: int,
    request: CommentCreateRequest,
    current_user: Optional[Any],
) -> CommentItem | None:
    user = require_current_user(current_user)
    user_id = _get_current_user_id(user)
    content = _validate_comment_content(request.content, request.media_json)
    media_json_value = _serialize_comment_media_json(getattr(request, "media_json", None))
    create_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    has_media_json = _db_news_comment_has_media_json()
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id FROM news WHERE id = %s AND status = 1 LIMIT 1",
                [news_id],
            )
            news = cursor.fetchone()
            if news is None:
                return None

            if has_media_json:
                cursor.execute(
                    """
                    INSERT INTO news_comment (news_id, user_id, parent_id, content, media_json, like_count, status, created_at, updated_at)
                    VALUES (%s, %s, NULL, %s, %s, 0, 1, %s, %s)
                    """,
                    [news_id, user_id, content, media_json_value, create_time, create_time],
                )
            else:
                cursor.execute(
                    """
                    INSERT INTO news_comment (news_id, user_id, parent_id, content, like_count, status, created_at, updated_at)
                    VALUES (%s, %s, NULL, %s, 0, 1, %s, %s)
                    """,
                    [news_id, user_id, content, create_time, create_time],
                )
            comment_id = int(cursor.lastrowid)
            cursor.execute(
                """
                UPDATE news
                SET comment_count = comment_count + 1, updated_at = NOW()
                WHERE id = %s
                """,
                [news_id],
            )
        connection.commit()
        return CommentItem(
            id=comment_id,
            news_id=news_id,
            user_id=int(user_id or 0),
            username=_get_current_user_value(user, "username"),
            nickname=_get_current_user_value(user, "nickname"),
            avatar=_get_current_user_value(user, "avatar"),
            parent_id=None,
            content=content,
            like_count=0,
            status=1,
            create_time=create_time,
            media_json=_normalize_comment_media_json(getattr(request, "media_json", None)),
            is_liked=False,
            replies=[],
        )
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def _db_reply_comment(
    comment_id: int,
    request: CommentReplyRequest,
    current_user: Optional[Any],
) -> CommentItem | None:
    user = require_current_user(current_user)
    user_id = _get_current_user_id(user)
    parent_comment = _db_comment_row(comment_id)
    if parent_comment is None:
        return None

    content = _validate_comment_content(request.content, request.media_json)
    media_json_value = _serialize_comment_media_json(getattr(request, "media_json", None))
    create_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    has_media_json = _db_news_comment_has_media_json()
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            if has_media_json:
                cursor.execute(
                    """
                    INSERT INTO news_comment (news_id, user_id, parent_id, content, media_json, like_count, status, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, 0, 1, %s, %s)
                    """,
                    [
                        int(parent_comment["news_id"]),
                        user_id,
                        comment_id,
                        content,
                        media_json_value,
                        create_time,
                        create_time,
                    ],
                )
            else:
                cursor.execute(
                    """
                    INSERT INTO news_comment (news_id, user_id, parent_id, content, like_count, status, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, 0, 1, %s, %s)
                    """,
                    [
                        int(parent_comment["news_id"]),
                        user_id,
                        comment_id,
                        content,
                        create_time,
                        create_time,
                    ],
                )
            reply_id = int(cursor.lastrowid)
            cursor.execute(
                """
                UPDATE news
                SET comment_count = comment_count + 1, updated_at = NOW()
                WHERE id = %s
                """,
                [int(parent_comment["news_id"])],
            )
        connection.commit()
        return CommentItem(
            id=reply_id,
            news_id=int(parent_comment["news_id"]),
            user_id=int(user_id or 0),
            username=_get_current_user_value(user, "username"),
            nickname=_get_current_user_value(user, "nickname"),
            avatar=_get_current_user_value(user, "avatar"),
            parent_id=comment_id,
            content=content,
            like_count=0,
            status=1,
            create_time=create_time,
            media_json=_normalize_comment_media_json(getattr(request, "media_json", None)),
            reply_to_user_id=int(parent_comment.get("user_id") or 0),
            reply_to_username=str(parent_comment.get("username") or ""),
            reply_to_nickname=str(parent_comment.get("nickname") or ""),
            reply_to_content=str(parent_comment.get("content") or ""),
            is_liked=False,
            replies=[],
        )
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def _db_like_comment(comment_id: int, current_user: Optional[Any]) -> CommentLikeResult | None:
    user = require_current_user(current_user)
    user_id = _get_current_user_id(user)
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, like_count
                FROM news_comment
                WHERE id = %s AND status <> 4
                LIMIT 1
                """,
                [comment_id],
            )
            comment = cursor.fetchone()
            if comment is None:
                return None

            cursor.execute(
                """
                SELECT id
                FROM user_like
                WHERE user_id = %s AND target_id = %s AND target_type = 'news_comment'
                LIMIT 1
                """,
                [user_id, comment_id],
            )
            exists = cursor.fetchone() is not None
            if exists:
                return CommentLikeResult(
                    comment_id=comment_id,
                    liked=True,
                    like_count=int(comment["like_count"]),
                )

            cursor.execute(
                """
                INSERT INTO user_like (user_id, target_id, target_type, created_at)
                VALUES (%s, %s, 'news_comment', NOW())
                """,
                [user_id, comment_id],
            )
            cursor.execute(
                """
                UPDATE news_comment
                SET like_count = like_count + 1, updated_at = NOW()
                WHERE id = %s
                """,
                [comment_id],
            )
            cursor.execute("SELECT like_count FROM news_comment WHERE id = %s LIMIT 1", [comment_id])
            updated = cursor.fetchone()
        connection.commit()
        return CommentLikeResult(
            comment_id=comment_id,
            liked=True,
            like_count=int(updated["like_count"]) if updated else int(comment["like_count"]) + 1,
        )
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def _db_delete_news_comment(comment_id: int, current_user: Optional[Any]) -> dict[str, Any] | None:
    user = require_current_user(current_user)
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, news_id, user_id, status
                FROM news_comment
                WHERE id = %s AND status <> 4
                LIMIT 1
                """,
                [comment_id],
            )
            comment = cursor.fetchone()
            if comment is None:
                return None

            if not _can_delete_comment(user, int(comment["user_id"] or 0)):
                raise AppException(code=403, message="当前账号无权限访问该资源")

            cursor.execute(
                """
                UPDATE news_comment
                SET status = 4, updated_at = NOW()
                WHERE id = %s
                """,
                [comment_id],
            )
            cursor.execute(
                """
                UPDATE news
                SET comment_count = GREATEST(comment_count - 1, 0), updated_at = NOW()
                WHERE id = %s
                """,
                [int(comment["news_id"] or 0)],
            )
            cursor.execute("SELECT comment_count FROM news WHERE id = %s LIMIT 1", [int(comment["news_id"] or 0)])
            updated = cursor.fetchone()
        connection.commit()
        return {
            "comment_id": comment_id,
            "deleted": True,
            "news_id": int(comment["news_id"] or 0),
            "comment_count": int(updated["comment_count"]) if updated else 0,
        }
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def _mock_delete_news_comment(comment_id: int, current_user: Optional[Any]) -> dict[str, Any]:
    user = require_current_user(current_user)
    comment = None
    for item in MOCK_NEWS_COMMENTS:
        if int(item.get("id") or 0) == comment_id and int(item.get("status") or 0) != 4:
            comment = item
            break
    if comment is None:
        raise AppException(code=404, message="评论不存在")

    if not _can_delete_comment(user, int(comment.get("user_id") or 0)):
        raise AppException(code=403, message="当前账号无权限访问该资源")

    comment["status"] = 4
    news_id = int(comment.get("news_id") or 0)
    new_count = 0
    for news in MOCK_NEWS:
        if int(news.get("id") or 0) == news_id:
            news["comment_count"] = max(0, int(news.get("comment_count") or 0) - 1)
            news["update_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            new_count = int(news["comment_count"] or 0)
            break
    return {
        "comment_id": comment_id,
        "deleted": True,
        "news_id": news_id,
        "comment_count": new_count,
    }


def _mock_like_news(news_id: int, current_user: Optional[Any]) -> InteractionResult:
    user = require_current_user(current_user)
    news = _mock_news_row(news_id)
    if news is None:
        raise AppException(code=404, message="新闻不存在")
    user_id = _get_current_user_value(user, "id")

    if _has_news_relation(MOCK_NEWS_LIKES, user_id, news_id):
        return InteractionResult(
            target_id=news_id,
            target_type="news",
            action="like",
            status=True,
            like_count=int(news.get("like_count") or 0),
            message="已点赞",
        )

    MOCK_NEWS_LIKES.append({"user_id": user_id, "news_id": news_id})
    news["like_count"] = int(news.get("like_count") or 0) + 1
    for item in MOCK_NEWS:
        if int(item.get("id") or 0) == news_id:
            item["like_count"] = news["like_count"]
            break
    return InteractionResult(
        target_id=news_id,
        target_type="news",
        action="like",
        status=True,
        like_count=news["like_count"],
        message="点赞成功",
    )


def _mock_unlike_news(news_id: int, current_user: Optional[Any]) -> InteractionResult:
    user = require_current_user(current_user)
    news = _mock_news_row(news_id)
    if news is None:
        raise AppException(code=404, message="新闻不存在")
    user_id = _get_current_user_value(user, "id")
    removed = _remove_news_relation(MOCK_NEWS_LIKES, user_id, news_id)
    if removed:
        news["like_count"] = max(int(news.get("like_count") or 0) - 1, 0)
        for item in MOCK_NEWS:
            if int(item.get("id") or 0) == news_id:
                item["like_count"] = news["like_count"]
                break

    return InteractionResult(
        target_id=news_id,
        target_type="news",
        action="unlike",
        status=False,
        like_count=int(news.get("like_count") or 0),
        message="已取消点赞" if removed else "当前未点赞",
    )


def _mock_favorite_news(news_id: int, current_user: Optional[Any]) -> InteractionResult:
    user = require_current_user(current_user)
    news = _mock_news_row(news_id)
    if news is None:
        raise AppException(code=404, message="新闻不存在")
    user_id = _get_current_user_value(user, "id")

    if _has_news_relation(MOCK_NEWS_FAVORITES, user_id, news_id):
        return InteractionResult(
            target_id=news_id,
            target_type="news",
            action="favorite",
            status=True,
            favorite_count=int(news.get("favorite_count") or 0),
            message="已收藏",
        )

    MOCK_NEWS_FAVORITES.append({"user_id": user_id, "news_id": news_id})
    news["favorite_count"] = int(news.get("favorite_count") or 0) + 1
    for item in MOCK_NEWS:
        if int(item.get("id") or 0) == news_id:
            item["favorite_count"] = news["favorite_count"]
            break
    return InteractionResult(
        target_id=news_id,
        target_type="news",
        action="favorite",
        status=True,
        favorite_count=news["favorite_count"],
        message="收藏成功",
    )


def _mock_unfavorite_news(news_id: int, current_user: Optional[Any]) -> InteractionResult:
    user = require_current_user(current_user)
    news = _mock_news_row(news_id)
    if news is None:
        raise AppException(code=404, message="新闻不存在")
    user_id = _get_current_user_value(user, "id")
    removed = _remove_news_relation(MOCK_NEWS_FAVORITES, user_id, news_id)
    if removed:
        news["favorite_count"] = max(int(news.get("favorite_count") or 0) - 1, 0)
        for item in MOCK_NEWS:
            if int(item.get("id") or 0) == news_id:
                item["favorite_count"] = news["favorite_count"]
                break

    return InteractionResult(
        target_id=news_id,
        target_type="news",
        action="unfavorite",
        status=False,
        favorite_count=int(news.get("favorite_count") or 0),
        message="已取消收藏" if removed else "当前未收藏",
    )


def _mock_get_news_comments(news_id: int, current_user: Optional[Any] = None) -> CommentListResponse:
    if _mock_news_row(news_id) is None:
        raise AppException(code=404, message="新闻不存在")
    rows = [
        dict(comment)
        for comment in MOCK_NEWS_COMMENTS
        if int(comment.get("news_id") or 0) == news_id and int(comment.get("status") or 0) in (1, 2, 4)
    ]
    comment_map = {int(row["id"]): row for row in rows}
    for row in rows:
        parent_id = row.get("parent_id")
        if parent_id is not None:
            parent_comment = comment_map.get(int(parent_id))
            if parent_comment:
                row["reply_to_user_id"] = int(parent_comment.get("user_id") or 0)
                row["reply_to_username"] = normalize_text(parent_comment.get("username") or "")
                row["reply_to_nickname"] = normalize_text(parent_comment.get("nickname") or "")
                row["reply_to_content"] = normalize_text(parent_comment.get("content") or "")
        else:
            row["reply_to_user_id"] = None
            row["reply_to_username"] = ""
            row["reply_to_nickname"] = ""
            row["reply_to_content"] = ""
    return _assemble_comment_tree(rows, current_user=current_user, liked_comment_ids=None)


def _mock_create_news_comment(
    news_id: int,
    request: CommentCreateRequest,
    current_user: Optional[Any],
) -> CommentItem:
    user = require_current_user(current_user)
    news = _mock_news_row(news_id)
    if news is None:
        raise AppException(code=404, message="新闻不存在")

    content = _validate_comment_content(request.content, request.media_json)
    comment_id = get_next_comment_id()
    create_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    media_json_dict = _normalize_comment_media_json(getattr(request, "media_json", None))
    comment = {
        "id": comment_id,
        "news_id": news_id,
        "user_id": _get_current_user_value(user, "id"),
        "username": _get_current_user_value(user, "username"),
        "nickname": _get_current_user_value(user, "nickname"),
        "avatar": _get_current_user_value(user, "avatar"),
        "parent_id": None,
        "content": content,
        "media_json": media_json_dict,
        "like_count": 0,
        "status": 1,
        "create_time": create_time,
    }
    MOCK_NEWS_COMMENTS.append(comment)
    news["comment_count"] = int(news.get("comment_count") or 0) + 1
    for item in MOCK_NEWS:
        if int(item.get("id") or 0) == news_id:
            item["comment_count"] = news["comment_count"]
            break
    return CommentItem(**comment, is_liked=False, replies=[])


def _mock_reply_comment(
    comment_id: int,
    request: CommentReplyRequest,
    current_user: Optional[Any],
) -> CommentItem:
    user = require_current_user(current_user)
    parent_comment = _mock_comment_row(comment_id)
    if parent_comment is None:
        raise AppException(code=404, message="评论不存在")

    content = _validate_comment_content(request.content, request.media_json)
    reply_id = get_next_comment_id()
    create_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    reply = {
        "id": reply_id,
        "news_id": int(parent_comment["news_id"]),
        "user_id": _get_current_user_value(user, "id"),
        "username": _get_current_user_value(user, "username"),
        "nickname": _get_current_user_value(user, "nickname"),
        "avatar": _get_current_user_value(user, "avatar"),
        "parent_id": comment_id,
        "content": content,
        "like_count": 0,
        "status": 1,
        "create_time": create_time,
        "media_json": _normalize_comment_media_json(getattr(request, "media_json", None)),
    }
    MOCK_NEWS_COMMENTS.append(reply)
    for item in MOCK_NEWS:
        if int(item.get("id") or 0) == int(parent_comment["news_id"]):
            item["comment_count"] = int(item.get("comment_count") or 0) + 1
            break
    return CommentItem(
        **reply,
        reply_to_user_id=int(parent_comment.get("user_id") or 0),
        reply_to_username=str(parent_comment.get("username") or ""),
        reply_to_nickname=str(parent_comment.get("nickname") or ""),
        reply_to_content=str(parent_comment.get("content") or ""),
        is_liked=False,
        replies=[],
    )


def _mock_like_comment(comment_id: int, current_user: Optional[Any]) -> CommentLikeResult:
    user = require_current_user(current_user)
    comment = _mock_comment_row(comment_id)
    if comment is None:
        raise AppException(code=404, message="评论不存在")
    user_id = _get_current_user_value(user, "id")
    if is_comment_liked(comment_id, user):
        return CommentLikeResult(comment_id=comment_id, liked=True, like_count=int(comment.get("like_count") or 0))

    MOCK_COMMENT_LIKES.append({"user_id": user_id, "comment_id": comment_id})
    comment["like_count"] = int(comment.get("like_count") or 0) + 1
    for item in MOCK_NEWS_COMMENTS:
        if int(item.get("id") or 0) == comment_id:
            item["like_count"] = comment["like_count"]
            break
    return CommentLikeResult(comment_id=comment_id, liked=True, like_count=comment["like_count"])


def delete_news_comment(comment_id: int, current_user: Optional[Any]) -> dict[str, Any]:
    """鍒犻櫎鏂伴椈璇勮锛涙暟鎹簱浼樺厛锛屽け璐ュ悗鍥為€€鍒?mock銆?"""

    try:
        result = _db_delete_news_comment(comment_id=comment_id, current_user=current_user)
        if result is not None:
            return result
    except Exception as exc:  # noqa: BLE001
        logger.warning("鏁版嵁搴撳垹闄よ瘎璁哄け璐ワ紝鍥為€€ mock锛?s", exc)
    return _mock_delete_news_comment(comment_id=comment_id, current_user=current_user)


def like_news(news_id: int, current_user: Optional[Any]) -> InteractionResult:
    """点赞新闻；数据库优先，失败后回退到 mock。"""

    try:
        result = _db_like_news(news_id, current_user)
        if result is not None:
            return result
    except Exception as exc:  # noqa: BLE001
        logger.warning("数据库点赞新闻失败，回退 mock：%s", exc)
    return _mock_like_news(news_id, current_user)


def unlike_news(news_id: int, current_user: Optional[Any]) -> InteractionResult:
    """取消新闻点赞；数据库优先，失败后回退到 mock。"""

    try:
        result = _db_unlike_news(news_id, current_user)
        if result is not None:
            return result
    except Exception as exc:  # noqa: BLE001
        logger.warning("数据库取消点赞失败，回退 mock：%s", exc)
    return _mock_unlike_news(news_id, current_user)


def favorite_news(news_id: int, current_user: Optional[Any]) -> InteractionResult:
    """收藏新闻；数据库优先，失败后回退到 mock。"""

    try:
        result = _db_favorite_news(news_id, current_user)
        if result is not None:
            return result
    except Exception as exc:  # noqa: BLE001
        logger.warning("数据库收藏新闻失败，回退 mock：%s", exc)
    return _mock_favorite_news(news_id, current_user)


def unfavorite_news(news_id: int, current_user: Optional[Any]) -> InteractionResult:
    """取消新闻收藏；数据库优先，失败后回退到 mock。"""

    try:
        result = _db_unfavorite_news(news_id, current_user)
        if result is not None:
            return result
    except Exception as exc:  # noqa: BLE001
        logger.warning("数据库取消收藏失败，回退 mock：%s", exc)
    return _mock_unfavorite_news(news_id, current_user)


def build_comment_tree(news_id: int, current_user: Optional[Any] = None) -> CommentListResponse:
    """按 parent_id 将指定新闻的评论组装为树形结构（mock 兜底路径）。"""

    visible_comments = [
        dict(comment)
        for comment in MOCK_NEWS_COMMENTS
        if int(comment.get("news_id") or 0) == news_id and int(comment.get("status") or 0) in (1, 2, 4)
    ]
    return _assemble_comment_tree(visible_comments, current_user=current_user, liked_comment_ids=None)


def get_news_comments(news_id: int, current_user: Optional[Any] = None) -> CommentListResponse:
    """获取新闻评论树；数据库优先，失败后回退到 mock。"""

    try:
        result = _db_get_news_comments(news_id=news_id, current_user=current_user)
        if result is not None:
            return result
    except Exception as exc:  # noqa: BLE001
        logger.warning("数据库读取评论列表失败，回退 mock：%s", exc)
    return _mock_get_news_comments(news_id=news_id, current_user=current_user)


def _has_comment_media(media_json: Any) -> bool:
    if not media_json:
        return False
    if isinstance(media_json, dict):
        return bool(media_json.get("images") or media_json.get("emojis") or media_json.get("files"))
    images = getattr(media_json, "images", None) or []
    emojis = getattr(media_json, "emojis", None) or []
    files = getattr(media_json, "files", None) or []
    return len(images) > 0 or len(emojis) > 0 or len(files) > 0


def _validate_comment_content(content: str, media_json: Any = None) -> str:
    normalized_content = content.strip() if content else ""
    if not normalized_content and not _has_comment_media(media_json):
        raise AppException(code=400, message="评论内容不能为空")
    return normalized_content


def create_news_comment(
    news_id: int,
    request: CommentCreateRequest,
    current_user: Optional[Any],
) -> CommentItem:
    """发布一级新闻评论；数据库优先，失败后回退到 mock。"""

    user = require_current_user(current_user)
    try:
        result = _db_create_news_comment(news_id=news_id, request=request, current_user=user)
        if result is not None:
            return result
    except Exception as exc:  # noqa: BLE001
        logger.warning("数据库发布评论失败，回退 mock：%s", exc)
    return _mock_create_news_comment(news_id=news_id, request=request, current_user=user)


def reply_comment(
    comment_id: int,
    request: CommentReplyRequest,
    current_user: Optional[Any],
) -> CommentItem:
    """回复指定评论；数据库优先，失败后回退到 mock。"""

    user = require_current_user(current_user)
    try:
        result = _db_reply_comment(comment_id=comment_id, request=request, current_user=user)
        if result is not None:
            return result
    except Exception as exc:  # noqa: BLE001
        logger.warning("数据库回复评论失败，回退 mock：%s", exc)
    return _mock_reply_comment(comment_id=comment_id, request=request, current_user=user)


def like_comment(comment_id: int, current_user: Optional[Any]) -> CommentLikeResult:
    """点赞评论；数据库优先，失败后回退到 mock。"""

    try:
        result = _db_like_comment(comment_id=comment_id, current_user=current_user)
        if result is not None:
            return result
    except Exception as exc:  # noqa: BLE001
        logger.warning("数据库点赞评论失败，回退 mock：%s", exc)
    return _mock_like_comment(comment_id=comment_id, current_user=current_user)

