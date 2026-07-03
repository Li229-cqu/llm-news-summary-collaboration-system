/** 新闻模块 API 封装。所有请求均通过 backend 统一入口发起。 */

import request from './request'

export interface NewsCategory {
  id: number
  name: string
  code: string
  sort: number
  status: number
}

export interface NewsItem {
  id: number
  title: string
  summary: string
  cover_image: string
  category_id: number
  category_name: string
  source: string
  editor: string
  publish_time: string
  view_count: number
  like_count: number
  comment_count: number
  favorite_count: number
  status: number
  tags: string[]
  topic_id?: number | null
  topic_name?: string
  source_url?: string
  recommendation_score?: number
  recommendation_reason?: string
  recommend_source?: 'related' | 'hot'
}

export interface NewsDetail extends NewsItem {
  content: string
  related_news: NewsItem[]
  recommended_news: NewsItem[]
  is_liked: boolean
  is_favorited: boolean
  timeline_news_count?: number
}

export interface NewsListParams {
  category?: string
  category_id?: number | string
  keyword?: string
  page?: number
  page_size?: number
}

export interface NewsListResponse {
  list: NewsItem[]
  total: number
  page: number
  page_size: number
}

export interface HotNewsItem {
  id: number
  title: string
  category_name: string
  source: string
  view_count: number
  comment_count: number
  like_count?: number
  favorite_count?: number
  cover_image?: string
  publish_time?: string
  heat_score?: number
  rank: number
}

export interface BrowseResult {
  news_id: number
  recorded: boolean
}

export interface HotNewsParams {
  limit?: number
  category_id?: number | string
}

export interface SearchNewsParams {
  keyword: string
  page?: number
  page_size?: number
}

/** 获取启用的新闻分类。 */
export function getNewsCategories() {
  return request.get<NewsCategory[], NewsCategory[]>('/api/news/categories')
}

/** 获取新闻列表，支持分类、关键词和分页参数。 */
export function getNewsList(params: NewsListParams = {}) {
  return request.get<NewsListResponse, NewsListResponse>('/api/news', { params })
}

/** 获取当前登录用户订阅分类下的新闻列表。*/
export function getSubscribedNews(params: Pick<NewsListParams, 'page' | 'page_size'> = {}) {
  return request.get<NewsListResponse, NewsListResponse>('/api/news/subscribed', { params })
}

/** 获取新闻热榜。 */
export function getHotNews(params: HotNewsParams = {}) {
  return request.get<HotNewsItem[], HotNewsItem[]>('/api/news/hot', { params })
}

/** 按关键词搜索新闻。 */
export function searchNews(params: SearchNewsParams) {
  return request.get<NewsListResponse, NewsListResponse>('/api/news/search', { params })
}

/** 获取新闻详情；Axios 请求拦截器会按需携带登录 Token。 */
export function getNewsDetail(newsId: number | string) {
  return request.get<NewsDetail, NewsDetail>(`/api/news/${newsId}`)
}

/** 记录新闻浏览行为，匿名访问同样可用。 */
export function recordBrowse(newsId: number | string) {
  return request.post<BrowseResult, BrowseResult>(`/api/news/${newsId}/browse`)
}
