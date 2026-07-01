<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Clock,
  DataBoard,
  Monitor,
  Refresh,
  TrendCharts,
  UserFilled,
  Warning,
} from '@element-plus/icons-vue'
import * as echarts from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { BarChart, LineChart, PieChart } from 'echarts/charts'
import { GridComponent, LegendComponent, TitleComponent, TooltipComponent } from 'echarts/components'
import {
  getAdminAnalyticsAiRisk,
  getAdminAnalyticsReviewSummary,
  getAdminAnalyticsTopContent,
  getAdminAnalyticsTrends,
  getAdminOpsDatabase,
  getAdminOpsBackups,
  getAdminOpsStatus,
  getDashboard,
  type AdminAnalyticsAiRiskResponse,
  type AdminAnalyticsReviewSummaryResponse,
  type AdminAnalyticsTopContentResponse,
  type AdminAnalyticsTrendsResponse,
  type AdminDashboard,
  type AdminOpsDatabaseResponse,
  type AdminOpsStatusResponse,
  type AdminBackupRecordListResponse,
} from '@/api/admin'
import { useUserStore } from '@/stores/user'

echarts.use([CanvasRenderer, LineChart, BarChart, PieChart, TitleComponent, TooltipComponent, LegendComponent, GridComponent])

type TrendRange = '7d' | '30d' | '90d'
type AlertTone = 'danger' | 'warning' | 'info'

interface KpiCard {
  key: string
  title: string
  value: string | number
  hint: string
  icon: unknown
  bg: string
  color: string
}

interface CompactItem {
  key: string
  label: string
  value: string
  tone?: AlertTone
}

interface AlertCard {
  key: string
  title: string
  description: string
  tone: AlertTone
}

const userStore = useUserStore()
const loading = ref(false)
const analyticsLoading = ref(false)
const error = ref('')
const lastRefreshTime = ref('')
const activeRange = ref<TrendRange>('7d')

const dashboard = ref<AdminDashboard | null>(null)
const trends = ref<AdminAnalyticsTrendsResponse | null>(null)
const topContent = ref<AdminAnalyticsTopContentResponse | null>(null)
const aiRisk = ref<AdminAnalyticsAiRiskResponse | null>(null)
const reviewSummary = ref<AdminAnalyticsReviewSummaryResponse | null>(null)
const opsStatus = ref<AdminOpsStatusResponse | null>(null)
const backupRecords = ref<AdminBackupRecordListResponse | null>(null)
const opsDatabase = ref<AdminOpsDatabaseResponse | null>(null)

const trendChartRef = ref<HTMLDivElement | null>(null)
const topContentChartRef = ref<HTMLDivElement | null>(null)
const aiRiskChartRef = ref<HTMLDivElement | null>(null)

let trendChart: echarts.ECharts | null = null
let topContentChart: echarts.ECharts | null = null
let aiRiskChart: echarts.ECharts | null = null

const rangeOptions: Array<{ key: TrendRange; label: string }> = [
  { key: '7d', label: '近 7 天' },
  { key: '30d', label: '近 30 天' },
  { key: '90d', label: '近 90 天' },
]

const kpiCards = computed<KpiCard[]>(() => [
  {
    key: 'today_new_users',
    title: '今日新增用户',
    value: dashboard.value?.today_new_users ?? '--',
    hint: dashboard.value ? '今日注册' : '等待加载',
    icon: UserFilled,
    bg: '#fef2f2',
    color: '#dc2626',
  },
  {
    key: 'active_users_7d',
    title: '7 日活跃用户',
    value: dashboard.value?.active_users_7d ?? '--',
    hint: dashboard.value ? '按浏览记录估算' : '等待加载',
    icon: TrendCharts,
    bg: '#fee2e2',
    color: '#b91c1c',
  },
  {
    key: 'today_review_done',
    title: '今日审核完成',
    value: dashboard.value?.today_review_done ?? '--',
    hint: dashboard.value ? '已处理内容数' : '等待加载',
    icon: Warning,
    bg: '#fef7e0',
    color: '#e6a23c',
  },
  {
    key: 'pending_total',
    title: '当前待处理',
    value: dashboard.value?.pending_total ?? '--',
    hint: dashboard.value ? '待审核内容总数' : '等待加载',
    icon: Clock,
    bg: '#fef0f0',
    color: '#f56c6c',
  },
  {
    key: 'today_ai_calls',
    title: '今日 AI 调用',
    value: dashboard.value?.today_ai_calls ?? '--',
    hint: dashboard.value ? '生成调用次数' : '等待加载',
    icon: Monitor,
    bg: '#fef2f2',
    color: '#dc2626',
  },
  {
    key: 'avg_response_ms',
    title: '平均响应时延',
    value: dashboard.value?.avg_response_ms != null ? `${dashboard.value.avg_response_ms} ms` : '暂未记录',
    hint: 'AI 与审核接口平均耗时',
    icon: DataBoard,
    bg: '#f7f0ff',
    color: '#a46bff',
  },
])

const pendingItems = computed<CompactItem[]>(() => [
  {
    key: 'news',
    label: '新闻待审',
    value: String(dashboard.value?.pending_news_count ?? dashboard.value?.pending_total ?? '--'),
    tone: (dashboard.value?.pending_news_count ?? dashboard.value?.pending_total ?? 0) > 0 ? 'warning' : 'info',
  },
  {
    key: 'post',
    label: '帖子待审',
    value: String(dashboard.value?.pending_post_count ?? dashboard.value?.pending_total ?? '--'),
    tone: (dashboard.value?.pending_post_count ?? dashboard.value?.pending_total ?? 0) > 0 ? 'warning' : 'info',
  },
  {
    key: 'comment',
    label: '评论待审',
    value: String(dashboard.value?.pending_comment_count ?? '--'),
    tone: (dashboard.value?.pending_comment_count ?? 0) > 0 ? 'warning' : 'info',
  },
  {
    key: 'timeline',
    label: 'Timeline 待处理',
    value: String(dashboard.value?.timeline_pending_count ?? '--'),
    tone: (dashboard.value?.timeline_pending_count ?? 0) > 0 ? 'warning' : 'info',
  },
])

const systemItems = computed<CompactItem[]>(() => [
  {
    key: 'backend',
    label: '后端服务',
    value: opsStatus.value?.backend?.status === 'normal' ? '正常' : (opsStatus.value?.backend?.status || '未知'),
    tone: opsStatus.value?.backend?.status === 'normal' ? 'info' : 'danger',
  },
  {
    key: 'database',
    label: '数据库',
    value: opsStatus.value?.database?.status === 'normal' ? '正常' : (opsStatus.value?.database?.status || '未知'),
    tone: opsStatus.value?.database?.status === 'normal' ? 'info' : 'danger',
  },
  {
    key: 'ai',
    label: 'AI 服务',
    value: opsStatus.value?.ai_service?.status === 'normal' ? '正常' : (opsStatus.value?.ai_service?.status === 'unknown' ? '未知' : '异常'),
    tone: opsStatus.value?.ai_service?.status === 'normal' ? 'info' : (opsStatus.value?.ai_service?.status === 'unknown' ? 'info' : 'danger'),
  },
  {
    key: 'backup',
    label: '最近备份',
    value: backupRecords.value?.items?.[0]?.status === 'success'
      ? '成功'
      : (backupRecords.value?.items?.[0]?.status === 'unsupported' ? '不支持' : (backupRecords.value?.items?.[0]?.status || '暂无')),
    tone: backupRecords.value?.items?.[0]?.status === 'success' ? 'info' : 'warning',
  },
])

const insightItems = computed<CompactItem[]>(() => [
  {
    key: 'review',
    label: '今日审核完成',
    value: String(dashboard.value?.today_review_done ?? 0),
    tone: 'info',
  },
  {
    key: 'active',
    label: '7 日活跃',
    value: String(dashboard.value?.active_users_7d ?? 0),
    tone: 'info',
  },
  {
    key: 'ai-call',
    label: '今日 AI 调用',
    value: String(dashboard.value?.today_ai_calls ?? 0),
    tone: 'info',
  },
  {
    key: 'response',
    label: '平均时延',
    value: dashboard.value?.avg_response_ms != null ? `${dashboard.value.avg_response_ms} ms` : '暂无',
    tone: 'info',
  },
])

const aiMonitorItems = computed(() => {
  const aiTrend = trends.value?.ai_trend || []
  const fallbackCount = aiTrend.reduce((sum, item) => sum + (item.fallback_count || 0), 0)
  const highRiskCount = aiTrend.reduce((sum, item) => sum + (item.high_risk_count || 0), 0)
  const abnormalDays = aiTrend.filter(item => (item.fallback_count || 0) > 0).length
  return [
    { key: 'today', label: '今日 AI 调用', value: String(dashboard.value?.today_ai_calls ?? 0), hint: '今日调用次数' },
    { key: 'fallback', label: '降级调用', value: String(fallbackCount), hint: '近段时间降级总量' },
    { key: 'abnormal', label: '异常调用日', value: String(abnormalDays), hint: '出现降级的日期数' },
    { key: 'risk', label: '高风险记录', value: String(highRiskCount), hint: '近段时间高风险内容' },
    { key: 'latency', label: '响应时延', value: dashboard.value?.avg_response_ms != null ? `${dashboard.value.avg_response_ms} ms` : '未记录', hint: dashboard.value?.avg_response_ms != null ? '已接入统计' : '暂未支持记录' },
    { key: 'timeline', label: 'Timeline 失败', value: String(dashboard.value?.timeline_pending_count ?? 0), hint: '待生成或生成失败' },
  ]
})

const alerts = computed<AlertCard[]>(() => {
  const items: AlertCard[] = []
  const pendingTotal = dashboard.value?.pending_total ?? 0
  const aiTrend = trends.value?.ai_trend || []
  const fallbackTotal = aiTrend.reduce((sum, item) => sum + (item.fallback_count || 0), 0)
  const highRiskTotal = aiTrend.reduce((sum, item) => sum + (item.high_risk_count || 0), 0)
  if (pendingTotal > 0) {
    items.push({
      key: 'pending',
      title: '待审核内容堆积',
      description: `当前共有 ${pendingTotal} 条待处理内容，建议优先查看“待审核中心”。`,
      tone: 'warning',
    })
  }
  if ((dashboard.value?.timeline_pending_count ?? 0) > 0) {
    items.push({
      key: 'timeline',
      title: 'Timeline 有待处理任务',
      description: `有 ${dashboard.value?.timeline_pending_count ?? 0} 条时间线尚未生成或生成失败。`,
      tone: 'info',
    })
  }
  if (opsStatus.value?.database?.status && opsStatus.value.database.status !== 'normal') {
    items.push({
      key: 'database',
      title: '数据库状态异常',
      description: opsStatus.value.database.message || '请检查数据库连接池和连接配置。',
      tone: 'danger',
    })
  }
  if (opsStatus.value?.ai_service?.status && opsStatus.value.ai_service.status === 'unknown') {
    items.push({
      key: 'ai-unknown',
      title: 'AI 服务状态未知',
      description: opsStatus.value.ai_service.message || '当前仅作连通性提示。',
      tone: 'info',
    })
  }
  if (fallbackTotal > 0) {
    items.push({
      key: 'ai-fallback',
      title: 'AI 发生降级调用',
      description: `近段时间共 ${fallbackTotal} 次降级调用，建议检查 AI 服务稳定性。`,
      tone: 'warning',
    })
  }
  if (highRiskTotal > 0) {
    items.push({
      key: 'ai-high-risk',
      title: '高风险内容需要关注',
      description: `近段时间共 ${highRiskTotal} 条高风险记录，建议优先审核。`,
      tone: 'danger',
    })
  }
  if (backupRecords.value?.items?.[0]?.status && backupRecords.value.items[0].status !== 'success') {
    items.push({
      key: 'backup',
      title: '最近备份需要关注',
      description: backupRecords.value.items[0].message || '最新备份记录未处于成功状态。',
      tone: 'warning',
    })
  }
  return items.slice(0, 4)
})

const hasTrendData = computed(() => Boolean(trends.value?.content_trend?.length))
const hasTopContentData = computed(() => Boolean(topContent.value?.top_news?.length))
const hasAiRiskData = computed(() => Boolean(aiRisk.value?.items?.length))

function riskLevelCn(level: string) {
  const map: Record<string, string> = { low: '低风险', medium: '中风险', high: '高风险', unknown: '未知' }
  return map[level] || level || '未知'
}

function formatRangeLabel(range: TrendRange) {
  if (range === '7d') return '近 7 天'
  if (range === '30d') return '近 30 天'
  return '近 90 天'
}

function buildTimeParam(days: number) {
  const end = new Date()
  const start = new Date()
  start.setDate(start.getDate() - days)
  const fmt = (date: Date) => `${date.toISOString().slice(0, 10)} 00:00:00`
  return { start_time: fmt(start), end_time: fmt(end) }
}

async function loadSummary() {
  const [dashRes, statusRes, backupsRes, databaseRes] = await Promise.allSettled([
    getDashboard(),
    getAdminOpsStatus(),
    getAdminOpsBackups({ page: 1, page_size: 1 }),
    getAdminOpsDatabase(),
  ])
  if (dashRes.status === 'fulfilled') dashboard.value = dashRes.value
  if (statusRes.status === 'fulfilled') opsStatus.value = statusRes.value
  if (backupsRes.status === 'fulfilled') backupRecords.value = backupsRes.value
  if (databaseRes.status === 'fulfilled') opsDatabase.value = databaseRes.value
  const failures = [dashRes, statusRes, backupsRes, databaseRes].filter(item => item.status === 'rejected') as PromiseRejectedResult[]
  if (failures.length && !error.value) {
    error.value = '部分工作台数据加载失败，请检查后端服务状态。'
  }
}

async function loadAnalytics() {
  const days = activeRange.value === '30d' ? 30 : (activeRange.value === '90d' ? 90 : 7)
  const params = buildTimeParam(days)
  const [trendRes, topRes, riskRes, reviewRes] = await Promise.allSettled([
    getAdminAnalyticsTrends(params),
    getAdminAnalyticsTopContent({ ...params, limit: 8 }),
    getAdminAnalyticsAiRisk(params),
    getAdminAnalyticsReviewSummary(params),
  ])
  if (trendRes.status === 'fulfilled') trends.value = trendRes.value
  if (topRes.status === 'fulfilled') topContent.value = topRes.value
  if (riskRes.status === 'fulfilled') aiRisk.value = riskRes.value
  if (reviewRes.status === 'fulfilled') reviewSummary.value = reviewRes.value
  const failures = [trendRes, topRes, riskRes, reviewRes].filter(item => item.status === 'rejected') as PromiseRejectedResult[]
  if (failures.length && !error.value) {
    error.value = '部分工作台数据加载失败，请检查后端服务状态。'
  }
}

async function refreshWorkbench() {
  if (!userStore.isAdmin) {
    return
  }
  loading.value = true
  analyticsLoading.value = true
  error.value = ''
  try {
    await Promise.all([loadSummary(), loadAnalytics()])
    lastRefreshTime.value = new Date().toLocaleString()
    await nextTick()
    renderCharts()
  } catch (err) {
    error.value = err instanceof Error ? err.message : '工作台数据加载失败'
    ElMessage.error(error.value)
  } finally {
    loading.value = false
    analyticsLoading.value = false
  }
}

async function refreshAnalytics() {
  if (!userStore.isAdmin) {
    return
  }
  analyticsLoading.value = true
  error.value = ''
  try {
    await loadAnalytics()
    lastRefreshTime.value = new Date().toLocaleString()
    await nextTick()
    renderCharts()
  } catch (err) {
    error.value = err instanceof Error ? err.message : '趋势数据加载失败'
    ElMessage.error(error.value)
  } finally {
    analyticsLoading.value = false
  }
}

function handleRangeChange(range: TrendRange) {
  if (activeRange.value === range) {
    return
  }
  activeRange.value = range
  void refreshAnalytics()
}

function renderCharts() {
  if (trendChartRef.value) {
    trendChart ||= echarts.init(trendChartRef.value)
  }
  if (topContentChartRef.value) {
    topContentChart ||= echarts.init(topContentChartRef.value)
  }
  if (aiRiskChartRef.value) {
    aiRiskChart ||= echarts.init(aiRiskChartRef.value)
  }

  if (trendChart) {
    if (trends.value?.content_trend?.length) {
      const data = trends.value.content_trend
      trendChart.setOption({
        tooltip: { trigger: 'axis' },
        legend: { data: ['新闻', '帖子', '评论', 'AI 调用'], top: 0 },
        grid: { left: 40, right: 16, top: 38, bottom: 28 },
        xAxis: {
          type: 'category',
          data: data.map(item => item.date.slice(5)),
          axisLabel: { rotate: 30, fontSize: 10 },
        },
        yAxis: { type: 'value', minInterval: 1 },
        series: [
          { name: '新闻', type: 'line', smooth: true, symbol: 'none', data: data.map(item => item.news_count) },
          { name: '帖子', type: 'line', smooth: true, symbol: 'none', data: data.map(item => item.post_count) },
          { name: '评论', type: 'bar', barMaxWidth: 12, data: data.map(item => item.comment_count) },
          { name: 'AI 调用', type: 'line', smooth: true, symbol: 'none', data: data.map(item => item.ai_count) },
        ],
      }, true)
    } else {
      trendChart.clear()
    }
  }

  if (topContentChart) {
    if (topContent.value?.top_news?.length) {
      const items = topContent.value.top_news.slice(0, 8)
      topContentChart.setOption({
        tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
        grid: { left: 120, right: 20, top: 20, bottom: 24 },
        xAxis: { type: 'value', minInterval: 1 },
        yAxis: {
          type: 'category',
          data: items.map(item => `${item.rank}. ${item.title.slice(0, 12)}`),
          axisLabel: { width: 110, overflow: 'truncate', fontSize: 10 },
        },
        series: [
          {
            name: '浏览量',
            type: 'bar',
            barMaxWidth: 14,
            data: items.map(item => item.view_count),
          },
        ],
      }, true)
    } else {
      topContentChart.clear()
    }
  }

  if (aiRiskChart) {
    if (aiRisk.value?.items?.length) {
      aiRiskChart.setOption({
        tooltip: { trigger: 'item' },
        legend: { top: 0, left: 'center' },
        series: [
          {
            name: '风险分布',
            type: 'pie',
            radius: ['42%', '68%'],
            center: ['50%', '58%'],
            data: aiRisk.value.items.map(item => ({
              name: riskLevelCn(item.risk_level),
              value: item.count,
            })),
            label: { formatter: '{b}\n{c}' },
          },
        ],
      }, true)
    } else {
      aiRiskChart.clear()
    }
  }
}

function handleResize() {
  trendChart?.resize()
  topContentChart?.resize()
  aiRiskChart?.resize()
}

onMounted(() => {
  if (!userStore.isAdmin) {
    return
  }
  void refreshWorkbench()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  trendChart?.dispose()
  topContentChart?.dispose()
  aiRiskChart?.dispose()
})

watch([trends, topContent, aiRisk], async () => {
  await nextTick()
  renderCharts()
})
</script>

<template>
  <section class="admin-workbench">
    <el-result
      v-if="!userStore.isAdmin"
      icon="warning"
      title="当前账号无权访问工作台"
      sub-title="请使用管理员账号查看趋势导向的工作台首页。"
    />

    <template v-else>
      <el-card class="hero-card" shadow="never">
        <div class="hero-main">
          <div>
            <div class="hero-badge">管理后台 · 工作台</div>
            <h1>趋势导向工作台</h1>
            <p>围绕内容生产、审核效率、系统健康和风险变化，实时查看管理后台的运行状态。</p>
          </div>

          <div class="hero-meta">
            <el-tag type="info" effect="plain">角色：管理员</el-tag>
            <el-tag effect="plain">最近刷新：{{ lastRefreshTime || '暂无' }}</el-tag>
            <el-button type="primary" :icon="Refresh" :loading="loading || analyticsLoading" @click="refreshWorkbench">
              刷新数据
            </el-button>
          </div>
        </div>

        <div class="range-bar">
          <div class="range-label">时间范围</div>
          <div class="range-tags">
            <el-tag
              v-for="item in rangeOptions"
              :key="item.key"
              class="range-tag"
              :effect="activeRange === item.key ? 'dark' : 'plain'"
              @click="handleRangeChange(item.key)"
            >
              {{ item.label }}
            </el-tag>
          </div>
        </div>
      </el-card>

      <el-alert
        v-if="error"
        :title="error"
        type="error"
        show-icon
        :closable="false"
      />

      <el-card class="kpi-card" shadow="never" v-loading="loading">
        <div class="section-head">
          <div>
            <h2>核心指标</h2>
            <p>来自后台真实接口的实时统计。</p>
          </div>
          <el-button text :icon="Refresh" @click="refreshWorkbench">重新加载</el-button>
        </div>

        <div class="kpi-grid">
          <article v-for="item in kpiCards" :key="item.key" class="kpi-item">
            <div class="kpi-icon" :style="{ backgroundColor: item.bg, color: item.color }">
              <component :is="item.icon" :size="22" />
            </div>
            <div class="kpi-body">
              <div class="kpi-value">{{ item.value }}</div>
              <div class="kpi-title">{{ item.title }}</div>
              <div class="kpi-hint">{{ item.hint }}</div>
            </div>
          </article>
        </div>
      </el-card>

      <div class="trend-grid">
        <el-card class="panel panel--large" shadow="never" v-loading="analyticsLoading">
          <div class="section-head">
            <div>
              <h3>核心业务趋势</h3>
              <p>{{ formatRangeLabel(activeRange) }} 内的内容增量与 AI 调用变化。</p>
            </div>
            <el-tag type="info" effect="plain">趋势分析</el-tag>
          </div>

          <div v-if="hasTrendData" ref="trendChartRef" class="chart-box" />
          <el-empty v-else description="暂无趋势数据" />
        </el-card>

        <el-card class="panel panel--side" shadow="never">
          <div class="section-head">
            <div>
              <h3>运营洞察</h3>
              <p>把关键运营数据拆成可快速扫读的结论。</p>
            </div>
          </div>

          <div class="compact-list">
            <div v-for="item in insightItems" :key="item.key" class="compact-item">
              <span>{{ item.label }}</span>
              <el-tag :type="item.tone || 'info'" effect="plain">{{ item.value }}</el-tag>
            </div>
          </div>

          <el-divider />

          <div class="section-mini">
            <div class="section-mini__title">审核概览</div>
            <div class="review-grid">
              <div class="review-item">
                <strong>{{ reviewSummary?.pending?.total ?? 0 }}</strong>
                <span>待审核总量</span>
              </div>
              <div class="review-item">
                <strong>{{ reviewSummary?.processed?.total ?? 0 }}</strong>
                <span>已处理总量</span>
              </div>
              <div class="review-item">
                <strong>{{ reviewSummary?.today_processed ?? 0 }}</strong>
                <span>今日处理</span>
              </div>
            </div>
          </div>
        </el-card>
      </div>

      <div class="status-grid">
        <el-card class="panel" shadow="never">
          <div class="section-head">
            <div>
              <h3>待处理事项</h3>
              <p>优先查看当前阻塞工作。</p>
            </div>
          </div>
          <div class="compact-list">
            <div v-for="item in pendingItems" :key="item.key" class="compact-item">
              <span>{{ item.label }}</span>
              <el-tag :type="item.tone || 'info'" effect="plain">{{ item.value }}</el-tag>
            </div>
          </div>
        </el-card>

        <el-card class="panel" shadow="never">
          <div class="section-head">
            <div>
              <h3>系统状态</h3>
              <p>后台、数据库、AI 服务和备份的基础健康情况。</p>
            </div>
          </div>
          <div class="compact-list">
            <div v-for="item in systemItems" :key="item.key" class="compact-item">
              <span>{{ item.label }}</span>
              <el-tag :type="item.tone || 'info'" effect="plain">{{ item.value }}</el-tag>
            </div>
            <div class="compact-item compact-item--muted">
              <span>数据库表</span>
              <span>{{ opsDatabase?.tables?.length ?? 0 }} 张</span>
            </div>
          </div>
        </el-card>

        <el-card class="panel" shadow="never">
          <div class="section-head">
            <div>
              <h3>提醒与洞察</h3>
              <p>自动汇总可能需要关注的异常点。</p>
            </div>
          </div>
          <div v-if="alerts.length" class="alert-list">
            <el-alert
              v-for="item in alerts"
              :key="item.key"
              :type="item.tone"
              :title="item.title"
              :description="item.description"
              show-icon
              :closable="false"
              class="alert-item"
            />
          </div>
          <el-empty v-else description="暂无异常提醒" />
        </el-card>
      </div>

      <el-card class="panel ai-monitor-card" shadow="never">
        <div class="section-head">
          <div>
            <h3>AI 监控概览</h3>
            <p>聚焦调用、降级、风险和时延统计。</p>
          </div>
        </div>

        <div class="ai-monitor-grid">
          <div v-for="item in aiMonitorItems" :key="item.key" class="ai-monitor-item">
            <strong>{{ item.value }}</strong>
            <span>{{ item.label }}</span>
            <small>{{ item.hint }}</small>
          </div>
        </div>
      </el-card>

      <div class="analysis-grid">
        <el-card class="panel" shadow="never" v-loading="analyticsLoading">
          <div class="section-head">
            <div>
              <h3>内容热度分析</h3>
              <p>展示当前最受关注的新闻条目。</p>
            </div>
          </div>
          <div v-if="hasTopContentData" ref="topContentChartRef" class="chart-box chart-box--small" />
          <el-empty v-else description="暂无热点内容" />
        </el-card>

        <el-card class="panel" shadow="never" v-loading="analyticsLoading">
          <div class="section-head">
            <div>
              <h3>AI 风险分布</h3>
              <p>查看 AI 生成内容的风险等级占比。</p>
            </div>
          </div>
          <div v-if="hasAiRiskData" ref="aiRiskChartRef" class="chart-box chart-box--small" />
          <el-empty v-else description="暂无风险分布数据" />
        </el-card>
      </div>
    </template>
  </section>
</template>

<style scoped>
.admin-workbench {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.hero-card,
.kpi-card,
.panel {
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 18px;
  background: linear-gradient(180deg, var(--el-bg-color) 0%, var(--el-fill-color-extra-light) 100%);
}

.hero-card :deep(.el-card__body),
.kpi-card :deep(.el-card__body),
.panel :deep(.el-card__body) {
  padding: 20px;
}

.hero-main {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  align-items: flex-start;
}

.hero-badge {
  display: inline-flex;
  align-items: center;
  padding: 6px 12px;
  border-radius: 999px;
  background: rgba(64, 158, 255, 0.12);
  color: var(--el-color-primary);
  font-size: 12px;
  font-weight: 600;
  margin-bottom: 12px;
}

.hero-main h1,
.section-head h2,
.section-head h3,
.section-mini__title {
  margin: 0;
  color: var(--el-text-color-primary);
}

.hero-main h1 {
  font-size: 28px;
  line-height: 1.2;
}

.hero-main p,
.section-head p {
  margin: 8px 0 0;
  color: var(--el-text-color-secondary);
  line-height: 1.6;
}

.hero-meta {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.range-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-top: 18px;
  padding-top: 18px;
  border-top: 1px solid var(--el-border-color-lighter);
}

.range-label {
  font-size: 13px;
  color: var(--el-text-color-secondary);
  white-space: nowrap;
}

.range-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.range-tag {
  cursor: pointer;
  user-select: none;
}

.section-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 16px;
}

.kpi-grid {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 14px;
}

.kpi-item {
  display: flex;
  gap: 12px;
  padding: 16px;
  border-radius: 16px;
  background: var(--el-bg-color-overlay);
  border: 1px solid var(--el-border-color-lighter);
}

.kpi-icon {
  width: 44px;
  height: 44px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex: 0 0 auto;
}

.kpi-body {
  min-width: 0;
}

.kpi-value {
  font-size: 24px;
  font-weight: 700;
  line-height: 1.2;
  color: var(--el-text-color-primary);
}

.kpi-title {
  margin-top: 4px;
  font-size: 13px;
  font-weight: 600;
}

.kpi-hint {
  margin-top: 4px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.trend-grid,
.status-grid,
.analysis-grid {
  display: grid;
  gap: 16px;
}

.trend-grid {
  grid-template-columns: minmax(0, 2fr) minmax(300px, 1fr);
}

.status-grid {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.analysis-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.ai-monitor-card :deep(.el-card__body) {
  padding-bottom: 18px;
}

.ai-monitor-grid {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 12px;
}

.ai-monitor-item {
  padding: 14px;
  border-radius: 14px;
  background: var(--el-fill-color-extra-light);
  border: 1px solid var(--el-border-color-lighter);
  min-height: 104px;
}

.ai-monitor-item strong {
  display: block;
  font-size: 22px;
  line-height: 1.1;
  color: var(--el-text-color-primary);
}

.ai-monitor-item span {
  display: block;
  margin-top: 8px;
  font-weight: 600;
}

.ai-monitor-item small {
  display: block;
  margin-top: 6px;
  color: var(--el-text-color-secondary);
  line-height: 1.5;
}

.panel {
  min-width: 0;
}

.panel--large .chart-box {
  min-height: 360px;
}

.panel--side {
  display: flex;
  flex-direction: column;
}

.compact-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.compact-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  border-radius: 14px;
  background: var(--el-fill-color-extra-light);
  border: 1px solid var(--el-border-color-lighter);
  color: var(--el-text-color-primary);
}

.compact-item--muted {
  color: var(--el-text-color-secondary);
}

.section-mini {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.review-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.review-item {
  padding: 14px;
  border-radius: 14px;
  background: var(--el-fill-color-extra-light);
  border: 1px solid var(--el-border-color-lighter);
}

.review-item strong {
  display: block;
  font-size: 24px;
  line-height: 1.1;
}

.review-item span {
  display: block;
  margin-top: 4px;
  color: var(--el-text-color-secondary);
  font-size: 12px;
}

.alert-list {
  display: grid;
  gap: 10px;
}

.alert-item :deep(.el-alert__content) {
  line-height: 1.55;
}

.chart-box {
  width: 100%;
  min-height: 320px;
}

.chart-box--small {
  min-height: 300px;
}

@media (max-width: 1400px) {
  .kpi-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .ai-monitor-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .trend-grid,
  .analysis-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 960px) {
  .hero-main,
  .range-bar,
  .section-head {
    flex-direction: column;
    align-items: stretch;
  }

  .kpi-grid,
  .status-grid,
  .review-grid,
  .ai-monitor-grid {
    grid-template-columns: 1fr;
  }
}
</style>
