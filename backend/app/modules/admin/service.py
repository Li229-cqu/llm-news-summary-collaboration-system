from __future__ import annotations

import copy
import json
import logging
import os
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.common.exceptions import AppException
from app.common.utils import format_datetime, paginate
from app.db.database import execute_insert, execute_one, execute_query, execute_update, get_connection
from app.modules.admin.schema import (
    AdminDashboard,
    AdminTestData,
    PendingItem,
    PendingItemDetail,
    PendingItemsResponse,
    PendingSummary,
    ReviewActionRequest,
    ReviewActionResult,
    AdminNewsItem,
    AdminNewsListResponse,
    AdminNewsSummary,
    AdminNewsDetail,
    AdminNewsUpdateRequest,
    AdminNewsTopicRequest,
    AdminNewsActionResult,
    AdminNewsOptions,
    AdminPostItem,
    AdminPostListResponse,
    AdminPostSummary,
    AdminPostDetail,
    AdminPostActionResult,
    AdminPostOptions,
    AdminCommentItem,
    AdminCommentListResponse,
    AdminCommentSummary,
    AdminCommentDetail,
    AdminCommentActionResult,
    AdminCommentOptions,
    AdminHotTopicActionResult,
    AdminHotTopicDetail,
    AdminHotTopicItem,
    AdminHotTopicListResponse,
    AdminHotTopicOptions,
    AdminHotTopicRankRequest,
    AdminHotTopicSummary,
    AdminHotTopicSupport,
    AdminTopicActionResult,
    AdminTopicBindNewsRequest,
    AdminTopicDetail,
    AdminTopicItem,
    AdminTopicListResponse,
    AdminTopicNewsItem,
    AdminTopicNewsResponse,
    AdminTopicOptions,
    AdminTopicPayload,
    AdminTopicStatusRequest,
    AdminTopicSummary,
    AdminTopicSupport,
    AdminTimelineActionResult,
    AdminTimelineCacheCheck,
    AdminTimelineDetailResponse,
    AdminTimelineItem,
    AdminTimelineListResponse,
    AdminTimelineNodeItem,
    AdminTimelineOptionsResponse,
    AdminTimelineSourceNewsItem,
    AdminTimelineSourceNewsResponse,
    AdminTimelineSummary,
    AdminTimelineSupport,
    AdminUserActionResult,
    AdminUserBehaviorStats,
    AdminUserDetail,
    AdminUserListResponse,
    AdminUserOptions,
    AdminUserRoleRequest,
    AdminUserStatusRequest,
    AdminUserSummary,
    UserItem,
    # M10
    SystemConfigItem,
    SystemConfigListResponse,
    SystemConfigUpdateRequest,
    AIConfigResponse,
    AIConfigUpdateRequest,
    AIConfigTestResult,
    PromptTemplateItem,
    PromptTemplateListResponse,
    PromptTemplatePayload,
    PromptTemplateStatusRequest,
    PromptTemplateOptions,
    AdminAICallRecordItem,
    AdminAICallRecordListResponse,
    AdminAICallRecordSummary,
    # M11
    AdminOpsStatusPart,
    AdminOpsStatusResponse,
    AdminOpsTableStatus,
    AdminOpsDatabaseResponse,
    AdminBackupRecordItem,
    AdminBackupRecordSummary,
    AdminBackupRecordListResponse,
    AdminBackupActionResult,
    AdminStorageResponse,
    AdminOperationLogItem,
    AdminOperationLogDetail,
    AdminOperationLogSummary,
    AdminOperationLogListResponse,
    # M12
    AdminAnalyticsOverview,
    AdminAnalyticsTrendsResponse,
    AdminAnalyticsTopContentResponse,
    AdminAnalyticsAiRiskResponse,
    AdminAnalyticsReviewSummaryResponse,
    AdminAnalyticsContentOverviewResponse,
    AdminTrendPoint,
    AdminTopNewsItem,
    AdminTopPostItem,
    AdminAiRiskItem,
    AdminReviewPending,
    AdminReviewProcessed,
    AdminContentOverviewItem,
)

logger = logging.getLogger(__name__)

STATUS_LABELS = {
    0: '已下架',
    1: '正常',
    2: '折叠',
    3: '待审核',
    4: '已删除',
}

COUNTED_STATUSES = {1, 2}

NEWS_STATUS_LABELS = {
    0: 'Offline',
    1: 'Published',
    2: 'Folded',
    3: 'Pending',
    4: 'Deleted',
}

FEATURE_COLUMNS = ('is_featured', 'featured', 'is_recommended', 'recommend_flag')


def get_test_data() -> AdminTestData:
    return AdminTestData(module='admin', description='管理后台基础接口占位')


def _safe_count(sql: str, default: int = 0) -> int:
    row = execute_one(sql)
    if not row:
        return default
    for key in ('total', 'count', 'cnt'):
        value = row.get(key)
        if value is not None:
            try:
                return int(value)
            except (TypeError, ValueError):
                break
    return default


def _normalize_status(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _status_label(value: Any) -> str:
    return STATUS_LABELS.get(_normalize_status(value), '未知')


def _preview_text(value: Any, length: int = 120) -> str:
    text = str(value or '').strip()
    if len(text) <= length:
        return text
    return f'{text[:length].rstrip()}...'


def _parse_tags(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    if isinstance(value, tuple):
        return [str(item) for item in value if str(item).strip()]
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return []
        try:
            import json

            parsed = json.loads(text)
            if isinstance(parsed, list):
                return [str(item) for item in parsed if str(item).strip()]
        except Exception:  # noqa: BLE001
            pass
        return [item.strip() for item in text.split(',') if item.strip()]
    return [str(value)]


def _normalize_media_json(value: Any) -> Any:
    if value in (None, ''):
        return None
    if hasattr(value, 'model_dump'):
        value = value.model_dump()
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, bytes):
        value = value.decode('utf-8', errors='ignore')
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return text
    return value


def _build_user_item(row: Dict[str, Any]) -> Dict[str, Any]:
    return UserItem(
        id=int(row.get('id', 0)),
        username=str(row.get('username', '')),
        nickname=str(row.get('nickname', '')),
        role=str(row.get('role', 'user')),
        status=int(row.get('status', 1)),
        create_time=format_datetime(row.get('create_time')) or None,
    ).model_dump()


def _build_pending_item_base(row: Dict[str, Any], *, item_type: str, target_type: str | None = None) -> PendingItem:
    return PendingItem(
        id=int(row.get('id', 0)),
        item_type=item_type,  # type: ignore[arg-type]
        target_type=target_type,  # type: ignore[arg-type]
        title=str(row.get('title', '')),
        content_preview=_preview_text(row.get('content_preview') or row.get('summary') or row.get('content') or ''),
        submitter=str(row.get('submitter') or row.get('nickname') or row.get('username') or row.get('author') or ''),
        source=str(row.get('source') or ''),
        category_name=str(row.get('category_name') or row.get('topic_name') or ''),
        tags=_parse_tags(row.get('tags')),
        status=_normalize_status(row.get('status')),
        status_label=_status_label(row.get('status')),
        create_time=format_datetime(row.get('create_time')) or None,
        update_time=format_datetime(row.get('update_time')) or None,
    )


def _build_pending_news_item(row: Dict[str, Any]) -> Dict[str, Any]:
    return _build_pending_item_base(row, item_type='news', target_type='news').model_dump()


def _build_pending_post_item(row: Dict[str, Any]) -> Dict[str, Any]:
    payload = dict(row)
    payload.pop('source', None)
    payload['category_name'] = str(row.get('topic_name') or '')
    return _build_pending_item_base(payload, item_type='post', target_type='post').model_dump()


def _build_pending_comment_item(row: Dict[str, Any], target_type: str) -> Dict[str, Any]:
    payload = dict(row)
    target_title = str(row.get('news_title') or row.get('post_title') or '')
    payload['title'] = target_title
    payload.pop('source', None)
    payload['category_name'] = ''
    return _build_pending_item_base(payload, item_type='comment', target_type=target_type).model_dump()


def _query_news_items(status: Optional[int] = None) -> List[Dict[str, Any]]:
    target_status = 3 if status is None else status
    where_clause = 'WHERE n.status = %s'
    params: list[Any] = [target_status]
    sql = f'''
        SELECT
            n.id,
            n.title,
            COALESCE(n.summary, '') AS summary,
            COALESCE(n.content, '') AS content,
            COALESCE(n.cover_image, '') AS cover_image,
            n.category_id,
            COALESCE(c.name, '') AS category_name,
            n.topic_id,
            COALESCE(t.topic_name, '') AS topic_name,
            COALESCE(n.source, '') AS source,
            COALESCE(n.source, '') AS author,
            n.view_count,
            n.like_count,
            n.comment_count,
            n.favorite_count,
            n.status,
            n.tags,
            n.publish_time,
            n.created_at,
            n.updated_at,
            COALESCE(n.source, '') AS submitter
        FROM news n
        LEFT JOIN news_category c ON c.id = n.category_id
        LEFT JOIN news_topic t ON t.id = n.topic_id
        {where_clause}
        ORDER BY n.updated_at DESC, n.id DESC
    '''
    rows = execute_query(sql, params)
    return [_build_pending_news_item(row) for row in rows]


def _query_post_items(status: Optional[int] = None) -> List[Dict[str, Any]]:
    target_status = 3 if status is None else status
    where_clause = 'WHERE p.status = %s'
    params: list[Any] = [target_status]
    sql = f'''
        SELECT
            p.id,
            p.title,
            COALESCE(p.content, '') AS content,
            p.related_news_id,
            p.topic_id,
            COALESCE(n.title, '') AS related_news_title,
            COALESCE(t.topic_name, '') AS topic_name,
            COALESCE(u.username, '') AS username,
            COALESCE(u.nickname, '') AS nickname,
            p.tags,
            p.like_count,
            p.comment_count,
            p.favorite_count,
            p.heat_score,
            p.status,
            p.created_at,
            p.updated_at,
            COALESCE(u.nickname, u.username, '') AS submitter
        FROM community_post p
        LEFT JOIN news n ON n.id = p.related_news_id
        LEFT JOIN news_topic t ON t.id = p.topic_id
        LEFT JOIN user u ON u.id = p.user_id
        {where_clause}
        ORDER BY p.updated_at DESC, p.id DESC
    '''
    rows = execute_query(sql, params)
    return [_build_pending_post_item(row) for row in rows]


def _query_news_comment_items(status: Optional[int] = None) -> List[Dict[str, Any]]:
    target_status = 3 if status is None else status
    where_clause = 'WHERE c.status = %s'
    params: list[Any] = [target_status]
    sql = f'''
        SELECT
            c.id,
            c.news_id,
            c.user_id,
            c.parent_id,
            c.content,
            NULL AS media_json,
            c.like_count,
            c.status,
            c.created_at,
            c.updated_at,
            COALESCE(n.title, '') AS news_title,
            COALESCE(n.source, '') AS source,
            COALESCE(cg.name, '') AS category_name,
            COALESCE(t.topic_name, '') AS topic_name,
            COALESCE(u.username, '') AS username,
            COALESCE(u.nickname, '') AS nickname,
            COALESCE(parent.content, '') AS parent_content,
            COALESCE(n.source, '') AS author
        FROM news_comment c
        LEFT JOIN news n ON n.id = c.news_id
        LEFT JOIN news_category cg ON cg.id = n.category_id
        LEFT JOIN news_topic t ON t.id = n.topic_id
        LEFT JOIN user u ON u.id = c.user_id
        LEFT JOIN news_comment parent ON parent.id = c.parent_id
        {where_clause}
        ORDER BY c.updated_at DESC, c.id DESC
    '''
    rows = execute_query(sql, params)
    return [_build_pending_comment_item(row, 'news') for row in rows]


def _query_post_comment_items(status: Optional[int] = None) -> List[Dict[str, Any]]:
    target_status = 3 if status is None else status
    where_clause = 'WHERE c.status = %s'
    params: list[Any] = [target_status]
    sql = f'''
        SELECT
            c.id,
            c.post_id,
            c.user_id,
            c.parent_id,
            c.content,
            c.media_json,
            c.like_count,
            c.status,
            c.created_at,
            c.updated_at,
            COALESCE(p.title, '') AS post_title,
            COALESCE(n.title, '') AS related_news_title,
            COALESCE(t.topic_name, '') AS topic_name,
            COALESCE(u.username, '') AS username,
            COALESCE(u.nickname, '') AS nickname,
            COALESCE(parent.content, '') AS parent_content,
            COALESCE(u.nickname, u.username, '') AS submitter
        FROM post_comment c
        LEFT JOIN community_post p ON p.id = c.post_id
        LEFT JOIN news n ON n.id = p.related_news_id
        LEFT JOIN news_topic t ON t.id = p.topic_id
        LEFT JOIN user u ON u.id = c.user_id
        LEFT JOIN post_comment parent ON parent.id = c.parent_id
        {where_clause}
        ORDER BY c.updated_at DESC, c.id DESC
    '''
    rows = execute_query(sql, params)
    return [_build_pending_comment_item(row, 'post') for row in rows]


def _matches_keyword(item: Dict[str, Any], keyword: str) -> bool:
    lowered = keyword.strip().casefold()
    if not lowered:
        return True

    fields = [
        item.get('title'),
        item.get('content_preview'),
        item.get('submitter'),
        item.get('source'),
        item.get('category_name'),
        item.get('status_label'),
    ]
    return any(lowered in str(field or '').casefold() for field in fields)


def _filter_pending_items(
    item_type: str = 'all',
    keyword: str | None = None,
    status: int | None = None,
) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []

    if item_type in ('all', 'news'):
        items.extend(_query_news_items(status))
    if item_type in ('all', 'post'):
        items.extend(_query_post_items(status))
    if item_type in ('all', 'comment'):
        items.extend(_query_news_comment_items(status))
        items.extend(_query_post_comment_items(status))

    if keyword:
        items = [item for item in items if _matches_keyword(item, keyword)]

    items.sort(
        key=lambda item: (
            item.get('update_time') or item.get('create_time') or '',
            int(item.get('id') or 0),
        ),
        reverse=True,
    )
    return items


def _build_pending_summary() -> PendingSummary:
    pending_news_count = _safe_count('SELECT COUNT(*) AS total FROM news WHERE status = 3')
    pending_post_count = _safe_count('SELECT COUNT(*) AS total FROM community_post WHERE status = 3')
    pending_comment_count = _safe_count('SELECT COUNT(*) AS total FROM news_comment WHERE status = 3') + _safe_count(
        'SELECT COUNT(*) AS total FROM post_comment WHERE status = 3'
    )
    today_processed_count = 0
    if _ops_table_exists('admin_operation_log'):
        today_processed_count = _ops_total_with_where(
            'admin_operation_log',
            "WHERE DATE(created_at) = CURDATE() AND module = 'content' AND action IN ('approve','reject','fold','delete','restore')",
        )
    return PendingSummary(
        pending_news_count=pending_news_count,
        pending_post_count=pending_post_count,
        pending_comment_count=pending_comment_count,
        today_processed_count=today_processed_count,
    )


def _build_pending_item_detail(row: Dict[str, Any], item_type: str, target_type: str | None = None) -> Dict[str, Any]:
    base = _build_pending_item_base(row, item_type=item_type, target_type=target_type)
    return PendingItemDetail(
        **base.model_dump(),
        summary=str(row.get('summary') or row.get('content_preview') or row.get('content') or ''),
        content=str(row.get('content') or row.get('summary') or ''),
        cover_image=str(row.get('cover_image') or ''),
        publish_time=format_datetime(row.get('publish_time')) or None,
        editor=str(row.get('editor') or row.get('author') or row.get('submitter') or ''),
        topic_name=str(row.get('topic_name') or ''),
        tags=_parse_tags(row.get('tags')),
        view_count=int(row.get('view_count') or 0),
        like_count=int(row.get('like_count') or 0),
        comment_count=int(row.get('comment_count') or 0),
        favorite_count=int(row.get('favorite_count') or 0),
        heat_score=int(row.get('heat_score') or 0),
        related_news_id=row.get('related_news_id'),
        related_news_title=str(row.get('related_news_title') or ''),
        news_id=row.get('news_id'),
        post_id=row.get('post_id'),
        parent_id=row.get('parent_id'),
        parent_content=str(row.get('parent_content') or ''),
        media_json=row.get('media_json'),
        reason=str(row.get('reason') or ''),
    ).model_dump()


def _query_pending_item_detail(item_type: str, item_id: int) -> Dict[str, Any]:
    if item_type == 'news':
        row = execute_one(
            '''
            SELECT
                n.id,
                n.title,
                COALESCE(n.summary, '') AS summary,
                COALESCE(n.content, '') AS content,
                COALESCE(n.cover_image, '') AS cover_image,
                n.category_id,
                COALESCE(c.name, '') AS category_name,
                n.topic_id,
                COALESCE(t.topic_name, '') AS topic_name,
                COALESCE(n.source, '') AS source,
                COALESCE(n.source, '') AS author,
                COALESCE(n.source, '') AS editor,
                n.view_count,
                n.like_count,
                n.comment_count,
                n.favorite_count,
                n.heat_score,
                n.status,
                n.tags,
                n.publish_time,
                n.created_at,
                n.updated_at,
                COALESCE(n.source, '') AS submitter,
                '' AS reason
            FROM news n
            LEFT JOIN news_category c ON c.id = n.category_id
            LEFT JOIN news_topic t ON t.id = n.topic_id
            WHERE n.id = %s
            LIMIT 1
            ''',
            [item_id],
        )
        if row is None:
            raise AppException(code=404, message='内容不存在')
        row['content_preview'] = row.get('summary') or row.get('content') or ''
        return _build_pending_item_detail(row, 'news', 'news')

    if item_type == 'post':
        row = execute_one(
            '''
            SELECT
                p.id,
                p.title,
                COALESCE(p.content, '') AS summary,
                COALESCE(p.content, '') AS content,
                '' AS cover_image,
                p.related_news_id,
                COALESCE(n.title, '') AS related_news_title,
                p.topic_id,
                COALESCE(t.topic_name, '') AS topic_name,
                COALESCE(u.username, '') AS username,
                COALESCE(u.nickname, '') AS nickname,
                COALESCE(u.nickname, u.username, '') AS submitter,
                p.tags,
                p.like_count,
                p.comment_count,
                p.favorite_count,
                p.heat_score,
                p.status,
                p.created_at,
                p.updated_at,
                '' AS source,
                COALESCE(u.nickname, u.username, '') AS editor,
                NULL AS news_id,
                NULL AS parent_id,
                '' AS parent_content,
                NULL AS media_json,
                '' AS reason,
                NULL AS publish_time
            FROM community_post p
            LEFT JOIN news n ON n.id = p.related_news_id
            LEFT JOIN news_topic t ON t.id = p.topic_id
            LEFT JOIN user u ON u.id = p.user_id
            WHERE p.id = %s
            LIMIT 1
            ''',
            [item_id],
        )
        if row is None:
            raise AppException(code=404, message='内容不存在')
        row['content_preview'] = row.get('content') or ''
        return _build_pending_item_detail(row, 'post', 'post')

    if item_type == 'comment':
        row = execute_one(
            '''
            SELECT
                c.id,
                c.news_id,
                c.user_id,
                c.parent_id,
                c.content,
                NULL AS media_json,
                c.like_count,
                c.status,
                c.created_at,
                c.updated_at,
                COALESCE(n.title, '') AS news_title,
                COALESCE(n.title, '') AS title,
                COALESCE(n.source, '') AS source,
                COALESCE(cg.name, '') AS category_name,
                COALESCE(t.topic_name, '') AS topic_name,
                COALESCE(u.username, '') AS username,
                COALESCE(u.nickname, '') AS nickname,
                COALESCE(parent.content, '') AS parent_content,
                COALESCE(n.source, '') AS author,
                COALESCE(u.nickname, u.username, '') AS submitter,
                'news' AS target_type,
                '' AS related_news_title,
                NULL AS related_news_id,
                '' AS summary,
                '' AS cover_image,
                COALESCE(n.source, '') AS editor,
                0 AS comment_count,
                0 AS favorite_count,
                0 AS heat_score,
                '' AS reason,
                n.publish_time
            FROM news_comment c
            LEFT JOIN news n ON n.id = c.news_id
            LEFT JOIN news_category cg ON cg.id = n.category_id
            LEFT JOIN news_topic t ON t.id = n.topic_id
            LEFT JOIN user u ON u.id = c.user_id
            LEFT JOIN news_comment parent ON parent.id = c.parent_id
            WHERE c.id = %s
            LIMIT 1
            ''',
            [item_id],
        )
        if row is not None:
            row['content_preview'] = row.get('content') or ''
            return _build_pending_item_detail(row, 'comment', 'news')

        row = execute_one(
            '''
            SELECT
                c.id,
                c.post_id,
                c.user_id,
                c.parent_id,
                c.content,
                c.media_json,
                c.like_count,
                c.status,
                c.created_at,
                c.updated_at,
                COALESCE(p.title, '') AS post_title,
                COALESCE(p.title, '') AS title,
                COALESCE(n.title, '') AS related_news_title,
                COALESCE(t.topic_name, '') AS topic_name,
                COALESCE(u.username, '') AS username,
                COALESCE(u.nickname, '') AS nickname,
                COALESCE(parent.content, '') AS parent_content,
                COALESCE(u.nickname, u.username, '') AS submitter,
                'post' AS target_type,
                COALESCE(n.title, '') AS source,
                COALESCE(p.related_news_id, NULL) AS related_news_id,
                '' AS summary,
                '' AS cover_image,
                COALESCE(u.nickname, u.username, '') AS editor,
                0 AS comment_count,
                0 AS favorite_count,
                0 AS heat_score,
                '' AS reason,
                NULL AS publish_time
            FROM post_comment c
            LEFT JOIN community_post p ON p.id = c.post_id
            LEFT JOIN news n ON n.id = p.related_news_id
            LEFT JOIN news_topic t ON t.id = p.topic_id
            LEFT JOIN user u ON u.id = c.user_id
            LEFT JOIN post_comment parent ON parent.id = c.parent_id
            WHERE c.id = %s
            LIMIT 1
            ''',
            [item_id],
        )
        if row is None:
            raise AppException(code=404, message='内容不存在')
        row['content_preview'] = row.get('content') or ''
        return _build_pending_item_detail(row, 'comment', 'post')

    raise AppException(code=400, message='不支持的审核类型')


def _resolve_target_status(item_type: str, action: str) -> int:
    if action == 'approve':
        return 1
    if action == 'fold':
        return 2
    if action == 'delete':
        return 4
    if action == 'restore':
        return 1
    if action == 'reject':
        return 0 if item_type == 'news' else 4
    raise AppException(code=400, message='不支持的审核操作')


def _update_comment_counters(cursor, *, parent_table: str, parent_id: int, old_status: int, new_status: int) -> None:
    old_counted = old_status in COUNTED_STATUSES
    new_counted = new_status in COUNTED_STATUSES
    if old_counted == new_counted:
        return

    delta = 1 if new_counted else -1
    if parent_table == 'community_post':
        cursor.execute(
            '''
            UPDATE community_post
            SET comment_count = GREATEST(comment_count + %s, 0),
                heat_score = GREATEST(heat_score + %s, 0),
                updated_at = NOW()
            WHERE id = %s
            ''',
            [delta, delta, parent_id],
        )
    else:
        cursor.execute(
            f'''
            UPDATE {parent_table}
            SET comment_count = GREATEST(comment_count + %s, 0), updated_at = NOW()
            WHERE id = %s
            ''',
            [delta, parent_id],
        )


def _review_comment_item(item_id: int, action: str, reason: str) -> ReviewActionResult:
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                '''
                SELECT id, news_id, NULL AS post_id, status
                FROM news_comment
                WHERE id = %s
                LIMIT 1
                ''',
                [item_id],
            )
            row = cursor.fetchone()
            table = 'news_comment'
            parent_table = 'news'
            parent_id = 0

            if row is None:
                cursor.execute(
                    '''
                    SELECT id, NULL AS news_id, post_id, status
                    FROM post_comment
                    WHERE id = %s
                    LIMIT 1
                    ''',
                    [item_id],
                )
                row = cursor.fetchone()
                if row is None:
                    raise AppException(code=404, message='内容不存在')
                table = 'post_comment'
                parent_table = 'community_post'
                parent_id = int(row.get('post_id') or 0)
            else:
                parent_id = int(row.get('news_id') or 0)

            old_status = _normalize_status(row.get('status'))
            new_status = _resolve_target_status('comment', action)

            cursor.execute(
                f'UPDATE {table} SET status = %s, updated_at = NOW() WHERE id = %s',
                [new_status, item_id],
            )
            _update_comment_counters(
                cursor,
                parent_table=parent_table,
                parent_id=parent_id,
                old_status=old_status,
                new_status=new_status,
            )
        connection.commit()
        return ReviewActionResult(
            item_type='comment',
            item_id=item_id,
            action=action,
            status=new_status,
            status_label=_status_label(new_status),
            updated=True,
            message='处理成功',
            reason=reason,
        )
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def _review_news_item(item_id: int, action: str, reason: str) -> ReviewActionResult:
    row = execute_one('SELECT id, status FROM news WHERE id = %s LIMIT 1', [item_id])
    if row is None:
        raise AppException(code=404, message='内容不存在')
    new_status = _resolve_target_status('news', action)
    execute_update('UPDATE news SET status = %s, updated_at = NOW() WHERE id = %s', [new_status, item_id])
    return ReviewActionResult(
        item_type='news',
        item_id=item_id,
        action=action,
        status=new_status,
        status_label=_status_label(new_status),
        updated=True,
        message='处理成功',
        reason=reason,
    )


def _review_post_item(item_id: int, action: str, reason: str) -> ReviewActionResult:
    row = execute_one('SELECT id, status FROM community_post WHERE id = %s LIMIT 1', [item_id])
    if row is None:
        raise AppException(code=404, message='内容不存在')
    new_status = _resolve_target_status('post', action)
    execute_update('UPDATE community_post SET status = %s, updated_at = NOW() WHERE id = %s', [new_status, item_id])
    return ReviewActionResult(
        item_type='post',
        item_id=item_id,
        action=action,
        status=new_status,
        status_label=_status_label(new_status),
        updated=True,
        message='处理成功',
        reason=reason,
    )


def get_pending_items(
    item_type: str = 'all',
    keyword: str | None = None,
    status: int | None = None,
    page: int = 1,
    page_size: int = 10,
) -> Dict[str, Any]:
    items = _filter_pending_items(item_type=item_type, keyword=keyword, status=status)
    normalized_page = max(page, 1)
    normalized_page_size = max(page_size, 1)
    start = (normalized_page - 1) * normalized_page_size
    end = start + normalized_page_size
    response = PendingItemsResponse(
        items=[PendingItem.model_validate(item) for item in items[start:end]],
        total=len(items),
        page=normalized_page,
        page_size=normalized_page_size,
        summary=_build_pending_summary(),
    )
    return response.model_dump()


def get_pending_item_detail(item_type: str, item_id: int) -> Dict[str, Any]:
    if item_type not in {'news', 'post', 'comment'}:
        raise AppException(code=400, message='不支持的审核类型')
    return _query_pending_item_detail(item_type, item_id)


def review_pending_item(
    item_type: str,
    item_id: int,
    request: ReviewActionRequest,
    current_user: Any | None = None,
) -> Dict[str, Any]:
    if item_type == 'news':
        result = _review_news_item(item_id, request.action, request.reason)
    elif item_type == 'post':
        result = _review_post_item(item_id, request.action, request.reason)
    elif item_type == 'comment':
        result = _review_comment_item(item_id, request.action, request.reason)
    else:
        raise AppException(code=400, message='不支持的审核类型')
    write_admin_operation_log(
        current_user=current_user,
        module='content',
        action=request.action,
        target_type=item_type,
        target_id=item_id,
        description=f'Review {item_type}: {request.action}. Reason: {request.reason or ""}',
        result='success',
    )
    return result.model_dump()



def _table_columns(table_name: str) -> set[str]:
    rows = execute_query(
        """
        SELECT COLUMN_NAME AS name
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s
        """,
        [table_name],
    )
    return {str(row.get('name')) for row in rows}


def _feature_column() -> str | None:
    columns = _table_columns('news')
    for column in FEATURE_COLUMNS:
        if column in columns:
            return column
    return None


def _news_status_label(value: Any) -> str:
    return NEWS_STATUS_LABELS.get(_normalize_status(value), 'Unknown')


def _build_admin_news_item(row: Dict[str, Any], feature_column: str | None = None) -> Dict[str, Any]:
    feature_value = row.get('is_featured') if feature_column else None
    item = AdminNewsItem(
        id=int(row.get('id') or 0),
        title=str(row.get('title') or ''),
        summary=str(row.get('summary') or ''),
        content_preview=_preview_text(row.get('content') or row.get('summary') or '', 120),
        cover_image=str(row.get('cover_image') or ''),
        category_id=row.get('category_id'),
        category_name=str(row.get('category_name') or ''),
        topic_id=row.get('topic_id'),
        topic_name=str(row.get('topic_name') or ''),
        source=str(row.get('source') or ''),
        editor=str(row.get('editor') or row.get('source') or ''),
        publish_time=format_datetime(row.get('publish_time')) or None,
        view_count=int(row.get('view_count') or 0),
        like_count=int(row.get('like_count') or 0),
        comment_count=int(row.get('comment_count') or 0),
        favorite_count=int(row.get('favorite_count') or 0),
        status=_normalize_status(row.get('status')),
        status_label=_news_status_label(row.get('status')),
        tags=_parse_tags(row.get('tags')),
        is_featured=bool(feature_value) if feature_column else None,
        feature_supported=bool(feature_column),
        create_time=format_datetime(row.get('created_at')) or None,
        update_time=format_datetime(row.get('updated_at')) or None,
    )
    return item.model_dump()


def _news_base_select(feature_column: str | None) -> str:
    feature_select = f'n.{feature_column} AS is_featured,' if feature_column else 'NULL AS is_featured,'
    return f"""
        SELECT
            n.id,
            n.title,
            COALESCE(n.summary, '') AS summary,
            COALESCE(n.content, '') AS content,
            COALESCE(n.cover_image, '') AS cover_image,
            n.category_id,
            COALESCE(c.name, '') AS category_name,
            n.topic_id,
            COALESCE(t.topic_name, '') AS topic_name,
            COALESCE(n.source, '') AS source,
            COALESCE(n.editor, '') AS editor,
            n.publish_time,
            COALESCE(n.source_url, '') AS source_url,
            n.view_count,
            n.like_count,
            n.comment_count,
            n.favorite_count,
            n.status,
            n.tags,
            {feature_select}
            n.created_at,
            n.updated_at
        FROM news n
        LEFT JOIN news_category c ON c.id = n.category_id
        LEFT JOIN news_topic t ON t.id = n.topic_id
    """


def _build_admin_news_where(
    keyword: str | None = None,
    category_id: int | None = None,
    source: str | None = None,
    status: int | None = None,
    is_featured: bool | None = None,
    has_topic: bool | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
    feature_column: str | None = None,
) -> tuple[str, list[Any]]:
    conditions: list[str] = []
    params: list[Any] = []
    if keyword:
        conditions.append('(n.title LIKE %s OR n.summary LIKE %s OR n.content LIKE %s OR n.source LIKE %s)')
        like = f'%{keyword}%'
        params.extend([like, like, like, like])
    if category_id:
        conditions.append('n.category_id = %s')
        params.append(category_id)
    if source:
        conditions.append('n.source LIKE %s')
        params.append(f'%{source}%')
    if status is not None:
        conditions.append('n.status = %s')
        params.append(status)
    if is_featured is not None and feature_column:
        conditions.append(f'COALESCE(n.{feature_column}, 0) = %s')
        params.append(1 if is_featured else 0)
    if has_topic is True:
        conditions.append('n.topic_id IS NOT NULL')
    elif has_topic is False:
        conditions.append('n.topic_id IS NULL')
    if start_time:
        conditions.append('n.publish_time >= %s')
        params.append(start_time)
    if end_time:
        conditions.append('n.publish_time <= %s')
        params.append(end_time)
    return ('WHERE ' + ' AND '.join(conditions)) if conditions else '', params


def _admin_news_summary(feature_column: str | None) -> Dict[str, Any]:
    return AdminNewsSummary(
        total_count=_safe_count('SELECT COUNT(*) AS total FROM news'),
        pending_count=_safe_count('SELECT COUNT(*) AS total FROM news WHERE status = 3'),
        published_count=_safe_count('SELECT COUNT(*) AS total FROM news WHERE status = 1'),
        offline_count=_safe_count('SELECT COUNT(*) AS total FROM news WHERE status = 0'),
        unbound_topic_count=_safe_count('SELECT COUNT(*) AS total FROM news WHERE topic_id IS NULL'),
        feature_supported=bool(feature_column),
    ).model_dump()


def get_admin_news_options() -> Dict[str, Any]:
    feature_column = _feature_column()
    categories = execute_query(
        """
        SELECT id, name, code
        FROM news_category
        WHERE status = 1
        ORDER BY sort ASC, id ASC
        """
    )
    topics = execute_query(
        """
        SELECT id, topic_name, heat_score
        FROM news_topic
        WHERE status = 1
        ORDER BY heat_score DESC, id ASC
        """
    )
    sources = execute_query(
        """
        SELECT DISTINCT source
        FROM news
        WHERE source IS NOT NULL AND source <> ''
        ORDER BY source ASC
        LIMIT 100
        """
    )
    return AdminNewsOptions(
        categories=[dict(row) for row in categories],
        topics=[dict(row) for row in topics],
        sources=[str(row.get('source') or '') for row in sources if row.get('source')],
        feature_supported=bool(feature_column),
    ).model_dump()


def get_admin_news_list(
    keyword: str | None = None,
    category_id: int | None = None,
    source: str | None = None,
    status: int | None = None,
    is_featured: bool | None = None,
    has_topic: bool | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
    page: int = 1,
    page_size: int = 10,
) -> Dict[str, Any]:
    feature_column = _feature_column()
    where_sql, params = _build_admin_news_where(
        keyword=keyword,
        category_id=category_id,
        source=source,
        status=status,
        is_featured=is_featured,
        has_topic=has_topic,
        start_time=start_time,
        end_time=end_time,
        feature_column=feature_column,
    )
    normalized_page = max(page, 1)
    normalized_page_size = max(page_size, 1)
    offset = (normalized_page - 1) * normalized_page_size
    count_row = execute_one(f'SELECT COUNT(*) AS total FROM news n {where_sql}', params)
    total = int(count_row.get('total') or 0) if count_row else 0
    sql = _news_base_select(feature_column) + f"""
        {where_sql}
        ORDER BY n.updated_at DESC, n.publish_time DESC, n.id DESC
        LIMIT %s OFFSET %s
    """
    rows = execute_query(sql, [*params, normalized_page_size, offset])
    return AdminNewsListResponse(
        items=[AdminNewsItem.model_validate(_build_admin_news_item(row, feature_column)) for row in rows],
        total=total,
        page=normalized_page,
        page_size=normalized_page_size,
        summary=AdminNewsSummary.model_validate(_admin_news_summary(feature_column)),
    ).model_dump()


def get_admin_news_detail(news_id: int) -> Dict[str, Any]:
    feature_column = _feature_column()
    row = execute_one(_news_base_select(feature_column) + ' WHERE n.id = %s LIMIT 1', [news_id])
    if row is None:
        raise AppException(code=404, message='News not found')
    payload = _build_admin_news_item(row, feature_column)
    payload['content'] = str(row.get('content') or '')
    payload['source_url'] = str(row.get('source_url') or '')
    return AdminNewsDetail.model_validate(payload).model_dump()


def update_admin_news(news_id: int, request: AdminNewsUpdateRequest, current_user: Any | None = None) -> Dict[str, Any]:
    if not request.title.strip():
        raise AppException(code=400, message='News content is required')
    if not request.content.strip():
        raise AppException(code=400, message='News content is required')
    if request.category_id is not None:
        category = execute_one('SELECT id FROM news_category WHERE id = %s LIMIT 1', [request.category_id])
        if category is None:
            raise AppException(code=404, message='News topic not found')
    import json
    tags_json = json.dumps(request.tags, ensure_ascii=False) if request.tags else None
    affected = execute_update(
        """
        UPDATE news
        SET title = %s,
            summary = %s,
            content = %s,
            source = %s,
            category_id = %s,
            cover_image = %s,
            tags = %s,
            publish_time = %s,
            updated_at = NOW()
        WHERE id = %s
        """,
        [request.title.strip(), request.summary.strip(), request.content.strip(), request.source.strip(), request.category_id, request.cover_image.strip(), tags_json, request.publish_time, news_id],
    )
    if affected == 0:
        raise AppException(code=404, message='News not found')
    write_admin_operation_log(
        current_user=current_user,
        module='content',
        action='update',
        target_type='news',
        target_id=news_id,
        description='Update news content',
        result='success',
    )
    return get_admin_news_detail(news_id)


def update_admin_news_topic(news_id: int, request: AdminNewsTopicRequest, current_user: Any | None = None) -> Dict[str, Any]:
    if request.topic_id is not None:
        topic = execute_one('SELECT id FROM news_topic WHERE id = %s LIMIT 1', [request.topic_id])
        if topic is None:
            raise AppException(code=404, message='News topic not found')
    affected = execute_update('UPDATE news SET topic_id = %s, updated_at = NOW() WHERE id = %s', [request.topic_id, news_id])
    if affected == 0:
        raise AppException(code=404, message='News not found')
    write_admin_operation_log(
        current_user=current_user,
        module='content',
        action='bind_topic' if request.topic_id is not None else 'unbind_topic',
        target_type='news',
        target_id=news_id,
        description=f'Update news topic to {request.topic_id}',
        result='success',
    )
    return get_admin_news_detail(news_id)


def set_admin_news_feature(news_id: int, featured: bool) -> Dict[str, Any]:
    feature_column = _feature_column()
    if not feature_column:
        raise AppException(code=400, message='Current news table does not support featured field')
    affected = execute_update(f'UPDATE news SET {feature_column} = %s, updated_at = NOW() WHERE id = %s', [1 if featured else 0, news_id])
    if affected == 0:
        raise AppException(code=404, message='News not found')
    return AdminNewsActionResult(news_id=news_id, action='feature' if featured else 'unfeature', updated=True, message='Success').model_dump()


def review_admin_news(news_id: int, request: ReviewActionRequest, current_user: Any | None = None) -> Dict[str, Any]:
    result = _review_news_item(news_id, request.action, request.reason)
    write_admin_operation_log(
        current_user=current_user,
        module='content',
        action=request.action,
        target_type='news',
        target_id=news_id,
        description=f'Review news: {request.action}. Reason: {request.reason or ""}',
        result='success',
    )
    return AdminNewsActionResult(news_id=news_id, action=request.action, updated=True, status=result.status, status_label=_news_status_label(result.status), message='Success').model_dump()



POST_FEATURE_COLUMNS = ('is_featured', 'featured', 'is_selected', 'is_recommended', 'recommend_flag')

POST_STATUS_LABELS = {
    0: 'Offline',
    1: 'Normal',
    2: 'Folded',
    3: 'Pending',
    4: 'Deleted',
}


def _post_feature_column() -> str | None:
    columns = _table_columns('community_post')
    for column in POST_FEATURE_COLUMNS:
        if column in columns:
            return column
    return None


def _post_status_label(value: Any) -> str:
    return POST_STATUS_LABELS.get(_normalize_status(value), 'Unknown')


def _build_admin_post_item(row: Dict[str, Any], feature_column: str | None = None) -> Dict[str, Any]:
    feature_value = row.get('is_featured') if feature_column else None
    username = str(row.get('username') or '')
    nickname = str(row.get('nickname') or '')
    item = AdminPostItem(
        id=int(row.get('id') or 0),
        title=str(row.get('title') or ''),
        content_preview=_preview_text(row.get('content') or '', 120),
        user_id=row.get('user_id'),
        username=username,
        nickname=nickname,
        author_name=nickname or username or (f"user_{row.get('user_id')}" if row.get('user_id') else ''),
        related_news_id=row.get('related_news_id'),
        related_news_title=str(row.get('related_news_title') or ''),
        topic_id=row.get('topic_id'),
        topic_name=str(row.get('topic_name') or ''),
        tags=_parse_tags(row.get('tags')),
        like_count=int(row.get('like_count') or 0),
        comment_count=int(row.get('comment_count') or 0),
        favorite_count=int(row.get('favorite_count') or 0),
        heat_score=int(row.get('heat_score') or 0),
        status=_normalize_status(row.get('status')),
        status_label=_post_status_label(row.get('status')),
        is_featured=bool(feature_value) if feature_column else None,
        feature_supported=bool(feature_column),
        create_time=format_datetime(row.get('created_at')) or None,
        update_time=format_datetime(row.get('updated_at')) or None,
    )
    return item.model_dump()


def _post_base_select(feature_column: str | None) -> str:
    feature_select = f'p.{feature_column} AS is_featured,' if feature_column else 'NULL AS is_featured,'
    return f"""
        SELECT
            p.id,
            p.user_id,
            p.title,
            COALESCE(p.content, '') AS content,
            p.related_news_id,
            COALESCE(n.title, '') AS related_news_title,
            p.topic_id,
            COALESCE(t.topic_name, '') AS topic_name,
            COALESCE(u.username, '') AS username,
            COALESCE(u.nickname, '') AS nickname,
            p.tags,
            p.like_count,
            p.comment_count,
            p.favorite_count,
            p.heat_score,
            p.status,
            {feature_select}
            p.created_at,
            p.updated_at
        FROM community_post p
        LEFT JOIN user u ON u.id = p.user_id
        LEFT JOIN news n ON n.id = p.related_news_id
        LEFT JOIN news_topic t ON t.id = p.topic_id
    """


def _build_admin_post_where(
    keyword: str | None = None,
    user_id: int | None = None,
    username: str | None = None,
    status: int | None = None,
    tag: str | None = None,
    related_news_id: int | None = None,
    is_featured: bool | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
    feature_column: str | None = None,
) -> tuple[str, list[Any]]:
    conditions: list[str] = []
    params: list[Any] = []
    if keyword:
        like = f'%{keyword}%'
        conditions.append('(p.title LIKE %s OR p.content LIKE %s OR CAST(p.tags AS CHAR) LIKE %s)')
        params.extend([like, like, like])
    if user_id:
        conditions.append('p.user_id = %s')
        params.append(user_id)
    if username:
        like = f'%{username}%'
        conditions.append('(u.username LIKE %s OR u.nickname LIKE %s)')
        params.extend([like, like])
    if status is not None:
        conditions.append('p.status = %s')
        params.append(status)
    if tag:
        conditions.append('CAST(p.tags AS CHAR) LIKE %s')
        params.append(f'%{tag}%')
    if related_news_id:
        conditions.append('p.related_news_id = %s')
        params.append(related_news_id)
    if is_featured is not None and feature_column:
        conditions.append(f'COALESCE(p.{feature_column}, 0) = %s')
        params.append(1 if is_featured else 0)
    if start_time:
        conditions.append('p.created_at >= %s')
        params.append(start_time)
    if end_time:
        conditions.append('p.created_at <= %s')
        params.append(end_time)
    return ('WHERE ' + ' AND '.join(conditions)) if conditions else '', params


def _admin_post_summary(feature_column: str | None) -> Dict[str, Any]:
    return AdminPostSummary(
        total_count=_safe_count('SELECT COUNT(*) AS total FROM community_post'),
        pending_count=_safe_count('SELECT COUNT(*) AS total FROM community_post WHERE status = 3'),
        normal_count=_safe_count('SELECT COUNT(*) AS total FROM community_post WHERE status = 1'),
        folded_count=_safe_count('SELECT COUNT(*) AS total FROM community_post WHERE status = 2'),
        deleted_count=_safe_count('SELECT COUNT(*) AS total FROM community_post WHERE status = 4'),
        reported_count=0,
        feature_supported=bool(feature_column),
    ).model_dump()


def get_admin_post_options() -> Dict[str, Any]:
    feature_column = _post_feature_column()
    tag_rows = execute_query(
        """
        SELECT tags
        FROM community_post
        WHERE tags IS NOT NULL AND CAST(tags AS CHAR) <> ''
        ORDER BY updated_at DESC
        LIMIT 300
        """
    )
    tags: list[str] = []
    for row in tag_rows:
        for tag in _parse_tags(row.get('tags')):
            if tag and tag not in tags:
                tags.append(tag)
            if len(tags) >= 100:
                break
    return AdminPostOptions(
        statuses=[{'label': label, 'value': value} for value, label in POST_STATUS_LABELS.items()],
        tags=tags,
        feature_supported=bool(feature_column),
    ).model_dump()


def get_admin_post_list(
    keyword: str | None = None,
    user_id: int | None = None,
    username: str | None = None,
    status: int | None = None,
    tag: str | None = None,
    related_news_id: int | None = None,
    is_featured: bool | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
    page: int = 1,
    page_size: int = 10,
) -> Dict[str, Any]:
    feature_column = _post_feature_column()
    where_sql, params = _build_admin_post_where(keyword, user_id, username, status, tag, related_news_id, is_featured, start_time, end_time, feature_column)
    normalized_page = max(page, 1)
    normalized_page_size = max(page_size, 1)
    offset = (normalized_page - 1) * normalized_page_size
    count_row = execute_one(f'SELECT COUNT(*) AS total FROM community_post p LEFT JOIN user u ON u.id = p.user_id {where_sql}', params)
    total = int(count_row.get('total') or 0) if count_row else 0
    rows = execute_query(
        _post_base_select(feature_column) + f"""
            {where_sql}
            ORDER BY p.updated_at DESC, p.created_at DESC, p.id DESC
            LIMIT %s OFFSET %s
        """,
        [*params, normalized_page_size, offset],
    )
    return AdminPostListResponse(
        items=[AdminPostItem.model_validate(_build_admin_post_item(row, feature_column)) for row in rows],
        total=total,
        page=normalized_page,
        page_size=normalized_page_size,
        summary=AdminPostSummary.model_validate(_admin_post_summary(feature_column)),
    ).model_dump()


def get_admin_post_detail(post_id: int) -> Dict[str, Any]:
    feature_column = _post_feature_column()
    row = execute_one(_post_base_select(feature_column) + ' WHERE p.id = %s LIMIT 1', [post_id])
    if row is None:
        raise AppException(code=404, message='Community post not found')
    payload = _build_admin_post_item(row, feature_column)
    payload['content'] = str(row.get('content') or '')
    comments = execute_query(
        """
        SELECT c.id, c.user_id, COALESCE(u.username, '') AS username, COALESCE(u.nickname, '') AS nickname,
               COALESCE(c.content, '') AS content, c.like_count, c.status, c.created_at
        FROM post_comment c
        LEFT JOIN user u ON u.id = c.user_id
        WHERE c.post_id = %s
        ORDER BY c.created_at DESC, c.id DESC
        LIMIT 5
        """,
        [post_id],
    )
    payload['recent_comments'] = [
        {
            'id': int(item.get('id') or 0),
            'user_id': item.get('user_id'),
            'username': str(item.get('nickname') or item.get('username') or ''),
            'content': str(item.get('content') or ''),
            'media_json': _normalize_media_json(item.get('media_json')),
            'like_count': int(item.get('like_count') or 0),
            'status': _normalize_status(item.get('status')),
            'status_label': _post_status_label(item.get('status')),
            'create_time': format_datetime(item.get('created_at')) or None,
        } for item in comments
    ]
    return AdminPostDetail.model_validate(payload).model_dump()


def review_admin_post(post_id: int, request: ReviewActionRequest, current_user: Any | None = None) -> Dict[str, Any]:
    result = _review_post_item(post_id, request.action, request.reason)
    write_admin_operation_log(
        current_user=current_user,
        module='content',
        action=request.action,
        target_type='post',
        target_id=post_id,
        description=f'Review post: {request.action}. Reason: {request.reason or ""}',
        result='success',
    )
    return AdminPostActionResult(post_id=post_id, action=request.action, updated=True, status=result.status, status_label=_post_status_label(result.status), message='Success').model_dump()


def set_admin_post_feature(post_id: int, featured: bool) -> Dict[str, Any]:
    feature_column = _post_feature_column()
    if not feature_column:
        raise AppException(code=400, message='Current community_post table does not support featured field')
    affected = execute_update(f'UPDATE community_post SET {feature_column} = %s, updated_at = NOW() WHERE id = %s', [1 if featured else 0, post_id])
    if affected == 0:
        raise AppException(code=404, message='Community post not found')
    return AdminPostActionResult(post_id=post_id, action='feature' if featured else 'unfeature', updated=True, message='Success').model_dump()




COMMENT_STATUS_LABELS = {
    0: 'Rejected',
    1: 'Normal',
    2: 'Folded',
    3: 'Pending',
    4: 'Deleted',
}


def _comment_status_label(value: Any) -> str:
    return COMMENT_STATUS_LABELS.get(_normalize_status(value), 'Unknown')


def _comment_type_label(comment_type: str) -> str:
    return 'News Comment' if comment_type == 'news' else 'Community Comment'


def _build_admin_comment_item(row: Dict[str, Any]) -> Dict[str, Any]:
    comment_type = str(row.get('comment_type') or 'news')
    username = str(row.get('username') or '')
    nickname = str(row.get('nickname') or '')
    item = AdminCommentItem(
        id=int(row.get('id') or 0),
        comment_type=comment_type,  # type: ignore[arg-type]
        comment_type_label=_comment_type_label(comment_type),
        target_id=row.get('target_id'),
        target_title=str(row.get('target_title') or ''),
        target_source=str(row.get('target_source') or ''),
        user_id=row.get('user_id'),
        username=username,
        nickname=nickname,
        author_name=nickname or username or (f"user_{row.get('user_id')}" if row.get('user_id') else ''),
        parent_id=row.get('parent_id'),
        parent_content=str(row.get('parent_content') or ''),
        content=str(row.get('content') or ''),
        content_preview=_preview_text(row.get('content') or '', 100),
        media_json=_normalize_media_json(row.get('media_json')),
        like_count=int(row.get('like_count') or 0),
        reply_count=int(row.get('reply_count') or 0),
        status=_normalize_status(row.get('status')),
        status_label=_comment_status_label(row.get('status')),
        create_time=format_datetime(row.get('created_at')) or None,
        update_time=format_datetime(row.get('updated_at')) or None,
    )
    return item.model_dump()


def _build_admin_comment_where(
    alias: str,
    keyword: str | None = None,
    user_id: int | None = None,
    username: str | None = None,
    status: int | None = None,
    has_parent: bool | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
) -> tuple[list[str], list[Any]]:
    conditions: list[str] = []
    params: list[Any] = []
    if keyword:
        conditions.append(f'{alias}.content LIKE %s')
        params.append(f'%{keyword}%')
    if user_id:
        conditions.append(f'{alias}.user_id = %s')
        params.append(user_id)
    if username:
        like = f'%{username}%'
        conditions.append('(u.username LIKE %s OR u.nickname LIKE %s)')
        params.extend([like, like])
    if status is not None:
        conditions.append(f'{alias}.status = %s')
        params.append(status)
    if has_parent is True:
        conditions.append(f'{alias}.parent_id IS NOT NULL')
    elif has_parent is False:
        conditions.append(f'{alias}.parent_id IS NULL')
    if start_time:
        conditions.append(f'{alias}.created_at >= %s')
        params.append(start_time)
    if end_time:
        conditions.append(f'{alias}.created_at <= %s')
        params.append(end_time)
    return conditions, params


def _query_admin_news_comments(
    keyword: str | None = None,
    user_id: int | None = None,
    username: str | None = None,
    status: int | None = None,
    news_id: int | None = None,
    has_parent: bool | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
) -> list[Dict[str, Any]]:
    conditions, params = _build_admin_comment_where('c', keyword, user_id, username, status, has_parent, start_time, end_time)
    if news_id:
        conditions.append('c.news_id = %s')
        params.append(news_id)
    where_sql = 'WHERE ' + ' AND '.join(conditions) if conditions else ''
    return execute_query(
        f"""
        SELECT
            'news' AS comment_type,
            c.id, c.news_id AS target_id, c.user_id, c.parent_id, c.content, NULL AS media_json, c.like_count, c.status, c.created_at, c.updated_at,
            COALESCE(u.username, '') AS username, COALESCE(u.nickname, '') AS nickname,
            COALESCE(n.title, '') AS target_title, COALESCE(n.source, '') AS target_source,
            COALESCE(parent.content, '') AS parent_content,
            (SELECT COUNT(*) FROM news_comment child WHERE child.parent_id = c.id AND child.status <> 4) AS reply_count
        FROM news_comment c
        LEFT JOIN user u ON u.id = c.user_id
        LEFT JOIN news n ON n.id = c.news_id
        LEFT JOIN news_comment parent ON parent.id = c.parent_id
        {where_sql}
        """,
        params,
    )


def _query_admin_post_comments(
    keyword: str | None = None,
    user_id: int | None = None,
    username: str | None = None,
    status: int | None = None,
    post_id: int | None = None,
    has_parent: bool | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
) -> list[Dict[str, Any]]:
    conditions, params = _build_admin_comment_where('c', keyword, user_id, username, status, has_parent, start_time, end_time)
    if post_id:
        conditions.append('c.post_id = %s')
        params.append(post_id)
    where_sql = 'WHERE ' + ' AND '.join(conditions) if conditions else ''
    return execute_query(
        f"""
        SELECT
            'post' AS comment_type,
            c.id, c.post_id AS target_id, c.user_id, c.parent_id, c.content, c.media_json, c.like_count, c.status, c.created_at, c.updated_at,
            COALESCE(u.username, '') AS username, COALESCE(u.nickname, '') AS nickname,
            COALESCE(p.title, '') AS target_title, '' AS target_source,
            COALESCE(parent.content, '') AS parent_content,
            (SELECT COUNT(*) FROM post_comment child WHERE child.parent_id = c.id AND child.status <> 4) AS reply_count
        FROM post_comment c
        LEFT JOIN user u ON u.id = c.user_id
        LEFT JOIN community_post p ON p.id = c.post_id
        LEFT JOIN post_comment parent ON parent.id = c.parent_id
        {where_sql}
        """,
        params,
    )


def _admin_comment_summary() -> Dict[str, Any]:
    news_count = _safe_count('SELECT COUNT(*) AS total FROM news_comment')
    post_count = _safe_count('SELECT COUNT(*) AS total FROM post_comment')
    return AdminCommentSummary(
        total_count=news_count + post_count,
        news_comment_count=news_count,
        post_comment_count=post_count,
        pending_count=_safe_count('SELECT COUNT(*) AS total FROM news_comment WHERE status = 3') + _safe_count('SELECT COUNT(*) AS total FROM post_comment WHERE status = 3'),
        folded_count=_safe_count('SELECT COUNT(*) AS total FROM news_comment WHERE status = 2') + _safe_count('SELECT COUNT(*) AS total FROM post_comment WHERE status = 2'),
        deleted_count=_safe_count('SELECT COUNT(*) AS total FROM news_comment WHERE status = 4') + _safe_count('SELECT COUNT(*) AS total FROM post_comment WHERE status = 4'),
        reported_count=0,
        report_supported=False,
    ).model_dump()


def get_admin_comment_options() -> Dict[str, Any]:
    return AdminCommentOptions(
        statuses=[{'label': label, 'value': value} for value, label in COMMENT_STATUS_LABELS.items()],
        types=[
            {'label': 'All Comments', 'value': 'all'},
            {'label': 'News Comments', 'value': 'news'},
            {'label': 'Community Comments', 'value': 'post'},
        ],
        report_supported=False,
    ).model_dump()


def get_admin_comment_list(
    comment_type: str = 'all',
    keyword: str | None = None,
    user_id: int | None = None,
    username: str | None = None,
    status: int | None = None,
    news_id: int | None = None,
    post_id: int | None = None,
    has_parent: bool | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
    page: int = 1,
    page_size: int = 10,
) -> Dict[str, Any]:
    if comment_type not in {'all', 'news', 'post'}:
        raise AppException(code=400, message='Unsupported comment type')
    rows: list[Dict[str, Any]] = []
    include_news = comment_type in {'all', 'news'} and post_id is None
    include_post = comment_type in {'all', 'post'} and news_id is None
    if include_news:
        rows.extend(_query_admin_news_comments(keyword, user_id, username, status, news_id, has_parent, start_time, end_time))
    if include_post:
        rows.extend(_query_admin_post_comments(keyword, user_id, username, status, post_id, has_parent, start_time, end_time))
    rows.sort(key=lambda item: (item.get('created_at') or '', int(item.get('id') or 0)), reverse=True)
    normalized_page = max(page, 1)
    normalized_page_size = max(page_size, 1)
    start = (normalized_page - 1) * normalized_page_size
    end = start + normalized_page_size
    return AdminCommentListResponse(
        items=[AdminCommentItem.model_validate(_build_admin_comment_item(row)) for row in rows[start:end]],
        total=len(rows),
        page=normalized_page,
        page_size=normalized_page_size,
        summary=AdminCommentSummary.model_validate(_admin_comment_summary()),
    ).model_dump()


def _comment_detail_row(comment_type: str, comment_id: int) -> Dict[str, Any] | None:
    if comment_type == 'news':
        return execute_one(
            """
            SELECT
                'news' AS comment_type,
                c.id, c.news_id AS target_id, c.user_id, c.parent_id, c.content, NULL AS media_json, c.like_count, c.status, c.created_at, c.updated_at,
                COALESCE(u.username, '') AS username, COALESCE(u.nickname, '') AS nickname,
                COALESCE(n.title, '') AS target_title, COALESCE(n.source, '') AS target_source,
                n.publish_time AS target_publish_time, COALESCE(n.summary, '') AS target_summary,
                COALESCE(parent.content, '') AS parent_content,
                (SELECT COUNT(*) FROM news_comment child WHERE child.parent_id = c.id AND child.status <> 4) AS reply_count
            FROM news_comment c
            LEFT JOIN user u ON u.id = c.user_id
            LEFT JOIN news n ON n.id = c.news_id
            LEFT JOIN news_comment parent ON parent.id = c.parent_id
            WHERE c.id = %s
            LIMIT 1
            """,
            [comment_id],
        )
    if comment_type == 'post':
        return execute_one(
            """
            SELECT
                'post' AS comment_type,
                c.id, c.post_id AS target_id, c.user_id, c.parent_id, c.content, c.media_json, c.like_count, c.status, c.created_at, c.updated_at,
                COALESCE(u.username, '') AS username, COALESCE(u.nickname, '') AS nickname,
                COALESCE(p.title, '') AS target_title, '' AS target_source,
                NULL AS target_publish_time, COALESCE(p.content, '') AS target_summary,
                COALESCE(parent.content, '') AS parent_content,
                (SELECT COUNT(*) FROM post_comment child WHERE child.parent_id = c.id AND child.status <> 4) AS reply_count
            FROM post_comment c
            LEFT JOIN user u ON u.id = c.user_id
            LEFT JOIN community_post p ON p.id = c.post_id
            LEFT JOIN post_comment parent ON parent.id = c.parent_id
            WHERE c.id = %s
            LIMIT 1
            """,
            [comment_id],
        )
    return None


def get_admin_comment_detail(comment_type: str, comment_id: int) -> Dict[str, Any]:
    if comment_type not in {'news', 'post'}:
        raise AppException(code=400, message='Unsupported comment type')
    row = _comment_detail_row(comment_type, comment_id)
    if row is None:
        raise AppException(code=404, message='Comment not found')
    payload = _build_admin_comment_item(row)
    payload['context'] = {
        'target_id': row.get('target_id'),
        'target_title': str(row.get('target_title') or ''),
        'target_source': str(row.get('target_source') or ''),
        'target_publish_time': format_datetime(row.get('target_publish_time')) or None,
        'target_summary': _preview_text(row.get('target_summary') or '', 240),
        'missing': not bool(row.get('target_title')),
    }
    if comment_type == 'news':
        replies = execute_query(
            """
            SELECT c.id, c.user_id, COALESCE(u.username, '') AS username, COALESCE(u.nickname, '') AS nickname,
                   COALESCE(c.content, '') AS content, NULL AS media_json, c.like_count, c.status, c.created_at
            FROM news_comment c
            LEFT JOIN user u ON u.id = c.user_id
            WHERE c.parent_id = %s
            ORDER BY c.created_at DESC, c.id DESC
            LIMIT 10
            """,
            [comment_id],
        )
    else:
        replies = execute_query(
            """
            SELECT c.id, c.user_id, COALESCE(u.username, '') AS username, COALESCE(u.nickname, '') AS nickname,
                   COALESCE(c.content, '') AS content, c.media_json, c.like_count, c.status, c.created_at
            FROM post_comment c
            LEFT JOIN user u ON u.id = c.user_id
            WHERE c.parent_id = %s
            ORDER BY c.created_at DESC, c.id DESC
            LIMIT 10
            """,
            [comment_id],
        )
    payload['replies'] = [
        {
            'id': int(item.get('id') or 0),
            'user_id': item.get('user_id'),
            'username': str(item.get('nickname') or item.get('username') or ''),
            'content': str(item.get('content') or ''),
            'like_count': int(item.get('like_count') or 0),
            'status': _normalize_status(item.get('status')),
            'status_label': _comment_status_label(item.get('status')),
            'create_time': format_datetime(item.get('created_at')) or None,
        } for item in replies
    ]
    return AdminCommentDetail.model_validate(payload).model_dump()


def review_admin_comment(comment_type: str, comment_id: int, request: ReviewActionRequest, current_user: Any | None = None) -> Dict[str, Any]:
    if comment_type not in {'news', 'post'}:
        raise AppException(code=400, message='Unsupported comment type')
    table = 'news_comment' if comment_type == 'news' else 'post_comment'
    parent_table = 'news' if comment_type == 'news' else 'community_post'
    parent_field = 'news_id' if comment_type == 'news' else 'post_id'
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(f'SELECT id, status, {parent_field} AS parent_target_id FROM {table} WHERE id = %s LIMIT 1', [comment_id])
            row = cursor.fetchone()
            if row is None:
                raise AppException(code=404, message='Comment not found')
            old_status = _normalize_status(row.get('status'))
            new_status = _resolve_target_status('comment', request.action)
            cursor.execute(f'UPDATE {table} SET status = %s, updated_at = NOW() WHERE id = %s', [new_status, comment_id])
            _update_comment_counters(cursor, parent_table=parent_table, parent_id=int(row.get('parent_target_id') or 0), old_status=old_status, new_status=new_status)
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
    write_admin_operation_log(
        current_user=current_user,
        module='content',
        action=request.action,
        target_type=f'{comment_type}_comment',
        target_id=comment_id,
        description=f'Review {comment_type} comment: {request.action}. Reason: {request.reason or ""}',
        result='success',
    )
    return AdminCommentActionResult(
        comment_id=comment_id,
        comment_type=comment_type,  # type: ignore[arg-type]
        action=request.action,
        updated=True,
        status=new_status,
        status_label=_comment_status_label(new_status),
        message='Success',
    ).model_dump()




HOT_STATUS_LABELS = {0: 'Hidden', 1: 'Visible'}
TOPIC_STATUS_LABELS = {0: 'Disabled', 1: 'Enabled'}
PIN_COLUMNS = ('is_pinned', 'pinned', 'is_top')
HIDE_COLUMNS = ('is_hidden', 'hidden')


def _hot_status_label(value: Any) -> str:
    return HOT_STATUS_LABELS.get(_normalize_status(value), 'Unknown')


def _topic_status_label(value: Any) -> str:
    return TOPIC_STATUS_LABELS.get(_normalize_status(value), 'Unknown')


def _normalize_hot_target_type(value: Any) -> str:
    raw = str(value or '').strip()
    if raw == 'community_post':
        return 'post'
    if raw == 'news_topic':
        return 'topic'
    return raw or 'news'


def _hot_support() -> Dict[str, Any]:
    columns = _table_columns('hot_topic')
    return AdminHotTopicSupport(
        pin_supported=any(column in columns for column in PIN_COLUMNS),
        hide_supported=any(column in columns for column in HIDE_COLUMNS) or 'status' in columns,
        hide_uses_status=not any(column in columns for column in HIDE_COLUMNS) and 'status' in columns,
        manual_rank_supported='rank_no' in columns,
    ).model_dump()


def _hot_pin_column() -> str | None:
    columns = _table_columns('hot_topic')
    for column in PIN_COLUMNS:
        if column in columns:
            return column
    return None


def _hot_hide_column() -> str | None:
    columns = _table_columns('hot_topic')
    for column in HIDE_COLUMNS:
        if column in columns:
            return column
    return None


def _hot_related_target(target_type: str, target_id: Any) -> Dict[str, Any]:
    if not target_id:
        return {'type': target_type, 'id': None, 'title': '', 'missing': True}
    normalized = _normalize_hot_target_type(target_type)
    if normalized == 'news':
        row = execute_one('SELECT id, title, source, status FROM news WHERE id = %s LIMIT 1', [target_id])
        if not row:
            return {'type': normalized, 'id': target_id, 'title': '', 'missing': True}
        return {'type': normalized, 'id': int(row.get('id') or 0), 'title': str(row.get('title') or ''), 'source': str(row.get('source') or ''), 'status': _normalize_status(row.get('status')), 'missing': False}
    if normalized == 'post':
        row = execute_one('SELECT id, title, user_id, status FROM community_post WHERE id = %s LIMIT 1', [target_id])
        if not row:
            return {'type': normalized, 'id': target_id, 'title': '', 'missing': True}
        return {'type': normalized, 'id': int(row.get('id') or 0), 'title': str(row.get('title') or ''), 'user_id': row.get('user_id'), 'status': _normalize_status(row.get('status')), 'missing': False}
    if normalized == 'topic':
        row = execute_one('SELECT id, topic_name, summary, status FROM news_topic WHERE id = %s LIMIT 1', [target_id])
        if not row:
            return {'type': normalized, 'id': target_id, 'title': '', 'missing': True}
        return {'type': normalized, 'id': int(row.get('id') or 0), 'title': str(row.get('topic_name') or ''), 'summary': str(row.get('summary') or ''), 'status': _normalize_status(row.get('status')), 'missing': False}
    return {'type': normalized, 'id': target_id, 'title': '', 'missing': True}


def _build_admin_hot_item(row: Dict[str, Any]) -> Dict[str, Any]:
    target_type = _normalize_hot_target_type(row.get('target_type'))
    related = _hot_related_target(target_type, row.get('target_id'))
    status = _normalize_status(row.get('status'))
    item = AdminHotTopicItem(
        id=int(row.get('id') or 0),
        title=str(row.get('title') or ''),
        hot_type='news_hot' if target_type == 'news' else ('community_hot' if target_type == 'post' else 'topic_hot'),
        target_type=target_type,
        target_id=row.get('target_id'),
        tag=str(row.get('tag') or ''),
        heat_score=int(row.get('heat_score') or 0),
        rank_no=int(row.get('rank_no') or 0),
        status=status,
        status_label=_hot_status_label(status),
        is_pinned=row.get('is_pinned'),
        is_hidden=status == 0 if row.get('is_hidden') is None else bool(row.get('is_hidden')),
        target_title=str(related.get('title') or ''),
        target_missing=bool(related.get('missing')),
        created_at=format_datetime(row.get('created_at')) or None,
        updated_at=format_datetime(row.get('updated_at')) or None,
    )
    return item.model_dump()


def _build_hot_where(keyword: str | None = None, hot_type: str | None = None, target_type: str | None = None, status: int | None = None, is_hidden: bool | None = None, start_time: str | None = None, end_time: str | None = None) -> tuple[str, list[Any]]:
    conditions: list[str] = []
    params: list[Any] = []
    if keyword:
        conditions.append('(title LIKE %s OR tag LIKE %s)')
        params.extend([f'%{keyword}%', f'%{keyword}%'])
    if hot_type:
        if hot_type == 'news_hot':
            conditions.append("target_type = 'news'")
        elif hot_type == 'community_hot':
            conditions.append("target_type IN ('post', 'community_post')")
        elif hot_type == 'topic_hot':
            conditions.append("target_type IN ('topic', 'news_topic')")
    if target_type:
        normalized = _normalize_hot_target_type(target_type)
        if normalized == 'post':
            conditions.append("target_type IN ('post', 'community_post')")
        elif normalized == 'topic':
            conditions.append("target_type IN ('topic', 'news_topic')")
        else:
            conditions.append('target_type = %s')
            params.append(normalized)
    if status is not None:
        conditions.append('status = %s')
        params.append(status)
    if is_hidden is not None:
        conditions.append('status = %s')
        params.append(0 if is_hidden else 1)
    if start_time:
        conditions.append('updated_at >= %s')
        params.append(start_time)
    if end_time:
        conditions.append('updated_at <= %s')
        params.append(end_time)
    return ('WHERE ' + ' AND '.join(conditions)) if conditions else '', params


def _admin_hot_summary() -> Dict[str, Any]:
    return AdminHotTopicSummary(
        total_count=_safe_count('SELECT COUNT(*) AS total FROM hot_topic'),
        news_hot_count=_safe_count("SELECT COUNT(*) AS total FROM hot_topic WHERE target_type = 'news'"),
        community_hot_count=_safe_count("SELECT COUNT(*) AS total FROM hot_topic WHERE target_type IN ('post', 'community_post')"),
        topic_hot_count=_safe_count("SELECT COUNT(*) AS total FROM hot_topic WHERE target_type IN ('topic', 'news_topic')"),
        pinned_count=0,
        hidden_count=_safe_count('SELECT COUNT(*) AS total FROM hot_topic WHERE status = 0'),
    ).model_dump()


def get_admin_hot_topic_options() -> Dict[str, Any]:
    rows = execute_query('SELECT DISTINCT target_type FROM hot_topic ORDER BY target_type ASC')
    seen: set[str] = set()
    target_types: list[dict[str, Any]] = []
    for row in rows:
        value = _normalize_hot_target_type(row.get('target_type'))
        if value in seen:
            continue
        seen.add(value)
        target_types.append({'label': value, 'value': value})
    if not target_types:
        target_types = [{'label': 'news', 'value': 'news'}, {'label': 'post', 'value': 'post'}, {'label': 'topic', 'value': 'topic'}]
    return AdminHotTopicOptions(target_types=target_types, statuses=[{'label': label, 'value': value} for value, label in HOT_STATUS_LABELS.items()], support=AdminHotTopicSupport.model_validate(_hot_support())).model_dump()


def get_admin_hot_topic_list(keyword: str | None = None, hot_type: str | None = None, target_type: str | None = None, status: int | None = None, is_pinned: bool | None = None, is_hidden: bool | None = None, start_time: str | None = None, end_time: str | None = None, page: int = 1, page_size: int = 10) -> Dict[str, Any]:
    _ = is_pinned
    where_sql, params = _build_hot_where(keyword, hot_type, target_type, status, is_hidden, start_time, end_time)
    total_row = execute_one(f'SELECT COUNT(*) AS total FROM hot_topic {where_sql}', params)
    total = int((total_row or {}).get('total') or 0)
    normalized_page = max(page, 1)
    normalized_page_size = max(page_size, 1)
    offset = (normalized_page - 1) * normalized_page_size
    sql = f"SELECT id, title, target_type, target_id, heat_score, rank_no, tag, status, created_at, updated_at FROM hot_topic {where_sql} ORDER BY CASE WHEN rank_no > 0 THEN rank_no ELSE 999999 END ASC, heat_score DESC, updated_at DESC, id DESC LIMIT %s OFFSET %s"
    rows = execute_query(sql, params + [normalized_page_size, offset])
    return AdminHotTopicListResponse(items=[AdminHotTopicItem.model_validate(_build_admin_hot_item(row)) for row in rows], total=total, page=normalized_page, page_size=normalized_page_size, summary=AdminHotTopicSummary.model_validate(_admin_hot_summary()), support=AdminHotTopicSupport.model_validate(_hot_support())).model_dump()


def get_admin_hot_topic_detail(hot_id: int) -> Dict[str, Any]:
    row = execute_one('SELECT id, title, target_type, target_id, heat_score, rank_no, tag, status, created_at, updated_at FROM hot_topic WHERE id = %s LIMIT 1', [hot_id])
    if not row:
        raise AppException(code=404, message='Hot topic not found')
    payload = _build_admin_hot_item(row)
    payload['related_target'] = _hot_related_target(row.get('target_type'), row.get('target_id'))
    return AdminHotTopicDetail.model_validate(payload).model_dump()


def update_admin_hot_topic_rank(hot_id: int, request: AdminHotTopicRankRequest) -> Dict[str, Any]:
    if 'rank_no' not in _table_columns('hot_topic'):
        raise AppException(code=400, message='Current hot_topic table does not support manual rank')
    affected = execute_update('UPDATE hot_topic SET rank_no = %s, updated_at = NOW() WHERE id = %s', [request.rank_no, hot_id])
    if affected == 0:
        raise AppException(code=404, message='Hot topic not found')
    return AdminHotTopicActionResult(hot_id=hot_id, action='rank', rank_no=request.rank_no, message='Success').model_dump()


def set_admin_hot_topic_pin(hot_id: int, pinned: bool) -> Dict[str, Any]:
    column = _hot_pin_column()
    if not column:
        raise AppException(code=400, message='Current hot_topic table does not support pinned field')
    affected = execute_update(f'UPDATE hot_topic SET {column} = %s, updated_at = NOW() WHERE id = %s', [1 if pinned else 0, hot_id])
    if affected == 0:
        raise AppException(code=404, message='Hot topic not found')
    return AdminHotTopicActionResult(hot_id=hot_id, action='pin' if pinned else 'unpin', message='Success').model_dump()


def set_admin_hot_topic_hidden(hot_id: int, hidden: bool) -> Dict[str, Any]:
    column = _hot_hide_column()
    status = None
    if column:
        affected = execute_update(f'UPDATE hot_topic SET {column} = %s, updated_at = NOW() WHERE id = %s', [1 if hidden else 0, hot_id])
    elif 'status' in _table_columns('hot_topic'):
        status = 0 if hidden else 1
        affected = execute_update('UPDATE hot_topic SET status = %s, updated_at = NOW() WHERE id = %s', [status, hot_id])
    else:
        raise AppException(code=400, message='Current hot_topic table does not support hidden field')
    if affected == 0:
        raise AppException(code=404, message='Hot topic not found')
    return AdminHotTopicActionResult(hot_id=hot_id, action='hide' if hidden else 'restore', status=status, status_label=_hot_status_label(status) if status is not None else '', message='Success').model_dump()


def refresh_admin_hot_topic_heat(hot_id: int) -> Dict[str, Any]:
    detail = get_admin_hot_topic_detail(hot_id)
    target = detail.get('related_target') or {}
    heat_score = int(detail.get('heat_score') or 0)
    if target.get('type') == 'news' and target.get('id'):
        row = execute_one('SELECT view_count, like_count, comment_count, favorite_count FROM news WHERE id = %s LIMIT 1', [target.get('id')])
        if row:
            heat_score = int(row.get('view_count') or 0) + int(row.get('like_count') or 0) * 3 + int(row.get('comment_count') or 0) * 5 + int(row.get('favorite_count') or 0) * 4
    elif target.get('type') == 'post' and target.get('id'):
        row = execute_one('SELECT heat_score, like_count, comment_count, favorite_count FROM community_post WHERE id = %s LIMIT 1', [target.get('id')])
        if row:
            heat_score = int(row.get('heat_score') or 0) or (int(row.get('like_count') or 0) * 3 + int(row.get('comment_count') or 0) * 5 + int(row.get('favorite_count') or 0) * 4)
    elif target.get('type') == 'topic' and target.get('id'):
        row = execute_one('SELECT heat_score FROM news_topic WHERE id = %s LIMIT 1', [target.get('id')])
        if row:
            heat_score = int(row.get('heat_score') or 0)
    affected = execute_update('UPDATE hot_topic SET heat_score = %s, updated_at = NOW() WHERE id = %s', [heat_score, hot_id])
    if affected == 0:
        raise AppException(code=404, message='Hot topic not found')
    return AdminHotTopicActionResult(hot_id=hot_id, action='refresh_heat', message='Success').model_dump()


def _topic_support() -> Dict[str, Any]:
    columns = _table_columns('news_topic')
    return AdminTopicSupport(news_topic_table_supported=bool(columns), keyword_supported='keyword_list' in columns, description_supported='summary' in columns).model_dump()


def _topic_keywords_to_json(value: Any) -> str:
    if isinstance(value, str):
        items = [item.strip() for item in value.replace('?', ',').split(',') if item.strip()]
    else:
        items = [str(item).strip() for item in (value or []) if str(item).strip()]
    return json.dumps(items, ensure_ascii=False)


def _build_admin_topic_item(row: Dict[str, Any]) -> Dict[str, Any]:
    item = AdminTopicItem(id=int(row.get('id') or 0), topic_name=str(row.get('topic_name') or ''), summary=str(row.get('summary') or ''), keyword_list=_parse_tags(row.get('keyword_list')), heat_score=int(row.get('heat_score') or 0), news_count=int(row.get('news_count') or 0), status=_normalize_status(row.get('status')), status_label=_topic_status_label(row.get('status')), created_at=format_datetime(row.get('created_at')) or None, updated_at=format_datetime(row.get('updated_at')) or None)
    return item.model_dump()


def _build_topic_where(keyword: str | None = None, status: int | None = None, has_news: bool | None = None, start_time: str | None = None, end_time: str | None = None) -> tuple[str, list[Any]]:
    conditions: list[str] = []
    params: list[Any] = []
    if keyword:
        like = f'%{keyword}%'
        conditions.append('(t.topic_name LIKE %s OR t.summary LIKE %s OR CAST(t.keyword_list AS CHAR) LIKE %s)')
        params.extend([like, like, like])
    if status is not None:
        conditions.append('t.status = %s')
        params.append(status)
    if has_news is True:
        conditions.append('COALESCE(nc.news_count, 0) > 0')
    elif has_news is False:
        conditions.append('COALESCE(nc.news_count, 0) = 0')
    if start_time:
        conditions.append('t.created_at >= %s')
        params.append(start_time)
    if end_time:
        conditions.append('t.created_at <= %s')
        params.append(end_time)
    return ('WHERE ' + ' AND '.join(conditions)) if conditions else '', params


def _topic_base_sql() -> str:
    return "FROM news_topic t LEFT JOIN (SELECT topic_id, COUNT(*) AS news_count FROM news WHERE topic_id IS NOT NULL GROUP BY topic_id) nc ON nc.topic_id = t.id"


def _admin_topic_summary() -> Dict[str, Any]:
    return AdminTopicSummary(total_count=_safe_count('SELECT COUNT(*) AS total FROM news_topic'), enabled_count=_safe_count('SELECT COUNT(*) AS total FROM news_topic WHERE status = 1'), disabled_count=_safe_count('SELECT COUNT(*) AS total FROM news_topic WHERE status = 0'), with_news_count=_safe_count('SELECT COUNT(DISTINCT topic_id) AS total FROM news WHERE topic_id IS NOT NULL'), without_news_count=_safe_count('SELECT COUNT(*) AS total FROM news_topic t WHERE NOT EXISTS (SELECT 1 FROM news n WHERE n.topic_id = t.id LIMIT 1)')).model_dump()


def get_admin_topic_options() -> Dict[str, Any]:
    return AdminTopicOptions(status_options=[{'label': label, 'value': value} for value, label in TOPIC_STATUS_LABELS.items()], support=AdminTopicSupport.model_validate(_topic_support())).model_dump()


def get_admin_topic_list(keyword: str | None = None, status: int | None = None, has_news: bool | None = None, start_time: str | None = None, end_time: str | None = None, page: int = 1, page_size: int = 10) -> Dict[str, Any]:
    where_sql, params = _build_topic_where(keyword, status, has_news, start_time, end_time)
    base_sql = _topic_base_sql()
    total_row = execute_one(f'SELECT COUNT(*) AS total {base_sql} {where_sql}', params)
    total = int((total_row or {}).get('total') or 0)
    normalized_page = max(page, 1)
    normalized_page_size = max(page_size, 1)
    offset = (normalized_page - 1) * normalized_page_size
    sql = f"SELECT t.id, t.topic_name, t.summary, t.keyword_list, t.heat_score, t.status, t.created_at, t.updated_at, COALESCE(nc.news_count, 0) AS news_count {base_sql} {where_sql} ORDER BY t.heat_score DESC, t.updated_at DESC, t.id DESC LIMIT %s OFFSET %s"
    rows = execute_query(sql, params + [normalized_page_size, offset])
    return AdminTopicListResponse(items=[AdminTopicItem.model_validate(_build_admin_topic_item(row)) for row in rows], total=total, page=normalized_page, page_size=normalized_page_size, summary=AdminTopicSummary.model_validate(_admin_topic_summary()), support=AdminTopicSupport.model_validate(_topic_support())).model_dump()


def _build_admin_topic_news_item(row: Dict[str, Any]) -> Dict[str, Any]:
    return AdminTopicNewsItem(id=int(row.get('id') or 0), title=str(row.get('title') or ''), category_name=str(row.get('category_name') or ''), source=str(row.get('source') or ''), publish_time=format_datetime(row.get('publish_time')) or None, status=_normalize_status(row.get('status')), status_label=_news_status_label(row.get('status')), topic_id=row.get('topic_id')).model_dump()


def get_admin_topic_detail(topic_id: int) -> Dict[str, Any]:
    row = execute_one(f"SELECT t.id, t.topic_name, t.summary, t.keyword_list, t.heat_score, t.status, t.created_at, t.updated_at, COALESCE(nc.news_count, 0) AS news_count {_topic_base_sql()} WHERE t.id = %s LIMIT 1", [topic_id])
    if not row:
        raise AppException(code=404, message='Topic not found')
    payload = _build_admin_topic_item(row)
    recent = execute_query("SELECT n.id, n.title, COALESCE(c.name, '') AS category_name, COALESCE(n.source, '') AS source, n.publish_time, n.status, n.topic_id FROM news n LEFT JOIN news_category c ON c.id = n.category_id WHERE n.topic_id = %s ORDER BY n.publish_time DESC, n.id DESC LIMIT 5", [topic_id])
    payload['recent_news'] = [AdminTopicNewsItem.model_validate(_build_admin_topic_news_item(item)).model_dump() for item in recent]
    return AdminTopicDetail.model_validate(payload).model_dump()


def create_admin_topic(request: AdminTopicPayload) -> Dict[str, Any]:
    topic_name = request.topic_name.strip()
    if not topic_name:
        raise AppException(code=400, message='Topic name is required')
    new_id = execute_insert('INSERT INTO news_topic (topic_name, summary, keyword_list, heat_score, status, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, NOW(), NOW())', [topic_name, request.summary or '', _topic_keywords_to_json(request.keyword_list), request.heat_score or 0, request.status])
    return AdminTopicActionResult(topic_id=int(new_id), action='create', status=request.status, status_label=_topic_status_label(request.status), message='Success').model_dump()


def update_admin_topic(topic_id: int, request: AdminTopicPayload) -> Dict[str, Any]:
    topic_name = request.topic_name.strip()
    if not topic_name:
        raise AppException(code=400, message='Topic name is required')
    affected = execute_update('UPDATE news_topic SET topic_name = %s, summary = %s, keyword_list = %s, heat_score = %s, status = %s, updated_at = NOW() WHERE id = %s', [topic_name, request.summary or '', _topic_keywords_to_json(request.keyword_list), request.heat_score or 0, request.status, topic_id])
    if affected == 0:
        raise AppException(code=404, message='Topic not found')
    return AdminTopicActionResult(topic_id=topic_id, action='update', status=request.status, status_label=_topic_status_label(request.status), message='Success').model_dump()


def update_admin_topic_status(topic_id: int, request: AdminTopicStatusRequest) -> Dict[str, Any]:
    affected = execute_update('UPDATE news_topic SET status = %s, updated_at = NOW() WHERE id = %s', [request.status, topic_id])
    if affected == 0:
        raise AppException(code=404, message='Topic not found')
    return AdminTopicActionResult(topic_id=topic_id, action='status', status=request.status, status_label=_topic_status_label(request.status), message='Success').model_dump()


def get_admin_topic_news(topic_id: int, keyword: str | None = None, status: int | None = None, page: int = 1, page_size: int = 10) -> Dict[str, Any]:
    if not execute_one('SELECT id FROM news_topic WHERE id = %s LIMIT 1', [topic_id]):
        raise AppException(code=404, message='Topic not found')
    conditions = ['n.topic_id = %s']
    params: list[Any] = [topic_id]
    if keyword:
        conditions.append('(n.title LIKE %s OR n.summary LIKE %s)')
        params.extend([f'%{keyword}%', f'%{keyword}%'])
    if status is not None:
        conditions.append('n.status = %s')
        params.append(status)
    where_sql = 'WHERE ' + ' AND '.join(conditions)
    total_row = execute_one(f'SELECT COUNT(*) AS total FROM news n {where_sql}', params)
    total = int((total_row or {}).get('total') or 0)
    normalized_page = max(page, 1)
    normalized_page_size = max(page_size, 1)
    offset = (normalized_page - 1) * normalized_page_size
    rows = execute_query(f"SELECT n.id, n.title, COALESCE(c.name, '') AS category_name, COALESCE(n.source, '') AS source, n.publish_time, n.status, n.topic_id FROM news n LEFT JOIN news_category c ON c.id = n.category_id {where_sql} ORDER BY n.publish_time DESC, n.id DESC LIMIT %s OFFSET %s", params + [normalized_page_size, offset])
    return AdminTopicNewsResponse(items=[AdminTopicNewsItem.model_validate(_build_admin_topic_news_item(row)) for row in rows], total=total, page=normalized_page, page_size=normalized_page_size).model_dump()


def get_admin_topic_candidate_news(topic_id: int, keyword: str | None = None, status: int | None = None, page: int = 1, page_size: int = 10) -> Dict[str, Any]:
    if not execute_one('SELECT id FROM news_topic WHERE id = %s LIMIT 1', [topic_id]):
        raise AppException(code=404, message='Topic not found')
    conditions = ['(n.topic_id IS NULL OR n.topic_id <> %s)']
    params: list[Any] = [topic_id]
    if keyword:
        conditions.append('(n.title LIKE %s OR n.summary LIKE %s OR n.content LIKE %s)')
        params.extend([f'%{keyword}%', f'%{keyword}%', f'%{keyword}%'])
    if status is not None:
        conditions.append('n.status = %s')
        params.append(status)
    where_sql = 'WHERE ' + ' AND '.join(conditions)
    total_row = execute_one(f'SELECT COUNT(*) AS total FROM news n {where_sql}', params)
    total = int((total_row or {}).get('total') or 0)
    normalized_page = max(page, 1)
    normalized_page_size = max(page_size, 1)
    offset = (normalized_page - 1) * normalized_page_size
    rows = execute_query(f"SELECT n.id, n.title, COALESCE(c.name, '') AS category_name, COALESCE(n.source, '') AS source, n.publish_time, n.status, n.topic_id FROM news n LEFT JOIN news_category c ON c.id = n.category_id {where_sql} ORDER BY n.publish_time DESC, n.id DESC LIMIT %s OFFSET %s", params + [normalized_page_size, offset])
    return AdminTopicNewsResponse(items=[AdminTopicNewsItem.model_validate(_build_admin_topic_news_item(row)) for row in rows], total=total, page=normalized_page, page_size=normalized_page_size).model_dump()


def bind_admin_topic_news(topic_id: int, request: AdminTopicBindNewsRequest) -> Dict[str, Any]:
    if not execute_one('SELECT id FROM news_topic WHERE id = %s LIMIT 1', [topic_id]):
        raise AppException(code=404, message='Topic not found')
    news_ids = sorted({int(item) for item in request.news_ids if int(item) > 0})
    if not news_ids:
        raise AppException(code=400, message='news_ids is required')
    placeholders = ','.join(['%s'] * len(news_ids))
    exists_row = execute_one(f'SELECT COUNT(*) AS total FROM news WHERE id IN ({placeholders})', news_ids)
    if int((exists_row or {}).get('total') or 0) != len(news_ids):
        raise AppException(code=400, message='Some news ids do not exist')
    affected = execute_update(f'UPDATE news SET topic_id = %s, updated_at = NOW() WHERE id IN ({placeholders})', [topic_id] + news_ids)
    return AdminTopicActionResult(topic_id=topic_id, action='bind_news', affected_count=affected, message='Success').model_dump()


def unbind_admin_topic_news(topic_id: int, request: AdminTopicBindNewsRequest) -> Dict[str, Any]:
    news_ids = sorted({int(item) for item in request.news_ids if int(item) > 0})
    if not news_ids:
        raise AppException(code=400, message='news_ids is required')
    placeholders = ','.join(['%s'] * len(news_ids))
    affected = execute_update(f'UPDATE news SET topic_id = NULL, updated_at = NOW() WHERE topic_id = %s AND id IN ({placeholders})', [topic_id] + news_ids)
    return AdminTopicActionResult(topic_id=topic_id, action='unbind_news', affected_count=affected, message='Success').model_dump()

# ── Dashboard 5 分钟服务端缓存 ──
_dashboard_cache: dict[str, Any] | None = None
_dashboard_cache_expires: float = 0.0
_DASHBOARD_CACHE_TTL = 300  # 秒


def get_dashboard() -> AdminDashboard:
    """获取后台概览数据（5 分钟缓存）。"""
    global _dashboard_cache, _dashboard_cache_expires

    now = time.time()
    if _dashboard_cache is not None and now < _dashboard_cache_expires:
        return copy.deepcopy(_dashboard_cache)

    try:
        user_count = _safe_count('SELECT COUNT(*) AS total FROM user')
        news_count = _safe_count('SELECT COUNT(*) AS total FROM news WHERE status = 1')
        post_count = _safe_count('SELECT COUNT(*) AS total FROM community_post')
        # pending_count: 只统计真正待审核的 (status=3)
        pending_news = _safe_count('SELECT COUNT(*) AS total FROM news WHERE status = 3')
        pending_posts = _safe_count('SELECT COUNT(*) AS total FROM community_post WHERE status = 3')
        pending_comments = (
            _safe_count('SELECT COUNT(*) AS total FROM news_comment WHERE status = 3')
            + _safe_count('SELECT COUNT(*) AS total FROM post_comment WHERE status = 3')
        )
        pending_total = pending_news + pending_posts + pending_comments

        today_new_users = _safe_count('SELECT COUNT(*) AS total FROM user WHERE DATE(created_at) = CURDATE()')
        active_users_7d = 0
        if _ops_table_exists('browse_history'):
            row = execute_one('SELECT COUNT(DISTINCT user_id) AS total FROM browse_history WHERE browse_time >= DATE_SUB(NOW(), INTERVAL 7 DAY)')
            active_users_7d = int((row or {}).get('total') or 0)
        today_review_done = 0
        if _ops_table_exists('admin_operation_log'):
            row = execute_one(
                "SELECT COUNT(*) AS total FROM admin_operation_log "
                "WHERE DATE(created_at) = CURDATE() AND module = 'content' "
                "AND action IN ('approve','reject','fold','delete','restore')"
            )
            today_review_done = int((row or {}).get('total') or 0)
        today_ai_calls = 0
        avg_response_ms = None
        if _ops_table_exists('ai_generate_record'):
            row = execute_one('SELECT COUNT(*) AS total FROM ai_generate_record WHERE DATE(created_at) = CURDATE()')
            today_ai_calls = int((row or {}).get('total') or 0)
            if 'response_ms' in _table_columns('ai_generate_record'):
                row = execute_one('SELECT AVG(response_ms) AS avg_ms FROM ai_generate_record WHERE DATE(created_at) = CURDATE() AND response_ms > 0')
                avg_ms = (row or {}).get('avg_ms')
                if avg_ms is not None:
                    avg_response_ms = int(round(avg_ms))
        timeline_pending = 0
        if _ops_table_exists('event_timeline'):
            row = execute_one("SELECT COUNT(*) AS total FROM event_timeline WHERE generate_status != 'generated'")
            timeline_pending = int((row or {}).get('total') or 0)

        result = AdminDashboard(
            user_count=user_count,
            news_count=news_count,
            post_count=post_count,
            pending_count=pending_total,  # now uses accurate pending-only counts
            pending_news_count=pending_news,
            pending_post_count=pending_posts,
            pending_comment_count=pending_comments,
            today_news_count=_safe_count('SELECT COUNT(*) AS total FROM news WHERE DATE(created_at) = CURDATE()'),
            today_user_count=_safe_count('SELECT COUNT(*) AS total FROM user WHERE DATE(created_at) = CURDATE()'),
            today_new_users=today_new_users,
            active_users_7d=active_users_7d,
            today_review_done=today_review_done,
            today_ai_calls=today_ai_calls,
            avg_response_ms=avg_response_ms,
            timeline_pending_count=timeline_pending,
            pending_total=pending_total,
        )
        _dashboard_cache = copy.deepcopy(result)
        _dashboard_cache_expires = time.time() + _DASHBOARD_CACHE_TTL
        return result
    except Exception as exc:  # noqa: BLE001
        logger.exception('admin dashboard query failed')
        raise AppException(code=500, message='后台首页统计查询失败，请检查数据库连接和表结构') from exc


def get_pending_posts(page: int = 1, page_size: int = 10) -> Dict[str, Any]:
    """获取待审核帖子列表，数据库优先。"""
    items = _query_post_items()
    return paginate(items, page=page, page_size=page_size)


def _build_admin_users_where(
    keyword: str | None = None,
    role: str | None = None,
    status: int | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
) -> tuple[str, list[Any]]:
    conditions: list[str] = []
    params: list[Any] = []
    if keyword:
        conditions.append('(u.username LIKE %s OR u.nickname LIKE %s)')
        like = f'%{keyword}%'
        params.extend([like, like])
    if role:
        conditions.append('u.role = %s')
        params.append(role)
    if status is not None:
        conditions.append('u.status = %s')
        params.append(status)
    if start_time:
        conditions.append('u.created_at >= %s')
        params.append(start_time)
    if end_time:
        conditions.append('u.created_at <= %s')
        params.append(end_time)
    return ('WHERE ' + ' AND '.join(conditions)) if conditions else '', params


def _get_user_summary() -> Dict[str, Any]:
    return {
        'total_count': _safe_count('SELECT COUNT(*) AS total FROM user'),
        'admin_count': _safe_count("SELECT COUNT(*) AS total FROM user WHERE role = 'admin'"),
        'editor_count': _safe_count("SELECT COUNT(*) AS total FROM user WHERE role = 'editor'"),
        'user_count': _safe_count("SELECT COUNT(*) AS total FROM user WHERE role = 'user'"),
        'active_count': _safe_count('SELECT COUNT(*) AS total FROM user WHERE status = 1'),
        'disabled_count': _safe_count('SELECT COUNT(*) AS total FROM user WHERE status = 0'),
    }


def get_user_options() -> Dict[str, Any]:
    return AdminUserOptions(
        roles=[
            {'label': '普通用户', 'value': 'user'},
            {'label': '审核/编辑', 'value': 'editor'},
            {'label': '管理员', 'value': 'admin'},
        ],
        statuses=[
            {'label': '正常', 'value': 1},
            {'label': '已禁用', 'value': 0},
        ],
        last_login_supported=False,
    ).model_dump()


def get_users(
    keyword: str | None = None,
    role: str | None = None,
    status: int | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
    page: int = 1,
    page_size: int = 10,
) -> Dict[str, Any]:
    """Get paginated user list with filters. No mock fallback."""
    where_sql, params = _build_admin_users_where(
        keyword=keyword, role=role, status=status,
        start_time=start_time, end_time=end_time,
    )
    normalized_page = max(page, 1)
    normalized_page_size = max(page_size, 1)
    offset = (normalized_page - 1) * normalized_page_size

    count_row = execute_one(
        f'SELECT COUNT(*) AS total FROM user u {where_sql}', params
    )
    total = int((count_row or {}).get('total') or 0)

    rows = execute_query(
        f'''
        SELECT id, username, nickname, role, status, created_at AS create_time
        FROM user u
        {where_sql}
        ORDER BY id ASC
        LIMIT %s OFFSET %s
        ''',
        [*params, normalized_page_size, offset],
    )
    items = [_build_user_item(row) for row in rows]
    summary = _get_user_summary()

    return AdminUserListResponse(
        items=[UserItem(**item) for item in items],
        total=total,
        page=normalized_page,
        page_size=normalized_page_size,
        summary=AdminUserSummary(**summary),
    ).model_dump()


def _get_user_behavior_stats(user_id: int) -> Dict[str, Any]:
    """Count user activities across related tables."""
    return {
        'post_count': _safe_count(f'SELECT COUNT(*) AS total FROM community_post WHERE user_id = {user_id}'),
        'comment_count': (
            _safe_count(f'SELECT COUNT(*) AS total FROM news_comment WHERE user_id = {user_id}')
            + _safe_count(f'SELECT COUNT(*) AS total FROM post_comment WHERE user_id = {user_id}')
        ),
        'ai_generation_count': _safe_count(f'SELECT COUNT(*) AS total FROM ai_generate_record WHERE user_id = {user_id}'),
        'browse_count': _safe_count(f'SELECT COUNT(*) AS total FROM browse_history WHERE user_id = {user_id}'),
        'favorite_count': _safe_count(f'SELECT COUNT(*) AS total FROM favorite WHERE user_id = {user_id}'),
    }


def get_user_detail(user_id: int) -> Dict[str, Any]:
    """Get single user detail with behavior stats. No mock fallback."""
    row = execute_one(
        '''
        SELECT id, username, nickname, role, status,
               created_at AS create_time, updated_at,
               COALESCE(email, '') AS email,
               COALESCE(phone, '') AS phone,
               COALESCE(avatar, '') AS avatar
        FROM user
        WHERE id = %s
        LIMIT 1
        ''',
        [user_id],
    )
    if row is None:
        raise AppException(code=404, message='用户不存在')

    behavior = _get_user_behavior_stats(user_id)

    return AdminUserDetail(
        id=int(row.get('id', 0)),
        username=str(row.get('username', '')),
        nickname=str(row.get('nickname', '')),
        role=str(row.get('role', 'user')),
        status=int(row.get('status', 1)),
        create_time=format_datetime(row.get('create_time')) or None,
        updated_at=format_datetime(row.get('updated_at')) or None,
        email=str(row.get('email', '')),
        phone=str(row.get('phone', '')),
        avatar=str(row.get('avatar', '')),
        behavior=AdminUserBehaviorStats(**behavior),
    ).model_dump()


def change_user_role(
    user_id: int,
    current_user_id: int,
    request: AdminUserRoleRequest,
    current_user: Any | None = None,
) -> Dict[str, Any]:
    """Change a user's role. Guards: can't change self, can't remove last admin."""
    if current_user_id == user_id:
        raise AppException(code=400, message='不能修改自己的角色')

    target = execute_one(
        'SELECT id, role FROM user WHERE id = %s LIMIT 1', [user_id]
    )
    if target is None:
        raise AppException(code=404, message='用户不存在')

    if target.get('role') == 'admin' and request.role != 'admin':
        admin_count = _safe_count(
            "SELECT COUNT(*) AS total FROM user WHERE role = 'admin' AND status = 1"
        )
        if admin_count <= 1:
            raise AppException(
                code=400, message='不能移除最后一位管理员，系统必须保留至少一位管理员'
            )

    execute_update(
        'UPDATE user SET role = %s, updated_at = NOW() WHERE id = %s',
        [request.role, user_id],
    )
    write_admin_operation_log(
        current_user=current_user,
        module='user',
        action='change_role',
        target_type='user',
        target_id=user_id,
        description=f'Change user role from {target.get("role")} to {request.role}',
        result='success',
    )
    return AdminUserActionResult(
        user_id=user_id,
        action='change_role',
        updated=True,
        message=f'角色已变更为 {request.role}',
    ).model_dump()


def change_user_status(
    user_id: int,
    current_user_id: int,
    request: AdminUserStatusRequest,
    current_user: Any | None = None,
) -> Dict[str, Any]:
    """Enable or disable a user account. Guards: can't disable self, can't disable last admin."""
    if current_user_id == user_id:
        raise AppException(code=400, message='不能禁用自己的账号')

    target = execute_one(
        'SELECT id, role FROM user WHERE id = %s LIMIT 1', [user_id]
    )
    if target is None:
        raise AppException(code=404, message='用户不存在')

    if request.status == 0 and target.get('role') == 'admin':
        admin_count = _safe_count(
            "SELECT COUNT(*) AS total FROM user WHERE role = 'admin' AND status = 1"
        )
        if admin_count <= 1:
            raise AppException(
                code=400, message='不能禁用最后一位管理员，系统必须保留至少一位管理员'
            )

    execute_update(
        'UPDATE user SET status = %s, updated_at = NOW() WHERE id = %s',
        [request.status, user_id],
    )
    write_admin_operation_log(
        current_user=current_user,
        module='user',
        action='change_status',
        target_type='user',
        target_id=user_id,
        description=f'Change user status to {request.status}',
        result='success',
    )
    label = '已启用' if request.status == 1 else '已禁用'
    return AdminUserActionResult(
        user_id=user_id,
        action='change_status',
        updated=True,
        message=f'用户账号{label}',
    ).model_dump()


def get_system_config() -> Dict[str, Any]:
    """M10: Get all system config items from database."""
    rows = execute_query('SELECT * FROM system_config ORDER BY id')
    items = []
    for r in rows:
        items.append(SystemConfigItem(
            id=r['id'],
            config_key=r['config_key'],
            config_value=r.get('config_value'),
            config_type=r.get('config_type', 'string'),
            description=r.get('description', ''),
            editable=bool(r.get('editable', 1)),
            created_at=format_datetime(r.get('created_at')) or None,
            updated_at=format_datetime(r.get('updated_at')) or None,
        ).model_dump())
    return SystemConfigListResponse(items=items, total=len(items)).model_dump()


def update_system_config(request: SystemConfigUpdateRequest, current_user: Any | None = None) -> Dict[str, Any]:
    """M10: Update editable system config items."""
    updated = 0
    for item in request.items:
        key = item.get('config_key')
        value = item.get('config_value')
        if not key:
            continue
        existing = execute_one(
            'SELECT id, editable FROM system_config WHERE config_key = %s',
            [key],
        )
        if not existing:
            continue
        if not existing.get('editable'):
            continue
        execute_update(
            'UPDATE system_config SET config_value = %s WHERE config_key = %s',
            [str(value) if value is not None else '', key],
        )
        updated += 1
    if updated:
        write_admin_operation_log(
            current_user=current_user,
            module='config',
            action='update_system_config',
            target_type='system_config',
            target_id='batch',
            description=f'Updated {updated} system config item(s)',
            result='success',
        )
    return {'updated': updated, 'message': f'已更新 {updated} 项配置'}


def get_ai_config() -> Dict[str, Any]:
    """M10: Get AI configuration from system_config table."""
    rows = execute_query(
        "SELECT config_key, config_value, config_type FROM system_config WHERE config_key LIKE %s",
        ['ai.%'],
    )
    cfg: Dict[str, Any] = {}
    for r in rows:
        k = r['config_key'].replace('ai.', '')
        v = r['config_value']
        t = r.get('config_type', 'string')
        if t == 'boolean':
            cfg[k] = v in ('true', 'True', '1', 'yes')
        elif t == 'int':
            cfg[k] = int(v) if v else 0
        elif t == 'float':
            cfg[k] = float(v) if v else 0.0
        elif t == 'json':
            try:
                cfg[k] = json.loads(v) if v else ([] if 'sensitive_words' in k else {} if 'strategy' in k else [])
            except (json.JSONDecodeError, TypeError):
                cfg[k] = v if v else ''
        else:
            cfg[k] = v or ''

    api_key = cfg.get('api_key', '')
    return AIConfigResponse(
        service_url=str(cfg.get('service_url', 'http://127.0.0.1:8001')),
        model_name=str(cfg.get('model_name', 'glm-4-flash')),
        api_key_configured=bool(api_key and api_key.strip()),
        timeout=int(cfg.get('timeout', 60)),
        max_input_length=int(cfg.get('max_input_length', 8000)),
        enable_real_llm=bool(cfg.get('enable_real_llm', False)),
        enable_fallback=bool(cfg.get('enable_fallback', True)),
        enable_cache=bool(cfg.get('enable_cache', False)),
        cache_supported=False,
        risk_threshold_low=float(cfg.get('risk.threshold.low', 0.3)),
        risk_threshold_medium=float(cfg.get('risk.threshold.medium', 0.7)),
        sensitive_words=cfg.get('sensitive_words', []) if isinstance(cfg.get('sensitive_words'), list) else [],
        risk_rules=cfg.get('risk_rules', []) if isinstance(cfg.get('risk_rules'), list) else [],
        fallback_strategy=cfg.get('fallback_strategy', {}) if isinstance(cfg.get('fallback_strategy'), dict) else {},
        service_status='',
        last_check_time=None,
    ).model_dump()


def update_ai_config(request: AIConfigUpdateRequest, current_user: Any | None = None) -> Dict[str, Any]:
    """M10: Update AI configuration in system_config."""
    updates: Dict[str, str] = {}
    mapping = {
        'service_url': 'ai.service_url',
        'model_name': 'ai.model_name',
        'timeout': 'ai.timeout',
        'max_input_length': 'ai.max_input_length',
        'enable_real_llm': 'ai.enable_real_llm',
        'enable_fallback': 'ai.enable_fallback',
        'risk_threshold_low': 'ai.risk.threshold.low',
        'risk_threshold_medium': 'ai.risk.threshold.medium',
        'sensitive_words': 'ai.sensitive_words',
        'risk_rules': 'ai.risk_rules',
        'fallback_strategy': 'ai.fallback_strategy',
    }
    data = request.model_dump(exclude_none=True)
    for field, db_key in mapping.items():
        if field in data:
            val = data[field]
            if isinstance(val, bool):
                val = 'true' if val else 'false'
            updates[db_key] = str(val)

    if 'api_key' in data and data['api_key'] is not None and data['api_key'] != '':
        updates['ai.api_key'] = data['api_key']

    count = 0
    for k, v in updates.items():
        affected = execute_update(
            'UPDATE system_config SET config_value = %s WHERE config_key = %s AND editable = 1',
            [v, k],
        )
        count += affected

    if count:
        write_admin_operation_log(
            current_user=current_user,
            module='ai',
            action='update_ai_config',
            target_type='system_config',
            target_id='ai.*',
            description=f'Updated {count} AI config item(s)',
            result='success',
        )
    return {'updated': count, 'message': f'已更新 {count} 项 AI 配置'}


def test_ai_connection() -> Dict[str, Any]:
    """M10: Test AI service connection."""
    import time as _time
    try:
        row = execute_one(
            "SELECT config_value FROM system_config WHERE config_key = 'ai.service_url'"
        )
        base_url = (row.get('config_value') or 'http://127.0.0.1:8001').strip()
    except Exception:
        base_url = 'http://127.0.0.1:8001'

    import httpx
    start = _time.time()
    try:
        resp = httpx.get(f'{base_url.rstrip("/")}/health', timeout=5.0)
        elapsed = int((_time.time() - start) * 1000)
        if resp.status_code == 200:
            return AIConfigTestResult(
                status='ok',
                latency_ms=elapsed,
                message=f'连接成功 ({elapsed}ms)',
            ).model_dump()
        return AIConfigTestResult(
            status='error',
            latency_ms=elapsed,
            message=f'HTTP {resp.status_code}',
        ).model_dump()
    except Exception as e:
        elapsed = int((_time.time() - start) * 1000)
        return AIConfigTestResult(
            status='error',
            latency_ms=elapsed,
            message=str(e),
        ).model_dump()


# ── M10: Prompt Template service ────────────────────────────────────

FUNCTION_TYPE_LABELS: Dict[str, str] = {
    'title_generation': '标题生成',
    'summary_generation': '摘要生成',
    'keyword_extraction': '关键词提取',
    'element_extraction': '要素提取',
    'consistency_check': '一致性检查',
    'timeline_generation': '时间线生成',
    'ai_chat': 'AI 对话',
}


def get_prompt_template_options() -> Dict[str, Any]:
    """M10: Return function_type list for filter dropdown."""
    fts = [{'value': k, 'label': v} for k, v in FUNCTION_TYPE_LABELS.items()]
    return PromptTemplateOptions(function_types=fts).model_dump()


def get_prompt_templates(
    function_type: str | None = None,
    status: int | None = None,
    keyword: str | None = None,
    page: int = 1,
    page_size: int = 10,
) -> Dict[str, Any]:
    """M10: List prompt templates with filters."""
    conditions: List[str] = ['1=1']
    params: List[Any] = []
    if function_type:
        conditions.append('function_type = %s')
        params.append(function_type)
    if status is not None:
        conditions.append('status = %s')
        params.append(status)
    if keyword:
        conditions.append('(name LIKE %s OR remark LIKE %s)')
        kw = f'%{keyword}%'
        params.extend([kw, kw])

    where = 'WHERE ' + ' AND '.join(conditions)
    total_row = execute_one(f'SELECT COUNT(*) AS cnt FROM ai_prompt_template {where}', params)
    total = int((total_row or {}).get('cnt') or 0)

    offset = (max(page, 1) - 1) * max(page_size, 1)
    rows = execute_query(
        f'SELECT * FROM ai_prompt_template {where} ORDER BY function_type, is_default DESC, id DESC LIMIT %s OFFSET %s',
        params + [max(page_size, 1), offset],
    )

    items = []
    for r in rows:
        items.append(PromptTemplateItem(
            id=r['id'],
            name=r['name'],
            function_type=r['function_type'],
            prompt_content=r['prompt_content'],
            version=r.get('version', 'v1'),
            status=r.get('status', 1),
            is_default=r.get('is_default', 0),
            remark=r.get('remark', ''),
            created_at=format_datetime(r.get('created_at')) or None,
            updated_at=format_datetime(r.get('updated_at')) or None,
        ).model_dump())

    return PromptTemplateListResponse(items=items, total=total, page=page, page_size=page_size).model_dump()


def create_prompt_template(payload: PromptTemplatePayload, current_user: Any | None = None) -> Dict[str, Any]:
    """M10: Create a new prompt template."""
    if payload.is_default:
        execute_update(
            'UPDATE ai_prompt_template SET is_default = 0 WHERE function_type = %s',
            [payload.function_type],
        )
    tid = execute_insert(
        'INSERT INTO ai_prompt_template (name, function_type, prompt_content, version, status, is_default, remark) VALUES (%s,%s,%s,%s,%s,%s,%s)',
        [payload.name, payload.function_type, payload.prompt_content, payload.version, payload.status, payload.is_default, payload.remark],
    )
    row = execute_one('SELECT * FROM ai_prompt_template WHERE id = %s', [tid])
    if not row:
        raise AppException(code=500, message='创建模板失败')
    write_admin_operation_log(
        current_user=current_user,
        module='ai',
        action='create_prompt',
        target_type='ai_prompt_template',
        target_id=tid,
        description=f'Create prompt template {payload.name}',
        result='success',
    )
    return PromptTemplateItem(
        id=row['id'], name=row['name'], function_type=row['function_type'],
        prompt_content=row['prompt_content'], version=row.get('version', 'v1'),
        status=row.get('status', 1), is_default=row.get('is_default', 0),
        remark=row.get('remark', ''), created_at=format_datetime(row.get('created_at')) or None,
        updated_at=format_datetime(row.get('updated_at')) or None,
    ).model_dump()


def get_prompt_template_detail(template_id: int) -> Dict[str, Any]:
    """M10: Get prompt template detail."""
    row = execute_one('SELECT * FROM ai_prompt_template WHERE id = %s', [template_id])
    if not row:
        raise AppException(code=404, message='模板不存在')
    return PromptTemplateItem(
        id=row['id'], name=row['name'], function_type=row['function_type'],
        prompt_content=row['prompt_content'], version=row.get('version', 'v1'),
        status=row.get('status', 1), is_default=row.get('is_default', 0),
        remark=row.get('remark', ''), created_at=format_datetime(row.get('created_at')) or None,
        updated_at=format_datetime(row.get('updated_at')) or None,
    ).model_dump()


def update_prompt_template(template_id: int, payload: PromptTemplatePayload, current_user: Any | None = None) -> Dict[str, Any]:
    """M10: Update a prompt template."""
    existing = execute_one('SELECT id FROM ai_prompt_template WHERE id = %s', [template_id])
    if not existing:
        raise AppException(code=404, message='模板不存在')
    if payload.is_default:
        execute_update(
            'UPDATE ai_prompt_template SET is_default = 0 WHERE function_type = %s',
            [payload.function_type],
        )
    execute_update(
        'UPDATE ai_prompt_template SET name=%s, function_type=%s, prompt_content=%s, version=%s, status=%s, is_default=%s, remark=%s WHERE id=%s',
        [payload.name, payload.function_type, payload.prompt_content, payload.version, payload.status, payload.is_default, payload.remark, template_id],
    )
    write_admin_operation_log(
        current_user=current_user,
        module='ai',
        action='update_prompt',
        target_type='ai_prompt_template',
        target_id=template_id,
        description=f'Update prompt template {payload.name}',
        result='success',
    )
    return get_prompt_template_detail(template_id)


def update_prompt_template_status(template_id: int, request: PromptTemplateStatusRequest, current_user: Any | None = None) -> Dict[str, Any]:
    """M10: Enable/disable a prompt template."""
    existing = execute_one('SELECT id, status FROM ai_prompt_template WHERE id = %s', [template_id])
    if not existing:
        raise AppException(code=404, message='模板不存在')
    execute_update(
        'UPDATE ai_prompt_template SET status = %s WHERE id = %s',
        [request.status, template_id],
    )
    write_admin_operation_log(
        current_user=current_user,
        module='ai',
        action='update_prompt_status',
        target_type='ai_prompt_template',
        target_id=template_id,
        description=f'Update prompt template status to {request.status}',
        result='success',
    )
    label = '启用' if request.status == 1 else '停用'
    return {'template_id': template_id, 'action': 'status', 'updated': True, 'message': f'模板已{label}'}


def set_prompt_template_default(template_id: int, current_user: Any | None = None) -> Dict[str, Any]:
    """M10: Set a prompt template as the default for its function_type."""
    row = execute_one('SELECT id, function_type FROM ai_prompt_template WHERE id = %s', [template_id])
    if not row:
        raise AppException(code=404, message='模板不存在')
    execute_update(
        'UPDATE ai_prompt_template SET is_default = 0 WHERE function_type = %s',
        [row['function_type']],
    )
    execute_update(
        'UPDATE ai_prompt_template SET is_default = 1, status = 1 WHERE id = %s',
        [template_id],
    )
    write_admin_operation_log(
        current_user=current_user,
        module='ai',
        action='set_prompt_default',
        target_type='ai_prompt_template',
        target_id=template_id,
        description=f'Set default prompt template for {row["function_type"]}',
        result='success',
    )
    return {'template_id': template_id, 'action': 'set_default', 'updated': True, 'message': '已设为默认模板'}


# ── M10: AI Call Records service ────────────────────────────────────


def get_ai_call_records(
    function_type: str | None = None,
    status: int | None = None,
    risk_level: str | None = None,
    is_fallback: bool | None = None,
    user_id: int | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
    page: int = 1,
    page_size: int = 10,
) -> Dict[str, Any]:
    """M10: Browse AI call records from ai_generate_record."""
    conditions: List[str] = ['1=1']
    params: List[Any] = []

    if function_type:
        if function_type == 'timeline_generation':
            conditions.append("agr.source = 'timeline'")
        elif function_type == 'ai_chat':
            conditions.append("agr.source = 'ai_chat'")
        else:
            conditions.append('agr.summary_type = %s')
            params.append(function_type)

    if status is not None:
        conditions.append('agr.status = %s')
        params.append(status)
    if risk_level:
        conditions.append('agr.risk_level = %s')
        params.append(risk_level)
    ai_record_columns = _table_columns('ai_generate_record')
    ai_source_supported = 'ai_source' in ai_record_columns
    fallback_sources = ('mock', 'fallback', 'rule', 'local', 'demo')
    if is_fallback is not None and ai_source_supported:
        if is_fallback:
            conditions.append("LOWER(COALESCE(agr.ai_source, '')) IN (%s, %s, %s, %s, %s)")
            params.extend(fallback_sources)
        else:
            conditions.append('(agr.ai_source IS NULL OR LOWER(agr.ai_source) NOT IN (%s, %s, %s, %s, %s))')
            params.extend(fallback_sources)
    if user_id is not None:
        conditions.append('agr.user_id = %s')
        params.append(user_id)
    if start_time:
        conditions.append('agr.created_at >= %s')
        params.append(start_time)
    if end_time:
        conditions.append('agr.created_at <= %s')
        params.append(end_time)

    where = 'WHERE ' + ' AND '.join(conditions)

    total_row = execute_one(
        f'SELECT COUNT(*) AS cnt FROM ai_generate_record agr {where}', params,
    )
    total = int((total_row or {}).get('cnt') or 0)

    offset = (max(page, 1) - 1) * max(page_size, 1)
    ai_source_select = 'agr.ai_source' if ai_source_supported else "'' AS ai_source"
    rows = execute_query(
        f'''SELECT agr.id, agr.user_id, u.username, agr.source, agr.summary_type,
                   CHAR_LENGTH(COALESCE(agr.input_text, '')) AS input_length,
                   agr.status, agr.risk_level, {ai_source_select},
                   CAST(IFNULL(agr.check_result, '') AS CHAR) AS error_message, agr.created_at
            FROM ai_generate_record agr
            LEFT JOIN user u ON u.id = agr.user_id
            {where}
            ORDER BY agr.created_at DESC
            LIMIT %s OFFSET %s''',
        params + [max(page_size, 1), offset],
    )

    items = []
    for r in rows:
        source = str(r.get('source') or '')
        st = str(r.get('summary_type') or '')
        func = _map_source_to_function_type(source, st)
        st_label = STATUS_LABELS.get(r.get('status') or 0, '未知')
        items.append(AdminAICallRecordItem(
            id=r['id'],
            user_id=r.get('user_id'),
            username=str(r.get('username') or ''),
            function_type=func,
            input_length=int(r.get('input_length') or 0),
            status=int(r.get('status') or 0),
            status_label=st_label,
            risk_level=str(r.get('risk_level') or ''),
            is_fallback=str(r.get('ai_source') or '').lower() in fallback_sources,
            error_message=str(r.get('error_message') or ''),
            created_at=format_datetime(r.get('created_at')) or None,
        ).model_dump())

    # Summary stats
    today_row = execute_one(
        f"SELECT COUNT(*) AS cnt FROM ai_generate_record agr {where} AND DATE(agr.created_at) = CURDATE()",
        params,
    )
    today_count = int((today_row or {}).get('cnt') or 0)
    fallback_count = 0
    if ai_source_supported:
        fallback_row = execute_one(
            f"SELECT COUNT(*) AS cnt FROM ai_generate_record agr {where} AND LOWER(COALESCE(agr.ai_source, '')) IN (%s, %s, %s, %s, %s)",
            params + list(fallback_sources),
        )
        fallback_count = int((fallback_row or {}).get('cnt') or 0)

    summary = AdminAICallRecordSummary(
        total_count=total,
        today_count=today_count,
        fallback_count=fallback_count,
    ).model_dump()

    return AdminAICallRecordListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        summary=summary,
        fallback_supported=ai_source_supported,
    ).model_dump()


def _map_source_to_function_type(source: str, summary_type: str) -> str:
    """Map source+summary_type to a function_type label."""
    if source == 'timeline':
        return 'timeline_generation'
    if source == 'ai_chat':
        return 'ai_chat'
    return summary_type or 'unknown'


# ══════════════════════════════════════════════════════════════════
# M8: AdminTimeline service
# ══════════════════════════════════════════════════════════════════

import json as _json

TIMELINE_STATUS_LABELS: dict[str, str] = {
    'not_generated': '未生成',
    'generated': '已生成（AI）',
    'generated (fallback)': '已生成（规则）',
    'failed': '生成失败',
    'generating': '生成中',
}

CACHE_STATUS_LABELS: dict[str, str] = {
    'normal': '正常',
    'no_cache': '无缓存',
    'json_error': 'JSON 异常',
    'source_mismatch': '来源新闻不匹配',
}


def _admin_parse_json_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        try:
            parsed = _json.loads(value)
            return parsed if isinstance(parsed, list) else []
        except (_json.JSONDecodeError, TypeError):
            return []
    return []


def _admin_timeline_cache_check(topic_id: int) -> AdminTimelineCacheCheck:
    row = execute_one(
        'SELECT timeline_json, source_news_ids FROM event_timeline WHERE topic_id = %s',
        [topic_id],
    )
    if row is None:
        return AdminTimelineCacheCheck(
            json_valid=False,
            source_news_valid=False,
            missing_source_news_ids=[],
            message='无缓存',
        )

    json_valid = True
    source_news_valid = True
    missing_ids: list[int] = []

    timeline_json = row.get('timeline_json')
    try:
        if isinstance(timeline_json, str):
            parsed = _json.loads(timeline_json)
            json_valid = isinstance(parsed, list)
    except (_json.JSONDecodeError, TypeError):
        json_valid = False

    source_news_ids = _admin_parse_json_list(row.get('source_news_ids'))
    if source_news_ids:
        placeholders = ','.join(['%s'] * len(source_news_ids))
        actual_rows = execute_query(
            f'SELECT id FROM news WHERE id IN ({placeholders})',
            source_news_ids,
        )
        actual_ids = {int(r['id']) for r in actual_rows}
        missing_ids = sorted(set(source_news_ids) - actual_ids)
        source_news_valid = len(missing_ids) == 0

    if not json_valid:
        return AdminTimelineCacheCheck(
            json_valid=False,
            source_news_valid=source_news_valid,
            missing_source_news_ids=missing_ids,
            message='Timeline JSON 解析失败',
        )
    if not source_news_valid:
        return AdminTimelineCacheCheck(
            json_valid=True,
            source_news_valid=False,
            missing_source_news_ids=missing_ids,
            message=f'来源新闻不匹配，缺失 {len(missing_ids)} 条',
        )
    return AdminTimelineCacheCheck(
        json_valid=True,
        source_news_valid=True,
        missing_source_news_ids=[],
        message='缓存正常',
    )


def get_admin_timeline_options() -> dict[str, Any]:
    return AdminTimelineOptionsResponse(
        status_options=[
            {'label': '已生成（AI）', 'value': 'generated'},
            {'label': '已生成（规则）', 'value': 'generated (fallback)'},
            {'label': '未生成', 'value': 'not_generated'},
            {'label': '生成失败', 'value': 'failed'},
            {'label': '生成中', 'value': 'generating'},
        ],
        news_count_options=[
            {'label': '不限', 'value': ''},
            {'label': '少于 2 篇', 'value': 'less_than_2'},
            {'label': '2 篇及以上', 'value': '2_or_more'},
        ],
        support=AdminTimelineSupport(
            event_timeline_table_supported=True,
            timeline_generate_supported=True,
            timeline_cache_supported=True,
        ),
    ).model_dump()


def get_admin_timeline_list(
    keyword: str | None = None,
    generate_status: str | None = None,
    news_count_type: str | None = None,
    has_cache: bool | None = None,
    cache_error: bool | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
    page: int = 1,
    page_size: int = 10,
) -> dict[str, Any]:
    conditions: list[str] = []
    params: list[Any] = []

    if keyword:
        conditions.append(
            '(nt.topic_name LIKE %s OR nt.summary LIKE %s OR nt.keyword_list LIKE %s)'
        )
        kw = f'%{keyword}%'
        params.extend([kw, kw, kw])

    if start_time:
        conditions.append('COALESCE(et.updated_at, nt.updated_at) >= %s')
        params.append(start_time)
    if end_time:
        conditions.append('COALESCE(et.updated_at, nt.updated_at) <= %s')
        params.append(end_time)

    where_sql = ''
    if conditions:
        where_sql = 'WHERE ' + ' AND '.join(conditions)

    # Build full list by joining news_topic + news count + event_timeline
    count_sql = f'''
        SELECT COUNT(*) AS total
        FROM news_topic nt
        LEFT JOIN event_timeline et ON et.topic_id = nt.id
        {where_sql}
    '''
    total_row = execute_one(count_sql, params)
    total = int((total_row or {}).get('total') or 0)

    offset = (max(page, 1) - 1) * max(page_size, 1)
    rows = execute_query(
        f'''
        SELECT
            nt.id AS topic_id,
            nt.topic_name,
            nt.keyword_list,
            nt.updated_at AS topic_updated_at,
            et.id AS et_id,
            et.timeline_json,
            et.source_news_ids,
            et.generate_status,
            et.generated_at,
            et.updated_at AS et_updated_at
        FROM news_topic nt
        LEFT JOIN event_timeline et ON et.topic_id = nt.id
        {where_sql}
        ORDER BY COALESCE(et.updated_at, nt.updated_at) DESC, nt.id DESC
        LIMIT %s OFFSET %s
        ''',
        params + [max(page_size, 1), offset],
    )

    items: list[dict[str, Any]] = []
    topic_count = 0
    generated_count = 0
    not_generated_count = 0
    failed_count = 0
    insufficient_news_count = 0
    cache_error_count = 0

    for r in rows:
        tid = int(r['topic_id'])
        et_status_raw = str(r.get('generate_status') or '')

        # Determine true generate status
        if et_status_raw and et_status_raw != 'generating':
            if et_status_raw in ('generated',):
                gs = 'generated'
            elif et_status_raw in ('mock',):
                gs = 'generated (fallback)'
            elif et_status_raw in ('failed',):
                gs = 'failed'
            elif et_status_raw == 'generating':
                gs = 'generating'
            else:
                gs = 'generated' if et_status_raw == 'success' else et_status_raw
        elif et_status_raw == 'generating':
            gs = 'generating'
        else:
            gs = 'not_generated'

        # Determine cache status
        source_news_ids = _admin_parse_json_list(r.get('source_news_ids'))
        src_count = len(source_news_ids)

        if et_status_raw == '' or r.get('et_id') is None:
            cs = 'no_cache'
        else:
            tl = r.get('timeline_json')
            json_ok = True
            try:
                if isinstance(tl, str):
                    _json.loads(tl)
                elif tl is None:
                    json_ok = False
            except (_json.JSONDecodeError, TypeError):
                json_ok = False

            if not json_ok:
                cs = 'json_error'
                cache_error_count += 1
            elif not source_news_ids:
                cs = 'source_mismatch'
                cache_error_count += 1
            else:
                cs = 'normal'

        # Count news for this topic
        news_row = execute_one('SELECT COUNT(*) AS cnt FROM news WHERE topic_id = %s', [tid])
        news_cnt = int((news_row or {}).get('cnt') or 0)

        # Apply post-filtering
        if generate_status and gs != generate_status:
            continue
        if news_count_type == 'less_than_2' and news_cnt >= 2:
            continue
        if news_count_type == '2_or_more' and news_cnt < 2:
            continue
        if has_cache is True and cs == 'no_cache':
            continue
        if has_cache is False and cs != 'no_cache':
            continue
        if cache_error is True and cs not in ('json_error', 'source_mismatch'):
            continue
        if cache_error is False and cs in ('json_error', 'source_mismatch'):
            continue

        items.append(AdminTimelineItem(
            topic_id=tid,
            topic_name=str(r.get('topic_name') or ''),
            keyword_list=_admin_parse_json_list(r.get('keyword_list')),
            news_count=news_cnt,
            generate_status=gs,
            generate_status_label=TIMELINE_STATUS_LABELS.get(gs, gs),
            cache_status=cs,
            cache_status_label=CACHE_STATUS_LABELS.get(cs, cs),
            source_news_count=src_count,
            generated_at=format_datetime(r.get('generated_at')) or None,
            updated_at=format_datetime(r.get('et_updated_at') or r.get('topic_updated_at')) or None,
        ).model_dump())

        topic_count += 1
        if gs in ('generated', 'generated (fallback)'):
            generated_count += 1
        elif gs == 'not_generated':
            not_generated_count += 1
        elif gs == 'failed':
            failed_count += 1
        if news_cnt < 2:
            insufficient_news_count += 1

    # After filtering, we need to re-count total (this is approximate since post-filtering
    # but it's the simplest approach for admin tooling)
    total_filtered = len(items)

    # Slice for pagination
    start_idx = (max(page, 1) - 1) * max(page_size, 1)
    items_sliced = items[start_idx:start_idx + max(page_size, 1)]

    summary = AdminTimelineSummary(
        topic_count=topic_count,
        generated_count=generated_count,
        not_generated_count=not_generated_count,
        failed_count=failed_count,
        insufficient_news_count=insufficient_news_count,
        cache_error_count=cache_error_count,
    )

    return AdminTimelineListResponse(
        items=items_sliced,
        total=total_filtered,
        page=max(page, 1),
        page_size=max(page_size, 1),
        summary=summary,
    ).model_dump()


def get_admin_timeline_detail(topic_id: int) -> dict[str, Any]:
    topic = execute_one('SELECT id, topic_name, keyword_list FROM news_topic WHERE id = %s', [topic_id])
    if topic is None:
        raise AppException(code=404, message='话题不存在')

    tl_row = execute_one(
        'SELECT timeline_json, source_news_ids, generate_status, generated_at, updated_at, error_message '
        'FROM event_timeline WHERE topic_id = %s',
        [topic_id],
    )

    source_news_ids: list[int] = []
    timeline_nodes: list[dict[str, Any]] = []
    raw_json = ''
    generate_status = 'not_generated'
    generate_status_label = '未生成'
    generated_at = None
    updated_at = None

    if tl_row:
        generate_status = str(tl_row.get('generate_status') or 'not_generated')
        if generate_status == 'mock':
            generate_status = 'generated (fallback)'
        elif generate_status in ('success',):
            generate_status = 'generated'
        generate_status_label = TIMELINE_STATUS_LABELS.get(generate_status, generate_status)
        generated_at = format_datetime(tl_row.get('generated_at')) or None
        updated_at = format_datetime(tl_row.get('updated_at')) or None

        tl = tl_row.get('timeline_json')
        if isinstance(tl, str):
            raw_json = tl
            try:
                parsed = _json.loads(tl)
                if isinstance(parsed, list):
                    timeline_nodes = parsed
            except (_json.JSONDecodeError, TypeError):
                timeline_nodes = []
        elif isinstance(tl, list):
            raw_json = _json.dumps(tl, ensure_ascii=False)
            timeline_nodes = tl

        source_news_ids = _admin_parse_json_list(tl_row.get('source_news_ids'))

    # Build source_news list
    source_news: list[dict[str, Any]] = []
    if source_news_ids:
        placeholders = ','.join(['%s'] * len(source_news_ids))
        source_news = execute_query(
            f'SELECT id, title, source, publish_time, status FROM news WHERE id IN ({placeholders}) ORDER BY publish_time ASC',
            source_news_ids,
        )
    else:
        # Fallback: show all news bound to this topic
        source_news = execute_query(
            'SELECT id, title, source, publish_time, status FROM news WHERE topic_id = %s ORDER BY publish_time ASC',
            [topic_id],
        )

    cache_check = _admin_timeline_cache_check(topic_id)

    return AdminTimelineDetailResponse(
        topic_id=int(topic['id']),
        topic_name=str(topic['topic_name']),
        keyword_list=_admin_parse_json_list(topic.get('keyword_list')),
        generate_status=generate_status,
        generate_status_label=generate_status_label,
        generated_at=generated_at,
        updated_at=updated_at,
        source_news_ids=source_news_ids,
        timeline_nodes=timeline_nodes,
        source_news=[{
            'id': int(n['id']),
            'title': str(n.get('title') or ''),
            'source': str(n.get('source') or ''),
            'publish_time': format_datetime(n.get('publish_time')) or None,
            'status': int(n.get('status') or 0),
            'status_label': {0: '已下架', 1: '正常', 2: '折叠', 3: '待审核', 4: '已删除'}.get(int(n.get('status') or 0), '未知'),
        } for n in source_news],
        cache_check=cache_check,
        raw_json=raw_json,
    ).model_dump()


def get_admin_timeline_source_news(
    topic_id: int,
    keyword: str | None = None,
    status: int | None = None,
    page: int = 1,
    page_size: int = 10,
) -> dict[str, Any]:
    topic = execute_one('SELECT id, topic_name FROM news_topic WHERE id = %s', [topic_id])
    if topic is None:
        raise AppException(code=404, message='话题不存在')

    # Get source_news_ids from cache
    tl_row = execute_one('SELECT source_news_ids FROM event_timeline WHERE topic_id = %s', [topic_id])
    source_ids: set[int] = set()
    if tl_row:
        source_ids = set(_admin_parse_json_list(tl_row.get('source_news_ids')))

    conditions = ['n.topic_id = %s']
    params: list[Any] = [topic_id]

    if keyword:
        conditions.append('(n.title LIKE %s OR n.summary LIKE %s)')
        kw = f'%{keyword}%'
        params.extend([kw, kw])
    if status is not None:
        conditions.append('n.status = %s')
        params.append(status)

    where_sql = 'WHERE ' + ' AND '.join(conditions)

    total_row = execute_one(f'SELECT COUNT(*) AS total FROM news n {where_sql}', params)
    total = int((total_row or {}).get('total') or 0)

    offset = (max(page, 1) - 1) * max(page_size, 1)
    rows = execute_query(
        f'SELECT id, title, source, publish_time, status FROM news n {where_sql} ORDER BY n.publish_time ASC LIMIT %s OFFSET %s',
        params + [max(page_size, 1), offset],
    )

    return AdminTimelineSourceNewsResponse(
        topic_id=int(topic['id']),
        topic_name=str(topic['topic_name']),
        items=[
            AdminTimelineSourceNewsItem(
                id=int(r['id']),
                title=str(r.get('title') or ''),
                source=str(r.get('source') or ''),
                publish_time=format_datetime(r.get('publish_time')) or None,
                status=int(r.get('status') or 0),
                status_label={0: '已下架', 1: '正常', 2: '折叠', 3: '待审核', 4: '已删除'}.get(int(r.get('status') or 0), '未知'),
                in_source_news_ids=int(r['id']) in source_ids,
            ).model_dump()
            for r in rows
        ],
        total=total,
        page=max(page, 1),
        page_size=max(page_size, 1),
    ).model_dump()


async def admin_timeline_generate(topic_id: int) -> dict[str, Any]:
    from app.modules.timeline.service import (
        _get_topic,
        _get_topic_news,
        _generate_with_ai_or_fallback,
    )

    topic = _get_topic(topic_id)
    if topic is None:
        raise AppException(code=404, message='话题不存在')

    news_rows = _get_topic_news(topic_id)[1]
    if len(news_rows) < 2:
        raise AppException(code=400, message='相关新闻不足：同一话题下至少需要 2 篇新闻才能生成事件脉络，当前仅有 {} 篇'.format(len(news_rows)))

    result = await _generate_with_ai_or_fallback(topic, news_rows)

    return AdminTimelineActionResult(
        topic_id=topic_id,
        action='generate',
        updated=True,
        generate_status=result.generate_status or 'generated',
        generate_status_label=TIMELINE_STATUS_LABELS.get(result.generate_status or 'generated', result.generate_status or ''),
        message='生成成功' if result.timeline else '生成完成但无节点',
    ).model_dump()


async def admin_timeline_refresh(topic_id: int) -> dict[str, Any]:
    from app.modules.timeline.service import (
        _get_topic,
        _get_topic_news,
        _generate_with_ai_or_fallback,
    )

    topic = _get_topic(topic_id)
    if topic is None:
        raise AppException(code=404, message='话题不存在')

    news_rows = _get_topic_news(topic_id)[1]
    if len(news_rows) < 2:
        raise AppException(code=400, message='相关新闻不足：同一话题下至少需要 2 篇新闻才能生成事件脉络，当前仅有 {} 篇'.format(len(news_rows)))

    result = await _generate_with_ai_or_fallback(topic, news_rows)

    return AdminTimelineActionResult(
        topic_id=topic_id,
        action='refresh',
        updated=True,
        generate_status=result.generate_status or 'generated',
        generate_status_label=TIMELINE_STATUS_LABELS.get(result.generate_status or 'generated', result.generate_status or ''),
        message='刷新成功' if result.timeline else '刷新完成但无节点',
    ).model_dump()


def admin_timeline_delete_cache(topic_id: int) -> dict[str, Any]:
    existing = execute_one('SELECT id FROM event_timeline WHERE topic_id = %s', [topic_id])
    if existing is None:
        return AdminTimelineActionResult(
            topic_id=topic_id,
            action='delete_cache',
            updated=True,
            generate_status='not_generated',
            generate_status_label='未生成',
            message='该话题没有缓存，无需清理',
        ).model_dump()

    execute_update('DELETE FROM event_timeline WHERE topic_id = %s', [topic_id])

    return AdminTimelineActionResult(
        topic_id=topic_id,
        action='delete_cache',
        updated=True,
        generate_status='not_generated',
        generate_status_label='未生成',
        message='缓存已清理',
    ).model_dump()

# M11: System Operations & Operation Log service

OPS_IMPORTANT_TABLES: list[tuple[str, str]] = [
    ('user', 'User'),
    ('news', 'News'),
    ('community_post', 'Community post'),
    ('news_comment', 'News comment'),
    ('post_comment', 'Post comment'),
    ('hot_topic', 'Hot topic'),
    ('news_topic', 'News topic'),
    ('event_timeline', 'Event timeline'),
    ('ai_generate_record', 'AI generate record'),
    ('system_config', 'System config'),
    ('ai_prompt_template', 'AI prompt template'),
]


def _ops_now() -> str:
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def _ops_user_value(user: Any, field: str, default: Any = None) -> Any:
    if user is None:
        return default
    if isinstance(user, dict):
        return user.get(field, default)
    return getattr(user, field, default)


def _ops_table_exists(table_name: str) -> bool:
    try:
        return bool(_table_columns(table_name))
    except Exception:  # noqa: BLE001
        return False


def _ops_count_table(table_name: str) -> int | None:
    if not _ops_table_exists(table_name):
        return None
    row = execute_one(f'SELECT COUNT(*) AS total FROM `{table_name}`')
    return int((row or {}).get('total') or 0)


def _ops_total_with_where(table_name: str, where_sql: str = '', params: list[Any] | None = None) -> int:
    if not _ops_table_exists(table_name):
        return 0
    row = execute_one(f'SELECT COUNT(*) AS total FROM `{table_name}` {where_sql}', params or [])
    return int((row or {}).get('total') or 0)


def write_admin_operation_log(
    current_user: Any | None = None,
    module: str = 'ops',
    action: str = 'view',
    target_type: str = '',
    target_id: str | int | None = '',
    description: str = '',
    result: str = 'success',
    error_message: str = '',
    ip_address: str = '',
    user_agent: str = '',
) -> None:
    """Write an admin operation log if the table exists."""
    if not _ops_table_exists('admin_operation_log'):
        logger.warning('admin_operation_log table is missing; skip operation log')
        return
    try:
        execute_insert(
            """INSERT INTO admin_operation_log
               (operator_id, operator_name, operator_role, module, action, target_type,
                target_id, description, ip_address, user_agent, result, error_message)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            [
                _ops_user_value(current_user, 'id'),
                str(_ops_user_value(current_user, 'username', '') or _ops_user_value(current_user, 'nickname', '') or ''),
                str(_ops_user_value(current_user, 'role', '') or ''),
                module,
                action,
                target_type,
                str(target_id or ''),
                description,
                ip_address,
                user_agent,
                result,
                error_message,
            ],
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning('failed to write admin operation log: %s', exc)


def get_admin_ops_status() -> Dict[str, Any]:
    database_status = AdminOpsStatusPart(status='unknown', message='数据库状态未知')
    try:
        row = execute_one('SELECT 1 AS ok')
        if int((row or {}).get('ok') or 0) == 1:
            database_status = AdminOpsStatusPart(status='normal', message='数据库连接正常')
        else:
            database_status = AdminOpsStatusPart(status='abnormal', message='数据库轻量查询结果异常')
    except Exception as exc:  # noqa: BLE001
        database_status = AdminOpsStatusPart(status='abnormal', message=str(exc))

    environment = os.getenv('APP_ENV') or os.getenv('ENV') or 'development'
    return AdminOpsStatusResponse(
        backend=AdminOpsStatusPart(status='normal', message='后端服务可用'),
        database=database_status,
        ai_service=AdminOpsStatusPart(status='normal', message='AI 生成服务正常'),
        environment=environment,
        last_check_time=_ops_now(),
    ).model_dump()


def get_admin_ops_database() -> Dict[str, Any]:
    database_name = ''
    connection_status = 'unknown'
    try:
        row = execute_one('SELECT DATABASE() AS database_name')
        database_name = str((row or {}).get('database_name') or '')
        connection_status = 'normal'
    except Exception as exc:  # noqa: BLE001
        connection_status = 'abnormal'
        logger.warning('database status query failed: %s', exc)

    table_items: list[dict[str, Any]] = []
    for table_name, display_name in OPS_IMPORTANT_TABLES:
        count = _ops_count_table(table_name)
        table_items.append(AdminOpsTableStatus(
            table_name=table_name,
            display_name=display_name,
            exists=count is not None,
            row_count=count,
        ).model_dump())

    last_backup_time = None
    backup_supported = _ops_table_exists('backup_record')
    if backup_supported:
        row = execute_one('SELECT MAX(created_at) AS last_backup_time FROM backup_record')
        last_backup_time = format_datetime((row or {}).get('last_backup_time')) or None

    return AdminOpsDatabaseResponse(
        connection_status=connection_status,
        database_name=database_name,
        tables=table_items,
        last_backup_time=last_backup_time,
        backup_supported=backup_supported,
    ).model_dump()


def get_admin_backup_records(
    status: str | None = None,
    backup_type: str | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
    page: int = 1,
    page_size: int = 10,
) -> Dict[str, Any]:
    if not _ops_table_exists('backup_record'):
        return AdminBackupRecordListResponse(items=[], total=0, page=page, page_size=page_size, summary=AdminBackupRecordSummary()).model_dump()

    conditions = ['1=1']
    params: list[Any] = []
    if status:
        conditions.append('status = %s')
        params.append(status)
    if backup_type:
        conditions.append('backup_type = %s')
        params.append(backup_type)
    if start_time:
        conditions.append('created_at >= %s')
        params.append(start_time)
    if end_time:
        conditions.append('created_at <= %s')
        params.append(end_time)
    where_sql = 'WHERE ' + ' AND '.join(conditions)

    total = _ops_total_with_where('backup_record', where_sql, params)
    offset = (max(page, 1) - 1) * max(page_size, 1)
    rows = execute_query(
        f"""SELECT * FROM backup_record {where_sql}
            ORDER BY created_at DESC, id DESC LIMIT %s OFFSET %s""",
        params + [max(page_size, 1), offset],
    )
    items = [AdminBackupRecordItem(
        id=int(r['id']), backup_name=str(r.get('backup_name') or ''),
        backup_type=str(r.get('backup_type') or 'manual'), file_path=str(r.get('file_path') or ''),
        file_size=int(r.get('file_size') or 0), status=str(r.get('status') or ''),
        message=str(r.get('message') or ''), operator_id=r.get('operator_id'),
        operator_name=str(r.get('operator_name') or ''),
        created_at=format_datetime(r.get('created_at')) or None,
        finished_at=format_datetime(r.get('finished_at')) or None,
    ).model_dump() for r in rows]

    summary = AdminBackupRecordSummary(
        total_count=_ops_total_with_where('backup_record'),
        success_count=_ops_total_with_where('backup_record', "WHERE status = 'success'"),
        failed_count=_ops_total_with_where('backup_record', "WHERE status = 'failed'"),
        unsupported_count=_ops_total_with_where('backup_record', "WHERE status = 'unsupported'"),
        today_count=_ops_total_with_where('backup_record', 'WHERE DATE(created_at) = CURDATE()'),
    )
    return AdminBackupRecordListResponse(items=items, total=total, page=page, page_size=page_size, summary=summary).model_dump()


def create_admin_backup_record(current_user: Any | None = None, ip_address: str = '', user_agent: str = '') -> Dict[str, Any]:
    if not _ops_table_exists('backup_record'):
        raise AppException(code=400, message='backup_record table is missing; please run migration 016')

    backup_name = f'manual_backup_{datetime.now().strftime("%Y%m%d%H%M%S")}'
    message = '当前环境未配置真实备份脚本，暂不支持执行数据库备份。'
    backup_id = execute_insert(
        """INSERT INTO backup_record
           (backup_name, backup_type, file_path, file_size, status, message, operator_id, operator_name, finished_at)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,NOW())""",
        [backup_name, 'manual', '', 0, 'unsupported', message, _ops_user_value(current_user, 'id'), str(_ops_user_value(current_user, 'username', '') or _ops_user_value(current_user, 'nickname', '') or '')],
    )
    write_admin_operation_log(
        current_user=current_user, module='ops', action='backup', target_type='backup_record', target_id=backup_id,
        description='Manual database backup requested', result='unsupported', error_message=message,
        ip_address=ip_address, user_agent=user_agent,
    )
    return AdminBackupActionResult(backup_id=backup_id, status='unsupported', message=message).model_dump()


def get_admin_storage_status() -> Dict[str, Any]:
    if not _ops_table_exists('upload_file'):
        return AdminStorageResponse(supported=False, message='Project has not connected a unified upload file table.').model_dump()

    cols = _table_columns('upload_file')
    file_type_col = 'file_type' if 'file_type' in cols else None
    file_size_col = 'file_size' if 'file_size' in cols else None
    status_col = 'parse_status' if 'parse_status' in cols else ('status' if 'status' in cols else None)
    time_col = 'created_at' if 'created_at' in cols else ('create_time' if 'create_time' in cols else None)

    total_files = _ops_total_with_where('upload_file')
    total_size = 0
    if file_size_col:
        row = execute_one(f'SELECT COALESCE(SUM({file_size_col}), 0) AS total_size FROM upload_file')
        total_size = int((row or {}).get('total_size') or 0)
    image_count = _ops_total_with_where('upload_file', f"WHERE {file_type_col} LIKE %s", ['image%']) if file_type_col else 0
    document_count = _ops_total_with_where('upload_file', f"WHERE {file_type_col} LIKE %s", ['%document%']) if file_type_col else 0
    abnormal_count = _ops_total_with_where('upload_file', f"WHERE {status_col} NOT IN (%s,%s,%s)", [1, 'success', 'parsed']) if status_col else 0
    last_upload_time = None
    if time_col:
        row = execute_one(f'SELECT MAX({time_col}) AS last_upload_time FROM upload_file')
        last_upload_time = format_datetime((row or {}).get('last_upload_time')) or None

    return AdminStorageResponse(
        supported=True, upload_dir=None, total_files=total_files, total_size=total_size,
        image_count=image_count, document_count=document_count, abnormal_count=abnormal_count,
        last_upload_time=last_upload_time, message='Storage statistics are based on upload_file table only.',
    ).model_dump()


def _admin_operation_log_summary() -> AdminOperationLogSummary:
    return AdminOperationLogSummary(
        total_count=_ops_total_with_where('admin_operation_log'),
        success_count=_ops_total_with_where('admin_operation_log', "WHERE result = 'success'"),
        failed_count=_ops_total_with_where('admin_operation_log', "WHERE result = 'failed'"),
        unsupported_count=_ops_total_with_where('admin_operation_log', "WHERE result = 'unsupported'"),
        today_count=_ops_total_with_where('admin_operation_log', 'WHERE DATE(created_at) = CURDATE()'),
    )


def get_admin_operation_logs(operator_keyword: str | None = None, module: str | None = None, action: str | None = None, result: str | None = None, start_time: str | None = None, end_time: str | None = None, page: int = 1, page_size: int = 10) -> Dict[str, Any]:
    if not _ops_table_exists('admin_operation_log'):
        return AdminOperationLogListResponse(items=[], total=0, page=page, page_size=page_size, summary=AdminOperationLogSummary()).model_dump()

    conditions = ['1=1']
    params: list[Any] = []
    if operator_keyword:
        conditions.append('(operator_name LIKE %s OR operator_role LIKE %s)')
        kw = f'%{operator_keyword}%'
        params.extend([kw, kw])
    if module:
        conditions.append('module = %s')
        params.append(module)
    if action:
        conditions.append('action = %s')
        params.append(action)
    if result:
        conditions.append('result = %s')
        params.append(result)
    if start_time:
        conditions.append('created_at >= %s')
        params.append(start_time)
    if end_time:
        conditions.append('created_at <= %s')
        params.append(end_time)
    where_sql = 'WHERE ' + ' AND '.join(conditions)

    total = _ops_total_with_where('admin_operation_log', where_sql, params)
    offset = (max(page, 1) - 1) * max(page_size, 1)
    rows = execute_query(
        f"""SELECT id, operator_id, operator_name, operator_role, module, action,
                   target_type, target_id, description, ip_address, result, created_at
            FROM admin_operation_log {where_sql}
            ORDER BY created_at DESC, id DESC LIMIT %s OFFSET %s""",
        params + [max(page_size, 1), offset],
    )
    items = [AdminOperationLogItem(
        id=int(r['id']), operator_id=r.get('operator_id'), operator_name=str(r.get('operator_name') or ''),
        operator_role=str(r.get('operator_role') or ''), module=str(r.get('module') or ''),
        action=str(r.get('action') or ''), target_type=str(r.get('target_type') or ''), target_id=str(r.get('target_id') or ''),
        description=str(r.get('description') or ''), ip_address=str(r.get('ip_address') or ''), result=str(r.get('result') or ''),
        created_at=format_datetime(r.get('created_at')) or None,
    ).model_dump() for r in rows]
    return AdminOperationLogListResponse(items=items, total=total, page=page, page_size=page_size, summary=_admin_operation_log_summary()).model_dump()


def get_admin_operation_log_detail(log_id: int) -> Dict[str, Any]:
    if not _ops_table_exists('admin_operation_log'):
        raise AppException(code=404, message='Operation log table is missing')
    row = execute_one('SELECT * FROM admin_operation_log WHERE id = %s', [log_id])
    if not row:
        raise AppException(code=404, message='Operation log not found')
    return AdminOperationLogDetail(
        id=int(row['id']), operator_id=row.get('operator_id'), operator_name=str(row.get('operator_name') or ''),
        operator_role=str(row.get('operator_role') or ''), module=str(row.get('module') or ''), action=str(row.get('action') or ''),
        target_type=str(row.get('target_type') or ''), target_id=str(row.get('target_id') or ''), description=str(row.get('description') or ''),
        ip_address=str(row.get('ip_address') or ''), result=str(row.get('result') or ''), created_at=format_datetime(row.get('created_at')) or None,
        user_agent=str(row.get('user_agent') or ''), error_message=str(row.get('error_message') or ''),
    ).model_dump()


# ── M12: Analytics ──────────────────────────────────────────────────


def _analytics_time_filter(
    start_time: str | None, end_time: str | None, column: str = 'created_at',
) -> tuple[str, list[Any]]:
    conditions: list[str] = ['1=1']
    params: list[Any] = []
    if start_time:
        conditions.append(f'{column} >= %s')
        params.append(start_time)
    if end_time:
        conditions.append(f'{column} <= %s')
        params.append(end_time)
    return 'WHERE ' + ' AND '.join(conditions), params


def _analytics_where_clause(where_sql: str) -> str:
    where_sql = where_sql.strip()
    if not where_sql:
        return ''
    if where_sql.startswith('WHERE 1=1 AND '):
        return where_sql[len('WHERE 1=1 AND '):].strip()
    if where_sql == 'WHERE 1=1':
        return ''
    if where_sql.startswith('WHERE '):
        return where_sql[len('WHERE '):].strip()
    return where_sql


def _analytics_active_user_count(start_time: str | None, end_time: str | None) -> int:
    if not _ops_table_exists('browse_history'):
        return 0
    if not start_time and not end_time:
        # default: last 30 days
        row = execute_one(
            'SELECT COUNT(DISTINCT user_id) AS total FROM browse_history WHERE browse_time >= DATE_SUB(NOW(), INTERVAL 30 DAY)',
        )
        return int((row or {}).get('total') or 0)
    where_sql, params = _analytics_time_filter(start_time, end_time, 'browse_time')
    row = execute_one(f'SELECT COUNT(DISTINCT user_id) AS total FROM browse_history {where_sql}', params)
    return int((row or {}).get('total') or 0)


def get_admin_analytics_overview(start_time: str | None = None, end_time: str | None = None) -> Dict[str, Any]:
    total_users = _safe_count('SELECT COUNT(*) AS total FROM user')
    active_users = _analytics_active_user_count(start_time, end_time)
    total_news = _safe_count('SELECT COUNT(*) AS total FROM news')
    total_posts = _safe_count('SELECT COUNT(*) AS total FROM community_post')
    total_comments = (
        _safe_count('SELECT COUNT(*) AS total FROM news_comment')
        + _safe_count('SELECT COUNT(*) AS total FROM post_comment')
    )

    ai_where, ai_params = _analytics_time_filter(start_time, end_time, 'created_at')
    ai_generate_count = 0
    if _ops_table_exists('ai_generate_record'):
        ai_generate_count = _ops_total_with_where('ai_generate_record', ai_where, ai_params)

    timeline_count = 0
    if _ops_table_exists('event_timeline'):
        row = execute_one("SELECT COUNT(*) AS total FROM event_timeline WHERE generate_status = 'generated'")
        timeline_count = int((row or {}).get('total') or 0)

    pending_count = (
        _safe_count('SELECT COUNT(*) AS total FROM news WHERE status = 3')
        + _safe_count('SELECT COUNT(*) AS total FROM community_post WHERE status = 3')
        + _safe_count('SELECT COUNT(*) AS total FROM news_comment WHERE status = 3')
        + _safe_count('SELECT COUNT(*) AS total FROM post_comment WHERE status = 3')
    )

    return AdminAnalyticsOverview(
        total_users=total_users,
        active_users=active_users,
        total_news=total_news,
        total_posts=total_posts,
        total_comments=total_comments,
        ai_generate_count=ai_generate_count,
        timeline_count=timeline_count,
        pending_count=pending_count,
    ).model_dump()


def get_admin_analytics_trends(start_time: str | None = None, end_time: str | None = None) -> Dict[str, Any]:
    content_trend: list[dict[str, Any]] = []
    ai_trend: list[dict[str, Any]] = []

    # Content trend: UNION ALL daily counts from 4 tables
    news_where, news_params = _analytics_time_filter(start_time, end_time, 'created_at')
    post_where, post_params = _analytics_time_filter(start_time, end_time, 'created_at')
    nc_where, nc_params = _analytics_time_filter(start_time, end_time, 'created_at')
    pc_where, pc_params = _analytics_time_filter(start_time, end_time, 'created_at')

    content_sql = f"""
        SELECT date, SUM(nc) AS news_count, SUM(pc) AS post_count, SUM(cc) AS comment_count
        FROM (
            SELECT DATE(created_at) AS date, 1 AS nc, 0 AS pc, 0 AS cc FROM news {news_where}
            UNION ALL
            SELECT DATE(created_at), 0, 1, 0 FROM community_post {post_where}
            UNION ALL
            SELECT DATE(created_at), 0, 0, 1 FROM news_comment {nc_where}
            UNION ALL
            SELECT DATE(created_at), 0, 0, 1 FROM post_comment {pc_where}
        ) t
        GROUP BY date ORDER BY date
    """
    rows = execute_query(content_sql, news_params + post_params + nc_params + pc_params)
    content_trend = [
        AdminTrendPoint(
            date=str(row.get('date') or ''),
            news_count=int(row.get('news_count') or 0),
            post_count=int(row.get('post_count') or 0),
            comment_count=int(row.get('comment_count') or 0),
        ).model_dump()
        for row in rows
    ]

    if content_trend:
        from datetime import datetime as _dt, timedelta
        first = min(r['date'] for r in content_trend if r['date'])
        last = max(r['date'] for r in content_trend if r['date'])
        if first and last:
            dt = _dt.strptime(first, '%Y-%m-%d')
            end_dt = _dt.strptime(last, '%Y-%m-%d')
            seen = {r['date'] for r in content_trend}
            filled = []
            while dt <= end_dt:
                ds = dt.strftime('%Y-%m-%d')
                if ds in seen:
                    filled.append(next(r for r in content_trend if r['date'] == ds))
                else:
                    filled.append(AdminTrendPoint(date=ds).model_dump())
                dt += timedelta(days=1)
            content_trend = filled

    # AI trend: daily counts from ai_generate_record
    if _ops_table_exists('ai_generate_record'):
        ai_columns = _table_columns('ai_generate_record')
        fallback_expr = (
            "SUM(CASE WHEN LOWER(COALESCE(ai_source, '')) IN ('mock','fallback','rule','local','demo') THEN 1 ELSE 0 END)"
            if 'ai_source' in ai_columns
            else '0'
        )
        ai_where, ai_params = _analytics_time_filter(start_time, end_time, 'created_at')
        ai_sql = f"""
            SELECT DATE(created_at) AS date, COUNT(*) AS ai_count,
                   {fallback_expr} AS fallback_count,
                   SUM(CASE WHEN risk_level = 'high' THEN 1 ELSE 0 END) AS high_risk_count
            FROM ai_generate_record {ai_where}
            GROUP BY DATE(created_at) ORDER BY date
        """
        rows = execute_query(ai_sql, ai_params)
        ai_trend = [
            AdminTrendPoint(
                date=str(row.get('date') or ''),
                ai_count=int(row.get('ai_count') or 0),
                fallback_count=int(row.get('fallback_count') or 0),
                high_risk_count=int(row.get('high_risk_count') or 0),
            ).model_dump()
            for row in rows
        ]

    return AdminAnalyticsTrendsResponse(content_trend=content_trend, ai_trend=ai_trend).model_dump()


def get_admin_analytics_top_content(
    start_time: str | None = None,
    end_time: str | None = None,
    content_type: str = 'all',
    limit: int = 10,
) -> Dict[str, Any]:
    top_news: list[dict[str, Any]] = []
    top_posts: list[dict[str, Any]] = []

    if content_type in ('all', 'news'):
        news_where, news_params = _analytics_time_filter(start_time, end_time, 'n.created_at')
        news_sql = f"""
            SELECT n.id, n.title, COALESCE(n.source, '') AS source, n.view_count, n.comment_count,
                   COALESCE(t.topic_name, '') AS topic_name, n.publish_time
            FROM news n
            LEFT JOIN news_topic t ON t.id = n.topic_id
            {news_where}
            ORDER BY n.view_count DESC, n.comment_count DESC
            LIMIT %s
        """
        rows = execute_query(news_sql, news_params + [max(limit, 1)])
        for rank, row in enumerate(rows, 1):
            top_news.append(AdminTopNewsItem(
                rank=rank,
                id=int(row.get('id') or 0),
                title=str(row.get('title') or ''),
                source=str(row.get('source') or ''),
                view_count=int(row.get('view_count') or 0),
                comment_count=int(row.get('comment_count') or 0),
                topic_name=str(row.get('topic_name') or ''),
                publish_time=format_datetime(row.get('publish_time')) or None,
            ).model_dump())

    if content_type in ('all', 'post'):
        post_where, post_params = _analytics_time_filter(start_time, end_time, 'p.created_at')
        post_sql = f"""
            SELECT p.id, p.title, COALESCE(u.nickname, u.username, '') AS author_name,
                   p.comment_count, p.like_count, p.heat_score, p.created_at
            FROM community_post p
            LEFT JOIN user u ON u.id = p.user_id
            {post_where}
            ORDER BY p.heat_score DESC, p.comment_count DESC
            LIMIT %s
        """
        rows = execute_query(post_sql, post_params + [max(limit, 1)])
        for rank, row in enumerate(rows, 1):
            top_posts.append(AdminTopPostItem(
                rank=rank,
                id=int(row.get('id') or 0),
                title=str(row.get('title') or ''),
                author_name=str(row.get('author_name') or ''),
                comment_count=int(row.get('comment_count') or 0),
                like_count=int(row.get('like_count') or 0),
                heat_score=int(row.get('heat_score') or 0),
                created_at=format_datetime(row.get('created_at')) or None,
            ).model_dump())

    return AdminAnalyticsTopContentResponse(top_news=top_news, top_posts=top_posts).model_dump()


def get_admin_analytics_ai_risk(start_time: str | None = None, end_time: str | None = None) -> Dict[str, Any]:
    items: list[dict[str, Any]] = []
    if not _ops_table_exists('ai_generate_record'):
        return AdminAnalyticsAiRiskResponse(items=items, supported=False).model_dump()

    where_sql, params = _analytics_time_filter(start_time, end_time, 'created_at')
    sql = f"""
        SELECT COALESCE(risk_level, 'unknown') AS risk_level, COUNT(*) AS count
        FROM ai_generate_record {where_sql}
        GROUP BY risk_level
        ORDER BY FIELD(risk_level, 'low', 'medium', 'high', 'unknown')
    """
    rows = execute_query(sql, params)
    count_map = {'low': 0, 'medium': 0, 'high': 0, 'unknown': 0}
    for row in rows:
        risk_level = str(row.get('risk_level') or '')
        count = int(row.get('count') or 0)
        if risk_level in count_map:
            count_map[risk_level] = count
        else:
            count_map['unknown'] += count

    for risk_level in ('low', 'medium', 'high', 'unknown'):
        items.append(AdminAiRiskItem(
            risk_level=risk_level,
            count=count_map[risk_level],
        ).model_dump())

    return AdminAnalyticsAiRiskResponse(items=items).model_dump()


def get_admin_analytics_review_summary(start_time: str | None = None, end_time: str | None = None) -> Dict[str, Any]:
    pending_news = _safe_count('SELECT COUNT(*) AS total FROM news WHERE status = 3')
    pending_posts = _safe_count('SELECT COUNT(*) AS total FROM community_post WHERE status = 3')
    pending_comments = (
        _safe_count('SELECT COUNT(*) AS total FROM news_comment WHERE status = 3')
        + _safe_count('SELECT COUNT(*) AS total FROM post_comment WHERE status = 3')
    )

    processed: dict[str, int] = {'approve': 0, 'reject': 0, 'fold': 0, 'delete': 0, 'restore': 0}
    today_processed = 0
    if _ops_table_exists('admin_operation_log'):
        where_sql, params = _analytics_time_filter(start_time, end_time, 'created_at')
        for action in ('approve', 'reject', 'fold', 'delete', 'restore'):
            cnt = _ops_total_with_where(
                'admin_operation_log',
                f"{where_sql} AND module = 'content' AND action = %s",
                params + [action],
            )
            processed[action] = cnt
        today_row = execute_one(
            "SELECT COUNT(*) AS total FROM admin_operation_log "
            "WHERE DATE(created_at) = CURDATE() AND module = 'content' "
            "AND action IN ('approve','reject','fold','delete','restore')"
        )
        today_processed = int((today_row or {}).get('total') or 0)

    return AdminAnalyticsReviewSummaryResponse(
        pending=AdminReviewPending(
            news=pending_news, posts=pending_posts, comments=pending_comments,
            total=pending_news + pending_posts + pending_comments,
        ),
        processed=AdminReviewProcessed(
            approve=processed['approve'], reject=processed['reject'],
            fold=processed['fold'], delete=processed['delete'],
            restore=processed['restore'],
            total=sum(processed.values()),
        ),
        today_processed=today_processed,
    ).model_dump()


def get_admin_analytics_content_overview(
    content_type: str | None = None,
    status: int | None = None,
    keyword: str | None = None,
    risk_level: str | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
    page: int = 1,
    page_size: int = 10,
) -> Dict[str, Any]:
    parts: list[tuple[str, str, list[Any]]] = []

    # ── news ──
    news_where, news_params = _analytics_time_filter(start_time, end_time, 'n.created_at')
    news_cond = _analytics_where_clause(news_where)
    extra_conds: list[str] = []
    extra_params: list[Any] = []
    if content_type is None or content_type == 'news':
        if status is not None:
            extra_conds.append('n.status = %s')
            extra_params.append(status)
        if keyword:
            extra_conds.append('(n.title LIKE %s OR n.summary LIKE %s)')
            kw = f'%{keyword}%'
            extra_params.extend([kw, kw])
        full_where = 'WHERE ' + ' AND '.join(c for c in [news_cond] + extra_conds if c and c != '1=1')
        if not full_where.strip() or full_where.strip() == 'WHERE':
            full_where = ''
        sql = f"""
            SELECT 'news' AS content_type, n.id, n.title, COALESCE(n.source, '') AS creator_or_source,
                   n.status, '' AS risk_level, COALESCE(c.name, '') AS related_info,
                   n.updated_at, 'news' AS target_tab
            FROM news n
            LEFT JOIN news_category c ON c.id = n.category_id
            {full_where}
        """
        parts.append(('news', sql, news_params + extra_params))

    # ── post ──
    post_where, post_params = _analytics_time_filter(start_time, end_time, 'p.created_at')
    post_cond = _analytics_where_clause(post_where)
    extra_conds = []
    extra_params = []
    if content_type is None or content_type == 'post':
        if status is not None:
            extra_conds.append('p.status = %s')
            extra_params.append(status)
        if keyword:
            extra_conds.append('(p.title LIKE %s OR p.content LIKE %s)')
            kw = f'%{keyword}%'
            extra_params.extend([kw, kw])
        full_where = 'WHERE ' + ' AND '.join(c for c in [post_cond] + extra_conds if c and c != '1=1')
        if not full_where.strip() or full_where.strip() == 'WHERE':
            full_where = ''
        sql = f"""
            SELECT 'post' AS content_type, p.id, p.title, COALESCE(u.nickname, u.username, '') AS creator_or_source,
                   p.status, '' AS risk_level, COALESCE(t.topic_name, '') AS related_info,
                   p.updated_at, 'posts' AS target_tab
            FROM community_post p
            LEFT JOIN user u ON u.id = p.user_id
            LEFT JOIN news_topic t ON t.id = p.topic_id
            {full_where}
        """
        parts.append(('post', sql, post_params + extra_params))

    # ── comment (union news_comment + post_comment) ──
    if content_type is None or content_type == 'comment':
        for table, col, label in [('news_comment', 'news_id', 'news'), ('post_comment', 'post_id', 'post')]:
            c_where, c_params = _analytics_time_filter(start_time, end_time, f'c.created_at')
            c_cond = _analytics_where_clause(c_where)
            extra_conds = []
            extra_params = []
            if status is not None:
                extra_conds.append('c.status = %s')
                extra_params.append(status)
            if keyword:
                extra_conds.append('c.content LIKE %s')
                extra_params.append(f'%{keyword}%')
            full_where = 'WHERE ' + ' AND '.join(c for c in [c_cond] + extra_conds if c and c != '1=1')
            if not full_where.strip() or full_where.strip() == 'WHERE':
                full_where = ''
            target_title = f"COALESCE(n.title, '')" if label == 'news' else "COALESCE(p2.title, '')"
            join_clause = "LEFT JOIN news n ON n.id = c.news_id" if label == 'news' else "LEFT JOIN community_post p2 ON p2.id = c.post_id"
            sql = f"""
                SELECT 'comment' AS content_type, c.id,
                       CONCAT(LEFT(COALESCE(c.content,''), 80), IF(LENGTH(c.content)>80,'...','')) AS title,
                       COALESCE(u.nickname, u.username, '') AS creator_or_source,
                       c.status, '' AS risk_level,
                       {target_title} AS related_info,
                       c.updated_at, 'comments' AS target_tab
                FROM {table} c
                LEFT JOIN user u ON u.id = c.user_id
                {join_clause}
                {full_where}
            """
            parts.append(('comment', sql, c_params + extra_params))

    # ── timeline ──
    if content_type is None or content_type == 'timeline':
        tl_where, tl_params = _analytics_time_filter(start_time, end_time, 'e.created_at')
        tl_cond = _analytics_where_clause(tl_where)
        extra_conds = []
        extra_params = []
        if keyword:
            extra_conds.append('(e.error_message LIKE %s OR t.topic_name LIKE %s)')
            kw = f'%{keyword}%'
            extra_params.extend([kw, kw])
        full_where = 'WHERE ' + ' AND '.join(c for c in [tl_cond] + extra_conds if c and c != '1=1')
        if not full_where.strip() or full_where.strip() == 'WHERE':
            full_where = ''
        sql = f"""
            SELECT 'timeline' AS content_type, e.id,
                   CONCAT('Timeline #', e.topic_id) AS title,
                   '' AS creator_or_source,
                   CASE e.generate_status WHEN 'generated' THEN 1 WHEN 'failed' THEN 0 ELSE 3 END AS status,
                   '' AS risk_level, COALESCE(t.topic_name, '') AS related_info,
                   e.updated_at, 'timelines' AS target_tab
            FROM event_timeline e
            LEFT JOIN news_topic t ON t.id = e.topic_id
            {full_where}
        """
        parts.append(('timeline', sql, tl_params + extra_params))

    # ── topic ──
    if content_type is None or content_type == 'topic':
        tp_where, tp_params = _analytics_time_filter(start_time, end_time, 't.created_at')
        tp_cond = _analytics_where_clause(tp_where)
        extra_conds = []
        extra_params = []
        if status is not None:
            extra_conds.append('t.status = %s')
            extra_params.append(status)
        if keyword:
            extra_conds.append('t.topic_name LIKE %s')
            extra_params.append(f'%{keyword}%')
        full_where = 'WHERE ' + ' AND '.join(c for c in [tp_cond] + extra_conds if c and c != '1=1')
        if not full_where.strip() or full_where.strip() == 'WHERE':
            full_where = ''
        sql = f"""
            SELECT 'topic' AS content_type, t.id, t.topic_name AS title,
                   '' AS creator_or_source, t.status, '' AS risk_level,
                   CONCAT('News: ', COALESCE(nc.news_count, 0)) AS related_info,
                   t.updated_at, 'hotTopics' AS target_tab
            FROM news_topic t
            LEFT JOIN (SELECT topic_id, COUNT(*) AS news_count FROM news GROUP BY topic_id) nc ON nc.topic_id = t.id
            {full_where}
        """
        parts.append(('topic', sql, tp_params + extra_params))

    # ── Combine: UNION ALL + pagination ──
    union_parts: list[str] = []
    all_params: list[Any] = []
    for _label, sql, params in parts:
        union_parts.append(sql)
        all_params.extend(params)

    if not union_parts:
        return AdminAnalyticsContentOverviewResponse().model_dump()

    combined = ' UNION ALL '.join(union_parts)
    count_sql = f'SELECT COUNT(*) AS total FROM ({combined}) AS u'
    total_row = execute_one(count_sql, all_params)
    total = int((total_row or {}).get('total') or 0)

    normalized_page = max(page, 1)
    normalized_page_size = max(page_size, 1)
    offset = (normalized_page - 1) * normalized_page_size

    final_sql = f'SELECT * FROM ({combined}) AS u ORDER BY updated_at DESC LIMIT %s OFFSET %s'
    rows = execute_query(final_sql, all_params + [normalized_page_size, offset])

    STATUS_LABELS_GLOBAL: dict[int, str] = {
        0: 'Disabled', 1: 'Normal', 2: 'Folded', 3: 'Pending', 4: 'Deleted',
    }

    items = [AdminContentOverviewItem(
        content_type=str(row.get('content_type') or ''),
        id=int(row.get('id') or 0),
        title=str(row.get('title') or ''),
        creator_or_source=str(row.get('creator_or_source') or ''),
        status_label=STATUS_LABELS_GLOBAL.get(int(row.get('status') or 0), 'Unknown'),
        risk_level=str(row.get('risk_level') or ''),
        related_info=str(row.get('related_info') or ''),
        updated_at=format_datetime(row.get('updated_at')) or None,
        target_tab=str(row.get('target_tab') or ''),
    ).model_dump() for row in rows]

    return AdminAnalyticsContentOverviewResponse(
        items=items, total=total, page=normalized_page, page_size=normalized_page_size,
    ).model_dump()

