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

// ── Step 8 建议类型兜底中文映射（兼容旧英文数据） ──
const EDIT_TYPE_CN_MAP: Record<string, string> = {
  title: '标题优化', headline: '标题优化', heading: '标题优化',
  summary: '摘要优化', abstract: '摘要优化', digest: '摘要优化',
  fact: '事实核查', 'fact check': '事实核查', fact_check: '事实核查', consistency: '事实核查', evidence: '事实核查',
  element: '要素补充', '5w1h': '要素补充',
  structure: '结构建议', format: '结构建议', layout: '结构建议',
  quality: '质量提醒', risk: '质量提醒', warning: '质量提醒',
  publish: '发布建议', release: '发布建议',
}
function displayEditType(raw: string): string {
  if (!raw) return '建议'
  const key = raw.trim()
  // 直接命中
  if (EDIT_TYPE_CN_MAP[key]) return EDIT_TYPE_CN_MAP[key]
  if (EDIT_TYPE_CN_MAP[key.toLowerCase()]) return EDIT_TYPE_CN_MAP[key.toLowerCase()]
  // 模糊匹配
  for (const [en, zh] of Object.entries(EDIT_TYPE_CN_MAP)) {
    if (key.includes(en) || en.includes(key.toLowerCase())) return zh
  }
  // 已经是中文则原样
  if (/[一-鿿]/.test(key)) return key
  return '建议'
}

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
              <el-tag effect="dark" :type="stepBadgeType(cleanStep?.status || 'pending')" size="small">
                {{ stepStateText(cleanStep?.status || 'pending') }}
              </el-tag>
            </div>
            <div class="mini-card__body">
              <template v-if="cleanStep?.output">
                <div class="stat-grid stat-grid--3">
                  <div class="stat-cell">
                    <span class="stat-cell__num">{{ cleanStep.output.original_length || 0 }}</span>
                    <span class="stat-cell__label">原文字数</span>
                  </div>
                  <div class="stat-cell">
                    <span class="stat-cell__num">{{ cleanStep.output.cleaned_length || 0 }}</span>
                    <span class="stat-cell__label">清洗后字数</span>
                  </div>
                  <div class="stat-cell stat-cell--accent">
                    <span class="stat-cell__num">{{ cleanStep.output.reduction_pct || 0 }}%</span>
                    <span class="stat-cell__label">压缩率</span>
                  </div>
                </div>
                <div v-if="(cleanStep.output.removed_noise || []).length" class="tag-row">
                  <el-tag
                    v-for="(item, index) in cleanStep.output.removed_noise"
                    :key="index"
                    size="small"
                    effect="dark"
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
              <el-tag effect="dark" :type="stepBadgeType(keywordStep?.status || 'pending')" size="small">
                {{ stepStateText(keywordStep?.status || 'pending') }}
              </el-tag>
            </div>
            <div class="mini-card__body">
              <template v-if="keywordStep?.output">
                <div class="stat-grid stat-grid--3">
                  <div class="stat-cell">
                    <span class="stat-cell__num">{{ (keywordStep.output.keywords || []).length || 0 }}</span>
                    <span class="stat-cell__label">关键词</span>
                  </div>
                  <div class="stat-cell">
                    <span class="stat-cell__num stat-cell__num--sm">{{ formatProviderLabel(keywordStep.provider) || 'NLP' }}</span>
                    <span class="stat-cell__label">来源</span>
                  </div>
                  <div class="stat-cell">
                    <span class="stat-cell__num stat-cell__num--sm">{{ formatMs(keywordStep.latencyMs || 0) }}</span>
                    <span class="stat-cell__label">耗时</span>
                  </div>
                </div>
                <div class="tag-row">
                  <el-tag
                    v-for="(kw, index) in (keywordStep.output.keywords || [])"
                    :key="index"
                    :type="index === 0 ? 'danger' : 'info'"
                    effect="dark"
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
            <el-tag effect="dark" :type="stepBadgeType(elementStep?.status || 'pending')" size="small">
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
            <el-tag effect="dark" :type="stepBadgeType(summaryStep?.status || 'pending')" size="small" class="step-tag">
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
              <el-tag effect="dark" :type="stepBadgeType(topicStep?.status || 'pending')" size="small">
                {{ stepStateText(topicStep?.status || 'pending') }}
              </el-tag>
            </div>
            <div class="mini-card__body">
              <template v-if="topicStep?.output">
                <div class="stat-grid stat-grid--2">
                  <div class="stat-cell">
                    <span class="stat-cell__num stat-cell__num--sm">{{ topicStep.output.primary_topic || '未知' }}</span>
                    <span class="stat-cell__label">主话题</span>
                  </div>
                  <div class="stat-cell">
                    <span class="stat-cell__num">{{ ((topicStep.output.confidence || 0) * 100).toFixed(0) }}%</span>
                    <span class="stat-cell__label">置信度</span>
                  </div>
                </div>
                <div v-if="(topicStep.output.secondary_topics || []).length" class="topic-secondary">
                  <div class="topic-chip-row">
                    <span v-for="(item, index) in (topicStep.output.secondary_topics || [])" :key="index" class="topic-chip">{{ item }}</span>
                  </div>
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
              <el-tag effect="dark" :type="stepBadgeType(timelineStep?.status || 'pending')" size="small">
                {{ stepStateText(timelineStep?.status || 'pending') }}
              </el-tag>
            </div>
            <div class="mini-card__body">
              <template v-if="timelineStep?.output">
                <div class="stat-grid stat-grid--3">
                  <div class="stat-cell">
                    <span class="stat-cell__num stat-cell__num--sm">{{ timelineStep.output.is_timely ? '符合时效' : '需更新' }}</span>
                    <span class="stat-cell__label">时效判断</span>
                  </div>
                  <div class="stat-cell">
                    <span class="stat-cell__num stat-cell__num--sm">{{ timelineStep.output.time_sensitivity || '中' }}</span>
                    <span class="stat-cell__label">敏感度</span>
                  </div>
                  <div class="stat-cell">
                    <span class="stat-cell__num stat-cell__num--sm">{{ timelineStep.output.recommended_position || '一般新闻' }}</span>
                    <span class="stat-cell__label">推荐位置</span>
                  </div>
                </div>
                <p v-if="timelineStep.output.reason" class="mini-copy">{{ timelineStep.output.reason }}</p>
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
            <el-tag effect="dark" :type="stepBadgeType(consistencyStep?.status || 'pending')" size="small">
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
            <el-tag effect="dark" :type="stepBadgeType(suggestionStep?.status || 'pending')" size="small">
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
                    effect="dark"
                    class="soft-tag"
                  >
                    {{ displayEditType(item.type) }}
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
/* ═══════════════════════════════════════════════════════════
   Shared tokens
   ═══════════════════════════════════════════════════════════ */
.agent-workbench {
  display: flex;
  flex-direction: column;
  gap: 14px;
}
/* ── Unified body font: 14px, matching the textarea ────── */
.mini-card__body,
.wide-card__body,
.hero-card__body {
  font-size: 14px;
  line-height: 1.75;
  color: var(--color-text-primary);
}

/* ═══════════════════════════════════════════════════════════
   Toolbar
   ═══════════════════════════════════════════════════════════ */
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
.agent-toolbar__left { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; flex-shrink: 0; }
.agent-toolbar__right { flex: 1; min-width: 320px; display: flex; flex-direction: column; gap: 8px; align-items: flex-end; }
.status-row { display: flex; align-items: center; gap: 10px; justify-content: flex-end; flex-wrap: wrap; }
.status-pill { border-radius: 999px; border-color: var(--color-primary-light); }
.status-text { font-size: 13px; color: var(--color-text-secondary); font-variant-numeric: tabular-nums; }
.progress-line { width: min(520px, 100%); }
.progress-line__track { height: 5px; border-radius: 999px; overflow: hidden; background: var(--color-primary-soft); }
.progress-line__fill { height: 100%; border-radius: 999px; background: linear-gradient(90deg, #d92d20 0%, #ea4d3d 100%); }

.main-btn {
  min-width: 168px; height: 40px; font-size: 15px; font-weight: 600;
  border: none; border-radius: 10px;
  background: linear-gradient(135deg, #d92d20 0%, #ea4d3d 100%);
}
.main-btn:not(:disabled):hover { background: linear-gradient(135deg, #ea4d3d 0%, #b42318 100%) !important; }
.ghost-btn { border-radius: 10px; border-color: var(--color-primary-light); color: var(--color-primary); height: 40px; }

.agent-empty { padding: 22px 18px; text-align: center; background: var(--color-bg-card); border: 1px dashed var(--color-primary-light); border-radius: 16px; }
.agent-empty__title { margin: 0 0 8px; font-size: 18px; font-weight: 700; color: var(--color-text-primary); }
.agent-empty__desc { margin: 0 auto; max-width: 700px; font-size: 14px; line-height: 1.7; color: var(--color-text-secondary); }
.agent-empty__hint { margin: 10px 0 0; font-size: 13px; color: var(--color-text-muted); }

.result-tabs { display: flex; gap: 10px; }
.result-tabs__tab {
  position: relative; padding: 10px 16px; border-radius: 999px;
  border: 1px solid var(--color-primary-light); background: var(--color-bg-card);
  color: var(--color-text-secondary); font-size: 14px; font-weight: 600; cursor: pointer;
}
.result-tabs__tab.is-active { color: var(--color-primary); background: var(--color-primary-soft); border-color: var(--color-primary-light); }
.result-tabs__dot { display: inline-block; width: 8px; height: 8px; margin-left: 8px; border-radius: 999px; background: #d92d20; }
.result-page { display: flex; flex-direction: column; gap: 14px; }

/* ═══════════════════════════════════════════════════════════
   Card shells
   ═══════════════════════════════════════════════════════════ */
.mini-card, .wide-card {
  background: var(--color-bg-card);
  border: 1px solid var(--color-primary-light);
  border-radius: 14px;
  overflow: hidden;
  box-shadow: 0 4px 16px rgba(217, 45, 32, 0.04);
}
/* Step 4: full red border highlight — replaces old left-red-line */
.hero-card {
  background: var(--color-bg-card);
  border: 2px solid rgba(217, 45, 32, 0.45);
  border-radius: 14px;
  overflow: hidden;
  box-shadow: 0 6px 24px rgba(217, 45, 32, 0.1);
}

.hero-card__head, .mini-card__head, .wide-card__head {
  display: flex; align-items: flex-start; justify-content: space-between;
  gap: 12px; padding: 14px 16px 0;
}
.hero-card__title, .mini-card__title, .wide-card__title {
  margin: 0; font-size: 17px; line-height: 1.35; font-weight: 800; color: var(--color-text-primary);
}
.hero-card__body, .mini-card__body, .wide-card__body { padding: 12px 16px 16px; }
.step-tag { border-radius: 999px; }

/* ═══════════════════════════════════════════════════════════
   Step 1 — three-column stats (replaces metric-line pills)
   ═══════════════════════════════════════════════════════════ */
/* ── Shared stat card grid ── */
.stat-grid { display: grid; gap: 8px; margin-bottom: 10px; }
.stat-grid--3 { grid-template-columns: repeat(3, minmax(0, 1fr)); }
.stat-grid--2 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
.stat-cell { text-align: center; padding: 10px 6px; border-radius: 12px; background: var(--color-bg-hover); border: 1px solid var(--color-border); }
.stat-cell__num { display: block; font-size: 22px; font-weight: 800; color: var(--color-text-primary); line-height: 1.25; font-variant-numeric: tabular-nums; word-break: break-word; }
.stat-cell__label { display: block; margin-top: 3px; font-size: 13px; color: var(--color-text-secondary); }
.stat-cell--accent { background: var(--color-primary-soft); border-color: var(--color-primary-light); }
.stat-cell--accent .stat-cell__num { color: var(--color-primary); }
.stat-cell__num--sm { font-size: 18px; }

.metric-line { display: flex; flex-wrap: wrap; gap: 8px; }
.tag-row { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 10px; }
.soft-tag { border-radius: 999px; font-size: 13px !important; }
.mini-copy { margin: 10px 0 0; font-size: 14px; line-height: 1.8; color: var(--color-text-secondary); }
.mini-copy--inline { margin-top: 0; }

/* ═══════════════════════════════════════════════════════════
   Step 2 — compact metric boxes, larger tags
   ═══════════════════════════════════════════════════════════ */

/* ═══════════════════════════════════════════════════════════
   Step 3 — elements table
   ═══════════════════════════════════════════════════════════ */
.elements-table { display: flex; flex-direction: column; gap: 8px; }
.element-row { display: grid; grid-template-columns: 92px minmax(0, 1fr) 92px minmax(0, 1fr); gap: 8px 12px; padding: 8px 0; border-bottom: 1px solid var(--color-border); }
.element-row:last-child { border-bottom: none; }
.element-label { font-size: 13px; font-weight: 700; color: var(--color-primary); }
.element-value { font-size: 14px; line-height: 1.7; color: var(--color-text-primary); word-break: break-word; }

/* ═══════════════════════════════════════════════════════════
   Step 4 — title & summary (core result, red-bordered)
   ═══════════════════════════════════════════════════════════ */
.hero-section { padding: 12px 14px; border-radius: 14px; background: var(--color-bg-card); border: 1px solid var(--color-border); }
.hero-section--accent { background: var(--color-bg-card); border-color: var(--color-primary-light); }
.hero-section__label { margin-bottom: 8px; font-size: 15px; font-weight: 700; color: var(--color-primary); }
.title-stack { display: flex; flex-direction: column; gap: 6px; }
.title-item { display: flex; align-items: flex-start; gap: 10px; margin: 0; padding: 10px 12px; border-radius: 12px; background: var(--color-bg-card); border: 1px solid var(--color-primary-light); }
.title-index { flex-shrink: 0; width: 22px; height: 22px; border-radius: 999px; background: #d92d20; color: #fff; display: inline-flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 700; }
.title-text { flex: 1; font-size: 14px; line-height: 1.75; color: var(--color-text-primary); }
.summary-grid, .compact-grid { display: grid; gap: 14px; }
.summary-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); margin-top: 10px; }
.compact-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
/* Short / Long summary with 2em indent */
.summary-text { margin: 0; font-size: 14px; line-height: 1.85; color: var(--color-text-primary); white-space: pre-wrap; word-break: break-word; text-indent: 2em; }

.empty-inline { padding: 12px 14px; border-radius: 14px; background: var(--color-primary-soft); border: 1px dashed var(--color-primary-light); color: var(--color-text-muted); font-size: 14px; text-align: center; }

/* ═══════════════════════════════════════════════════════════
   Step 5 — topic match (plain, no red accent)
   ═══════════════════════════════════════════════════════════ */
.topic-secondary { margin-top: 2px; }
.topic-chip-row { display: flex; flex-wrap: wrap; gap: 6px; }
.topic-chip { max-width: 100%; padding: 5px 10px; border-radius: 999px; background: var(--color-bg-hover); border: 1px solid var(--color-border); color: var(--color-text-primary); font-size: 13px; line-height: 1.5; word-break: break-word; }

/* ═══════════════════════════════════════════════════════════
   Step 8 — edit suggestions
   ═══════════════════════════════════════════════════════════ */
.suggestion-list { margin: 0; padding: 0; display: flex; flex-direction: column; gap: 8px; list-style: none; }
.suggestion-item { display: flex; align-items: flex-start; gap: 8px; flex-wrap: wrap; padding: 10px 12px; border-radius: 12px; background: var(--color-bg-hover); border: 1px solid var(--color-border); color: var(--color-text-primary); font-size: 14px; line-height: 1.7; }
.publish-row { display: flex; margin-top: 10px; }
.summary-banner { margin-top: 2px; }

/* ═══════════════════════════════════════════════════════════
   Responsive
   ═══════════════════════════════════════════════════════════ */
@media (max-width: 1120px) {
  .summary-grid, .compact-grid { grid-template-columns: 1fr; }
  .element-row { grid-template-columns: 88px minmax(0, 1fr); }
}
@media (max-width: 720px) {
  .stat-grid--3, .stat-grid--2 { grid-template-columns: 1fr; }
}
@media (max-width: 900px) {
  .agent-toolbar { flex-direction: column; align-items: stretch; }
  .agent-toolbar__right { align-items: stretch; min-width: 0; }
  .status-row { justify-content: flex-start; }
  .progress-line { width: 100%; }
  .result-tabs { overflow-x: auto; padding-bottom: 2px; }
  .hero-card__head, .mini-card__head, .wide-card__head { padding: 12px 12px 0; }
  .hero-card__body, .mini-card__body, .wide-card__body { padding: 12px; }
  .element-row { grid-template-columns: 1fr; }
}
</style>
