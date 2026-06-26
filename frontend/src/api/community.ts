import request from './request'

export interface CommunityPost {
  id: number
  title: string
  content: string
  author: string
  author_id: number
  created_at: string
  updated_at: string
  likes: number
  comments: number
  views: number
  tags: string[]
  liked?: boolean
  hot?: boolean
  official?: boolean
}

export interface CreatePostRequest {
  title: string
  content: string
  tags?: string[]
}

export interface PostListResponse {
  list: CommunityPost[]
  total: number
  page: number
  page_size: number
}

export interface CommentItem {
  id: number
  post_id: number
  content: string
  author: string
  author_id: number
  created_at: string
  likes: number
}

export interface CreateCommentRequest {
  content: string
}

export interface CommentListResponse {
  list: CommentItem[]
  total: number
  page: number
  page_size: number
}

export interface HotSearchItem {
  id: number
  keyword: string
  rank: number
  search_count: number
  trend: 'up' | 'down' | 'stable'
}

export interface AIHelperResponse {
  success: boolean
  message: string
  answer?: string
}

export interface CommentsSummaryResponse {
  summary: string
  sentiment: 'positive' | 'negative' | 'neutral'
  keyword: string
  source: 'llm' | 'fallback'
}

export interface LikeResponse {
  success: boolean
  liked: boolean
  count: number
}

export interface PostListParams {
  page?: number
  page_size?: number
  keyword?: string
}

export interface CommentListParams {
  page?: number
  page_size?: number
}

export function getPostList(params: PostListParams = {}) {
  return request.get<PostListResponse, PostListResponse>('/api/community/posts', { params })
}

export function createPost(data: CreatePostRequest) {
  return request.post<CommunityPost, CommunityPost>('/api/community/posts', data)
}

export function getPostDetail(postId: number | string) {
  return request.get<CommunityPost, CommunityPost>(`/api/community/posts/${postId}`)
}

export function createComment(postId: number | string, data: CreateCommentRequest) {
  return request.post<CommentItem, CommentItem>(`/api/community/posts/${postId}/comments`, data)
}

export function getComments(postId: number | string, params: CommentListParams = {}) {
  return request.get<CommentListResponse, CommentListResponse>(`/api/community/posts/${postId}/comments`, { params })
}

export function toggleLike(postId: number | string) {
  return request.post<LikeResponse, LikeResponse>(`/api/community/posts/${postId}/like`)
}

export function getHotSearch(params: { limit?: number } = {}) {
  return request.get<HotSearchItem[], HotSearchItem[]>('/api/community/hot-search', { params })
}

export function aiNewsHelper(question: string) {
  return request.post<AIHelperResponse, AIHelperResponse>('/api/community/ai-helper', { question })
}

export function getCommentsSummary(postId: number | string) {
  return request.get<CommentsSummaryResponse, CommentsSummaryResponse>(`/api/community/posts/${postId}/comments-summary`)
}
