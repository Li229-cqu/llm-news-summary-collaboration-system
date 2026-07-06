from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class AdminTestData(BaseModel):
    module: str
    description: str


class AdminDashboard(BaseModel):
    # existing
    user_count: int = 0
    news_count: int = 0
    post_count: int = 0
    pending_count: int = 0
    pending_news_count: int = 0
    pending_post_count: int = 0
    pending_comment_count: int = 0
    today_news_count: int = 0
    today_user_count: int = 0
    ai_call_count: int = 0
    timeline_error_count: int = 0
    today_processed_count: int = 0
    # new trend-oriented fields
    today_new_users: int = 0
    active_users_7d: int = 0
    today_review_done: int = 0
    today_ai_calls: int = 0
    avg_response_ms: int | None = None
    timeline_pending_count: int = 0
    pending_total: int = 0


class AdminRankingSummary(BaseModel):
    news_hot_count: int = 0
    community_hot_count: int = 0
    today_news_count: int = 0
    today_post_count: int = 0


class AdminNewsHotRankingItem(BaseModel):
    rank: int
    id: int
    title: str = ''
    category_name: str = ''
    source: str = ''
    view_count: int = 0
    like_count: int = 0
    favorite_count: int = 0
    comment_count: int = 0
    heat_score: int = 0
    publish_time: Optional[str] = None
    status: int = 1
    status_label: str = ''


class AdminNewsHotRankingResponse(BaseModel):
    items: list[AdminNewsHotRankingItem] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 10
    summary: AdminRankingSummary = Field(default_factory=AdminRankingSummary)


class AdminCommunityHotRankingItem(BaseModel):
    rank: int
    id: int
    title: str = ''
    author_name: str = ''
    view_count: int = 0
    like_count: int = 0
    favorite_count: int = 0
    comment_count: int = 0
    heat_score: int = 0
    created_at: Optional[str] = None
    status: int = 1
    status_label: str = ''


class AdminCommunityHotRankingResponse(BaseModel):
    items: list[AdminCommunityHotRankingItem] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 10
    summary: AdminRankingSummary = Field(default_factory=AdminRankingSummary)


class UserItem(BaseModel):
    id: int
    username: str
    nickname: str
    role: str
    status: int
    create_time: Optional[str] = None


class PaginationResponse(BaseModel):
    list: list[dict]
    total: int
    page: int
    page_size: int


class PendingSummary(BaseModel):
    pending_news_count: int = 0
    pending_post_count: int = 0
    pending_comment_count: int = 0
    today_processed_count: int = 0


class PendingItem(BaseModel):
    id: int
    item_type: Literal['news', 'post', 'comment']
    target_type: Optional[Literal['news', 'post']] = None
    title: str = ''
    content_preview: str = ''
    submitter: str = ''
    source: str = ''
    category_name: str = ''
    tags: list[str] = Field(default_factory=list)
    status: int = 0
    status_label: str = ''
    create_time: Optional[str] = None
    update_time: Optional[str] = None


class PendingItemsResponse(BaseModel):
    items: list[PendingItem] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 10
    summary: PendingSummary = Field(default_factory=PendingSummary)


class PendingItemDetail(PendingItem):
    summary: str = ''
    content: str = ''
    cover_image: str = ''
    publish_time: Optional[str] = None
    editor: str = ''
    topic_name: str = ''
    tags: list[str] = Field(default_factory=list)
    view_count: int = 0
    like_count: int = 0
    comment_count: int = 0
    favorite_count: int = 0
    heat_score: int = 0
    related_news_id: Optional[int] = None
    related_news_title: str = ''
    news_id: Optional[int] = None
    post_id: Optional[int] = None
    parent_id: Optional[int] = None
    parent_content: str = ''
    media_json: Any | None = None
    reason: str = ''


class ReviewActionRequest(BaseModel):
    action: Literal['approve', 'reject', 'fold', 'delete', 'restore']
    reason: str = ''


class ReviewActionResult(BaseModel):
    item_type: Literal['news', 'post', 'comment']
    item_id: int
    action: str
    status: int
    status_label: str
    updated: bool = True
    message: str = ''
    reason: str = ''



class AdminNewsSummary(BaseModel):
    total_count: int = 0
    pending_count: int = 0
    published_count: int = 0
    offline_count: int = 0
    unbound_topic_count: int = 0
    feature_supported: bool = False


class AdminNewsItem(BaseModel):
    id: int
    title: str = ''
    summary: str = ''
    content_preview: str = ''
    cover_image: str = ''
    category_id: Optional[int] = None
    category_name: str = ''
    topic_id: Optional[int] = None
    topic_name: str = ''
    source: str = ''
    editor: str = ''
    publish_time: Optional[str] = None
    view_count: int = 0
    like_count: int = 0
    comment_count: int = 0
    favorite_count: int = 0
    status: int = 0
    status_label: str = ''
    tags: list[str] = Field(default_factory=list)
    is_featured: Optional[bool] = None
    feature_supported: bool = False
    create_time: Optional[str] = None
    update_time: Optional[str] = None


class AdminNewsListResponse(BaseModel):
    items: list[AdminNewsItem] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 10
    summary: AdminNewsSummary = Field(default_factory=AdminNewsSummary)


class AdminNewsDetail(AdminNewsItem):
    content: str = ''
    source_url: str = ''


class AdminNewsUpdateRequest(BaseModel):
    title: str
    summary: str = ''
    content: str
    source: str = ''
    category_id: Optional[int] = None
    cover_image: str = ''
    tags: list[str] = Field(default_factory=list)
    publish_time: Optional[str] = None


class AdminNewsTopicRequest(BaseModel):
    topic_id: Optional[int] = None


class AdminNewsActionResult(BaseModel):
    news_id: int
    action: str
    updated: bool = True
    status: Optional[int] = None
    status_label: str = ''
    message: str = ''


class AdminNewsOptions(BaseModel):
    categories: list[dict] = Field(default_factory=list)
    topics: list[dict] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)
    feature_supported: bool = False



class AdminPostSummary(BaseModel):
    total_count: int = 0
    pending_count: int = 0
    normal_count: int = 0
    folded_count: int = 0
    deleted_count: int = 0
    reported_count: int = 0
    feature_supported: bool = False


class AdminPostItem(BaseModel):
    id: int
    title: str = ''
    content_preview: str = ''
    user_id: Optional[int] = None
    username: str = ''
    nickname: str = ''
    author_name: str = ''
    related_news_id: Optional[int] = None
    related_news_title: str = ''
    topic_id: Optional[int] = None
    topic_name: str = ''
    tags: list[str] = Field(default_factory=list)
    like_count: int = 0
    comment_count: int = 0
    favorite_count: int = 0
    heat_score: int = 0
    status: int = 0
    status_label: str = ''
    is_featured: Optional[bool] = None
    feature_supported: bool = False
    create_time: Optional[str] = None
    update_time: Optional[str] = None


class AdminPostListResponse(BaseModel):
    items: list[AdminPostItem] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 10
    summary: AdminPostSummary = Field(default_factory=AdminPostSummary)


class AdminPostDetail(AdminPostItem):
    content: str = ''
    recent_comments: list[dict] = Field(default_factory=list)


class AdminPostActionResult(BaseModel):
    post_id: int
    action: str
    updated: bool = True
    status: Optional[int] = None
    status_label: str = ''
    message: str = ''


class AdminPostOptions(BaseModel):
    statuses: list[dict] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    feature_supported: bool = False



class AdminCommentSummary(BaseModel):
    total_count: int = 0
    news_comment_count: int = 0
    post_comment_count: int = 0
    pending_count: int = 0
    folded_count: int = 0
    deleted_count: int = 0
    reported_count: int = 0
    report_supported: bool = False


class AdminCommentItem(BaseModel):
    id: int
    comment_type: Literal['news', 'post']
    comment_type_label: str = ''
    target_id: Optional[int] = None
    target_title: str = ''
    target_source: str = ''
    user_id: Optional[int] = None
    username: str = ''
    nickname: str = ''
    author_name: str = ''
    parent_id: Optional[int] = None
    parent_content: str = ''
    content: str = ''
    content_preview: str = ''
    media_json: Any | None = None
    like_count: int = 0
    reply_count: int = 0
    status: int = 0
    status_label: str = ''
    create_time: Optional[str] = None
    update_time: Optional[str] = None


class AdminCommentListResponse(BaseModel):
    items: list[AdminCommentItem] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 10
    summary: AdminCommentSummary = Field(default_factory=AdminCommentSummary)


class AdminCommentDetail(AdminCommentItem):
    context: dict = Field(default_factory=dict)
    replies: list[dict] = Field(default_factory=list)


class AdminCommentActionResult(BaseModel):
    comment_id: int
    comment_type: Literal['news', 'post']
    action: str
    updated: bool = True
    status: Optional[int] = None
    status_label: str = ''
    message: str = ''


class AdminCommentOptions(BaseModel):
    statuses: list[dict] = Field(default_factory=list)
    types: list[dict] = Field(default_factory=list)
    report_supported: bool = False


class AdminHotTopicSupport(BaseModel):
    pin_supported: bool = False
    hide_supported: bool = True
    hide_uses_status: bool = True
    manual_rank_supported: bool = True


class AdminHotTopicSummary(BaseModel):
    total_count: int = 0
    news_hot_count: int = 0
    community_hot_count: int = 0
    topic_hot_count: int = 0
    pinned_count: int = 0
    hidden_count: int = 0


class AdminHotTopicItem(BaseModel):
    id: int
    title: str = ''
    hot_type: str = ''
    target_type: str = ''
    target_id: Optional[int] = None
    tag: str = ''
    heat_score: int = 0
    rank_no: int = 0
    status: int = 1
    status_label: str = ''
    is_pinned: Optional[bool] = None
    is_hidden: bool = False
    target_title: str = ''
    target_missing: bool = False
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class AdminHotTopicListResponse(BaseModel):
    items: list[AdminHotTopicItem] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 10
    summary: AdminHotTopicSummary = Field(default_factory=AdminHotTopicSummary)
    support: AdminHotTopicSupport = Field(default_factory=AdminHotTopicSupport)


class AdminHotTopicDetail(AdminHotTopicItem):
    related_target: dict = Field(default_factory=dict)


class AdminHotTopicOptions(BaseModel):
    target_types: list[dict] = Field(default_factory=list)
    statuses: list[dict] = Field(default_factory=list)
    support: AdminHotTopicSupport = Field(default_factory=AdminHotTopicSupport)


class AdminHotTopicRankRequest(BaseModel):
    rank_no: int = Field(..., ge=1)


class AdminHotTopicActionResult(BaseModel):
    hot_id: int
    action: str
    updated: bool = True
    rank_no: Optional[int] = None
    status: Optional[int] = None
    status_label: str = ''
    message: str = ''


class AdminTopicSupport(BaseModel):
    news_topic_table_supported: bool = True
    keyword_supported: bool = True
    description_supported: bool = True


class AdminTopicSummary(BaseModel):
    total_count: int = 0
    enabled_count: int = 0
    disabled_count: int = 0
    with_news_count: int = 0
    without_news_count: int = 0


class AdminTopicItem(BaseModel):
    id: int
    topic_name: str = ''
    summary: str = ''
    keyword_list: list[str] = Field(default_factory=list)
    heat_score: int = 0
    news_count: int = 0
    status: int = 1
    status_label: str = ''
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class AdminTopicListResponse(BaseModel):
    items: list[AdminTopicItem] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 10
    summary: AdminTopicSummary = Field(default_factory=AdminTopicSummary)
    support: AdminTopicSupport = Field(default_factory=AdminTopicSupport)


class AdminTopicDetail(AdminTopicItem):
    recent_news: list[dict] = Field(default_factory=list)


class AdminTopicOptions(BaseModel):
    status_options: list[dict] = Field(default_factory=list)
    support: AdminTopicSupport = Field(default_factory=AdminTopicSupport)


class AdminTopicPayload(BaseModel):
    topic_name: str
    summary: str = ''
    keyword_list: list[str] | str = Field(default_factory=list)
    heat_score: int = 0
    status: int = 1


class AdminTopicStatusRequest(BaseModel):
    status: int = Field(..., ge=0, le=1)


class AdminTopicActionResult(BaseModel):
    topic_id: int
    action: str
    updated: bool = True
    status: Optional[int] = None
    status_label: str = ''
    affected_count: int = 0
    message: str = ''


class AdminTopicNewsItem(BaseModel):
    id: int
    title: str = ''
    category_name: str = ''
    source: str = ''
    publish_time: Optional[str] = None
    status: int = 1
    status_label: str = ''
    topic_id: Optional[int] = None


class AdminTopicNewsResponse(BaseModel):
    items: list[AdminTopicNewsItem] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 10


class AdminTopicBindNewsRequest(BaseModel):
    news_ids: list[int] = Field(default_factory=list)


# ── M8: AdminTimeline schemas ─────────────────────────────────────


class AdminTimelineSupport(BaseModel):
    event_timeline_table_supported: bool = True
    timeline_generate_supported: bool = True
    timeline_cache_supported: bool = True


class AdminTimelineOptionsResponse(BaseModel):
    status_options: list[dict] = Field(default_factory=list)
    news_count_options: list[dict] = Field(default_factory=list)
    support: AdminTimelineSupport = Field(default_factory=AdminTimelineSupport)


class AdminTimelineSummary(BaseModel):
    topic_count: int = 0
    generated_count: int = 0
    not_generated_count: int = 0
    failed_count: int = 0
    insufficient_news_count: int = 0
    cache_error_count: int = 0


class AdminTimelineListParams(BaseModel):
    keyword: str | None = None
    generate_status: str | None = None
    news_count_type: str | None = None  # 'less_than_2' | '2_or_more'
    has_cache: bool | None = None
    cache_error: bool | None = None
    start_time: str | None = None
    end_time: str | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=10, ge=1, le=100)


class AdminTimelineItem(BaseModel):
    topic_id: int
    topic_name: str = ''
    keyword_list: list[str] = Field(default_factory=list)
    news_count: int = 0
    generate_status: str = ''  # 'not_generated', 'generated', 'generated (fallback)', 'failed', 'generating'
    generate_status_label: str = ''
    cache_status: str = ''  # 'normal', 'no_cache', 'json_error', 'source_mismatch'
    cache_status_label: str = ''
    source_news_count: int = 0
    generated_at: str | None = None
    updated_at: str | None = None


class AdminTimelineListResponse(BaseModel):
    items: list[AdminTimelineItem] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 10
    summary: AdminTimelineSummary = Field(default_factory=AdminTimelineSummary)


class AdminTimelineNodeItem(BaseModel):
    event_id: int = 0
    event_time: str = ''
    event_title: str = ''
    event_summary: str = ''
    source_news_id: int = 0
    source_title: str = ''
    source_name: str = ''
    event_type: str = 'other'
    importance: int = 3


class AdminTimelineCacheCheck(BaseModel):
    json_valid: bool = False
    source_news_valid: bool = False
    missing_source_news_ids: list[int] = Field(default_factory=list)
    message: str = '无缓存'


class AdminTimelineDetailResponse(BaseModel):
    topic_id: int
    topic_name: str = ''
    keyword_list: list[str] = Field(default_factory=list)
    generate_status: str = ''
    generate_status_label: str = ''
    generated_at: str | None = None
    updated_at: str | None = None
    source_news_ids: list[int] = Field(default_factory=list)
    timeline_nodes: list[AdminTimelineNodeItem] = Field(default_factory=list)
    source_news: list[dict] = Field(default_factory=list)
    overview: str = ''
    cache_check: AdminTimelineCacheCheck = Field(default_factory=AdminTimelineCacheCheck)
    raw_json: str = ''


class AdminTimelineSourceNewsItem(BaseModel):
    id: int
    title: str = ''
    source: str = ''
    publish_time: str | None = None
    status: int = 0
    status_label: str = ''
    in_source_news_ids: bool = False


class AdminTimelineSourceNewsResponse(BaseModel):
    topic_id: int
    topic_name: str = ''
    items: list[AdminTimelineSourceNewsItem] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 10


class AdminTimelineActionResult(BaseModel):
    topic_id: int
    action: str = ''
    updated: bool = True
    generate_status: str = ''
    generate_status_label: str = ''
    message: str = ''


# ── M9: AdminUser schemas ─────────────────────────────────────────


class AdminUserSummary(BaseModel):
    total_count: int = 0
    admin_count: int = 0
    editor_count: int = 0
    user_count: int = 0
    active_count: int = 0
    disabled_count: int = 0


class AdminUserListResponse(BaseModel):
    items: list[UserItem] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 10
    summary: AdminUserSummary = Field(default_factory=AdminUserSummary)


class AdminUserBehaviorStats(BaseModel):
    post_count: int = 0
    comment_count: int = 0
    ai_generation_count: int = 0
    browse_count: int = 0
    favorite_count: int = 0


class AdminUserDetail(BaseModel):
    id: int
    username: str
    nickname: str
    role: str
    status: int
    create_time: Optional[str] = None
    updated_at: Optional[str] = None
    email: str = ''
    phone: str = ''
    avatar: str = ''
    behavior: AdminUserBehaviorStats = Field(default_factory=AdminUserBehaviorStats)


class AdminUserOptions(BaseModel):
    roles: list[dict] = Field(default_factory=list)
    statuses: list[dict] = Field(default_factory=list)
    last_login_supported: bool = False


class AdminUserRoleRequest(BaseModel):
    role: Literal['user', 'editor', 'admin']


class AdminUserStatusRequest(BaseModel):
    status: int = Field(..., ge=0, le=1)


class AdminUserActionResult(BaseModel):
    user_id: int
    action: str
    updated: bool = True
    message: str = ''


# ── M10: System Config & AI Model Rules schemas ────────────────────

class SystemConfigItem(BaseModel):
    id: int
    config_key: str
    config_value: Optional[str] = None
    config_type: str = 'string'
    description: str = ''
    editable: bool = True
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class SystemConfigListResponse(BaseModel):
    items: list[SystemConfigItem] = Field(default_factory=list)
    total: int = 0


class SystemConfigUpdateRequest(BaseModel):
    items: list[dict] = Field(default_factory=list)


class AIConfigResponse(BaseModel):
    service_url: str = ''
    model_name: str = ''
    api_key_configured: bool = False
    timeout: int = 60
    max_input_length: int = 8000
    enable_real_llm: bool = False
    enable_fallback: bool = True
    enable_cache: bool = False
    cache_supported: bool = False
    risk_threshold_low: float = 0.3
    risk_threshold_medium: float = 0.7
    sensitive_words: list[str] = Field(default_factory=list)
    risk_rules: list[dict] = Field(default_factory=list)
    fallback_strategy: dict = Field(default_factory=dict)
    service_status: str = ''
    last_check_time: Optional[str] = None


class AIConfigUpdateRequest(BaseModel):
    service_url: Optional[str] = None
    model_name: Optional[str] = None
    timeout: Optional[int] = None
    max_input_length: Optional[int] = None
    enable_real_llm: Optional[bool] = None
    enable_fallback: Optional[bool] = None
    risk_threshold_low: Optional[float] = None
    risk_threshold_medium: Optional[float] = None
    sensitive_words: Optional[str] = None
    risk_rules: Optional[str] = None
    fallback_strategy: Optional[str] = None


class AIConfigTestResult(BaseModel):
    status: str = ''
    latency_ms: int = 0
    message: str = ''


class PromptTemplateItem(BaseModel):
    id: int
    name: str
    function_type: str
    prompt_content: str
    version: str = 'v1'
    status: int = 1
    is_default: int = 0
    remark: str = ''
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class PromptTemplateListResponse(BaseModel):
    items: list[PromptTemplateItem] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 10


class PromptTemplatePayload(BaseModel):
    name: str
    function_type: str
    prompt_content: str
    version: str = 'v1'
    status: int = 1
    is_default: int = 0
    remark: str = ''


class PromptTemplateStatusRequest(BaseModel):
    status: int = Field(..., ge=0, le=1)


class PromptTemplateOptions(BaseModel):
    function_types: list[dict] = Field(default_factory=list)


class AdminAICallRecordItem(BaseModel):
    id: int
    user_id: Optional[int] = None
    username: str = ''
    function_type: str = ''
    input_length: int = 0
    status: int = 0
    status_label: str = ''
    risk_level: str = ''
    is_fallback: bool = False
    error_message: str = ''
    created_at: Optional[str] = None


class AdminAICallRecordSummary(BaseModel):
    total_count: int = 0
    today_count: int = 0
    fallback_count: int = 0


class AdminAICallRecordListResponse(BaseModel):
    items: list[AdminAICallRecordItem] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 10
    summary: AdminAICallRecordSummary = Field(default_factory=AdminAICallRecordSummary)
    fallback_supported: bool = False


# M11: System Operations & Operation Log schemas


class AdminOpsStatusPart(BaseModel):
    status: str = 'unknown'
    message: str = ''


class AdminOpsStatusResponse(BaseModel):
    backend: AdminOpsStatusPart = Field(default_factory=AdminOpsStatusPart)
    database: AdminOpsStatusPart = Field(default_factory=AdminOpsStatusPart)
    ai_service: AdminOpsStatusPart = Field(default_factory=AdminOpsStatusPart)
    environment: str = 'development'
    last_check_time: Optional[str] = None


class AdminOpsTableStatus(BaseModel):
    table_name: str
    display_name: str = ''
    exists: bool = False
    row_count: Optional[int] = None


class AdminOpsDatabaseResponse(BaseModel):
    connection_status: str = 'unknown'
    database_name: str = ''
    tables: list[AdminOpsTableStatus] = Field(default_factory=list)
    last_backup_time: Optional[str] = None
    backup_supported: bool = False


class AdminBackupRecordItem(BaseModel):
    id: int
    backup_name: str
    backup_type: str = 'manual'
    file_path: str = ''
    file_size: int = 0
    status: str = 'pending'
    message: str = ''
    operator_id: Optional[int] = None
    operator_name: str = ''
    created_at: Optional[str] = None
    finished_at: Optional[str] = None


class AdminBackupRecordSummary(BaseModel):
    total_count: int = 0
    success_count: int = 0
    failed_count: int = 0
    unsupported_count: int = 0
    today_count: int = 0


class AdminBackupRecordListResponse(BaseModel):
    items: list[AdminBackupRecordItem] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 10
    summary: AdminBackupRecordSummary = Field(default_factory=AdminBackupRecordSummary)


class AdminBackupActionResult(BaseModel):
    backup_id: Optional[int] = None
    status: str = 'unsupported'
    message: str = ''


class AdminStorageResponse(BaseModel):
    supported: bool = False
    upload_dir: Optional[str] = None
    total_files: int = 0
    total_size: int = 0
    image_count: int = 0
    document_count: int = 0
    abnormal_count: int = 0
    last_upload_time: Optional[str] = None
    message: str = ''


class AdminOperationLogSummary(BaseModel):
    total_count: int = 0
    success_count: int = 0
    failed_count: int = 0
    unsupported_count: int = 0
    today_count: int = 0


class AdminOperationLogItem(BaseModel):
    id: int
    operator_id: Optional[int] = None
    operator_name: str = ''
    operator_role: str = ''
    module: str = ''
    action: str = ''
    target_type: str = ''
    target_id: str = ''
    description: str = ''
    ip_address: str = ''
    result: str = 'success'
    created_at: Optional[str] = None


class AdminOperationLogDetail(AdminOperationLogItem):
    user_agent: str = ''
    error_message: str = ''


class AdminOperationLogListResponse(BaseModel):
    items: list[AdminOperationLogItem] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 10
    summary: AdminOperationLogSummary = Field(default_factory=AdminOperationLogSummary)


# ── M12: Analytics ──────────────────────────────────────────────────


class AdminAnalyticsOverview(BaseModel):
    total_users: int = 0
    active_users: int = 0
    total_news: int = 0
    total_posts: int = 0
    total_comments: int = 0
    ai_generate_count: int = 0
    timeline_count: int = 0
    pending_count: int = 0


class AdminTrendPoint(BaseModel):
    date: str = ''
    news_count: int = 0
    post_count: int = 0
    comment_count: int = 0
    ai_count: int = 0
    fallback_count: int = 0
    high_risk_count: int = 0


class AdminAnalyticsTrendsResponse(BaseModel):
    content_trend: list[AdminTrendPoint] = Field(default_factory=list)
    ai_trend: list[AdminTrendPoint] = Field(default_factory=list)
    supported: bool = True


class AdminTopNewsItem(BaseModel):
    rank: int = 0
    id: int = 0
    title: str = ''
    source: str = ''
    view_count: int = 0
    comment_count: int = 0
    topic_name: str = ''
    publish_time: Optional[str] = None


class AdminTopPostItem(BaseModel):
    rank: int = 0
    id: int = 0
    title: str = ''
    author_name: str = ''
    comment_count: int = 0
    like_count: int = 0
    heat_score: int = 0
    created_at: Optional[str] = None


class AdminAnalyticsTopContentResponse(BaseModel):
    top_news: list[AdminTopNewsItem] = Field(default_factory=list)
    top_posts: list[AdminTopPostItem] = Field(default_factory=list)


class AdminAiRiskItem(BaseModel):
    risk_level: str = ''
    count: int = 0


class AdminAnalyticsAiRiskResponse(BaseModel):
    items: list[AdminAiRiskItem] = Field(default_factory=list)
    supported: bool = True


class AdminReviewPending(BaseModel):
    news: int = 0
    posts: int = 0
    comments: int = 0
    total: int = 0


class AdminReviewProcessed(BaseModel):
    approve: int = 0
    reject: int = 0
    fold: int = 0
    delete: int = 0
    restore: int = 0
    total: int = 0


class AdminAnalyticsReviewSummaryResponse(BaseModel):
    pending: AdminReviewPending = Field(default_factory=AdminReviewPending)
    processed: AdminReviewProcessed = Field(default_factory=AdminReviewProcessed)
    today_processed: int = 0


class AdminContentOverviewItem(BaseModel):
    content_type: str = ''
    id: int = 0
    title: str = ''
    creator_or_source: str = ''
    status_label: str = ''
    risk_level: str = ''
    related_info: str = ''
    updated_at: Optional[str] = None
    target_tab: str = ''


class AdminAnalyticsContentOverviewResponse(BaseModel):
    items: list[AdminContentOverviewItem] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 10

