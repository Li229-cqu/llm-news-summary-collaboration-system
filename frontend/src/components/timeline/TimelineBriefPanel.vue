<template>
  <section class="timeline-brief-panel">
    <!-- ========== 生成中状态 ========== -->
    <div v-if="isGenerating" class="timeline-brief-panel__generating">
      <div class="generating-spinner">
        <span class="generating-dot generating-dot--1"></span>
        <span class="generating-dot generating-dot--2"></span>
        <span class="generating-dot generating-dot--3"></span>
      </div>
      <p class="generating-title">AI 正在梳理事件脉络</p>
      <p class="generating-desc">正在分析新闻数据，构建时间线...</p>
      <div class="generating-progress">
        <span class="generating-progress-bar" :style="{ width: progressPercentage + '%' }"></span>
      </div>
      <p class="generating-count">已等待 {{ pollCount }} 秒</p>
      <el-button size="small" @click="handleCancelGenerate">取消</el-button>
    </div>

    <!-- ========== 加载中 ========== -->
    <template v-else-if="loading">
      <div class="timeline-brief-panel__skeleton">
        <div class="skeleton-header"></div>
        <div class="skeleton-line skeleton-line--1"></div>
        <div class="skeleton-line skeleton-line--2"></div>
        <div class="skeleton-line skeleton-line--3"></div>
        <div class="skeleton-pills">
          <span class="skeleton-pill"></span>
          <span class="skeleton-pill"></span>
          <span class="skeleton-pill"></span>
        </div>
      </div>
    </template>

    <!-- ========== 错误 ========== -->
    <template v-else-if="errorMessage">
      <div class="timeline-brief-panel__error">
        <div class="error-icon">⚠️</div>
        <p class="error-text">{{ errorMessage }}</p>
        <el-button size="small" type="primary" @click="handleRetry">重试</el-button>
        <el-button size="small" @click="emit('close')">关闭</el-button>
      </div>
    </template>

    <!-- ========== 空 / 无数据 ========== -->
    <template v-else-if="!timelineData || !timelineData.timeline.length">
      <div class="timeline-brief-panel__empty">
        <div class="empty-icon">📋</div>
        <p class="empty-text">暂无事件脉络数据</p>
        <el-button size="small" @click="emit('close')">关闭</el-button>
      </div>
    </template>

    <!-- ========== 正常展示 ========== -->
    <template v-else>
      <!-- 面板头部：红色顶线 + 标题行 + 收起 -->
      <div class="timeline-brief-panel__header">
        <div class="panel-header-top">
          <span class="panel-header-accent" aria-hidden="true"></span>
          <div class="panel-header-info">
            <span class="panel-header-label">事件脉络速览</span>
            <h2 class="panel-header-title">{{ displayTopicName }}</h2>
          </div>
          <button class="panel-close-btn" :title="props.closeText" @click="emit('close')">
            <span>{{ props.closeText }}</span>
            <span class="panel-close-arrow">↑</span>
          </button>
        </div>
        <p class="panel-header-desc">AI 聚合同一话题下的多篇新闻，提炼关键进展</p>
      </div>

      <!-- 统计胶囊 -->
      <div class="timeline-brief-panel__stats">
        <div class="stats-item">
          <span class="stats-value">{{ timelineData.timeline.length }}</span>
          <span class="stats-label">关键节点</span>
        </div>
        <div class="stats-item">
          <span class="stats-value">{{ sourceNewsList.length }}</span>
          <span class="stats-label">篇来源新闻</span>
        </div>
        <div class="stats-item">
          <span class="stats-value">{{ sourceLabel }}</span>
          <span class="stats-label">数据来源</span>
        </div>
        <div v-if="updateTimeText" class="stats-item">
          <span class="stats-value stats-value--small">{{ updateTimeText }}</span>
          <span class="stats-label">更新时间</span>
        </div>
      </div>

      <!-- 整体概述 -->
      <div v-if="timelineData.overview" class="timeline-brief-panel__overview">
        <p>{{ timelineData.overview }}</p>
      </div>

      <!-- 中轴线 + 左右交错节点卡片 -->
      <div class="timeline-brief-panel__nodes">
        <h3 class="nodes-title">事件脉络</h3>
        <div class="timeline-rail">
          <div
            v-for="(node, index) in timelineData.timeline"
            :key="node.event_id"
            class="timeline-node"
            :class="[
              index % 2 === 0 ? 'timeline-node--left' : 'timeline-node--right',
              { 'timeline-node--latest': index === timelineData.timeline.length - 1 }
            ]"
          >
            <!-- 节点卡片（CSS grid-column 由父级 --left / --right 控制左右放置） -->
            <div
              class="timeline-node__card"
              :class="{ 'timeline-node__card--key': (node.importance ?? 3) >= 4 }"
            >
              <div class="timeline-node__card-header">
                <span class="timeline-node__type-tag">{{ typeLabel(node.event_type) }}</span>
                <span v-if="node.source_name" class="timeline-node__source-name">{{ node.source_name }}</span>
              </div>
              <h4 class="timeline-node__card-title">{{ node.event_title }}</h4>
              <p class="timeline-node__card-summary">{{ node.event_summary }}</p>
              <div v-if="node.keywords?.length" class="timeline-node__card-keywords">
                <span
                  v-for="(kw, kIdx) in node.keywords.slice(0, 3)"
                  :key="kIdx"
                  class="timeline-node__keyword"
                >#{{ kw }}</span>
              </div>
              <div class="timeline-node__card-footer">
                <span v-if="node.importance" class="timeline-node__importance">
                  重要度 {{ '★'.repeat(Math.min(node.importance, 5)) }}
                </span>
                <button
                  class="timeline-node__source-toggle"
                  :class="{ 'timeline-node__source-toggle--active': expandedNodeId === node.event_id }"
                  @click.stop="toggleNodeSource(node.event_id)"
                >
                  <span>{{ expandedNodeId === node.event_id ? '收起来源摘要' : '查看来源摘要' }}</span>
                  <span class="source-toggle-arrow" :class="{ 'source-toggle-arrow--up': expandedNodeId === node.event_id }">▼</span>
                </button>
              </div>

              <!-- 来源新闻摘要展开区 -->
              <div v-if="expandedNodeId === node.event_id" class="timeline-node__source-detail">
                <div class="source-detail__header">
                  <span class="source-detail__label">来源新闻</span>
                  <span class="source-detail__meta">
                    {{ getNodeSourceNews(node)?.source || node.source_name }} · {{ formatSourceTime(node) }}
                  </span>
                </div>
                <h5 class="source-detail__title">{{ getNodeSourceNews(node)?.title || node.source_title }}</h5>
                <p class="source-detail__summary">{{ getSourceSummary(node) }}</p>
              </div>
            </div>

            <!-- 中心列：日期 + 圆点 + 最新徽章 -->
            <div class="timeline-node__center">
              <span class="timeline-node__date">{{ formatNodeDate(node.event_time) }}</span>
              <span class="timeline-node__dot" :class="dotClass(node.importance)"></span>
              <span v-if="index === timelineData.timeline.length - 1" class="timeline-node__latest-badge">最新</span>
            </div>
          </div>
        </div>
      </div>
    </template>
  </section>
</template>

<script setup lang="ts">
import { ref, computed, watch, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  generateTimeline,
  getTimeline,
  getTimelineTopicNews,
  type TimelineNewsItem,
  type TimelineResponse,
} from '@/api/timeline'

const props = withDefaults(
  defineProps<{
    topicId: number | null
    topicName?: string
    closeText?: string
  }>(),
  {
    topicName: '',
    closeText: '收起',
  },
)

const emit = defineEmits<{
  (event: 'close'): void
}>()

// ── 事件类型中文映射 ──
const EVENT_TYPE_LABELS: Record<string, string> = {
  policy: '政策发布',
  reaction: '各方回应',
  breakthrough: '关键进展',
  outcome: '后续结果',
  background: '背景信息',
  other: '事件节点',
}

function typeLabel(eventType?: string): string {
  return EVENT_TYPE_LABELS[eventType || ''] || '事件节点'
}

/** 格式化节点时间为短日期展示（"2026-06-23 11:30" → "06-23"） */
function formatNodeDate(eventTime: string): string {
  if (!eventTime) return ''
  const datePart = eventTime.split(' ')[0]
  const parts = datePart.split('-')
  if (parts.length >= 3) {
    return `${parts[1]}-${parts[2]}`
  }
  return datePart
}

/** 根据重要程度返回中轴圆点尺寸 class */
function dotClass(importance?: number): string {
  const imp = importance ?? 3
  if (imp >= 5) return 'timeline-node__dot--major'
  if (imp >= 4) return 'timeline-node__dot--key'
  return 'timeline-node__dot--normal'
}

// ── 来源新闻匹配与展开逻辑 ──

/** 文本截断 */
function truncateText(text: string, maxLen: number): string {
  if (!text) return ''
  if (text.length <= maxLen) return text
  return text.slice(0, maxLen) + '...'
}

/** 根据 source_news_id 匹配来源新闻列表 */
function getNodeSourceNews(node: { source_news_id: number }): TimelineNewsItem | undefined {
  return sourceNewsList.value.find((news) => news.id === node.source_news_id)
}

/** 获取来源新闻摘要（优先级：news.summary → news.content 截断 → node 自身兜底） */
function getSourceSummary(node: {
  event_summary: string
  source_news_id: number
}): string {
  const news = getNodeSourceNews(node)
  const text = news?.summary || news?.content || node.event_summary || ''
  const trimmed = text.trim()
  if (!trimmed) return '暂无来源摘要，已根据事件节点生成概述。'
  return truncateText(trimmed, 150)
}

/** 格式化来源新闻发布时间 */
function formatSourceTime(node: { source_news_id: number; event_time: string }): string {
  const news = getNodeSourceNews(node)
  const time = news?.publish_time || node.event_time || ''
  if (!time) return ''
  // "2026-06-23 11:30:00" → "2026-06-23 11:30"
  return time.slice(0, 16)
}

/** 展开/收起来源摘要（同一节点再点即收起，切换节点自动关闭前一个） */
function toggleNodeSource(eventId: number): void {
  expandedNodeId.value = expandedNodeId.value === eventId ? null : eventId
}

// ── 状态 ──
const loading = ref(false)
const isGenerating = ref(false)
const pollCount = ref(0)
const errorMessage = ref('')
const timelineData = ref<TimelineResponse | null>(null)
const sourceNewsList = ref<TimelineNewsItem[]>([])

// 来源摘要展开状态（只允许同时展开一个节点）
const expandedNodeId = ref<number | null>(null)

let pollTimer: ReturnType<typeof setInterval> | null = null
let timeoutTimer: ReturnType<typeof setTimeout> | null = null

const POLL_INTERVAL = 2000
const TIMEOUT_SECONDS = 60

// ── 计算属性 ──
const displayTopicName = computed(() => {
  return props.topicName || timelineData.value?.topic_name || '事件脉络'
})

const sourceLabel = computed(() => {
  const src = timelineData.value?.source
  if (src === 'ai-service') return 'AI 生成'
  if (src === 'cache') return '缓存数据'
  if (src === 'mock') return '示例数据'
  return '未知'
})

const updateTimeText = computed(() => {
  const t = timelineData.value?.updated_at || timelineData.value?.generated_at
  if (!t) return ''
  // 提取日期部分
  return t.slice(0, 10)
})

const progressPercentage = computed(() => {
  return Math.min(Math.round((pollCount.value / TIMEOUT_SECONDS) * 100), 95)
})

// ── 轮询控制 ──
function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
  if (timeoutTimer) {
    clearTimeout(timeoutTimer)
    timeoutTimer = null
  }
}

function resetState() {
  loading.value = false
  isGenerating.value = false
  pollCount.value = 0
  errorMessage.value = ''
  timelineData.value = null
  sourceNewsList.value = []
  expandedNodeId.value = null
  stopPolling()
}

// ── 生成状态检查 ──
async function checkGenerationStatus() {
  try {
    const result = await getTimeline(props.topicId!)
    if (result.generate_status !== 'generating') {
      stopPolling()
      isGenerating.value = false
      loading.value = false

      if (result.timeline?.length) {
        timelineData.value = {
          ...result,
          topic_id: Number(props.topicId),
          topic_name: result.topic_name || props.topicName || '事件脉络',
        }
      } else {
        errorMessage.value = '事件脉络生成失败，请重试'
      }
    }
  } catch {
    // 轮询静默失败
  }
}

function startPolling() {
  stopPolling()

  pollTimer = setInterval(() => {
    pollCount.value += POLL_INTERVAL / 1000
    void checkGenerationStatus()
  }, POLL_INTERVAL)

  timeoutTimer = setTimeout(() => {
    stopPolling()
    isGenerating.value = false
    loading.value = false
    errorMessage.value = '事件脉络生成超时，请稍后重试'
    ElMessage.error('事件脉络生成超时')
  }, TIMEOUT_SECONDS * 1000)
}

// ── 数据加载 ──
async function loadTimelineData() {
  if (props.topicId === null || props.topicId === undefined) {
    errorMessage.value = '请选择话题后查看事件脉络'
    timelineData.value = null
    sourceNewsList.value = []
    return
  }

  loading.value = true
  errorMessage.value = ''
  isGenerating.value = false
  pollCount.value = 0
  stopPolling()

  try {
    const [topicNewsResult, initialTimelineResult] = await Promise.all([
      getTimelineTopicNews(props.topicId).catch(() => null),
      getTimeline(props.topicId).catch(() => null),
    ])

    sourceNewsList.value = topicNewsResult?.news_items ?? []

    if (initialTimelineResult?.generate_status === 'generating') {
      isGenerating.value = true
      loading.value = false
      startPolling()
      return
    }

    if (initialTimelineResult?.timeline?.length) {
      timelineData.value = {
        ...initialTimelineResult,
        topic_id: Number(props.topicId),
        topic_name:
          initialTimelineResult.topic_name || props.topicName || topicNewsResult?.topic_name || '事件脉络',
      }
      loading.value = false
      return
    }

    // 无缓存 → 触发生成
    try {
      const generateResult = await generateTimeline(props.topicId)
      if (generateResult.generate_status === 'generating') {
        isGenerating.value = true
        loading.value = false
        startPolling()
        return
      }
      if (generateResult.timeline?.length) {
        timelineData.value = {
          ...generateResult,
          topic_id: Number(props.topicId),
          topic_name:
            generateResult.topic_name || props.topicName || topicNewsResult?.topic_name || '事件脉络',
        }
      } else {
        throw new Error('生成结果为空')
      }
    } catch {
      throw new Error('事件脉络生成失败，请稍后重试')
    }
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '事件脉络加载失败，请稍后重试'
    timelineData.value = null
    sourceNewsList.value = []
  } finally {
    if (!isGenerating.value) {
      loading.value = false
    }
  }
}

function handleCancelGenerate() {
  stopPolling()
  isGenerating.value = false
  loading.value = false
  errorMessage.value = '已取消事件脉络生成'
}

function handleRetry() {
  void loadTimelineData()
}

// ── 监听 topicId ──
watch(
  () => props.topicId,
  (newId) => {
    if (newId !== null && newId !== undefined) {
      resetState()
      void loadTimelineData()
    }
  },
  { immediate: true },
)

onUnmounted(() => {
  stopPolling()
})
</script>

<style scoped>
/* ========================================
   面板容器
   ======================================== */
.timeline-brief-panel {
  position: relative;
  min-height: 520px;
  margin-bottom: 20px;
  padding: 24px 28px;
  border: 1px solid var(--color-border);
  border-top: 3px solid var(--color-primary);
  border-radius: 18px;
  background: var(--color-bg-card);
  box-shadow: 0 4px 20px rgba(217, 45, 32, 0.05);
}

/* ========================================
   生成中
   ======================================== */
.timeline-brief-panel__generating {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  min-height: 380px;
  padding: 32px 16px;
  text-align: center;
}

.generating-spinner {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
}

.generating-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--color-primary);
  animation: dot-bounce 1.2s infinite ease-in-out;
}

.generating-dot--1 { animation-delay: 0s; }
.generating-dot--2 { animation-delay: 0.2s; }
.generating-dot--3 { animation-delay: 0.4s; }

@keyframes dot-bounce {
  0%, 80%, 100% { opacity: 0.3; transform: scale(0.8); }
  40% { opacity: 1; transform: scale(1.2); }
}

.generating-title {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  color: var(--color-text-primary);
}

.generating-desc {
  margin: 0;
  font-size: 13px;
  color: var(--color-text-secondary);
}

.generating-count {
  margin: 0;
  font-size: 12px;
  color: var(--color-text-secondary);
}

.generating-progress {
  width: 100%;
  max-width: 280px;
  height: 4px;
  border-radius: 2px;
  background: color-mix(in srgb, var(--color-primary) 15%, transparent);
  overflow: hidden;
}

.generating-progress-bar {
  display: block;
  height: 100%;
  border-radius: 2px;
  background: var(--color-primary);
  transition: width 1.5s ease;
}

/* ========================================
   骨架屏
   ======================================== */
.timeline-brief-panel__skeleton {
  display: grid;
  gap: 12px;
  min-height: 360px;
  align-content: center;
}

.skeleton-header {
  width: 40%;
  height: 22px;
  border-radius: 6px;
  background: var(--el-fill-color);
}

.skeleton-line {
  height: 14px;
  border-radius: 6px;
  background: var(--el-fill-color);
}

.skeleton-line--1 { width: 90%; }
.skeleton-line--2 { width: 75%; }
.skeleton-line--3 { width: 60%; }

.skeleton-pills {
  display: flex;
  gap: 10px;
  margin-top: 4px;
}

.skeleton-pill {
  width: 70px;
  height: 28px;
  border-radius: 14px;
  background: var(--el-fill-color);
}

/* ========================================
   错误 / 空态
   ======================================== */
.timeline-brief-panel__error,
.timeline-brief-panel__empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  min-height: 380px;
  padding: 24px 16px;
  text-align: center;
}

.error-icon,
.empty-icon {
  font-size: 36px;
}

.error-text,
.empty-text {
  margin: 0;
  font-size: 14px;
  color: var(--color-text-secondary);
}

/* ========================================
   面板头部
   ======================================== */
.timeline-brief-panel__header {
  margin-bottom: 18px;
}

.panel-header-top {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.panel-header-accent {
  flex-shrink: 0;
  width: 4px;
  height: 36px;
  border-radius: 2px;
  background: var(--color-primary);
  margin-top: 4px;
}

.panel-header-info {
  flex: 1;
  min-width: 0;
}

.panel-header-label {
  display: block;
  margin-bottom: 2px;
  color: var(--color-primary);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.panel-header-title {
  margin: 0;
  color: var(--color-text-primary);
  font-size: 22px;
  font-weight: 800;
  line-height: 1.35;
}

.panel-header-desc {
  margin: 8px 0 0;
  padding-left: 16px;
  color: var(--color-text-secondary);
  font-size: 13px;
  line-height: 1.6;
}

/* 收起按钮 */
.panel-close-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
  padding: 6px 16px;
  border: 1px solid var(--color-border);
  border-radius: 999px;
  background: var(--color-bg);
  color: var(--color-text-secondary);
  font-size: 13px;
  cursor: pointer;
  transition:
    color 0.18s ease,
    border-color 0.18s ease,
    background 0.18s ease;
  white-space: nowrap;
}

.panel-close-btn:hover {
  color: var(--color-primary);
  border-color: var(--color-primary);
  background: color-mix(in srgb, var(--color-primary) 6%, var(--color-bg-card));
}

.panel-close-arrow {
  display: inline-block;
  transition: transform 0.22s ease;
}

.panel-close-btn:hover .panel-close-arrow {
  transform: translateY(-2px);
}

/* ========================================
   统计胶囊
   ======================================== */
.timeline-brief-panel__stats {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 16px;
}

.stats-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 3px;
  min-width: 90px;
  padding: 10px 16px;
  border: 1px solid color-mix(in srgb, var(--color-primary) 18%, var(--color-border));
  border-radius: 12px;
  background: color-mix(in srgb, var(--color-primary) 4%, var(--color-bg-card));
}

.stats-value {
  color: var(--color-primary);
  font-size: 20px;
  font-weight: 700;
  line-height: 1.2;
}

.stats-value--small {
  font-size: 13px;
}

.stats-label {
  color: var(--color-text-secondary);
  font-size: 11px;
  white-space: nowrap;
}

/* ========================================
   概述
   ======================================== */
.timeline-brief-panel__overview {
  margin-bottom: 16px;
  padding: 12px 16px;
  border-left: 3px solid color-mix(in srgb, var(--color-primary) 35%, var(--color-border));
  border-radius: 0 8px 8px 0;
  background: color-mix(in srgb, var(--color-primary) 4%, var(--color-bg));
}

.timeline-brief-panel__overview p {
  margin: 0;
  color: var(--color-text-secondary);
  font-size: 13px;
  line-height: 1.75;
}

/* ========================================
   中轴线 + 左右交错节点卡片
   ======================================== */
.timeline-brief-panel__nodes {
  border-top: 1px solid var(--color-border);
  padding-top: 20px;
}

.nodes-title {
  margin: 0 0 20px;
  color: var(--color-text-primary);
  font-size: 15px;
  font-weight: 700;
  text-align: center;
}

/* ── 中轴轨道 ── */
.timeline-rail {
  position: relative;
  padding: 8px 0 4px;
}

/* 中轴竖线 */
.timeline-rail::before {
  content: '';
  position: absolute;
  left: 50%;
  top: 8px;
  bottom: 8px;
  width: 2px;
  transform: translateX(-50%);
  background: linear-gradient(
    180deg,
    rgba(217, 45, 32, 0.06),
    rgba(217, 45, 32, 0.22) 30%,
    rgba(217, 45, 32, 0.32) 70%,
    rgba(217, 45, 32, 0.08)
  );
  z-index: 0;
}

/* ── 单行节点：三列网格 ── */
.timeline-node {
  display: grid;
  grid-template-columns: 1fr 72px 1fr;
  align-items: start;
  margin-bottom: 10px;
}

/* ── 中心列 ── */
.timeline-node__center {
  grid-column: 2;
  grid-row: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding-top: 0;
  z-index: 1;
}

.timeline-node__date {
  font-size: 11px;
  font-weight: 600;
  color: var(--color-primary);
  letter-spacing: 0.04em;
  white-space: nowrap;
}

/* ── 圆点（按重要程度分三级） ── */
.timeline-node__dot {
  display: block;
  border-radius: 50%;
  background: var(--color-primary);
  border: 2px solid var(--color-bg-card);
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--color-primary) 25%, transparent);
  flex-shrink: 0;
  z-index: 1;
}

.timeline-node__dot--normal {
  width: 10px;
  height: 10px;
}

.timeline-node__dot--key {
  width: 14px;
  height: 14px;
  box-shadow:
    0 0 0 3px color-mix(in srgb, var(--color-primary) 30%, transparent),
    0 0 8px color-mix(in srgb, var(--color-primary) 25%, transparent);
}

.timeline-node__dot--major {
  width: 18px;
  height: 18px;
  box-shadow:
    0 0 0 4px color-mix(in srgb, var(--color-primary) 35%, transparent),
    0 0 14px color-mix(in srgb, var(--color-primary) 30%, transparent);
}

/* ── 最新进展徽章 ── */
.timeline-node__latest-badge {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--color-primary) 12%, var(--color-bg-card));
  border: 1px solid var(--color-primary);
  color: var(--color-primary);
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.04em;
  white-space: nowrap;
}

/* ── 卡片左右放置 ── */
.timeline-node--left .timeline-node__card {
  grid-column: 1;
  grid-row: 1;
}

.timeline-node--right .timeline-node__card {
  grid-column: 3;
  grid-row: 1;
}

/* ========================================
   节点卡片
   ======================================== */
.timeline-node__card {
  padding: 16px 18px;
  border: 1px solid var(--color-border);
  border-radius: 14px;
  background: var(--color-bg-card);
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.03);
  transition:
    transform 0.2s ease,
    border-color 0.2s ease,
    box-shadow 0.2s ease;
}

.timeline-node__card:hover {
  transform: translateY(-1px);
  border-color: color-mix(in srgb, var(--color-primary) 35%, var(--color-border));
  box-shadow: 0 6px 18px rgba(217, 45, 32, 0.07);
}

/* 高重要度节点：左侧红色强调线 */
.timeline-node__card--key {
  border-left: 3px solid var(--color-primary);
}

/* 最新节点：浅红背景 */
.timeline-node--latest .timeline-node__card {
  background: color-mix(in srgb, var(--color-primary) 3%, var(--color-bg-card));
  border-color: color-mix(in srgb, var(--color-primary) 28%, var(--color-border));
}

/* ── 卡片头部 ── */
.timeline-node__card-header {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.timeline-node__type-tag {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 999px;
  border: 1px solid color-mix(in srgb, var(--color-primary) 22%, var(--color-border));
  background: color-mix(in srgb, var(--color-primary) 7%, transparent);
  color: #b91c1c;
  font-size: 11px;
  font-weight: 500;
  white-space: nowrap;
}

.timeline-node__source-name {
  color: var(--color-text-secondary);
  font-size: 11px;
}

/* ── 卡片标题 ── */
.timeline-node__card-title {
  margin: 0 0 6px;
  color: var(--color-text-primary);
  font-size: 15px;
  font-weight: 700;
  line-height: 1.45;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

/* ── 卡片摘要 ── */
.timeline-node__card-summary {
  margin: 0 0 8px;
  color: var(--color-text-secondary);
  font-size: 13px;
  line-height: 1.7;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 3;
}

/* ── 关键词 ── */
.timeline-node__card-keywords {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 8px;
}

.timeline-node__keyword {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--color-primary) 6%, transparent);
  border: 1px solid color-mix(in srgb, var(--color-primary) 20%, transparent);
  color: #b91c1c;
  font-size: 11px;
  font-weight: 500;
  white-space: nowrap;
  line-height: 1.6;
}

/* ── 卡片底部 ── */
.timeline-node__card-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding-top: 8px;
  border-top: 1px solid var(--color-border);
}

.timeline-node__importance {
  color: #9d8b6c;
  font-size: 11px;
  letter-spacing: 0.03em;
}

/* ========================================
   来源摘要展开按钮
   ======================================== */
.timeline-node__source-toggle {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 12px;
  border: 1px solid color-mix(in srgb, var(--color-primary) 22%, var(--color-border));
  border-radius: 999px;
  background: transparent;
  color: var(--color-primary);
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition:
    background 0.18s ease,
    border-color 0.18s ease,
    color 0.18s ease;
}

.timeline-node__source-toggle:hover {
  background: color-mix(in srgb, var(--color-primary) 8%, transparent);
  border-color: var(--color-primary);
}

.timeline-node__source-toggle--active {
  background: color-mix(in srgb, var(--color-primary) 10%, transparent);
  border-color: var(--color-primary);
}

.source-toggle-arrow {
  display: inline-block;
  font-size: 10px;
  transition: transform 0.25s ease;
}

.source-toggle-arrow--up {
  transform: rotate(180deg);
}

/* ========================================
   来源新闻摘要展开区
   ======================================== */
.timeline-node__source-detail {
  margin-top: 10px;
  padding: 12px 14px;
  border-left: 3px solid var(--color-primary);
  border-radius: 0 10px 10px 0;
  background: color-mix(in srgb, var(--color-primary) 4%, var(--color-bg));
  animation: source-fade-in 0.22s ease;
}

@keyframes source-fade-in {
  from { opacity: 0; transform: translateY(-4px); }
  to { opacity: 1; transform: translateY(0); }
}

.source-detail__header {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 8px;
  margin-bottom: 6px;
}

.source-detail__label {
  display: inline-block;
  padding: 1px 8px;
  border-radius: 999px;
  border: 1px solid color-mix(in srgb, var(--color-primary) 20%, var(--color-border));
  background: color-mix(in srgb, var(--color-primary) 8%, transparent);
  color: #b91c1c;
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.03em;
  text-transform: uppercase;
  white-space: nowrap;
}

.source-detail__meta {
  color: var(--color-text-secondary);
  font-size: 11px;
}

.source-detail__title {
  margin: 0 0 6px;
  color: var(--color-text-primary);
  font-size: 13px;
  font-weight: 600;
  line-height: 1.5;
}

.source-detail__summary {
  margin: 0;
  color: var(--color-text-secondary);
  font-size: 12px;
  line-height: 1.75;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 4;
}

/* ========================================
   暗色模式
   ======================================== */
:root.dark .timeline-brief-panel {
  background: #1f2933;
  border-color: #3b2020;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
}

:root.dark .generating-title,
:root.dark .panel-header-title,
:root.dark .nodes-title,
:root.dark .timeline-node__card-title {
  color: #e5e7eb;
}

:root.dark .generating-desc,
:root.dark .generating-count,
:root.dark .panel-header-desc,
:root.dark .timeline-node__card-summary,
:root.dark .timeline-node__source-name,
:root.dark .error-text,
:root.dark .empty-text {
  color: #9ca3af;
}

:root.dark .stats-item {
  background: rgba(248, 113, 113, 0.06);
  border-color: rgba(248, 113, 113, 0.18);
}

:root.dark .stats-label {
  color: #aeb8c4;
}

:root.dark .timeline-brief-panel__overview {
  background: rgba(248, 113, 113, 0.04);
}

:root.dark .timeline-brief-panel__overview p {
  color: #aeb8c4;
}

:root.dark .timeline-node__type-tag {
  border-color: rgba(248, 113, 113, 0.22);
  background: rgba(248, 113, 113, 0.1);
  color: #fca5a5;
}

:root.dark .panel-close-btn {
  background: #263038;
  border-color: #334150;
  color: #aeb8c4;
}

:root.dark .panel-close-btn:hover {
  color: #f87171;
  border-color: #f87171;
  background: rgba(248, 113, 113, 0.1);
}

:root.dark .skeleton-header,
:root.dark .skeleton-line,
:root.dark .skeleton-pill {
  background: rgba(255, 255, 255, 0.06);
}

/* 暗色中轴线 */
:root.dark .timeline-rail::before {
  background: linear-gradient(
    180deg,
    rgba(248, 113, 113, 0.04),
    rgba(248, 113, 113, 0.16) 30%,
    rgba(248, 113, 113, 0.22) 70%,
    rgba(248, 113, 113, 0.06)
  );
}

:root.dark .timeline-node__date {
  color: #d97979;
}

/* 暗色圆点 */
:root.dark .timeline-node__dot {
  border-color: #1f2933;
}

/* 暗色卡片 */
:root.dark .timeline-node__card {
  background: #263038;
  border-color: #334150;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.15);
}

:root.dark .timeline-node__card:hover {
  border-color: rgba(248, 113, 113, 0.3);
  box-shadow: 0 6px 18px rgba(0, 0, 0, 0.25);
}

:root.dark .timeline-node__card--key {
  border-left-color: #f87171;
}

:root.dark .timeline-node--latest .timeline-node__card {
  background: rgba(248, 113, 113, 0.06);
  border-color: rgba(248, 113, 113, 0.25);
}

:root.dark .timeline-node__keyword {
  background: rgba(248, 113, 113, 0.1);
  border-color: rgba(248, 113, 113, 0.22);
  color: #fca5a5;
}

:root.dark .timeline-node__importance {
  color: #b8a88a;
}

:root.dark .timeline-node__card-footer {
  border-top-color: #334150;
}

:root.dark .timeline-node__latest-badge {
  background: rgba(248, 113, 113, 0.1);
  border-color: rgba(248, 113, 113, 0.35);
  color: #d97979;
}

/* 暗色来源摘要展开 */
:root.dark .timeline-node__source-toggle {
  border-color: rgba(248, 113, 113, 0.25);
  color: #f87171;
}

:root.dark .timeline-node__source-toggle:hover {
  background: rgba(248, 113, 113, 0.1);
  border-color: #f87171;
}

:root.dark .timeline-node__source-toggle--active {
  background: rgba(248, 113, 113, 0.12);
}

:root.dark .timeline-node__source-detail {
  background: rgba(248, 113, 113, 0.05);
}

:root.dark .source-detail__label {
  border-color: rgba(248, 113, 113, 0.22);
  background: rgba(248, 113, 113, 0.12);
  color: #fca5a5;
}

:root.dark .source-detail__meta {
  color: #9ca3af;
}

:root.dark .source-detail__title {
  color: #e5e7eb;
}

:root.dark .source-detail__summary {
  color: #aeb8c4;
}

/* ========================================
   响应式
   ======================================== */
@media (max-width: 768px) {
  .timeline-brief-panel {
    padding: 16px;
    border-radius: 14px;
  }

  .panel-header-top {
    flex-wrap: wrap;
  }

  .panel-header-title {
    font-size: 18px;
  }

  .panel-close-btn {
    margin-top: 4px;
  }

  .stats-item {
    min-width: 70px;
    padding: 8px 12px;
  }

  .stats-value {
    font-size: 17px;
  }

  /* ── 中轴移到左侧，全部卡片在右侧单列 ── */
  .timeline-rail::before {
    left: 18px;
  }

  .timeline-node {
    grid-template-columns: 42px minmax(0, 1fr);
    margin-bottom: 16px;
  }

  .timeline-node__center {
    grid-column: 1;
  }

  /* 所有卡片强制放在第二列 */
  .timeline-node--left .timeline-node__card,
  .timeline-node--right .timeline-node__card {
    grid-column: 2;
    grid-row: 1;
  }

  .timeline-node__card {
    padding: 14px;
  }

  .timeline-node__card-title {
    font-size: 14px;
  }

  .timeline-node__card-summary {
    -webkit-line-clamp: 3;
  }

  .timeline-node__date {
    font-size: 10px;
  }

  .timeline-node__source-toggle {
    font-size: 11px;
    padding: 3px 10px;
  }

  .source-detail__summary {
    -webkit-line-clamp: 5;
  }
}
</style>
