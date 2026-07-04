<script setup lang="ts">
import { computed, onUnmounted, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import type { AIGenerateResponse } from '@/api/ai'
import { useNewsEditorAgentStore } from '@/stores/newsEditorAgent'
import { formatProviderLabel } from '@/utils/normalizeAIGenerateResult'
import Step7SummaryPanel from './Step7SummaryPanel.vue'

const props = defineProps<{
  inputText: string
  params?: Record<string, any>
  useMock?: boolean
}>()

const emit = defineEmits<{ (e: 'done', result: AIGenerateResponse | null): void }>()

const store = useNewsEditorAgentStore()
const submitting = ref(false)
const activeTab = ref<'generation' | 'quality'>('generation')

const completedCount = computed(() => store.steps.filter(step => step.status === 'completed').length)
const currentStep = computed(() => store.steps.find(step => step.status === 'running'))
const totalLatency = computed(() => store.steps.reduce((sum, step) => sum + step.latencyMs, 0))
const progressPct = computed(() => (store.steps.length ? Math.round((completedCount.value / store.steps.length) * 100) : 0))
const hasQualityData = computed(() => store.steps.slice(4).some(step => step.status !== 'pending'))
const summaryMode = computed(() => String(props.params?.summary_length || 'both'))

const statusLabel = computed(() => {
  switch (store.status) {
    case 'running':
      return currentStep.value ? `执行中 · Step ${currentStep.value.order}` : '执行中'
    case 'completed':
      return '全部完成'
    case 'failed':
      return '执行失败'
    default:
      return '待生成'
  }
})

const statusType = computed(() => {
  switch (store.status) {
    case 'running':
      return 'warning'
    case 'completed':
      return 'success'
    case 'failed':
      return 'danger'
    default:
      return 'info'
  }
})

const progressText = computed(() => {
  if (store.status === 'running') {
    return currentStep.value
      ? `当前步骤：${currentStep.value.label} · 已完成 ${completedCount.value}/8 · 耗时 ${formatMs(totalLatency.value)}`
      : `已完成 ${completedCount.value}/8 · 耗时 ${formatMs(totalLatency.value)}`
  }
  if (store.status === 'completed') {
    return `全部完成 · 总耗时 ${formatMs(totalLatency.value)}`
  }
  if (store.status === 'failed') {
    return store.error || '执行失败，请重试'
  }
  return '等待输入原文后启动生成'
})

function formatMs(ms: number): string {
  return ms >= 1000 ? `${(ms / 1000).toFixed(1)}s` : `${ms}ms`
}

function getStep(name: string) {
  return store.steps.find(step => step.name === name)
}

function stepBadgeType(status: string) {
  switch (status) {
    case 'completed':
      return 'success'
    case 'running':
      return 'warning'
    case 'failed':
      return 'danger'
    default:
      return 'info'
  }
}

function stepStateText(status: string) {
  switch (status) {
    case 'completed':
      return '已完成'
    case 'running':
      return '执行中'
    case 'failed':
      return '失败'
    default:
      return '等待'
  }
}

function stepStatusClass(status: string) {
  switch (status) {
    case 'completed':
      return 'is-complete'
    case 'running':
      return 'is-running'
    case 'failed':
      return 'is-failed'
    default:
      return 'is-pending'
  }
}

async function handleStart() {
  const text = props.inputText.trim()
  if (!text) {
    ElMessage.warning('请先输入新闻正文')
    return
  }
  if (text.length < 20) {
    ElMessage.warning('输入文本至少需要 20 个字符')
    return
  }

  submitting.value = true
  try {
    if (props.useMock === true) {
      await store.submitTaskMock(text, props.params)
    } else {
      await store.submitTask(text, props.params)
    }
    if (store.status === 'failed') {
      ElMessage.error(store.error || 'Agent 任务提交失败')
    }
  } catch {
    // store handles error state
  } finally {
    submitting.value = false
  }
}

function handleReset() {
  store.reset()
  activeTab.value = 'generation'
}

function handleAbort() {
  store.abort()
  activeTab.value = 'generation'
}

watch(() => store.status, (status) => {
  if (status === 'completed') emit('done', store.standardResult)
  if (status === 'failed') emit('done', null)
})

onUnmounted(() => {
  store.disconnect()
})

const cleanStep = computed(() => getStep('clean'))
const keywordStep = computed(() => getStep('extract_keywords'))
const elementStep = computed(() => getStep('extract_elements'))
const summaryStep = computed(() => getStep('generate_title_summary'))
const topicStep = computed(() => getStep('match_topic'))
const timelineStep = computed(() => getStep('judge_timeline'))
const consistencyStep = computed(() => getStep('check_consistency'))
const suggestionStep = computed(() => getStep('edit_suggestions'))

const showShortSummary = computed(() => {
  if (!summaryStep.value?.output?.summary_short) return false
  return summaryMode.value === 'short' || summaryMode.value === 'both'
})

const showLongSummary = computed(() => {
  if (!summaryStep.value?.output?.summary_long) return false
  return summaryMode.value === 'long' || summaryMode.value === 'both'
})
</script>

<template>
  <section class="agent-workbench">
    <div class="agent-toolbar">
      <div class="agent-toolbar__left">
        <el-button
          v-if="store.status === 'idle'"
          type="primary"
          size="large"
          class="main-btn"
          :loading="submitting"
          @click="handleStart"
        >
          {{ submitting ? '启动中...' : '启动 AI 生成' }}
        </el-button>

        <template v-else-if="store.status === 'running'">
          <el-button type="warning" size="large" disabled class="main-btn">
            执行中 · {{ completedCount }}/8
          </el-button>
          <el-button type="danger" size="large" plain class="ghost-btn" @click="handleAbort">
            取消
          </el-button>
        </template>

        <template v-else>
          <el-button v-if="store.status === 'completed'" type="success" size="large" disabled class="main-btn">
            全部完成 · {{ formatMs(totalLatency) }}
          </el-button>
          <el-button v-else-if="store.status === 'failed'" type="danger" size="large" disabled class="main-btn">
            执行失败
          </el-button>
          <el-button size="large" class="ghost-btn" @click="handleReset">
            重置
          </el-button>
        </template>
      </div>

      <div class="agent-toolbar__right">
        <div class="status-row">
          <el-tag :type="statusType" effect="plain" size="small" class="status-pill">
            {{ statusLabel }}
          </el-tag>
          <span class="status-text">{{ progressText }}</span>
          <span class="status-text">{{ completedCount }}/8</span>
        </div>
        <div class="progress-line">
          <div class="progress-line__track">
            <div class="progress-line__fill" :style="{ width: `${progressPct}%` }"></div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="store.status === 'idle'" class="agent-empty">
      <p class="agent-empty__title">AI 新闻智能编辑</p>
      <p class="agent-empty__desc">输入新闻正文后即可启动 8 步流水线。Step1-4 属于生成页，Step5-8 属于质检建议页。</p>
      <p class="agent-empty__hint">建议先检查左侧参数，再点击启动按钮。</p>
    </div>

    <template v-else>
      <div class="result-tabs">
        <button class="result-tabs__tab" :class="{ 'is-active': activeTab === 'generation' }" @click="activeTab = 'generation'">
          生成结果页
        </button>
        <button class="result-tabs__tab" :class="{ 'is-active': activeTab === 'quality' }" @click="activeTab = 'quality'">
          质检建议页
          <span v-if="hasQualityData" class="result-tabs__dot"></span>
        </button>
      </div>

      <div v-show="activeTab === 'generation'" class="result-page">
        <div class="compact-grid">
          <article class="mini-card">
            <div class="mini-card__head">
              <div>
                <p class="mini-card__title">Step 1 正文清洗</p>
              </div>
              <el-tag :type="stepBadgeType(cleanStep?.status || 'pending')" size="small">
                {{ stepStateText(cleanStep?.status || 'pending') }}
              </el-tag>
            </div>
            <div class="mini-card__body">
              <template v-if="cleanStep?.output">
                <div class="metric-line">
                  <span class="metric-pill">原文 {{ cleanStep.output.original_length || 0 }}</span>
                  <span class="metric-pill">清洗后 {{ cleanStep.output.cleaned_length || 0 }}</span>
                  <span class="metric-pill metric-pill--accent">压缩率 {{ cleanStep.output.reduction_pct || 0 }}%</span>
                </div>
                <div v-if="(cleanStep.output.removed_noise || []).length" class="tag-row">
                  <el-tag
                    v-for="(item, index) in cleanStep.output.removed_noise"
                    :key="index"
                    size="small"
                    effect="light"
                    type="danger"
                    class="soft-tag"
                  >
                    {{ item }}
                  </el-tag>
                </div>
                <p v-if="cleanStep.output.diff_preview?.change_summary" class="mini-copy">
                  {{ cleanStep.output.diff_preview.change_summary }}
                </p>
              </template>
              <div v-else class="empty-inline">等待清洗结果</div>
            </div>
          </article>

          <article class="mini-card">
            <div class="mini-card__head">
              <div>
                <p class="mini-card__title">Step 2 关键词提取</p>
              </div>
              <el-tag :type="stepBadgeType(keywordStep?.status || 'pending')" size="small">
                {{ stepStateText(keywordStep?.status || 'pending') }}
              </el-tag>
            </div>
            <div class="mini-card__body">
              <template v-if="keywordStep?.output">
                <div class="metric-grid">
                  <div class="metric-box">
                    <span class="metric-box__label">关键词</span>
                    <strong>{{ (keywordStep.output.keywords || []).length || 0 }}</strong>
                    <span class="metric-box__unit">个</span>
                  </div>
                  <div class="metric-box">
                    <span class="metric-box__label">来源</span>
                    <strong>{{ formatProviderLabel(keywordStep.provider) || 'NLP' }}</strong>
                  </div>
                  <div class="metric-box">
                    <span class="metric-box__label">耗时</span>
                    <strong>{{ formatMs(keywordStep.latencyMs || 0) }}</strong>
                  </div>
                </div>
                <div class="tag-row">
                  <el-tag
                    v-for="(kw, index) in (keywordStep.output.keywords || [])"
                    :key="index"
                    :type="index === 0 ? 'danger' : 'info'"
                    effect="light"
                    size="small"
                    class="soft-tag"
                  >
                    {{ typeof kw === 'string' ? kw : (kw.word || kw) }}
                  </el-tag>
                </div>
              </template>
              <div v-else class="empty-inline">等待关键词结果</div>
            </div>
          </article>
        </div>

        <article class="wide-card">
          <div class="wide-card__head">
            <div>
              <p class="wide-card__title">Step 3 六要素识别</p>
            </div>
            <el-tag :type="stepBadgeType(elementStep?.status || 'pending')" size="small">
              {{ stepStateText(elementStep?.status || 'pending') }}
            </el-tag>
          </div>
          <div class="wide-card__body">
            <div v-if="elementStep?.output?.news_elements" class="elements-table">
              <div class="element-row">
                <span class="element-label">人物 / 主体</span>
                <span class="element-value">{{ elementStep.output.news_elements.who || '暂无' }}</span>
                <span class="element-label">事件</span>
                <span class="element-value">{{ elementStep.output.news_elements.what || '暂无' }}</span>
              </div>
              <div class="element-row">
                <span class="element-label">时间</span>
                <span class="element-value">{{ elementStep.output.news_elements.when || '暂无' }}</span>
                <span class="element-label">地点</span>
                <span class="element-value">{{ elementStep.output.news_elements.where || '暂无' }}</span>
              </div>
              <div class="element-row">
                <span class="element-label">原因</span>
                <span class="element-value">{{ elementStep.output.news_elements.why || '暂无' }}</span>
                <span class="element-label">方式</span>
                <span class="element-value">{{ elementStep.output.news_elements.how || '暂无' }}</span>
              </div>
            </div>
            <div v-else class="empty-inline">等待六要素识别结果</div>
          </div>
        </article>

        <article class="hero-card">
          <div class="hero-card__head">
            <div>
              <p class="hero-card__title">Step 4 标题摘要生成</p>
            </div>
            <el-tag :type="stepBadgeType(summaryStep?.status || 'pending')" size="small" class="step-tag">
              {{ stepStateText(summaryStep?.status || 'pending') }}
            </el-tag>
          </div>
          <div class="hero-card__body">
            <template v-if="summaryStep?.output">
              <div v-if="(summaryStep.output.candidate_titles || []).length" class="hero-section hero-section--accent">
                <div class="hero-section__label">候选标题</div>
                <div class="title-stack">
                  <p v-for="(title, index) in summaryStep.output.candidate_titles" :key="index" class="title-item">
                    <span class="title-index">{{ Number(index) + 1 }}</span>
                    <span class="title-text">{{ title }}</span>
                  </p>
                </div>
              </div>

              <div class="summary-grid">
                <div v-if="showShortSummary" class="hero-section">
                  <div class="hero-section__label">短摘要</div>
                  <p class="summary-text">{{ summaryStep.output.summary_short }}</p>
                </div>
                <div v-if="showLongSummary" class="hero-section">
                  <div class="hero-section__label">长摘要</div>
                  <p class="summary-text">{{ summaryStep.output.summary_long }}</p>
                </div>
              </div>

              <div v-if="!showShortSummary && !showLongSummary" class="empty-inline">
                当前摘要长度设置未显示摘要内容
              </div>

              <div v-if="(summaryStep.output.summary_points || []).length" class="hero-section">
                <div class="hero-section__label">摘要要点</div>
                <ul class="point-list">
                  <li v-for="(point, index) in summaryStep.output.summary_points" :key="index">
                    {{ point }}
                  </li>
                </ul>
              </div>
            </template>
            <div v-else class="empty-inline">等待标题摘要结果</div>
          </div>
        </article>
      </div>

      <div v-show="activeTab === 'quality'" class="result-page">
        <div class="compact-grid">
          <article class="mini-card">
            <div class="mini-card__head">
              <div>
                <p class="mini-card__title">Step 5 话题匹配</p>
              </div>
              <el-tag :type="stepBadgeType(topicStep?.status || 'pending')" size="small">
                {{ stepStateText(topicStep?.status || 'pending') }}
              </el-tag>
            </div>
            <div class="mini-card__body">
              <template v-if="topicStep?.output">
                <div class="topic-match">
                  <div v-if="topicStep.output.primary_topic" class="topic-primary">
                    <span class="topic-label">主话题</span>
                    <strong>{{ topicStep.output.primary_topic }}</strong>
                  </div>
                  <div v-if="(topicStep.output.secondary_topics || []).length" class="topic-secondary">
                    <span class="topic-label">相关话题</span>
                    <div class="topic-chip-row">
                      <span
                        v-for="(item, index) in (topicStep.output.secondary_topics || [])"
                        :key="index"
                        class="topic-chip"
                      >
                        {{ item }}
                      </span>
                    </div>
                  </div>
                </div>
                <div class="topic-meta">
                  <span>置信度 {{ ((topicStep.output.confidence || 0) * 100).toFixed(0) }}%</span>
                  <span>{{ topicStep.output.topic_category || '未分类' }}</span>
                </div>
              </template>
              <div v-else class="empty-inline">等待话题匹配结果</div>
            </div>
          </article>

          <article class="mini-card">
            <div class="mini-card__head">
              <div>
                <p class="mini-card__title">Step 6 时间线适配</p>
              </div>
              <el-tag :type="stepBadgeType(timelineStep?.status || 'pending')" size="small">
                {{ stepStateText(timelineStep?.status || 'pending') }}
              </el-tag>
            </div>
            <div class="mini-card__body">
              <template v-if="timelineStep?.output">
                <div class="tag-row">
                  <el-tag :type="timelineStep.output.is_timely ? 'success' : 'warning'" size="small">
                    {{ timelineStep.output.is_timely ? '符合时效' : '需要更新' }}
                  </el-tag>
                  <el-tag v-if="timelineStep.output.time_sensitivity" type="info" effect="light" size="small">
                    敏感度 {{ timelineStep.output.time_sensitivity }}
                  </el-tag>
                  <el-tag v-if="timelineStep.output.recommended_position" type="danger" effect="light" size="small">
                    {{ timelineStep.output.recommended_position }}
                  </el-tag>
                </div>
                <p v-if="timelineStep.output.reason" class="mini-copy">
                  {{ timelineStep.output.reason }}
                </p>
              </template>
              <div v-else class="empty-inline">等待时间线判断结果</div>
            </div>
          </article>
        </div>

        <article class="wide-card">
          <div class="wide-card__head">
            <div>
              <p class="wide-card__title">Step 7 一致性检查</p>
            </div>
            <el-tag :type="stepBadgeType(consistencyStep?.status || 'pending')" size="small">
              {{ stepStateText(consistencyStep?.status || 'pending') }}
            </el-tag>
          </div>
          <div class="wide-card__body">
            <Step7SummaryPanel :consistency-data="consistencyStep?.output || null" />
          </div>
        </article>

        <article class="wide-card">
          <div class="wide-card__head">
            <div>
              <p class="wide-card__title">Step 8 编辑建议生成</p>
            </div>
            <el-tag :type="stepBadgeType(suggestionStep?.status || 'pending')" size="small">
              {{ stepStateText(suggestionStep?.status || 'pending') }}
            </el-tag>
          </div>
          <div class="wide-card__body">
            <template v-if="suggestionStep?.output">
              <ul v-if="(suggestionStep.output.suggestions || []).length" class="suggestion-list">
                <li v-for="(item, index) in suggestionStep.output.suggestions" :key="index" class="suggestion-item">
                  <el-tag
                    :type="item.priority === 'high' ? 'danger' : item.priority === 'medium' ? 'warning' : 'info'"
                    size="small"
                    effect="light"
                    class="soft-tag"
                  >
                    {{ item.type || '建议' }}
                  </el-tag>
                  <strong>{{ item.detail || item.reason || item }}</strong>
                  <span v-if="item.detail && item.reason" class="mini-copy mini-copy--inline">· {{ item.reason }}</span>
                </li>
              </ul>
              <div v-else class="empty-inline">暂无编辑建议</div>

              <div v-if="suggestionStep.output.ready_to_publish !== undefined" class="publish-row">
                <el-tag :type="suggestionStep.output.ready_to_publish ? 'success' : 'warning'" size="small">
                  {{ suggestionStep.output.ready_to_publish ? '可直接发布' : '仍需修改' }}
                </el-tag>
              </div>
            </template>
            <div v-else class="empty-inline">等待编辑建议结果</div>
          </div>
        </article>
      </div>

      <div v-if="store.status === 'completed'" class="summary-banner">
        <el-alert
          title="全部完成"
          type="success"
          :description="`8/8 已完成，总耗时 ${formatMs(totalLatency)}。`"
          :closable="false"
          show-icon
        />
      </div>

      <div v-else-if="store.status === 'failed'" class="summary-banner">
        <el-alert
          title="执行失败"
          type="error"
          :description="store.error || 'Agent 执行失败，请重试。'"
          :closable="false"
          show-icon
        />
      </div>
    </template>
  </section>
</template>

<style scoped>
.agent-workbench {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.agent-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  min-height: 64px;
  padding: 12px 14px;
  background: var(--color-bg-card);
  border: 1px solid var(--color-primary-light);
  border-radius: 16px;
  box-shadow: 0 8px 24px rgba(217, 45, 32, 0.06);
}

.agent-toolbar__left {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  flex-shrink: 0;
}

.agent-toolbar__right {
  flex: 1;
  min-width: 320px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  align-items: flex-end;
}

.status-row {
  display: flex;
  align-items: center;
  gap: 10px;
  justify-content: flex-end;
  flex-wrap: wrap;
}

.status-pill {
  border-radius: 999px;
  border-color: var(--color-primary-light);
}

.status-text {
  font-size: 12px;
  color: var(--color-text-secondary);
  font-variant-numeric: tabular-nums;
}

.progress-line {
  width: min(520px, 100%);
}

.progress-line__track {
  height: 5px;
  border-radius: 999px;
  overflow: hidden;
  background: var(--color-primary-soft);
}

.progress-line__fill {
  height: 100%;
  border-radius: 999px;
  background: linear-gradient(90deg, #d92d20 0%, #ea4d3d 100%);
}

.main-btn {
  min-width: 168px;
  height: 40px;
  font-size: 15px;
  font-weight: 600;
  border: none;
  border-radius: 10px;
  background: linear-gradient(135deg, #d92d20 0%, #ea4d3d 100%);
}

.main-btn:not(:disabled):hover {
  background: linear-gradient(135deg, #ea4d3d 0%, #b42318 100%) !important;
}

.ghost-btn {
  border-radius: 10px;
  border-color: var(--color-primary-light);
  color: var(--color-primary);
  height: 40px;
}

.agent-empty {
  padding: 22px 18px;
  text-align: center;
  background: var(--color-bg-card);
  border: 1px dashed var(--color-primary-light);
  border-radius: 16px;
}

.agent-empty__title {
  margin: 0 0 8px;
  font-size: 18px;
  font-weight: 700;
  color: var(--color-text-primary);
}

.agent-empty__desc {
  margin: 0 auto;
  max-width: 700px;
  font-size: 13px;
  line-height: 1.7;
  color: var(--color-text-secondary);
}

.agent-empty__hint {
  margin: 10px 0 0;
  font-size: 12px;
  color: var(--color-text-muted);
}

.result-tabs {
  display: flex;
  gap: 10px;
}

.result-tabs__tab {
  position: relative;
  padding: 10px 16px;
  border-radius: 999px;
  border: 1px solid var(--color-primary-light);
  background: var(--color-bg-card);
  color: var(--color-text-secondary);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
}

.result-tabs__tab.is-active {
  color: var(--color-primary);
  background: var(--color-primary-soft);
  border-color: var(--color-primary-light);
}

.result-tabs__dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  margin-left: 8px;
  border-radius: 999px;
  background: #d92d20;
}

.result-page {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.hero-card,
.mini-card,
.wide-card {
  background: var(--color-bg-card);
  border: 1px solid var(--color-primary-light);
  border-radius: 18px;
  overflow: hidden;
  box-shadow: 0 10px 28px rgba(217, 45, 32, 0.05);
}

.hero-card {
  border-left: 6px solid var(--color-primary);
  background: linear-gradient(180deg, var(--color-bg-card) 0%, var(--color-primary-soft) 100%);
}

.hero-card__head,
.mini-card__head,
.wide-card__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  padding: 16px 18px 0;
}

.hero-card__title,
.mini-card__title,
.wide-card__title {
  margin: 0;
  font-size: 18px;
  line-height: 1.35;
  font-weight: 800;
  color: var(--color-text-primary);
}

.hero-card__body,
.mini-card__body,
.wide-card__body {
  padding: 14px 18px 18px;
}

.step-tag {
  border-radius: 999px;
}

.hero-section {
  padding: 14px;
  border-radius: 16px;
  background: var(--color-bg-card);
  border: 1px solid var(--color-primary-light);
}

.hero-section--accent {
  background: var(--color-primary-soft);
  border-color: var(--color-primary-light);
}

.hero-section__label {
  margin-bottom: 10px;
  font-size: 12px;
  font-weight: 700;
  color: var(--color-primary);
  text-transform: uppercase;
  letter-spacing: 0.02em;
}

.title-stack {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.title-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  margin: 0;
  padding: 10px 12px;
  border-radius: 12px;
  background: var(--color-bg-card);
  border: 1px solid var(--color-primary-light);
}

.title-index {
  flex-shrink: 0;
  width: 24px;
  height: 24px;
  border-radius: 999px;
  background: #d92d20;
  color: #fff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
}

.title-text {
  flex: 1;
  font-size: 14px;
  line-height: 1.7;
  color: var(--color-text-primary);
}

.summary-grid,
.compact-grid {
  display: grid;
  gap: 14px;
}

.summary-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
  margin-top: 12px;
}

.compact-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.metric-line {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.metric-line--single {
  gap: 10px;
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.metric-box {
  min-width: 0;
  padding: 10px 12px;
  border-radius: 14px;
  background: var(--color-primary-soft);
  border: 1px solid var(--color-primary-light);
}

.metric-box__label {
  display: block;
  margin-bottom: 5px;
  color: var(--color-text-secondary);
  font-size: 11px;
  line-height: 1;
}

.metric-box strong {
  color: var(--color-text-primary);
  font-size: 14px;
  line-height: 1.35;
  font-weight: 700;
  word-break: break-word;
  font-variant-numeric: tabular-nums;
}

.metric-box__unit {
  margin-left: 3px;
  color: var(--color-text-secondary);
  font-size: 12px;
}

.metric-pill {
  display: inline-flex;
  align-items: center;
  padding: 6px 10px;
  border-radius: 999px;
  background: var(--color-primary-soft);
  border: 1px solid var(--color-primary-light);
  color: var(--color-text-primary);
  font-size: 12px;
  font-variant-numeric: tabular-nums;
}

.metric-pill--accent {
  background: var(--color-primary-soft);
  border-color: var(--color-primary-light);
  color: var(--color-primary);
  font-weight: 700;
}

.tag-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 10px;
}

.soft-tag {
  border-radius: 999px;
}

.topic-match {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.topic-primary,
.topic-secondary {
  min-width: 0;
  padding: 12px;
  border-radius: 14px;
  border: 1px solid var(--color-primary-light);
  background: var(--color-bg-card);
}

.topic-primary {
  background: linear-gradient(135deg, var(--color-primary-soft), var(--color-bg-card));
  border-left: 4px solid var(--color-primary);
}

.topic-label {
  display: block;
  margin-bottom: 8px;
  color: var(--color-text-secondary);
  font-size: 11px;
  font-weight: 700;
}

.topic-primary strong {
  display: block;
  color: var(--color-text-primary);
  font-size: 14px;
  line-height: 1.45;
  word-break: break-word;
}

.topic-chip-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.topic-chip {
  max-width: 100%;
  padding: 6px 10px;
  border-radius: 999px;
  background: var(--color-bg-hover);
  border: 1px solid var(--color-border);
  color: var(--color-text-primary);
  font-size: 12px;
  line-height: 1.35;
  word-break: break-word;
}

.topic-meta {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
  margin-top: 12px;
}

.topic-meta span {
  min-width: 0;
  padding: 7px 10px;
  border-radius: 12px;
  background: var(--color-primary-soft);
  color: var(--color-text-secondary);
  font-size: 12px;
  line-height: 1.35;
  word-break: break-word;
  font-variant-numeric: tabular-nums;
}

.summary-text,
.mini-copy {
  margin: 0;
  font-size: 13px;
  line-height: 1.8;
  color: var(--color-text-primary);
  white-space: pre-wrap;
  word-break: break-word;
}

.mini-copy {
  margin-top: 10px;
  color: var(--color-text-secondary);
}

.mini-copy--inline {
  margin-top: 0;
}

.empty-inline {
  padding: 12px 14px;
  border-radius: 14px;
  background: var(--color-primary-soft);
  border: 1px dashed var(--color-primary-light);
  color: var(--color-text-muted);
  font-size: 13px;
  text-align: center;
}

.point-list {
  margin: 0;
  padding-left: 18px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  color: var(--color-text-primary);
}

.elements-table {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.element-row {
  display: grid;
  grid-template-columns: 92px minmax(0, 1fr) 92px minmax(0, 1fr);
  gap: 10px 12px;
  padding: 10px 0;
  border-bottom: 1px solid var(--color-border);
}

.element-row:last-child {
  border-bottom: none;
}

.element-label {
  font-size: 12px;
  font-weight: 700;
  color: var(--color-primary);
}

.element-value {
  font-size: 13px;
  line-height: 1.7;
  color: var(--color-text-primary);
  word-break: break-word;
}

.suggestion-list {
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
  list-style: none;
}

.suggestion-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  flex-wrap: wrap;
  padding: 12px 14px;
  border-radius: 14px;
  background: var(--color-primary-soft);
  border: 1px solid var(--color-primary-light);
  color: var(--color-text-primary);
  font-size: 13px;
  line-height: 1.7;
}

.publish-row {
  display: flex;
  margin-top: 12px;
}

.summary-banner {
  margin-top: 2px;
}

@media (max-width: 1120px) {
  .summary-grid,
  .compact-grid {
    grid-template-columns: 1fr;
  }

  .element-row {
    grid-template-columns: 88px minmax(0, 1fr);
  }
}

@media (max-width: 720px) {
  .metric-grid,
  .topic-meta {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 900px) {
  .agent-toolbar {
    flex-direction: column;
    align-items: stretch;
  }

  .agent-toolbar__right {
    align-items: stretch;
    min-width: 0;
  }

  .status-row {
    justify-content: flex-start;
  }

  .progress-line {
    width: 100%;
  }

  .result-tabs {
    overflow-x: auto;
    padding-bottom: 2px;
  }

  .hero-card__head,
  .mini-card__head,
  .wide-card__head {
    padding: 14px 14px 0;
  }

  .hero-card__body,
  .mini-card__body,
  .wide-card__body {
    padding: 14px;
  }

  .element-row {
    grid-template-columns: 1fr;
  }
}
</style>
