<template>
  <div class="reading-heatmap">
    <div class="heatmap-header">
      <div class="header-info">
        <h3 class="header-title">阅读热力图</h3>
        <p class="header-subtitle">按分类查看每日阅读热度分布</p>
      </div>
      <div class="header-controls">
        <el-radio-group v-model="timeRange" size="small" @change="handleReload">
          <el-radio-button value="7">7天</el-radio-button>
          <el-radio-button value="30">30天</el-radio-button>
        </el-radio-group>
        <el-button size="small" :loading="loading" @click="handleReload">刷新</el-button>
      </div>
    </div>

    <el-skeleton v-if="loading" :rows="4" animated />

    <el-empty v-else-if="!hasData" description="暂无热力图数据" :image-size="60" />

    <div v-else class="heatmap-content">
      <!-- Summary -->
      <div class="heatmap-summary">
        <span class="summary-text">
          最高热度: <strong>{{ data?.summary.max_value ?? 0 }}</strong>
        </span>
        <span class="summary-text">
          最活跃分类: <strong>{{ data?.summary.most_active_category || '-' }}</strong>
        </span>
        <span class="summary-text">
          最活跃日期: <strong>{{ data?.summary.most_active_date || '-' }}</strong>
        </span>
      </div>

      <!-- Chart -->
      <div ref="chartRef" class="heatmap-chart"></div>

      <div class="heatmap-hint">
        💡 颜色越深表示该分类在该日期的阅读次数越多
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, nextTick, watch } from 'vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import type { ECharts } from 'echarts'
import { getReadingHeatmap, type ReadingHeatmapResponse } from '@/api/profile'
import { useThemeStore } from '@/stores/theme'
import { createCategoryAxis, createChartTooltip, getChartThemeColors } from '@/utils/chartTheme'

const loading = ref(false)
const data = ref<ReadingHeatmapResponse | null>(null)
const timeRange = ref<7 | 30>(30)
const chartRef = ref<HTMLElement | null>(null)
const themeStore = useThemeStore()
let chartInstance: ECharts | null = null
let resizeObserver: ResizeObserver | null = null

const hasData = computed(() => {
  return data.value && data.value.x_axis.length > 0 && data.value.y_axis.length > 0 && data.value.cells.length > 0
})

function renderChart() {
  if (!chartRef.value || !hasData.value || !data.value) return

  const el = chartRef.value
  const width = el.clientWidth
  const height = el.clientHeight
  if (width < 200 || height < 200) return

  if (!chartInstance) {
    try {
      chartInstance = echarts.init(el)
    } catch (err) {
      console.error('[ReadingHeatmap] ECharts init failed', err)
      return
    }
  }

  const { x_axis, y_axis, cells } = data.value
  const maxVal = data.value.summary.max_value || 1
  const theme = getChartThemeColors()

  const heatData = cells.map(cell => [x_axis.indexOf(cell.x), y_axis.indexOf(cell.y), cell.value])

  const option: any = {
    backgroundColor: theme.background,
    tooltip: createChartTooltip('item', {
      position: 'top',
      formatter: (params: any) => {
        const [xi, yi, val] = params.data
        return `${x_axis[xi]}<br/>${y_axis[yi]}: <strong>${val}</strong> 篇`
      },
    }),
    grid: {
      left: '120px',
      right: '40px',
      top: '20px',
      bottom: '60px',
    },
    xAxis: createCategoryAxis(x_axis, {
      splitArea: { show: true },
      axisLabel: {
        fontSize: 11,
        rotate: 30,
      },
    }),
    yAxis: createCategoryAxis(y_axis, {
      splitArea: { show: true },
      axisLabel: {
        fontSize: 12,
      },
    }),
    visualMap: {
      min: 0,
      max: maxVal,
      calculable: true,
      orient: 'horizontal',
      left: 'center',
      bottom: '0%',
      inRange: {
        color: ['#fff1f0', '#fecaca', '#f87171', '#d92d20', '#b91c1c', '#991b1b'],
      },
      text: ['高', '低'],
      textStyle: {
        fontSize: 11,
        color: theme.axisText,
      },
    },
    series: [
      {
        name: '阅读次数',
        type: 'heatmap',
        data: heatData,
        label: {
          show: heatData.length < 50,
          fontSize: 10,
          color: theme.tooltipText,
        },
        emphasis: {
          itemStyle: {
            shadowBlur: 8,
            shadowColor: 'rgba(0, 0, 0, 0.4)',
          },
        },
      },
    ],
  }

  chartInstance.setOption(option, true)
  chartInstance.resize()
}

function setupResizeObserver() {
  if (!chartRef.value) return
  if (resizeObserver) resizeObserver.disconnect()

  resizeObserver = new ResizeObserver((entries) => {
    if (entries.length === 0) return
    const { width, height } = entries[0].contentRect
    if (width >= 200 && height >= 200) {
      renderChart()
      chartInstance?.resize()
    }
  })
  resizeObserver.observe(chartRef.value)
}

async function loadData() {
  loading.value = true
  try {
    data.value = await getReadingHeatmap({ days: timeRange.value })
    await nextTick()
    setupResizeObserver()
    renderChart()
  } catch (err) {
    ElMessage.error('加载热力图数据失败')
  } finally {
    loading.value = false
  }
}

function handleReload() {
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
  loadData()
}

onMounted(async () => {
  await nextTick()
  loadData()
  window.addEventListener('resize', () => chartInstance?.resize())
})

watch(() => themeStore.theme, () => nextTick(renderChart))

onBeforeUnmount(() => {
  window.removeEventListener('resize', () => chartInstance?.resize())
  resizeObserver?.disconnect()
  resizeObserver = null
  chartInstance?.dispose()
  chartInstance = null
})
</script>

<style scoped lang="scss">
.reading-heatmap {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.heatmap-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;

  .header-title {
    margin: 0 0 2px;
    font-size: 18px;
    font-weight: 600;
    color: var(--el-text-color-primary);
  }

  .header-subtitle {
    margin: 0;
    font-size: 13px;
    color: var(--el-text-color-secondary);
  }

  .header-controls {
    display: flex;
    align-items: center;
    gap: 8px;
  }
}

.heatmap-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.heatmap-summary {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  padding: 10px 14px;
  background: var(--el-fill-color-lighter);
  border-radius: 8px;
  border: 1px solid var(--el-border-color-light);

  .summary-text {
    font-size: 13px;
    color: var(--el-text-color-secondary);

    strong {
      color: var(--el-text-color-primary);
      font-weight: 600;
    }
  }
}

.heatmap-chart {
  width: 100%;
  min-width: 320px;
  height: 360px;
  border: 1px solid var(--el-border-color-light);
  border-radius: 8px;
  background: var(--el-bg-color);
}

.heatmap-hint {
  text-align: center;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}
</style>
