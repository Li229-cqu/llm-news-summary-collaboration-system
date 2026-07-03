/** 新闻互动模块 API 封装。受保护接口的 Token 由 request.ts 自动注入。 */

import request from './request'

export interface InteractionResult {
  target_id: number
  target_type: string
  action: string
  status: boolean
  like_count: number | null
  favorite_count: number | null
  message: string | null
}

export interface CommentMediaJson {
  images?: string[]
  emojis?: string[]
}

export interface CommentCreatePayload {
  content: string
  media_json?: CommentMediaJson | null
}

export interface CommentReplyPayload {
  content: string
  media_json?: CommentMediaJson | null
}

export interface CommentItem {
  id: number
  news_id: number
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
  reply_to_user_id?: number | null
  reply_to_username?: string
  reply_to_nickname?: string
  reply_to_content?: string
}

export interface CommentMediaUploadResponse {
  url: string
  filename: string
  size: number
}

export interface CommentListResponse {
  list: CommentItem[]
  total: number
}

export interface CommentLikeResult {
  comment_id: number
  liked: boolean
  like_count: number
}

export interface CommentDeleteResult {
  comment_id: number
  deleted: boolean
  news_id: number
  comment_count: number
}

/** 点赞新闻，需要登录。 */
export function likeNews(newsId: number | string) {
  return request.post<InteractionResult, InteractionResult>(`/api/news/${newsId}/like`)
}

/** 取消点赞新闻，需要登录。 */
export function unlikeNews(newsId: number | string) {
  return request.delete<InteractionResult, InteractionResult>(`/api/news/${newsId}/like`)
}

/** 收藏新闻，需要登录。 */
export function favoriteNews(newsId: number | string) {
  return request.post<InteractionResult, InteractionResult>(`/api/news/${newsId}/favorite`)
}

/** 取消收藏新闻，需要登录。 */
export function unfavoriteNews(newsId: number | string) {
  return request.delete<InteractionResult, InteractionResult>(`/api/news/${newsId}/favorite`)
}

/** 获取新闻评论，未登录时同样可访问。 */
export function getNewsComments(newsId: number | string) {
  return request.get<CommentListResponse, CommentListResponse>(`/api/news/${newsId}/comments`)
}

/** 发布新闻一级评论，需要登录。 */
export function createNewsComment(
  newsId: number | string,
  payload: CommentCreatePayload,
) {
  return request.post<CommentItem, CommentItem>(`/api/news/${newsId}/comments`, payload)
}

/** 回复指定评论，需要登录。 */
export function replyComment(commentId: number | string, payload: CommentReplyPayload) {
  return request.post<CommentItem, CommentItem>(`/api/comments/${commentId}/reply`, payload)
}

/** 点赞评论，需要登录。 */
export function likeComment(commentId: number | string) {
  return request.post<CommentLikeResult, CommentLikeResult>(`/api/comments/${commentId}/like`)
}

/** 删除新闻评论，需要登录。*/
export function deleteNewsComment(commentId: number | string) {
  return request.delete<CommentDeleteResult, CommentDeleteResult>(`/api/comments/${commentId}`)
}

/** 上传评论富媒体图片，需要登录。 */
export function uploadCommentMedia(file: File) {
  const formData = new FormData()
  formData.append('file', file)
  return request.post<CommentMediaUploadResponse, CommentMediaUploadResponse>(
    '/api/comments/media/upload',
    formData,
  )
}

