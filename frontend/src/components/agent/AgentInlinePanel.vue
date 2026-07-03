<script setup lang="ts">
/** AgentInlinePanel — 嵌入 AI 生成页面的 Agent 执行面板（Phase 3 SSE 实时流）。
 *
 * 包含：
 *   1. 8 段式进度条（实时更新）
 *   2. 当前执行步骤卡片（SSE step_start 实时触发）
 *   3. 已完成步骤输出卡片列表（SSE step_complete 实时填充）
 *   4. 后端 MockTaskRunner + SSEManager 驱动的实时状态
 *
 * 数据流：
 *   Phase 3: submitTaskMock → POST /run-text-mock → SSE stream → store → UI 实时渲染
 *            SSE 失败 → 自动降级 polling → store → UI
 *   Phase 3 真实: submitTask → POST /run-text → SSE stream → store → UI
 */

import { computed, onUnmounted, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { useNewsEditorAgentStore, AGENT_STEPS } from '@/stores/newsEditorAgent'
import Step7SummaryPanel from './Step7SummaryPanel.vue'

const props = defineProps<{
  inputText: string
  params?: Record<string, any>
  /** Phase 3 Mock 模式：true = 后端 MockTaskRunner + SSE 实时流（默认），false = 真实 AI + SSE */
  useMock?: boolean
}>()
const emit = defineEmits<{ done: [] }>()

const store = useNewsEditorAgentStore()
const submitting = ref(false)

const hoveredSimItem = ref<any>(null)

// ── 评分颜色映射（0-1 → 颜色） ──────────────────────────
function scoreColor(score: number): string {
  if (score >= 0.9) return '#16a34a'  // 深绿
  if (score >= 0.7) return '#22c55e'  // 绿
  if (score >= 0.5) return '#f59e0b'  // 黄
  if (score >= 0.3) return '#f97316'  // 橙
  return '#ef4444'                     // 红
}
function heatmapColor(score: number): string {
  if (score >= 0.9) return '#22c55e'
  if (score >= 0.7) return '#86efac'
  if (score >= 0.5) return '#fde047'
  if (score >= 0.3) return '#fdba74'
  return '#fca5a5'
}
function typeLabel(type: string): string {
  switch (type) {
    case 'match': return '匹配'
    case 'drift': return '偏离'
    case 'hallucination': return '幻觉'
    default: return type || '未知'
  }
}

async function handleStart() {
  const text = props.inputText.trim()
  if (!text) {
    ElMessage.warning('请先输入新闻文本')
    return
  }
  if (text.length < 20) {
    ElMessage.warning('输入文本至少需要 20 个字符')
    return
  }

  submitting.value = true
  try {
    if (props.useMock === true) {
      // Phase 3 Mock 模式：后端 MockTaskRunner + SSE 实时流（仅当明确指定 mock 时）
      await store.submitTaskMock(text)
    } else {
      // Phase 3 真实模式：真实 AI pipeline + SSE 实时流（默认），传入侧边栏参数
      await store.submitTask(text, props.params)
    }
    if (store.status === 'failed') {
      ElMessage.error(store.error || 'Agent 任务提交失败')
    }
  } catch {
    // store handles errors
  } finally {
    submitting.value = false
  }
}

function handleReset() {
  store.reset()
}

// Notify parent when task completes
watch(() => store.status, (s) => {
  if (s === 'completed' || s === 'failed') emit('done')
})

onUnmounted(() => { store.disconnect() })

// ── Helpers ──
const completedCount = computed(() => store.steps.filter(s => s.status === 'completed').length)
const progressPct = computed(() => store.steps.length ? Math.round(completedCount.value / 8 * 100) : 0)
const currentStep = computed(() => store.steps.find(s => s.status === 'running'))
const completedSteps = computed(() => store.steps.filter(s => s.status === 'completed'))
const totalLatency = computed(() => store.steps.reduce((sum, s) => sum + s.latencyMs, 0))

function stepIcon(s: string): string {
  switch (s) { case 'completed': return '✔'; case 'running': return '↻'; case 'failed': return '✖'; default: return '' }
}
function stepProgressClass(s: string): string {
  switch (s) { case 'completed': return 'is-done'; case 'running': return 'is-active'; case 'failed': return 'is-error'; default: return '' }
}
function formatMs(ms: number): string {
  return ms >= 1000 ? (ms / 1000).toFixed(1) + 's' : ms + 'ms'
}
</script>

<template>
  <div class="agent-inline">
    <!-- ═══════════════════════════════════════════════════ -->
    <!-- 操作按钮 -->
    <!-- ═══════════════════════════════════════════════════ -->
    <div class="agent-actions">
      <el-button
        v-if="store.status === 'idle'"
        type="primary"
        size="large"
        class="agent-start-btn"
        :loading="submitting"
        @click="handleStart"
      >
        {{ submitting ? '启动中...' : '启动 AI 智能编辑' }}
      </el-button>

      <template v-else-if="store.status === 'running'">
        <el-button type="warning" size="large" disabled class="agent-start-btn">
          执行中 {{ completedCount }}/8
        </el-button>
        <el-button
          type="danger"
          size="large"
          plain
          @click="store.abort()"
          style="margin-left: 8px; border-radius: 8px;"
        >取消</el-button>
      </template>

      <template v-else>
        <el-button type="success" size="large" disabled class="agent-start-btn" v-if="store.status === 'completed'">
          全部完成 · {{ formatMs(totalLatency) }}
        </el-button>
        <el-button type="danger" size="large" disabled class="agent-start-btn" v-else-if="store.status === 'failed'">
          执行失败
        </el-button>
        <el-button size="large" @click="handleReset" style="margin-left: 8px;">重置</el-button>
      </template>
    </div>

    <!-- ═══════════════════════════════════════════════════ -->
    <!-- 8 段式进度条 -->
    <!-- ═══════════════════════════════════════════════════ -->
    <div v-if="store.status !== 'idle'" class="agent-progress-bar">
      <div class="progress-track">
        <div class="progress-fill" :style="{ width: progressPct + '%' }"></div>
      </div>
      <div class="progress-segments">
        <div
          v-for="step in store.steps"
          :key="step.name"
          class="progress-seg"
          :class="stepProgressClass(step.status)"
          :title="`Step ${step.order}: ${step.label}`"
        >
          <span class="seg-icon">{{ stepIcon(step.status) }}</span>
        </div>
      </div>
      <div class="progress-label">
        <span class="progress-label__count">{{ completedCount }} / 8</span>
        <span v-if="currentStep" class="progress-label__name">{{ currentStep.label }}</span>
      </div>
    </div>

    <!-- ═══════════════════════════════════════════════════ -->
    <!-- 当前执行步骤（高亮卡片） -->
    <!-- ═══════════════════════════════════════════════════ -->
    <div v-if="currentStep" class="current-step-card">
      <div class="current-step-card__header">
        <span class="current-step-card__badge">执行中</span>
        <span class="current-step-card__name">Step {{ currentStep.order }}: {{ currentStep.label }}</span>
      </div>
      <el-progress :percentage="100" :indeterminate="true" :stroke-width="4" :show-text="false" color="#ff4d4f" />
    </div>

    <!-- ═══════════════════════════════════════════════════ -->
    <!-- 已完成步骤输出卡片 -->
    <!-- ═══════════════════════════════════════════════════ -->
    <div v-if="completedSteps.length" class="step-results">
      <h3 class="step-results__title">执行结果</h3>

      <div
        v-for="step in completedSteps"
        :key="step.name"
        class="step-result-card"
      >
        <div class="step-result-card__header">
          <span class="step-result-card__icon">✔</span>
          <span class="step-result-card__order">Step {{ step.order }}</span>
          <span class="step-result-card__label">{{ step.label }}</span>
          <span class="step-result-card__meta">
            <span class="meta-time">{{ formatMs(step.latencyMs) }}</span>
            <span v-if="step.provider" class="meta-provider">
              {{ step.provider === 'local' ? '💻' : '🤖' }} {{ step.provider }}
              <template v-if="step.model">/ {{ step.model }}</template>
            </span>
            <span v-if="step.tokens > 0" class="meta-tokens">{{ step.tokens }} tokens</span>
          </span>
        </div>

        <!-- 输出内容（从 step.output 实时渲染，每步完成即刻展示） -->
        <div class="step-result-card__body" v-if="step.output">
          <!-- Step 1: 正文清洗（仅统计摘要） -->
          <template v-if="step.name === 'clean'">
            <!-- ═══ 统计条 ═══ -->
            <div class="clean-stats" v-if="step.output.original_length">
              <div class="clean-stat-item">
                <span class="clean-stat-val">{{ step.output.original_length }}</span>
                <span class="clean-stat-label">原文字数</span>
              </div>
              <div class="clean-stat-arrow">→</div>
              <div class="clean-stat-item">
                <span class="clean-stat-val">{{ step.output.cleaned_length }}</span>
                <span class="clean-stat-label">清洗后字数</span>
              </div>
              <div class="clean-stat-item clean-stat-item--highlight">
                <span class="clean-stat-val">{{ step.output.reduction_pct }}%</span>
                <span class="clean-stat-label">压缩率</span>
              </div>
            </div>

            <!-- 清洗操作标签 -->
            <div class="output-section" v-if="(step.output.removed_noise || []).length">
              <div class="output-tags">
                <el-tag v-for="(item, i) in step.output.removed_noise" :key="i" size="small" type="info" effect="plain">
                  {{ item }}
                </el-tag>
              </div>
            </div>

            <!-- 清洗总结 -->
            <div class="output-section" v-if="step.output.diff_preview?.change_summary">
              <p class="output-text output-text--dim">{{ step.output.diff_preview.change_summary }}</p>
            </div>
          </template>

          <!-- Step 2: 关键词提取 -->
          <template v-if="step.name === 'extract_keywords'">
            <div class="output-section">
              <div class="output-tags">
                <el-tag
                  v-for="(kw, i) in (step.output.keywords || [])"
                  :key="i"
                  :type="i === 0 ? 'danger' : ''"
                  effect="light"
                  size="small"
                >
                  {{ typeof kw === 'string' ? kw : (kw.word || kw) }}
                </el-tag>
              </div>
            </div>
          </template>

          <!-- Step 3: 六要素识别 -->
          <template v-if="step.name === 'extract_elements'">
            <div class="output-section">
              <div class="elements-grid" v-if="step.output.news_elements">
                <div class="element-item" v-if="step.output.news_elements.who">
                  <span class="element-key">何人</span>
                  <span class="element-val">{{ step.output.news_elements.who }}</span>
                </div>
                <div class="element-item" v-if="step.output.news_elements.what">
                  <span class="element-key">何事</span>
                  <span class="element-val">{{ step.output.news_elements.what }}</span>
                </div>
                <div class="element-item" v-if="step.output.news_elements.when">
                  <span class="element-key">何时</span>
                  <span class="element-val">{{ step.output.news_elements.when }}</span>
                </div>
                <div class="element-item" v-if="step.output.news_elements.where">
                  <span class="element-key">何地</span>
                  <span class="element-val">{{ step.output.news_elements.where }}</span>
                </div>
                <div class="element-item" v-if="step.output.news_elements.why">
                  <span class="element-key">为何</span>
                  <span class="element-val">{{ step.output.news_elements.why }}</span>
                </div>
                <div class="element-item" v-if="step.output.news_elements.how">
                  <span class="element-key">如何</span>
                  <span class="element-val">{{ step.output.news_elements.how }}</span>
                </div>
              </div>
            </div>
          </template>

          <!-- Step 4: 标题摘要生成 -->
          <template v-if="step.name === 'generate_title_summary'">
            <div class="output-section" v-if="(step.output.candidate_titles || []).length">
              <span class="s4-label">候选标题 ({{ step.output.candidate_titles.length }} 个)</span>
              <div class="titles-list">
                <p v-for="(t, i) in step.output.candidate_titles" :key="i" class="output-text output-text--title">
                  {{ i + 1 }}. {{ t }}
                </p>
              </div>
            </div>
            <div class="output-section" v-if="step.output.summary_short">
              <span class="s4-label">简短摘要 ({{ step.output.summary_short.length }} 字)</span>
              <p class="output-text">{{ step.output.summary_short }}</p>
            </div>
            <div class="output-section" v-if="step.output.summary_long">
              <span class="s4-label">
                详细摘要 ({{ step.output.summary_long.length }} 字 ·
                {{ step.output.summary_short ? (step.output.summary_long.length / Math.max(step.output.summary_short.length, 1)).toFixed(1) + 'x 短摘要' : '' }})
              </span>
              <p class="output-text">{{ step.output.summary_long }}</p>
            </div>
          </template>

          <!-- Step 5: 话题匹配 -->
          <template v-if="step.name === 'match_topic'">
            <div class="output-section">
              <div class="output-tags">
                <el-tag type="danger" effect="dark" size="small" v-if="step.output.primary_topic">
                  {{ step.output.primary_topic }}
                </el-tag>
                <el-tag
                  v-for="(t, i) in (step.output.secondary_topics || [])"
                  :key="i"
                  effect="plain"
                  size="small"
                >{{ t }}</el-tag>
              </div>
              <span v-if="step.output.confidence" class="output-meta">
                置信度: {{ (step.output.confidence * 100).toFixed(0) }}%
                <template v-if="step.output.topic_category"> · {{ step.output.topic_category }}</template>
              </span>
            </div>
          </template>

          <!-- Step 6: 时间线适配 -->
          <template v-if="step.name === 'judge_timeline'">
            <div class="output-section">
              <p class="output-text">
                <el-tag :type="step.output.is_timely ? 'success' : 'warning'" size="small">
                  {{ step.output.is_timely ? '✅ 符合时效' : '⚠️ 需更新' }}
                </el-tag>
                <template v-if="step.output.time_sensitivity">
                  · 敏感度: <strong>{{ step.output.time_sensitivity }}</strong>
                </template>
                <template v-if="step.output.recommended_position">
                  · 推荐: {{ step.output.recommended_position }}
                </template>
              </p>
              <p v-if="step.output.reason" class="output-text output-text--dim">{{ step.output.reason }}</p>
            </div>
          </template>

          <!-- Step 7: 一致性检查（简洁模式 — Top-K 关键问题） -->
          <template v-if="step.name === 'check_consistency'">
            <Step7SummaryPanel :consistency-data="step.output" />

            <!-- Hover 预览浮层（保留完整交互） -->
            <div class="sim-hover-preview" v-if="hoveredSimItem">
              <div class="hover-card">
                <div class="hover-score" :style="{ color: scoreColor(hoveredSimItem.score) }">
                  {{ (hoveredSimItem.score * 100).toFixed(0) }}%
                </div>
                <div class="hover-type">
                  <el-tag :type="hoveredSimItem.type === 'match' ? 'success' : hoveredSimItem.type === 'drift' ? 'warning' : 'danger'" size="small">
                    {{ typeLabel(hoveredSimItem.type) }}
                  </el-tag>
                </div>
                <p class="hover-text"><strong>AI 输出:</strong> {{ hoveredSimItem.summary_sentence }}</p>
                <p class="hover-text"><strong>原文:</strong> {{ hoveredSimItem.source_sentence || '无对应原文 — 可能为 AI 幻觉' }}</p>
                <p class="hover-text hover-text--dim"><strong>判断:</strong> {{ hoveredSimItem.reason }}</p>
              </div>
            </div>
          </template>

          <!-- Step 8: 编辑建议 -->
          <template v-if="step.name === 'edit_suggestions'">
            <div class="output-section">
              <ul class="suggestion-list">
                <li v-for="(s, i) in (step.output.suggestions || [])" :key="i">
                  <el-tag
                    :type="s.priority === 'high' ? 'danger' : s.priority === 'medium' ? 'warning' : 'info'"
                    size="small"
                    style="margin-right: 6px;"
                  >{{ s.type || '建议' }}</el-tag>
                  <strong>{{ s.detail || s.reason || s }}</strong>
                  <span v-if="s.detail && s.reason" class="output-text--dim"> — {{ s.reason }}</span>
                </li>
              </ul>
              <p v-if="step.output.ready_to_publish !== undefined" class="output-text" style="margin-top: 8px;">
                <el-tag :type="step.output.ready_to_publish ? 'success' : 'warning'" size="small">
                  {{ step.output.ready_to_publish ? '✅ 可直接发布' : '⚠️ 需要修改' }}
                </el-tag>
              </p>
            </div>
          </template>
        </div>
      </div>
    </div>

    <!-- ═══════════════════════════════════════════════════ -->
    <!-- 空状态 -->
    <!-- ═══════════════════════════════════════════════════ -->
    <div v-if="store.status === 'idle'" class="agent-empty">
      <p class="agent-empty__title">AI 新闻智能编辑</p>
      <p class="agent-empty__desc">8 步流水线：正文清洗 → 关键词提取 + 六要素识别 → 标题摘要生成 → 话题匹配 + 时间线适配 → 一致性检查 → 编辑建议</p>
      <p class="agent-empty__hint">输入新闻文本后点击上方按钮启动</p>
    </div>

    <!-- ═══════════════════════════════════════════════════ -->
    <!-- 完成总结 -->
    <!-- ═══════════════════════════════════════════════════ -->
    <div v-if="store.status === 'completed'" class="agent-summary">
      <el-alert
        title="流水线执行完成"
        type="success"
        :description="`全部 8 步已完成，总耗时 ${formatMs(totalLatency)}。可在右侧查看完整结果。`"
        show-icon
        :closable="false"
      />
    </div>
  </div>
</template>

<style scoped>
.agent-inline { display: flex; flex-direction: column; gap: 16px; }

/* ── 操作按钮 ── */
.agent-actions { display: flex; align-items: center; }

.agent-start-btn {
  height: 46px;
  font-size: 16px;
  font-weight: 600;
  border-radius: 8px;
  border: none;
}
.agent-start-btn:not(.el-button--warning):not(.el-button--success):not(.el-button--danger) {
  background: linear-gradient(135deg, #ff4d4f 0%, #ff7875 100%);
}
.agent-start-btn:not(:disabled):hover {
  background: linear-gradient(135deg, #ff7875 0%, #ff4d4f 100%) !important;
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(255, 77, 79, 0.4);
}

/* ── 8 段式进度条 ── */
.agent-progress-bar {
  background: #fff;
  border: 1px solid #f1d4d4;
  border-radius: 14px;
  padding: 16px 20px;
  box-shadow: 0 2px 12px rgba(217, 45, 32, .05);
}

.progress-track {
  width: 100%;
  height: 6px;
  background: #f5f5f5;
  border-radius: 3px;
  margin-bottom: 10px;
  overflow: hidden;
}
.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #ff4d4f, #ff7875);
  border-radius: 3px;
  transition: width 0.4s ease;
}

.progress-segments {
  display: flex;
  justify-content: space-between;
  margin-bottom: 6px;
}
.progress-seg {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f0f0f0;
  border: 2px solid #e8e8e8;
  font-size: 12px;
  font-weight: 700;
  transition: all 0.3s ease;
  color: #ccc;
}
.progress-seg.is-active {
  background: #fff5f5;
  border-color: #ff4d4f;
  color: #ff4d4f;
  animation: seg-pulse 1.2s ease-in-out infinite;
}
.progress-seg.is-done {
  background: #f0fff4;
  border-color: #22c55e;
  color: #16a34a;
}
.progress-seg.is-error {
  background: #fef2f2;
  border-color: #ef4444;
  color: #dc2626;
}
@keyframes seg-pulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(255, 77, 79, 0.3); }
  50% { box-shadow: 0 0 0 6px rgba(255, 77, 79, 0); }
}

.progress-label {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 12px;
  color: #666;
}
.progress-label__count { font-weight: 700; color: #1e293b; font-variant-numeric: tabular-nums; }
.progress-label__name { color: #ff4d4f; font-weight: 500; }

/* ── 当前步骤卡片 ── */
.current-step-card {
  background: #fff5f5;
  border: 1px solid #ffccc7;
  border-radius: 12px;
  padding: 14px 18px;
}
.current-step-card__header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}
.current-step-card__badge {
  font-size: 12px;
  font-weight: 600;
  color: #ff4d4f;
  background: #ffe4e4;
  padding: 2px 10px;
  border-radius: 10px;
}
.current-step-card__name { font-size: 15px; font-weight: 600; color: #1e293b; }

/* ── 已完成步骤输出卡片 ── */
.step-results { display: flex; flex-direction: column; gap: 12px; }
.step-results__title {
  font-size: 15px;
  font-weight: 600;
  color: #1e293b;
  margin: 0;
}

.step-result-card {
  background: #fff;
  border: 1px solid #f0f0f0;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, .04);
  transition: border-color 0.2s;
}
.step-result-card:hover { border-color: #b7eb8f; }

.step-result-card__header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: #fafafa;
  border-bottom: 1px solid #f5f5f5;
}
.step-result-card__icon { color: #16a34a; font-weight: 700; font-size: 13px; }
.step-result-card__order { font-size: 11px; font-weight: 600; color: #999; text-transform: uppercase; }
.step-result-card__label { font-size: 14px; font-weight: 600; color: #1e293b; flex: 1; }
.step-result-card__meta { display: flex; gap: 10px; font-size: 11px; color: #999; }

.step-result-card__body { padding: 14px 16px; }

.output-section { margin-bottom: 8px; }
.output-section:last-child { margin-bottom: 0; }
.output-label {
  font-size: 11px;
  font-weight: 600;
  color: #999;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  display: block;
  margin-bottom: 4px;
}

.s4-label {
  display: block;
  margin-bottom: 8px;
  font-size: 14px;
  font-weight: 700;
  color: #374151;
}
.output-text {
  margin: 0;
  font-size: 13px;
  line-height: 1.6;
  color: #444;
}
.output-text--title { font-size: 15px; font-weight: 600; color: #1e293b; }
.output-text--dim { color: #999; font-size: 12px; margin-top: 2px; }
.output-tags { display: flex; flex-wrap: wrap; gap: 6px; }
.output-meta { display: block; margin-top: 4px; font-size: 12px; color: #999; }
.output-stats {
  display: flex; gap: 12px; font-size: 12px; color: #999; margin-top: 4px;
}
.suggestion-list {
  margin: 4px 0 0;
  padding-left: 18px;
  font-size: 12px;
  color: #555;
  line-height: 1.6;
}

/* ── 六要素网格 ── */
.elements-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 6px;
}
.element-item {
  display: flex;
  gap: 6px;
  font-size: 12px;
  padding: 4px 0;
}
.element-key {
  font-weight: 600;
  color: #666;
  flex-shrink: 0;
}
.element-val {
  color: #333;
  word-break: break-all;
}

/* ── 候选标题列表 ── */
.titles-list p {
  margin: 2px 0;
  padding: 4px 8px;
  background: #fafafa;
  border-radius: 4px;
  font-size: 13px;
}

/* ── 检查项 ── */
.check-items {
  margin-top: 6px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.check-item {
  font-size: 12px;
  color: #555;
  display: flex;
  gap: 4px;
  align-items: baseline;
}

/* ── 空状态 ── */
.agent-empty {
  text-align: center;
  padding: 40px 20px;
  background: #fff;
  border: 1px dashed #e8e8e8;
  border-radius: 14px;
}
.agent-empty__title { font-size: 18px; font-weight: 700; color: #1e293b; margin: 0 0 8px; }
.agent-empty__desc { font-size: 13px; color: #666; line-height: 1.6; margin: 0 auto; max-width: 480px; }
.agent-empty__hint { margin-top: 10px; font-size: 12px; color: #999; }

/* ── 完成总结 ── */
.agent-summary :deep(.el-alert) { border-radius: 10px; }

/* ── Step 1 清洗统计 ── */
.clean-stats {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: #f9fafb;
  border-radius: 10px;
  margin-bottom: 8px;
}
.clean-stat-item {
  text-align: center;
  flex: 1;
}
.clean-stat-item--highlight .clean-stat-val {
  color: #16a34a;
  font-size: 22px;
}
.clean-stat-val {
  display: block;
  font-size: 20px;
  font-weight: 700;
  color: #1e293b;
  font-variant-numeric: tabular-nums;
}
.clean-stat-label {
  font-size: 11px;
  color: #999;
}
.clean-stat-arrow {
  font-size: 20px;
  color: #bbb;
  font-weight: 700;
}

/* ── 原文覆盖度热力图 ── */
.highlight-bar {
  display: flex;
  height: 12px;
  border-radius: 6px;
  overflow: hidden;
  gap: 2px;
  margin: 8px 0;
}
.highlight-seg {
  min-width: 4px;
  border-radius: 2px;
  cursor: pointer;
  transition: opacity 0.2s;
}
.highlight-seg:hover { opacity: 0.7; }
.highlight-legend {
  display: flex;
  gap: 12px;
  font-size: 11px;
  color: #999;
  margin-bottom: 8px;
  align-items: center;
}
.legend-dot {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 3px;
}

/* ── 逐句对齐分析 ── */
.similarity-item {
  padding: 10px 12px;
  margin-bottom: 8px;
  background: #fafafa;
  border-radius: 8px;
  border-left: 3px solid #e5e7eb;
  transition: all 0.2s;
  cursor: default;
}
.similarity-item:hover {
  border-left-color: #ff4d4f;
  background: #fff5f5;
}
.sim-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
  flex-wrap: wrap;
}
.sim-type-badge {
  padding: 2px 8px;
  border-radius: 4px;
  color: #fff;
  font-size: 11px;
  font-weight: 600;
}
.sim-score {
  font-size: 13px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  color: #1e293b;
}
.sim-reason {
  font-size: 11px;
  color: #999;
  flex: 1;
}
.sim-score-bar {
  height: 4px;
  background: #e5e7eb;
  border-radius: 2px;
  margin-bottom: 6px;
  overflow: hidden;
}
.sim-score-fill {
  height: 100%;
  border-radius: 2px;
  transition: width 0.3s ease;
}
.sim-summary-text {
  margin: 0;
  font-size: 12px;
  color: #555;
  line-height: 1.5;
}
.sim-source-text {
  margin: 4px 0 0;
  font-size: 11px;
  color: #999;
  font-style: italic;
  line-height: 1.4;
  padding-left: 12px;
  border-left: 2px solid #e5e7eb;
}

/* ── Hover 预览浮层 ── */
.sim-hover-preview {
  position: fixed;
  bottom: 24px;
  right: 24px;
  z-index: 100;
  max-width: 420px;
}
.hover-card {
  background: #fff;
  border: 1px solid #ffccc7;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 8px 32px rgba(0,0,0,.12);
}
.hover-score {
  font-size: 28px;
  font-weight: 700;
  margin-bottom: 4px;
}
.hover-type { margin-bottom: 8px; }
.hover-text {
  margin: 4px 0;
  font-size: 12px;
  line-height: 1.5;
  color: #444;
}
.hover-text--dim { color: #999; font-size: 11px; }
</style>
