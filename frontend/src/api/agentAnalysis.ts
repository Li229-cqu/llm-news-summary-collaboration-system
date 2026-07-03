/** Agent Analysis — 只读分析 API（Phase 4）。*/

import request from './request'

// ── Replay ────────────────────────────────────────────────

export interface ReplayStep {
  step: string
  label: string
  order: number
  status: string
  latency_ms: number
  tokens: number
  provider?: string
  model?: string
  input_data?: Record<string, any>
  output_data?: Record<string, any>
  error?: string
}

export interface TaskReplayResponse {
  task_id: number
  status: string
  total_steps: number
  completed_steps: number
  total_latency_ms: number
  steps: ReplayStep[]
}

export function getTaskReplay(taskId: number) {
  return request.get<TaskReplayResponse, TaskReplayResponse>(
    `/api/agent-analysis/task/${taskId}/replay`,
  )
}

// ── Explain ──────────────────────────────────────────────

export interface ReasoningItem {
  category: string
  label: string
  detail: string
  confidence: number
}

export interface ExplainResult {
  task_id: number
  summary: string
  reasoning: ReasoningItem[]
  confidence: number
  evidence: Record<string, any>
}

export function getTaskExplain(taskId: number) {
  return request.get<ExplainResult, ExplainResult>(
    `/api/agent-analysis/task/${taskId}/explain`,
  )
}

// ── DAG Steps ─────────────────────────────────────────────

export interface DAGStepData {
  step_name: string
  step_label: string
  step_order: number
  status: string
  latency_ms: number
  tokens: number
  provider?: string
  model?: string
}

export function getTaskSteps(taskId: number) {
  return request.get<DAGStepData[], DAGStepData[]>(
    `/api/agent-analysis/task/${taskId}/steps`,
  )
}

// ── DAG Graph（Phase 4: 节点 + 边图结构）─────────────────

export interface DAGNode {
  id: string
  label: string
  order: number
  status: string                // pending | running | completed | failed
  latency_ms: number
  tokens: number
  provider?: string
  model?: string
}

export interface DAGEdge {
  source: string
  target: string
}

export interface TaskDAGResponse {
  task_id: number
  status: string
  nodes: DAGNode[]
  edges: DAGEdge[]
}

/** 获取任务的 DAG 图结构（节点 + 边 + 实时状态）。 */
export function getTaskDAG(taskId: number) {
  return request.get<TaskDAGResponse, TaskDAGResponse>(
    `/api/agent-analysis/task/${taskId}/dag`,
  )
}

// ── Observability ────────────────────────────────────────

export interface ObservabilityOverview {
  total_tasks: number
  completed_tasks: number
  failed_tasks: number
  success_rate: number
  total_tokens: number
  avg_latency_ms: number
  total_steps: number
}

export interface ProviderStat {
  provider: string
  count: number
  percentage: number
}

export interface StepLatencyStat {
  step_name: string
  step_label: string
  avg_ms: number
  min_ms: number
  max_ms: number
  count: number
}

export interface StepTokenStat {
  step_name: string
  step_label: string
  total_tokens: number
  avg_tokens: number
  count: number
}

export interface TrendPoint {
  date: string         // YYYY-MM-DD
  completed: number
  failed: number
  total: number
}

export interface ObservabilityResponse {
  overview: ObservabilityOverview
  provider_stats: ProviderStat[]
  latency_stats: StepLatencyStat[]
  token_stats: StepTokenStat[]
  trend_stats: TrendPoint[]
}

export function getObservability(days: number = 7) {
  return request.get<ObservabilityResponse, ObservabilityResponse>(
    '/api/agent-analysis/observability',
    { params: { days } },
  )
}
