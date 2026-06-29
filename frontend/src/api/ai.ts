/** AI 标题摘要生成模块 API 封装。所有请求均通过 backend 统一入口发起。 */

import request from './request'

export interface AIGenerateRequest {
  input_text: string
  title_count?: number
  summary_type?: 'extract' | 'generate'
  summary_style?: string
  title_style?: string
  summary_length?: 'short' | 'long' | 'both'
  source?: 'manual' | 'news'
  source_news_id?: number | string | null
  source_title?: string
}

export interface NewsElement {
  who: string
  what: string
  when: string
  where: string
  why: string
  how: string
}

export interface ConsistencyCheck {
  score: number
  risk_level: 'low' | 'medium' | 'high'
  issues: string[]
  suggestions: string[]
}

export interface AIGenerateResponse {
  candidate_titles: string[]
  summary_short: string
  summary_long: string
  summary_points: string[]
  keywords: string[]
  elements: NewsElement
  consistency: ConsistencyCheck
  source?: 'mock' | 'llm'
}

/** 调用 AI 生成标题和摘要。 */
export function generateTitleSummary(data: AIGenerateRequest) {
  // AI 生成接口可能需要调用智谱 GLM-4-Flash，耗时 2-5 秒
  // 因此单独设置更长的 timeout（60 秒）
  return request.post<AIGenerateResponse, AIGenerateResponse, AIGenerateRequest>(
    '/api/ai/generate',
    data,
    { timeout: 60000 }  // 60 秒 timeout
  )
}

export interface AIGenerateRecordItem {
  id: number | string
  source: 'manual' | 'news'
  source_news_id: number | string | null
  source_title: string
  title_count: number
  risk_level: 'low' | 'medium' | 'high'
  created_at: string
}

export interface AIGenerateRecordDetail {
  id: number | string
  source: 'manual' | 'news'
  source_news_id: number | string | null
  source_title: string
  input_text: string
  params: Record<string, any>
  result: AIGenerateResponse
  created_at: string
}

export interface AIRecordListResponse {
  records: AIGenerateRecordItem[]
  total: number
}

export interface DeleteAIRecordResult {
  success: boolean
  message: string
}

/** 获取 AI 生成历史列表。 */
export function getAIHistory() {
  return request.get<AIRecordListResponse, AIRecordListResponse>('/api/ai/records')
}

/** 获取 AI 生成历史详情。 */
export function getAIRecordDetail(recordId: number | string) {
  return request.get<AIGenerateRecordDetail, AIGenerateRecordDetail>(`/api/ai/records/${recordId}`)
}

/** 删除 AI 生成历史。 */
export function deleteAIRecord(recordId: number | string) {
  return request.delete<DeleteAIRecordResult, DeleteAIRecordResult>(`/api/ai/records/${recordId}`)
}

export interface FileUploadResponse {
  success: boolean
  message: string
  content: string
  filename: string
}

/** 上传文件并提取文本内容。 */
export function uploadFile(formData: FormData) {
  return request.post<FileUploadResponse, FileUploadResponse, FormData>(
    '/api/ai/upload',
    formData,
    {
      headers: { 'Content-Type': 'multipart/form-data' },
    }
  )
}
