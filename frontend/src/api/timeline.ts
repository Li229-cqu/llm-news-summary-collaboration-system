/** Timeline 模块 API 封装。所有请求均通过 backend 统一入口发起。 */

import request from './request'

export interface TimelineTopic {
  topic_id: number
  topic_name: string
  keyword_list: string[]
  heat_score: number
  summary: string
  news_count: number
  source_type?: 'manual' | 'auto' | string
  auto_generated_at?: string | null
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

// ── 自动聚类生成事件脉络 ──────────────────────────────────────────

export interface AutoClusterRequest {
  days?: number
  max_news?: number
  max_write_topics?: number
  use_llm_polish?: boolean
  dry_run?: boolean
  confirm?: boolean
  confirmed_topics?: ConfirmedTimelineTopic[]
}

export interface AutoClusterTopicPreview {
  topic_name: string
  summary?: string
  keyword_list?: string[]
  heat_score?: number
  news_count?: number
  news_ids?: number[]
  event_point_count?: number
  quality_status?: string
  quality_score?: number
  quality_flags?: string[]
  quality_reasons?: string[]
  category_purity?: number
  entity_purity?: number
  core_entities?: string[]
  removed_count?: number
  removed_news_ids?: number[]
  removed_news_titles?: string[]
  cluster_size_raw?: number
  cluster_size_after_filter?: number
  split_from_large_cluster?: boolean
  k_used?: number
  event_merge_threshold?: number
  strict_entity_match?: boolean
  cluster_avg_similarity?: number
  cluster_entity_purity?: number
  split_reason?: string
  llm_used?: boolean
  llm_polished?: boolean
  representative_titles?: string[]
  event_points?: Array<Record<string, any>>
  timeline_preview?: Array<{
    event_title: string
    source_news_ids?: number[]
  }>
}

export interface AutoClusterSkippedTopic extends AutoClusterTopicPreview {
  reason?: string
}

export interface ConfirmedTimelineEventPoint {
  event_title?: string
  title?: string
  event_summary?: string
  summary?: string
  event_time?: string
  source_news_ids?: number[]
  representative_news_id?: number
  source_news_id?: number
  keywords?: string[]
}

export interface ConfirmedTimelineTopic {
  topic_name: string
  summary?: string
  keyword_list?: string[]
  news_ids: number[]
  event_points?: ConfirmedTimelineEventPoint[]
  quality_status?: string
  quality_score?: number
  quality_flags?: string[]
  quality_reasons?: string[]
  core_entities?: string[]
  removed_news_ids?: number[]
  removed_count?: number
  entity_purity?: number
  category_purity?: number
  heat_score?: number
  metadata?: Record<string, any>
}

export interface AutoClusterResponse {
  success: boolean
  dry_run: boolean
  message?: string
  total_candidates?: number
  recommended_count?: number
  skipped_count?: number
  summary?: {
    candidate_count?: number
    write_topic_count?: number
    skipped_count?: number
    updated_news_count?: number
    timeline_count?: number
    manual_topic_count?: number
    auto_active_count?: number
  }
  topics?: AutoClusterTopicPreview[]
  topics_to_insert?: AutoClusterTopicPreview[]
  skipped_topics?: AutoClusterSkippedTopic[]
  warnings?: string[]
}

/** 后台批量自动聚类生成事件脉络（dry_run=true 预览，dry_run=false+confirm=true 发布） */
export function autoClusterTimelineTopics(params: AutoClusterRequest) {
  return request.post<AutoClusterResponse, AutoClusterResponse>(
    '/api/timeline/topics/auto-cluster',
    params,
    { timeout: 180000 },
  )
}
