/** News Editor Agent — Pinia 状态管理（Phase 3 SSE 实时流 + Polling Fallback）。
 *
 * 管理 Agent 任务的完整生命周期：
 *   - Phase 3 Mock 模式：提交 → SSE 实时流（主）→ polling fallback → UI 渲染
 *   - Phase 3 真实模式：提交 → SSE 连接 → 逐步更新 → 结果展示
 *
 * 核心原则：后端是唯一状态源（Truth Source），前端只做拉取 + 渲染。
 * SSE 是主通道，polling 仅在 SSE 连接失败时作为降级方案。
 *
 * 遵循 Composition API store 模式（与 user.ts、homeFeed.ts 一致）。
 */

import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import {
  runTextAgent,
  runTextAgentMock,
  getAgentTask,
  connectTaskStream,
  type SSEEvent,
  type AgentTaskDetail,
} from '@/api/newsEditorAgent'
import type { AIGenerateResponse } from '@/api/ai'
import { normalizeAIGenerateResult } from '@/utils/normalizeAIGenerateResult'

// ── 步骤定义（与后端 pipeline.py STEP_META 一致） ────────

export const AGENT_STEPS = [
  { name: 'clean',              label: '正文清洗',     order: 1 },
  { name: 'extract_keywords',   label: '关键词提取',   order: 2 },
  { name: 'extract_elements',   label: '六要素识别',   order: 3 },
  { name: 'generate_title_summary', label: '标题摘要生成', order: 4 },
  { name: 'match_topic',        label: '话题匹配',     order: 5 },
  { name: 'judge_timeline',     label: '时间线适配',   order: 6 },
  { name: 'check_consistency',  label: '一致性检查',   order: 7 },
  { name: 'edit_suggestions',   label: '使用建议生成', order: 8 },
] as const

// ── 步骤状态 ──────────────────────────────────────────────

export interface StepState {
  name: string
  label: string
  order: number
  status: 'pending' | 'running' | 'completed' | 'failed'
  latencyMs: number
  tokens: number
  provider: string
  model: string
  error?: string
  output?: Record<string, any>  // 步骤输出数据（SSE step_complete 推送，UI 实时渲染）
}

export interface AgentResult {
  title?: string
  summary?: string
  topic?: Record<string, any>
  timeline?: Record<string, any>
  consistency?: Record<string, any>
  editSuggestions?: Record<string, any>
}

function createDefaultSteps(): StepState[] {
  return AGENT_STEPS.map((s) => ({
    name: s.name,
    label: s.label,
    order: s.order,
    status: 'pending' as const,
    latencyMs: 0,
    tokens: 0,
    provider: '',
    model: '',
  }))
}

// ── Store ──────────────────────────────────────────────────

export const useNewsEditorAgentStore = defineStore('newsEditorAgent', () => {
  const taskId = ref<number | null>(null)
  const status = ref<'idle' | 'running' | 'completed' | 'failed'>('idle')
  const inputText = ref('')
  const steps = ref<StepState[]>(createDefaultSteps())
  const result = ref<AgentResult | null>(null)
  const standardResult = ref<AIGenerateResponse | null>(null)
  const error = ref('')
  const loading = ref(false)

  let streamController: AbortController | null = null

  // ── 计算属性 ────────────────────────────────────────────

  const currentStep = computed(() => steps.value.find((s) => s.status === 'running'))
  const completedCount = computed(() => steps.value.filter((s) => s.status === 'completed').length)
  const totalLatencyMs = computed(() => steps.value.reduce((sum, s) => sum + s.latencyMs, 0))

  // ── 内部方法 ────────────────────────────────────────────

  function resetSteps() {
    steps.value = createDefaultSteps()
  }

  function updateStep(stepName: string, updates: Partial<StepState>) {
    const idx = steps.value.findIndex((s) => s.name === stepName)
    if (idx !== -1) {
      steps.value[idx] = { ...steps.value[idx], ...updates }
    }
  }

  // ── SSE 事件处理 ────────────────────────────────────────

  function handleStepStart(event: SSEEvent) {
    if (event.step) {
      updateStep(event.step, { status: 'running' })
    }
  }

  function handleStepComplete(event: SSEEvent) {
    if (event.step) {
      updateStep(event.step, {
        status: 'completed',
        latencyMs: event.data?.latency_ms ?? 0,
        tokens: event.data?.tokens ?? 0,
        provider: event.data?.provider ?? '',
        model: event.data?.model ?? '',
        output: event.data?.output ?? {},
      })
      standardResult.value = normalizeAIGenerateResult(event.data?.result_json ?? event.data?.output ?? event.data ?? null, {
        steps: steps.value,
      })
    }
  }

  function handleStepError(event: SSEEvent) {
    if (event.step) {
      updateStep(event.step, {
        status: 'failed',
        error: event.data?.error ?? '未知错误',
      })
    }
    error.value = event.data?.error ?? '步骤执行失败'
  }

  function handleTaskComplete(event: SSEEvent) {
    if (event.status === 'completed') {
      status.value = 'completed'
      // 从完成事件提取结果
      const raw = event.data?.result_json
      if (typeof raw === 'string') {
        try {
          const parsed = JSON.parse(raw)
          extractResultFromSteps(parsed)
          standardResult.value = normalizeAIGenerateResult(parsed, { steps: steps.value })
        } catch {
          standardResult.value = normalizeAIGenerateResult(event.data?.result ?? event.data ?? null, {
            steps: steps.value,
          })
        }
      } else {
        standardResult.value = normalizeAIGenerateResult(event.data?.result ?? event.data ?? null, {
          steps: steps.value,
        })
      }
    } else {
      status.value = 'failed'
      error.value = event.data?.error ?? '任务执行失败'
    }
    streamController = null
  }

  /** 从步骤输出中聚合最终结果。 */
  function extractResultFromSteps(stepResults: any[]) {
    if (!Array.isArray(stepResults)) return

    const out: AgentResult = {}
    for (const sr of stepResults) {
      const step = sr.step
      const output = sr.output || {}
      switch (step) {
        case 'generate_title_summary':
          out.title = output.candidate_titles?.[0] || output.summary_short?.slice(0, 40)
          out.summary = output.summary_short || output.summary_long
          break
        case 'match_topic':
          out.topic = output
          break
        case 'judge_timeline':
          out.timeline = output
          break
        case 'check_consistency':
          out.consistency = output
          break
        case 'edit_suggestions':
          out.editSuggestions = output
          break
      }
    }
    result.value = out
  }

  // ── 公共 Actions ────────────────────────────────────────

  /** 提交文本并启动 SSE 实时监听。 */
  async function submitTask(text: string, params?: Record<string, any>): Promise<void> {
    if (!text.trim()) return

    resetSteps()
    result.value = null
    standardResult.value = null
    error.value = ''
    loading.value = true
    status.value = 'running'

    try {
      const res = await runTextAgent({
        input_text: text.trim(),
        pipeline_params: params as any,
      })
      taskId.value = res.task_id
      inputText.value = text.trim()

      // 立即连接 SSE 流
      connectStream()
    } catch (err) {
      status.value = 'failed'
      error.value = err instanceof Error ? err.message : '任务提交失败'
    } finally {
      loading.value = false
    }
  }

  /** 连接 SSE 实时流。 */
  function connectStream() {
    const tid = taskId.value
    if (!tid) return

    // 断开已有的连接
    disconnect()

    streamController = connectTaskStream(tid, {
      onStepStart: handleStepStart,
      onStepComplete: handleStepComplete,
      onStepError: handleStepError,
      onTaskComplete: handleTaskComplete,
    })
  }

  /** 断开 SSE 连接 + 清理 polling 降级定时器（Phase 3）。 */
  function disconnect() {
    if (streamController) {
      streamController.abort()
      streamController = null
    }
    _stopPolling()
  }

  // ── Phase 3 Polling Fallback（SSE 降级方案） ──────────

  let _pollTimer: ReturnType<typeof setInterval> | null = null
  const POLL_INTERVAL_MS = 1000
  const POLL_MAX_RETRIES = 60 // 最多轮询 60 次（60秒）

  /** Phase 3：提交任务到后端 MockTaskRunner + SSE 实时流（主）+ polling 降级。
   *
   * 流程：
   *   1. POST /api/news-editor-agent/run-text-mock → 后端创建 task + 启动 MockTaskRunner
   *   2. 后端 MockTaskRunner 每步通过 SSEManager 推送 step_start / step_complete 事件
   *   3. 前端通过 SSE 实时接收事件 → 更新 store → UI 实时渲染
   *   4. SSE 连接失败 → 自动降级为 polling GET /task/{id}
   *   5. status === 'completed' | 'failed' → 停止 SSE + polling
   *
   * 后端 MockTaskRunner 是唯一状态源（每个 step 写入 DB + 推送 SSE），
   * 前端只做接收 + 渲染，不做任何客户端模拟。
   */
  async function submitTaskMock(text: string, params?: Record<string, any>): Promise<void> {
    if (!text.trim()) return

    resetSteps()
    result.value = null
    standardResult.value = null
    error.value = ''
    loading.value = true
    status.value = 'running'

    try {
      // 调用 /run-text-mock 启动后端 MockTaskRunner（含 SSE 推送）
      const res = await runTextAgentMock({
        input_text: text.trim(),
        pipeline_params: params as any,
      })
      taskId.value = res.task_id
      inputText.value = text.trim()
    } catch (err) {
      status.value = 'failed'
      error.value = err instanceof Error ? err.message : '任务提交失败'
      loading.value = false
      return
    } finally {
      loading.value = false
    }

    // Phase 3: SSE 实时流（主通道），失败自动降级 polling
    _connectSSEPrimary()
  }

  // ── Phase 3 SSE Primary + Polling Fallback ──────────────

  /** SSE 实时流（主通道），连接失败自动降级为 polling。
   *
   * 策略：
   *   1. 优先通过 SSE 连接接收实时 step_start / step_complete 事件
   *   2. 若 SSE 连接失败且尚未收到任何步骤事件 → 自动降级 polling
   *   3. 若 SSE 中途失败但已有步骤完成 → 标记当前步骤为 error
   *   4. 任务完成（task_complete）→ 正常结束
   *
   * polling 降级后行为与 Phase 2 完全一致：
   *   - 每 1 秒 GET /task/{id}
   *   - 最多 60 次（60 秒）超时
   */
  function _connectSSEPrimary() {
    const tid = taskId.value
    if (!tid) return

    // 断开已有连接
    disconnect()

    let anyStepCompleted = false

    streamController = connectTaskStream(tid, {
      onStepStart: (event) => {
        anyStepCompleted = true // SSE 通道正常工作
        handleStepStart(event)
      },
      onStepComplete: (event) => {
        anyStepCompleted = true
        handleStepComplete(event)
      },
      onStepError: (event) => {
        // SSE 连接失败且尚未收到任何步骤 → 降级 polling
        if (!anyStepCompleted && status.value === 'running') {
          console.warn('[newsEditorAgent] SSE 连接失败，降级为 polling')
          _startPolling()
        } else {
          // 中途失败：正常处理步骤错误
          handleStepError(event)
        }
      },
      onTaskComplete: (event) => {
        handleTaskComplete(event)
      },
    })
  }

  /** 启动 polling 轮询后端 task 状态（SSE 不可用时的降级方案）。 */
  function _startPolling() {
    _stopPolling()

    let pollCount = 0

    // 立即执行第一次拉取
    _pollOnce()

    _pollTimer = setInterval(() => {
      pollCount++
      if (pollCount > POLL_MAX_RETRIES) {
        _stopPolling()
        if (status.value === 'running') {
          status.value = 'failed'
          error.value = '任务轮询超时，请稍后重试'
        }
        return
      }
      _pollOnce()
    }, POLL_INTERVAL_MS)
  }

  /** 单次 polling（SSE 降级方案）：拉取后端 task 状态 → 映射到 store。 */
  async function _pollOnce() {
    const tid = taskId.value
    if (!tid) return

    try {
      const detail: AgentTaskDetail = await getAgentTask(tid)

      // 映射 task status
      switch (detail.status) {
        case 'pending':
          status.value = 'running'
          break
        case 'running':
          status.value = 'running'
          break
        case 'completed':
          status.value = 'completed'
          _stopPolling()
          break
        case 'failed':
          status.value = 'failed'
          error.value = detail.error_message || '任务执行失败'
          _stopPolling()
          break
      }

      // 映射步骤状态：后端 step_log → store StepState
      if (detail.steps && detail.steps.length > 0) {
        for (const log of detail.steps) {
          updateStep(log.step_name, {
            status: log.status as StepState['status'],
            latencyMs: log.response_ms || 0,
            tokens: (log.llm_request_tokens || 0) + (log.llm_response_tokens || 0),
            provider: log.llm_provider || 'mock',
            model: log.llm_model || 'mock/task-runner',
            error: log.error_message || undefined,
            output: log.output_data || {},
          })
        }

        // 聚合结果
        _extractResultFromDetail(detail)
        standardResult.value = normalizeAIGenerateResult(detail, {
          steps: steps.value,
        })
      }

      // 如果后端有 current_step 信息且 steps 为空，手动标记当前步骤
      if (detail.current_step && (!detail.steps || detail.steps.length === 0)) {
        updateStep(detail.current_step, { status: 'running' })
      }
    } catch {
      // 网络错误不中断 polling，继续重试
    }
  }

  /** 从 task detail 的步骤输出中聚合最终结果。 */
  function _extractResultFromDetail(detail: AgentTaskDetail) {
    if (!detail.steps) return

    const out: AgentResult = {}
    for (const log of detail.steps) {
      if (log.status !== 'completed') continue
      const output = log.output_data || {}
      const name = log.step_name

      switch (name) {
        case 'generate_title_summary':
          out.title = output.candidate_titles?.[0] || output.summary_short?.slice(0, 40) || ''
          out.summary = output.summary_short || output.summary_long || ''
          break
        case 'match_topic':
          out.topic = output
          break
        case 'judge_timeline':
          out.timeline = output
          break
        case 'check_consistency':
          out.consistency = output
          break
        case 'edit_suggestions':
          out.editSuggestions = output
          break
      }
    }
    result.value = Object.keys(out).length > 0 ? { ...out } : null
  }

  /** 停止 polling 定时器。 */
  function _stopPolling() {
    if (_pollTimer !== null) {
      clearInterval(_pollTimer)
      _pollTimer = null
    }
  }

  /** 清空执行态，但保留当前输入文本。 */
  function clearExecutionState() {
    disconnect()
    _stopPolling()
    taskId.value = null
    status.value = 'idle'
    error.value = ''
    loading.value = false
    resetSteps()
    result.value = null
    standardResult.value = null
  }

  /** 取消当前任务（断开 SSE + 停止 polling，重置状态）。 */
  function abort() {
    clearExecutionState()
  }

  /** 重置到初始状态。 */
  function reset() {
    clearExecutionState()
    inputText.value = ''
  }

  return {
    // state
    taskId,
    status,
    inputText,
    steps,
    result,
    standardResult,
    error,
    loading,
    // computed
    currentStep,
    completedCount,
    totalLatencyMs,
    // actions
    submitTask,
    submitTaskMock,
    connectStream,
    disconnect,
    clearExecutionState,
    abort,
    reset,
  }
})
