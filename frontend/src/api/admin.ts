import request from '@/api/http'

export interface AdminDashboard {
  user_count: number
  news_count: number
  post_count: number
  pending_count: number
  pending_news_count?: number
  pending_post_count?: number
  pending_comment_count?: number
  today_news_count?: number
  today_user_count?: number
  ai_call_count?: number
  timeline_error_count?: number
  // M13: trend-oriented fields
  today_new_users?: number
  active_users_7d?: number
  today_review_done?: number
  today_ai_calls?: number
  avg_response_ms?: number | null
  timeline_pending_count?: number
  pending_total?: number
}

export interface UserItem {
  id: number
  username: string
  nickname: string
  role: string
  status: number
  create_time?: string
}

// ── M9: User management types ────────────────────────────────────

export interface AdminUserQueryParams {
  keyword?: string
  role?: string
  status?: number | null
  start_time?: string
  end_time?: string
  page?: number
  page_size?: number
}

export interface AdminUserBehaviorStats {
  post_count: number
  comment_count: number
  ai_generation_count: number
  browse_count: number
  favorite_count: number
}

export interface AdminUserDetail extends UserItem {
  updated_at?: string | null
  email: string
  phone: string
  avatar: string
  behavior: AdminUserBehaviorStats
}

export interface AdminUserSummary {
  total_count: number
  admin_count: number
  editor_count: number
  user_count: number
  active_count: number
  disabled_count: number
}

export interface AdminUserListResponse {
  items: UserItem[]
  total: number
  page: number
  page_size: number
  summary: AdminUserSummary
}

export interface AdminUserOptions {
  roles: Array<{ label: string; value: string }>
  statuses: Array<{ label: string; value: number }>
  last_login_supported: boolean
}

export interface AdminUserActionResult {
  user_id: number
  action: string
  updated: boolean
  message: string
}

export interface AdminUserRoleRequest {
  role: 'user' | 'editor' | 'admin'
}

export interface AdminUserStatusRequest {
  status: number
}

export interface PendingPostItem {
  id: number
  title: string
  content?: string
  username?: string
  author?: string
  user_id?: number
  topic_id?: number | null
  view_count?: number
  like_count?: number
  comment_count?: number
  favorite_count?: number
  heat_score?: number
  status?: number
  create_time?: string | null
  update_time?: string | null
}

export type AdminPendingItemType = 'all' | 'news' | 'post' | 'comment'
export type AdminReviewAction = 'approve' | 'reject' | 'fold' | 'delete' | 'restore'

export interface AdminPendingSummary {
  pending_news_count: number
  pending_post_count: number
  pending_comment_count: number
  today_processed_count: number
}

export interface AdminPendingItem {
  id: number
  item_type: 'news' | 'post' | 'comment'
  target_type?: 'news' | 'post' | null
  title: string
  content_preview: string
  submitter: string
  source: string
  category_name: string
  tags?: string[]
  status: number
  status_label: string
  create_time?: string | null
  update_time?: string | null
}

export interface AdminPendingItemDetail extends AdminPendingItem {
  summary?: string
  content?: string
  cover_image?: string
  publish_time?: string | null
  editor?: string
  topic_name?: string
  tags?: string[]
  view_count?: number
  like_count?: number
  comment_count?: number
  favorite_count?: number
  heat_score?: number
  related_news_id?: number | null
  related_news_title?: string
  news_id?: number | null
  post_id?: number | null
  parent_id?: number | null
  parent_content?: string
  media_json?: unknown
  reason?: string
}

export interface AdminPendingItemsResponse {
  items: AdminPendingItem[]
  total: number
  page: number
  page_size: number
  summary: AdminPendingSummary
}

export interface AdminReviewActionRequest {
  action: AdminReviewAction
  reason?: string
}

export interface AdminReviewActionResult {
  item_type: 'news' | 'post' | 'comment'
  item_id: number
  action: AdminReviewAction
  status: number
  status_label: string
  updated: boolean
  message: string
  reason?: string
}


export interface AdminNewsSummary {
  total_count: number
  pending_count: number
  published_count: number
  offline_count: number
  unbound_topic_count: number
  feature_supported: boolean
}

export interface AdminNewsItem {
  id: number
  title: string
  summary: string
  content_preview: string
  cover_image: string
  category_id?: number | null
  category_name: string
  topic_id?: number | null
  topic_name: string
  source: string
  editor: string
  publish_time?: string | null
  view_count: number
  like_count: number
  comment_count: number
  favorite_count: number
  status: number
  status_label: string
  tags: string[]
  is_featured?: boolean | null
  feature_supported: boolean
  create_time?: string | null
  update_time?: string | null
}

export interface AdminNewsDetail extends AdminNewsItem {
  content: string
  source_url: string
}

export interface AdminNewsListResponse {
  items: AdminNewsItem[]
  total: number
  page: number
  page_size: number
  summary: AdminNewsSummary
}

export interface AdminNewsOptions {
  categories: Array<{ id: number; name: string; code?: string }>
  topics: Array<{ id: number; topic_name: string; heat_score?: number }>
  sources: string[]
  feature_supported: boolean
}

export interface AdminNewsQueryParams {
  keyword?: string
  category_id?: number | null
  source?: string
  status?: number | null
  is_featured?: boolean | null
  has_topic?: boolean | null
  start_time?: string
  end_time?: string
  page?: number
  page_size?: number
}

export interface AdminNewsUpdatePayload {
  title: string
  summary: string
  content: string
  source: string
  category_id?: number | null
  cover_image: string
  tags: string[]
  publish_time?: string | null
}

export interface AdminNewsActionResult {
  news_id: number
  action: string
  updated: boolean
  status?: number | null
  status_label: string
  message: string
}

export interface AdminPostSummary {
  total_count: number
  pending_count: number
  normal_count: number
  folded_count: number
  deleted_count: number
  reported_count: number
  feature_supported: boolean
}

export interface AdminPostItem {
  id: number
  title: string
  content_preview: string
  user_id?: number | null
  username: string
  nickname: string
  author_name: string
  related_news_id?: number | null
  related_news_title: string
  topic_id?: number | null
  topic_name: string
  tags: string[]
  like_count: number
  comment_count: number
  favorite_count: number
  heat_score: number
  status: number
  status_label: string
  is_featured?: boolean | null
  feature_supported: boolean
  create_time?: string | null
  update_time?: string | null
}

export interface AdminPostDetail extends AdminPostItem {
  content: string
  recent_comments: Array<{
    id: number
    user_id?: number | null
    username: string
    content: string
    like_count: number
    status: number
    status_label: string
    create_time?: string | null
  }>
}

export interface AdminPostListResponse {
  items: AdminPostItem[]
  total: number
  page: number
  page_size: number
  summary: AdminPostSummary
}

export interface AdminPostOptions {
  statuses: Array<{ label: string; value: number }>
  tags: string[]
  feature_supported: boolean
}

export interface AdminPostQueryParams {
  keyword?: string
  user_id?: number | null
  username?: string
  status?: number | null
  tag?: string
  related_news_id?: number | null
  is_featured?: boolean | null
  start_time?: string
  end_time?: string
  page?: number
  page_size?: number
}

export interface AdminPostActionResult {
  post_id: number
  action: string
  updated: boolean
  status?: number | null
  status_label: string
  message: string
}

export interface AdminCommentSummary {
  total_count: number
  news_comment_count: number
  post_comment_count: number
  pending_count: number
  folded_count: number
  deleted_count: number
  reported_count: number
  report_supported: boolean
}

export interface AdminCommentMediaJson {
  images?: string[]
  emojis?: string[]
}

export interface AdminCommentItem {
  id: number
  comment_type: 'news' | 'post'
  comment_type_label: string
  target_id?: number | null
  target_title: string
  target_source: string
  user_id?: number | null
  username: string
  nickname: string
  author_name: string
  parent_id?: number | null
  parent_content: string
  content: string
  content_preview: string
  media_json?: AdminCommentMediaJson | string | null
  like_count: number
  reply_count: number
  status: number
  status_label: string
  create_time?: string | null
  update_time?: string | null
}

export interface AdminCommentDetail extends AdminCommentItem {
  context: {
    target_id?: number | null
    target_title?: string
    target_source?: string
    target_publish_time?: string | null
    target_summary?: string
    missing?: boolean
  }
  replies: Array<{
    id: number
    user_id?: number | null
    username: string
    content: string
    media_json?: AdminCommentMediaJson | string | null
    like_count: number
    status: number
    status_label: string
    create_time?: string | null
  }>
}

export interface AdminCommentListResponse {
  items: AdminCommentItem[]
  total: number
  page: number
  page_size: number
  summary: AdminCommentSummary
}

export interface AdminCommentOptions {
  statuses: Array<{ label: string; value: number }>
  types: Array<{ label: string; value: 'all' | 'news' | 'post' }>
  report_supported: boolean
}

export interface AdminCommentQueryParams {
  type?: 'all' | 'news' | 'post'
  keyword?: string
  user_id?: number | null
  username?: string
  status?: number | null
  news_id?: number | null
  post_id?: number | null
  has_parent?: boolean | null
  start_time?: string
  end_time?: string
  page?: number
  page_size?: number
}

export interface AdminCommentActionResult {
  comment_id: number
  comment_type: 'news' | 'post'
  action: string
  updated: boolean
  status?: number | null
  status_label: string
  message: string
}

// ── M10: System Config types ───────────────────────────────────────

export interface SystemConfigItem {
  id: number
  config_key: string
  config_value: string | null
  config_type: string
  description: string
  editable: boolean
  created_at?: string | null
  updated_at?: string | null
}

export interface SystemConfigListResponse {
  items: SystemConfigItem[]
  total: number
}

export interface SystemConfigUpdateRequest {
  items: Array<{ config_key: string; config_value: string }>
}

// ── M10: AI Config types ────────────────────────────────────────────

export interface AIConfigResponse {
  service_url: string
  model_name: string
  api_key_configured: boolean
  timeout: number
  max_input_length: number
  enable_real_llm: boolean
  enable_fallback: boolean
  enable_cache: boolean
  cache_supported: boolean
  risk_threshold_low: number
  risk_threshold_medium: number
  sensitive_words: string[]
  risk_rules: Array<Record<string, unknown>>
  fallback_strategy: Record<string, unknown>
  service_status: string
  last_check_time?: string | null
}

export interface AIConfigUpdateRequest {
  service_url?: string
  model_name?: string
  api_key?: string
  timeout?: number
  max_input_length?: number
  enable_real_llm?: boolean
  enable_fallback?: boolean
  risk_threshold_low?: number
  risk_threshold_medium?: number
  sensitive_words?: string
  risk_rules?: string
  fallback_strategy?: string
}

export interface AIConfigTestResult {
  status: string
  latency_ms: number
  message: string
}

// ── M10: Prompt Template types ──────────────────────────────────────

export interface PromptTemplateItem {
  id: number
  name: string
  function_type: string
  prompt_content: string
  version: string
  status: number
  is_default: number
  remark: string
  created_at?: string | null
  updated_at?: string | null
}

export interface PromptTemplateListResponse {
  items: PromptTemplateItem[]
  total: number
  page: number
  page_size: number
}

export interface PromptTemplatePayload {
  name: string
  function_type: string
  prompt_content: string
  version?: string
  status?: number
  is_default?: number
  remark?: string
}

export interface PromptTemplateStatusRequest {
  status: number
}

export interface PromptTemplateOptions {
  function_types: Array<{ label: string; value: string }>
}

export interface PromptTemplateQueryParams {
  function_type?: string
  status?: number | null
  keyword?: string
  page?: number
  page_size?: number
}

// ── M10: AI Call Records types ──────────────────────────────────────

export interface AdminAICallRecordItem {
  id: number
  user_id?: number | null
  username: string
  function_type: string
  input_length: number
  status: number
  status_label: string
  risk_level: string
  is_fallback: boolean
  error_message: string
  created_at?: string | null
}

export interface AdminAICallRecordSummary {
  total_count: number
  today_count: number
  fallback_count: number
}

export interface AdminAICallRecordListResponse {
  items: AdminAICallRecordItem[]
  total: number
  page: number
  page_size: number
  summary: AdminAICallRecordSummary
  fallback_supported: boolean
}

export interface AdminAICallRecordQueryParams {
  function_type?: string
  status?: number | null
  risk_level?: string
  is_fallback?: boolean | null
  user_id?: number | null
  start_time?: string
  end_time?: string
  page?: number
  page_size?: number
}

export interface PaginationResponse<T> {
  list: T[]
  total: number
  page: number
  page_size: number
}

export async function getDashboard(): Promise<AdminDashboard> {
  return request.get('/api/admin/dashboard')
}

export async function getPendingItems(params: {
  type?: AdminPendingItemType
  keyword?: string
  status?: number | null
  page?: number
  pageSize?: number
} = {}): Promise<AdminPendingItemsResponse> {
  return request.get('/api/admin/pending-items', {
    params: {
      type: params.type ?? 'all',
      keyword: params.keyword || undefined,
      status: params.status ?? undefined,
      page: params.page ?? 1,
      page_size: params.pageSize ?? 10,
    },
  })
}

export async function getPendingItemDetail(itemType: Exclude<AdminPendingItemType, 'all'>, itemId: number): Promise<AdminPendingItemDetail> {
  return request.get(`/api/admin/pending-items/${itemType}/${itemId}`)
}

export async function reviewPendingItem(
  itemType: Exclude<AdminPendingItemType, 'all'>,
  itemId: number,
  payload: AdminReviewActionRequest,
): Promise<AdminReviewActionResult> {
  return request.post(`/api/admin/pending-items/${itemType}/${itemId}/review`, payload)
}

export async function getPendingPosts(
  page: number = 1,
  pageSize: number = 10
): Promise<PaginationResponse<PendingPostItem>> {
  return request.get('/api/admin/pending-posts', {
    params: { page, page_size: pageSize },
  })
}

export async function getAdminUserOptions(): Promise<AdminUserOptions> {
  return request.get('/api/admin/users/options')
}

export async function getUsers(params: AdminUserQueryParams = {}): Promise<AdminUserListResponse> {
  return request.get('/api/admin/users', {
    params: {
      keyword: params.keyword || undefined,
      role: params.role || undefined,
      status: params.status ?? undefined,
      start_time: params.start_time || undefined,
      end_time: params.end_time || undefined,
      page: params.page ?? 1,
      page_size: params.page_size ?? 10,
    },
  })
}

export async function getUserDetail(userId: number): Promise<AdminUserDetail> {
  return request.get(`/api/admin/users/${userId}`)
}

export async function changeUserRole(
  userId: number,
  payload: AdminUserRoleRequest,
): Promise<AdminUserActionResult> {
  return request.post(`/api/admin/users/${userId}/role`, payload)
}

export async function changeUserStatus(
  userId: number,
  payload: AdminUserStatusRequest,
): Promise<AdminUserActionResult> {
  return request.post(`/api/admin/users/${userId}/status`, payload)
}

export async function getSystemConfig(): Promise<SystemConfigListResponse> {
  return request.get('/api/admin/system-config')
}

export async function updateSystemConfig(payload: SystemConfigUpdateRequest): Promise<{ updated: number; message: string }> {
  return request.put('/api/admin/system-config', payload)
}

// ── M10: AI Config API ──────────────────────────────────────────────

export async function getAIConfig(): Promise<AIConfigResponse> {
  return request.get('/api/admin/ai-config')
}

export async function updateAIConfig(payload: AIConfigUpdateRequest): Promise<{ updated: number; message: string }> {
  return request.put('/api/admin/ai-config', payload)
}

export async function testAIConnection(): Promise<AIConfigTestResult> {
  return request.post('/api/admin/ai-config/test')
}

// ── M10: Prompt Template API ────────────────────────────────────────

export async function getPromptTemplateOptions(): Promise<PromptTemplateOptions> {
  return request.get('/api/admin/prompt-templates/options')
}

export async function getPromptTemplates(params: PromptTemplateQueryParams = {}): Promise<PromptTemplateListResponse> {
  return request.get('/api/admin/prompt-templates', {
    params: {
      function_type: params.function_type || undefined,
      status: params.status ?? undefined,
      keyword: params.keyword || undefined,
      page: params.page ?? 1,
      page_size: params.page_size ?? 10,
    },
  })
}

export async function getPromptTemplateDetail(templateId: number): Promise<PromptTemplateItem> {
  return request.get(`/api/admin/prompt-templates/${templateId}`)
}

export async function createPromptTemplate(payload: PromptTemplatePayload): Promise<PromptTemplateItem> {
  return request.post('/api/admin/prompt-templates', payload)
}

export async function updatePromptTemplate(templateId: number, payload: PromptTemplatePayload): Promise<PromptTemplateItem> {
  return request.put(`/api/admin/prompt-templates/${templateId}`, payload)
}

export async function updatePromptTemplateStatus(templateId: number, payload: PromptTemplateStatusRequest): Promise<{ template_id: number; action: string; updated: boolean; message: string }> {
  return request.post(`/api/admin/prompt-templates/${templateId}/status`, payload)
}

export async function setPromptTemplateDefault(templateId: number): Promise<{ template_id: number; action: string; updated: boolean; message: string }> {
  return request.post(`/api/admin/prompt-templates/${templateId}/default`)
}

// ── M10: AI Call Records API ────────────────────────────────────────

export async function getAICallRecords(params: AdminAICallRecordQueryParams = {}): Promise<AdminAICallRecordListResponse> {
  return request.get('/api/admin/ai-call-records', {
    params: {
      function_type: params.function_type || undefined,
      status: params.status ?? undefined,
      risk_level: params.risk_level || undefined,
      is_fallback: params.is_fallback ?? undefined,
      user_id: params.user_id ?? undefined,
      start_time: params.start_time || undefined,
      end_time: params.end_time || undefined,
      page: params.page ?? 1,
      page_size: params.page_size ?? 10,
    },
  })
}


export async function getAdminNewsOptions(): Promise<AdminNewsOptions> {
  return request.get('/api/admin/news/options')
}

export async function getAdminNewsList(params: AdminNewsQueryParams = {}): Promise<AdminNewsListResponse> {
  return request.get('/api/admin/news', {
    params: {
      keyword: params.keyword || undefined,
      category_id: params.category_id ?? undefined,
      source: params.source || undefined,
      status: params.status ?? undefined,
      is_featured: params.is_featured ?? undefined,
      has_topic: params.has_topic ?? undefined,
      start_time: params.start_time || undefined,
      end_time: params.end_time || undefined,
      page: params.page ?? 1,
      page_size: params.page_size ?? 10,
    },
  })
}

export async function getAdminNewsDetail(newsId: number): Promise<AdminNewsDetail> {
  return request.get(`/api/admin/news/${newsId}`)
}

export async function updateAdminNews(newsId: number, payload: AdminNewsUpdatePayload): Promise<AdminNewsDetail> {
  return request.put(`/api/admin/news/${newsId}`, payload)
}

export async function reviewAdminNews(
  newsId: number,
  payload: AdminReviewActionRequest,
): Promise<AdminNewsActionResult> {
  return request.post(`/api/admin/news/${newsId}/review`, payload)
}

export async function updateAdminNewsTopic(newsId: number, topicId: number | null): Promise<AdminNewsDetail> {
  return request.post(`/api/admin/news/${newsId}/topic`, { topic_id: topicId })
}

export async function featureAdminNews(newsId: number): Promise<AdminNewsActionResult> {
  return request.post(`/api/admin/news/${newsId}/feature`)
}

export async function unfeatureAdminNews(newsId: number): Promise<AdminNewsActionResult> {
  return request.delete(`/api/admin/news/${newsId}/feature`)
}


export async function getAdminPostOptions(): Promise<AdminPostOptions> {
  return request.get('/api/admin/posts/options')
}

export async function getAdminPostList(params: AdminPostQueryParams = {}): Promise<AdminPostListResponse> {
  return request.get('/api/admin/posts', {
    params: {
      keyword: params.keyword || undefined,
      user_id: params.user_id ?? undefined,
      username: params.username || undefined,
      status: params.status ?? undefined,
      tag: params.tag || undefined,
      related_news_id: params.related_news_id ?? undefined,
      is_featured: params.is_featured ?? undefined,
      start_time: params.start_time || undefined,
      end_time: params.end_time || undefined,
      page: params.page ?? 1,
      page_size: params.page_size ?? 10,
    },
  })
}

export async function getAdminPostDetail(postId: number): Promise<AdminPostDetail> {
  return request.get(`/api/admin/posts/${postId}`)
}

export async function reviewAdminPost(
  postId: number,
  payload: AdminReviewActionRequest,
): Promise<AdminPostActionResult> {
  return request.post(`/api/admin/posts/${postId}/review`, payload)
}

export async function featureAdminPost(postId: number): Promise<AdminPostActionResult> {
  return request.post(`/api/admin/posts/${postId}/feature`)
}

export async function unfeatureAdminPost(postId: number): Promise<AdminPostActionResult> {
  return request.delete(`/api/admin/posts/${postId}/feature`)
}


export async function getAdminCommentOptions(): Promise<AdminCommentOptions> {
  return request.get('/api/admin/comments/options')
}

export async function getAdminCommentList(params: AdminCommentQueryParams = {}): Promise<AdminCommentListResponse> {
  return request.get('/api/admin/comments', {
    params: {
      type: params.type ?? 'all',
      keyword: params.keyword || undefined,
      user_id: params.user_id ?? undefined,
      username: params.username || undefined,
      status: params.status ?? undefined,
      news_id: params.news_id ?? undefined,
      post_id: params.post_id ?? undefined,
      has_parent: params.has_parent ?? undefined,
      start_time: params.start_time || undefined,
      end_time: params.end_time || undefined,
      page: params.page ?? 1,
      page_size: params.page_size ?? 10,
    },
  })
}

export async function getAdminCommentDetail(commentType: 'news' | 'post', commentId: number): Promise<AdminCommentDetail> {
  return request.get(`/api/admin/comments/${commentType}/${commentId}`)
}

export async function reviewAdminComment(
  commentType: 'news' | 'post',
  commentId: number,
  payload: AdminReviewActionRequest,
): Promise<AdminCommentActionResult> {
  return request.post(`/api/admin/comments/${commentType}/${commentId}/review`, payload)
}

export interface AdminHotTopicSupport {
  pin_supported: boolean
  hide_supported: boolean
  hide_uses_status?: boolean
  manual_rank_supported: boolean
}

export interface AdminHotTopicSummary {
  total_count: number
  news_hot_count: number
  community_hot_count: number
  topic_hot_count: number
  pinned_count: number
  hidden_count: number
}

export interface AdminHotTopicItem {
  id: number
  title: string
  hot_type: string
  target_type: string
  target_id?: number | null
  tag: string
  heat_score: number
  rank_no: number
  status: number
  status_label: string
  is_pinned?: boolean | null
  is_hidden: boolean
  target_title: string
  target_missing: boolean
  created_at?: string | null
  updated_at?: string | null
}

export interface AdminHotTopicListResponse {
  items: AdminHotTopicItem[]
  total: number
  page: number
  page_size: number
  summary: AdminHotTopicSummary
  support: AdminHotTopicSupport
}

export interface AdminHotTopicDetail extends AdminHotTopicItem {
  related_target: Record<string, unknown>
}

export interface AdminHotTopicOptions {
  target_types: Array<{ label: string; value: string }>
  statuses: Array<{ label: string; value: number }>
  support: AdminHotTopicSupport
}

export interface AdminHotTopicQueryParams {
  keyword?: string
  hot_type?: string
  target_type?: string
  status?: number | null
  is_pinned?: boolean | null
  is_hidden?: boolean | null
  start_time?: string
  end_time?: string
  page?: number
  page_size?: number
}

export interface AdminHotTopicActionResult {
  hot_id: number
  action: string
  updated: boolean
  rank_no?: number | null
  status?: number | null
  status_label: string
  message: string
}

export interface AdminTopicSupport {
  news_topic_table_supported: boolean
  keyword_supported: boolean
  description_supported: boolean
}

export interface AdminTopicSummary {
  total_count: number
  enabled_count: number
  disabled_count: number
  with_news_count: number
  without_news_count: number
}

export interface AdminTopicItem {
  id: number
  topic_name: string
  summary: string
  keyword_list: string[]
  heat_score: number
  news_count: number
  status: number
  status_label: string
  created_at?: string | null
  updated_at?: string | null
}

export interface AdminTopicListResponse {
  items: AdminTopicItem[]
  total: number
  page: number
  page_size: number
  summary: AdminTopicSummary
  support: AdminTopicSupport
}

export interface AdminTopicDetail extends AdminTopicItem {
  recent_news: AdminTopicNewsItem[]
}

export interface AdminTopicOptions {
  status_options: Array<{ label: string; value: number }>
  support: AdminTopicSupport
}

export interface AdminTopicQueryParams {
  keyword?: string
  status?: number | null
  has_news?: boolean | null
  start_time?: string
  end_time?: string
  page?: number
  page_size?: number
}

export interface AdminTopicPayload {
  topic_name: string
  summary: string
  keyword_list: string[] | string
  heat_score?: number
  status: number
}

export interface AdminTopicActionResult {
  topic_id: number
  action: string
  updated: boolean
  status?: number | null
  status_label: string
  affected_count: number
  message: string
}

export interface AdminTopicNewsItem {
  id: number
  title: string
  category_name: string
  source: string
  publish_time?: string | null
  status: number
  status_label: string
  topic_id?: number | null
}

export interface AdminTopicNewsResponse {
  items: AdminTopicNewsItem[]
  total: number
  page: number
  page_size: number
}

export async function getAdminHotTopicOptions(): Promise<AdminHotTopicOptions> {
  return request.get('/api/admin/hot-topics/options')
}

export async function getAdminHotTopicList(params: AdminHotTopicQueryParams = {}): Promise<AdminHotTopicListResponse> {
  return request.get('/api/admin/hot-topics', {
    params: {
      keyword: params.keyword || undefined,
      hot_type: params.hot_type || undefined,
      target_type: params.target_type || undefined,
      status: params.status ?? undefined,
      is_pinned: params.is_pinned ?? undefined,
      is_hidden: params.is_hidden ?? undefined,
      start_time: params.start_time || undefined,
      end_time: params.end_time || undefined,
      page: params.page ?? 1,
      page_size: params.page_size ?? 10,
    },
  })
}

export async function getAdminHotTopicDetail(hotId: number): Promise<AdminHotTopicDetail> {
  return request.get(`/api/admin/hot-topics/${hotId}`)
}

export async function updateAdminHotTopicRank(hotId: number, rankNo: number): Promise<AdminHotTopicActionResult> {
  return request.post(`/api/admin/hot-topics/${hotId}/rank`, { rank_no: rankNo })
}

export async function hideAdminHotTopic(hotId: number): Promise<AdminHotTopicActionResult> {
  return request.post(`/api/admin/hot-topics/${hotId}/hide`)
}

export async function restoreAdminHotTopic(hotId: number): Promise<AdminHotTopicActionResult> {
  return request.delete(`/api/admin/hot-topics/${hotId}/hide`)
}

export async function refreshAdminHotTopicHeat(hotId: number): Promise<AdminHotTopicActionResult> {
  return request.post(`/api/admin/hot-topics/${hotId}/refresh-heat`)
}

export async function getAdminTopicOptions(): Promise<AdminTopicOptions> {
  return request.get('/api/admin/topics/options')
}

export async function getAdminTopicList(params: AdminTopicQueryParams = {}): Promise<AdminTopicListResponse> {
  return request.get('/api/admin/topics', {
    params: {
      keyword: params.keyword || undefined,
      status: params.status ?? undefined,
      has_news: params.has_news ?? undefined,
      start_time: params.start_time || undefined,
      end_time: params.end_time || undefined,
      page: params.page ?? 1,
      page_size: params.page_size ?? 10,
    },
  })
}

export async function getAdminTopicDetail(topicId: number): Promise<AdminTopicDetail> {
  return request.get(`/api/admin/topics/${topicId}`)
}

export async function createAdminTopic(payload: AdminTopicPayload): Promise<AdminTopicDetail> {
  return request.post('/api/admin/topics', payload)
}

export async function updateAdminTopic(topicId: number, payload: AdminTopicPayload): Promise<AdminTopicDetail> {
  return request.put(`/api/admin/topics/${topicId}`, payload)
}

export async function updateAdminTopicStatus(topicId: number, status: number): Promise<AdminTopicActionResult> {
  return request.post(`/api/admin/topics/${topicId}/status`, { status })
}

export async function getAdminTopicNews(topicId: number, params: { keyword?: string; status?: number | null; page?: number; page_size?: number } = {}): Promise<AdminTopicNewsResponse> {
  return request.get(`/api/admin/topics/${topicId}/news`, {
    params: {
      keyword: params.keyword || undefined,
      status: params.status ?? undefined,
      page: params.page ?? 1,
      page_size: params.page_size ?? 10,
    },
  })
}

export async function getAdminTopicCandidateNews(topicId: number, params: { keyword?: string; status?: number | null; page?: number; page_size?: number } = {}): Promise<AdminTopicNewsResponse> {
  return request.get(`/api/admin/topics/${topicId}/candidate-news`, {
    params: {
      keyword: params.keyword || undefined,
      status: params.status ?? undefined,
      page: params.page ?? 1,
      page_size: params.page_size ?? 10,
    },
  })
}

export async function bindAdminTopicNews(topicId: number, newsIds: number[]): Promise<AdminTopicActionResult> {
  return request.post(`/api/admin/topics/${topicId}/bind-news`, { news_ids: newsIds })
}

export async function unbindAdminTopicNews(topicId: number, newsIds: number[]): Promise<AdminTopicActionResult> {
  return request.post(`/api/admin/topics/${topicId}/unbind-news`, { news_ids: newsIds })
}

// ── M8: Admin Timeline Management ─────────────────────────────

export interface AdminTimelineSupport {
  event_timeline_table_supported: boolean
  timeline_generate_supported: boolean
  timeline_cache_supported: boolean
}

export interface AdminTimelineOptionsResponse {
  status_options: Array<{ label: string; value: string }>
  news_count_options: Array<{ label: string; value: string }>
  support: AdminTimelineSupport
}

export interface AdminTimelineSummary {
  topic_count: number
  generated_count: number
  not_generated_count: number
  failed_count: number
  insufficient_news_count: number
  cache_error_count: number
}

export interface AdminTimelineItem {
  topic_id: number
  topic_name: string
  keyword_list: string[]
  news_count: number
  generate_status: string
  generate_status_label: string
  cache_status: string
  cache_status_label: string
  source_news_count: number
  generated_at?: string | null
  updated_at?: string | null
}

export interface AdminTimelineListResponse {
  items: AdminTimelineItem[]
  total: number
  page: number
  page_size: number
  summary: AdminTimelineSummary
}

export interface AdminTimelineNodeItem {
  event_id: number
  event_time: string
  event_title: string
  event_summary: string
  source_news_id: number
  source_title: string
  source_name: string
  event_type: string
  importance: number
}

export interface AdminTimelineCacheCheck {
  json_valid: boolean
  source_news_valid: boolean
  missing_source_news_ids: number[]
  message: string
}

export interface AdminTimelineDetailResponse {
  topic_id: number
  topic_name: string
  keyword_list: string[]
  generate_status: string
  generate_status_label: string
  generated_at?: string | null
  updated_at?: string | null
  source_news_ids: number[]
  timeline_nodes: AdminTimelineNodeItem[]
  source_news: Array<Record<string, unknown>>
  overview: string
  cache_check: AdminTimelineCacheCheck
  raw_json: string
}

export interface AdminTimelineSourceNewsItem {
  id: number
  title: string
  source: string
  publish_time?: string | null
  status: number
  status_label: string
  in_source_news_ids: boolean
}

export interface AdminTimelineSourceNewsResponse {
  topic_id: number
  topic_name: string
  items: AdminTimelineSourceNewsItem[]
  total: number
  page: number
  page_size: number
}

export interface AdminTimelineActionResult {
  topic_id: number
  action: string
  updated: boolean
  generate_status: string
  generate_status_label: string
  message: string
}

export interface AdminTimelineQueryParams {
  keyword?: string
  generate_status?: string
  news_count_type?: string
  has_cache?: boolean | null
  cache_error?: boolean | null
  start_time?: string
  end_time?: string
  page?: number
  page_size?: number
}

export async function getAdminTimelineOptions(): Promise<AdminTimelineOptionsResponse> {
  return request.get('/api/admin/timelines/options')
}

export async function getAdminTimelineList(params: AdminTimelineQueryParams = {}): Promise<AdminTimelineListResponse> {
  return request.get('/api/admin/timelines', {
    params: {
      keyword: params.keyword || undefined,
      generate_status: params.generate_status || undefined,
      news_count_type: params.news_count_type || undefined,
      has_cache: params.has_cache ?? undefined,
      cache_error: params.cache_error ?? undefined,
      start_time: params.start_time || undefined,
      end_time: params.end_time || undefined,
      page: params.page ?? 1,
      page_size: params.page_size ?? 10,
    },
  })
}

export async function getAdminTimelineDetail(topicId: number): Promise<AdminTimelineDetailResponse> {
  return request.get(`/api/admin/timelines/${topicId}`)
}

export async function getAdminTimelineSourceNews(topicId: number, params: { keyword?: string; status?: number | null; page?: number; page_size?: number } = {}): Promise<AdminTimelineSourceNewsResponse> {
  return request.get(`/api/admin/timelines/${topicId}/source-news`, {
    params: {
      keyword: params.keyword || undefined,
      status: params.status ?? undefined,
      page: params.page ?? 1,
      page_size: params.page_size ?? 10,
    },
  })
}

export async function generateAdminTimeline(topicId: number): Promise<AdminTimelineActionResult> {
  return request.post(`/api/admin/timelines/${topicId}/generate`)
}

export async function refreshAdminTimeline(topicId: number): Promise<AdminTimelineActionResult> {
  return request.post(`/api/admin/timelines/${topicId}/refresh`)
}

export async function clearAdminTimelineCache(topicId: number): Promise<AdminTimelineActionResult> {
  return request.delete(`/api/admin/timelines/${topicId}/cache`)
}

// M11: System Operations & Operation Logs

export interface AdminOpsStatusPart {
  status: 'normal' | 'abnormal' | 'unknown' | 'unsupported' | string
  message: string
}

export interface AdminOpsStatusResponse {
  backend: AdminOpsStatusPart
  database: AdminOpsStatusPart
  ai_service: AdminOpsStatusPart
  environment: string
  last_check_time?: string | null
}

export interface AdminOpsTableStatus {
  table_name: string
  display_name: string
  exists: boolean
  row_count?: number | null
}

export interface AdminOpsDatabaseResponse {
  connection_status: string
  database_name: string
  tables: AdminOpsTableStatus[]
  last_backup_time?: string | null
  backup_supported: boolean
}

export interface AdminBackupRecordItem {
  id: number
  backup_name: string
  backup_type: string
  file_path: string
  file_size: number
  status: string
  message: string
  operator_id?: number | null
  operator_name: string
  created_at?: string | null
  finished_at?: string | null
}

export interface AdminBackupRecordSummary {
  total_count: number
  success_count: number
  failed_count: number
  unsupported_count: number
  today_count: number
}

export interface AdminBackupRecordListResponse {
  items: AdminBackupRecordItem[]
  total: number
  page: number
  page_size: number
  summary: AdminBackupRecordSummary
}

export interface AdminBackupActionResult {
  backup_id?: number | null
  status: string
  message: string
}

export interface AdminStorageResponse {
  supported: boolean
  upload_dir?: string | null
  total_files: number
  total_size: number
  image_count: number
  document_count: number
  abnormal_count: number
  last_upload_time?: string | null
  message: string
}

export interface AdminOperationLogSummary {
  total_count: number
  success_count: number
  failed_count: number
  unsupported_count: number
  today_count: number
}

export interface AdminOperationLogItem {
  id: number
  operator_id?: number | null
  operator_name: string
  operator_role: string
  module: string
  action: string
  target_type: string
  target_id: string
  description: string
  ip_address: string
  result: string
  created_at?: string | null
}

export interface AdminOperationLogDetail extends AdminOperationLogItem {
  user_agent: string
  error_message: string
}

export interface AdminOperationLogListResponse {
  items: AdminOperationLogItem[]
  total: number
  page: number
  page_size: number
  summary: AdminOperationLogSummary
}

export interface AdminBackupQueryParams {
  status?: string
  backup_type?: string
  start_time?: string
  end_time?: string
  page?: number
  page_size?: number
}

export interface AdminOperationLogQueryParams {
  operator_keyword?: string
  module?: string
  action?: string
  result?: string
  start_time?: string
  end_time?: string
  page?: number
  page_size?: number
}

export async function getAdminOpsStatus(): Promise<AdminOpsStatusResponse> {
  return request.get('/api/admin/ops/status')
}

export async function getAdminOpsDatabase(): Promise<AdminOpsDatabaseResponse> {
  return request.get('/api/admin/ops/database')
}

export async function getAdminOpsBackups(params: AdminBackupQueryParams = {}): Promise<AdminBackupRecordListResponse> {
  return request.get('/api/admin/ops/backups', {
    params: {
      status: params.status || undefined,
      backup_type: params.backup_type || undefined,
      start_time: params.start_time || undefined,
      end_time: params.end_time || undefined,
      page: params.page ?? 1,
      page_size: params.page_size ?? 10,
    },
  })
}

export async function getAdminOpsStorage(): Promise<AdminStorageResponse> {
  return request.get('/api/admin/ops/storage')
}

export async function getAdminOpsLogs(params: AdminOperationLogQueryParams = {}): Promise<AdminOperationLogListResponse> {
  return request.get('/api/admin/ops/logs', {
    params: {
      operator_keyword: params.operator_keyword || undefined,
      module: params.module || undefined,
      action: params.action || undefined,
      result: params.result || undefined,
      start_time: params.start_time || undefined,
      end_time: params.end_time || undefined,
      page: params.page ?? 1,
      page_size: params.page_size ?? 10,
    },
  })
}

export async function getAdminOpsLogDetail(logId: number): Promise<AdminOperationLogDetail> {
  return request.get(`/api/admin/ops/logs/${logId}`)
}

// ── M12: Analytics types ───────────────────────────────────────────

export interface AdminAnalyticsOverview {
  total_users: number
  active_users: number
  total_news: number
  total_posts: number
  total_comments: number
  ai_generate_count: number
  timeline_count: number
  pending_count: number
}

export interface AdminTrendPoint {
  date: string
  news_count: number
  post_count: number
  comment_count: number
  ai_count: number
  fallback_count: number
  high_risk_count: number
}

export interface AdminAnalyticsTrendsResponse {
  content_trend: AdminTrendPoint[]
  ai_trend: AdminTrendPoint[]
  supported: boolean
}

export interface AdminTopNewsItem {
  rank: number
  id: number
  title: string
  source: string
  view_count: number
  comment_count: number
  topic_name: string
  publish_time?: string | null
}

export interface AdminTopPostItem {
  rank: number
  id: number
  title: string
  author_name: string
  comment_count: number
  like_count: number
  heat_score: number
  created_at?: string | null
}

export interface AdminAnalyticsTopContentResponse {
  top_news: AdminTopNewsItem[]
  top_posts: AdminTopPostItem[]
}

export interface AdminAiRiskItem {
  risk_level: string
  count: number
}

export interface AdminAnalyticsAiRiskResponse {
  items: AdminAiRiskItem[]
  supported: boolean
}

export interface AdminReviewPending {
  news: number
  posts: number
  comments: number
  total: number
}

export interface AdminReviewProcessed {
  approve: number
  reject: number
  fold: number
  delete: number
  restore: number
  total: number
}

export interface AdminAnalyticsReviewSummaryResponse {
  pending: AdminReviewPending
  processed: AdminReviewProcessed
  today_processed: number
}

export interface AdminContentOverviewItem {
  content_type: string
  id: number
  title: string
  creator_or_source: string
  status_label: string
  risk_level: string
  related_info: string
  updated_at?: string | null
  target_tab: string
}

export interface AdminAnalyticsContentOverviewResponse {
  items: AdminContentOverviewItem[]
  total: number
  page: number
  page_size: number
}

export interface AdminAnalyticsQueryParams {
  start_time?: string
  end_time?: string
}

export interface AdminContentOverviewQueryParams extends AdminAnalyticsQueryParams {
  type?: string
  status?: number | null
  keyword?: string
  risk_level?: string
  page?: number
  page_size?: number
}

// ── M12: Analytics API functions ───────────────────────────────────

export async function getAdminAnalyticsOverview(params: AdminAnalyticsQueryParams = {}): Promise<AdminAnalyticsOverview> {
  return request.get('/api/admin/analytics/overview', {
    params: {
      start_time: params.start_time || undefined,
      end_time: params.end_time || undefined,
    },
  })
}

export async function getAdminAnalyticsTrends(params: AdminAnalyticsQueryParams = {}): Promise<AdminAnalyticsTrendsResponse> {
  return request.get('/api/admin/analytics/trends', {
    params: {
      start_time: params.start_time || undefined,
      end_time: params.end_time || undefined,
    },
  })
}

export async function getAdminAnalyticsTopContent(params: AdminAnalyticsQueryParams & { type?: string; limit?: number } = {}): Promise<AdminAnalyticsTopContentResponse> {
  return request.get('/api/admin/analytics/top-content', {
    params: {
      start_time: params.start_time || undefined,
      end_time: params.end_time || undefined,
      type: params.type || undefined,
      limit: params.limit ?? 10,
    },
  })
}

export async function getAdminAnalyticsAiRisk(params: AdminAnalyticsQueryParams = {}): Promise<AdminAnalyticsAiRiskResponse> {
  return request.get('/api/admin/analytics/ai-risk', {
    params: {
      start_time: params.start_time || undefined,
      end_time: params.end_time || undefined,
    },
  })
}

export async function getAdminAnalyticsReviewSummary(params: AdminAnalyticsQueryParams = {}): Promise<AdminAnalyticsReviewSummaryResponse> {
  return request.get('/api/admin/analytics/review-summary', {
    params: {
      start_time: params.start_time || undefined,
      end_time: params.end_time || undefined,
    },
  })
}

export async function getAdminAnalyticsContentOverview(params: AdminContentOverviewQueryParams = {}): Promise<AdminAnalyticsContentOverviewResponse> {
  return request.get('/api/admin/analytics/content-overview', {
    params: {
      type: params.type || undefined,
      status: params.status !== null && params.status !== undefined ? params.status : undefined,
      keyword: params.keyword || undefined,
      risk_level: params.risk_level || undefined,
      start_time: params.start_time || undefined,
      end_time: params.end_time || undefined,
      page: params.page ?? 1,
      page_size: params.page_size ?? 10,
    },
  })
}

