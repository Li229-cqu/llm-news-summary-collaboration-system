import request from '@/api/http'

export interface ProfileOverview {
  user_id: number
  browse_count: number
  favorite_count: number
  comment_count: number
  ai_generate_count: number
}

export interface BrowseHistoryItem {
  news_id: number
  title: string
  category_name: string
  browse_time: string
}

export interface FavoriteItem {
  news_id: number
  title: string
  summary: string
  category_name: string
  source: string
  publish_time: string
}

export interface CommentRecordItem {
  comment_id: number
  news_id: number
  news_title: string
  category_name: string
  content: string
  like_count: number
  status: number
  create_time: string
}

export interface AIRecordItem {
  id: number
  source: string
  source_news_id?: number | string | null
  source_title: string
  input_text: string
  candidate_titles: string[]
  summary_short: string
  summary_long?: string
  risk_level?: string
  create_time?: string
}

export interface SubscriptionCategory {
  id: number
  name: string
  code: string
  subscribed: boolean
}

export interface SubscriptionResponse {
  subscribed_category_ids: number[]
  categories: SubscriptionCategory[]
}

export interface PaginationResponse<T> {
  list: T[]
  total: number
  page: number
  page_size: number
}

export async function getProfileOverview(): Promise<ProfileOverview> {
  return request.get('/api/profile/overview')
}

export async function getBrowseHistory(
  page: number = 1,
  pageSize: number = 10
): Promise<PaginationResponse<BrowseHistoryItem>> {
  return request.get('/api/profile/browse-history', {
    params: { page, page_size: pageSize },
  })
}

export async function getFavorites(
  page: number = 1,
  pageSize: number = 10
): Promise<PaginationResponse<FavoriteItem>> {
  return request.get('/api/profile/favorites', {
    params: { page, page_size: pageSize },
  })
}

export async function getComments(
  page: number = 1,
  pageSize: number = 10
): Promise<PaginationResponse<CommentRecordItem>> {
  return request.get('/api/profile/comments', {
    params: { page, page_size: pageSize },
  })
}

export async function getAIRecords(
  page: number = 1,
  pageSize: number = 10
): Promise<PaginationResponse<AIRecordItem>> {
  return request.get('/api/profile/ai-records', {
    params: { page, page_size: pageSize },
  })
}

export async function getSubscriptions(): Promise<SubscriptionResponse> {
  return request.get('/api/profile/subscriptions')
}

export async function updateSubscriptions(categoryIds: number[]): Promise<SubscriptionResponse> {
  return request.post('/api/profile/subscriptions', {
    category_ids: categoryIds,
  })
}
