<script setup lang="ts">
/** News Editor Agent — 主视图（Phase 4 升级）。
 *
 * 布局：
 *   1. 输入面板 — 文本输入 + 提交按钮（始终可见）
 *   2. Tab 面板 — 实时时间线 | DAG 执行图 | 结果 | 回放 | 可解释性
 *
 * 通过 SSE 驱动实时更新，无需轮询。
 */

import { ref, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useNewsEditorAgentStore } from '@/stores/newsEditorAgent'
import AgentDAGView from '@/components/agent/AgentDAGView.vue'
import AgentReplayView from '@/components/agent/AgentReplayView.vue'
import AgentExplainPanel from '@/components/agent/AgentExplainPanel.vue'

const store = useNewsEditorAgentStore()

const inputText = ref('')
const submitting = ref(false)
const activeTab = ref('timeline')

const MIN_TEXT_LENGTH = 20

async function handleSubmit() {
  const text = inputText.value.trim()
  if (!text) {
    ElMessage.warning('请输入新闻文本')
    return
  }
  if (text.length < MIN_TEXT_LENGTH) {
    ElMessage.warning(`输入文本至少需要 ${MIN_TEXT_LENGTH} 个字符`)
    return
  }

  submitting.value = true
  try {
    await store.submitTask(text)
    if (store.status === 'failed') {
      ElMessage.error(store.error || '任务提交失败')
    }
  } catch {
    // store 已处理错误
  } finally {
    submitting.value = false
  }
}

function handleReset() {
  store.reset()
  inputText.value = ''
  activeTab.value = 'timeline'
}

function statusIcon(stepStatus: string): string {
  switch (stepStatus) {
    case 'completed': return '✔'
    case 'running':   return '↻'
    case 'failed':    return '✖'
    default:          return '○'
  }
}

function statusClass(stepStatus: string): string {
  return `step--${stepStatus}`
}

function formatMs(ms: number): string {
  if (ms >= 1000) return (ms / 1000).toFixed(1) + 's'
  return ms + 'ms'
}

function qualityText(level: string): string {
  switch (level) {
    case 'low': return '低质量'
    case 'medium': return '中质量'
    case 'high': return '高质量'
    default: return level || '未知'
  }
}

// 清理 SSE 连接
onUnmounted(() => {
  store.disconnect()
})
</script>

<template>
  <div class="agent-view">
    <!-- ═══════════════════════════════════════════════════ -->
    <!-- 页面标题 -->
    <!-- ═══════════════════════════════════════════════════ -->
    <div class="agent-view__header">
      <h1 class="agent-view__title">
        <span class="agent-view__title-icon">🤖</span>
        AI 新闻智能编辑
      </h1>
      <p class="agent-view__subtitle">输入原始新闻文本，AI Agent 将自动执行 8 步编辑流水线 | DAG 可视化 · 回放 · 可观测</p>
    </div>

    <!-- ═══════════════════════════════════════════════════ -->
    <!-- 输入面板（始终可见） -->
    <!-- ═══════════════════════════════════════════════════ -->
    <section class="panel panel--input">
      <div class="panel__header">
        <h2 class="panel__title">📝 新闻文本输入</h2>
        <el-tag
          v-if="store.status === 'idle'"
          type="info"
          size="small"
        >等待输入</el-tag>
        <el-tag
          v-else-if="store.status === 'running'"
          type="warning"
          size="small"
        >{{ store.completedCount }}/8 执行中...</el-tag>
        <el-tag
          v-else-if="store.status === 'completed'"
          type="success"
          size="small"
        >{{ store.totalLatencyMs > 0 ? `完成 · ${formatMs(store.totalLatencyMs)}` : '完成' }}</el-tag>
        <el-tag
          v-else-if="store.status === 'failed'"
          type="danger"
          size="small"
        >失败</el-tag>
      </div>

      <el-input
        v-model="inputText"
        type="textarea"
        :rows="5"
        placeholder="请粘贴新闻原文（至少20个字符）..."
        :disabled="store.status === 'running'"
        class="input-textarea"
      />

      <div class="panel__actions">
        <span class="char-count">{{ inputText.trim().length }} 字符</span>
        <el-button
          type="primary"
          :loading="submitting"
          :disabled="store.status === 'running'"
          @click="handleSubmit"
        >
          {{ submitting ? '提交中...' : '🚀 启动 AI 编辑流水线' }}
        </el-button>
        <el-button
          v-if="store.status !== 'idle' && store.status !== 'running'"
          @click="handleReset"
        >重置</el-button>
      </div>

      <el-alert
        v-if="store.error && store.status === 'failed'"
        :title="store.error"
        type="error"
        show-icon
        :closable="false"
        class="error-alert"
      />
    </section>

    <!-- ═══════════════════════════════════════════════════ -->
    <!-- Tab 面板 -->
    <!-- ═══════════════════════════════════════════════════ -->
    <div class="panel panel--tabs">
      <el-tabs v-model="activeTab" class="agent-tabs">
        <!-- Tab 1: 实时时间线 -->
        <el-tab-pane label="⚡ 实时时间线" name="timeline">
          <div class="timeline">
            <div
              v-for="step in store.steps"
              :key="step.name"
              class="timeline__step"
              :class="statusClass(step.status)"
            >
              <div class="step__icon">
                <span v-if="step.status === 'running'" class="step__spinner"></span>
                <span v-else>{{ statusIcon(step.status) }}</span>
              </div>
              <div class="step__info">
                <div class="step__header">
                  <span class="step__order">Step {{ step.order }}</span>
                  <span class="step__label">{{ step.label }}</span>
                </div>
                <div v-if="step.status === 'completed'" class="step__meta">
                  <span v-if="step.latencyMs > 0" class="step__latency">⏱ {{ formatMs(step.latencyMs) }}</span>
                  <span v-if="step.tokens > 0" class="step__tokens">🔤 {{ step.tokens }} tokens</span>
                  <span v-if="step.provider" class="step__provider">
                    {{ step.provider === 'local' ? '💻' : step.provider === 'mock' ? '📦' : '🤖' }}
                    {{ step.provider }}<template v-if="step.model"> / {{ step.model }}</template>
                  </span>
                </div>
                <div v-if="step.status === 'failed'" class="step__error">{{ step.error || '执行失败' }}</div>
              </div>
              <div v-if="step.order < 8" class="step__connector" :class="{ 'is-active': step.status === 'completed' }"></div>
            </div>
          </div>
        </el-tab-pane>

        <!-- Tab 2: DAG 执行图 -->
        <el-tab-pane label="🔀 DAG 执行图" name="dag">
          <AgentDAGView
            :steps="store.steps.map(s => ({
              name: s.name,
              label: s.label,
              order: s.order,
              status: s.status,
              latencyMs: s.latencyMs,
              tokens: s.tokens,
              provider: s.provider,
              model: s.model,
            }))"
            :task-id="store.taskId"
          />
        </el-tab-pane>

        <!-- Tab 3: 结果面板 -->
        <el-tab-pane label="📊 结果" name="result">
          <div class="result-panel">
            <el-empty
              v-if="store.status === 'idle'"
              description="提交文本后，结果将在此展示"
              :image-size="60"
            />
            <el-skeleton v-else-if="store.status === 'running'" animated :rows="6" :throttle="500" />

            <template v-else-if="store.result">
              <div v-if="store.result.title" class="result-block">
                <h3 class="result-block__title">📰 生成标题</h3>
                <p class="result-block__content result-block__content--title">{{ store.result.title }}</p>
              </div>
              <div v-if="store.result.summary" class="result-block">
                <h3 class="result-block__title">📝 摘要</h3>
                <p class="result-block__content">{{ store.result.summary }}</p>
              </div>
              <div v-if="store.result.topic" class="result-block">
                <h3 class="result-block__title">🏷 话题匹配</h3>
                <div class="result-tags">
                  <el-tag v-if="store.result.topic.primary_topic" type="danger" effect="dark">{{ store.result.topic.primary_topic }}</el-tag>
                  <el-tag v-for="t in store.result.topic.secondary_topics" :key="t" effect="plain">{{ t }}</el-tag>
                </div>
                <span v-if="store.result.topic.confidence" class="result-block__sub">置信度: {{ (store.result.topic.confidence * 100).toFixed(0) }}%</span>
              </div>
              <div v-if="store.result.timeline" class="result-block">
                <h3 class="result-block__title">📅 时间线适配</h3>
                <div class="result-row">
                  <el-tag :type="store.result.timeline.is_timely ? 'success' : 'warning'" size="small">
                    {{ store.result.timeline.is_timely ? '✅ 符合时效' : '⚠️ 需更新' }}
                  </el-tag>
                  <span v-if="store.result.timeline.time_sensitivity">时效敏感度: {{ store.result.timeline.time_sensitivity }}</span>
                </div>
                <p v-if="store.result.timeline.recommended_position" class="result-block__sub">推荐位置: {{ store.result.timeline.recommended_position }}</p>
              </div>
              <div v-if="store.result.consistency" class="result-block">
                <h3 class="result-block__title">🔍 一致性检查</h3>
                <div class="result-row">
                  <el-tag :type="store.result.consistency.risk_level === 'low' ? 'success' : store.result.consistency.risk_level === 'medium' ? 'warning' : 'danger'" size="small">
                    质量: {{ qualityText(store.result.consistency.risk_level) }}
                  </el-tag>
                </div>
                <ul v-if="store.result.consistency.suggestions?.length" class="result-list">
                  <li v-for="(s, i) in store.result.consistency.suggestions" :key="i">{{ s }}</li>
                </ul>
              </div>
              <div v-if="store.result.editSuggestions" class="result-block">
                <h3 class="result-block__title">✏️ 编辑建议</h3>
                <div v-if="store.result.editSuggestions.overall_score" class="result-row">
                  <span>综合评分: </span>
                  <el-tag type="warning" effect="dark">{{ store.result.editSuggestions.overall_score }} / 100</el-tag>
                </div>
                <ul v-if="store.result.editSuggestions.suggestions?.length" class="result-list result-list--suggestions">
                  <li v-for="(s, i) in store.result.editSuggestions.suggestions" :key="i">
                    <span class="suggestion-type">{{ s.type }}</span>
                    <span v-if="s.reason"> — {{ s.reason }}</span>
                  </li>
                </ul>
              </div>
            </template>

            <el-alert v-if="store.status === 'failed' && store.error" :title="store.error" type="error" show-icon :closable="false" />
          </div>
        </el-tab-pane>

        <!-- Tab 4: 回放 -->
        <el-tab-pane label="▶ 回放" name="replay">
          <AgentReplayView
            v-if="store.taskId"
            :task-id="store.taskId"
          />
          <el-empty v-else description="提交任务后可使用回放功能" :image-size="60" />
        </el-tab-pane>

        <!-- Tab 5: 可解释性 -->
        <el-tab-pane label="💡 可解释性" name="explain">
          <AgentExplainPanel :task-id="store.taskId" />
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>

<style scoped>
/* ========================================
   页面容器
   ======================================== */
.agent-view {
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 0 40px;
}

.agent-view__header { margin-bottom: 20px; }

.agent-view__title {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 0;
  font-size: 24px;
  font-weight: 700;
  color: var(--color-text-primary);
}
.agent-view__title-icon { font-size: 28px; }

.agent-view__subtitle {
  margin: 6px 0 0 38px;
  color: var(--color-text-secondary);
  font-size: 14px;
}

/* ========================================
   面板通用
   ======================================== */
.panel {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: 16px;
  padding: 20px;
  margin-bottom: 20px;
}

.panel__header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
}
.panel__title {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  color: var(--color-text-primary);
}
.panel__actions {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 14px;
}
.char-count {
  margin-right: auto;
  color: var(--color-text-secondary);
  font-size: 12px;
  font-variant-numeric: tabular-nums;
}
.error-alert { margin-top: 14px; }

/* Tab 面板 */
.panel--tabs {
  min-height: 400px;
}

.agent-tabs :deep(.el-tabs__header) {
  margin-bottom: 8px;
}
.agent-tabs :deep(.el-tabs__nav-wrap::after) {
  height: 1px;
}

/* ========================================
   输入
   ======================================== */
.input-textarea :deep(.el-textarea__inner) {
  font-size: 14px;
  line-height: 1.7;
  border-radius: 10px;
}

/* ========================================
   步骤时间线
   ======================================== */
.timeline { position: relative; padding: 4px 0; }
.timeline__step {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  position: relative;
  padding: 10px 0;
}
.step__connector {
  position: absolute;
  left: 15px;
  top: 44px;
  width: 2px;
  height: calc(100% - 28px);
  background: var(--color-border);
  border-radius: 1px;
  transition: background 0.3s ease;
}
.step__connector.is-active { background: var(--color-primary); opacity: 0.35; }

.step__icon {
  flex: 0 0 32px;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  font-size: 14px;
  font-weight: 700;
  background: color-mix(in srgb, var(--color-text-secondary) 12%, transparent);
  color: var(--color-text-secondary);
  transition: all 0.35s ease;
  z-index: 1;
}
.step--running .step__icon {
  background: color-mix(in srgb, var(--color-primary) 15%, transparent);
  color: var(--color-primary);
  box-shadow: 0 0 0 4px color-mix(in srgb, var(--color-primary) 8%, transparent);
}
.step--completed .step__icon {
  background: color-mix(in srgb, #22c55e 15%, transparent);
  color: #16a34a;
}
.step--failed .step__icon {
  background: color-mix(in srgb, #ef4444 15%, transparent);
  color: #dc2626;
}

.step__spinner {
  display: inline-block;
  width: 16px;
  height: 16px;
  border: 2px solid color-mix(in srgb, var(--color-primary) 25%, transparent);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: step-spin 0.8s linear infinite;
}
@keyframes step-spin {
  from { transform: rotate(0deg); }
  to   { transform: rotate(360deg); }
}

.step__info { flex: 1; min-width: 0; padding-top: 4px; }
.step__header { display: flex; align-items: center; gap: 8px; }
.step__order {
  font-size: 11px;
  font-weight: 600;
  color: var(--color-text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
.step__label { font-size: 14px; font-weight: 600; color: var(--color-text-primary); }
.step--running .step__label { color: var(--color-primary); }
.step__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 4px;
  font-size: 12px;
  color: var(--color-text-secondary);
  font-variant-numeric: tabular-nums;
}
.step__error { margin-top: 4px; font-size: 12px; color: #dc2626; }

/* ========================================
   结果面板
   ======================================== */
.result-panel { min-height: 300px; }
.result-block {
  margin-bottom: 18px;
  padding-bottom: 16px;
  border-bottom: 1px solid color-mix(in srgb, var(--color-border) 60%, transparent);
}
.result-block:last-child { margin-bottom: 0; padding-bottom: 0; border-bottom: 0; }
.result-block__title {
  margin: 0 0 6px;
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.03em;
}
.result-block__content {
  margin: 0;
  font-size: 14px;
  line-height: 1.65;
  color: var(--color-text-primary);
}
.result-block__content--title { font-size: 16px; font-weight: 600; line-height: 1.5; }
.result-block__sub { display: block; margin-top: 4px; font-size: 12px; color: var(--color-text-secondary); }
.result-tags { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 6px; }
.result-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  font-size: 13px;
  color: var(--color-text-secondary);
}
.result-list {
  margin: 6px 0 0;
  padding-left: 18px;
  font-size: 13px;
  color: var(--color-text-primary);
  line-height: 1.6;
}
.result-list--suggestions { list-style: none; padding-left: 0; }
.result-list--suggestions li {
  padding: 6px 10px;
  margin-bottom: 4px;
  background: color-mix(in srgb, var(--color-primary) 5%, var(--color-bg-card));
  border-radius: 8px;
  font-size: 13px;
}
.suggestion-type { font-weight: 600; color: var(--color-primary); }
</style>
