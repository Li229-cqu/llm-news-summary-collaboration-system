/** News Editor Agent — API 封装。
 *
 * 任务创建与查询（非流式 + SSE）。
 *
 * Phase 2 升级：
 * - 新增 runTextAgentMock() — 调用 /run-text-mock 启动后端 MockTaskRunner
 * - 前端不再使用 MOCK_STEP_OUTPUTS 做客户端模拟
 * - 保留 runTextAgent + SSE 用于真实模式（Phase 3+）
 */

import request from './request'

// ── 请求/响应类型 ──────────────────────────────────────────

export interface PipelineParams {
  title_count?: number
  summary_type?: string        // 'generate' | 'extract'
  summary_style?: string       // '简明扼要' | '客观正式' | '通俗易懂'
  title_style?: string         // '客观新闻型' | '吸引点击型' | '简洁概括型'
  summary_length?: string      // 'short' | 'long' | 'both'
  temperature?: number
  model?: string | null
}

export interface RunTextRequest {
  input_text: string
  news_id?: number | null
  task_type?: string
  pipeline_params?: PipelineParams
}

export interface RunTextResponse {
  task_id: number
  status: string
  message: string
}

/** 提交文本发起 Agent 流水线（真实 AI），返回 task_id。 */
export function runTextAgent(data: RunTextRequest) {
  return request.post<RunTextResponse, RunTextResponse, RunTextRequest>(
    '/api/news-editor-agent/run-text',
    data,
    { timeout: 10000 },
  )
}

/** Phase 2 Mock：提交文本启动后端 MockTaskRunner 状态机，返回 task_id。 */
export function runTextAgentMock(data: RunTextRequest) {
  return request.post<RunTextResponse, RunTextResponse, RunTextRequest>(
    '/api/news-editor-agent/run-text-mock',
    data,
    { timeout: 10000 },
  )
}

// ── 任务详情（轮询） ──────────────────────────────────────

export interface AgentStepLog {
  id: number
  task_id: number
  step_order: number
  step_name: string
  step_label: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  input_data: Record<string, any> | null
  output_data: Record<string, any> | null
  llm_provider: string | null
  llm_model: string | null
  llm_request_tokens: number
  llm_response_tokens: number
  response_ms: number
  error_message: string | null
  retry_count: number
  started_at: string | null
  completed_at: string | null
  created_at: string
}

export interface AgentTaskDetail {
  id: number
  user_id: number
  news_id: number | null
  task_type: string
  input_text: string
  cleaned_text: string | null
  status: string
  progress: number
  current_step: string | null
  result_json: any
  total_steps: number
  completed_steps: number
  failed_step: string | null
  error_message: string | null
  started_at: string | null
  completed_at: string | null
  created_at: string
  updated_at: string
  steps: AgentStepLog[]
}

/** 查询 Agent 任务状态与全部步骤日志（轮询用）。 */
export function getAgentTask(taskId: number) {
  return request.get<AgentTaskDetail, AgentTaskDetail>(
    `/api/news-editor-agent/task/${taskId}`,
    { timeout: 10000 },
  )
}

// ── Phase 1 Mock 数据（前端模拟流水线用） ─────────────────

/** 8 步元数据（与后端 pipeline.py STEP_META 一致） */
export const MOCK_STEP_META = [
  { name: 'clean',              label: '正文清洗',     order: 1 },
  { name: 'extract_keywords',   label: '关键词提取',   order: 2 },
  { name: 'extract_elements',   label: '六要素识别',   order: 3 },
  { name: 'generate_title_summary', label: '标题摘要生成', order: 4 },
  { name: 'match_topic',        label: '话题匹配',     order: 5 },
  { name: 'judge_timeline',     label: '时间线适配',   order: 6 },
  { name: 'check_consistency',  label: '一致性检查',   order: 7 },
  { name: 'edit_suggestions',   label: '编辑建议生成', order: 8 },
] as const

/** 每步 mock 输出（与后端 mock_api.py MOCK_STEP_OUTPUTS 一致） */
export const MOCK_STEP_OUTPUTS: Record<string, Record<string, any>> = {
  clean: {
    cleaned_text: '近日，我国新能源汽车产业发展再传捷报。据中国汽车工业协会最新数据显示，今年前五个月，全国新能源汽车销量达到224.7万辆，同比增长46.8%，市场占有率达到27.7%。在技术创新方面，多家车企宣布在固态电池领域取得重大突破。',
    original_length: 450,
    cleaned_length: 128,
    removed_patterns: ['HTML标签', '多余空行', '广告文本'],
  },
  extract_keywords: {
    keywords: [
      { word: '新能源汽车', weight: 0.95, type: '核心主题' },
      { word: '固态电池', weight: 0.87, type: '技术突破' },
      { word: '销量增长', weight: 0.82, type: '市场表现' },
      { word: '充电基础设施', weight: 0.76, type: '产业配套' },
      { word: '市场占有率', weight: 0.71, type: '行业指标' },
    ],
    total_extracted: 12,
  },
  extract_elements: {
    who: '中国汽车工业协会、多家新能源车企',
    when: '今年前五个月（最新数据）',
    where: '全国',
    what: '新能源汽车销量224.7万辆，同比增长46.8%',
    why: '技术创新（固态电池突破）+ 政策支持',
    how: '固态电池能量密度突破500Wh/kg，充电设施达630万台',
    confidence: 0.89,
  },
  generate_title_summary: {
    candidate_titles: [
      '新能源汽车前五月销量突破224万辆，固态电池技术取得重大突破',
      '同比增长46.8%！新能源汽车市场占有率攀升至27.7%',
      '固态电池能量密度突破500Wh/kg，纯电动车续航有望超1000公里',
    ],
    summary_short: '今年前五个月，我国新能源汽车销量达224.7万辆，同比增长46.8%，市场占有率达27.7%。多家车企在固态电池领域取得突破，能量密度突破500Wh/kg。',
    summary_long: '据中国汽车工业协会最新数据，今年前五个月全国新能源汽车销量达224.7万辆，同比增长46.8%，市场占有率达27.7%。在技术创新方面，固态电池能量密度已突破500Wh/kg，预计明年搭载于高端车型，续航里程将突破1000公里。充电基础设施累计达630万台，同比增长56%。业内预计全年销量有望突破500万辆，继续保持全球领先地位。',
    selected_title_index: 0,
  },
  match_topic: {
    primary_topic: '新能源汽车产业',
    secondary_topics: ['固态电池技术', '汽车工业', '清洁能源'],
    confidence: 0.92,
    topic_category: '科技/产业',
  },
  judge_timeline: {
    is_timely: true,
    time_sensitivity: 'high',
    recommended_position: '头条/要闻区',
    expiration_hours: 48,
    reason: '涉及最新产业数据与技术突破，时效性强',
  },
  check_consistency: {
    risk_level: 'low',
    risk_label: '低风险',
    title_summary_match: 0.94,
    fact_check_results: [
      { claim: '销量224.7万辆', verdict: '与原文一致' },
      { claim: '同比增长46.8%', verdict: '与原文一致' },
      { claim: '能量密度500Wh/kg', verdict: '与原文一致' },
    ],
    suggestions: [],
  },
  edit_suggestions: {
    overall_score: 87,
    suggestions: [
      {
        type: '标题优化',
        priority: 'medium',
        detail: '建议在标题中加入「同比+46.8%」等关键数据以增强说服力',
        reason: '数据驱动标题点击率更高',
      },
      {
        type: '结构优化',
        priority: 'low',
        detail: '可增加专家点评段落以提升深度',
        reason: '行业分析类新闻读者期待多方观点',
      },
    ],
    readability_score: 82,
  },
}

// ── SSE 事件类型 ──────────────────────────────────────────

export interface SSEEvent {
  event_type: 'step_start' | 'step_complete' | 'step_error' | 'task_complete'
  task_id: number
  step?: string
  step_order: number
  status: string
  timestamp: number
  data: Record<string, any>
}

export interface SSECallbacks {
  onStepStart?: (event: SSEEvent) => void
  onStepComplete?: (event: SSEEvent) => void
  onStepError?: (event: SSEEvent) => void
  onTaskComplete?: (event: SSEEvent) => void
}

/** 通过 fetch ReadableStream 连接 SSE 实时进度流。
 *
 * 使用 fetch（而非 EventSource）以便携带 Authorization header。
 * 返回 AbortController，调用 .abort() 即可断开连接。
 */
export function connectTaskStream(taskId: number, callbacks: SSECallbacks): AbortController {
  const controller = new AbortController()
  const TOKEN_KEY = 'llm_news_token' // 与 request.ts 一致
  const token = localStorage.getItem(TOKEN_KEY)
  const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

  const url = `${baseURL}/api/news-editor-agent/task/${taskId}/stream`

  fetch(url, {
    method: 'GET',
    headers: {
      'Accept': 'text/event-stream',
      'Cache-Control': 'no-cache',
      ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
    },
    signal: controller.signal,
  })
    .then(async (response) => {
      if (!response.ok) {
        const text = await response.text().catch(() => '')
        throw new Error(`SSE 连接失败: HTTP ${response.status}${text ? ` — ${text}` : ''}`)
      }

      const reader = response.body?.getReader()
      if (!reader) {
        throw new Error('浏览器不支持 ReadableStream')
      }

      const decoder = new TextDecoder('utf-8')
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        // 最后一个可能是不完整的行，保留在 buffer
        buffer = lines.pop() || ''

        let currentEventType = ''
        let currentData = ''

        for (const line of lines) {
          if (line.startsWith('event: ')) {
            currentEventType = line.slice(7).trim()
          } else if (line.startsWith('data: ')) {
            currentData = line.slice(6).trim()
          } else if (line === '' && currentData) {
            // 空行表示一个完整的 SSE 消息结束
            try {
              const event: SSEEvent = JSON.parse(currentData)
              switch (event.event_type) {
                case 'step_start':
                  callbacks.onStepStart?.(event)
                  break
                case 'step_complete':
                  callbacks.onStepComplete?.(event)
                  break
                case 'step_error':
                  callbacks.onStepError?.(event)
                  break
                case 'task_complete':
                  callbacks.onTaskComplete?.(event)
                  break
              }
            } catch {
              // 忽略 JSON 解析错误
            }
            currentEventType = ''
            currentData = ''
          }
        }
      }
    })
    .catch((err) => {
      if ((err as Error).name !== 'AbortError') {
        console.error('[newsEditorSSE] 连接错误:', err)
        callbacks.onStepError?.({
          event_type: 'step_error',
          task_id: taskId,
          step_order: 0,
          status: 'failed',
          timestamp: Date.now(),
          data: { error: (err as Error).message || 'SSE 连接异常' },
        })
      }
    })

  return controller
}
