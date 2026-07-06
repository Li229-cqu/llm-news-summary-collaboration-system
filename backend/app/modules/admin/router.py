
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Body, Depends, Query, Request

from app.common.auth import require_admin, require_editor_or_admin
from app.common.response import ApiResponse, success_response
from app.modules.admin.schema import (
    AdminDashboard,
    PendingItemDetail,
    PendingItemsResponse,
    ReviewActionRequest,
    ReviewActionResult,
    AdminNewsListResponse,
    AdminNewsDetail,
    AdminNewsUpdateRequest,
    AdminNewsTopicRequest,
    AdminNewsActionResult,
    AdminNewsOptions,
    AdminPostListResponse,
    AdminPostDetail,
    AdminPostActionResult,
    AdminPostOptions,
    AdminCommentListResponse,
    AdminCommentDetail,
    AdminCommentActionResult,
    AdminCommentOptions,
    AdminCommunityHotRankingResponse,
    AdminHotTopicActionResult,
    AdminHotTopicDetail,
    AdminHotTopicListResponse,
    AdminHotTopicOptions,
    AdminHotTopicRankRequest,
    AdminNewsHotRankingResponse,
    AdminTopicActionResult,
    AdminTopicBindNewsRequest,
    AdminTopicDetail,
    AdminTopicListResponse,
    AdminTopicNewsResponse,
    AdminTopicOptions,
    AdminTopicPayload,
    AdminTopicStatusRequest,
    AdminTimelineActionResult,
    AdminTimelineDetailResponse,
    AdminTimelineListResponse,
    AdminTimelineListParams,
    AdminTimelineOptionsResponse,
    AdminTimelineSourceNewsResponse,
    AdminUserActionResult,
    AdminUserDetail,
    AdminUserListResponse,
    AdminUserOptions,
    AdminUserRoleRequest,
    AdminUserStatusRequest,
    # M10
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
    AdminAICallRecordListResponse,
    # M11
    AdminOpsStatusResponse,
    AdminOpsDatabaseResponse,
    AdminBackupRecordListResponse,
    AdminBackupActionResult,
    AdminStorageResponse,
    AdminOperationLogListResponse,
    AdminOperationLogDetail,
    # M12
    AdminAnalyticsOverview,
    AdminAnalyticsTrendsResponse,
    AdminAnalyticsTopContentResponse,
    AdminAnalyticsAiRiskResponse,
    AdminAnalyticsReviewSummaryResponse,
    AdminAnalyticsContentOverviewResponse,
)
from app.modules.admin.service import (
    get_dashboard,
    get_pending_item_detail,
    get_pending_items,
    get_pending_posts,
    get_system_config,
    update_system_config,
    get_ai_config,
    update_ai_config,
    test_ai_connection,
    get_prompt_template_options,
    get_prompt_templates,
    create_prompt_template,
    get_prompt_template_detail,
    update_prompt_template,
    update_prompt_template_status,
    set_prompt_template_default,
    get_ai_call_records,
    get_users,
    review_pending_item,
    get_admin_news_list,
    get_admin_news_detail,
    update_admin_news,
    update_admin_news_topic,
    set_admin_news_feature,
    review_admin_news,
    get_admin_news_options,
    get_admin_post_list,
    get_admin_post_detail,
    review_admin_post,
    set_admin_post_feature,
    get_admin_post_options,
    get_admin_comment_list,
    get_admin_comment_detail,
    review_admin_comment,
    get_admin_comment_options,
    get_admin_community_hot_ranking,
    get_admin_news_hot_ranking,
    bind_admin_topic_news,
    create_admin_topic,
    get_admin_hot_topic_detail,
    get_admin_hot_topic_list,
    get_admin_hot_topic_options,
    get_admin_topic_candidate_news,
    get_admin_topic_detail,
    get_admin_topic_list,
    get_admin_topic_news,
    get_admin_topic_options,
    refresh_admin_hot_topic_heat,
    set_admin_hot_topic_hidden,
    set_admin_hot_topic_pin,
    unbind_admin_topic_news,
    update_admin_hot_topic_rank,
    update_admin_topic,
    update_admin_topic_status,
    get_admin_timeline_options,
    get_admin_timeline_list,
    get_admin_timeline_detail,
    admin_timeline_generate,
    admin_timeline_refresh,
    admin_timeline_delete_cache,
    get_admin_timeline_source_news,
    get_user_options,
    get_user_detail,
    change_user_role,
    change_user_status,
    # M11
    get_admin_ops_status,
    get_admin_ops_database,
    get_admin_backup_records,
    create_admin_backup_record,
    get_admin_storage_status,
    get_admin_operation_logs,
    get_admin_operation_log_detail,
    # M12
    get_admin_analytics_overview,
    get_admin_analytics_trends,
    get_admin_analytics_top_content,
    get_admin_analytics_ai_risk,
    get_admin_analytics_review_summary,
    get_admin_analytics_content_overview,
)
from app.modules.auth.schema import UserInfo

router = APIRouter(prefix='/api/admin', tags=['admin'])


@router.get('/ping', response_model=ApiResponse[str])
async def ping_admin(_: UserInfo = Depends(require_editor_or_admin)) -> ApiResponse[str]:
    return success_response('admin module ok')


@router.get('/dashboard', response_model=ApiResponse[AdminDashboard])
async def dashboard(
    _: UserInfo = Depends(require_editor_or_admin),
) -> ApiResponse[AdminDashboard]:
    """Get admin dashboard."""
    data = get_dashboard()
    return success_response(data)


# M11: System Operations & Operation Logs


@router.get('/ops/status', response_model=ApiResponse[AdminOpsStatusResponse])
async def admin_ops_status(
    _: UserInfo = Depends(require_admin),
) -> ApiResponse[AdminOpsStatusResponse]:
    data = get_admin_ops_status()
    return success_response(data)


@router.get('/ops/database', response_model=ApiResponse[AdminOpsDatabaseResponse])
async def admin_ops_database(
    _: UserInfo = Depends(require_admin),
) -> ApiResponse[AdminOpsDatabaseResponse]:
    data = get_admin_ops_database()
    return success_response(data)


@router.get('/ops/backups', response_model=ApiResponse[AdminBackupRecordListResponse])
async def admin_ops_backups(
    status: str | None = Query(default=None),
    backup_type: str | None = Query(default=None),
    start_time: str | None = Query(default=None),
    end_time: str | None = Query(default=None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    _: UserInfo = Depends(require_admin),
) -> ApiResponse[AdminBackupRecordListResponse]:
    data = get_admin_backup_records(
        status=status, backup_type=backup_type, start_time=start_time,
        end_time=end_time, page=page, page_size=page_size,
    )
    return success_response(data)


@router.post('/ops/backups', response_model=ApiResponse[AdminBackupActionResult])
async def admin_ops_create_backup(
    request: Request,
    current_user: UserInfo = Depends(require_admin),
) -> ApiResponse[AdminBackupActionResult]:
    data = create_admin_backup_record(
        current_user=current_user,
        ip_address=request.client.host if request.client else '',
        user_agent=request.headers.get('user-agent', ''),
    )
    return success_response(data, message='backup request recorded')


@router.get('/ops/storage', response_model=ApiResponse[AdminStorageResponse])
async def admin_ops_storage(
    _: UserInfo = Depends(require_admin),
) -> ApiResponse[AdminStorageResponse]:
    data = get_admin_storage_status()
    return success_response(data)


@router.get('/ops/logs', response_model=ApiResponse[AdminOperationLogListResponse])
async def admin_ops_logs(
    operator_keyword: str | None = Query(default=None),
    module: str | None = Query(default=None),
    action: str | None = Query(default=None),
    result: str | None = Query(default=None),
    start_time: str | None = Query(default=None),
    end_time: str | None = Query(default=None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    _: UserInfo = Depends(require_admin),
) -> ApiResponse[AdminOperationLogListResponse]:
    data = get_admin_operation_logs(
        operator_keyword=operator_keyword, module=module, action=action,
        result=result, start_time=start_time, end_time=end_time,
        page=page, page_size=page_size,
    )
    return success_response(data)


@router.get('/ops/logs/{log_id}', response_model=ApiResponse[AdminOperationLogDetail])
async def admin_ops_log_detail(
    log_id: int,
    _: UserInfo = Depends(require_admin),
) -> ApiResponse[AdminOperationLogDetail]:
    data = get_admin_operation_log_detail(log_id)
    return success_response(data)


# ── M12: Analytics ──────────────────────────────────────────────────


@router.get('/analytics/overview', response_model=ApiResponse[AdminAnalyticsOverview])
async def admin_analytics_overview(
    start_time: str | None = Query(default=None),
    end_time: str | None = Query(default=None),
    _: UserInfo = Depends(require_admin),
) -> ApiResponse[AdminAnalyticsOverview]:
    data = get_admin_analytics_overview(start_time=start_time, end_time=end_time)
    return success_response(data)


@router.get('/analytics/trends', response_model=ApiResponse[AdminAnalyticsTrendsResponse])
async def admin_analytics_trends(
    start_time: str | None = Query(default=None),
    end_time: str | None = Query(default=None),
    _: UserInfo = Depends(require_admin),
) -> ApiResponse[AdminAnalyticsTrendsResponse]:
    data = get_admin_analytics_trends(start_time=start_time, end_time=end_time)
    return success_response(data)


@router.get('/analytics/top-content', response_model=ApiResponse[AdminAnalyticsTopContentResponse])
async def admin_analytics_top_content(
    start_time: str | None = Query(default=None),
    end_time: str | None = Query(default=None),
    content_type: str = Query('all', alias='type', description='all/news/post'),
    limit: int = Query(10, ge=1, le=50),
    _: UserInfo = Depends(require_admin),
) -> ApiResponse[AdminAnalyticsTopContentResponse]:
    data = get_admin_analytics_top_content(
        start_time=start_time, end_time=end_time, content_type=content_type, limit=limit,
    )
    return success_response(data)


@router.get('/analytics/ai-risk', response_model=ApiResponse[AdminAnalyticsAiRiskResponse])
async def admin_analytics_ai_risk(
    start_time: str | None = Query(default=None),
    end_time: str | None = Query(default=None),
    _: UserInfo = Depends(require_admin),
) -> ApiResponse[AdminAnalyticsAiRiskResponse]:
    data = get_admin_analytics_ai_risk(start_time=start_time, end_time=end_time)
    return success_response(data)


@router.get('/analytics/review-summary', response_model=ApiResponse[AdminAnalyticsReviewSummaryResponse])
async def admin_analytics_review_summary(
    start_time: str | None = Query(default=None),
    end_time: str | None = Query(default=None),
    _: UserInfo = Depends(require_admin),
) -> ApiResponse[AdminAnalyticsReviewSummaryResponse]:
    data = get_admin_analytics_review_summary(start_time=start_time, end_time=end_time)
    return success_response(data)


@router.get('/analytics/content-overview', response_model=ApiResponse[AdminAnalyticsContentOverviewResponse])
async def admin_analytics_content_overview(
    content_type: str | None = Query(default=None, alias='type'),
    status: int | None = Query(default=None),
    keyword: str | None = Query(default=None),
    risk_level: str | None = Query(default=None),
    start_time: str | None = Query(default=None),
    end_time: str | None = Query(default=None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    _: UserInfo = Depends(require_admin),
) -> ApiResponse[AdminAnalyticsContentOverviewResponse]:
    data = get_admin_analytics_content_overview(
        content_type=content_type, status=status, keyword=keyword,
        risk_level=risk_level, start_time=start_time, end_time=end_time,
        page=page, page_size=page_size,
    )
    return success_response(data)


@router.get('/pending-items', response_model=ApiResponse[PendingItemsResponse])
async def pending_items(
    item_type: str = Query('all', alias='type', description='all/news/post/comment'),
    keyword: str | None = Query(default=None, description='Keyword'),
    status: Optional[int] = Query(default=None, ge=0, le=4, description='Status'),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    _: UserInfo = Depends(require_editor_or_admin),
) -> ApiResponse[PendingItemsResponse]:
    data = get_pending_items(item_type=item_type, keyword=keyword, status=status, page=page, page_size=page_size)
    return success_response(data)


@router.get('/pending-items/{item_type}/{item_id}', response_model=ApiResponse[PendingItemDetail])
async def pending_item_detail(
    item_type: str,
    item_id: int,
    _: UserInfo = Depends(require_editor_or_admin),
) -> ApiResponse[PendingItemDetail]:
    data = get_pending_item_detail(item_type, item_id)
    return success_response(data)


@router.post('/pending-items/{item_type}/{item_id}/review', response_model=ApiResponse[ReviewActionResult])
async def review_pending_item_endpoint(
    item_type: str,
    item_id: int,
    request: ReviewActionRequest = Body(...),
    current_user: UserInfo = Depends(require_editor_or_admin),
) -> ApiResponse[ReviewActionResult]:
    data = review_pending_item(item_type, item_id, request, current_user=current_user)
    return success_response(data)


@router.get('/news/options', response_model=ApiResponse[AdminNewsOptions])
async def admin_news_options(
    _: UserInfo = Depends(require_editor_or_admin),
) -> ApiResponse[AdminNewsOptions]:
    data = get_admin_news_options()
    return success_response(data)


@router.get('/news', response_model=ApiResponse[AdminNewsListResponse])
async def admin_news_list(
    keyword: str | None = Query(default=None),
    category_id: Optional[int] = Query(default=None),
    source: str | None = Query(default=None),
    status: Optional[int] = Query(default=None, ge=0, le=4),
    is_featured: Optional[bool] = Query(default=None),
    has_topic: Optional[bool] = Query(default=None),
    start_time: str | None = Query(default=None),
    end_time: str | None = Query(default=None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    _: UserInfo = Depends(require_editor_or_admin),
) -> ApiResponse[AdminNewsListResponse]:
    data = get_admin_news_list(keyword=keyword, category_id=category_id, source=source, status=status, is_featured=is_featured, has_topic=has_topic, start_time=start_time, end_time=end_time, page=page, page_size=page_size)
    return success_response(data)


@router.get('/news/{news_id}', response_model=ApiResponse[AdminNewsDetail])
async def admin_news_detail(news_id: int, _: UserInfo = Depends(require_editor_or_admin)) -> ApiResponse[AdminNewsDetail]:
    data = get_admin_news_detail(news_id)
    return success_response(data)


@router.put('/news/{news_id}', response_model=ApiResponse[AdminNewsDetail])
async def admin_news_update(news_id: int, request: AdminNewsUpdateRequest = Body(...), current_user: UserInfo = Depends(require_editor_or_admin)) -> ApiResponse[AdminNewsDetail]:
    data = update_admin_news(news_id, request, current_user=current_user)
    return success_response(data)


@router.post('/news/{news_id}/review', response_model=ApiResponse[AdminNewsActionResult])
async def admin_news_review(news_id: int, request: ReviewActionRequest = Body(...), current_user: UserInfo = Depends(require_editor_or_admin)) -> ApiResponse[AdminNewsActionResult]:
    data = review_admin_news(news_id, request, current_user=current_user)
    return success_response(data)


@router.post('/news/{news_id}/topic', response_model=ApiResponse[AdminNewsDetail])
async def admin_news_topic(news_id: int, request: AdminNewsTopicRequest = Body(...), current_user: UserInfo = Depends(require_editor_or_admin)) -> ApiResponse[AdminNewsDetail]:
    data = update_admin_news_topic(news_id, request, current_user=current_user)
    return success_response(data)


@router.post('/news/{news_id}/feature', response_model=ApiResponse[AdminNewsActionResult])
async def admin_news_feature(news_id: int, _: UserInfo = Depends(require_editor_or_admin)) -> ApiResponse[AdminNewsActionResult]:
    data = set_admin_news_feature(news_id, True)
    return success_response(data)


@router.delete('/news/{news_id}/feature', response_model=ApiResponse[AdminNewsActionResult])
async def admin_news_unfeature(news_id: int, _: UserInfo = Depends(require_editor_or_admin)) -> ApiResponse[AdminNewsActionResult]:
    data = set_admin_news_feature(news_id, False)
    return success_response(data)


@router.get('/posts/options', response_model=ApiResponse[AdminPostOptions])
async def admin_post_options(
    _: UserInfo = Depends(require_editor_or_admin),
) -> ApiResponse[AdminPostOptions]:
    data = get_admin_post_options()
    return success_response(data)


@router.get('/posts', response_model=ApiResponse[AdminPostListResponse])
async def admin_post_list(
    keyword: str | None = Query(default=None),
    user_id: Optional[int] = Query(default=None),
    username: str | None = Query(default=None),
    status: Optional[int] = Query(default=None, ge=0, le=4),
    tag: str | None = Query(default=None),
    related_news_id: Optional[int] = Query(default=None),
    is_featured: Optional[bool] = Query(default=None),
    start_time: str | None = Query(default=None),
    end_time: str | None = Query(default=None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    _: UserInfo = Depends(require_editor_or_admin),
) -> ApiResponse[AdminPostListResponse]:
    data = get_admin_post_list(
        keyword=keyword, user_id=user_id, username=username, status=status, tag=tag,
        related_news_id=related_news_id, is_featured=is_featured, start_time=start_time,
        end_time=end_time, page=page, page_size=page_size,
    )
    return success_response(data)


@router.get('/posts/{post_id}', response_model=ApiResponse[AdminPostDetail])
async def admin_post_detail(post_id: int, _: UserInfo = Depends(require_editor_or_admin)) -> ApiResponse[AdminPostDetail]:
    data = get_admin_post_detail(post_id)
    return success_response(data)


@router.post('/posts/{post_id}/review', response_model=ApiResponse[AdminPostActionResult])
async def admin_post_review(post_id: int, request: ReviewActionRequest = Body(...), current_user: UserInfo = Depends(require_editor_or_admin)) -> ApiResponse[AdminPostActionResult]:
    data = review_admin_post(post_id, request, current_user=current_user)
    return success_response(data)


@router.post('/posts/{post_id}/feature', response_model=ApiResponse[AdminPostActionResult])
async def admin_post_feature(post_id: int, _: UserInfo = Depends(require_editor_or_admin)) -> ApiResponse[AdminPostActionResult]:
    data = set_admin_post_feature(post_id, True)
    return success_response(data)


@router.delete('/posts/{post_id}/feature', response_model=ApiResponse[AdminPostActionResult])
async def admin_post_unfeature(post_id: int, _: UserInfo = Depends(require_editor_or_admin)) -> ApiResponse[AdminPostActionResult]:
    data = set_admin_post_feature(post_id, False)
    return success_response(data)


@router.get('/comments/options', response_model=ApiResponse[AdminCommentOptions])
async def admin_comment_options(
    _: UserInfo = Depends(require_editor_or_admin),
) -> ApiResponse[AdminCommentOptions]:
    data = get_admin_comment_options()
    return success_response(data)


@router.get('/comments', response_model=ApiResponse[AdminCommentListResponse])
async def admin_comment_list(
    comment_type: str = Query('all', alias='type', description='all/news/post'),
    keyword: str | None = Query(default=None),
    user_id: Optional[int] = Query(default=None),
    username: str | None = Query(default=None),
    status: Optional[int] = Query(default=None, ge=0, le=4),
    news_id: Optional[int] = Query(default=None),
    post_id: Optional[int] = Query(default=None),
    has_parent: Optional[bool] = Query(default=None),
    start_time: str | None = Query(default=None),
    end_time: str | None = Query(default=None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    _: UserInfo = Depends(require_editor_or_admin),
) -> ApiResponse[AdminCommentListResponse]:
    data = get_admin_comment_list(
        comment_type=comment_type, keyword=keyword, user_id=user_id, username=username,
        status=status, news_id=news_id, post_id=post_id, has_parent=has_parent,
        start_time=start_time, end_time=end_time, page=page, page_size=page_size,
    )
    return success_response(data)


@router.get('/comments/{comment_type}/{comment_id}', response_model=ApiResponse[AdminCommentDetail])
async def admin_comment_detail(comment_type: str, comment_id: int, _: UserInfo = Depends(require_editor_or_admin)) -> ApiResponse[AdminCommentDetail]:
    data = get_admin_comment_detail(comment_type, comment_id)
    return success_response(data)


@router.post('/comments/{comment_type}/{comment_id}/review', response_model=ApiResponse[AdminCommentActionResult])
async def admin_comment_review(comment_type: str, comment_id: int, request: ReviewActionRequest = Body(...), current_user: UserInfo = Depends(require_editor_or_admin)) -> ApiResponse[AdminCommentActionResult]:
    data = review_admin_comment(comment_type, comment_id, request, current_user=current_user)
    return success_response(data)


@router.get('/pending-posts', response_model=ApiResponse[dict])
async def pending_posts(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    _: UserInfo = Depends(require_editor_or_admin),
) -> ApiResponse[dict]:
    """Get legacy pending post list."""
    data = get_pending_posts(page=page, page_size=page_size)
    return success_response(data)


# ── M9: User & Permission Management ─────────────────────────────


@router.get('/users/options', response_model=ApiResponse[AdminUserOptions])
async def user_options(
    _: UserInfo = Depends(require_admin),
) -> ApiResponse[AdminUserOptions]:
    """Get user management options (roles, statuses, capability info)."""
    data = get_user_options()
    return success_response(data)


@router.get('/users/{user_id}', response_model=ApiResponse[AdminUserDetail])
async def user_detail(
    user_id: int,
    _: UserInfo = Depends(require_admin),
) -> ApiResponse[AdminUserDetail]:
    """Get user detail with behavior statistics."""
    data = get_user_detail(user_id)
    return success_response(data)


@router.post('/users/{user_id}/role', response_model=ApiResponse[AdminUserActionResult])
async def user_change_role(
    user_id: int,
    request: AdminUserRoleRequest = Body(...),
    current_user: UserInfo = Depends(require_admin),
) -> ApiResponse[AdminUserActionResult]:
    """Change user role. Cannot change own role or remove the last admin."""
    data = change_user_role(user_id, current_user.id, request, current_user=current_user)
    return success_response(data)


@router.post('/users/{user_id}/status', response_model=ApiResponse[AdminUserActionResult])
async def user_change_status(
    user_id: int,
    request: AdminUserStatusRequest = Body(...),
    current_user: UserInfo = Depends(require_admin),
) -> ApiResponse[AdminUserActionResult]:
    """Enable or disable user account. Cannot disable self or the last admin."""
    data = change_user_status(user_id, current_user.id, request, current_user=current_user)
    return success_response(data)


@router.get('/users', response_model=ApiResponse[AdminUserListResponse])
async def users(
    keyword: str | None = Query(default=None),
    role: str | None = Query(default=None),
    status: int | None = Query(default=None),
    start_time: str | None = Query(default=None),
    end_time: str | None = Query(default=None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    _: UserInfo = Depends(require_admin),
) -> ApiResponse[AdminUserListResponse]:
    """Get admin user list with filters and summary."""
    data = get_users(
        keyword=keyword, role=role, status=status,
        start_time=start_time, end_time=end_time,
        page=page, page_size=page_size,
    )
    return success_response(data)


# ── M10: System Config & AI Model Rules ──────────────────────────


@router.get('/system-config', response_model=ApiResponse[SystemConfigListResponse])
async def system_config_list(
    _: UserInfo = Depends(require_admin),
) -> ApiResponse[SystemConfigListResponse]:
    """M10: Get all system config items."""
    data = get_system_config()
    return success_response(data)


@router.put('/system-config', response_model=ApiResponse[dict])
async def system_config_update(
    request: SystemConfigUpdateRequest,
    current_user: UserInfo = Depends(require_admin),
) -> ApiResponse[dict]:
    """M10: Update system config items."""
    data = update_system_config(request, current_user=current_user)
    return success_response(data)


@router.get('/ai-config', response_model=ApiResponse[AIConfigResponse])
async def ai_config(
    _: UserInfo = Depends(require_admin),
) -> ApiResponse[AIConfigResponse]:
    """M10: Get AI configuration."""
    data = get_ai_config()
    return success_response(data)


@router.put('/ai-config', response_model=ApiResponse[dict])
async def ai_config_update(
    request: AIConfigUpdateRequest,
    current_user: UserInfo = Depends(require_admin),
) -> ApiResponse[dict]:
    """M10: Update AI configuration."""
    data = update_ai_config(request, current_user=current_user)
    return success_response(data)


@router.post('/ai-config/test', response_model=ApiResponse[AIConfigTestResult])
async def ai_config_test(
    _: UserInfo = Depends(require_admin),
) -> ApiResponse[AIConfigTestResult]:
    """M10: Test AI service connection."""
    data = test_ai_connection()
    return success_response(data)


# ── M10: Prompt Templates ─────────────────────────────────────────


@router.get('/prompt-templates/options', response_model=ApiResponse[PromptTemplateOptions])
async def prompt_template_options(
    _: UserInfo = Depends(require_admin),
) -> ApiResponse[PromptTemplateOptions]:
    """M10: Get prompt template options (function types)."""
    data = get_prompt_template_options()
    return success_response(data)


@router.get('/prompt-templates', response_model=ApiResponse[PromptTemplateListResponse])
async def prompt_template_list(
    function_type: str | None = Query(default=None),
    status: Optional[int] = Query(default=None),
    keyword: str | None = Query(default=None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    _: UserInfo = Depends(require_admin),
) -> ApiResponse[PromptTemplateListResponse]:
    """M10: List prompt templates."""
    data = get_prompt_templates(
        function_type=function_type, status=status, keyword=keyword,
        page=page, page_size=page_size,
    )
    return success_response(data)


@router.get('/prompt-templates/{template_id}', response_model=ApiResponse[PromptTemplateItem])
async def prompt_template_detail(
    template_id: int,
    _: UserInfo = Depends(require_admin),
) -> ApiResponse[PromptTemplateItem]:
    """M10: Get prompt template detail."""
    data = get_prompt_template_detail(template_id)
    return success_response(data)


@router.post('/prompt-templates', response_model=ApiResponse[PromptTemplateItem])
async def prompt_template_create(
    payload: PromptTemplatePayload,
    current_user: UserInfo = Depends(require_admin),
) -> ApiResponse[PromptTemplateItem]:
    """M10: Create a prompt template."""
    data = create_prompt_template(payload, current_user=current_user)
    return success_response(data)


@router.put('/prompt-templates/{template_id}', response_model=ApiResponse[PromptTemplateItem])
async def prompt_template_update(
    template_id: int,
    payload: PromptTemplatePayload,
    current_user: UserInfo = Depends(require_admin),
) -> ApiResponse[PromptTemplateItem]:
    """M10: Update a prompt template."""
    data = update_prompt_template(template_id, payload, current_user=current_user)
    return success_response(data)


@router.post('/prompt-templates/{template_id}/status', response_model=ApiResponse[dict])
async def prompt_template_status(
    template_id: int,
    request: PromptTemplateStatusRequest,
    current_user: UserInfo = Depends(require_admin),
) -> ApiResponse[dict]:
    """M10: Enable/disable a prompt template."""
    data = update_prompt_template_status(template_id, request, current_user=current_user)
    return success_response(data)


@router.post('/prompt-templates/{template_id}/default', response_model=ApiResponse[dict])
async def prompt_template_default(
    template_id: int,
    current_user: UserInfo = Depends(require_admin),
) -> ApiResponse[dict]:
    """M10: Set prompt template as default."""
    data = set_prompt_template_default(template_id, current_user=current_user)
    return success_response(data)


# ── M10: AI Call Records ──────────────────────────────────────────

@router.get('/ai-call-records', response_model=ApiResponse[AdminAICallRecordListResponse])
async def ai_call_record_list(
    function_type: str | None = Query(default=None),
    status: Optional[int] = Query(default=None),
    risk_level: str | None = Query(default=None),
    is_fallback: Optional[bool] = Query(default=None),
    user_id: Optional[int] = Query(default=None),
    start_time: str | None = Query(default=None),
    end_time: str | None = Query(default=None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    _: UserInfo = Depends(require_admin),
) -> ApiResponse[AdminAICallRecordListResponse]:
    """M10: Browse AI call records."""
    data = get_ai_call_records(
        function_type=function_type, status=status, risk_level=risk_level,
        is_fallback=is_fallback, user_id=user_id, start_time=start_time,
        end_time=end_time, page=page, page_size=page_size,
    )
    return success_response(data)


# ── M7: Hot Topics ──────────────────────────────────────────────


@router.get('/rankings/news-hot', response_model=ApiResponse[AdminNewsHotRankingResponse])
async def admin_news_hot_ranking(
    keyword: str | None = Query(default=None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    _: UserInfo = Depends(require_editor_or_admin),
) -> ApiResponse[AdminNewsHotRankingResponse]:
    data = get_admin_news_hot_ranking(keyword=keyword, page=page, page_size=page_size)
    return success_response(data)


@router.get('/rankings/community-hot', response_model=ApiResponse[AdminCommunityHotRankingResponse])
async def admin_community_hot_ranking(
    keyword: str | None = Query(default=None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    _: UserInfo = Depends(require_editor_or_admin),
) -> ApiResponse[AdminCommunityHotRankingResponse]:
    data = get_admin_community_hot_ranking(keyword=keyword, page=page, page_size=page_size)
    return success_response(data)


@router.get('/hot-topics/options', response_model=ApiResponse[AdminHotTopicOptions])
async def admin_hot_topic_options(
    _: UserInfo = Depends(require_editor_or_admin),
) -> ApiResponse[AdminHotTopicOptions]:
    data = get_admin_hot_topic_options()
    return success_response(data)


@router.get('/hot-topics', response_model=ApiResponse[AdminHotTopicListResponse])
async def admin_hot_topic_list(
    keyword: str | None = Query(default=None),
    hot_type: str | None = Query(default=None),
    target_type: str | None = Query(default=None),
    status: Optional[int] = Query(default=None),
    is_pinned: Optional[bool] = Query(default=None),
    is_hidden: Optional[bool] = Query(default=None),
    start_time: str | None = Query(default=None),
    end_time: str | None = Query(default=None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    _: UserInfo = Depends(require_editor_or_admin),
) -> ApiResponse[AdminHotTopicListResponse]:
    data = get_admin_hot_topic_list(
        keyword=keyword, hot_type=hot_type, target_type=target_type,
        status=status, is_pinned=is_pinned, is_hidden=is_hidden,
        start_time=start_time, end_time=end_time, page=page, page_size=page_size,
    )
    return success_response(data)


@router.get('/hot-topics/{hot_id}', response_model=ApiResponse[AdminHotTopicDetail])
async def admin_hot_topic_detail(
    hot_id: int, _: UserInfo = Depends(require_editor_or_admin),
) -> ApiResponse[AdminHotTopicDetail]:
    data = get_admin_hot_topic_detail(hot_id)
    return success_response(data)


@router.post('/hot-topics/{hot_id}/rank', response_model=ApiResponse[AdminHotTopicActionResult])
async def admin_hot_topic_rank(
    hot_id: int, request: AdminHotTopicRankRequest = Body(...),
    _: UserInfo = Depends(require_editor_or_admin),
) -> ApiResponse[AdminHotTopicActionResult]:
    data = update_admin_hot_topic_rank(hot_id, request)
    return success_response(data)


@router.post('/hot-topics/{hot_id}/pin', response_model=ApiResponse[AdminHotTopicActionResult])
async def admin_hot_topic_pin(
    hot_id: int, _: UserInfo = Depends(require_editor_or_admin),
) -> ApiResponse[AdminHotTopicActionResult]:
    data = set_admin_hot_topic_pin(hot_id, True)
    return success_response(data)


@router.delete('/hot-topics/{hot_id}/pin', response_model=ApiResponse[AdminHotTopicActionResult])
async def admin_hot_topic_unpin(
    hot_id: int, _: UserInfo = Depends(require_editor_or_admin),
) -> ApiResponse[AdminHotTopicActionResult]:
    data = set_admin_hot_topic_pin(hot_id, False)
    return success_response(data)


@router.post('/hot-topics/{hot_id}/hide', response_model=ApiResponse[AdminHotTopicActionResult])
async def admin_hot_topic_hide(
    hot_id: int, _: UserInfo = Depends(require_editor_or_admin),
) -> ApiResponse[AdminHotTopicActionResult]:
    data = set_admin_hot_topic_hidden(hot_id, True)
    return success_response(data)


@router.delete('/hot-topics/{hot_id}/hide', response_model=ApiResponse[AdminHotTopicActionResult])
async def admin_hot_topic_restore(
    hot_id: int, _: UserInfo = Depends(require_editor_or_admin),
) -> ApiResponse[AdminHotTopicActionResult]:
    data = set_admin_hot_topic_hidden(hot_id, False)
    return success_response(data)


@router.post('/hot-topics/{hot_id}/refresh-heat', response_model=ApiResponse[AdminHotTopicActionResult])
async def admin_hot_topic_refresh_heat(
    hot_id: int, _: UserInfo = Depends(require_editor_or_admin),
) -> ApiResponse[AdminHotTopicActionResult]:
    data = refresh_admin_hot_topic_heat(hot_id)
    return success_response(data)


# ── M7: Topics ────────────────────────────────────────────────────


@router.get('/topics/options', response_model=ApiResponse[AdminTopicOptions])
async def admin_topic_options(
    _: UserInfo = Depends(require_editor_or_admin),
) -> ApiResponse[AdminTopicOptions]:
    data = get_admin_topic_options()
    return success_response(data)


@router.get('/topics', response_model=ApiResponse[AdminTopicListResponse])
async def admin_topic_list(
    keyword: str | None = Query(default=None),
    status: Optional[int] = Query(default=None),
    has_news: Optional[bool] = Query(default=None),
    start_time: str | None = Query(default=None),
    end_time: str | None = Query(default=None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    _: UserInfo = Depends(require_editor_or_admin),
) -> ApiResponse[AdminTopicListResponse]:
    data = get_admin_topic_list(
        keyword=keyword, status=status, has_news=has_news,
        start_time=start_time, end_time=end_time, page=page, page_size=page_size,
    )
    return success_response(data)


@router.post('/topics', response_model=ApiResponse[AdminTopicActionResult])
async def admin_topic_create(
    request: AdminTopicPayload = Body(...),
    _: UserInfo = Depends(require_editor_or_admin),
) -> ApiResponse[AdminTopicActionResult]:
    data = create_admin_topic(request)
    return success_response(data)


@router.get('/topics/{topic_id}', response_model=ApiResponse[AdminTopicDetail])
async def admin_topic_detail(
    topic_id: int, _: UserInfo = Depends(require_editor_or_admin),
) -> ApiResponse[AdminTopicDetail]:
    data = get_admin_topic_detail(topic_id)
    return success_response(data)


@router.put('/topics/{topic_id}', response_model=ApiResponse[AdminTopicActionResult])
async def admin_topic_update(
    topic_id: int, request: AdminTopicPayload = Body(...),
    _: UserInfo = Depends(require_editor_or_admin),
) -> ApiResponse[AdminTopicActionResult]:
    data = update_admin_topic(topic_id, request)
    return success_response(data)


@router.post('/topics/{topic_id}/status', response_model=ApiResponse[AdminTopicActionResult])
async def admin_topic_status(
    topic_id: int, request: AdminTopicStatusRequest = Body(...),
    _: UserInfo = Depends(require_editor_or_admin),
) -> ApiResponse[AdminTopicActionResult]:
    data = update_admin_topic_status(topic_id, request)
    return success_response(data)


@router.get('/topics/{topic_id}/news', response_model=ApiResponse[AdminTopicNewsResponse])
async def admin_topic_news(
    topic_id: int,
    keyword: str | None = Query(default=None),
    status: Optional[int] = Query(default=None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    _: UserInfo = Depends(require_editor_or_admin),
) -> ApiResponse[AdminTopicNewsResponse]:
    data = get_admin_topic_news(
        topic_id=topic_id, keyword=keyword, status=status, page=page, page_size=page_size,
    )
    return success_response(data)


@router.get('/topics/{topic_id}/candidate-news', response_model=ApiResponse[AdminTopicNewsResponse])
async def admin_topic_candidate_news(
    topic_id: int,
    keyword: str | None = Query(default=None),
    status: Optional[int] = Query(default=None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    _: UserInfo = Depends(require_editor_or_admin),
) -> ApiResponse[AdminTopicNewsResponse]:
    data = get_admin_topic_candidate_news(
        topic_id=topic_id, keyword=keyword, status=status, page=page, page_size=page_size,
    )
    return success_response(data)


@router.post('/topics/{topic_id}/bind-news', response_model=ApiResponse[AdminTopicActionResult])
async def admin_topic_bind_news(
    topic_id: int, request: AdminTopicBindNewsRequest = Body(...),
    _: UserInfo = Depends(require_editor_or_admin),
) -> ApiResponse[AdminTopicActionResult]:
    data = bind_admin_topic_news(topic_id, request)
    return success_response(data)


@router.post('/topics/{topic_id}/unbind-news', response_model=ApiResponse[AdminTopicActionResult])
async def admin_topic_unbind_news(
    topic_id: int, request: AdminTopicBindNewsRequest = Body(...),
    _: UserInfo = Depends(require_editor_or_admin),
) -> ApiResponse[AdminTopicActionResult]:
    data = unbind_admin_topic_news(topic_id, request)
    return success_response(data)


# ── M8: Timeline Management ──────────────────────────────────────


@router.get('/timelines/options', response_model=ApiResponse[AdminTimelineOptionsResponse])
async def admin_timeline_options(
    _: UserInfo = Depends(require_editor_or_admin),
) -> ApiResponse[AdminTimelineOptionsResponse]:
    data = get_admin_timeline_options()
    return success_response(data)


@router.get('/timelines', response_model=ApiResponse[AdminTimelineListResponse])
async def admin_timeline_list(
    keyword: str | None = Query(default=None),
    generate_status: str | None = Query(default=None),
    news_count_type: str | None = Query(default=None),
    has_cache: bool | None = Query(default=None),
    cache_error: bool | None = Query(default=None),
    start_time: str | None = Query(default=None),
    end_time: str | None = Query(default=None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    _: UserInfo = Depends(require_editor_or_admin),
) -> ApiResponse[AdminTimelineListResponse]:
    data = get_admin_timeline_list(
        keyword=keyword, generate_status=generate_status,
        news_count_type=news_count_type, has_cache=has_cache,
        cache_error=cache_error, start_time=start_time,
        end_time=end_time, page=page, page_size=page_size,
    )
    return success_response(data)


@router.get('/timelines/{topic_id}', response_model=ApiResponse[AdminTimelineDetailResponse])
async def admin_timeline_detail(
    topic_id: int, _: UserInfo = Depends(require_editor_or_admin),
) -> ApiResponse[AdminTimelineDetailResponse]:
    data = get_admin_timeline_detail(topic_id)
    return success_response(data)


@router.get('/timelines/{topic_id}/source-news', response_model=ApiResponse[AdminTimelineSourceNewsResponse])
async def admin_timeline_source_news(
    topic_id: int,
    keyword: str | None = Query(default=None),
    status: int | None = Query(default=None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    _: UserInfo = Depends(require_editor_or_admin),
) -> ApiResponse[AdminTimelineSourceNewsResponse]:
    data = get_admin_timeline_source_news(
        topic_id=topic_id, keyword=keyword, status=status,
        page=page, page_size=page_size,
    )
    return success_response(data)


@router.post('/timelines/{topic_id}/generate', response_model=ApiResponse[AdminTimelineActionResult])
async def admin_timeline_generate_endpoint(
    topic_id: int, _: UserInfo = Depends(require_editor_or_admin),
) -> ApiResponse[AdminTimelineActionResult]:
    data = await admin_timeline_generate(topic_id)
    return success_response(data)


@router.post('/timelines/{topic_id}/refresh', response_model=ApiResponse[AdminTimelineActionResult])
async def admin_timeline_refresh_endpoint(
    topic_id: int, _: UserInfo = Depends(require_editor_or_admin),
) -> ApiResponse[AdminTimelineActionResult]:
    data = await admin_timeline_refresh(topic_id)
    return success_response(data)


@router.delete('/timelines/{topic_id}/cache', response_model=ApiResponse[AdminTimelineActionResult])
async def admin_timeline_delete_cache_endpoint(
    topic_id: int, _: UserInfo = Depends(require_editor_or_admin),
) -> ApiResponse[AdminTimelineActionResult]:
    data = admin_timeline_delete_cache(topic_id)
    return success_response(data)
