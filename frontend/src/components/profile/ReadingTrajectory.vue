<template>
  <div class="reading-trajectory">
    <!-- 标题区域 -->
    <div class="trajectory-header">
      <div class="header-title">
        <h2 class="title">阅读脉络</h2>
        <p class="subtitle">基于你的浏览历史生成阅读主题关系图</p>
      </div>
      <el-button type="primary" :loading="loading" @click="handleReload">刷新数据</el-button>
    </div>

    <!-- Loading 状态 -->
    <el-skeleton v-if="loading" animated :rows="6" />

    <!-- Error 状态 -->
    <el-alert
      v-else-if="error"
      type="error"
      :title="error"
      :closable="false"
      class="error-alert"
    >
      <template #default>
        <el-button type="primary" @click="handleReload" class="error-button">重新加载</el-button>
      </template>
    </el-alert>

    <!-- Empty 状态 -->
    <el-empty
      v-else-if="!trajectoryData || trajectoryData.nodes.length === 0"
      description="暂无阅读脉络数据"
      :image-size="80"
    >
      <el-button type="primary" @click="handleReload">刷新重试</el-button>
    </el-empty>

    <!-- 正常展示 -->
    <div v-else class="trajectory-content">
      <!-- 数据概览卡片 -->
      <div class="overview-section">
        <h3 class="section-title">数据概览</h3>
        <div class="overview-cards">
          <div class="stat-card">
            <div class="stat-value">{{ trajectoryData.summary.total_reads }}</div>
            <div class="stat-label">总阅读数</div>
          </div>
          <div class="stat-card">
            <div class="stat-value">{{ trajectoryData.summary.unique_news_count }}</div>
            <div class="stat-label">独立新闻数</div>
          </div>
          <div class="stat-card">
            <div class="stat-value">{{ trajectoryData.summary.category_count }}</div>
            <div class="stat-label">涉及分类</div>
          </div>
          <div class="stat-card">
            <div class="stat-value">{{ trajectoryData.summary.topic_count }}</div>
            <div class="stat-label">涉及话题</div>
          </div>
        </div>
        <div class="summary-details">
          <div class="detail-item">
            <span class="detail-label">最常读分类：</span>
            <el-tag>{{ trajectoryData.summary.top_category }}</el-tag>
          </div>
          <div class="detail-item">
            <span class="detail-label">最感兴趣话题：</span>
            <el-tag>{{ trajectoryData.summary.top_topic }}</el-tag>
          </div>
        </div>
      </div>

      <!-- 图表控制栏 -->
      <div class="chart-controls">
        <div class="control-left">
          <el-radio-group v-model="timeRange" size="small" @change="handleTimeRangeChange">
            <el-radio-button value="7">最近7天</el-radio-button>
            <el-radio-button value="30">最近30天</el-radio-button>
          </el-radio-group>
          <el-checkbox-group v-model="visibleNodeTypes" size="small" @change="handleFilterChange">
            <el-checkbox value="category">分类</el-checkbox>
            <el-checkbox value="topic">话题</el-checkbox>
            <el-checkbox value="news">新闻</el-checkbox>
          </el-checkbox-group>
        </div>
        <div class="control-right">
          <el-button size="small" :icon="RefreshRight" @click="handleResetView">重置视图</el-button>
        </div>
      </div>

      <!-- 图表区域 -->
      <el-card class="chart-section" shadow="never">
        <template #header>
          <div class="card-header">
            <span>阅读脉络图</span>
            <span class="data-scale">节点数：{{ filteredNodeCount }} | 关系数：{{ filteredEdgeCount }}</span>
          </div>
        </template>
        <div ref="chartRef" class="trajectory-chart">
          <div v-if="!chartContainerReady" class="chart-placeholder-inner">
            <el-icon class="is-loading" :size="36"><Loading /></el-icon>
            <span>图表区域准备中...</span>
          </div>
        </div>
        <div class="chart-hint">
          💡 可拖拽节点，滚轮缩放；点击新闻节点进入详情页
        </div>
      </el-card>

      <!-- 热门分类、话题、最近阅读 -->
      <div class="supplementary-section">
        <!-- 热门分类 -->
        <el-card class="supplement-card" shadow="never">
          <template #header>
            <div class="card-header">
              <span>热门分类（{{ trajectoryData.top_categories.length }}）</span>
            </div>
          </template>
          <div v-if="trajectoryData.top_categories.length === 0" class="empty-card-text">
            暂无分类数据
          </div>
          <div v-else class="category-list">
            <div v-for="(category, index) in trajectoryData.top_categories" :key="category.category_id ?? index" class="category-item">
              <span class="category-name">{{ category.category_name }}</span>
              <el-badge :value="category.read_count" class="item-badge" />
            </div>
          </div>
        </el-card>

        <!-- 热门话题 -->
        <el-card class="supplement-card" shadow="never">
          <template #header>
            <div class="card-header">
              <span>热门话题（{{ trajectoryData.top_topics.length }}）</span>
            </div>
          </template>
          <div v-if="trajectoryData.top_topics.length === 0" class="empty-card-text">
            暂无话题数据
          </div>
          <div v-else class="topic-list">
            <div v-for="(topic, index) in trajectoryData.top_topics" :key="topic.topic_id ?? index" class="topic-item">
              <span class="topic-name">{{ topic.topic_name }}</span>
              <el-badge :value="topic.read_count" class="item-badge" />
            </div>
          </div>
        </el-card>

        <!-- 最近阅读 -->
        <el-card class="supplement-card" shadow="never">
          <template #header>
            <div class="card-header">
              <span>最近阅读（{{ trajectoryData.recent_news.length }}）</span>
            </div>
          </template>
          <div v-if="trajectoryData.recent_news.length === 0" class="empty-card-text">
            暂无阅读记录
          </div>
          <div v-else class="recent-news-list">
            <div
              v-for="news in trajectoryData.recent_news"
              :key="news.news_id"
              class="recent-news-item"
              @click="handleNewsClick(news.news_id)"
            >
              <div class="news-main">
                <h4 class="news-title">{{ news.title }}</h4>
                <div class="news-meta">
                  <el-tag size="small" type="info">{{ news.category_name }}</el-tag>
                  <el-tag v-if="news.topic_name" size="small">{{ news.topic_name }}</el-tag>
                  <span class="news-time">{{ formatTime(news.browse_time) }}</span>
                </div>
              </div>
              <div class="news-arrow">→</div>
            </div>
          </div>
        </el-card>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { RefreshRight, Loading } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'
import * as echarts from 'echarts'
import type { ECharts, EChartsOption } from 'echarts'
import { getReadingTrajectory, type ReadingTrajectoryResponse, type ReadingTrajectoryNode, type ReadingTrajectoryEdge } from '@/api/profile'
import { useThemeStore } from '@/stores/theme'
import { getChartThemeColors } from '@/utils/chartTheme'

const router = useRouter()
const themeStore = useThemeStore()

const loading = ref(false)
const error = ref('')
const trajectoryData = ref<ReadingTrajectoryResponse | null>(null)
const chartRef = ref<HTMLElement | null>(null)
const chartContainerReady = ref(false)
let chartInstance: ECharts | null = null
let renderTimer: any = null
let resizeObserver: ResizeObserver | null = null
let lastChartWidth = 0

// Filter state
const timeRange = ref<7 | 30>(30)
const visibleNodeTypes = ref<string[]>(['category', 'topic', 'news'])

function getNodeColor(type: string): string {
  const colors: Record<string, string> = {
    category: '#d92d20',
    topic: '#67C23A',
    news: '#F56C6C',
  }
  return colors[type] || '#909399'
}

function getNodeSize(type: string, value: number): number {
  // More distinct node sizes per type
  if (type === 'category') {
    return 30 + Math.min(value * 2, 30)
  }
  if (type === 'topic') {
    return 20 + Math.min(value * 1.8, 24)
  }
  // news nodes
  return 10 + Math.min(value * 1.2, 16)
}

function getNodeCategory(type: string): number {
  const categoryMap: Record<string, number> = {
    category: 0,
    topic: 1,
    news: 2,
  }
  return categoryMap[type] ?? 2
}

function getTypeLabel(type: string): string {
  const labels: Record<string, string> = {
    category: '分类',
    topic: '话题',
    news: '新闻',
  }
  return labels[type] || type
}

function getEdgeTypeLabel(type: string): string {
  const labels: Record<string, string> = {
    category_topic: '分类-话题',
    topic_news: '话题-新闻',
    sequence: '阅读顺序',
  }
  return labels[type] || type
}

// Filtered nodes and edges
const filteredNodes = computed(() => {
  if (!trajectoryData.value) return []
  return trajectoryData.value.nodes.filter(n => visibleNodeTypes.value.includes(n.type))
})

const filteredEdges = computed(() => {
  if (!trajectoryData.value) return []
  const visibleNodeIds = new Set(filteredNodes.value.map(n => n.id))
  return trajectoryData.value.edges.filter(
    e => visibleNodeIds.has(e.source) && visibleNodeIds.has(e.target)
  )
})

const filteredNodeCount = computed(() => filteredNodes.value.length)
const filteredEdgeCount = computed(() => filteredEdges.value.length)

function setupResizeObserver(): void {
  if (!chartRef.value) {
    return
  }

  // Clean up old observer
  if (resizeObserver) {
    resizeObserver.disconnect()
  }

  resizeObserver = new ResizeObserver((entries) => {
    if (entries.length === 0) return

    const entry = entries[0]
    const width = entry.contentRect.width
    const height = entry.contentRect.height

    // Mark container as ready when valid size detected
    if (width >= 300 && height >= 300) {
      chartContainerReady.value = true
      if (trajectoryData.value && filteredNodes.value.length > 0) {
        renderChart()
      }
      chartInstance?.resize()
    }
  })

  resizeObserver.observe(chartRef.value)
}

function renderChart() {
  if (!chartRef.value || !trajectoryData.value) {
    return
  }

  const nodes = filteredNodes.value
  if (nodes.length === 0) {
    return
  }

  const el = chartRef.value
  const width = el.clientWidth
  const height = el.clientHeight

  // Container too small — don't render, wait for ResizeObserver
  if (width < 300 || height < 300) {
    return
  }

  // Track last valid width
  lastChartWidth = width

  // If chart was previously initialized at a bad width (< 300), dispose and re-init
  if (chartInstance && lastChartWidth < 300) {
    chartInstance.dispose()
    chartInstance = null
  }

  if (!chartInstance) {
    try {
      chartInstance = echarts.init(chartRef.value)
    } catch (err) {
      console.error('[ReadingTrajectory] ECharts init failed', err)
      return
    }
  }
  const theme = getChartThemeColors()

  const edges = filteredEdges.value

  const graphNodes = nodes.map((node: ReadingTrajectoryNode) => ({
    id: node.id,
    name: node.name,
    value: node.value,
    type: node.type,
    news_id: node.news_id,
    category_name: node.category_name,
    topic_name: node.topic_name,
    browse_time: node.browse_time,
    symbolSize: getNodeSize(node.type, node.value),
    itemStyle: {
      color: getNodeColor(node.type),
    },
    category: getNodeCategory(node.type),
  }))

  const graphLinks = edges.map((edge: ReadingTrajectoryEdge) => ({
    source: edge.source,
    target: edge.target,
    value: edge.value,
    type: edge.type,
    lineStyle: {
      width: Math.min(Math.max(edge.value, 1), 6),
      opacity: 0.45,
      type: edge.type === 'sequence' ? 'dashed' : 'solid',
    },
  }))

  const option: any = {
    tooltip: {
      trigger: 'item',
      backgroundColor: theme.tooltipBg,
      borderColor: theme.axisLine,
      textStyle: {
        color: theme.tooltipText,
      },
      formatter: (params: any) => {
        if (params.dataType === 'node') {
          const node = params.data
          let content = `<div style="font-weight: 600; margin-bottom: 6px;">${node.name}</div>`
          content += `<div>类型: ${getTypeLabel(node.type)}</div>`
          content += `<div>权重: ${node.value}</div>`
          if (node.category_name) {
            content += `<div>分类: ${node.category_name}</div>`
          }
          if (node.topic_name) {
            content += `<div>话题: ${node.topic_name}</div>`
          }
          if (node.browse_time) {
            content += `<div>时间: ${node.browse_time}</div>`
          }
          return content
        } else if (params.dataType === 'edge') {
          const edge = params.data
          return `<div>${edge.source} → ${edge.target}</div><div>关系: ${getEdgeTypeLabel(edge.type)}</div><div>强度: ${edge.value}</div>`
        }
        return ''
      },
    },
    series: [
      {
        type: 'graph',
        layout: 'force',
        data: graphNodes,
        links: graphLinks,
        roam: true,
        draggable: true,
        force: {
          repulsion: 120,
          gravity: 0.05,
          friction: 0.6,
          edgeLength: [80, 160],
        },
        emphasis: {
          focus: 'adjacency',
          lineStyle: {
            width: 2,
          },
        },
        label: {
          position: 'right',
          fontSize: 11,
          color: theme.axisText,
        },
        edgeLabel: {
          fontSize: 11,
          color: theme.axisText,
        },
      },
    ],
  }

  chartInstance.setOption(option)
  chartInstance.resize()

  // 处理点击事件
  chartInstance.off('click')
  chartInstance.on('click', (params: any) => {
    if (params.dataType !== 'node') return
    const node = params.data

    if (node.type === 'news' && node.news_id) {
      router.push(`/news/${node.news_id}`)
    } else {
      const msg = `${getTypeLabel(node.type)}: ${node.name}`
      ElMessage.info(msg)
    }
  })
}

function scheduleRenderChart(retryCount = 0): void {
  if (retryCount > 8) {
    // After all retries, rely on ResizeObserver
    return
  }

  const el = chartRef.value
  if (!el) {
    return
  }

  const width = el.clientWidth
  const height = el.clientHeight

  // If width is still too small, retry with backoff
  if (width < 200 || height < 300) {
    chartContainerReady.value = false
    if (renderTimer !== null) {
      window.clearTimeout(renderTimer)
    }
    const delay = Math.min(100 * Math.pow(1.5, retryCount), 800)
    renderTimer = window.setTimeout(() => {
      scheduleRenderChart(retryCount + 1)
    }, delay)
    return
  }

  // Container has valid dimensions
  chartContainerReady.value = true
  lastChartWidth = width

  renderChart()
}

function handleResize() {
  chartInstance?.resize()
}

async function loadTrajectory() {
  loading.value = true
  error.value = ''
  try {
    const result = await getReadingTrajectory({ days: timeRange.value, limit: 200 })
    trajectoryData.value = result
    loading.value = false
    await nextTick()
    setupResizeObserver()
    scheduleRenderChart()
  } catch (err) {
    error.value = err instanceof Error ? err.message : '加载阅读脉络数据失败，请稍后重试'
    ElMessage.error(error.value)
    loading.value = false
  }
}

function handleReload() {
  loadTrajectory()
}

function handleTimeRangeChange() {
  // Dispose old chart before reloading data
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
  chartContainerReady.value = false
  lastChartWidth = 0
  loadTrajectory()
}

function handleFilterChange() {
  nextTick(() => {
    renderChart()
  })
}

function handleResetView() {
  if (chartInstance) {
    chartInstance.dispatchAction({
      type: 'restore'
    })
    ElMessage.success('视图已重置')
  }
}

function handleNewsClick(newsId: number) {
  router.push(`/news/${newsId}`)
}

function formatTime(timestamp: string): string {
  try {
    const date = new Date(timestamp)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

    if (diffDays === 0) {
      return '今天'
    } else if (diffDays === 1) {
      return '昨天'
    } else if (diffDays < 7) {
      return `${diffDays}天前`
    } else {
      return date.toLocaleDateString('zh-CN')
    }
  } catch {
    return timestamp
  }
}

watch(
  () => trajectoryData.value,
  async () => {
    await nextTick()
    scheduleRenderChart()
  },
)

watch(() => themeStore.theme, () => nextTick(renderChart))

onMounted(async () => {
  await nextTick()
  loadTrajectory()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  if (renderTimer !== null) {
    window.clearTimeout(renderTimer)
    renderTimer = null
  }
  if (resizeObserver !== null) {
    resizeObserver.disconnect()
    resizeObserver = null
  }
  chartInstance?.dispose()
  chartInstance = null
})
</script>

<style scoped lang="scss">
.reading-trajectory {
  width: 100%;
  min-width: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.trajectory-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: 8px;

  .header-title {
    flex: 1;
    min-width: 0;

    .title {
      margin: 0 0 4px;
      font-size: 22px;
      font-weight: 600;
      color: var(--el-text-color-primary);
    }

    .subtitle {
      margin: 0;
      font-size: 14px;
      color: var(--el-text-color-secondary);
    }
  }
}

.error-alert {
  margin-bottom: 12px;

  .error-button {
    margin-top: 8px;
  }
}

.trajectory-content {
  width: 100%;
  max-width: 100%;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 20px;
  box-sizing: border-box;
}

// 数据概览部分
.overview-section {
  display: flex;
  flex-direction: column;
  gap: 16px;

  .section-title {
    margin: 0;
    font-size: 16px;
    font-weight: 600;
    color: var(--el-text-color-primary);
  }

  .overview-cards {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
    gap: 12px;
  }

  .stat-card {
    padding: 16px;
    border: 1px solid var(--el-border-color-light);
    border-radius: 8px;
    background: var(--el-fill-color-light);
    text-align: center;
    transition: all 0.3s ease;

    &:hover {
      border-color: var(--el-color-primary);
      background: var(--el-color-primary-light-9);
    }

    .stat-value {
      font-size: 28px;
      font-weight: 700;
      color: var(--el-color-primary);
      line-height: 1.2;
      margin-bottom: 4px;
    }

    .stat-label {
      font-size: 12px;
      color: var(--el-text-color-secondary);
    }
  }

  .summary-details {
    display: flex;
    gap: 20px;
    padding: 12px 0;
    border-top: 1px solid var(--el-border-color-light);
    border-bottom: 1px solid var(--el-border-color-light);

    .detail-item {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 14px;

      .detail-label {
        color: var(--el-text-color-secondary);
      }
    }
  }
}

// 图表控制栏
.chart-controls {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
  padding: 12px 16px;
  background: var(--el-fill-color-lighter);
  border-radius: 8px;
  border: 1px solid var(--el-border-color-light);

  .control-left {
    display: flex;
    align-items: center;
    gap: 16px;
    flex-wrap: wrap;
  }

  .control-right {
    flex-shrink: 0;
  }
}

// 图表区域
.chart-section {
  width: 100%;
  max-width: 100%;
  min-width: 0;
  flex: 1 1 100%;
  border: 1px solid var(--el-border-color-light);
  border-radius: 8px;
  box-sizing: border-box;

  :deep(.el-card__header) {
    border-bottom: 1px solid var(--el-border-color-light);
  }

  :deep(.el-card__body) {
    width: 100%;
    max-width: 100%;
    min-width: 0;
    padding: 16px;
    box-sizing: border-box;
  }

  .card-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    width: 100%;

    .data-scale {
      font-size: 12px;
      color: var(--el-text-color-secondary);
    }
  }

	  .trajectory-chart {
	    display: block;
	    width: 100%;
	    max-width: 100%;
	    min-width: 320px;
	    min-height: 520px;
	    height: 520px;
	    box-sizing: border-box;
	    position: relative;
	  }

	  .chart-placeholder-inner {
	    display: flex;
	    flex-direction: column;
	    align-items: center;
	    justify-content: center;
	    gap: 12px;
	    width: 100%;
	    height: 100%;
	    color: var(--el-text-color-secondary);
	    font-size: 14px;
	    position: absolute;
	    top: 0;
	    left: 0;
	  }

  .chart-hint {
    padding: 12px 0;
    text-align: center;
    font-size: 13px;
    color: var(--el-text-color-secondary);
    border-top: 1px solid var(--el-border-color-light);
    margin-top: 12px;
  }
}

// 补充信息区域
.supplementary-section {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 20px;

  .supplement-card {
    border: 1px solid var(--el-border-color-light);
    border-radius: 8px;

    :deep(.el-card__header) {
      border-bottom: 1px solid var(--el-border-color-light);
    }

    .card-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      width: 100%;
      font-size: 14px;
      font-weight: 600;
    }

    .empty-card-text {
      padding: 40px 20px;
      text-align: center;
      color: var(--el-text-color-secondary);
      font-size: 13px;
    }
  }
}

// 分类列表
.category-list {
  display: flex;
  flex-direction: column;
  gap: 10px;

  .category-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px 12px;
    border-radius: 6px;
    background: var(--el-fill-color-light);
    transition: all 0.3s ease;

    &:hover {
      background: var(--el-color-primary-light-9);
    }

    .category-name {
      font-size: 14px;
      color: var(--el-text-color-primary);
      font-weight: 500;
    }

    .item-badge {
      font-size: 12px;
    }
  }
}

// 话题列表
.topic-list {
  display: flex;
  flex-direction: column;
  gap: 10px;

  .topic-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px 12px;
    border-radius: 6px;
    background: var(--el-fill-color-light);
    transition: all 0.3s ease;

    &:hover {
      background: var(--el-color-primary-light-9);
    }

    .topic-name {
      font-size: 14px;
      color: var(--el-text-color-primary);
      font-weight: 500;
    }

    .item-badge {
      font-size: 12px;
    }
  }
}

// 最近阅读列表
.recent-news-list {
  display: flex;
  flex-direction: column;
  gap: 10px;

  .recent-news-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px;
    border-radius: 6px;
    background: var(--el-fill-color-light);
    cursor: pointer;
    transition: all 0.3s ease;

    &:hover {
      background: var(--el-color-primary-light-9);
      transform: translateX(4px);

      .news-arrow {
        color: var(--el-color-primary);
      }
    }

    .news-main {
      flex: 1;
      min-width: 0;
      display: flex;
      flex-direction: column;
      gap: 6px;

      .news-title {
        margin: 0;
        font-size: 13px;
        font-weight: 500;
        color: var(--el-text-color-primary);
        line-height: 1.4;
        overflow: hidden;
        text-overflow: ellipsis;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
      }

      .news-meta {
        display: flex;
        align-items: center;
        gap: 6px;
        flex-wrap: wrap;

        .news-time {
          font-size: 12px;
          color: var(--el-text-color-secondary);
          white-space: nowrap;
        }
      }
    }

    .news-arrow {
      flex-shrink: 0;
      margin-left: 8px;
      font-size: 18px;
      color: var(--el-text-color-placeholder);
      transition: color 0.3s ease;
    }
  }
}

// 响应式设计
@media (max-width: 768px) {
  .trajectory-header {
    flex-direction: column;
    align-items: flex-start;

    .header-title {
      .title {
        font-size: 18px;
      }

      .subtitle {
        font-size: 13px;
      }
    }
  }

  .overview-section {
    .overview-cards {
      grid-template-columns: repeat(2, minmax(100px, 1fr));
    }

    .summary-details {
      flex-direction: column;
      gap: 12px;
    }
  }

  .supplementary-section {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 480px) {
  .reading-trajectory {
    padding: 0;
  }

  .overview-section {
    .overview-cards {
      grid-template-columns: 1fr;
    }
  }

  .chart-placeholder {
    min-height: 280px !important;
  }

  .recent-news-item {
    flex-direction: column;
    align-items: flex-start !important;

    .news-arrow {
      margin-left: 0 !important;
      margin-top: 6px;
    }
  }
}
</style>
