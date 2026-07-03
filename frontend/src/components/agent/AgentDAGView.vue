<script setup lang="ts">
/** AgentDAGView — DAG 流水线可视化图（Phase 4）。
 *
 * 使用 SVG 绘制 8 节点 DAG 执行图：
 *   Step1 → [Step2 ∥ Step3] → Step4 → [Step5 ∥ Step6] → Step7 → Step8
 *
 * 双模式：
 *   - Live 模式：通过 props.steps 接收 SSE 实时驱动的步骤状态
 *   - Historical 模式：通过 props.taskId 从 API 获取 DAG 图结构
 */

import { computed, ref, watch, onMounted } from 'vue'
import { getTaskDAG, type DAGNode } from '@/api/agentAnalysis'

export interface DAGStep {
  name: string
  label: string
  order: number
  status: 'pending' | 'running' | 'completed' | 'failed'
  latencyMs: number
  tokens: number
  provider: string
  model: string
  error?: string
}

const props = defineProps<{
  steps?: DAGStep[]
  taskId?: number | null
}>()

// ── Historical 模式：从 API 获取 DAG 图 ──────────────
const apiNodes = ref<DAGNode[]>([])
const apiLoading = ref(false)
const apiError = ref('')

async function fetchDAG() {
  if (!props.taskId) return
  apiLoading.value = true
  apiError.value = ''
  try {
    const data = await getTaskDAG(props.taskId)
    apiNodes.value = data.nodes
  } catch (e) {
    apiError.value = e instanceof Error ? e.message : '加载 DAG 数据失败'
  } finally {
    apiLoading.value = false
  }
}

watch(() => props.taskId, () => { if (props.taskId) fetchDAG() })
onMounted(() => { if (props.taskId) fetchDAG() })

// ── 统一步骤数据（props 优先 → API 数据） ────────────
const displaySteps = computed<DAGStep[]>(() => {
  if (props.steps && props.steps.length > 0) return props.steps
  if (apiNodes.value.length > 0) {
    return apiNodes.value.map(n => ({
      name: n.id,
      label: n.label,
      order: n.order,
      status: n.status as DAGStep['status'],
      latencyMs: n.latency_ms,
      tokens: n.tokens,
      provider: n.provider || '',
      model: n.model || '',
    }))
  }
  return []
})

// ── DAG 拓扑：每个节点的 (col, row) 在 3×6 网格中的位置 ──
interface NodeLayout { col: number; row: number; label: string }

const LAYOUT: Record<string, NodeLayout> = {
  clean:               { col: 1, row: 0, label: '正文清洗' },
  extract_keywords:    { col: 0, row: 1, label: '关键词提取' },
  extract_elements:    { col: 2, row: 1, label: '六要素识别' },
  generate_title_summary: { col: 1, row: 2, label: '标题摘要生成' },
  match_topic:         { col: 0, row: 3, label: '话题匹配' },
  judge_timeline:      { col: 2, row: 3, label: '时间线适配' },
  check_consistency:   { col: 1, row: 4, label: '一致性检查' },
  edit_suggestions:    { col: 1, row: 5, label: '编辑建议生成' },
}

// ── SVG 画布计算（响应式网格）──
const GRID_COLS = 3
const GRID_ROWS = 6
const NODE_W = 160
const NODE_H = 62
const PADDING = 44
const GAP_X = 24
const GAP_Y = 16

const svgW = computed(() => GRID_COLS * (NODE_W + GAP_X) + PADDING * 2)
const svgH = computed(() => GRID_ROWS * (NODE_H + GAP_Y) + PADDING * 2)

function nodeX(col: number): number { return PADDING + col * (NODE_W + GAP_X) }
function nodeY(row: number): number { return PADDING + row * (NODE_H + GAP_Y) }
function nodeCX(col: number): number { return nodeX(col) + NODE_W / 2 }
function nodeCY(row: number): number { return nodeY(row) + NODE_H / 2 }

// ── 边的定义（from → to）──
interface Edge { from: string; to: string; points: string }
const edges = computed<Edge[]>(() => {
  const e: Edge[] = []

  // Step1 → Step2, Step1 → Step3
  e.push({ from: 'clean', to: 'extract_keywords', points: linePoints('clean', 'extract_keywords') })
  e.push({ from: 'clean', to: 'extract_elements', points: linePoints('clean', 'extract_elements') })

  // Step2 → Step4, Step3 → Step4
  e.push({ from: 'extract_keywords', to: 'generate_title_summary', points: linePoints('extract_keywords', 'generate_title_summary') })
  e.push({ from: 'extract_elements', to: 'generate_title_summary', points: linePoints('extract_elements', 'generate_title_summary') })

  // Step4 → Step5, Step4 → Step6
  e.push({ from: 'generate_title_summary', to: 'match_topic', points: linePoints('generate_title_summary', 'match_topic') })
  e.push({ from: 'generate_title_summary', to: 'judge_timeline', points: linePoints('generate_title_summary', 'judge_timeline') })

  // Step5 → Step7, Step6 → Step7
  e.push({ from: 'match_topic', to: 'check_consistency', points: linePoints('match_topic', 'check_consistency') })
  e.push({ from: 'judge_timeline', to: 'check_consistency', points: linePoints('judge_timeline', 'check_consistency') })

  // Step7 → Step8
  e.push({ from: 'check_consistency', to: 'edit_suggestions', points: linePoints('check_consistency', 'edit_suggestions') })

  return e
})

// 两点间使用直角折线的 SVG path
function linePoints(f: string, t: string): string {
  const fl = LAYOUT[f], tl = LAYOUT[t]
  if (!fl || !tl) return ''
  const yMid = (nodeY(fl.row) + NODE_H + nodeY(tl.row)) / 2
  const x1 = nodeCX(fl.col), y1 = nodeY(fl.row) + NODE_H
  const x2 = nodeCX(tl.col), y2 = nodeY(tl.row)
  return `M${x1},${y1} L${x1},${yMid} L${x2},${yMid} L${x2},${y2}`
}

// ── 状态颜色映射 ──
function statusColor(s: string): string {
  switch (s) {
    case 'completed': return '#16a34a'
    case 'running':   return '#d92d20'
    case 'failed':    return '#dc2626'
    default:          return '#9ca3af'
  }
}

function statusBg(s: string): string {
  switch (s) {
    case 'completed': return '#f0fdf4'
    case 'running':   return '#fef2f2'
    case 'failed':    return '#fef2f2'
    default:          return '#f9fafb'
  }
}

function statusIcon(s: string): string {
  switch (s) {
    case 'completed': return '✔'
    case 'running':   return '↻'
    case 'failed':    return '✖'
    default:          return '○'
  }
}

function hasStep(name: string): boolean {
  return displaySteps.value.some(s => s.name === name)
}
function getStep(name: string): DAGStep | undefined {
  return displaySteps.value.find(s => s.name === name)
}
</script>

<template>
  <div class="dag-view">
    <!-- API 加载状态 -->
    <el-skeleton v-if="apiLoading" animated :rows="6" />

    <!-- API 错误 -->
    <el-alert v-else-if="apiError" :title="apiError" type="error" show-icon :closable="false" />

    <!-- 空状态（无 taskId 且无 steps） -->
    <el-empty
      v-else-if="!displaySteps.length"
      description="提交任务后，DAG 执行图将在此展示"
      :image-size="60"
    />

    <template v-else>
      <svg
        :viewBox="`0 0 ${svgW} ${svgH}`"
        :width="svgW"
        :height="svgH"
        class="dag-svg"
      >
        <!-- 连接线 -->
        <g class="dag-edges">
          <path
            v-for="(edge, i) in edges"
            :key="'e' + i"
            :d="edge.points"
            class="dag-edge"
            :class="{
              'is-active': getStep(edge.from)?.status === 'completed',
            }"
            fill="none"
            stroke-width="2"
          />
        </g>

        <!-- 节点 -->
        <g
          v-for="step in displaySteps"
          :key="step.name"
          class="dag-node-group"
        >
          <!-- 节点背景 -->
          <rect
            :x="nodeX(LAYOUT[step.name]?.col ?? 0)"
            :y="nodeY(LAYOUT[step.name]?.row ?? 0)"
            :width="NODE_W"
            :height="NODE_H"
            :rx="10"
            :fill="statusBg(step.status)"
            :stroke="statusColor(step.status)"
            stroke-width="2"
            class="dag-node-rect"
            :class="{
              'is-running': step.status === 'running',
              'is-completed': step.status === 'completed',
            }"
          />

          <!-- 状态图标 -->
          <text
            :x="nodeX(LAYOUT[step.name]?.col ?? 0) + 16"
            :y="nodeY(LAYOUT[step.name]?.row ?? 0) + 24"
            :fill="statusColor(step.status)"
            font-size="14"
            font-weight="700"
            text-anchor="middle"
            class="dag-node-icon"
          >
            {{ statusIcon(step.status) }}
          </text>

          <!-- 步骤名 -->
          <text
            :x="nodeX(LAYOUT[step.name]?.col ?? 0) + 62"
            :y="nodeY(LAYOUT[step.name]?.row ?? 0) + 20"
            fill="#374151"
            font-size="12"
            font-weight="600"
          >
            Step {{ step.order }}
          </text>
          <text
            :x="nodeX(LAYOUT[step.name]?.col ?? 0) + 62"
            :y="nodeY(LAYOUT[step.name]?.row ?? 0) + 38"
            fill="#6b7280"
            font-size="11"
          >
            {{ step.label }}
          </text>

          <!-- 元数据 -->
          <text
            v-if="step.status === 'completed'"
            :x="nodeX(LAYOUT[step.name]?.col ?? 0) + 62"
            :y="nodeY(LAYOUT[step.name]?.row ?? 0) + 52"
            fill="#9ca3af"
            font-size="10"
          >
            {{ step.latencyMs }}ms
            <template v-if="step.provider"> · {{ step.provider }}</template>
          </text>
        </g>
      </svg>

      <!-- 图例 -->
      <div class="dag-legend">
        <span class="legend-item"><span class="legend-dot legend-dot--pending"></span> 待执行</span>
        <span class="legend-item"><span class="legend-dot legend-dot--running"></span> 执行中</span>
        <span class="legend-item"><span class="legend-dot legend-dot--completed"></span> 已完成</span>
        <span class="legend-item"><span class="legend-dot legend-dot--failed"></span> 失败</span>
      </div>
    </template>
  </div>
</template>

<style scoped>
.dag-view {
  display: flex;
  flex-direction: column;
  align-items: center;
  overflow-x: auto;
  padding: 8px 0;
}

.dag-svg {
  max-width: 100%;
  height: auto;
}

.dag-edge {
  stroke: #e5e7eb;
  transition: stroke 0.4s ease;
}
.dag-edge.is-active {
  stroke: #16a34a;
  opacity: 0.5;
}

.dag-node-rect {
  transition: all 0.3s ease;
  cursor: default;
}
.dag-node-rect.is-running {
  animation: dag-pulse 1.2s ease-in-out infinite;
}
.dag-node-rect.is-completed:hover {
  filter: brightness(0.97);
}

@keyframes dag-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}

.dag-node-icon {
  dominant-baseline: central;
}

.dag-legend {
  display: flex;
  gap: 20px;
  margin-top: 12px;
  font-size: 12px;
  color: var(--color-text-secondary);
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  display: inline-block;
}
.legend-dot--pending   { background: #9ca3af; }
.legend-dot--running   { background: #d92d20; animation: dag-pulse 1.2s ease-in-out infinite; }
.legend-dot--completed { background: #16a34a; }
.legend-dot--failed    { background: #dc2626; }
</style>
