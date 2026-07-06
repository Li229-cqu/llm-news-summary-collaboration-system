<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh, View, TrendCharts, UserFilled, Files, Message, DataBoard, Warning } from '@element-plus/icons-vue'
import * as echarts from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { BarChart, LineChart, PieChart } from 'echarts/charts'
import { GridComponent, LegendComponent, TitleComponent, TooltipComponent } from 'echarts/components'
import {
  type AdminAnalyticsAiRiskResponse,
  type AdminAnalyticsOverview,
  type AdminAnalyticsReviewSummaryResponse,
  type AdminAnalyticsTrendsResponse,
  type AdminContentOverviewItem,
  getAdminAnalyticsAiRisk,
  getAdminAnalyticsContentOverview,
  getAdminAnalyticsOverview,
  getAdminAnalyticsReviewSummary,
  getAdminAnalyticsTrends,
} from '@/api/admin'
import { useThemeStore } from '@/stores/theme'
import {
  createCategoryAxis,
  createChartLegend,
  createChartTooltip,
  createValueAxis,
  getChartThemeColors,
} from '@/utils/chartTheme'

echarts.use([CanvasRenderer, LineChart, BarChart, PieChart, TitleComponent, TooltipComponent, LegendComponent, GridComponent])

const emit = defineEmits<{ navigate: [tab: string] }>()
const themeStore = useThemeStore()

// ── Time range ──
type RangeKey = '7d' | '30d' | '90d' | 'custom'
const rangeKey = ref<RangeKey>('7d')
const customRange = ref<[string, string]>(['', ''])
const rangeLoading = ref(false)

const rangeStart = computed(() => {
  if (rangeKey.value === 'custom') return customRange.value[0] || undefined
  const days: Record<RangeKey, number> = { '7d': 7, '30d': 30, '90d': 90, custom: 7 }
  const d = new Date()
  d.setDate(d.getDate() - days[rangeKey.value])
  return d.toISOString().slice(0, 10) + ' 00:00:00'
})
const rangeEnd = computed(() => {
  if (rangeKey.value === 'custom') return customRange.value[1] || undefined
  return undefined
})

// ── Chinese label maps ──
function riskLevelCn(r: string) {
  const map: Record<string, string> = { low: '高质量', medium: '中质量', high: '低质量', unknown: '未知' }
  return map[r] || r || '未知'
}
function statusCnLabel(s: string | number) {
  const map: Record<string, string> = { Normal: '正常', Pending: '待审核', Folded: '折叠', Deleted: '已删除', Disabled: '已禁用' }
  return map[String(s)] || String(s) || '未知'
}
function contentTypeCn(t: string) {
  const map: Record<string, string> = { news: '新闻', post: '帖子', comment: '评论', timeline: '时间线', topic: '话题' }
  return map[t] || t
}

const colorMap: Record<string, string> = { low: '#67c23a', medium: '#e6a23c', high: '#f56c6c', unknown: '#909399' }

// ── Loading states ──
const overviewLoading = ref(false)
const trendsLoading = ref(false)
const riskLoading = ref(false)
const reviewLoading = ref(false)
const overviewTabLoading = ref(false)

// ── Data ──
const overview = ref<AdminAnalyticsOverview | null>(null)
const trends = ref<AdminAnalyticsTrendsResponse | null>(null)
const aiRisk = ref<AdminAnalyticsAiRiskResponse | null>(null)
const reviewSummary = ref<AdminAnalyticsReviewSummaryResponse | null>(null)
const contentItems = ref<AdminContentOverviewItem[]>([])
const contentTotal = ref(0)
const contentPage = ref(1)
const contentPageSize = ref(10)

// content-overview filters
const overviewType = ref('')
const overviewStatus = ref<number | null>(null)
const overviewKeyword = ref('')

// ── Charts ──
const contentChartRef = ref<HTMLDivElement>()
const aiChartRef = ref<HTMLDivElement>()
const riskChartRef = ref<HTMLDivElement>()
let contentChart: echarts.ECharts | null = null
let aiChart: echarts.ECharts | null = null
let riskChart: echarts.ECharts | null = null

// ── Computed: Review summary stats ──
const processedActions = computed(() => {
  if (!reviewSummary.value) return []
  const p = reviewSummary.value.processed
  const total = p.approve + p.reject + p.fold + p.delete + p.restore
  if (total === 0) return []
  const items = [
    { key: 'approve', label: '通过', count: p.approve, color: '#67c23a' },
    { key: 'reject', label: '驳回', count: p.reject, color: '#f56c6c' },
    { key: 'fold', label: '折叠', count: p.fold, color: '#909399' },
    { key: 'delete', label: '删除', count: p.delete, color: '#e6a23c' },
    { key: 'restore', label: '恢复', count: p.restore, color: '#409eff' },
  ]
  return items.map(i => ({ ...i, pct: total > 0 ? (i.count / total) * 100 : 0 })).filter(i => i.count > 0)
})

// ── Computed: AI risk stats ──
const riskStats = computed(() => {
  if (!aiRisk.value?.items?.length) return null
  const items = aiRisk.value.items
  const total = items.reduce((s, i) => s + i.count, 0)
  if (total === 0) return { total: 0, levels: [] }
  return {
    total,
    levels: items.map(i => ({
      level: i.risk_level,
      label: riskLevelCn(i.risk_level),
      count: i.count,
      pct: Math.round((i.count / total) * 100),
      color: colorMap[i.risk_level] || '#909399',
    })),
  }
})

const lowQualityHigh = computed(() => {
  const high = riskStats.value?.levels.find(item => item.level === 'high')
  return Boolean(high && high.pct >= 30)
})

// ── Chart renderers ──
function initCharts() {
  if (contentChartRef.value && !contentChart) contentChart = echarts.init(contentChartRef.value)
  if (aiChartRef.value && !aiChart) aiChart = echarts.init(aiChartRef.value)
  if (riskChartRef.value && !riskChart) riskChart = echarts.init(riskChartRef.value)
}

function disposeCharts() {
  contentChart?.dispose()
  aiChart?.dispose()
  riskChart?.dispose()
}

function renderContentTrend() {
  if (!contentChart || !trends.value) return
  const data = trends.value.content_trend
  if (!data.length) { contentChart.clear(); return }
  const theme = getChartThemeColors()
  contentChart.setOption({
    backgroundColor: theme.background,
    tooltip: createChartTooltip('axis'),
    legend: createChartLegend({ data: ['新闻', '帖子', '评论'], top: 0 }),
    grid: { left: 40, right: 16, top: 36, bottom: 24 },
    xAxis: createCategoryAxis(data.map(d => d.date.slice(5)), { axisLabel: { rotate: 30, fontSize: 10 } }),
    yAxis: createValueAxis({ minInterval: 1 }),
    series: [
      { name: '新闻', type: 'line', data: data.map(d => d.news_count), smooth: true, symbol: 'none' },
      { name: '帖子', type: 'line', data: data.map(d => d.post_count), smooth: true, symbol: 'none' },
      { name: '评论', type: 'line', data: data.map(d => d.comment_count), smooth: true, symbol: 'none' },
    ],
  }, true)
}

function renderAiTrend() {
  if (!aiChart || !trends.value) return
  const data = trends.value.ai_trend
  if (!data.length) { aiChart.clear(); return }
  const theme = getChartThemeColors()
  aiChart.setOption({
    backgroundColor: theme.background,
    tooltip: createChartTooltip('axis'),
    legend: createChartLegend({ data: ['AI 调用', '低质量'], top: 0 }),
    grid: { left: 40, right: 16, top: 36, bottom: 24 },
    xAxis: createCategoryAxis(data.map(d => d.date.slice(5)), { axisLabel: { rotate: 30, fontSize: 10 } }),
    yAxis: createValueAxis({ minInterval: 1 }),
    series: [
      { name: 'AI 调用', type: 'bar', data: data.map(d => d.ai_count), barMaxWidth: 12 },
      { name: '低质量', type: 'line', data: data.map(d => d.high_risk_count), smooth: true, symbol: 'none' },
    ],
  }, true)
}

function renderRiskChart() {
  if (!riskChart || !aiRisk.value) return
  const items = aiRisk.value.items
  if (!items.length) { riskChart.clear(); return }
  const theme = getChartThemeColors()
  riskChart.setOption({
    backgroundColor: theme.background,
    tooltip: createChartTooltip('item', {
      formatter: (p: { name: string; value: number; percent: number }) =>
        p.name + ': ' + p.value + ' (' + p.percent + '%)',
    }),
    legend: { show: false },
    series: [{
      type: 'pie',
      radius: ['45%', '75%'],
      center: ['50%', '50%'],
      label: { show: false, color: theme.axisText },
      emphasis: { label: { show: true, color: theme.tooltipText } },
      data: items.map(i => ({
        name: riskLevelCn(i.risk_level),
        value: i.count,
        itemStyle: { color: colorMap[i.risk_level] || '#909399' },
      })),
    }],
  }, true)
}

// ── Loaders ──
async function loadOverview() {
  overviewLoading.value = true
  try {
    overview.value = await getAdminAnalyticsOverview({ start_time: rangeStart.value, end_time: rangeEnd.value })
  } catch (e) {
    ElMessage.error('加载概览数据失败，请检查后端服务是否启动')
  } finally { overviewLoading.value = false }
}

async function loadTrends() {
  trendsLoading.value = true
  try {
    trends.value = await getAdminAnalyticsTrends({ start_time: rangeStart.value, end_time: rangeEnd.value })
  } catch (e) {
    ElMessage.error('加载趋势数据失败，请检查后端服务是否启动')
  } finally { trendsLoading.value = false }
}

async function loadRisk() {
  riskLoading.value = true
  try {
    aiRisk.value = await getAdminAnalyticsAiRisk({ start_time: rangeStart.value, end_time: rangeEnd.value })
  } catch (e) {
    ElMessage.error('加载 AI 生成质量数据失败，请检查后端服务是否启动')
  } finally { riskLoading.value = false }
}

async function loadReview() {
  reviewLoading.value = true
  try {
    reviewSummary.value = await getAdminAnalyticsReviewSummary({ start_time: rangeStart.value, end_time: rangeEnd.value })
  } catch (e) {
    ElMessage.error('加载审核概况失败，请检查后端服务是否启动')
  } finally { reviewLoading.value = false }
}

async function loadContentOverview(reset = false) {
  if (reset) contentPage.value = 1
  overviewTabLoading.value = true
  try {
    const res = await getAdminAnalyticsContentOverview({
      type: overviewType.value || undefined,
      status: overviewStatus.value,
      keyword: overviewKeyword.value || undefined,
      start_time: rangeStart.value,
      end_time: rangeEnd.value,
      page: contentPage.value,
      page_size: contentPageSize.value,
    })
    contentItems.value = res.items
    contentTotal.value = res.total
  } catch (e) {
    ElMessage.error('加载内容总览失败，请检查后端服务是否启动')
  } finally { overviewTabLoading.value = false }
}

async function loadAll() {
  rangeLoading.value = true
  await Promise.all([loadOverview(), loadTrends(), loadRisk(), loadReview(), loadContentOverview(true)])
  rangeLoading.value = false
}

function handleRangeChange() {
  loadAll().then(() => {
    nextTick(() => { initCharts(); renderContentTrend(); renderAiTrend(); renderRiskChart() })
  })
}

function jumpTo(tab: string) {
  emit('navigate', tab)
}

// ── Summary cards ──
const summaryCards = computed(() => {
  const o = overview.value
  const totalPosts = Number(o?.total_posts ?? 0)
  const totalComments = Number(o?.total_comments ?? 0)
  const iconBg = (light: string, dark: string) => themeStore.theme === 'dark' ? dark : light
  return [
    { key: 'users', title: '用户总数', value: o?.total_users ?? '-', hint: '活跃用户数量：' + (o?.active_users ?? '-'), icon: UserFilled, bg: iconBg('#fef2f2', 'rgba(248, 113, 113, 0.14)'), color: themeStore.theme === 'dark' ? '#fca5a5' : '#dc2626' },
    { key: 'content', title: '内容总量', value: o?.total_news ?? '-', hint: '新闻内容', icon: Files, bg: iconBg('#f0fdf4', 'rgba(34, 197, 94, 0.14)'), color: '#16a34a' },
    { key: 'community', title: '社区互动', value: o ? totalPosts + totalComments : '-', hint: `帖子 ${o?.total_posts ?? '-'} / 评论 ${o?.total_comments ?? '-'}`, icon: Message, bg: iconBg('#fefce8', 'rgba(234, 179, 8, 0.14)'), color: '#ca8a04' },
    { key: 'ai', title: 'AI 生成', value: o?.ai_generate_count ?? '-', hint: '生成记录 / 调用次数', icon: TrendCharts, bg: iconBg('#f5f3ff', 'rgba(139, 92, 246, 0.16)'), color: '#8b5cf6' },
    { key: 'timeline', title: 'Timeline', value: o?.timeline_count ?? '-', hint: '已生成事件线', icon: DataBoard, bg: iconBg('#ecfeff', 'rgba(8, 145, 178, 0.16)'), color: '#0891b2' },
    { key: 'pending', title: '待处理', value: o?.pending_count ?? '-', hint: '新闻 / 帖子 / 评论待审', icon: Warning, bg: iconBg('#fff7ed', 'rgba(234, 88, 12, 0.16)'), color: '#ea580c' },
  ]
})

// ── Lifecycle ──
onMounted(async () => {
  await loadAll()
  nextTick(() => {
    initCharts()
    renderContentTrend()
    renderAiTrend()
    renderRiskChart()
  })
})

watch([trends, aiRisk], () => {
  nextTick(() => {
    initCharts()
    renderContentTrend()
    renderAiTrend()
    renderRiskChart()
  })
})

watch(() => themeStore.theme, () => {
  nextTick(() => {
    renderContentTrend()
    renderAiTrend()
    renderRiskChart()
  })
})

onBeforeUnmount(() => disposeCharts())

function onResize() {
  contentChart?.resize()
  aiChart?.resize()
  riskChart?.resize()
}
onMounted(() => window.addEventListener('resize', onResize))
onBeforeUnmount(() => window.removeEventListener('resize', onResize))
</script>

<template>
  <section class="analytics-dashboard">
    <!-- Header -->
    <el-card class="analytics-header" shadow="never">
      <div>
        <h2>数据看板</h2>
        <p>汇总系统运营、内容审核、AI 生成质量与服务状态，辅助管理员快速判断当前平台运行情况。</p>
      </div>
      <div class="header-actions">
        <el-radio-group v-model="rangeKey" size="default" @change="handleRangeChange">
          <el-radio-button value="7d">近 7 天</el-radio-button>
          <el-radio-button value="30d">近 30 天</el-radio-button>
          <el-radio-button value="90d">近 90 天</el-radio-button>
          <el-radio-button value="custom">自定义</el-radio-button>
        </el-radio-group>
        <el-date-picker
          v-if="rangeKey === 'custom'"
          v-model="customRange"
          type="datetimerange"
          value-format="YYYY-MM-DD HH:mm:ss"
          start-placeholder="开始时间"
          end-placeholder="结束时间"
          @change="handleRangeChange"
        />
        <el-button :icon="Refresh" :loading="rangeLoading" @click="loadAll">刷新</el-button>
      </div>
    </el-card>

    <!-- Summary cards -->
    <div class="summary-grid" v-loading="overviewLoading">
      <el-card v-for="card in summaryCards" :key="card.key" class="summary-card" shadow="never">
        <div class="summary-card__inner">
          <div class="summary-card__icon" :style="{ background: card.bg, color: card.color }">
            <component :is="card.icon" :size="22" />
          </div>
          <div>
            <div class="summary-card__title">{{ card.title }}</div>
            <div class="summary-card__value">{{ card.value }}</div>
            <div class="summary-card__hint">{{ card.hint }}</div>
          </div>
        </div>
      </el-card>
    </div>

    <!-- Trend charts row -->
    <div class="charts-row">
      <el-card class="chart-card" shadow="never">
        <div class="card-header">
          <div>
            <h3>内容增长趋势</h3>
            <p class="card-subtitle">按时间统计新闻、帖子与评论新增量</p>
          </div>
        </div>
        <div v-if="trends?.content_trend?.length" ref="contentChartRef" class="chart-box" />
        <el-empty v-else description="暂无内容趋势数据" />
      </el-card>
      <el-card class="chart-card" shadow="never">
        <div class="card-header">
          <div>
            <h3>AI 使用趋势</h3>
            <p class="card-subtitle">按时间统计 AI 调用与生成质量变化</p>
          </div>
        </div>
        <div v-if="trends?.ai_trend?.length" ref="aiChartRef" class="chart-box" />
        <el-empty v-else description="暂无 AI 趋势数据" />
      </el-card>
    </div>

    <!-- Row 1: Review Summary + AI Risk -->
    <div class="content-row">
      <!-- Review Summary -->
      <el-card class="content-card" shadow="never" v-loading="reviewLoading">
        <div class="card-header">
          <div>
            <h3>待审核与今日处理</h3>
            <p class="card-subtitle">待审核内容与今日处理结果</p>
          </div>
        </div>
        <template v-if="reviewSummary">
          <div class="review-body">
            <!-- Pending section -->
            <div>
              <div class="review-section-title">待处理</div>
              <div class="stat-grid-4">
                <div class="stat-block">
                  <span class="stat-label">新闻待审</span>
                  <span class="stat-value stat-value--warning">{{ reviewSummary.pending.news }}</span>
                </div>
                <div class="stat-block">
                  <span class="stat-label">帖子待审</span>
                  <span class="stat-value stat-value--warning">{{ reviewSummary.pending.posts }}</span>
                </div>
                <div class="stat-block">
                  <span class="stat-label">评论待审</span>
                  <span class="stat-value stat-value--warning">{{ reviewSummary.pending.comments }}</span>
                </div>
                <div class="stat-block">
                  <span class="stat-label">合计待审</span>
                  <span class="stat-value stat-value--danger">{{ reviewSummary.pending.total }}</span>
                </div>
              </div>
            </div>
            <!-- Processed section -->
            <div>
              <div class="review-section-title">已处理 / 今日内容处理</div>
              <div class="stat-grid-5">
                <div class="stat-block stat-block--sm">
                  <span class="stat-label">通过</span>
                  <span class="stat-value stat-value--success">{{ reviewSummary.processed.approve }}</span>
                </div>
                <div class="stat-block stat-block--sm">
                  <span class="stat-label">驳回</span>
                  <span class="stat-value stat-value--danger">{{ reviewSummary.processed.reject }}</span>
                </div>
                <div class="stat-block stat-block--sm">
                  <span class="stat-label">折叠</span>
                  <span class="stat-value stat-value--info">{{ reviewSummary.processed.fold }}</span>
                </div>
                <div class="stat-block stat-block--sm">
                  <span class="stat-label">删除</span>
                  <span class="stat-value">{{ reviewSummary.processed.delete }}</span>
                </div>
                <div class="stat-block stat-block--sm">
                  <span class="stat-label">恢复</span>
                  <span class="stat-value stat-value--primary">{{ reviewSummary.processed.restore }}</span>
                </div>
              </div>
            </div>
            <!-- Footer: today processed + action distribution bar -->
            <div class="review-footer">
              <div class="review-today">
                <span>今日内容处理：</span>
                <strong>{{ reviewSummary.today_processed }}</strong>
              </div>
              <div v-if="processedActions.length > 1" class="action-bar">
                <div
                  v-for="a in processedActions"
                  :key="a.key"
                  class="action-segment"
                  :style="{ width: a.pct + '%', backgroundColor: a.color }"
                  :title="a.label + ': ' + a.count + ' (' + a.pct.toFixed(0) + '%)'"
                />
              </div>
              <div class="action-legend">
                <span v-for="a in processedActions" :key="a.key" class="action-legend-item">
                  <span class="action-dot" :style="{ backgroundColor: a.color }" />
                  {{ a.label }}{{ a.count > 0 ? ` (${a.count})` : '' }}
                </span>
                <span v-if="processedActions.length === 0" class="action-legend-item">暂无处理记录</span>
              </div>
              <el-button class="review-entry" type="primary" plain size="small" @click="jumpTo('pending')">进入待审核中心</el-button>
            </div>
          </div>
        </template>
        <el-empty v-else description="暂无审核数据" />
      </el-card>

      <!-- AI Risk Distribution -->
      <el-card class="content-card" shadow="never" v-loading="riskLoading">
        <div class="card-header">
          <div>
            <h3>AI 生成质量监控</h3>
            <p class="card-subtitle">AI 生成记录质量等级统计</p>
          </div>
        </div>
        <template v-if="riskStats && riskStats.total > 0">
          <div class="risk-body">
            <!-- Chart + Stats side by side -->
            <div class="risk-row">
              <div ref="riskChartRef" class="risk-chart" />
              <div class="risk-stats">
                <div class="risk-stat-item">
                  <span class="risk-stat-label">AI 调用总数</span>
                  <span class="risk-stat-value">{{ riskStats.total }}</span>
                </div>
                <div v-for="lvl in riskStats.levels" :key="lvl.level" class="risk-stat-item">
                  <span class="risk-stat-label">
                    <span class="risk-dot" :style="{ backgroundColor: lvl.color }" />
                    {{ lvl.label }}
                  </span>
                  <span class="risk-stat-value">{{ lvl.count }}</span>
                </div>
                <div v-if="lowQualityHigh" class="risk-high-alert">
                  <el-tag type="warning" effect="plain" size="small">低质量生成占比较高，建议检查生成规则或模型调用参数。</el-tag>
                </div>
              </div>
            </div>
            <!-- Risk ratio bar -->
            <div class="risk-bar-section">
              <div class="risk-bar">
                <div
                  v-for="lvl in riskStats.levels"
                  :key="lvl.level"
                  class="risk-bar-segment"
                  :style="{ width: lvl.pct + '%', backgroundColor: lvl.color }"
                  :title="lvl.label + ': ' + lvl.count + ' (' + lvl.pct + '%)'"
                />
              </div>
              <div class="risk-bar-legend">
                <span v-for="lvl in riskStats.levels" :key="lvl.level" class="risk-bar-legend-item">
                  <span class="risk-dot" :style="{ backgroundColor: lvl.color }" />
                  {{ lvl.label }}：{{ lvl.pct }}%
                </span>
              </div>
            </div>
          </div>
        </template>
        <el-empty v-else-if="aiRisk && aiRisk.items && aiRisk.items.length === 0" description="暂无 AI 生成质量统计数据" />
        <el-empty v-else description="暂无 AI 生成质量统计数据" />
      </el-card>
    </div>

    <!-- Content overview table -->
    <el-card class="overview-card" shadow="never">
      <div class="overview-header">
        <div>
          <h3>内容总览复核</h3>
          <p>统一查看最近内容，点击“查看”跳转到对应管理模块。</p>
        </div>
      </div>
      <div class="overview-filter">
        <el-select v-model="overviewType" placeholder="内容类型" clearable style="width: 130px" @change="loadContentOverview(true)">
          <el-option label="全部" value="" />
          <el-option label="新闻" value="news" />
          <el-option label="帖子" value="post" />
          <el-option label="评论" value="comment" />
          <el-option label="时间线" value="timeline" />
          <el-option label="话题" value="topic" />
        </el-select>
        <el-select v-model="overviewStatus" placeholder="状态" clearable style="width: 110px" @change="loadContentOverview(true)">
          <el-option label="正常" :value="1" />
          <el-option label="待审核" :value="3" />
          <el-option label="折叠" :value="2" />
          <el-option label="已删除" :value="4" />
          <el-option label="已禁用" :value="0" />
        </el-select>
        <el-input v-model="overviewKeyword" placeholder="关键词" clearable style="width: 160px" @keyup.enter="loadContentOverview(true)" />
        <el-button type="primary" @click="loadContentOverview(true)">筛选</el-button>
      </div>
      <el-table :data="contentItems" v-loading="overviewTabLoading" empty-text="暂无内容" size="small">
        <el-table-column prop="content_type" label="类型" width="80">
          <template #default="{ row }">
            <el-tag size="small" :type="row.content_type === 'news' ? 'success' : row.content_type === 'post' ? '' : row.content_type === 'comment' ? 'warning' : 'info'">
              {{ contentTypeCn(row.content_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="title" label="标题" min-width="220" show-overflow-tooltip />
        <el-table-column prop="creator_or_source" label="创建者/来源" width="140" show-overflow-tooltip />
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <el-tag size="small" :type="row.status_label === 'Normal' ? 'success' : row.status_label === 'Pending' ? 'warning' : 'info'">
              {{ statusCnLabel(row.status_label) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="risk_level" label="质量" width="70">
          <template #default="{ row }">{{ row.risk_level ? riskLevelCn(row.risk_level) : '-' }}</template>
        </el-table-column>
        <el-table-column prop="related_info" label="关联信息" width="160" show-overflow-tooltip />
        <el-table-column prop="updated_at" label="更新时间" width="150" />
        <el-table-column label="操作" width="70">
          <template #default="{ row }">
            <el-button text type="primary" size="small" :icon="View" @click="jumpTo(row.target_tab)">查看</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination
        v-model:current-page="contentPage"
        v-model:page-size="contentPageSize"
        layout="total, prev, pager, next"
        :total="contentTotal"
        @current-change="loadContentOverview()"
      />
    </el-card>
  </section>
</template>

<style scoped>
.analytics-dashboard {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.analytics-header {
  border-radius: 18px;
}
.analytics-header :deep(.el-card__body) {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
}
.analytics-header h2 { margin: 0 0 4px; }
.analytics-header p { margin: 0; color: var(--el-text-color-secondary); font-size: 13px; }
.header-actions { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }

.summary-grid {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 12px;
}
.summary-card { border-radius: 16px; }
.summary-card__inner { display: flex; gap: 12px; align-items: center; }
.summary-card__icon { width: 40px; height: 40px; border-radius: 12px; display: grid; place-items: center; flex-shrink: 0; }
.summary-card__title { font-size: 12px; color: var(--el-text-color-secondary); }
.summary-card__value { font-size: 22px; font-weight: 800; color: var(--el-text-color-primary); }
.summary-card__hint { font-size: 11px; color: var(--el-text-color-secondary); margin-top: 2px; }

.charts-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}
.chart-card {
  border-radius: 18px;
}
.chart-card h3 {
  margin: 0;
}
.chart-box { width: 100%; height: 280px; }

/* ── Content rows (2-col grids) ── */
.content-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}
.content-card {
  border-radius: 18px;
  display: flex;
  flex-direction: column;
}
.content-card :deep(.el-card__body) {
  flex: 1;
  display: flex;
  flex-direction: column;
}
.content-card .card-header {
  margin-bottom: 14px;
}
.card-header h3 {
  margin: 0;
}
.card-subtitle {
  margin: 4px 0 0;
  color: var(--el-text-color-secondary);
  font-size: 12px;
}

/* ── Review summary card ── */
.review-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 18px;
}
.review-section-title {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-bottom: 8px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.stat-grid-4 {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
}
.stat-grid-5 {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 10px;
}
.stat-block {
  background: var(--el-fill-color-extra-light);
  border-radius: 10px;
  padding: 12px;
  text-align: center;
  border: 1px solid var(--el-border-color-lighter);
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.stat-block--sm {
  padding: 10px 6px;
}
.stat-label {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}
.stat-value {
  font-size: 20px;
  font-weight: 700;
  line-height: 1.2;
}
.stat-value--warning { color: var(--el-color-warning); }
.stat-value--danger { color: var(--el-color-danger); }
.stat-value--success { color: var(--el-color-success); }
.stat-value--info { color: var(--el-color-info); }
.stat-value--primary { color: var(--el-color-primary); }

.review-footer {
  background: var(--el-fill-color-extra-light);
  border-radius: 10px;
  padding: 12px 14px;
  border: 1px solid var(--el-border-color-lighter);
  margin-top: auto;
}
.review-entry {
  margin-top: 10px;
}
.review-today {
  font-size: 13px;
  color: var(--el-text-color-secondary);
  margin-bottom: 8px;
}
.review-today strong {
  font-size: 18px;
  color: var(--el-color-primary);
  margin-left: 4px;
}
.action-bar {
  display: flex;
  height: 8px;
  border-radius: 4px;
  overflow: hidden;
  background: var(--el-fill-color);
  margin-bottom: 6px;
}
.action-segment {
  height: 100%;
  transition: width 0.3s;
}
.action-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  font-size: 11px;
  color: var(--el-text-color-secondary);
}
.action-legend-item {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}
.action-dot {
  width: 8px;
  height: 8px;
  border-radius: 2px;
  display: inline-block;
}

/* ── AI Risk card ── */
.risk-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.risk-row {
  display: flex;
  gap: 16px;
  align-items: stretch;
}
.risk-chart {
  width: 140px;
  min-height: 140px;
  flex-shrink: 0;
}
.risk-stats {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 8px;
}
.risk-stat-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 10px;
  background: var(--el-fill-color-extra-light);
  border-radius: 8px;
}
.risk-stat-label {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  display: flex;
  align-items: center;
  gap: 6px;
}
.risk-stat-value {
  font-size: 16px;
  font-weight: 700;
}
.risk-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
}
.risk-high-alert {
  margin-top: 4px;
}

.risk-bar-section {
  background: var(--el-fill-color-extra-light);
  border-radius: 10px;
  padding: 12px 14px;
  border: 1px solid var(--el-border-color-lighter);
}
.risk-bar {
  display: flex;
  height: 10px;
  border-radius: 5px;
  overflow: hidden;
  background: var(--el-fill-color);
  margin-bottom: 6px;
}
.risk-bar-segment {
  height: 100%;
  transition: width 0.3s;
}
.risk-bar-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  font-size: 11px;
  color: var(--el-text-color-secondary);
}
.risk-bar-legend-item {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

/* ── Overview card ── */
.overview-card {
  border-radius: 18px;
}
.overview-filter {
  display: flex;
  gap: 8px;
  margin-bottom: 10px;
  align-items: center;
  flex-wrap: wrap;
}
.overview-header { margin-bottom: 6px; }
.overview-header h3 { margin: 0; }
.overview-header p { margin: 4px 0 0; color: var(--el-text-color-secondary); font-size: 12px; }

.el-pagination { margin-top: 12px; justify-content: flex-end; }

@media (max-width: 1200px) {
  .summary-grid { grid-template-columns: repeat(4, minmax(0, 1fr)); }
  .stat-grid-5 { grid-template-columns: repeat(3, 1fr); }
  .risk-row { flex-direction: column; align-items: center; }
}
@media (max-width: 960px) {
  .summary-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .charts-row, .content-row { grid-template-columns: 1fr; }
  .stat-grid-4 { grid-template-columns: repeat(2, 1fr); }
  .stat-grid-5 { grid-template-columns: repeat(3, 1fr); }
}
</style>
