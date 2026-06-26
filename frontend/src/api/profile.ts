import request from '@/api/http'
import type { NewsItem } from '@/api/news'

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

export async function getRecommendations(
  limit: number = 10
): Promise<PaginationResponse<NewsItem>> {
  return request.get('/api/profile/recommendations', {
    params: { limit },
  })
}

export interface ReadingTrajectoryParams {
  days?: number
  limit?: number
}

export interface ReadingTrajectorySummary {
  total_reads: number
  unique_news_count: number
  category_count: number
  topic_count: number
  top_category: string
  top_topic: string
  date_range: string
}

export interface ReadingTrajectoryNode {
  id: string
  name: string
  type: 'category' | 'topic' | 'news'
  value: number
  read_count?: number
  news_id?: number | null
  category_id?: number | null
  topic_id?: number | null
  category_name?: string | null
  topic_name?: string | null
  browse_time?: string | null
}

export interface ReadingTrajectoryEdge {
  source: string
  target: string
  value: number
  type: 'category_topic' | 'topic_news' | 'sequence'
}

export interface ReadingTopCategory {
  category_id?: number | null
  category_name: string
  read_count: number
}

export interface ReadingTopTopic {
  topic_id?: number | null
  topic_name: string
  read_count: number
}

export interface ReadingRecentNews {
  news_id: number
  title: string
  category_name: string
  topic_name: string
  browse_time: string
}

export interface ReadingTrajectoryResponse {
  summary: ReadingTrajectorySummary
  nodes: ReadingTrajectoryNode[]
  edges: ReadingTrajectoryEdge[]
  top_categories: ReadingTopCategory[]
  top_topics: ReadingTopTopic[]
  recent_news: ReadingRecentNews[]
}

export async function getReadingTrajectory(
  params?: ReadingTrajectoryParams
): Promise<ReadingTrajectoryResponse> {
  return request.get('/api/profile/reading-trajectory', {
    params: { days: 30, limit: 100, ...params },
  })
}
