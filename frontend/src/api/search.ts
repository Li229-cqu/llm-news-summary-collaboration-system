/** 统一搜索 API */
import request from './request'

export interface SearchResultItem {
  type: 'news' | 'community_post' | 'news_comment' | 'post_comment' | 'news_topic'
  id: number
  title: string | null
  content: string
  summary: string | null
  source: string | null
  publishTime: string | null
  relevance: string
  newsId?: number | null
  postId?: number | null
  topicId?: number | null
  categoryId?: number | null
}

export interface SearchResults {
  news: SearchResultItem[]
  posts: SearchResultItem[]
  totalNews: number
  totalPosts: number
}

export function searchAll(q: string): Promise<SearchResults> {
  return request.get('/api/search', { params: { q, pageSize: 20 } })
}
