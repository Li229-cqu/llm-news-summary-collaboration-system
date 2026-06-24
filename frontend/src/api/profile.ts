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

export interface AIRecordItem {
  id: number
  input_text: string
  candidate_titles: string[]
  summary_short: string
  summary_long?: string
  create_time?: string
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

export async function getAIRecords(
  page: number = 1,
  pageSize: number = 10
): Promise<PaginationResponse<AIRecordItem>> {
  return request.get('/api/profile/ai-records', {
    params: { page, page_size: pageSize },
  })
}
