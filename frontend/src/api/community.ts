import request from './request'

export interface CommunityPost {
  id: number
  title: string
  content: string
  author: string
  author_id: number
  avatar?: string
  created_at: string
  updated_at: string
  likes: number
  comments: number
  comment_count?: number
  views: number
  tags: string[]
  liked?: boolean
  is_favorited?: boolean
  favorite_count?: number
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
  user_id: number
  username: string
  nickname: string
  avatar: string
  parent_id: number | null
  content: string
  like_count: number
  status: number
  create_time: string
  is_liked: boolean
  replies: CommentItem[]
  media_json?: CommentMediaJson | null
  author?: string
  author_id?: number
  created_at?: string
  likes?: number
  reply_to_user_id?: number | null
  reply_to_username?: string
  reply_to_nickname?: string
  reply_to_content?: string
}

export interface CreateCommentRequest {
  content: string
  media_json?: CommentMediaJson | null
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
  title: string
  target_type: string
  target_id: number
  view_count?: number
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
  keywords: string[]
  key_points: string[]
  source: 'llm' | 'fallback'
}

export interface LikeResponse {
  success: boolean
  liked: boolean
  count: number
}

export interface CommentLikeResult {
  comment_id: number
  liked: boolean
  like_count: number
}

export interface CommentDeleteResponse {
  comment_id: number
  deleted: boolean
  post_id: number
  comment_count: number
}

export interface CommentMediaJson {
  images?: string[]
  emojis?: string[]
  files?: Array<{
    name?: string
    url?: string
    type?: string
  }>
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

export function replyComment(commentId: number | string, data: CreateCommentRequest) {
  return request.post<CommentItem, CommentItem>(`/api/community/comments/${commentId}/reply`, data)
}

export function getComments(postId: number | string, params: CommentListParams = {}) {
  return request.get<CommentListResponse, CommentListResponse>(`/api/community/posts/${postId}/comments`, { params })
}

export function toggleLike(postId: number | string) {
  return request.post<LikeResponse, LikeResponse>(`/api/community/posts/${postId}/like`)
}

export function unlikePost(postId: number | string) {
  return request.delete<LikeResponse, LikeResponse>(`/api/community/posts/${postId}/like`)
}

export interface FavoriteResponse {
  success: boolean
  is_favorited: boolean
  favorite_count: number
}

export function toggleFavorite(postId: number | string) {
  return request.post<FavoriteResponse, FavoriteResponse>(`/api/community/posts/${postId}/favorite`)
}

export function unfavoritePost(postId: number | string) {
  return request.delete<FavoriteResponse, FavoriteResponse>(`/api/community/posts/${postId}/favorite`)
}

export function recordPostBrowse(postId: number | string) {
  return request.post<{ recorded: boolean; message: string }, { recorded: boolean; message: string }>(`/api/community/posts/${postId}/browse`)
}

export function getPostFavoriteStatus(postId: number | string) {
  return request.get<{ is_favorited: boolean }, { is_favorited: boolean }>(`/api/community/posts/${postId}/favorite/status`)
}

export function likeComment(commentId: number | string) {
  return request.post<CommentLikeResult, CommentLikeResult>(`/api/community/comments/${commentId}/like`)
}

export function deleteComment(commentId: number | string) {
  return request.delete<CommentDeleteResponse, CommentDeleteResponse>(`/api/community/comments/${commentId}`)
}

export function getHotSearch(params: { limit?: number } = {}) {
  return request.get<HotSearchItem[], HotSearchItem[]>('/api/community/hot-search', { params })
}

export interface TagCount {
  name: string
  count: number
}

export function getHotTags(params: { limit?: number } = {}) {
  return request.get<TagCount[], TagCount[]>('/api/community/hot-tags', { params })
}

export function getAvailableTags() {
  return request.get<TagCount[], TagCount[]>('/api/community/available-tags')
}

export function aiNewsHelper(question: string) {
  return request.post<AIHelperResponse, AIHelperResponse>('/api/community/ai-helper', { question }, { timeout: 60000 })
}

export function getCommentsSummary(postId: number | string) {
  return request.get<CommentsSummaryResponse, CommentsSummaryResponse>(`/api/community/posts/${postId}/comments-summary`)
}

export function generateCommentsSummary(comments: string[]) {
  return request.post<CommentsSummaryResponse, CommentsSummaryResponse>(
    '/api/community/comments/summary',
    { comments },
    { timeout: 30000 }
  )
}
