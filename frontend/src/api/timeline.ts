/** Timeline 模块 API 封装。所有请求均通过 backend 统一入口发起。 */

import request from './request'

export interface TimelineTopic {
  topic_id: number
  topic_name: string
  keyword_list: string[]
  heat_score: number
  summary: string
  news_count: number
}

export interface TimelineNewsItem {
  id: number
  title: string
  content: string
  source: string
  publish_time: string
  summary?: string | null
  category_id?: number | null
  category_name?: string | null
  topic_id?: number | null
}

export interface TimelineNode {
  event_id: number
  event_time: string
  event_title: string
  event_summary: string
  source_news_id: number
  source_title: string
  source_name: string
  event_type?: 'policy' | 'reaction' | 'breakthrough' | 'outcome' | 'background' | 'other'
  importance?: number
  event_detail?: string
  related_event_ids?: number[]
  keywords?: string[]
}

export interface TimelinePhase {
  name: string
  start_event_id: number
  end_event_id: number
}

export interface TimelineRelationship {
  from_id: number
  to_id: number
  type?: 'causes' | 'follows' | 'parallel'
}

export interface TimelineResponse {
  topic_id: number
  topic_name: string
  timeline: TimelineNode[]
  source?: 'cache' | 'ai-service' | 'mock'
  generated_at?: string | null
  updated_at?: string | null
  generate_status?: 'cached' | 'generated' | 'mock' | 'generating'
  schema_version?: string
  overview?: string
  key_figures?: string[]
  phases?: TimelinePhase[]
  relationships?: TimelineRelationship[]
}

export interface TimelineNewsListResponse {
  topic_id: number
  topic_name: string
  news_items: TimelineNewsItem[]
}

export interface TimelineGenerateRequest {
  topic_id: number
  topic_name?: string
  news_items: TimelineNewsItem[]
}

/** 获取可查看事件脉络的话题列表。 */
export function getTimelineTopics() {
  return request.get<TimelineTopic[], TimelineTopic[]>('/api/timeline/topics')
}

/** 获取某个话题下的相关新闻列表。 */
export function getTimelineTopicNews(topicId: number | string) {
  return request.get<TimelineNewsListResponse, TimelineNewsListResponse>(`/api/timeline/topics/${topicId}/news`)
}

/** 生成指定话题的事件脉络时间线。 */
export function generateTimeline(topicId: number | string) {
  return request.post<TimelineResponse, TimelineResponse>(`/api/timeline/topics/${topicId}/generate`)
}

/** 获取指定话题的 timeline。 */
export function getTimeline(topicId: number | string) {
  return request.get<TimelineResponse, TimelineResponse>(`/api/timeline/topics/${topicId}`)
}
