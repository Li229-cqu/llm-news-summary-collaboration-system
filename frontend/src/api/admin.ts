import request from '@/api/http'

export interface AdminDashboard {
  user_count: number
  news_count: number
  post_count: number
  pending_count: number
}

export interface UserItem {
  id: number
  username: string
  nickname: string
  role: string
  status: number
  create_time?: string
}

export interface PendingPostItem {
  id: number
  title: string
  content: string
  username: string
  author: string
  user_id: number
  status: number
  create_time: string
  update_time: string
}

export interface AuditResponse {
  id: number
  status: number
  message: string
  reason?: string
}

export interface HotTopicItem {
  id: number
  title: string
  heat_score: number
  target_type?: string
  target_id?: number
  tag?: string
  rank_no: number
  status: number
  create_time?: string
  update_time?: string
}

export interface HotTopicForm {
  title: string
  heat_score: number
  target_type?: string
  target_id?: number
  tag?: string
  rank_no: number
  status: number
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

export async function getPendingPosts(
  page: number = 1,
  pageSize: number = 10
): Promise<PaginationResponse<PendingPostItem>> {
  return request.get('/api/admin/pending-posts', {
    params: { page, page_size: pageSize },
  })
}

export async function approvePost(postId: number): Promise<AuditResponse> {
  return request.post(`/api/admin/posts/${postId}/approve`)
}

export async function rejectPost(postId: number, reason?: string): Promise<AuditResponse> {
  return request.post(`/api/admin/posts/${postId}/reject`, { reason })
}

export async function getUsers(
  page: number = 1,
  pageSize: number = 10
): Promise<PaginationResponse<UserItem>> {
  return request.get('/api/admin/users', {
    params: { page, page_size: pageSize },
  })
}

export async function getSystemConfig(): Promise<Record<string, unknown>> {
  return request.get('/api/admin/system-config')
}

// ==================== 新闻热搜榜管理 ====================

export async function getNewsHotRanking(
  page: number = 1,
  pageSize: number = 20
): Promise<PaginationResponse<HotTopicItem>> {
  return request.get('/api/admin/news-hot-ranking', {
    params: { page, page_size: pageSize },
  })
}

export async function createNewsHot(data: HotTopicForm): Promise<HotTopicItem> {
  return request.post('/api/admin/news-hot-ranking', data)
}

export async function updateNewsHot(id: number, data: Partial<HotTopicForm>): Promise<HotTopicItem> {
  return request.put(`/api/admin/news-hot-ranking/${id}`, data)
}

export async function deleteNewsHot(id: number): Promise<{ id: number; deleted: boolean }> {
  return request.delete(`/api/admin/news-hot-ranking/${id}`)
}

// ==================== 社区热搜管理 ====================

export async function getCommunityHotTopics(
  page: number = 1,
  pageSize: number = 20
): Promise<PaginationResponse<HotTopicItem>> {
  return request.get('/api/admin/community-hot-topics', {
    params: { page, page_size: pageSize },
  })
}

export async function createCommunityHot(data: HotTopicForm): Promise<HotTopicItem> {
  return request.post('/api/admin/community-hot-topics', data)
}

export async function updateCommunityHot(id: number, data: Partial<HotTopicForm>): Promise<HotTopicItem> {
  return request.put(`/api/admin/community-hot-topics/${id}`, data)
}

export async function deleteCommunityHot(id: number): Promise<{ id: number; deleted: boolean }> {
  return request.delete(`/api/admin/community-hot-topics/${id}`)
}

// ==================== 简化热搜管理（E2） ====================

export interface SimpleHotTopicItem {
  id: number
  keyword: string
  heat: number
  is_pinned: boolean
  status: number
  create_time?: string
  update_time?: string
}

export interface SimpleHotTopicForm {
  keyword: string
  heat: number
}

export interface SimpleHotTopicUpdateForm {
  keyword?: string
  heat?: number
  is_pinned?: boolean
  status?: number
}

export async function getHotTopics(
  page: number = 1,
  pageSize: number = 20
): Promise<PaginationResponse<SimpleHotTopicItem>> {
  return request.get('/api/admin/hot-topics', {
    params: { page, page_size: pageSize },
  })
}

export async function createHotTopic(data: SimpleHotTopicForm): Promise<SimpleHotTopicItem> {
  return request.post('/api/admin/hot-topics', data)
}

export async function updateHotTopic(
  id: number,
  data: SimpleHotTopicUpdateForm
): Promise<SimpleHotTopicItem> {
  return request.put(`/api/admin/hot-topics/${id}`, data)
}

export async function deleteHotTopic(id: number): Promise<{ id: number; deleted: boolean }> {
  return request.delete(`/api/admin/hot-topics/${id}`)
}
