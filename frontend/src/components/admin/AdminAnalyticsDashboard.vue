<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh, View, TrendCharts, UserFilled, Files, Message, Document, DataBoard, Warning } from '@element-plus/icons-vue'
import * as echarts from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { BarChart, LineChart, PieChart } from 'echarts/charts'
import { GridComponent, LegendComponent, TitleComponent, TooltipComponent } from 'echarts/components'
import {
  type AdminAnalyticsAiRiskResponse,
  type AdminAnalyticsOverview,
  type AdminAnalyticsReviewSummaryResponse,
  type AdminAnalyticsTopContentResponse,
  type AdminAnalyticsTrendsResponse,
  type AdminContentOverviewItem,
  getAdminAnalyticsAiRisk,
  getAdminAnalyticsContentOverview,
  getAdminAnalyticsOverview,
  getAdminAnalyticsReviewSummary,
  getAdminAnalyticsTopContent,
  getAdminAnalyticsTrends,
} from '@/api/admin'

echarts.use([CanvasRenderer, LineChart, BarChart, PieChart, TitleComponent, TooltipComponent, LegendComponent, GridComponent])

const emit = defineEmits<{ navigate: [tab: string] }>()

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
  const map: Record<string, string> = { low: '低风险', medium: '中风险', high: '高风险', unknown: '未知' }
  return map[r] || r || '未知'
}
function statusCnLabel(s: string | number) {
  const map: Record<string, string> = { 'Normal': '正常', 'Pending': '待审核', 'Folded': '折叠', 'Deleted': '已删除', 'Disabled': '已禁用' }
  return map[String(s)] || String(s) || '未知'
}
function contentTypeCn(t: string) {
  const map: Record<string, string> = { news: '新闻', post: '帖子', comment: '评论', timeline: '时间线', topic: '话题' }
  return map[t] || t
}
function resultCnSimple(r: string) {
  const map: Record<string, string> = { success: '成功', failed: '失败', unsupported: '不支持' }
  return map[r] || r
}

// ── Loading states ──
const overviewLoading = ref(false)
const trendsLoading = ref(false)
const topLoading = ref(false)
const riskLoading = ref(false)
const reviewLoading = ref(false)
const overviewTabLoading = ref(false)

// ── Data ──
const overview = ref<AdminAnalyticsOverview | null>(null)
const trends = ref<AdminAnalyticsTrendsResponse | null>(null)
const topContent = ref<AdminAnalyticsTopContentResponse | null>(null)
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
  contentChart.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['新闻', '帖子', '评论'], top: 0 },
    grid: { left: 40, right: 16, top: 36, bottom: 24 },
    xAxis: { type: 'category', data: data.map((d) => d.date.slice(5)), axisLabel: { rotate: 30, fontSize: 10 } },
    yAxis: { type: 'value', minInterval: 1 },
    series: [
      { name: '新闻', type: 'line', data: data.map((d) => d.news_count), smooth: true, symbol: 'none' },
      { name: '帖子', type: 'line', data: data.map((d) => d.post_count), smooth: true, symbol: 'none' },
      { name: '评论', type: 'line', data: data.map((d) => d.comment_count), smooth: true, symbol: 'none' },
    ],
  }, true)
}

function renderAiTrend() {
  if (!aiChart || !trends.value) return
  const data = trends.value.ai_trend
  if (!data.length) { aiChart.clear(); return }
  aiChart.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['AI 调用', '降级', '高风险'], top: 0 },
    grid: { left: 40, right: 16, top: 36, bottom: 24 },
    xAxis: { type: 'category', data: data.map((d) => d.date.slice(5)), axisLabel: { rotate: 30, fontSize: 10 } },
    yAxis: { type: 'value', minInterval: 1 },
    series: [
      { name: 'AI 调用', type: 'bar', data: data.map((d) => d.ai_count), barMaxWidth: 12 },
      { name: '降级', type: 'line', data: data.map((d) => d.fallback_count), smooth: true, symbol: 'none' },
      { name: '高风险', type: 'line', data: data.map((d) => d.high_risk_count), smooth: true, symbol: 'none' },
    ],
  }, true)
}

function renderRiskChart() {
  if (!riskChart || !aiRisk.value) return
  const items = aiRisk.value.items
  if (!items.length) { riskChart.clear(); return }
  const colors: Record<string, string> = { low: '#16a34a', medium: '#d97706', high: '#dc2626', unknown: '#9ca3af' }
  riskChart.setOption({
    tooltip: {
      trigger: 'item',
      formatter: (p: { name: string; value: number; percent: number }) =>
        riskLevelCn(p.name) + ': ' + p.value + ' (' + p.percent + '%)',
    },
    legend: { orient: 'vertical', right: 8, top: 'center' },
    series: [{
      type: 'pie',
      radius: ['45%', '75%'],
      center: ['40%', '50%'],
      label: { show: false },
      emphasis: { label: { show: true } },
      data: items.map((i) => ({
        name: riskLevelCn(i.risk_level),
        value: i.count,
        itemStyle: { color: colors[i.risk_level] || '#9ca3af' },
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

async function loadTop() {
  topLoading.value = true
  try {
    topContent.value = await getAdminAnalyticsTopContent({ start_time: rangeStart.value, end_time: rangeEnd.value, limit: 10 })
  } catch (e) {
    ElMessage.error('加载热门内容失败，请检查后端服务是否启动')
  } finally { topLoading.value = false }
}

async function loadRisk() {
  riskLoading.value = true
  try {
    aiRisk.value = await getAdminAnalyticsAiRisk({ start_time: rangeStart.value, end_time: rangeEnd.value })
  } catch (e) {
    ElMessage.error('加载 AI 风险数据失败，请检查后端服务是否启动')
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
  await Promise.all([loadOverview(), loadTrends(), loadTop(), loadRisk(), loadReview(), loadContentOverview(true)])
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

// ── Summary cards (Chinese) ──
const summaryCards = computed(() => {
  const o = overview.value
  return [
    { key: 'users', title: '用户总数', value: o?.total_users ?? '-', hint: '活跃: ' + (o?.active_users ?? '-'), icon: UserFilled, bg: '#fef2f2', color: '#dc2626' },
    { key: 'news', title: '新闻总数', value: o?.total_news ?? '-', hint: '文章总量', icon: Files, bg: '#f0fdf4', color: '#16a34a' },
    { key: 'posts', title: '帖子总数', value: o?.total_posts ?? '-', hint: '社区帖子', icon: Message, bg: '#fefce8', color: '#ca8a04' },
    { key: 'comments', title: '评论总数', value: o?.total_comments ?? '-', hint: '新闻+帖子评论', icon: Document, bg: '#fdf2f8', color: '#db2777' },
    { key: 'ai', title: 'AI 生成', value: o?.ai_generate_count ?? '-', hint: '调用次数', icon: TrendCharts, bg: '#f5f3ff', color: '#7c3aed' },
    { key: 'timeline', title: '时间线', value: o?.timeline_count ?? '-', hint: '已生成', icon: DataBoard, bg: '#ecfeff', color: '#0891b2' },
    { key: 'pending', title: '待处理', value: o?.pending_count ?? '-', hint: '需审核', icon: Warning, bg: '#fff7ed', color: '#ea580c' },
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
        <p>查看系统运营数据、AI 生成情况、社区互动趋势与内容总览复核。</p>
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
        <h3>内容增长趋势</h3>
        <div v-if="trends?.content_trend?.length" ref="contentChartRef" class="chart-box" />
        <el-empty v-else description="暂无内容趋势数据" />
      </el-card>
      <el-card class="chart-card" shadow="never">
        <h3>AI 使用趋势</h3>
        <div v-if="trends?.ai_trend?.length" ref="aiChartRef" class="chart-box" />
        <el-empty v-else description="暂无 AI 趋势数据" />
      </el-card>
    </div>

    <!-- Top content + AI risk row -->
    <div class="content-row">
      <el-card class="content-card" shadow="never">
        <h3>热门新闻 Top10（按浏览量）</h3>
        <el-table :data="topContent?.top_news || []" v-loading="topLoading" empty-text="暂无数据" size="small">
          <el-table-column label="#" width="50"><template #default="{ row }">{{ row.rank }}</template></el-table-column>
          <el-table-column prop="title" label="标题" min-width="200" show-overflow-tooltip />
          <el-table-column prop="source" label="来源" width="100" />
          <el-table-column prop="view_count" label="浏览" width="70" />
          <el-table-column prop="comment_count" label="评论" width="70" />
          <el-table-column label="操作" width="70">
            <template #default><el-button text type="primary" size="small" :icon="View" @click="jumpTo('news')">查看</el-button></template>
          </el-table-column>
        </el-table>
      </el-card>

      <el-card class="content-card" shadow="never">
        <h3>AI 风险分布</h3>
        <div v-if="aiRisk?.items?.length" ref="riskChartRef" class="chart-box chart-box--small" />
        <el-empty v-else description="暂无 AI 风险数据" />
      </el-card>
    </div>

    <!-- Review summary + Top posts row -->
    <div class="content-row">
      <el-card class="content-card" shadow="never">
        <h3>审核处理概况</h3>
        <div v-if="reviewSummary" v-loading="reviewLoading">
          <div class="review-block">
            <h4>待处理</h4>
            <div class="tag-row">
              <el-tag type="warning">新闻: {{ reviewSummary.pending.news }}</el-tag>
              <el-tag type="warning">帖子: {{ reviewSummary.pending.posts }}</el-tag>
              <el-tag type="warning">评论: {{ reviewSummary.pending.comments }}</el-tag>
              <el-tag type="danger">合计: {{ reviewSummary.pending.total }}</el-tag>
            </div>
          </div>
          <div class="review-block">
            <h4>已处理（来自操作日志）</h4>
            <div class="tag-row">
              <el-tag type="success">通过: {{ reviewSummary.processed.approve }}</el-tag>
              <el-tag type="danger">驳回: {{ reviewSummary.processed.reject }}</el-tag>
              <el-tag type="info">折叠: {{ reviewSummary.processed.fold }}</el-tag>
              <el-tag>删除: {{ reviewSummary.processed.delete }}</el-tag>
              <el-tag>恢复: {{ reviewSummary.processed.restore }}</el-tag>
            </div>
          </div>
          <p class="review-footer">今日处理: {{ reviewSummary.today_processed }}</p>
        </div>
        <el-empty v-else description="暂无审核数据" />
      </el-card>

      <el-card class="content-card" shadow="never">
        <h3>热门帖子 Top10（按热度）</h3>
        <el-table :data="topContent?.top_posts || []" v-loading="topLoading" empty-text="暂无数据" size="small">
          <el-table-column label="#" width="50"><template #default="{ row }">{{ row.rank }}</template></el-table-column>
          <el-table-column prop="title" label="标题" min-width="180" show-overflow-tooltip />
          <el-table-column prop="author_name" label="作者" width="100" />
          <el-table-column prop="heat_score" label="热度" width="70" />
          <el-table-column label="操作" width="70">
            <template #default><el-button text type="primary" size="small" :icon="View" @click="jumpTo('posts')">查看</el-button></template>
          </el-table-column>
        </el-table>
      </el-card>
    </div>

    <!-- Content overview table -->
    <el-card class="overview-card" shadow="never">
      <div class="overview-header">
        <div>
          <h3>内容总览复核</h3>
          <p>统一查看所有内容类型。点击"查看"跳转到对应管理模块。</p>
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
        <el-table-column prop="risk_level" label="风险" width="70">
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
  grid-template-columns: repeat(7, minmax(0, 1fr));
  gap: 12px;
}
.summary-card { border-radius: 16px; }
.summary-card__inner { display: flex; gap: 12px; align-items: center; }
.summary-card__icon { width: 40px; height: 40px; border-radius: 12px; display: grid; place-items: center; flex-shrink: 0; }
.summary-card__title { font-size: 12px; color: var(--el-text-color-secondary); }
.summary-card__value { font-size: 22px; font-weight: 800; color: var(--el-text-color-primary); }
.summary-card__hint { font-size: 11px; color: var(--el-text-color-secondary); margin-top: 2px; }

.charts-row, .content-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}
.chart-card, .content-card, .overview-card {
  border-radius: 18px;
}
.chart-card h3, .content-card h3, .overview-card .overview-header h3 {
  margin: 0 0 10px;
}
.chart-box { width: 100%; height: 280px; }
.chart-box--small { height: 240px; }

.content-row { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }

.overview-filter {
  display: flex;
  gap: 8px;
  margin-bottom: 10px;
  align-items: center;
  flex-wrap: wrap;
}
.overview-header { margin-bottom: 6px; }
.overview-header p { margin: 0; color: var(--el-text-color-secondary); font-size: 12px; }

.review-block { margin-bottom: 12px; }
.review-block h4 { font-size: 13px; margin: 0 0 6px; color: var(--el-text-color-secondary); }
.tag-row { display: flex; flex-wrap: wrap; gap: 6px; }
.review-footer { font-size: 13px; color: var(--el-text-color-secondary); margin: 8px 0 0; }

.el-pagination { margin-top: 12px; justify-content: flex-end; }

@media (max-width: 1200px) {
  .summary-grid { grid-template-columns: repeat(4, minmax(0, 1fr)); }
}
@media (max-width: 960px) {
  .summary-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .charts-row, .content-row { grid-template-columns: 1fr; }
}
</style>
