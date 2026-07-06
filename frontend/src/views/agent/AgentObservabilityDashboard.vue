<script setup lang="ts">
/** AgentObservabilityDashboard — 系统级可观测面板（Phase 4）。
 *
 * 4 个图表 + 概览卡片：
 *   1. Token 统计（柱状图）
 *   2. 延迟热力图（横向柱状图）
 *   3. Provider 分布（饼图）
 *   4. 成功率卡片
 *
 * 遵循 AdminAnalyticsDashboard.vue 的 ECharts 模式。
 */

import { computed, onBeforeUnmount, onMounted, ref, watch, nextTick } from 'vue'
import * as echarts from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { BarChart, LineChart, PieChart } from 'echarts/charts'
import { GridComponent, LegendComponent, TitleComponent, TooltipComponent } from 'echarts/components'
import { getObservability, type ObservabilityResponse } from '@/api/agentAnalysis'
import { useThemeStore } from '@/stores/theme'
import {
  createCategoryAxis,
  createChartLegend,
  createChartTooltip,
  createValueAxis,
  getChartThemeColors,
} from '@/utils/chartTheme'

echarts.use([CanvasRenderer, BarChart, LineChart, PieChart, TitleComponent, TooltipComponent, LegendComponent, GridComponent])

const loading = ref(false)
const error = ref('')
const days = ref(7)
const data = ref<ObservabilityResponse | null>(null)
const themeStore = useThemeStore()

// ── Chart refs ──
const tokenChartRef = ref<HTMLDivElement>()
const latencyChartRef = ref<HTMLDivElement>()
const providerChartRef = ref<HTMLDivElement>()
const trendChartRef = ref<HTMLDivElement>()
let tokenChart: echarts.ECharts | null = null
let latencyChart: echarts.ECharts | null = null
let providerChart: echarts.ECharts | null = null
let trendChart: echarts.ECharts | null = null

// ── Computed ──
const successPct = computed(() => data.value ? Math.round(data.value.overview.success_rate * 100) : 0)
const totalTokens = computed(() => data.value?.overview.total_tokens ?? 0)
const avgLatency = computed(() => data.value?.overview.avg_latency_ms ?? 0)

function formatMs(ms: number): string {
  return ms >= 1000 ? (ms / 1000).toFixed(1) + 's' : ms.toFixed(0) + 'ms'
}
function formatTokens(n: number): string {
  return n >= 1000 ? (n / 1000).toFixed(1) + 'k' : String(n)
}

// ── Load data ──
async function loadData() {
  loading.value = true
  error.value = ''
  try {
    data.value = await getObservability(days.value)
    await nextTick()
    renderCharts()
  } catch (e) {
    error.value = e instanceof Error ? e.message : '加载可观测数据失败'
  } finally {
    loading.value = false
  }
}

// ── Chart rendering ──
function renderCharts() {
  if (!data.value) return
  const theme = getChartThemeColors()

  // 1. Token 柱状图
  if (tokenChartRef.value) {
    if (!tokenChart) tokenChart = echarts.init(tokenChartRef.value)
    const labels = data.value.token_stats.map(s => s.step_label)
    tokenChart.setOption({
      backgroundColor: theme.background,
      tooltip: createChartTooltip('axis'),
      grid: { left: 20, right: 20, top: 10, bottom: 30 },
      xAxis: createCategoryAxis(labels, { axisLabel: { rotate: 30, fontSize: 10 } }),
      yAxis: createValueAxis({ name: 'tokens' }),
      series: [{
        type: 'bar',
        data: data.value.token_stats.map(s => s.total_tokens),
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#d92d20' },
            { offset: 1, color: '#fca5a5' },
          ]),
          borderRadius: [6, 6, 0, 0],
        },
        barWidth: '50%',
      }],
    }, true)
  }

  // 2. 延迟横向柱状图
  if (latencyChartRef.value) {
    if (!latencyChart) latencyChart = echarts.init(latencyChartRef.value)
    const labels = data.value.latency_stats.map(s => s.step_label)
    const values = data.value.latency_stats.map(s => s.avg_ms)
    const maxVal = Math.max(...values, 1)
    const colors = values.map(v => v < 100 ? '#22c55e' : v < 500 ? '#f59e0b' : '#ef4444')
    latencyChart.setOption({
      backgroundColor: theme.background,
      tooltip: createChartTooltip('axis', {
        formatter: (p: any) => {
          const item = p[0]
          return `${item.name}<br/>平均: ${formatMs(item.value)}<br/>范围: ${formatMs(data.value!.latency_stats[item.dataIndex].min_ms)} ~ ${formatMs(data.value!.latency_stats[item.dataIndex].max_ms)}`
        },
      }),
      grid: { left: 100, right: 40, top: 10, bottom: 20 },
      xAxis: createValueAxis({ name: 'ms', axisLabel: { fontSize: 10 } }),
      yAxis: createCategoryAxis(labels.reverse(), { axisLabel: { fontSize: 11 } }),
      series: [{
        type: 'bar',
        data: values.reverse().map((v, i) => ({
          value: v,
          itemStyle: {
            color: colors.reverse()[i],
            borderRadius: [0, 6, 6, 0],
          },
        })),
        barWidth: '55%',
      }],
    }, true)
  }

  // 3. Provider 饼图
  if (providerChartRef.value) {
    if (!providerChart) providerChart = echarts.init(providerChartRef.value)
    const pieData = data.value.provider_stats.map(s => ({
      name: s.provider,
      value: s.count,
    }))
    providerChart.setOption({
      backgroundColor: theme.background,
      tooltip: createChartTooltip('item', { formatter: '{b}: {c} ({d}%)' }),
      legend: createChartLegend({ bottom: 0 }),
      series: [{
        type: 'pie',
        radius: ['45%', '75%'],
        center: ['50%', '48%'],
        data: pieData,
        label: { show: false, color: theme.axisText },
        emphasis: {
          label: { show: true, fontSize: 14, fontWeight: 'bold', color: theme.tooltipText },
        },
        itemStyle: { borderRadius: 4, borderColor: theme.axisLine, borderWidth: 2 },
      }],
    }, true)
  }

  // 4. 成功/失败趋势折线图
  if (trendChartRef.value && data.value.trend_stats?.length) {
    if (!trendChart) trendChart = echarts.init(trendChartRef.value)
    const dates = data.value.trend_stats.map(t => t.date.slice(5)) // MM-DD
    trendChart.setOption({
      backgroundColor: theme.background,
      tooltip: createChartTooltip('axis'),
      legend: createChartLegend({
        data: ['成功', '失败', '总计'],
        bottom: 0,
      }),
      grid: { left: 20, right: 20, top: 20, bottom: 30 },
      xAxis: createCategoryAxis(dates, { axisLabel: { fontSize: 10 } }),
      yAxis: createValueAxis({ minInterval: 1, axisLabel: { fontSize: 10 } }),
      series: [
        {
          name: '成功',
          type: 'line',
          data: data.value.trend_stats.map(t => t.completed),
          smooth: true,
          symbol: 'circle',
          symbolSize: 6,
          lineStyle: { color: '#22c55e', width: 2 },
          itemStyle: { color: '#22c55e' },
          areaStyle: { color: 'rgba(34, 197, 94, 0.08)' },
        },
        {
          name: '失败',
          type: 'line',
          data: data.value.trend_stats.map(t => t.failed),
          smooth: true,
          symbol: 'diamond',
          symbolSize: 6,
          lineStyle: { color: '#ef4444', width: 2, type: 'dashed' },
          itemStyle: { color: '#ef4444' },
        },
        {
          name: '总计',
          type: 'line',
          data: data.value.trend_stats.map(t => t.total),
          smooth: true,
          symbol: 'none',
          lineStyle: { color: '#94a3b8', width: 1.5, type: 'dotted' },
          itemStyle: { color: '#94a3b8' },
        },
      ],
    }, true)
  }
}

// ── Resize ──
function handleResize() {
  tokenChart?.resize()
  latencyChart?.resize()
  providerChart?.resize()
  trendChart?.resize()
}

onMounted(() => { loadData(); window.addEventListener('resize', handleResize) })
watch(() => themeStore.theme, () => nextTick(renderCharts))
onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  tokenChart?.dispose()
  latencyChart?.dispose()
  providerChart?.dispose()
  trendChart?.dispose()
})
</script>

<template>
  <div class="obs-dashboard">
    <!-- 页面标题 -->
    <div class="obs-header">
      <h1 class="obs-title">📊 Agent 可观测面板</h1>
      <div class="obs-actions">
        <el-radio-group v-model="days" size="small" @change="loadData">
          <el-radio-button :value="1">24h</el-radio-button>
          <el-radio-button :value="7">7d</el-radio-button>
          <el-radio-button :value="30">30d</el-radio-button>
        </el-radio-group>
        <el-button size="small" :icon="'Refresh'" @click="loadData" :loading="loading">刷新</el-button>
      </div>
    </div>

    <!-- 错误 -->
    <el-alert v-if="error" :title="error" type="error" show-icon :closable="false" class="obs-error" />

    <!-- 概览卡片 -->
    <div class="obs-cards">
      <div class="obs-card">
        <div class="obs-card__icon">📋</div>
        <div class="obs-card__value">{{ data?.overview.total_tasks ?? '-' }}</div>
        <div class="obs-card__label">总任务数</div>
      </div>
      <div class="obs-card">
        <div class="obs-card__icon">✅</div>
        <div class="obs-card__value">{{ successPct }}%</div>
        <div class="obs-card__label">成功率 ({{ data?.overview.completed_tasks ?? 0 }}/{{ data?.overview.total_tasks ?? 0 }})</div>
      </div>
      <div class="obs-card">
        <div class="obs-card__icon">⏱</div>
        <div class="obs-card__value">{{ formatMs(avgLatency) }}</div>
        <div class="obs-card__label">平均步骤延迟</div>
      </div>
      <div class="obs-card">
        <div class="obs-card__icon">🔤</div>
        <div class="obs-card__value">{{ formatTokens(totalTokens) }}</div>
        <div class="obs-card__label">总 Token 消耗</div>
      </div>
    </div>

    <!-- 图表区域 -->
    <el-skeleton v-if="loading" animated :rows="8" />

    <template v-else-if="data">
      <div class="obs-charts">
        <!-- Token 统计 -->
        <div class="obs-chart-panel">
          <h3 class="chart-title">🔤 Token 消耗（按步骤）</h3>
          <div ref="tokenChartRef" class="chart-box"></div>
        </div>

        <!-- 延迟热力图 -->
        <div class="obs-chart-panel">
          <h3 class="chart-title">⏱ 延迟分布（按步骤）</h3>
          <div ref="latencyChartRef" class="chart-box"></div>
        </div>

        <!-- Provider 分布 -->
        <div class="obs-chart-panel">
          <h3 class="chart-title">🤖 LLM Provider 分布</h3>
          <div ref="providerChartRef" class="chart-box chart-box--pie"></div>
        </div>

        <!-- 成功/失败趋势 -->
        <div class="obs-chart-panel obs-chart-panel--wide">
          <h3 class="chart-title">📈 成功 / 失败趋势</h3>
          <div ref="trendChartRef" class="chart-box"></div>
        </div>
      </div>
    </template>

    <el-empty v-else description="暂无数据" :image-size="80" />
  </div>
</template>

<style scoped>
.obs-dashboard {
  max-width: 1300px;
  margin: 0 auto;
  padding-bottom: 40px;
}

.obs-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
  flex-wrap: wrap;
  gap: 12px;
}

.obs-title {
  margin: 0;
  font-size: 24px;
  font-weight: 700;
  color: var(--color-text-primary);
}

.obs-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.obs-error { margin-bottom: 16px; }

/* 概览卡片 */
.obs-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.obs-card {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: 14px;
  padding: 20px;
  text-align: center;
}

.obs-card__icon { font-size: 28px; margin-bottom: 8px; }
.obs-card__value {
  font-size: 28px;
  font-weight: 700;
  color: var(--color-text-primary);
  font-variant-numeric: tabular-nums;
}
.obs-card__label {
  margin-top: 4px;
  font-size: 12px;
  color: var(--color-text-secondary);
}

/* 图表区 */
.obs-charts {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.obs-chart-panel {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: 14px;
  padding: 16px;
}

.obs-chart-panel--wide {
  grid-column: 1 / -1;
}

.chart-title {
  margin: 0 0 10px;
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.chart-box { width: 100%; height: 280px; }
.chart-box--pie { height: 320px; }

@media (max-width: 900px) {
  .obs-cards { grid-template-columns: repeat(2, 1fr); }
  .obs-charts { grid-template-columns: 1fr; }
}

@media (max-width: 500px) {
  .obs-cards { grid-template-columns: 1fr; }
}
</style>
