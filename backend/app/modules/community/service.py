"""社区模块服务层：数据库优先，mock 兜底。"""

from __future__ import annotations

import json
import logging
from copy import deepcopy
from datetime import datetime
from functools import lru_cache
from typing import Any, Dict, List, Optional, Set

from app.common.exceptions import AppException
from app.common.utils import format_datetime, normalize_text, paginate
from app.db.database import execute_insert, execute_one, execute_query, execute_update, get_connection
from app.mock.community import (
    MOCK_COMMUNITY_BLOCKS,
    MOCK_COMMUNITY_COMMENT_LIKES,
    MOCK_COMMUNITY_COMMENTS,
    MOCK_COMMUNITY_HOT_TOPICS,
    MOCK_COMMUNITY_POSTS,
    MOCK_COMMUNITY_POST_FAVORITES,
    MOCK_COMMUNITY_POST_LIKES,
)
from app.mock.news import MOCK_NEWS
from app.modules.community.schema import (
    AIHelperResponse,
    BlockResponse,
    CommentItem,
    CommentLikeResult,
    CommentListResponse,
    CommentsSummaryResponse,
    CommunityAiMessageCreate,
    CommunityAiMessageItem,
    CommunityAiSessionCreate,
    CommunityAiSessionDetailResponse,
    CommunityAiSessionItem,
    CommunityAiSessionListResponse,
    CommunityAiMessageSendResponse,
    CommunityPost,
    CreateCommentRequest,
    CreatePostRequest,
    FavoriteResponse,
    HotSearchItem,
    LikeResponse,
    MyCommunityPostListResponse,
    PostListResponse,
    ReceivedInteractionItem,
    ReceivedInteractionListResponse,
)

logger = logging.getLogger(__name__)

VALID_COMMUNITY_TAGS = {"时政", "经济", "科技", "教育", "军事", "社会", "国际", "体育", "娱乐", "健康"}


def _validate_tags(tags: list[str]) -> list[str]:
    if not tags:
        return []
    return [tag for tag in tags if tag in VALID_COMMUNITY_TAGS]


def get_available_tags() -> list[dict[str, Any]]:
    return [{"name": tag, "count": 0} for tag in sorted(VALID_COMMUNITY_TAGS)]


def _now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _get_current_user_id(current_user: Optional[Any]) -> Optional[int]:
    if current_user is None:
        return None
    if isinstance(current_user, dict):
        return current_user.get("id")
    return getattr(current_user, "id", None)


def _format_datetime(value: Any) -> str:
    return format_datetime(value) or _now_text()


@lru_cache(maxsize=1)
def _db_post_comment_has_media_json() -> bool:
    try:
        row = execute_one(
            """
            SELECT COUNT(*) AS cnt
            FROM information_schema.columns
            WHERE table_schema = DATABASE()
              AND table_name = 'post_comment'
              AND column_name = 'media_json'
            """,
        )
        return bool(int(row.get("cnt") or 0)) if row else False
    except Exception:  # noqa: BLE001
        return False


@lru_cache(maxsize=1)
def _community_post_has_images_column() -> bool:
    try:
        row = execute_one(
            """
            SELECT COUNT(*) AS cnt
            FROM information_schema.columns
            WHERE table_schema = DATABASE()
              AND table_name = 'community_post'
              AND column_name = 'images'
            """,
        )
        return bool(int(row.get("cnt") or 0)) if row else False
    except Exception:  # noqa: BLE001
        return False


def _normalize_media_json(value: Any) -> Any:
    if value in (None, ""):
        return None
    if hasattr(value, "model_dump"):
        value = value.model_dump()
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, bytes):
        value = value.decode("utf-8", errors="ignore")
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return text
    return value


def _serialize_media_json(value: Any) -> Optional[str]:
    normalized = _normalize_media_json(value)
    if normalized is None:
        return None
    if isinstance(normalized, str):
        return normalized
    return json.dumps(normalized, ensure_ascii=False)


def _parse_json_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, bytes):
        value = value.decode("utf-8", errors="ignore")
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return []
        try:
            parsed = json.loads(text)
            if isinstance(parsed, list):
                return [str(item) for item in parsed]
        except json.JSONDecodeError:
            return []
    return []


def _current_user_id(current_user: Optional[Any]) -> Optional[int]:
    if current_user is None:
        return None
    if isinstance(current_user, dict):
        value = current_user.get("id")
    else:
        value = getattr(current_user, "id", None)
    if value is None:
        return None
    return int(value)


def _current_user_name(current_user: Optional[Any]) -> str:
    if current_user is None:
        return "匿名用户"
    if isinstance(current_user, dict):
        return normalize_text(current_user.get("nickname") or current_user.get("username"))
    return normalize_text(getattr(current_user, "nickname", "") or getattr(current_user, "username", ""))


def _can_delete_comment(current_user: Any, comment_user_id: int) -> bool:
    current_user_id = _current_user_id(current_user)
    if current_user_id is None:
        return False
    if current_user_id == comment_user_id:
        return True
    role = ""
    if isinstance(current_user, dict):
        role = str(current_user.get("role", "") or "").lower()
    else:
        role = str(getattr(current_user, "role", "") or "").lower()
    return role in {"admin", "editor"}


def _db_has_posts() -> bool:
    row = execute_one("SELECT COUNT(*) AS total FROM community_post WHERE status = 1")
    return int((row or {}).get("total") or 0) > 0


def _db_has_hot_topics() -> bool:
    row = execute_one("SELECT COUNT(*) AS total FROM hot_topic")
    return int((row or {}).get("total") or 0) > 0


@lru_cache(maxsize=1)
def _community_post_has_tags_column() -> bool:
    row = execute_one(
        """
        SELECT COUNT(*) AS total
        FROM information_schema.columns
        WHERE table_schema = DATABASE()
          AND table_name = 'community_post'
          AND column_name = 'tags'
        """
    )
    return int((row or {}).get("total") or 0) > 0




def _mock_post_lookup() -> dict[int, dict[str, Any]]:
    return {int(item["id"]): deepcopy(item) for item in MOCK_COMMUNITY_POSTS}


def _mock_comment_lookup() -> dict[int, dict[str, Any]]:
    return {int(item["id"]): deepcopy(item) for item in MOCK_COMMUNITY_COMMENTS}


def _mock_is_post_liked(post_id: int, user_id: Optional[int]) -> bool:
    return user_id is not None and any(
        item["user_id"] == user_id and item["post_id"] == post_id for item in FALLBACK_POST_LIKES
    )


def _mock_is_post_favorited(post_id: int, user_id: Optional[int]) -> bool:
    return user_id is not None and any(
        item["user_id"] == user_id and item["post_id"] == post_id for item in FALLBACK_POST_FAVORITES
    )


def _mock_is_post_blocked(author_id: int, user_id: Optional[int]) -> bool:
    return user_id is not None and any(
        item["user_id"] == user_id and item["blocked_user_id"] == author_id for item in FALLBACK_BLOCKS
    )


def _mock_is_comment_liked(comment_id: int, user_id: Optional[int]) -> bool:
    return user_id is not None and any(
        item["user_id"] == user_id and item["comment_id"] == comment_id for item in FALLBACK_COMMENT_LIKES
    )


def _resolve_post_author(user_id: int, nickname: str, username: str, fallback_author: str = "") -> str:
    name = nickname or username or fallback_author
    if name:
        return name
    return f"用户{user_id}"


def _post_row_to_item(
    row: dict[str, Any],
    *,
    liked: bool = False,
    favorited: bool = False,
    blocked: bool = False,
) -> dict[str, Any]:
    like_count = int(row.get("like_count") or 0)
    comment_count = int(row.get("comment_count") or 0)
    favorite_count = int(row.get("favorite_count") or 0)
    heat_score = int(row.get("heat_score") or 0)
    view_count = int(row.get("view_count") or 0)
    author_name = _resolve_post_author(
        int(row.get("user_id") or 0),
        normalize_text(row.get("nickname")),
        normalize_text(row.get("username")),
        normalize_text(row.get("author")),
    )
    tags = _parse_json_list(row.get("tags"))
    images = _parse_json_list(row.get("images"))

    return {
        "id": int(row.get("id") or 0),
        "user_id": int(row.get("user_id") or 0),
        "username": normalize_text(row.get("username")),
        "nickname": normalize_text(row.get("nickname")),
        "avatar": normalize_text(row.get("avatar")),
        "title": normalize_text(row.get("title")),
        "content": normalize_text(row.get("content")),
        "related_news_id": row.get("related_news_id"),
        "related_news_title": normalize_text(row.get("related_news_title")),
        "topic_id": row.get("topic_id"),
        "images": images,
        "like_count": like_count,
        "comment_count": comment_count,
        "favorite_count": favorite_count,
        "view_count": view_count,
        "heat_score": heat_score,
        "status": int(row.get("status") or 0),
        "create_time": _format_datetime(row.get("create_time")),
        "update_time": _format_datetime(row.get("update_time")),
        "tags": tags,
        "author": author_name,
        "author_id": int(row.get("author_id") or row.get("user_id") or 0),
        "created_at": _format_datetime(row.get("create_time")),
        "updated_at": _format_datetime(row.get("update_time")),
        "likes": like_count,
        "comments": comment_count,
        "views": view_count,
        "liked": liked,
        "is_liked": liked,
        "is_favorited": favorited,
        "is_blocked": blocked,
    }


def _comment_row_to_item(
    row: dict[str, Any],
    *,
    liked: bool = False,
    replies: Optional[list[dict[str, Any]]] = None,
) -> dict[str, Any]:
    author_name = _resolve_post_author(
        int(row.get("user_id") or 0),
        normalize_text(row.get("nickname")),
        normalize_text(row.get("username")),
        normalize_text(row.get("author")),
    )
    like_count = int(row.get("like_count") or 0)
    status = int(row.get("status") or 0)
    if status == 4:
        content = "该评论已删除"
    elif status == 2:
        content = "该评论已被折叠"
    else:
        content = normalize_text(row.get("content"))
    item = {
        "id": int(row.get("id") or 0),
        "post_id": int(row.get("post_id") or 0),
        "user_id": int(row.get("user_id") or 0),
        "username": normalize_text(row.get("username")),
        "nickname": normalize_text(row.get("nickname")),
        "avatar": normalize_text(row.get("avatar")),
        "parent_id": row.get("parent_id"),
        "content": content,
        "like_count": like_count,
        "status": status,
        "create_time": _format_datetime(row.get("create_time")),
        "media_json": _normalize_media_json(row.get("media_json")),
        "reply_to_user_id": row.get("reply_to_user_id"),
        "reply_to_username": normalize_text(row.get("reply_to_username") or ""),
        "reply_to_nickname": normalize_text(row.get("reply_to_nickname") or ""),
        "reply_to_content": normalize_text(row.get("reply_to_content") or ""),
        "author": author_name,
        "author_id": int(row.get("author_id") or row.get("user_id") or 0),
        "created_at": _format_datetime(row.get("create_time")),
        "likes": like_count,
        "is_liked": liked,
        "replies": replies or [],
    }
    return item


def _build_comment_tree(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    nodes: dict[int, dict[str, Any]] = {}
    roots: list[dict[str, Any]] = []
    for item in items:
        node = dict(item)
        node.setdefault("replies", [])
        nodes[int(node["id"])] = node

    for node in nodes.values():
        parent_id = node.get("parent_id")
        if parent_id is None or int(parent_id) not in nodes:
            roots.append(node)
        else:
            nodes[int(parent_id)]["replies"].append(node)

    roots.sort(key=lambda item: (-int(item.get("like_count") or 0), item.get("create_time"), int(item.get("id") or 0)))
    for node in nodes.values():
        node["replies"].sort(key=lambda reply: (-int(reply.get("like_count") or 0), reply.get("create_time"), int(reply.get("id") or 0)))
    return roots


def _mock_posts_sorted() -> list[dict[str, Any]]:
    posts = [deepcopy(item) for item in MOCK_COMMUNITY_POSTS if int(item.get("status", 0)) == 1]
    posts.sort(
        key=lambda item: (
            int(item.get("heat_score") or 0),
            _format_datetime(item.get("create_time")),
            int(item.get("id") or 0),
        ),
        reverse=True,
    )
    return posts


def _mock_news_title_map() -> dict[int, str]:
    return {int(item["id"]): normalize_text(item.get("title")) for item in MOCK_NEWS}


def _mock_comments_for_post(post_id: int) -> list[dict[str, Any]]:
    comments = [
        deepcopy(item)
        for item in MOCK_COMMUNITY_COMMENTS
        if int(item.get("post_id") or 0) == post_id and int(item.get("status") or 0) in (1, 2, 4)
    ]
    comments.sort(
        key=lambda item: (
            _format_datetime(item.get("create_time")),
            int(item.get("id") or 0),
        ),
        reverse=True,
    )
    return comments


def _mock_hot_topics() -> list[dict[str, Any]]:
    topics = [deepcopy(item) for item in MOCK_COMMUNITY_HOT_TOPICS]
    topics.sort(key=lambda item: (int(item.get("rank_no") or 0), -int(item.get("heat_score") or 0)))
    return topics


def _db_post_liked_ids(user_id: int, post_ids: list[int]) -> set[int]:
    if not post_ids:
        return set()
    placeholders = ",".join(["%s"] * len(post_ids))
    rows = execute_query(
        f"""
        SELECT target_id
        FROM user_like
        WHERE user_id = %s
          AND target_type = 'post'
          AND target_id IN ({placeholders})
        """,
        [user_id, *post_ids],
    )
    return {int(row["target_id"]) for row in rows}


def _db_post_favorited_ids(user_id: int, post_ids: list[int]) -> set[int]:
    if not post_ids:
        return set()
    placeholders = ",".join(["%s"] * len(post_ids))
    rows = execute_query(
        f"""
        SELECT target_id
        FROM favorite
        WHERE user_id = %s
          AND target_type = 'post'
          AND target_id IN ({placeholders})
        """,
        [user_id, *post_ids],
    )
    return {int(row["target_id"]) for row in rows}


def _db_blocked_ids(user_id: int) -> set[int]:
    rows = execute_query(
        """
        SELECT blocked_user_id
        FROM user_block
        WHERE user_id = %s
        """,
        [user_id],
    )
    return {int(row["blocked_user_id"]) for row in rows}


def _db_comment_liked_ids(user_id: int, comment_ids: list[int]) -> set[int]:
    if not comment_ids:
        return set()
    placeholders = ",".join(["%s"] * len(comment_ids))
    rows = execute_query(
        f"""
        SELECT target_id
        FROM user_like
        WHERE user_id = %s
          AND target_type = 'post_comment'
          AND target_id IN ({placeholders})
        """,
        [user_id, *comment_ids],
    )
    return {int(row["target_id"]) for row in rows}


def _db_posts_total(
    keyword: Optional[str] = None,
    tag: Optional[str] = None,
) -> int:
    where_sql = ["cp.status = 1"]
    params: list[Any] = []
    if keyword and keyword.strip():
        like_value = f"%{keyword.strip()}%"
        where_sql.append("(cp.title LIKE %s OR cp.content LIKE %s)")
        params.extend([like_value, like_value])
    if tag and tag.strip():
        where_sql.append("JSON_CONTAINS(cp.tags, %s)")
        params.append(json.dumps(tag))
    row = execute_one(
        f"""
        SELECT COUNT(*) AS total
        FROM community_post cp
        WHERE {" AND ".join(where_sql)}
        """,
        params,
    )
    return int((row or {}).get("total") or 0)


def _db_get_posts(
    page: int = 1,
    page_size: int = 10,
    keyword: Optional[str] = None,
    tag: Optional[str] = None,
    sort: str = "hot",
    current_user: Optional[Any] = None,
) -> dict[str, Any] | None:
    total = _db_posts_total(keyword=keyword, tag=tag)
    if total == 0:
        return None

    normalized_page = max(page, 1)
    normalized_page_size = max(page_size, 1)
    params: list[Any] = []
    clauses = ["cp.status = 1"]
    if keyword and keyword.strip():
        like_value = f"%{keyword.strip()}%"
        clauses.append("(cp.title LIKE %s OR cp.content LIKE %s)")
        params.extend([like_value, like_value])
    if tag and tag.strip():
        clauses.append("JSON_CONTAINS(cp.tags, %s)")
        params.append(json.dumps(tag))

    # 排序方式
    if sort == "latest":
        order_clause = "cp.created_at DESC, cp.id DESC"
    else:
        order_clause = """COALESCE(cp.heat_score, 0) DESC,
                         COALESCE(cp.comment_count, 0) DESC,
                         COALESCE(cp.like_count, 0) DESC,
                         COALESCE(cp.favorite_count, 0) DESC,
                         cp.created_at DESC,
                         cp.id DESC"""

    images_expr = "cp.images" if _community_post_has_images_column() else "'[]'"
    rows = execute_query(
        f"""
        SELECT
            cp.id,
            cp.user_id,
            u.username,
            u.nickname,
            u.avatar,
            cp.title,
            cp.content,
            cp.related_news_id,
            COALESCE(n.title, '') AS related_news_title,
            cp.topic_id,
            {images_expr} AS images,
            cp.like_count,
            cp.comment_count,
            cp.favorite_count,
            cp.view_count,
            cp.heat_score,
            cp.status,
            cp.created_at AS create_time,
            cp.updated_at AS update_time,
            { 'cp.tags' if _community_post_has_tags_column() else 'NULL' } AS tags
        FROM community_post cp
        LEFT JOIN `user` u ON u.id = cp.user_id
        LEFT JOIN news n ON n.id = cp.related_news_id
        WHERE {" AND ".join(clauses)}
        ORDER BY {order_clause}
        LIMIT %s OFFSET %s
        """,
        params + [normalized_page_size, (normalized_page - 1) * normalized_page_size],
    )

    current_user_id = _current_user_id(current_user)
    liked_ids = _db_post_liked_ids(current_user_id, [int(row["id"]) for row in rows]) if current_user_id else set()
    favorited_ids = _db_post_favorited_ids(current_user_id, [int(row["id"]) for row in rows]) if current_user_id else set()
    blocked_ids = _db_blocked_ids(current_user_id) if current_user_id else set()

    items = []
    for row in rows:
        author_id = int(row.get("user_id") or 0)
        liked = int(row["id"]) in liked_ids
        favorited = int(row["id"]) in favorited_ids
        blocked = author_id in blocked_ids if blocked_ids else False
        tags_value = row.get("tags")
        if isinstance(tags_value, str):
            tags = _parse_json_list(tags_value)
        elif isinstance(tags_value, list):
            tags = [str(item) for item in tags_value]
        else:
            tags = []

        item = _post_row_to_item(
            {
                **row,
                "tags": tags,
                "author_id": author_id,
            },
            liked=liked,
            favorited=favorited,
            blocked=blocked,
        )
        items.append(item)

    return {
        "list": items,
        "total": total,
        "page": normalized_page,
        "page_size": normalized_page_size,
    }


def _db_get_post(post_id: int, current_user: Optional[Any] = None) -> dict[str, Any] | None:
    images_expr = "cp.images" if _community_post_has_images_column() else "'[]'"
    tags_expr = "cp.tags" if _community_post_has_tags_column() else "NULL"
    row = execute_one(
        f"""
        SELECT
            cp.id,
            cp.user_id,
            u.username,
            u.nickname,
            u.avatar,
            cp.title,
            cp.content,
            cp.related_news_id,
            COALESCE(n.title, '') AS related_news_title,
            cp.topic_id,
            cp.like_count,
            cp.comment_count,
            cp.favorite_count,
            cp.view_count,
            cp.heat_score,
            cp.status,
            cp.created_at AS create_time,
            cp.updated_at AS update_time,
            {tags_expr} AS tags,
            {images_expr} AS images
        FROM community_post cp
        LEFT JOIN `user` u ON u.id = cp.user_id
        LEFT JOIN news n ON n.id = cp.related_news_id
        WHERE cp.id = %s AND cp.status = 1
        LIMIT 1
        """,
        [post_id],
    )
    if row is None:
        return None

    current_user_id = _current_user_id(current_user)
    liked = False
    favorited = False
    blocked = False
    if current_user_id is not None:
        liked = execute_one(
            """
            SELECT id FROM user_like
            WHERE user_id = %s AND target_type = 'post' AND target_id = %s
            LIMIT 1
            """,
            [current_user_id, post_id],
        ) is not None
        favorited = execute_one(
            """
            SELECT id FROM favorite
            WHERE user_id = %s AND target_type = 'post' AND target_id = %s
            LIMIT 1
            """,
            [current_user_id, post_id],
        ) is not None
        blocked = execute_one(
            """
            SELECT id FROM user_block
            WHERE user_id = %s AND blocked_user_id = %s
            LIMIT 1
            """,
            [current_user_id, int(row.get("user_id") or 0)],
        ) is not None

    tags_value = row.get("tags")
    if isinstance(tags_value, str):
        tags = _parse_json_list(tags_value)
    elif isinstance(tags_value, list):
        tags = [str(item) for item in tags_value]
    else:
        tags = []

    return _post_row_to_item(
        {
            **row,
            "tags": tags,
        },
        liked=liked,
        favorited=favorited,
        blocked=blocked,
    )


def _db_comment_rows(post_id: int, current_user: Optional[Any] = None) -> list[dict[str, Any]] | None:
    post_exists = execute_one(
        "SELECT id FROM community_post WHERE id = %s AND status = 1 LIMIT 1",
        [post_id],
    )
    if post_exists is None:
        return None

    media_json_column = "pc.media_json" if _db_post_comment_has_media_json() else "NULL AS media_json"
    rows = execute_query(
        f"""
        SELECT
            pc.id,
            pc.post_id,
            pc.user_id,
            u.username,
            u.nickname,
            u.avatar,
            pc.parent_id,
            pc.content,
            pc.like_count,
            pc.status,
            pc.created_at AS create_time,
            {media_json_column},
            COALESCE(ru.id, NULL) AS reply_to_user_id,
            COALESCE(ru.username, '') AS reply_to_username,
            COALESCE(ru.nickname, '') AS reply_to_nickname,
            COALESCE(parent_pc.content, '') AS reply_to_content
        FROM post_comment pc
        LEFT JOIN `user` u ON u.id = pc.user_id
        LEFT JOIN post_comment parent_pc ON parent_pc.id = pc.parent_id
        LEFT JOIN `user` ru ON ru.id = parent_pc.user_id
        WHERE pc.post_id = %s AND pc.status IN (1, 2, 4)
        ORDER BY pc.created_at ASC, pc.id ASC
        """,
        [post_id],
    )
    if rows is None:
        return None

    current_user_id = _current_user_id(current_user)
    liked_ids = _db_comment_liked_ids(current_user_id, [int(row["id"]) for row in rows]) if current_user_id else set()
    items: list[dict[str, Any]] = []
    for row in rows:
        liked = int(row["id"]) in liked_ids
        items.append(
            _comment_row_to_item(
                {
                    **row,
                    "author": _resolve_post_author(
                        int(row.get("user_id") or 0),
                        normalize_text(row.get("nickname")),
                        normalize_text(row.get("username")),
                    ),
                    "author_id": int(row.get("user_id") or 0),
                },
                liked=liked,
            )
        )
    return items


def _db_hot_topics(limit: int = 10) -> list[dict[str, Any]] | None:
    rows = execute_query(
        """
        SELECT
            p.id,
            p.title,
            'post' AS target_type,
            p.id AS target_id,
            0 AS rank_no,
            p.tags AS tags_json,
            p.updated_at AS update_time,
            p.created_at AS create_time,
            COALESCE(p.view_count, 0) AS view_count,
            COALESCE(p.favorite_count, 0) AS favorite_count,
            (
                COALESCE(p.like_count, 0) * 4
                + COALESCE(p.favorite_count, 0) * 5
                + COALESCE(p.comment_count, 0) * 6
                + COALESCE(p.view_count, 0) * 3
            ) AS heat_score
        FROM community_post p
        WHERE p.status = 1
        ORDER BY heat_score DESC, p.created_at DESC
        LIMIT %s
        """,
        [max(limit, 0)],
    )
    if not rows:
        return None

    items = []
    for index, row in enumerate(rows, start=1):
        heat = int(row.get("heat_score") or 0)
        tags_json = row.get("tags_json")
        tag_str = ""
        if tags_json:
            try:
                tags = json.loads(tags_json) if isinstance(tags_json, str) else tags_json
                if isinstance(tags, list):
                    tag_str = ", ".join(str(t) for t in tags)
            except Exception:
                tag_str = ""
        items.append(
            {
                "id": int(row.get("id") or 0),
                "keyword": normalize_text(row.get("title")),
                "rank": index,
                "search_count": heat,
                "trend": "up" if index <= 3 else "stable" if index <= 6 else "down",
                "title": normalize_text(row.get("title")),
                "target_type": "post",
                "target_id": int(row.get("target_id") or 0),
                "tag": tag_str,
                "update_time": _format_datetime(row.get("update_time")),
                "create_time": _format_datetime(row.get("create_time")),
                "view_count": int(row.get("view_count") or 0),
            }
        )
    return items


def _db_post_like_relation_exists(user_id: int, post_id: int) -> bool:
    return (
        execute_one(
            """
            SELECT id FROM user_like
            WHERE user_id = %s AND target_type = 'post' AND target_id = %s
            LIMIT 1
            """,
            [user_id, post_id],
        )
        is not None
    )


def _db_post_favorite_relation_exists(user_id: int, post_id: int) -> bool:
    return (
        execute_one(
            """
            SELECT id FROM favorite
            WHERE user_id = %s AND target_type = 'post' AND target_id = %s
            LIMIT 1
            """,
            [user_id, post_id],
        )
        is not None
    )


def _db_comment_like_relation_exists(user_id: int, comment_id: int) -> bool:
    return (
        execute_one(
            """
            SELECT id FROM user_like
            WHERE user_id = %s AND target_type = 'post_comment' AND target_id = %s
            LIMIT 1
            """,
            [user_id, comment_id],
        )
        is not None
    )


def _db_block_relation_exists(user_id: int, blocked_user_id: int) -> bool:
    return (
        execute_one(
            """
            SELECT id FROM user_block
            WHERE user_id = %s AND blocked_user_id = %s
            LIMIT 1
            """,
            [user_id, blocked_user_id],
        )
        is not None
    )


def _increment_post_heat_score(post_id: int, delta: int) -> None:
    if delta == 0:
        return
    if delta > 0:
        execute_update(
            "UPDATE community_post SET heat_score = heat_score + %s, updated_at = NOW() WHERE id = %s",
            [delta, post_id],
        )
        return
    execute_update(
        """
        UPDATE community_post
        SET heat_score = GREATEST(heat_score + %s, 0),
            updated_at = NOW()
        WHERE id = %s
        """,
        [delta, post_id],
    )


def _update_post_counter(post_id: int, field: str, delta: int) -> None:
    if delta == 0:
        return
    sql = f"""
        UPDATE community_post
        SET {field} = GREATEST({field} + %s, 0),
            updated_at = NOW()
        WHERE id = %s
    """
    execute_update(sql, [delta, post_id])


def _update_comment_like_count(comment_id: int, delta: int) -> None:
    if delta == 0:
        return
    sql = """
        UPDATE post_comment
        SET like_count = GREATEST(like_count + %s, 0),
            updated_at = NOW()
        WHERE id = %s
    """
    execute_update(sql, [delta, comment_id])


def _mock_find_post(post_id: int) -> dict[str, Any] | None:
    for post in FALLBACK_POSTS:
        if int(post.get("id") or 0) == post_id and int(post.get("status") or 0) == 1:
            return post
    return None


def _mock_find_comment(comment_id: int) -> dict[str, Any] | None:
    for comment in FALLBACK_COMMENTS:
        if int(comment.get("id") or 0) == comment_id and int(comment.get("status") or 0) == 1:
            return comment
    return None


def _mock_get_posts(
    page: int = 1,
    page_size: int = 10,
    keyword: Optional[str] = None,
    current_user: Optional[Any] = None,
) -> dict[str, Any]:
    user_id = _current_user_id(current_user)
    items = [deepcopy(item) for item in FALLBACK_POSTS if int(item.get("status") or 0) == 1]
    news_title_map = _mock_news_title_map()
    if keyword and keyword.strip():
        lowered = keyword.strip().casefold()
        items = [
            item
            for item in items
            if lowered in normalize_text(item.get("title")).casefold()
            or lowered in normalize_text(item.get("content")).casefold()
        ]

    items.sort(
        key=lambda item: (
            int(item.get("heat_score") or 0),
            _format_datetime(item.get("create_time")),
            int(item.get("id") or 0),
        ),
        reverse=True,
    )
    for item in items:
        post_id = int(item["id"])
        author_id = int(item.get("user_id") or 0)
        item["author"] = normalize_text(item.get("author")) or _resolve_post_author(
            author_id,
            "",
            "",
            "",
        )
        item["author_id"] = author_id
        item["created_at"] = _format_datetime(item.get("create_time"))
        item["updated_at"] = _format_datetime(item.get("update_time"))
        item["likes"] = int(item.get("like_count") or 0)
        item["comments"] = int(item.get("comment_count") or 0)
        item["views"] = int(item.get("view_count") or item.get("heat_score") or 0)
        item["liked"] = _mock_is_post_liked(post_id, user_id)
        item["is_liked"] = item["liked"]
        item["is_favorited"] = _mock_is_post_favorited(post_id, user_id)
        item["is_blocked"] = _mock_is_post_blocked(author_id, user_id)
        item["hot"] = int(item.get("heat_score") or 0) > 100
        item["official"] = int(item.get("user_id") or 0) == 0
        related_news_id = item.get("related_news_id")
        item["related_news_title"] = normalize_text(
            item.get("related_news_title") or news_title_map.get(int(related_news_id or 0), "")
        )

    return paginate(items, page=page, page_size=page_size)


def _mock_get_post(post_id: int, current_user: Optional[Any] = None) -> dict[str, Any] | None:
    post = _mock_find_post(post_id)
    if post is None:
        return None
    item = deepcopy(post)
    news_title_map = _mock_news_title_map()
    author_id = int(item.get("user_id") or 0)
    user_id = _current_user_id(current_user)
    item["author"] = normalize_text(item.get("author"))
    item["author_id"] = author_id
    item["created_at"] = _format_datetime(item.get("create_time"))
    item["updated_at"] = _format_datetime(item.get("update_time"))
    item["likes"] = int(item.get("like_count") or 0)
    item["comments"] = int(item.get("comment_count") or 0)
    item["views"] = int(item.get("view_count") or item.get("heat_score") or 0)
    item["liked"] = _mock_is_post_liked(post_id, user_id)
    item["is_liked"] = item["liked"]
    item["is_favorited"] = _mock_is_post_favorited(post_id, user_id)
    item["is_blocked"] = _mock_is_post_blocked(author_id, user_id)
    related_news_id = item.get("related_news_id")
    item["related_news_title"] = normalize_text(
        item.get("related_news_title") or news_title_map.get(int(related_news_id or 0), "")
    )
    return item


def _mock_get_comments(post_id: int, current_user: Optional[Any] = None) -> list[dict[str, Any]]:
    user_id = _current_user_id(current_user)
    items = [deepcopy(item) for item in FALLBACK_COMMENTS if int(item.get("post_id") or 0) == post_id and int(item.get("status") or 0) == 1]
    items.sort(key=lambda item: (_format_datetime(item.get("create_time")), int(item.get("id") or 0)))
    liked_ids = {
        int(item["comment_id"])
        for item in FALLBACK_COMMENT_LIKES
        if user_id is not None and int(item["user_id"]) == user_id
    }
    comment_map = {int(item["id"]): item for item in items}
    result_items = []
    for item in items:
        comment_id = int(item["id"])
        author_id = int(item.get("user_id") or 0)
        parent_id = item.get("parent_id")
        reply_to_user_id = None
        reply_to_username = ""
        reply_to_nickname = ""
        if parent_id is not None:
            parent_comment = comment_map.get(int(parent_id))
            if parent_comment:
                reply_to_user_id = int(parent_comment.get("user_id") or 0)
                reply_to_username = normalize_text(parent_comment.get("username") or "")
                reply_to_nickname = normalize_text(parent_comment.get("nickname") or "")
                reply_to_content = normalize_text(parent_comment.get("content") or "")
        result_items.append(
            {
                "id": comment_id,
                "post_id": post_id,
                "user_id": author_id,
                "username": normalize_text(item.get("username")),
                "nickname": normalize_text(item.get("nickname")),
                "avatar": normalize_text(item.get("avatar")),
                "parent_id": parent_id,
                "content": normalize_text(item.get("content")),
                "like_count": int(item.get("like_count") or 0),
                "status": int(item.get("status") or 0),
                "create_time": _format_datetime(item.get("create_time")),
                "media_json": _normalize_media_json(item.get("media_json")),
                "reply_to_user_id": reply_to_user_id,
                "reply_to_username": reply_to_username,
                "reply_to_nickname": reply_to_nickname,
                "reply_to_content": reply_to_content,
                "author": normalize_text(item.get("author")),
                "author_id": author_id,
                "created_at": _format_datetime(item.get("create_time")),
                "likes": int(item.get("like_count") or 0),
                "is_liked": comment_id in liked_ids,
                "replies": [],
            }
        )
    return _build_comment_tree(result_items)


def _mock_hot_search(limit: int = 10) -> list[dict[str, Any]]:
    items = []
    for item in _mock_hot_topics()[: max(limit, 0)]:
        heat_score = int(item.get("heat_score") or 0)
        target_type = normalize_text(item.get("target_type"))
        target_id = int(item.get("target_id") or 0)

        view_count = heat_score
        like_count = 0
        comment_count = 0
        favorite_count = 0

        if target_type == "community_post":
            post = _mock_find_post(target_id)
            if post:
                like_count = int(post.get("like_count") or 0)
                comment_count = int(post.get("comment_count") or 0)
                favorite_count = int(post.get("favorite_count") or 0)
                view_count = int(post.get("view_count") or post.get("heat_score") or 0)

        search_count = like_count * 4 + favorite_count * 5 + comment_count * 6 + view_count * 3

        items.append(
            {
                "id": int(item["id"]),
                "keyword": normalize_text(item.get("title")),
                "rank": int(item.get("rank_no") or 0),
                "search_count": search_count,
                "trend": "up" if int(item.get("rank_no") or 0) <= 3 else "stable" if int(item.get("rank_no") or 0) <= 6 else "down",
                "title": normalize_text(item.get("title")),
                "target_type": target_type,
                "target_id": target_id,
                "tag": normalize_text(item.get("tag")),
                "update_time": update_time,
                "create_time": update_time,
                "view_count": view_count,
            }
        )
    return items


def _mock_blocked_ids(user_id: int) -> set[int]:
    return {
        int(item["blocked_user_id"])
        for item in FALLBACK_BLOCKS
        if int(item["user_id"]) == user_id
    }


def _post_create_row_from_request(request: CreatePostRequest, current_user: Optional[Any]) -> dict[str, Any]:
    user_id = _current_user_id(current_user)
    news_title_map = _mock_news_title_map()
    return {
        "id": 0,
        "user_id": user_id or 0,
        "username": normalize_text(getattr(current_user, "username", "") if current_user else ""),
        "nickname": _current_user_name(current_user),
        "avatar": normalize_text(getattr(current_user, "avatar", "") if current_user else ""),
        "title": request.title,
        "content": request.content,
        "related_news_id": request.related_news_id,
        "related_news_title": news_title_map.get(int(request.related_news_id or 0), ""),
        "topic_id": request.topic_id,
        "like_count": 0,
        "comment_count": 0,
        "favorite_count": 0,
        "heat_score": 0,
        "status": 1,
        "create_time": _now_text(),
        "update_time": _now_text(),
        "tags": request.tags or [],
        "images": request.images or [],
        "author": _current_user_name(current_user),
        "author_id": user_id or 0,
        "created_at": _now_text(),
        "updated_at": _now_text(),
        "likes": 0,
        "comments": 0,
        "views": 0,
        "liked": False,
        "is_liked": False,
        "is_favorited": False,
        "is_blocked": False,
    }


def _insert_post_db(request: CreatePostRequest, current_user: Optional[Any]) -> dict[str, Any]:
    user_id = _current_user_id(current_user)
    if user_id is None:
        raise AppException(code=401, message="未登录或登录状态已失效")

    validated_tags = _validate_tags(request.tags or [])
    images_json = json.dumps(request.images or [], ensure_ascii=False) if request.images else "[]"

    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            if _community_post_has_tags_column():
                has_images = _community_post_has_images_column()
                if has_images:
                    cursor.execute(
                        """
                        INSERT INTO community_post (
                            user_id, title, content, related_news_id, topic_id,
                            like_count, comment_count, favorite_count, heat_score,
                            status, created_at, updated_at, tags, images
                        ) VALUES (%s, %s, %s, %s, %s, 0, 0, 0, 0, 1, NOW(), NOW(), %s, %s)
                        """,
                        [
                            user_id,
                            request.title,
                            request.content,
                            request.related_news_id,
                            request.topic_id,
                            json.dumps(validated_tags, ensure_ascii=False),
                            images_json,
                        ],
                    )
                else:
                    cursor.execute(
                        """
                        INSERT INTO community_post (
                            user_id, title, content, related_news_id, topic_id,
                            like_count, comment_count, favorite_count, heat_score,
                            status, created_at, updated_at, tags
                        ) VALUES (%s, %s, %s, %s, %s, 0, 0, 0, 0, 1, NOW(), NOW(), %s)
                        """,
                        [
                            user_id,
                            request.title,
                            request.content,
                            request.related_news_id,
                            request.topic_id,
                            json.dumps(validated_tags, ensure_ascii=False),
                        ],
                    )
            else:
                cursor.execute(
                    """
                    INSERT INTO community_post (
                        user_id, title, content, related_news_id, topic_id,
                        like_count, comment_count, favorite_count, heat_score,
                        status, created_at, updated_at
                    ) VALUES (%s, %s, %s, %s, %s, 0, 0, 0, 0, 1, NOW(), NOW())
                    """,
                    [
                        user_id,
                        request.title,
                        request.content,
                        request.related_news_id,
                        request.topic_id,
                    ],
                )
            cursor.execute(
                "SELECT id FROM community_post WHERE user_id = %s ORDER BY id DESC LIMIT 1",
                [user_id],
            )
            row = cursor.fetchone()
            post_id = int(row["id"]) if row else 0
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

    post = _db_get_post(post_id, current_user=current_user)
    if post is None:
        return _post_create_row_from_request(request, current_user)
    return post


def create_post(request: CreatePostRequest, current_user: Optional[Any] = None) -> CommunityPost:
    if current_user is None:
        raise AppException(code=401, message="未登录或登录状态已失效")

    try:
        if _db_has_posts() or not _db_has_posts():
            # 数据库可用时优先写入数据库；如果后续库异常会在外层兜底到 mock。
            result = _insert_post_db(request, current_user)
            return CommunityPost(**result)
    except Exception as exc:  # noqa: BLE001
        logger.warning("创建社区帖子失败，回退 mock：%s", exc)

    new_id = max([item["id"] for item in FALLBACK_POSTS], default=0) + 1
    post = _post_create_row_from_request(request, current_user)
    post["id"] = new_id
    FALLBACK_POSTS.append(
        {
            "id": new_id,
            "user_id": post["user_id"],
            "author": post["author"],
            "title": post["title"],
            "content": post["content"],
            "related_news_id": post["related_news_id"],
            "topic_id": post["topic_id"],
            "like_count": 0,
            "comment_count": 0,
            "favorite_count": 0,
            "heat_score": 0,
            "status": 1,
            "create_time": post["create_time"],
            "update_time": post["update_time"],
            "tags": request.tags or [],
            "images": request.images or [],
        }
    )
    return CommunityPost(**post)


def get_post_list(
    page: int = 1,
    page_size: int = 10,
    keyword: Optional[str] = None,
    tag: Optional[str] = None,
    sort: str = "hot",
    current_user: Optional[Any] = None,
) -> PostListResponse:
    try:
        result = _db_get_posts(page=page, page_size=page_size, keyword=keyword, tag=tag, sort=sort, current_user=current_user)
        if result is not None:
            return PostListResponse(**result)
    except Exception as exc:  # noqa: BLE001
        logger.warning("读取社区帖子失败，回退 mock：%s", exc)
    return PostListResponse(**_mock_get_posts(page=page, page_size=page_size, keyword=keyword, current_user=current_user))


def get_post_detail(post_id: int, current_user: Optional[Any] = None) -> Optional[CommunityPost]:
    try:
        if _db_has_posts():
            post = _db_get_post(post_id, current_user=current_user)
            if post is not None:
                execute_update(
                    "UPDATE community_post SET view_count = view_count + 1, updated_at = NOW() WHERE id = %s",
                    [post_id],
                )
                post["view_count"] = int(post.get("view_count") or 0) + 1
                post["views"] = post["view_count"]

                current_user_id = _get_current_user_id(current_user)
                if current_user_id is not None:
                    try:
                        existing = execute_one(
                            """
                            SELECT id FROM browse_history
                            WHERE user_id = %s
                              AND target_type = 'post'
                              AND target_id = %s
                            LIMIT 1
                            """,
                            [current_user_id, post_id],
                        )
                        if existing:
                            execute_update(
                                """
                                UPDATE browse_history
                                SET browse_time = NOW()
                                WHERE id = %s
                                """,
                                [int(existing["id"])],
                            )
                        else:
                            execute_update(
                                """
                                INSERT INTO browse_history (user_id, news_id, target_type, target_id, browse_time, created_at)
                                VALUES (%s, %s, 'post', %s, NOW(), NOW())
                                """,
                                [current_user_id, 0, post_id],
                            )
                    except Exception as exc:  # noqa: BLE001
                        logger.warning("写入帖子浏览历史失败，已忽略：%s", exc)

                return CommunityPost(**post)
            return None
    except Exception as exc:  # noqa: BLE001
        logger.warning("读取社区帖子详情失败，回退 mock：%s", exc)

    post = _mock_get_post(post_id, current_user=current_user)
    if post is None:
        return None
    for item in FALLBACK_POSTS:
        if int(item.get("id") or 0) == post_id:
            item["heat_score"] = int(item.get("heat_score") or 0) + 1
            item["updated_at"] = _now_text()
            break
    return CommunityPost(**post)


def _sync_post_counter_in_fallback(post_id: int, field: str, delta: int) -> None:
    for item in FALLBACK_POSTS:
        if int(item.get("id") or 0) == post_id:
            item[field] = max(0, int(item.get(field) or 0) + delta)
            item["heat_score"] = max(0, int(item.get("heat_score") or 0) + delta)
            item["update_time"] = _now_text()
            item["updated_at"] = item["update_time"]
            break


def _sync_comment_counter_in_fallback(post_id: int, delta: int) -> None:
    for item in FALLBACK_POSTS:
        if int(item.get("id") or 0) == post_id:
            item["comment_count"] = max(0, int(item.get("comment_count") or 0) + delta)
            item["heat_score"] = max(0, int(item.get("heat_score") or 0) + delta)
            item["update_time"] = _now_text()
            item["updated_at"] = item["update_time"]
            break


def _sync_post_like_state_fallback(post_id: int, user_id: int, liked: bool) -> None:
    global FALLBACK_POST_LIKES
    if liked:
        if not any(item["user_id"] == user_id and item["post_id"] == post_id for item in FALLBACK_POST_LIKES):
            FALLBACK_POST_LIKES.append({"user_id": user_id, "post_id": post_id})
            _sync_post_counter_in_fallback(post_id, "like_count", 1)
    else:
        before = len(FALLBACK_POST_LIKES)
        FALLBACK_POST_LIKES = [item for item in FALLBACK_POST_LIKES if not (item["user_id"] == user_id and item["post_id"] == post_id)]
        if len(FALLBACK_POST_LIKES) != before:
            _sync_post_counter_in_fallback(post_id, "like_count", -1)


def _sync_post_favorite_state_fallback(post_id: int, user_id: int, favorited: bool) -> None:
    global FALLBACK_POST_FAVORITES
    if favorited:
        if not any(item["user_id"] == user_id and item["post_id"] == post_id for item in FALLBACK_POST_FAVORITES):
            FALLBACK_POST_FAVORITES.append({"user_id": user_id, "post_id": post_id})
            _sync_post_counter_in_fallback(post_id, "favorite_count", 1)
    else:
        before = len(FALLBACK_POST_FAVORITES)
        FALLBACK_POST_FAVORITES = [item for item in FALLBACK_POST_FAVORITES if not (item["user_id"] == user_id and item["post_id"] == post_id)]
        if len(FALLBACK_POST_FAVORITES) != before:
            _sync_post_counter_in_fallback(post_id, "favorite_count", -1)


def _next_comment_id_fallback() -> int:
    return max([int(item["id"]) for item in FALLBACK_COMMENTS], default=0) + 1


def _append_comment_fallback(comment: dict[str, Any]) -> dict[str, Any]:
    FALLBACK_COMMENTS.append(comment)
    _sync_comment_counter_in_fallback(int(comment["post_id"]), 1)
    return comment


def _db_comment_post_id(comment_id: int) -> Optional[int]:
    row = execute_one(
        """
        SELECT post_id
        FROM post_comment
        WHERE id = %s AND status <> 4
        LIMIT 1
        """,
        [comment_id],
    )
    if row is None:
        return None
    return int(row["post_id"])


def _db_delete_comment(comment_id: int, current_user: Optional[Any]) -> dict[str, Any] | None:
    user_id = _current_user_id(current_user)
    if user_id is None:
        raise AppException(code=401, message="未登录或登录状态已失效")

    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, post_id, user_id
                FROM post_comment
                WHERE id = %s AND status <> 4
                LIMIT 1
                """,
                [comment_id],
            )
            comment = cursor.fetchone()
            if comment is None:
                return None

            if not _can_delete_comment(current_user, int(comment["user_id"] or 0)):
                raise AppException(code=403, message="当前账号无权限访问该资源")

            cursor.execute(
                """
                UPDATE post_comment
                SET status = 4, updated_at = NOW()
                WHERE id = %s
                """,
                [comment_id],
            )
            cursor.execute(
                """
                UPDATE community_post
                SET comment_count = GREATEST(comment_count - 1, 0),
                    heat_score = GREATEST(heat_score - 1, 0),
                    updated_at = NOW()
                WHERE id = %s
                """,
                [int(comment["post_id"] or 0)],
            )
            cursor.execute(
                "SELECT comment_count FROM community_post WHERE id = %s LIMIT 1",
                [int(comment["post_id"] or 0)],
            )
            updated = cursor.fetchone()
        connection.commit()
        return {
            "comment_id": comment_id,
            "deleted": True,
            "post_id": int(comment["post_id"] or 0),
            "comment_count": int(updated["comment_count"]) if updated else 0,
        }
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def _db_create_comment(post_id: int, request: CreateCommentRequest, current_user: Optional[Any]) -> CommentItem:
    user_id = _current_user_id(current_user)
    if user_id is None:
        raise AppException(code=401, message="未登录或登录状态已失效")

    if execute_one("SELECT id FROM community_post WHERE id = %s AND status = 1 LIMIT 1", [post_id]) is None:
        raise AppException(code=404, message="帖子不存在")

    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            params: list[Any] = [post_id, user_id, request.content]
            media_json_value = _serialize_media_json(getattr(request, "media_json", None))
            if _db_post_comment_has_media_json():
                cursor.execute(
                    """
                    INSERT INTO post_comment (post_id, user_id, parent_id, content, media_json, like_count, status, created_at, updated_at)
                    VALUES (%s, %s, NULL, %s, %s, 0, 1, NOW(), NOW())
                    """,
                    [post_id, user_id, request.content, media_json_value],
                )
            else:
                cursor.execute(
                    """
                    INSERT INTO post_comment (post_id, user_id, parent_id, content, like_count, status, created_at, updated_at)
                    VALUES (%s, %s, NULL, %s, 0, 1, NOW(), NOW())
                    """,
                    params,
                )
            cursor.execute(
                "UPDATE community_post SET comment_count = comment_count + 1, heat_score = heat_score + 1, updated_at = NOW() WHERE id = %s",
                [post_id],
            )
            cursor.execute(
                "SELECT id FROM post_comment WHERE post_id = %s AND user_id = %s ORDER BY id DESC LIMIT 1",
                [post_id, user_id],
            )
            row = cursor.fetchone()
            comment_id = int(row["id"]) if row else 0
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

    media_json_column = "pc.media_json" if _db_post_comment_has_media_json() else "NULL AS media_json"
    row = execute_one(
        f"""
        SELECT
            pc.id,
            pc.post_id,
            pc.user_id,
            u.username,
            u.nickname,
            u.avatar,
            pc.parent_id,
            pc.content,
            pc.like_count,
            pc.status,
            pc.created_at AS create_time,
            {media_json_column}
        FROM post_comment pc
        LEFT JOIN `user` u ON u.id = pc.user_id
        WHERE pc.id = %s
        LIMIT 1
        """,
        [comment_id],
    )
    if row is None:
        return CommentItem(
            id=comment_id,
            post_id=post_id,
            user_id=user_id,
            username="",
            nickname=_current_user_name(current_user),
            avatar="",
            parent_id=None,
            content=request.content,
            like_count=0,
            status=1,
            create_time=_now_text(),
            media_json=_normalize_media_json(getattr(request, "media_json", None)),
            author=_current_user_name(current_user),
            author_id=user_id,
            created_at=_now_text(),
            likes=0,
            is_liked=False,
            replies=[],
        )

    payload = _comment_row_to_item(
        {
            **row,
            "author": _current_user_name(current_user),
            "author_id": user_id,
        }
    )
    return CommentItem(**payload)


def _db_reply_comment(comment_id: int, request: CreateCommentRequest, current_user: Optional[Any]) -> CommentItem:
    user_id = _current_user_id(current_user)
    if user_id is None:
        raise AppException(code=401, message="未登录或登录状态已失效")

    parent = execute_one(
        """
        SELECT id, post_id
        FROM post_comment
        WHERE id = %s AND status <> 4
        LIMIT 1
        """,
        [comment_id],
    )
    if parent is None:
        raise AppException(code=404, message="评论不存在")

    post_id = int(parent["post_id"])
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            params: list[Any] = [post_id, user_id, comment_id, request.content]
            media_json_value = _serialize_media_json(getattr(request, "media_json", None))
            if _db_post_comment_has_media_json():
                cursor.execute(
                    """
                    INSERT INTO post_comment (post_id, user_id, parent_id, content, media_json, like_count, status, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, 0, 1, NOW(), NOW())
                    """,
                    [post_id, user_id, comment_id, request.content, media_json_value],
                )
            else:
                cursor.execute(
                    """
                    INSERT INTO post_comment (post_id, user_id, parent_id, content, like_count, status, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, 0, 1, NOW(), NOW())
                    """,
                    params,
                )
            cursor.execute(
                "UPDATE community_post SET comment_count = comment_count + 1, heat_score = heat_score + 1, updated_at = NOW() WHERE id = %s",
                [post_id],
            )
            cursor.execute(
                "SELECT id FROM post_comment WHERE post_id = %s AND user_id = %s ORDER BY id DESC LIMIT 1",
                [post_id, user_id],
            )
            row = cursor.fetchone()
            new_comment_id = int(row["id"]) if row else 0
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

    media_json_column = "pc.media_json" if _db_post_comment_has_media_json() else "NULL AS media_json"
    row = execute_one(
        f"""
        SELECT
            pc.id,
            pc.post_id,
            pc.user_id,
            u.username,
            u.nickname,
            u.avatar,
            pc.parent_id,
            pc.content,
            pc.like_count,
            pc.status,
            pc.created_at AS create_time,
            {media_json_column},
            COALESCE(ru.id, NULL) AS reply_to_user_id,
            COALESCE(ru.username, '') AS reply_to_username,
            COALESCE(ru.nickname, '') AS reply_to_nickname,
            COALESCE(parent_pc.content, '') AS reply_to_content
        FROM post_comment pc
        LEFT JOIN `user` u ON u.id = pc.user_id
        LEFT JOIN post_comment parent_pc ON parent_pc.id = pc.parent_id
        LEFT JOIN `user` ru ON ru.id = parent_pc.user_id
        WHERE pc.id = %s
        LIMIT 1
        """,
        [new_comment_id],
    )
    if row is None:
        parent_comment = execute_one(
            """
            SELECT pc.content, u.id AS user_id, u.username, u.nickname
            FROM post_comment pc
            LEFT JOIN `user` u ON u.id = pc.user_id
            WHERE pc.id = %s
            LIMIT 1
            """,
            [comment_id],
        )
        return CommentItem(
            id=new_comment_id,
            post_id=post_id,
            user_id=user_id,
            username="",
            nickname=_current_user_name(current_user),
            avatar="",
            parent_id=comment_id,
            content=request.content,
            like_count=0,
            status=1,
            create_time=_now_text(),
            media_json=_normalize_media_json(getattr(request, "media_json", None)),
            reply_to_user_id=parent_comment.get("user_id") if parent_comment else None,
            reply_to_username=normalize_text(parent_comment.get("username")) if parent_comment else "",
            reply_to_nickname=normalize_text(parent_comment.get("nickname")) if parent_comment else "",
            reply_to_content=normalize_text(parent_comment.get("content")) if parent_comment else "",
            author=_current_user_name(current_user),
            author_id=user_id,
            created_at=_now_text(),
            likes=0,
            is_liked=False,
            replies=[],
        )

    payload = _comment_row_to_item(
        {
            **row,
            "author": _current_user_name(current_user),
            "author_id": user_id,
        }
    )
    return CommentItem(**payload)


def _db_toggle_post_like(post_id: int, current_user: Optional[Any]) -> LikeResponse:
    user_id = _current_user_id(current_user)
    if user_id is None:
        raise AppException(code=401, message="未登录或登录状态已失效")

    post = execute_one(
        "SELECT id, like_count FROM community_post WHERE id = %s AND status = 1 LIMIT 1",
        [post_id],
    )
    if post is None:
        raise AppException(code=404, message="帖子不存在")

    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            existed = cursor.execute(
                """
                SELECT id
                FROM user_like
                WHERE user_id = %s AND target_type = 'post' AND target_id = %s
                LIMIT 1
                """,
                [user_id, post_id],
            )
            if existed:
                cursor.execute(
                    """
                    DELETE FROM user_like
                    WHERE user_id = %s AND target_type = 'post' AND target_id = %s
                    """,
                    [user_id, post_id],
                )
                cursor.execute(
                    "UPDATE community_post SET like_count = GREATEST(like_count - 1, 0), heat_score = GREATEST(heat_score - 1, 0), updated_at = NOW() WHERE id = %s",
                    [post_id],
                )
                connection.commit()
                like_count = max(0, int(post.get("like_count") or 0) - 1)
                return LikeResponse(success=True, liked=False, count=like_count)

            cursor.execute(
                """
                INSERT INTO user_like (user_id, target_id, target_type, created_at)
                VALUES (%s, %s, 'post', NOW())
                """,
                [user_id, post_id],
            )
            cursor.execute(
                "UPDATE community_post SET like_count = like_count + 1, heat_score = heat_score + 1, updated_at = NOW() WHERE id = %s",
                [post_id],
            )
            connection.commit()
            like_count = int(post.get("like_count") or 0) + 1
            return LikeResponse(success=True, liked=True, count=like_count)
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def _db_unlike_post(post_id: int, current_user: Optional[Any]) -> LikeResponse:
    user_id = _current_user_id(current_user)
    if user_id is None:
        raise AppException(code=401, message="未登录或登录状态已失效")

    post = execute_one(
        "SELECT id, like_count FROM community_post WHERE id = %s AND status = 1 LIMIT 1",
        [post_id],
    )
    if post is None:
        raise AppException(code=404, message="帖子不存在")

    existed = _db_post_like_relation_exists(user_id, post_id)
    if not existed:
        return LikeResponse(success=True, liked=False, count=int(post.get("like_count") or 0))

    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                DELETE FROM user_like
                WHERE user_id = %s AND target_type = 'post' AND target_id = %s
                """,
                [user_id, post_id],
            )
            cursor.execute(
                "UPDATE community_post SET like_count = GREATEST(like_count - 1, 0), heat_score = GREATEST(heat_score - 1, 0), updated_at = NOW() WHERE id = %s",
                [post_id],
            )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
    count = max(0, int(post.get("like_count") or 0) - 1)
    return LikeResponse(success=True, liked=False, count=count)


def _db_toggle_post_favorite(post_id: int, current_user: Optional[Any]) -> FavoriteResponse:
    user_id = _current_user_id(current_user)
    if user_id is None:
        raise AppException(code=401, message="未登录或登录状态已失效")

    post = execute_one(
        "SELECT id, favorite_count FROM community_post WHERE id = %s AND status = 1 LIMIT 1",
        [post_id],
    )
    if post is None:
        raise AppException(code=404, message="帖子不存在")

    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            existed = cursor.execute(
                """
                SELECT id
                FROM favorite
                WHERE user_id = %s AND target_type = 'post' AND target_id = %s
                LIMIT 1
                """,
                [user_id, post_id],
            )
            if existed:
                cursor.execute(
                    """
                    DELETE FROM favorite
                    WHERE user_id = %s AND target_type = 'post' AND target_id = %s
                    """,
                    [user_id, post_id],
                )
                cursor.execute(
                    "UPDATE community_post SET favorite_count = GREATEST(favorite_count - 1, 0), updated_at = NOW() WHERE id = %s",
                    [post_id],
                )
                connection.commit()
                count = max(0, int(post.get("favorite_count") or 0) - 1)
                return FavoriteResponse(success=True, is_favorited=False, favorite_count=count)

            cursor.execute(
                """
                INSERT INTO favorite (user_id, target_id, target_type, created_at)
                VALUES (%s, %s, 'post', NOW())
                """,
                [user_id, post_id],
            )
            cursor.execute(
                "UPDATE community_post SET favorite_count = favorite_count + 1, updated_at = NOW() WHERE id = %s",
                [post_id],
            )
            connection.commit()
            count = int(post.get("favorite_count") or 0) + 1
            return FavoriteResponse(success=True, is_favorited=True, favorite_count=count)
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def _db_unfavorite_post(post_id: int, current_user: Optional[Any]) -> FavoriteResponse:
    user_id = _current_user_id(current_user)
    if user_id is None:
        raise AppException(code=401, message="未登录或登录状态已失效")

    post = execute_one(
        "SELECT id, favorite_count FROM community_post WHERE id = %s AND status = 1 LIMIT 1",
        [post_id],
    )
    if post is None:
        raise AppException(code=404, message="帖子不存在")

    existed = _db_post_favorite_relation_exists(user_id, post_id)
    if not existed:
        return FavoriteResponse(success=True, is_favorited=False, favorite_count=int(post.get("favorite_count") or 0))

    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                DELETE FROM favorite
                WHERE user_id = %s AND target_type = 'post' AND target_id = %s
                """,
                [user_id, post_id],
            )
            cursor.execute(
                "UPDATE community_post SET favorite_count = GREATEST(favorite_count - 1, 0), updated_at = NOW() WHERE id = %s",
                [post_id],
            )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
    count = max(0, int(post.get("favorite_count") or 0) - 1)
    return FavoriteResponse(success=True, is_favorited=False, favorite_count=count)


def _db_toggle_comment_like(comment_id: int, current_user: Optional[Any]) -> CommentLikeResult:
    from app.modules.community.schema import CommentLikeResult

    user_id = _current_user_id(current_user)
    if user_id is None:
        raise AppException(code=401, message="未登录或登录状态已失效")

    comment = execute_one(
        "SELECT id, like_count FROM post_comment WHERE id = %s AND status <> 4 LIMIT 1",
        [comment_id],
    )
    if comment is None:
        raise AppException(code=404, message="评论不存在")

    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            existed = cursor.execute(
                """
                SELECT id
                FROM user_like
                WHERE user_id = %s AND target_type = 'post_comment' AND target_id = %s
                LIMIT 1
                """,
                [user_id, comment_id],
            )
            if existed:
                cursor.execute(
                    """
                    DELETE FROM user_like
                    WHERE user_id = %s AND target_type = 'post_comment' AND target_id = %s
                    """,
                    [user_id, comment_id],
                )
                cursor.execute(
                    "UPDATE post_comment SET like_count = GREATEST(like_count - 1, 0), updated_at = NOW() WHERE id = %s",
                    [comment_id],
                )
                connection.commit()
                count = max(0, int(comment.get("like_count") or 0) - 1)
                return CommentLikeResult(comment_id=comment_id, liked=False, like_count=count)

            cursor.execute(
                """
                INSERT INTO user_like (user_id, target_id, target_type, created_at)
                VALUES (%s, %s, 'post_comment', NOW())
                """,
                [user_id, comment_id],
            )
            cursor.execute(
                "UPDATE post_comment SET like_count = like_count + 1, updated_at = NOW() WHERE id = %s",
                [comment_id],
            )
            connection.commit()
            count = int(comment.get("like_count") or 0) + 1
            return CommentLikeResult(comment_id=comment_id, liked=True, like_count=count)
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def _db_block_user(blocked_user_id: int, current_user: Optional[Any]) -> BlockResponse:
    user_id = _current_user_id(current_user)
    if user_id is None:
        raise AppException(code=401, message="未登录或登录状态已失效")

    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            existed = cursor.execute(
                """
                SELECT id
                FROM user_block
                WHERE user_id = %s AND blocked_user_id = %s
                LIMIT 1
                """,
                [user_id, blocked_user_id],
            )
            if existed:
                return BlockResponse(success=True, blocked=True, user_id=blocked_user_id)

            cursor.execute(
                """
                INSERT INTO user_block (user_id, blocked_user_id, created_at)
                VALUES (%s, %s, NOW())
                """,
                [user_id, blocked_user_id],
            )
            connection.commit()
            return BlockResponse(success=True, blocked=True, user_id=blocked_user_id)
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def _db_unblock_user(blocked_user_id: int, current_user: Optional[Any]) -> BlockResponse:
    user_id = _current_user_id(current_user)
    if user_id is None:
        raise AppException(code=401, message="未登录或登录状态已失效")

    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                DELETE FROM user_block
                WHERE user_id = %s AND blocked_user_id = %s
                """,
                [user_id, blocked_user_id],
            )
        connection.commit()
        return BlockResponse(success=True, blocked=False, user_id=blocked_user_id)
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def _mock_create_post(request: CreatePostRequest, current_user: Optional[Any]) -> CommunityPost:
    if current_user is None:
        raise AppException(code=401, message="未登录或登录状态已失效")
    new_id = max([int(item["id"]) for item in FALLBACK_POSTS], default=0) + 1
    now = _now_text()
    news_title_map = _mock_news_title_map()
    validated_tags = _validate_tags(request.tags or [])
    post = {
        "id": new_id,
        "user_id": _current_user_id(current_user) or 0,
        "username": normalize_text(getattr(current_user, "username", "") if current_user else ""),
        "nickname": _current_user_name(current_user),
        "avatar": normalize_text(getattr(current_user, "avatar", "") if current_user else ""),
        "title": request.title,
        "content": request.content,
        "related_news_id": request.related_news_id,
        "related_news_title": news_title_map.get(int(request.related_news_id or 0), ""),
        "topic_id": request.topic_id,
        "like_count": 0,
        "comment_count": 0,
        "favorite_count": 0,
        "heat_score": 0,
        "status": 1,
        "create_time": now,
        "update_time": now,
        "tags": validated_tags,
        "images": request.images or [],
        "author": _current_user_name(current_user),
        "author_id": _current_user_id(current_user) or 0,
        "created_at": now,
        "updated_at": now,
        "likes": 0,
        "comments": 0,
        "views": 0,
        "liked": False,
        "is_liked": False,
        "is_favorited": False,
        "is_blocked": False,
    }
    FALLBACK_POSTS.append(deepcopy(post))
    return CommunityPost(**post)


def _mock_create_comment(post_id: int, request: CreateCommentRequest, current_user: Optional[Any]) -> CommentItem:
    if current_user is None:
        raise AppException(code=401, message="未登录或登录状态已失效")
    if _mock_find_post(post_id) is None:
        raise AppException(code=404, message="帖子不存在")

    new_id = _next_comment_id_fallback()
    now = _now_text()
    comment = {
        "id": new_id,
        "post_id": post_id,
        "user_id": _current_user_id(current_user) or 0,
        "username": normalize_text(getattr(current_user, "username", "") if current_user else ""),
        "nickname": _current_user_name(current_user),
        "avatar": normalize_text(getattr(current_user, "avatar", "") if current_user else ""),
        "parent_id": None,
        "content": request.content,
        "like_count": 0,
        "status": 1,
        "create_time": now,
        "media_json": _normalize_media_json(getattr(request, "media_json", None)),
        "author": _current_user_name(current_user),
        "author_id": _current_user_id(current_user) or 0,
        "created_at": now,
        "likes": 0,
        "is_liked": False,
        "replies": [],
    }
    _append_comment_fallback(comment)
    return CommentItem(**comment)


def _mock_reply_comment(comment_id: int, request: CreateCommentRequest, current_user: Optional[Any]) -> CommentItem:
    if current_user is None:
        raise AppException(code=401, message="未登录或登录状态已失效")
    parent = _mock_find_comment(comment_id)
    if parent is None:
        raise AppException(code=404, message="评论不存在")

    new_id = _next_comment_id_fallback()
    post_id = int(parent.get("post_id") or 0)
    now = _now_text()
    comment = {
        "id": new_id,
        "post_id": post_id,
        "user_id": _current_user_id(current_user) or 0,
        "username": normalize_text(getattr(current_user, "username", "") if current_user else ""),
        "nickname": _current_user_name(current_user),
        "avatar": normalize_text(getattr(current_user, "avatar", "") if current_user else ""),
        "parent_id": comment_id,
        "content": request.content,
        "like_count": 0,
        "status": 1,
        "create_time": now,
        "media_json": _normalize_media_json(getattr(request, "media_json", None)),
        "author": _current_user_name(current_user),
        "author_id": _current_user_id(current_user) or 0,
        "created_at": now,
        "likes": 0,
        "is_liked": False,
        "replies": [],
    }
    _append_comment_fallback(comment)
    return CommentItem(**comment)


def _mock_toggle_post_like(post_id: int, current_user: Optional[Any]) -> LikeResponse:
    user_id = _current_user_id(current_user)
    if user_id is None:
        raise AppException(code=401, message="未登录或登录状态已失效")
    post = _mock_find_post(post_id)
    if post is None:
        raise AppException(code=404, message="帖子不存在")

    existed = any(item["user_id"] == user_id and item["post_id"] == post_id for item in FALLBACK_POST_LIKES)
    if existed:
        _sync_post_like_state_fallback(post_id, user_id, False)
        return LikeResponse(success=True, liked=False, count=max(0, int(post.get("like_count") or 0) - 1))
    _sync_post_like_state_fallback(post_id, user_id, True)
    return LikeResponse(success=True, liked=True, count=int(post.get("like_count") or 0) + 1)


def _mock_unlike_post(post_id: int, current_user: Optional[Any]) -> LikeResponse:
    user_id = _current_user_id(current_user)
    if user_id is None:
        raise AppException(code=401, message="未登录或登录状态已失效")
    post = _mock_find_post(post_id)
    if post is None:
        raise AppException(code=404, message="帖子不存在")
    existed = any(item["user_id"] == user_id and item["post_id"] == post_id for item in FALLBACK_POST_LIKES)
    if not existed:
        return LikeResponse(success=True, liked=False, count=int(post.get("like_count") or 0))
    _sync_post_like_state_fallback(post_id, user_id, False)
    return LikeResponse(success=True, liked=False, count=max(0, int(post.get("like_count") or 0) - 1))


def _mock_toggle_post_favorite(post_id: int, current_user: Optional[Any]) -> FavoriteResponse:
    user_id = _current_user_id(current_user)
    if user_id is None:
        raise AppException(code=401, message="未登录或登录状态已失效")
    post = _mock_find_post(post_id)
    if post is None:
        raise AppException(code=404, message="帖子不存在")

    existed = any(item["user_id"] == user_id and item["post_id"] == post_id for item in FALLBACK_POST_FAVORITES)
    if existed:
        _sync_post_favorite_state_fallback(post_id, user_id, False)
        return FavoriteResponse(success=True, is_favorited=False, favorite_count=max(0, int(post.get("favorite_count") or 0) - 1))
    _sync_post_favorite_state_fallback(post_id, user_id, True)
    return FavoriteResponse(success=True, is_favorited=True, favorite_count=int(post.get("favorite_count") or 0) + 1)


def _mock_unfavorite_post(post_id: int, current_user: Optional[Any]) -> FavoriteResponse:
    user_id = _current_user_id(current_user)
    if user_id is None:
        raise AppException(code=401, message="未登录或登录状态已失效")
    post = _mock_find_post(post_id)
    if post is None:
        raise AppException(code=404, message="帖子不存在")
    existed = any(item["user_id"] == user_id and item["post_id"] == post_id for item in FALLBACK_POST_FAVORITES)
    if not existed:
        return FavoriteResponse(success=True, is_favorited=False, favorite_count=int(post.get("favorite_count") or 0))
    _sync_post_favorite_state_fallback(post_id, user_id, False)
    return FavoriteResponse(success=True, is_favorited=False, favorite_count=max(0, int(post.get("favorite_count") or 0) - 1))


def _mock_toggle_comment_like(comment_id: int, current_user: Optional[Any]) -> CommentLikeResult:
    from app.modules.community.schema import CommentLikeResult

    global FALLBACK_COMMENT_LIKES
    user_id = _current_user_id(current_user)
    if user_id is None:
        raise AppException(code=401, message="未登录或登录状态已失效")
    comment = _mock_find_comment(comment_id)
    if comment is None:
        raise AppException(code=404, message="评论不存在")

    existed = any(item["user_id"] == user_id and item["comment_id"] == comment_id for item in FALLBACK_COMMENT_LIKES)
    if existed:
        FALLBACK_COMMENT_LIKES = [item for item in FALLBACK_COMMENT_LIKES if not (item["user_id"] == user_id and item["comment_id"] == comment_id)]
        comment["like_count"] = max(0, int(comment.get("like_count") or 0) - 1)
        return CommentLikeResult(comment_id=comment_id, liked=False, like_count=int(comment.get("like_count") or 0))

    FALLBACK_COMMENT_LIKES.append({"user_id": user_id, "comment_id": comment_id})
    comment["like_count"] = int(comment.get("like_count") or 0) + 1
    return CommentLikeResult(comment_id=comment_id, liked=True, like_count=int(comment.get("like_count") or 0))


def _mock_delete_comment(comment_id: int, current_user: Optional[Any]) -> dict[str, Any]:
    user_id = _current_user_id(current_user)
    if user_id is None:
        raise AppException(code=401, message="鏈櫥褰曟垨鐧诲綍鐘舵€佸凡澶辨晥")
    comment = None
    for item in FALLBACK_COMMENTS:
        if int(item.get("id") or 0) == comment_id and int(item.get("status") or 0) != 4:
            comment = item
            break
    if comment is None:
        raise AppException(code=404, message="璇勮涓嶅瓨鍦?")

    if not _can_delete_comment(current_user, int(comment.get("user_id") or 0)):
        raise AppException(code=403, message="当前账号无权限访问该资源")

    comment["status"] = 4
    post_id = int(comment.get("post_id") or 0)
    new_count = 0
    for post in FALLBACK_POSTS:
        if int(post.get("id") or 0) == post_id:
            post["comment_count"] = max(0, int(post.get("comment_count") or 0) - 1)
            post["heat_score"] = max(0, int(post.get("heat_score") or 0) - 1)
            post["update_time"] = _now_text()
            post["updated_at"] = post["update_time"]
            new_count = int(post.get("comment_count") or 0)
            break
    return {
        "comment_id": comment_id,
        "deleted": True,
        "post_id": post_id,
        "comment_count": new_count,
    }


def _mock_block_user(blocked_user_id: int, current_user: Optional[Any]) -> BlockResponse:
    user_id = _current_user_id(current_user)
    if user_id is None:
        raise AppException(code=401, message="未登录或登录状态已失效")
    if any(item["user_id"] == user_id and item["blocked_user_id"] == blocked_user_id for item in FALLBACK_BLOCKS):
        return BlockResponse(success=True, blocked=True, user_id=blocked_user_id)
    FALLBACK_BLOCKS.append({"user_id": user_id, "blocked_user_id": blocked_user_id})
    return BlockResponse(success=True, blocked=True, user_id=blocked_user_id)


def _mock_unblock_user(blocked_user_id: int, current_user: Optional[Any]) -> BlockResponse:
    user_id = _current_user_id(current_user)
    if user_id is None:
        raise AppException(code=401, message="未登录或登录状态已失效")
    global FALLBACK_BLOCKS
    FALLBACK_BLOCKS = [
        item for item in FALLBACK_BLOCKS if not (item["user_id"] == user_id and item["blocked_user_id"] == blocked_user_id)
    ]
    return BlockResponse(success=True, blocked=False, user_id=blocked_user_id)


def _mock_get_post_comments(post_id: int, current_user: Optional[Any] = None) -> dict[str, Any]:
    post = _mock_find_post(post_id)
    if post is None:
        raise AppException(code=404, message="帖子不存在")

    current_user_id = _current_user_id(current_user)
    comment_items = _mock_comments_for_post(post_id)
    liked_ids = {
        int(item["comment_id"])
        for item in FALLBACK_COMMENT_LIKES
        if current_user_id is not None and int(item["user_id"]) == current_user_id
    }
    formatted: list[dict[str, Any]] = []
    for item in comment_items:
        comment_id = int(item["id"])
        author_id = int(item.get("user_id") or 0)
        formatted.append(
            {
                "id": comment_id,
                "post_id": post_id,
                "user_id": author_id,
                "username": normalize_text(item.get("username")),
                "nickname": normalize_text(item.get("nickname")),
                "avatar": normalize_text(item.get("avatar")),
                "parent_id": item.get("parent_id"),
                "content": normalize_text(item.get("content")),
                "like_count": int(item.get("like_count") or 0),
                "status": int(item.get("status") or 0),
                "create_time": _format_datetime(item.get("create_time")),
                "media_json": _normalize_media_json(item.get("media_json")),
                "author": normalize_text(item.get("author")),
                "author_id": author_id,
                "created_at": _format_datetime(item.get("create_time")),
                "likes": int(item.get("like_count") or 0),
                "is_liked": comment_id in liked_ids,
                "replies": [],
            }
        )
    return {"list": _build_comment_tree(formatted), "total": len(formatted), "page": 1, "page_size": len(formatted) or 10}


def get_post_list(
    page: int = 1,
    page_size: int = 10,
    keyword: Optional[str] = None,
    tag: Optional[str] = None,
    sort: str = "hot",
    current_user: Optional[Any] = None,
) -> PostListResponse:
    try:
        if _db_has_posts():
            result = _db_get_posts(page=page, page_size=page_size, keyword=keyword, tag=tag, sort=sort, current_user=current_user)
            if result is not None:
                return PostListResponse(**result)
    except Exception as exc:  # noqa: BLE001
        logger.warning("读取社区帖子失败，回退 mock：%s", exc)
    return PostListResponse(**_mock_get_posts(page=page, page_size=page_size, keyword=keyword, current_user=current_user))


def get_post_detail(post_id: int, current_user: Optional[Any] = None) -> Optional[CommunityPost]:
    try:
        if _db_has_posts():
            post = _db_get_post(post_id, current_user=current_user)
            if post is not None:
                try:
                    execute_update(
                        "UPDATE community_post SET view_count = view_count + 1, updated_at = NOW() WHERE id = %s",
                        [post_id],
                    )
                except Exception as exc:  # noqa: BLE001
                    logger.warning("更新社区帖子浏览数失败：%s", exc)
                post["view_count"] = int(post.get("view_count") or 0) + 1
                post["views"] = post["view_count"]
                post["update_time"] = _now_text()
                post["updated_at"] = post["update_time"]

                current_user_id = _get_current_user_id(current_user)
                if current_user_id is not None:
                    try:
                        existing = execute_one(
                            """
                            SELECT id FROM browse_history
                            WHERE user_id = %s
                              AND target_type = 'post'
                              AND target_id = %s
                            LIMIT 1
                            """,
                            [current_user_id, post_id],
                        )
                        if existing:
                            execute_update(
                                """
                                UPDATE browse_history
                                SET browse_time = NOW()
                                WHERE id = %s
                                """,
                                [int(existing["id"])],
                            )
                        else:
                            execute_update(
                                """
                                INSERT INTO browse_history (user_id, news_id, target_type, target_id, browse_time, created_at)
                                VALUES (%s, %s, 'post', %s, NOW(), NOW())
                                """,
                                [current_user_id, 0, post_id],
                            )
                    except Exception as exc:  # noqa: BLE001
                        logger.warning("写入帖子浏览历史失败，已忽略：%s", exc)

                return CommunityPost(**post)
            return None
    except Exception as exc:  # noqa: BLE001
        logger.warning("读取社区帖子详情失败，回退 mock：%s", exc)

    post = _mock_get_post(post_id, current_user=current_user)
    if post is None:
        return None
    for item in FALLBACK_POSTS:
        if int(item.get("id") or 0) == post_id:
            item["heat_score"] = int(item.get("heat_score") or 0) + 1
            item["update_time"] = _now_text()
            item["updated_at"] = item["update_time"]
            break
    return CommunityPost(**post)


def create_post(request: CreatePostRequest, current_user: Optional[Any] = None) -> CommunityPost:
    if current_user is None:
        raise AppException(code=401, message="未登录或登录状态已失效")

    try:
        result = _insert_post_db(request, current_user)
        return CommunityPost(**result)
    except Exception as exc:  # noqa: BLE001
        logger.warning("创建社区帖子失败，回退 mock：%s", exc)
    return _mock_create_post(request, current_user)


def get_comments(
    post_id: int,
    page: int = 1,
    page_size: int = 10,
    current_user: Optional[Any] = None,
) -> CommentListResponse:
    try:
        if _db_has_posts():
            rows = _db_comment_rows(post_id, current_user=current_user)
            if rows is None:
                raise AppException(code=404, message="帖子不存在")
            tree = _build_comment_tree(rows)
            normalized_page = max(page, 1)
            normalized_page_size = max(page_size, 1)
            return CommentListResponse(
                list=tree[(normalized_page - 1) * normalized_page_size : normalized_page * normalized_page_size],
                total=len(tree),
                page=normalized_page,
                page_size=normalized_page_size,
            )
    except AppException:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.warning("读取社区评论失败，回退 mock：%s", exc)
    result = _mock_get_post_comments(post_id, current_user=current_user)
    normalized_page = max(page, 1)
    normalized_page_size = max(page_size, 1)
    return CommentListResponse(
        list=result["list"][(normalized_page - 1) * normalized_page_size : normalized_page * normalized_page_size],
        total=result["total"],
        page=normalized_page,
        page_size=normalized_page_size,
    )


def create_comment(post_id: int, request: CreateCommentRequest, current_user: Optional[Any] = None) -> CommentItem:
    try:
        if _db_has_posts():
            return _db_create_comment(post_id, request, current_user)
    except Exception as exc:  # noqa: BLE001
        logger.warning("创建社区评论失败，回退 mock：%s", exc)
    return _mock_create_comment(post_id, request, current_user)


def reply_comment(comment_id: int, request: CreateCommentRequest, current_user: Optional[Any] = None) -> CommentItem:
    try:
        if _db_has_posts():
            return _db_reply_comment(comment_id, request, current_user)
    except Exception as exc:  # noqa: BLE001
        logger.warning("回复社区评论失败，回退 mock：%s", exc)
    return _mock_reply_comment(comment_id, request, current_user)


def toggle_post_like(post_id: int, current_user: Optional[Any] = None) -> LikeResponse:
    try:
        if _db_has_posts():
            return _db_toggle_post_like(post_id, current_user)
    except Exception as exc:  # noqa: BLE001
        logger.warning("切换社区帖子点赞失败，回退 mock：%s", exc)
    return _mock_toggle_post_like(post_id, current_user)


def unlike_post(post_id: int, current_user: Optional[Any] = None) -> LikeResponse:
    try:
        if _db_has_posts():
            return _db_unlike_post(post_id, current_user)
    except Exception as exc:  # noqa: BLE001
        logger.warning("取消社区帖子点赞失败，回退 mock：%s", exc)
    return _mock_unlike_post(post_id, current_user)


def toggle_post_favorite(post_id: int, current_user: Optional[Any] = None) -> FavoriteResponse:
    try:
        if _db_has_posts():
            return _db_toggle_post_favorite(post_id, current_user)
    except Exception as exc:  # noqa: BLE001
        logger.warning("切换社区帖子收藏失败，回退 mock：%s", exc)
    return _mock_toggle_post_favorite(post_id, current_user)


def unfavorite_post(post_id: int, current_user: Optional[Any] = None) -> FavoriteResponse:
    try:
        if _db_has_posts():
            return _db_unfavorite_post(post_id, current_user)
    except Exception as exc:  # noqa: BLE001
        logger.warning("取消社区帖子收藏失败，回退 mock：%s", exc)
    return _mock_unfavorite_post(post_id, current_user)


def record_post_browse(post_id: int, current_user: Optional[Any] = None) -> dict:
    """记录社区帖子浏览历史，重复浏览只更新 browse_time。"""
    user_id = _current_user_id(current_user)
    if user_id is None:
        return {"recorded": False, "message": "未登录，不记录浏览"}

    try:
        if _db_has_posts():
            existing = execute_one(
                """
                SELECT id FROM browse_history
                WHERE user_id = %s AND target_type = 'post' AND target_id = %s
                LIMIT 1
                """,
                [user_id, post_id],
            )
            if existing:
                execute_update(
                    "UPDATE browse_history SET browse_time = NOW() WHERE id = %s",
                    [int(existing["id"])],
                )
            else:
                execute_update(
                    """
                    INSERT INTO browse_history (user_id, news_id, target_type, target_id, browse_time, created_at)
                    VALUES (%s, 0, 'post', %s, NOW(), NOW())
                    """,
                    [user_id, post_id],
                )
            return {"recorded": True, "message": "浏览记录已保存"}
    except Exception:
        pass
    return {"recorded": False, "message": "记录失败"}


def get_post_favorite_status(post_id: int, current_user: Optional[Any] = None) -> dict:
    """查询当前用户是否已收藏指定帖子。"""
    user_id = _current_user_id(current_user)
    if user_id is None:
        return {"favorited": False}

    try:
        if _db_has_posts():
            row = execute_one(
                """
                SELECT id FROM favorite
                WHERE user_id = %s AND target_type = 'post' AND target_id = %s
                LIMIT 1
                """,
                [user_id, post_id],
            )
            return {"favorited": row is not None}
    except Exception:
        pass
    return {"favorited": False}


def toggle_comment_like(comment_id: int, current_user: Optional[Any] = None) -> CommentLikeResult:
    try:
        if _db_has_posts():
            return _db_toggle_comment_like(comment_id, current_user)
    except Exception as exc:  # noqa: BLE001
        logger.warning("切换社区评论点赞失败，回退 mock：%s", exc)
    return _mock_toggle_comment_like(comment_id, current_user)


def delete_comment(comment_id: int, current_user: Optional[Any] = None) -> dict[str, Any]:
    try:
        if _db_has_posts():
            result = _db_delete_comment(comment_id, current_user)
            if result is not None:
                return result
    except Exception as exc:  # noqa: BLE001
        logger.warning("鍒犻櫎绀惧尯璇勮澶辫触锛屽洖閫€ mock锛?s", exc)
    return _mock_delete_comment(comment_id, current_user)


def block_user(blocked_user_id: int, current_user: Optional[Any] = None) -> BlockResponse:
    try:
        if _db_has_posts():
            return _db_block_user(blocked_user_id, current_user)
    except Exception as exc:  # noqa: BLE001
        logger.warning("拉黑用户失败，回退 mock：%s", exc)
    return _mock_block_user(blocked_user_id, current_user)


def unblock_user(blocked_user_id: int, current_user: Optional[Any] = None) -> BlockResponse:
    try:
        if _db_has_posts():
            return _db_unblock_user(blocked_user_id, current_user)
    except Exception as exc:  # noqa: BLE001
        logger.warning("取消拉黑用户失败，回退 mock：%s", exc)
    return _mock_unblock_user(blocked_user_id, current_user)


def get_hot_search(limit: int = 10) -> list[HotSearchItem]:
    try:
        rows = _db_hot_topics(limit=limit)
        if rows:
            return [HotSearchItem(**row) for row in rows]
    except Exception as exc:  # noqa: BLE001
        logger.warning("读取社区热搜失败，回退 mock：%s", exc)
    return [HotSearchItem(**row) for row in _mock_hot_search(limit=limit)]


def get_hot_topics(limit: int = 10) -> list[HotSearchItem]:
    return get_hot_search(limit=limit)


def get_hot_tags(limit: int = 10) -> list[dict[str, Any]]:
    try:
        rows = execute_query(
            """
            SELECT tags FROM community_post WHERE status = 1 AND tags IS NOT NULL
            """,
            [],
        )
        if not rows:
            return []

        tag_counter: dict[str, int] = {}
        for row in rows:
            tags_json = row.get("tags")
            if not tags_json:
                continue
            try:
                tags = json.loads(tags_json) if isinstance(tags_json, str) else tags_json
                if isinstance(tags, list):
                    for tag in tags:
                        tag_name = str(tag).strip()
                        if tag_name:
                            tag_counter[tag_name] = tag_counter.get(tag_name, 0) + 1
            except Exception:
                continue

        sorted_tags = sorted(tag_counter.items(), key=lambda x: -x[1])[:limit]
        return [{"name": name, "count": count} for name, count in sorted_tags]
    except Exception as exc:
        logger.warning("读取热门标签失败：%s", exc)
        return []


def _get_all_categories() -> list[dict[str, Any]]:
    try:
        rows = execute_query(
            """
            SELECT id, name, code, description
            FROM news_category
            WHERE status = 1
            ORDER BY sort ASC, id ASC
            """
        )
        return rows or []
    except Exception:  # noqa: BLE001
        return []


def _get_news_by_category(category_id: int, limit: int = 10) -> list[dict[str, Any]]:
    try:
        rows = execute_query(
            """
            SELECT n.id, n.title, n.summary, n.content, n.category_id, nc.name AS category_name
            FROM news n
            LEFT JOIN news_category nc ON nc.id = n.category_id
            WHERE n.status = 1 AND n.category_id = %s
            ORDER BY n.publish_time DESC, n.id DESC
            LIMIT %s
            """,
            [category_id, limit],
        )
        return rows or []
    except Exception:  # noqa: BLE001
        return []


async def ai_news_helper(question: str) -> AIHelperResponse:
    """AI 新闻助手：基于系统内容提供智能回答。"""
    import httpx
    from app.core.config import settings
    from app.modules.news.service import get_news_list, get_hot_news
    from app.modules.community.service import get_post_list, get_hot_search

    try:
        news_list = get_news_list(page=1, page_size=50)
        hot_news = get_hot_news(limit=20)
        posts = get_post_list(page=1, page_size=30)
        hot_topics = get_hot_search(limit=20)
        categories = _get_all_categories()

        news_context = "\n".join([
            f"新闻 {n['id']} [{n.get('category_name', '')}]: {n['title']} - {(n.get('content', '') or n.get('summary', ''))[:300]}"
            for n in news_list.get("list", [])[:30]
        ])

        hot_news_context = "\n".join([
            f"热点新闻 {n['id']} [{n.get('category_name', '')}]: {n['title']} - {(n.get('content', '') or n.get('summary', ''))[:150]}"
            for n in hot_news[:15]
        ])

        post_context = "\n".join([
            f"社区帖子 {p.id}: {p.title} - {p.content[:200]}"
            for p in posts.list[:15]
        ])

        topic_context = "\n".join([
            f"热点话题 {t.id}: {t.keyword} (搜索量: {t.search_count})"
            for t in hot_topics[:15]
        ])

        category_context = "\n".join([
            f"分类 {c['id']}: {c['name']} ({c['code']}) - {c.get('description', '')}"
            for c in categories
        ])

        category_news_context = ""
        for category in categories:
            cat_news = _get_news_by_category(category["id"], limit=5)
            if cat_news:
                cat_news_lines = "\n".join([
                    f"  - 新闻 {n['id']}: {n['title']} - {(n.get('content', '') or n.get('summary', ''))[:200]}"
                    for n in cat_news
                ])
                category_news_context += f"\n【{category['name']}】\n{cat_news_lines}\n"

        system_prompt = f"""你是一个专业的AI新闻助手，运行在智能新闻摘要系统中。请根据以下系统内容回答用户的问题。

【新闻分类】
{category_context}

【最新新闻】
{news_context}

【热点新闻】
{hot_news_context}

【各分类新闻】
{category_news_context}

【社区讨论帖子】
{post_context}

【热点话题】
{topic_context}

请根据以上内容回答用户的问题。如果问题与系统内容相关，请引用具体信息进行回答。如果问题与系统内容无关，请礼貌地告知用户当前系统的数据范围。回答要简洁、准确、有价值。"""

        ai_service_url = f"{settings.ai_service_url}/ai/chat"
        logger.info(f"🚀 [REAL API] 调用 AI 服务生成新闻助手回答: {ai_service_url}")
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                ai_service_url,
                json={
                    "question": question,
                    "context": system_prompt
                }
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("code") == 200 and "data" in data:
                    answer = data["data"].get("answer", "")
                    if answer:
                        logger.info("✅ [REAL API] AI 新闻助手回答生成成功")
                        return AIHelperResponse(
                            success=True,
                            message="success",
                            answer=answer
                        )
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"❌ [REAL API] AI 服务调用失败，回退到关键词匹配：{exc}")

    logger.info("🤖 [FALLBACK] 使用关键词匹配回答")
    news_list = get_news_list(page=1, page_size=50)
    hot_topics = get_hot_search(limit=20)
    categories = _get_all_categories()

    matched_category = None
    for category in categories:
        if category["name"] in question or category["code"] in question:
            matched_category = category
            break

    if matched_category:
        cat_news = _get_news_by_category(matched_category["id"], limit=10)
        if cat_news:
            news_lines = []
            for i, n in enumerate(cat_news[:5], 1):
                content = (n.get("content", "") or n.get("summary", ""))[:100]
                news_lines.append(f"{i}. **{n['title']}** - {content}")
            news_text = "\n".join(news_lines)
            return AIHelperResponse(
                success=True,
                message="success",
                answer=f"根据系统数据，当前【{matched_category['name']}】分类下的新闻包括：\n\n{news_text}\n\n如需了解某条新闻的详细内容，请告诉我。"
            )
        else:
            return AIHelperResponse(
                success=True,
                message="success",
                answer=f"当前【{matched_category['name']}】分类下暂无新闻。"
            )

    keywords = ["新闻", "摘要", "热点", "话题", "社区", "帖子", "讨论"]
    matched_keywords = [k for k in keywords if k in question]

    if matched_keywords:
        if "新闻" in question or "摘要" in question:
            news_count = len(news_list.get("list", []))
            cat_names = ", ".join([c["name"] for c in categories])
            return AIHelperResponse(
                success=True,
                message="success",
                answer=f"系统目前有 {news_count} 条新闻，涵盖 {cat_names} 等分类。你可以在首页浏览新闻摘要，了解最新资讯。"
            )
        if "热点" in question or "话题" in question:
            topics = ", ".join([t.keyword for t in hot_topics[:5]])
            return AIHelperResponse(
                success=True,
                message="success",
                answer=f"当前热点话题有：{topics}。点击查看详细内容。"
            )
        if "社区" in question or "帖子" in question:
            posts = get_post_list(page=1, page_size=30)
            post_count = len(posts.list)
            return AIHelperResponse(
                success=True,
                message="success",
                answer=f"社区里有 {post_count} 条讨论帖子，你可以浏览热门话题，参与讨论。"
            )

    return AIHelperResponse(
        success=True,
        message="success",
        answer="谢谢你的提问！我是 AI 新闻助手，可以帮你了解系统中的新闻内容、热点话题和社区讨论。请问有什么可以帮你的？",
    )


async def generate_comments_summary(comments: list[str]) -> CommentsSummaryResponse:
    """生成评论总结（接收评论列表，调用 AI 服务）。"""
    import httpx
    from app.core.config import settings

    if not comments:
        return CommentsSummaryResponse(
            summary="暂无评论可总结",
            sentiment="neutral",
            keyword="",
            keywords=[],
            key_points=[],
            source="fallback"
        )

    try:
        ai_service_url = f"{settings.ai_service_url}/ai/comment-summary"
        logger.info(f"🚀 [REAL API] 调用 AI 服务生成评论总结: {ai_service_url}")
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                ai_service_url,
                json={
                    "comments": comments
                }
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("code") == 200 and "data" in data:
                    ai_data = data["data"]
                    logger.info("✅ [REAL API] AI 评论总结生成成功")
                    return CommentsSummaryResponse(
                        summary=ai_data.get("summary", ""),
                        sentiment=ai_data.get("sentiment", "neutral"),
                        keyword=ai_data.get("keyword", "") or ",".join(ai_data.get("keywords", [])[:3]),
                        keywords=ai_data.get("keywords", []),
                        key_points=ai_data.get("key_points", []),
                        source=ai_data.get("source", "llm")
                    )
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"❌ [REAL API] AI 服务调用失败，返回基础总结：{exc}")

    import re
    all_text = "\n".join(comments)
    positive_words = ["支持", "赞同", "好", "棒", "赞", "喜欢", "满意", "精彩", "优秀", "不错", "推荐", "认可", "肯定"]
    negative_words = ["反对", "不赞同", "差", "垃圾", "烂", "讨厌", "失望", "糟糕", "问题", "不满", "投诉", "批评"]
    pos_count = sum(1 for word in positive_words if word in all_text)
    neg_count = sum(1 for word in negative_words if word in all_text)
    sentiment = "positive" if pos_count > neg_count else "negative" if neg_count > pos_count else "neutral"

    words = re.findall(r'[一-鿿]{2,}', all_text)
    keyword_freq = {}
    for word in words:
        keyword_freq[word] = keyword_freq.get(word, 0) + 1
    sorted_keywords = sorted(keyword_freq.items(), key=lambda x: (-x[1], -len(x[0])))
    keywords = [word for word, _ in sorted_keywords[:5]]

    key_points = []
    for i, comment in enumerate(comments[:3], 1):
        if comment.strip():
            key_points.append(f"观点{i}：{comment[:50]}")

    logger.info("🤖 [FALLBACK] 使用基础总结（关键词匹配）")
    sentiment_text = "正面" if sentiment == "positive" else "负面" if sentiment == "negative" else "中立"
    basic_summary = f"该话题共有 {len(comments)} 条评论。整体情感倾向为{sentiment_text}。主要讨论热点包括：{('、'.join(keywords)) if keywords else '暂无明显热点'}。建议查看完整评论了解详细观点。"

    return CommentsSummaryResponse(
        summary=basic_summary,
        sentiment=sentiment,
        keyword=",".join(keywords[:3]),
        keywords=keywords,
        key_points=key_points,
        source="fallback"
    )


async def get_comments_summary(post_id: int) -> CommentsSummaryResponse:
    """获取帖子的评论区 AI 总结。"""
    all_comments = []
    page = 1
    page_size = 50
    total_text_length = 0
    max_text_length = 10000

    while True:
        comment_result = get_comments(post_id, page=page, page_size=page_size, current_user=None)
        if not comment_result.list:
            break

        for comment in comment_result.list:
            comment_text = getattr(comment, "content", "")
            if total_text_length + len(comment_text) <= max_text_length:
                all_comments.append(comment_text)
                total_text_length += len(comment_text)
            else:
                break

        if len(comment_result.list) < page_size:
            break
        page += 1

    return await generate_comments_summary(all_comments)


# ─── AI Session & Message ──────────────────────────────────────


def _build_community_context() -> str:
    """构建社区上下文（复用 ai_news_helper 中的逻辑片段）。"""
    from app.modules.news.service import get_news_list, get_hot_news

    try:
        news_list = get_news_list(page=1, page_size=50)
        hot_news = get_hot_news(limit=20)
        posts = get_post_list(page=1, page_size=30)
        hot_topics = get_hot_search(limit=20)
        categories = _get_all_categories()

        news_context = "\n".join([
            f"新闻 {n['id']} [{n.get('category_name', '')}]: {n['title']} - {(n.get('content', '') or n.get('summary', ''))[:300]}"
            for n in news_list.get("list", [])[:30]
        ])

        hot_news_context = "\n".join([
            f"热点新闻 {n['id']} [{n.get('category_name', '')}]: {n['title']} - {(n.get('content', '') or n.get('summary', ''))[:150]}"
            for n in hot_news[:15]
        ])

        post_context = "\n".join([
            f"社区帖子 {p.id}: {p.title} - {p.content[:200]}"
            for p in posts.list[:15]
        ])

        topic_context = "\n".join([
            f"热点话题 {t.id}: {t.keyword} (搜索量: {t.search_count})"
            for t in hot_topics[:15]
        ])

        category_context = "\n".join([
            f"分类 {c['id']}: {c['name']} ({c['code']}) - {c.get('description', '')}"
            for c in categories
        ])

        category_news_context = ""
        for category in categories:
            cat_news = _get_news_by_category(category["id"], limit=5)
            if cat_news:
                cat_news_lines = "\n".join([
                    f"  - 新闻 {n['id']}: {n['title']} - {(n.get('content', '') or n.get('summary', ''))[:200]}"
                    for n in cat_news
                ])
                category_news_context += f"\n【{category['name']}】\n{cat_news_lines}\n"

        return f"""【新闻分类】
{category_context}

【最新新闻】
{news_context}

【热点新闻】
{hot_news_context}

【各分类新闻】
{category_news_context}

【社区讨论帖子】
{post_context}

【热点话题】
{topic_context}"""
    except Exception as exc:
        logger.warning("构建社区上下文失败：%s", exc)
        return ""


async def _call_ai_service(
    question: str,
    history: list[dict[str, str]] | None = None,
) -> str:
    """调用 AI 服务生成回答（复用 ai_news_helper 的调用方式）。"""
    import httpx
    from app.core.config import settings

    system_context = _build_community_context()

    # 拼接 history 文本
    history_text = ""
    if history:
        parts = []
        for h in history[-8:]:  # 最多取最近 8 条
            role_label = "用户" if h["role"] == "user" else "AI助手"
            content = h["content"][:200]
            parts.append(f"{role_label}：{content}")
        if parts:
            history_text = "\n".join(parts) + "\n"

    system_prompt = f"""你是一个专业的AI新闻助手，运行在智能新闻摘要系统中。请根据以下系统内容回答用户的问题。

{system_context}

【对话历史】
{history_text}

请根据以上内容回答用户的问题。如果问题与系统内容相关，请引用具体信息进行回答。如果问题与系统内容无关，请礼貌地告知用户当前系统的数据范围。回答要简洁、准确、有价值。"""

    try:
        ai_service_url = f"{settings.ai_service_url}/ai/chat"
        logger.info("🚀 [AI SESSION] 调用 AI 服务: %s", ai_service_url)
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                ai_service_url,
                json={"question": question, "context": system_prompt},
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("code") == 200 and "data" in data:
                    answer = data["data"].get("answer", "")
                    if answer:
                        logger.info("✅ [AI SESSION] AI 回答生成成功")
                        return answer
    except Exception as exc:
        logger.warning("❌ [AI SESSION] AI 服务调用失败：%s", exc)

    # fallback 关键词匹配
    from app.modules.news.service import get_news_list, get_hot_news

    categories = _get_all_categories()
    matched_category = None
    for category in categories:
        if category["name"] in question or category["code"] in question:
            matched_category = category
            break

    if matched_category:
        cat_news = _get_news_by_category(matched_category["id"], limit=10)
        if cat_news:
            news_lines = []
            for i, n in enumerate(cat_news[:5], 1):
                content = (n.get("content", "") or n.get("summary", ""))[:100]
                news_lines.append(f"{i}. **{n['title']}** - {content}")
            news_text = "\n".join(news_lines)
            return f"根据系统数据，当前【{matched_category['name']}】分类下的新闻包括：\n\n{news_text}\n\n如需了解某条新闻的详细内容，请告诉我。"
        else:
            return f"当前【{matched_category['name']}】分类下暂无新闻。"

    keywords = ["新闻", "摘要", "热点", "话题", "社区", "帖子", "讨论"]
    matched = [k for k in keywords if k in question]
    if matched:
        if "新闻" in question or "摘要" in question:
            news_list = get_news_list(page=1, page_size=50)
            categories = _get_all_categories()
            count = len(news_list.get("list") or [])
            cat_names = ", ".join([c["name"] for c in categories])
            return f"系统目前有 {count} 条新闻，涵盖 {cat_names} 等分类。你可以在首页浏览新闻摘要，了解最新资讯。"
        if "热点" in question or "话题" in question:
            hot_topics = get_hot_search(limit=5)
            topics = ", ".join(t.keyword for t in hot_topics[:5])
            return f"当前热点话题有：{topics}。点击查看详细内容。"
        if "社区" in question or "帖子" in question:
            posts = get_post_list(page=1, page_size=30)
            post_count = len(posts.list)
            return f"社区里有 {post_count} 条讨论帖子，你可以浏览热门话题，参与讨论。"

    return "谢谢你的提问！我是 AI 新闻助手，可以帮你了解系统中的新闻内容、热点话题和社区讨论。请问有什么可以帮你的？"


def _session_row_to_item(
    row: dict[str, Any],
    message_count: int = 0,
    last_message_preview: str = "",
) -> dict[str, Any]:
    return {
        "id": int(row["id"]),
        "title": normalize_text(row.get("title", "")),
        "summary": normalize_text(row.get("summary") or "") or None,
        "source_type": row.get("source_type") or None,
        "source_post_id": row.get("source_post_id"),
        "source_news_id": row.get("source_news_id"),
        "status": row.get("status", "active"),
        "created_at": _format_datetime(row.get("created_at")),
        "updated_at": _format_datetime(row.get("updated_at")),
        "last_message_at": _format_datetime(row.get("last_message_at")) if row.get("last_message_at") else None,
        "message_count": message_count,
        "last_message_preview": last_message_preview,
    }


def _message_row_to_item(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": int(row["id"]),
        "session_id": int(row["session_id"]),
        "user_id": int(row["user_id"]),
        "role": row["role"],
        "content": normalize_text(row.get("content", "")),
        "status": row.get("status", "success"),
        "error_message": row.get("error_message"),
        "created_at": _format_datetime(row.get("created_at")),
    }


def _db_get_session_message_count(session_id: int) -> int:
    row = execute_one(
        "SELECT COUNT(*) AS cnt FROM community_ai_message WHERE session_id = %s",
        [session_id],
    )
    return int(row["cnt"]) if row else 0


def _db_get_session_last_message(session_id: int) -> dict | None:
    return execute_one(
        """SELECT content FROM community_ai_message
         WHERE session_id = %s AND role = 'assistant' AND status = 'success'
         ORDER BY id DESC LIMIT 1""",
        [session_id],
    )


def _db_get_recent_messages(session_id: int, limit: int = 10) -> list[dict[str, Any]]:
    rows = execute_query(
        """SELECT id, session_id, user_id, role, content, status, error_message, created_at
         FROM community_ai_message
         WHERE session_id = %s AND status = 'success'
         ORDER BY id ASC""",
        [session_id],
    )
    return rows[-limit:] if rows else []


async def create_ai_session(
    request: CommunityAiSessionCreate,
    current_user: UserInfo,
) -> CommunityAiSessionDetailResponse:
    """创建 AI 会话，可选携带首条问题。"""
    user_id = _current_user_id(current_user)
    if user_id is None:
        raise AppException(code=401, message="未登录或登录状态已失效")

    title = request.question[:30] if request.question else "新的社区 AI 会话"
    if request.question and len(request.question) > 30:
        title = request.question[:27] + "..."

    # 插入 session
    session_id = execute_insert(
        """INSERT INTO community_ai_session
         (user_id, title, summary, source_type, source_post_id, source_news_id, status, last_message_at, created_at, updated_at)
         VALUES (%s, %s, %s, %s, %s, %s, 'active', NOW(), NOW(), NOW())""",
        [user_id, title, "", request.source_type, request.source_post_id, request.source_news_id],
    )

    messages: list[dict] = []

    if request.question:
        # 插入 user message
        execute_insert(
            """INSERT INTO community_ai_message (session_id, user_id, role, content, status, created_at)
             VALUES (%s, %s, 'user', %s, 'success', NOW())""",
            [session_id, user_id, request.question],
        )
        messages.append({
            "id": 0,
            "session_id": session_id,
            "user_id": user_id,
            "role": "user",
            "content": request.question,
            "status": "success",
            "error_message": None,
            "created_at": _now_text(),
        })

        # 调用 AI
        answer = await _call_ai_service(request.question)

        execute_insert(
            """INSERT INTO community_ai_message (session_id, user_id, role, content, status, created_at)
             VALUES (%s, %s, 'assistant', %s, 'success', NOW())""",
            [session_id, user_id, answer],
        )
        messages.append({
            "id": 0,
            "session_id": session_id,
            "user_id": user_id,
            "role": "assistant",
            "content": answer,
            "status": "success",
            "error_message": None,
            "created_at": _now_text(),
        })

        # 更新 last_message_at
        execute_update(
            "UPDATE community_ai_session SET last_message_at = NOW(), updated_at = NOW() WHERE id = %s",
            [session_id],
        )

    # 查回 session 完整数据
    row = execute_one("SELECT * FROM community_ai_session WHERE id = %s", [session_id])
    if row is None:
        raise AppException(code=500, message="创建会话失败")

    message_count = _db_get_session_message_count(session_id)
    last_msg = _db_get_session_last_message(session_id)
    preview = normalize_text(last_msg["content"][:80]) if last_msg and last_msg.get("content") else ""

    return CommunityAiSessionDetailResponse(
        session=CommunityAiSessionItem(**_session_row_to_item(row, message_count=message_count, last_message_preview=preview)),
        messages=[CommunityAiMessageItem(**m) for m in messages],
    )


def get_ai_session_list(
    page: int = 1,
    page_size: int = 20,
    current_user: UserInfo | None = None,
) -> CommunityAiSessionListResponse:
    """获取当前用户的 AI 会话列表。"""
    user_id = _current_user_id(current_user)
    if user_id is None:
        raise AppException(code=401, message="未登录或登录状态已失效")

    total_row = execute_one(
        "SELECT COUNT(*) AS cnt FROM community_ai_session WHERE user_id = %s AND status = 'active'",
        [user_id],
    )
    total = int(total_row["cnt"]) if total_row else 0

    if total == 0:
        return CommunityAiSessionListResponse(list=[], total=0, page=page, page_size=page_size)

    rows = execute_query(
        """SELECT * FROM community_ai_session
         WHERE user_id = %s AND status = 'active'
         ORDER BY COALESCE(last_message_at, updated_at) DESC, id DESC
         LIMIT %s OFFSET %s""",
        [user_id, page_size, (page - 1) * page_size],
    )

    items = []
    for row in rows:
        sid = int(row["id"])
        message_count = _db_get_session_message_count(sid)
        last_msg = _db_get_session_last_message(sid)
        preview = normalize_text(last_msg["content"][:80]) if last_msg and last_msg.get("content") else ""
        items.append(CommunityAiSessionItem(**_session_row_to_item(row, message_count=message_count, last_message_preview=preview)))

    return CommunityAiSessionListResponse(list=items, total=total, page=page, page_size=page_size)


def get_ai_session_detail(
    session_id: int,
    current_user: UserInfo | None = None,
) -> CommunityAiSessionDetailResponse:
    """获取单个会话的详情和消息。"""
    user_id = _current_user_id(current_user)
    if user_id is None:
        raise AppException(code=401, message="未登录或登录状态已失效")

    row = execute_one(
        "SELECT * FROM community_ai_session WHERE id = %s AND status = 'active'",
        [session_id],
    )
    if row is None:
        raise AppException(code=404, message="会话不存在")
    if int(row["user_id"]) != user_id:
        raise AppException(code=403, message="无权访问该会话")

    message_count = _db_get_session_message_count(session_id)
    last_msg = _db_get_session_last_message(session_id)
    preview = normalize_text(last_msg["content"][:80]) if last_msg and last_msg.get("content") else ""

    msg_rows = _db_get_recent_messages(session_id, limit=100)
    messages = [CommunityAiMessageItem(**_message_row_to_item(m)) for m in msg_rows]

    return CommunityAiSessionDetailResponse(
        session=CommunityAiSessionItem(**_session_row_to_item(row, message_count=message_count, last_message_preview=preview)),
        messages=messages,
    )


async def send_ai_message(
    session_id: int,
    request: CommunityAiMessageCreate,
    current_user: UserInfo,
) -> CommunityAiMessageSendResponse:
    """在已有会话中连续追问。"""
    user_id = _current_user_id(current_user)
    if user_id is None:
        raise AppException(code=401, message="未登录或登录状态已失效")

    # 校验 session
    session_row = execute_one(
        "SELECT * FROM community_ai_session WHERE id = %s AND status = 'active'",
        [session_id],
    )
    if session_row is None:
        raise AppException(code=404, message="会话不存在")
    if int(session_row["user_id"]) != user_id:
        raise AppException(code=403, message="无权访问该会话")

    # 插入 user 消息
    user_msg_id = execute_insert(
        """INSERT INTO community_ai_message (session_id, user_id, role, content, status, created_at)
         VALUES (%s, %s, 'user', %s, 'success', NOW())""",
        [session_id, user_id, request.question],
    )

    user_msg = CommunityAiMessageItem(
        id=user_msg_id,
        session_id=session_id,
        user_id=user_id,
        role="user",
        content=request.question,
        status="success",
        created_at=_now_text(),
    )

    # 获取历史消息
    history_rows = _db_get_recent_messages(session_id, limit=10)
    history = [{"role": r["role"], "content": r["content"]} for r in history_rows]

    # 调用 AI
    answer_text = "抱歉，AI 服务暂时不可用，请稍后重试。"
    try:
        answer_text = await _call_ai_service(request.question, history)
    except Exception as exc:
        logger.error("AI 消息发送异常：%s", exc)
        answer_text = "抱歉，AI 服务暂时不可用，请稍后重试。"

    assistant_msg_id = execute_insert(
        """INSERT INTO community_ai_message (session_id, user_id, role, content, status, created_at)
         VALUES (%s, %s, 'assistant', %s, 'success', NOW())""",
        [session_id, user_id, answer_text],
    )

    assistant_msg = CommunityAiMessageItem(
        id=assistant_msg_id,
        session_id=session_id,
        user_id=user_id,
        role="assistant",
        content=answer_text,
        status="success",
        created_at=_now_text(),
    )

    # 更新会话
    execute_update(
        "UPDATE community_ai_session SET last_message_at = NOW(), updated_at = NOW() WHERE id = %s",
        [session_id],
    )

    # 重新读取 session
    updated_row = execute_one("SELECT * FROM community_ai_session WHERE id = %s", [session_id])
    message_count = _db_get_session_message_count(session_id)
    last_msg = _db_get_session_last_message(session_id)
    preview = normalize_text(last_msg["content"][:80]) if last_msg and last_msg.get("content") else ""

    return CommunityAiMessageSendResponse(
        session=CommunityAiSessionItem(**_session_row_to_item(updated_row, message_count=message_count, last_message_preview=preview)),
        user_message=user_msg,
        assistant_message=assistant_msg,
    )


# ─── AI Session Streaming (SSE) ──────────────────────────────────


async def _call_ai_service_stream(
    question: str,
    history: list[dict[str, str]] | None = None,
):
    """流式调用 AI 服务，逐 chunk yield dict（token/done/error）。"""
    import httpx
    from app.core.config import settings

    system_context = _build_community_context()

    history_text = ""
    if history:
        parts = []
        for h in history[-8:]:
            role_label = "用户" if h["role"] == "user" else "AI助手"
            content = h["content"][:200]
            parts.append(f"{role_label}：{content}")
        if parts:
            history_text = "\n".join(parts) + "\n"

    system_prompt = f"""你是一个专业的AI新闻助手，运行在智能新闻摘要系统中。请根据以下系统内容回答用户的问题。

{system_context}

【对话历史】
{history_text}

请根据以上内容回答用户的问题。如果问题与系统内容相关，请引用具体信息进行回答。如果问题与系统内容无关，请礼貌地告知用户当前系统的数据范围。回答要简洁、准确、有价值。"""

    try:
        ai_service_url = f"{settings.ai_service_url}/ai/chat/stream"
        logger.info("🚀 [AI SESSION STREAM] 调用 AI 服务: %s", ai_service_url)
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST",
                ai_service_url,
                json={"question": question, "context": system_prompt},
            ) as response:
                if response.status_code != 200:
                    yield {"error": f"AI 服务返回错误: {response.status_code}", "done": True}
                    return

                async for line in response.aiter_lines():
                    line = line.strip()
                    if not line:
                        continue
                    if line.startswith("data: "):
                        raw = line[len("data: "):]
                        try:
                            chunk = json.loads(raw)
                            yield chunk
                            if chunk.get("done") or chunk.get("error"):
                                return
                        except json.JSONDecodeError:
                            logger.warning("SSE JSON 解析失败: %s", raw[:100])
                            continue
    except Exception as exc:
        logger.warning("❌ [AI SESSION STREAM] AI 服务调用失败：%s", exc)
        yield {"error": f"AI 服务不可用: {str(exc)}", "done": True}


async def send_ai_message_stream(
    session_id: int,
    request: CommunityAiMessageCreate,
    current_user: UserInfo,
):
    """SSE 流式：在已有会话中追问，实时返回 token。"""
    from fastapi.responses import StreamingResponse

    user_id = _current_user_id(current_user)
    if user_id is None:
        raise AppException(code=401, message="未登录或登录状态已失效")

    # 校验 session
    session_row = execute_one(
        "SELECT * FROM community_ai_session WHERE id = %s AND status = 'active'",
        [session_id],
    )
    if session_row is None:
        raise AppException(code=404, message="会话不存在")
    if int(session_row["user_id"]) != user_id:
        raise AppException(code=403, message="无权访问该会话")

    # 插入 user 消息
    user_msg_id = execute_insert(
        """INSERT INTO community_ai_message (session_id, user_id, role, content, status, created_at)
         VALUES (%s, %s, 'user', %s, 'success', NOW())""",
        [session_id, user_id, request.question],
    )

    # 获取历史消息
    history_rows = _db_get_recent_messages(session_id, limit=10)
    history = [{"role": r["role"], "content": r["content"]} for r in history_rows]

    async def event_generator():
        full_answer: list[str] = []

        try:
            async for chunk in _call_ai_service_stream(request.question, history):
                if chunk.get("error"):
                    # 保存部分内容（如有）
                    partial = "".join(full_answer)
                    if partial.strip():
                        try:
                            execute_insert(
                                """INSERT INTO community_ai_message (session_id, user_id, role, content, status, error_message, created_at)
                                 VALUES (%s, %s, 'assistant', %s, 'partial', %s, NOW())""",
                                [session_id, user_id, partial, chunk.get("error", "")],
                            )
                            execute_update(
                                "UPDATE community_ai_session SET last_message_at = NOW(), updated_at = NOW() WHERE id = %s",
                                [session_id],
                            )
                        except Exception as db_exc:
                            logger.error("保存部分 AI 回答失败: %s", db_exc)
                    yield f"data: {json.dumps({'error': chunk['error'], 'done': True}, ensure_ascii=False)}\n\n"
                    return

                if chunk.get("done"):
                    # 保存完整回答到 DB
                    answer_text = "".join(full_answer) or "AI 服务暂时无回复"
                    try:
                        assistant_msg_id = execute_insert(
                            """INSERT INTO community_ai_message (session_id, user_id, role, content, status, created_at)
                             VALUES (%s, %s, 'assistant', %s, 'success', NOW())""",
                            [session_id, user_id, answer_text],
                        )
                        execute_update(
                            "UPDATE community_ai_session SET last_message_at = NOW(), updated_at = NOW() WHERE id = %s",
                            [session_id],
                        )

                        # 重新读取 session
                        updated_row = execute_one(
                            "SELECT * FROM community_ai_session WHERE id = %s", [session_id]
                        )
                        message_count = _db_get_session_message_count(session_id)
                        last_msg = _db_get_session_last_message(session_id)
                        preview = normalize_text(last_msg["content"][:80]) if last_msg and last_msg.get("content") else ""
                        session_item = CommunityAiSessionItem(
                            **_session_row_to_item(updated_row, message_count=message_count, last_message_preview=preview)
                        )

                        yield f"data: {json.dumps({'done': True, 'message_id': assistant_msg_id, 'session_id': session_id, 'content': answer_text, 'session': session_item.model_dump()}, ensure_ascii=False)}\n\n"
                    except Exception as db_exc:
                        logger.error("保存 AI 回答失败: %s", db_exc)
                        yield f"data: {json.dumps({'error': f'保存失败: {str(db_exc)}', 'done': True}, ensure_ascii=False)}\n\n"
                    return

                token = chunk.get("token", "")
                if token:
                    full_answer.append(token)
                    yield f"data: {json.dumps({'token': token, 'done': False}, ensure_ascii=False)}\n\n"

        except Exception as exc:
            logger.error("SSE 流异常: %s", exc)
            # 保存部分内容
            partial = "".join(full_answer)
            if partial.strip():
                try:
                    execute_insert(
                        """INSERT INTO community_ai_message (session_id, user_id, role, content, status, error_message, created_at)
                         VALUES (%s, %s, 'assistant', %s, 'partial', %s, NOW())""",
                        [session_id, user_id, partial, str(exc)],
                    )
                    execute_update(
                        "UPDATE community_ai_session SET last_message_at = NOW(), updated_at = NOW() WHERE id = %s",
                        [session_id],
                    )
                except Exception:
                    pass
            yield f"data: {json.dumps({'error': f'流异常: {str(exc)}', 'done': True}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


async def create_ai_session_stream(
    request: CommunityAiSessionCreate,
    current_user: UserInfo,
):
    """SSE 流式：创建 AI 会话并可选携带首条问题，实时返回 token。"""
    from fastapi.responses import StreamingResponse

    user_id = _current_user_id(current_user)
    if user_id is None:
        raise AppException(code=401, message="未登录或登录状态已失效")

    title = request.question[:30] if request.question else "新的社区 AI 会话"
    if request.question and len(request.question) > 30:
        title = request.question[:27] + "..."

    # 插入 session
    session_id = execute_insert(
        """INSERT INTO community_ai_session
         (user_id, title, summary, source_type, source_post_id, source_news_id, status, last_message_at, created_at, updated_at)
         VALUES (%s, %s, %s, %s, %s, %s, 'active', NOW(), NOW(), NOW())""",
        [user_id, title, "", request.source_type, request.source_post_id, request.source_news_id],
    )

    async def event_generator():
        full_answer: list[str] = []

        if not request.question:
            # 无首问，直接返回 session 信息
            row = execute_one("SELECT * FROM community_ai_session WHERE id = %s", [session_id])
            session_item = CommunityAiSessionItem(
                **_session_row_to_item(row, message_count=0, last_message_preview="")
            )
            yield f"data: {json.dumps({'done': True, 'session_id': session_id, 'content': '', 'session': session_item.model_dump(), 'messages': []}, ensure_ascii=False)}\n\n"
            return

        # 插入 user 消息
        user_msg_id = execute_insert(
            """INSERT INTO community_ai_message (session_id, user_id, role, content, status, created_at)
             VALUES (%s, %s, 'user', %s, 'success', NOW())""",
            [session_id, user_id, request.question],
        )

        try:
            async for chunk in _call_ai_service_stream(request.question):
                if chunk.get("error"):
                    partial = "".join(full_answer)
                    if partial.strip():
                        try:
                            execute_insert(
                                """INSERT INTO community_ai_message (session_id, user_id, role, content, status, error_message, created_at)
                                 VALUES (%s, %s, 'assistant', %s, 'partial', %s, NOW())""",
                                [session_id, user_id, partial, chunk.get("error", "")],
                            )
                            execute_update(
                                "UPDATE community_ai_session SET last_message_at = NOW(), updated_at = NOW() WHERE id = %s",
                                [session_id],
                            )
                        except Exception:
                            pass
                    yield f"data: {json.dumps({'error': chunk['error'], 'done': True}, ensure_ascii=False)}\n\n"
                    return

                if chunk.get("done"):
                    answer_text = "".join(full_answer) or "AI 服务暂时无回复"
                    try:
                        assistant_msg_id = execute_insert(
                            """INSERT INTO community_ai_message (session_id, user_id, role, content, status, created_at)
                             VALUES (%s, %s, 'assistant', %s, 'success', NOW())""",
                            [session_id, user_id, answer_text],
                        )
                        execute_update(
                            "UPDATE community_ai_session SET last_message_at = NOW(), updated_at = NOW() WHERE id = %s",
                            [session_id],
                        )

                        row = execute_one("SELECT * FROM community_ai_session WHERE id = %s", [session_id])
                        message_count = _db_get_session_message_count(session_id)
                        last_msg = _db_get_session_last_message(session_id)
                        preview = normalize_text(last_msg["content"][:80]) if last_msg and last_msg.get("content") else ""
                        session_item = CommunityAiSessionItem(
                            **_session_row_to_item(row, message_count=message_count, last_message_preview=preview)
                        )

                        yield f"data: {json.dumps({'done': True, 'message_id': assistant_msg_id, 'session_id': session_id, 'content': answer_text, 'session': session_item.model_dump()}, ensure_ascii=False)}\n\n"
                    except Exception as db_exc:
                        logger.error("保存 AI 回答失败: %s", db_exc)
                        yield f"data: {json.dumps({'error': f'保存失败: {str(db_exc)}', 'done': True}, ensure_ascii=False)}\n\n"
                    return

                token = chunk.get("token", "")
                if token:
                    full_answer.append(token)
                    yield f"data: {json.dumps({'token': token, 'done': False}, ensure_ascii=False)}\n\n"

        except Exception as exc:
            logger.error("SSE 流异常: %s", exc)
            partial = "".join(full_answer)
            if partial.strip():
                try:
                    execute_insert(
                        """INSERT INTO community_ai_message (session_id, user_id, role, content, status, error_message, created_at)
                         VALUES (%s, %s, 'assistant', %s, 'partial', %s, NOW())""",
                        [session_id, user_id, partial, str(exc)],
                    )
                    execute_update(
                        "UPDATE community_ai_session SET last_message_at = NOW(), updated_at = NOW() WHERE id = %s",
                        [session_id],
                    )
                except Exception:
                    pass
            yield f"data: {json.dumps({'error': f'流异常: {str(exc)}', 'done': True}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


def delete_ai_session(
    session_id: int,
    current_user: UserInfo | None = None,
) -> dict[str, Any]:
    """软删除 AI 会话。"""
    user_id = _current_user_id(current_user)
    if user_id is None:
        raise AppException(code=401, message="未登录或登录状态已失效")

    row = execute_one(
        "SELECT id, user_id FROM community_ai_session WHERE id = %s AND status = 'active'",
        [session_id],
    )
    if row is None:
        raise AppException(code=404, message="会话不存在")
    if int(row["user_id"]) != user_id:
        raise AppException(code=403, message="无权删除该会话")

    execute_update(
        "UPDATE community_ai_session SET status = 'deleted', updated_at = NOW() WHERE id = %s",
        [session_id],
    )
    return {"success": True, "message": "会话已删除"}


# ─── My Posts ───────────────────────────────────────────────────


def _my_post_row_to_item(row: dict[str, Any]) -> dict[str, Any]:
    """将 community_post 行转为 MyCommunityPostItem 格式。"""
    content = normalize_text(row.get("content") or "")
    related_news_title = normalize_text(row.get("related_news_title") or "")
    images = _parse_json_list(row.get("images"))
    return {
        "id": int(row.get("id") or 0),
        "title": normalize_text(row.get("title") or ""),
        "content": content,
        "summary": content[:200] if content else "",
        "author_id": int(row.get("user_id") or 0),
        "author": normalize_text(row.get("author")) or normalize_text(row.get("nickname")) or normalize_text(row.get("username")) or f"用户{row.get('user_id', 0)}",
        "avatar": normalize_text(row.get("avatar") or ""),
        "created_at": _format_datetime(row.get("create_time") or row.get("created_at")),
        "updated_at": _format_datetime(row.get("update_time") or row.get("updated_at")),
        "tags": _parse_json_list(row.get("tags")),
        "images": images,
        "status": int(row.get("status") or 0),
        "view_count": int(row.get("view_count") or 0),
        "like_count": int(row.get("like_count") or 0),
        "comment_count": int(row.get("comment_count") or 0),
        "favorite_count": int(row.get("favorite_count") or 0),
        "likes": int(row.get("like_count") or 0),
        "comments": int(row.get("comment_count") or 0),
        "views": int(row.get("view_count") or 0),
        "related_news_id": row.get("related_news_id"),
        "related_news_title": related_news_title,
        "liked": False,
        "favorited": False,
    }


def get_my_posts(
    page: int = 1,
    page_size: int = 10,
    keyword: str | None = None,
    current_user: UserInfo | None = None,
) -> MyCommunityPostListResponse:
    """获取当前用户自己的社区帖子。"""
    user_id = _current_user_id(current_user)
    if user_id is None:
        raise AppException(code=401, message="未登录或登录状态已失效")

    try:
        where = ["cp.user_id = %s", "cp.status = 1"]
        params: list[Any] = [user_id]
        if keyword and keyword.strip():
            like_val = f"%{keyword.strip()}%"
            where.append("(cp.title LIKE %s OR cp.content LIKE %s)")
            params.extend([like_val, like_val])

        total_row = execute_one(
            f"SELECT COUNT(*) AS cnt FROM community_post cp WHERE {' AND '.join(where)}",
            params,
        )
        total = int(total_row["cnt"]) if total_row else 0

        if total == 0:
            return MyCommunityPostListResponse(list=[], total=0, page=page, page_size=page_size)

        rows = execute_query(
            f"""SELECT cp.*, u.nickname, u.username, u.avatar,
                       COALESCE(n.title, '') AS related_news_title
                FROM community_post cp
                LEFT JOIN `user` u ON u.id = cp.user_id
                LEFT JOIN news n ON n.id = cp.related_news_id
                WHERE {' AND '.join(where)}
                ORDER BY cp.created_at DESC, cp.id DESC
                LIMIT %s OFFSET %s""",
            params + [page_size, (page - 1) * page_size],
        )
        items = [_my_post_row_to_item(r) for r in rows]
        return MyCommunityPostListResponse(list=items, total=total, page=page, page_size=page_size)
    except AppException:
        raise
    except Exception as exc:
        logger.warning("获取我的帖子失败：%s", exc)
        raise AppException(code=500, message="获取我的帖子失败") from exc


# ─── Received Interactions ──────────────────────────────────────


def _get_my_post_ids(user_id: int) -> list[int]:
    """获取当前用户所有正常帖子的 id 列表。"""
    rows = execute_query(
        "SELECT id FROM community_post WHERE user_id = %s AND status = 1",
        [user_id],
    )
    return [int(r["id"]) for r in rows]


def get_received_likes(
    page: int = 1,
    page_size: int = 10,
    current_user: UserInfo | None = None,
) -> ReceivedInteractionListResponse:
    """获取别人对我帖子的点赞。"""
    user_id = _current_user_id(current_user)
    if user_id is None:
        raise AppException(code=401, message="未登录或登录状态已失效")

    post_ids = _get_my_post_ids(user_id)
    if not post_ids:
        return ReceivedInteractionListResponse(list=[], total=0, page=page, page_size=page_size)

    placeholders = ",".join(["%s"] * len(post_ids))
    # 过滤自己给自己点赞
    total_row = execute_one(
        f"""SELECT COUNT(*) AS cnt FROM user_like ul
            WHERE ul.target_type = 'post'
            AND ul.target_id IN ({placeholders})
            AND ul.user_id != %s""",
        [*post_ids, user_id],
    )
    total = int(total_row["cnt"]) if total_row else 0
    if total == 0:
        return ReceivedInteractionListResponse(list=[], total=0, page=page, page_size=page_size)

    rows = execute_query(
        f"""SELECT ul.id, ul.user_id AS actor_user_id,
                   u.nickname AS actor_nickname, u.avatar AS actor_avatar,
                   ul.created_at AS action_time,
                   cp.id AS target_post_id, cp.title AS target_post_title,
                   SUBSTRING(cp.content, 1, 200) AS target_post_summary,
                   cp.created_at AS target_post_created_at,
                   cp.related_news_id, COALESCE(n.title, '') AS related_news_title
            FROM user_like ul
            LEFT JOIN `user` u ON u.id = ul.user_id
            LEFT JOIN community_post cp ON cp.id = ul.target_id
            LEFT JOIN news n ON n.id = cp.related_news_id
            WHERE ul.target_type = 'post'
            AND ul.target_id IN ({placeholders})
            AND ul.user_id != %s
            ORDER BY ul.created_at DESC, ul.id DESC
            LIMIT %s OFFSET %s""",
        [*post_ids, user_id, page_size, (page - 1) * page_size],
    )
    items = [
        ReceivedInteractionItem(
            id=r["id"],
            actor_user_id=r["actor_user_id"],
            actor_nickname=normalize_text(r.get("actor_nickname") or ""),
            actor_avatar=normalize_text(r.get("actor_avatar") or ""),
            action_type="like",
            action_time=_format_datetime(r.get("action_time")),
            target_post_id=r["target_post_id"],
            target_post_title=normalize_text(r.get("target_post_title") or ""),
            target_post_summary=normalize_text(r.get("target_post_summary") or ""),
            target_post_created_at=_format_datetime(r.get("target_post_created_at")),
            related_news_id=r.get("related_news_id"),
            related_news_title=normalize_text(r.get("related_news_title") or ""),
        )
        for r in rows
    ]
    return ReceivedInteractionListResponse(list=items, total=total, page=page, page_size=page_size)


def get_received_comments(
    page: int = 1,
    page_size: int = 10,
    current_user: UserInfo | None = None,
) -> ReceivedInteractionListResponse:
    """获取别人评论我帖子的记录。"""
    user_id = _current_user_id(current_user)
    if user_id is None:
        raise AppException(code=401, message="未登录或登录状态已失效")

    post_ids = _get_my_post_ids(user_id)
    if not post_ids:
        return ReceivedInteractionListResponse(list=[], total=0, page=page, page_size=page_size)

    placeholders = ",".join(["%s"] * len(post_ids))
    # 过滤自己评论自己帖子、过滤已删除（status=4）评论
    total_row = execute_one(
        f"""SELECT COUNT(*) AS cnt FROM post_comment pc
            WHERE pc.post_id IN ({placeholders})
            AND pc.status IN (1, 2)
            AND pc.user_id != %s""",
        [*post_ids, user_id],
    )
    total = int(total_row["cnt"]) if total_row else 0
    if total == 0:
        return ReceivedInteractionListResponse(list=[], total=0, page=page, page_size=page_size)

    rows = execute_query(
        f"""SELECT pc.id, pc.user_id AS actor_user_id,
                   u.nickname AS actor_nickname, u.avatar AS actor_avatar,
                   pc.created_at AS action_time,
                   pc.content AS comment_content,
                   cp.id AS target_post_id, cp.title AS target_post_title,
                   SUBSTRING(cp.content, 1, 200) AS target_post_summary,
                   cp.created_at AS target_post_created_at,
                   cp.related_news_id, COALESCE(n.title, '') AS related_news_title
            FROM post_comment pc
            LEFT JOIN `user` u ON u.id = pc.user_id
            LEFT JOIN community_post cp ON cp.id = pc.post_id
            LEFT JOIN news n ON n.id = cp.related_news_id
            WHERE pc.post_id IN ({placeholders})
            AND pc.status IN (1, 2)
            AND pc.user_id != %s
            ORDER BY pc.created_at DESC, pc.id DESC
            LIMIT %s OFFSET %s""",
        [*post_ids, user_id, page_size, (page - 1) * page_size],
    )
    items = [
        ReceivedInteractionItem(
            id=r["id"],
            actor_user_id=r["actor_user_id"],
            actor_nickname=normalize_text(r.get("actor_nickname") or ""),
            actor_avatar=normalize_text(r.get("actor_avatar") or ""),
            action_type="comment",
            action_time=_format_datetime(r.get("action_time")),
            comment_id=r["id"],
            comment_content=normalize_text(r.get("comment_content") or ""),
            target_post_id=r["target_post_id"],
            target_post_title=normalize_text(r.get("target_post_title") or ""),
            target_post_summary=normalize_text(r.get("target_post_summary") or ""),
            target_post_created_at=_format_datetime(r.get("target_post_created_at")),
            related_news_id=r.get("related_news_id"),
            related_news_title=normalize_text(r.get("related_news_title") or ""),
        )
        for r in rows
    ]
    return ReceivedInteractionListResponse(list=items, total=total, page=page, page_size=page_size)


def get_received_favorites(
    page: int = 1,
    page_size: int = 10,
    current_user: UserInfo | None = None,
) -> ReceivedInteractionListResponse:
    """获取别人收藏我帖子的记录。favorite 表已支持 target_type='post'。"""
    user_id = _current_user_id(current_user)
    if user_id is None:
        raise AppException(code=401, message="未登录或登录状态已失效")

    post_ids = _get_my_post_ids(user_id)
    if not post_ids:
        return ReceivedInteractionListResponse(list=[], total=0, page=page, page_size=page_size)

    placeholders = ",".join(["%s"] * len(post_ids))
    # 过滤自己收藏自己帖子
    total_row = execute_one(
        f"""SELECT COUNT(*) AS cnt FROM favorite f
            WHERE f.target_type = 'post'
            AND f.target_id IN ({placeholders})
            AND f.user_id != %s""",
        [*post_ids, user_id],
    )
    total = int(total_row["cnt"]) if total_row else 0
    if total == 0:
        return ReceivedInteractionListResponse(list=[], total=0, page=page, page_size=page_size)

    rows = execute_query(
        f"""SELECT f.id, f.user_id AS actor_user_id,
                   u.nickname AS actor_nickname, u.avatar AS actor_avatar,
                   f.created_at AS action_time,
                   cp.id AS target_post_id, cp.title AS target_post_title,
                   SUBSTRING(cp.content, 1, 200) AS target_post_summary,
                   cp.created_at AS target_post_created_at,
                   cp.related_news_id, COALESCE(n.title, '') AS related_news_title
            FROM favorite f
            LEFT JOIN `user` u ON u.id = f.user_id
            LEFT JOIN community_post cp ON cp.id = f.target_id
            LEFT JOIN news n ON n.id = cp.related_news_id
            WHERE f.target_type = 'post'
            AND f.target_id IN ({placeholders})
            AND f.user_id != %s
            ORDER BY f.created_at DESC, f.id DESC
            LIMIT %s OFFSET %s""",
        [*post_ids, user_id, page_size, (page - 1) * page_size],
    )
    items = [
        ReceivedInteractionItem(
            id=r["id"],
            actor_user_id=r["actor_user_id"],
            actor_nickname=normalize_text(r.get("actor_nickname") or ""),
            actor_avatar=normalize_text(r.get("actor_avatar") or ""),
            action_type="favorite",
            action_time=_format_datetime(r.get("action_time")),
            target_post_id=r["target_post_id"],
            target_post_title=normalize_text(r.get("target_post_title") or ""),
            target_post_summary=normalize_text(r.get("target_post_summary") or ""),
            target_post_created_at=_format_datetime(r.get("target_post_created_at")),
            related_news_id=r.get("related_news_id"),
            related_news_title=normalize_text(r.get("related_news_title") or ""),
        )
        for r in rows
    ]
    return ReceivedInteractionListResponse(list=items, total=total, page=page, page_size=page_size)


FALLBACK_POSTS = [deepcopy(item) for item in MOCK_COMMUNITY_POSTS]
FALLBACK_COMMENTS = [deepcopy(item) for item in MOCK_COMMUNITY_COMMENTS]
FALLBACK_POST_LIKES = [deepcopy(item) for item in MOCK_COMMUNITY_POST_LIKES]
FALLBACK_POST_FAVORITES = [deepcopy(item) for item in MOCK_COMMUNITY_POST_FAVORITES]
FALLBACK_COMMENT_LIKES = [deepcopy(item) for item in MOCK_COMMUNITY_COMMENT_LIKES]
FALLBACK_BLOCKS = [deepcopy(item) for item in MOCK_COMMUNITY_BLOCKS]

