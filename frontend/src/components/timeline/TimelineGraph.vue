<template>
  <div class="timeline-graph">
    <div class="graph-toolbar">
      <div class="graph-legend">
        <span
          v-for="item in legendItems"
          :key="item.type"
          class="legend-item"
          :style="{ '--legend-color': item.color }"
        >
          <span class="legend-dot"></span>
          {{ item.label }}
        </span>
      </div>
      <div class="graph-actions">
        <el-button size="small" @click="handleResetView">重置视图</el-button>
        <el-switch
          v-model="showLabels"
          active-text="标签"
          size="small"
          @change="handleToggleLabels"
        />
      </div>
    </div>

    <div v-if="!hasData" class="graph-empty">
      <el-empty description="暂无事件关系数据" :image-size="60" />
    </div>

    <div v-else ref="graphRef" class="graph-container"></div>

    <div class="graph-hint">
      💡 可拖拽节点，滚轮缩放 | 节点大小表示重要程度 | 连线表示事件关系
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import * as echarts from 'echarts'
import type { ECharts } from 'echarts'
import type { TimelineNode, TimelineRelationship, TimelinePhase } from '@/api/timeline'

const props = defineProps<{
  nodes: TimelineNode[]
  relationships: TimelineRelationship[]
  phases: TimelinePhase[]
}>()

const router = useRouter()

const graphRef = ref<HTMLElement | null>(null)
const showLabels = ref(true)
let chartInstance: ECharts | null = null
let resizeObserver: ResizeObserver | null = null

const hasData = computed(() => props.nodes.length > 0)

const legendItems = [
  { type: 'policy', label: '政策', color: '#F56C6C' },
  { type: 'reaction', label: '反应', color: '#E6A23C' },
  { type: 'breakthrough', label: '突破', color: '#67C23A' },
  { type: 'outcome', label: '结果', color: '#409EFF' },
  { type: 'background', label: '背景', color: '#909399' },
  { type: 'other', label: '其他', color: '#B0B0B0' },
]

const eventColorMap: Record<string, string> = {
  policy: '#F56C6C',
  reaction: '#E6A23C',
  breakthrough: '#67C23A',
  outcome: '#409EFF',
  background: '#909399',
  other: '#B0B0B0',
}

const eventLabelMap: Record<string, string> = {
  policy: '政策',
  reaction: '反应',
  breakthrough: '突破',
  outcome: '结果',
  background: '背景',
  other: '其他',
}

const relationTypeMap: Record<string, string> = {
  causes: '导致',
  follows: '承接',
  parallel: '并行',
}

function getNodeSymbolSize(importance: number | undefined): number {
  const imp = importance ?? 3
  return 20 + Math.min(imp * 8, 40)
}

function renderGraph() {
  if (!graphRef.value || !hasData.value) return

  const el = graphRef.value
  const width = el.clientWidth
  const height = el.clientHeight
  if (width < 200 || height < 200) return

  if (!chartInstance) {
    try {
      chartInstance = echarts.init(el)
    } catch (err) {
      console.error('[TimelineGraph] ECharts init failed', err)
      return
    }
  }

  const graphNodes = props.nodes.map((node, index) => ({
    id: node.event_id,
    name: node.event_title,
    eventTime: node.event_time,
    eventType: node.event_type || 'other',
    eventSummary: node.event_summary,
    sourceNewsId: node.source_news_id,
    symbolSize: getNodeSymbolSize(node.importance),
    x: undefined as number | undefined,
    y: undefined as number | undefined,
    itemStyle: {
      color: eventColorMap[node.event_type || 'other'] || eventColorMap.other,
      borderColor: '#fff',
      borderWidth: 2,
      shadowBlur: 8,
      shadowColor: 'rgba(0,0,0,0.15)',
    },
    label: {
      show: showLabels.value,
      position: 'bottom' as const,
      fontSize: 11,
      color: '#333',
      formatter: (p: any) => {
        const name = p.name || ''
        return name.length > 8 ? name.slice(0, 8) + '...' : name
      },
    },
  }))

  // Position nodes in time order along x-axis for initial layout
  graphNodes.forEach((node, index) => {
    node.x = 100 + index * 120
    node.y = 200 + (index % 2 === 0 ? -60 : 60)
  })

  const graphLinks = props.relationships.map((rel) => ({
    source: rel.from_id,
    target: rel.to_id,
    relationType: rel.type || 'follows',
    lineStyle: {
      width: 1.5,
      opacity: 0.6,
      curveness: 0.2,
      type: rel.type === 'causes' ? 'solid' : rel.type === 'parallel' ? 'dashed' : 'dotted' as const,
    },
    label: {
      show: showLabels.value,
      formatter: relationTypeMap[rel.type || 'follows'] || rel.type,
      fontSize: 10,
    },
  }))

  const option: any = {
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(50, 50, 50, 0.92)',
      borderColor: '#444',
      textStyle: { color: '#fff' },
      formatter: (params: any) => {
        if (params.dataType === 'node') {
          const d = params.data
          let html = `<div style="font-weight:600;margin-bottom:6px;font-size:14px;">${d.name}</div>`
          html += `<div>类型: ${eventLabelMap[d.eventType] || d.eventType}</div>`
          html += `<div>时间: ${d.eventTime}</div>`
          if (d.eventSummary) {
            html += `<div style="max-width:220px;margin-top:4px;font-size:12px;color:#ccc;">${d.eventSummary.length > 80 ? d.eventSummary.slice(0, 80) + '...' : d.eventSummary}</div>`
          }
          html += `<div style="margin-top:4px;font-size:11px;color:#aaa;">点击查看原文 →</div>`
          return html
        }
        if (params.dataType === 'edge') {
          const d = params.data
          return `<div>关系: ${relationTypeMap[d.relationType] || d.relationType}</div>`
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
          repulsion: 250,
          gravity: 0.08,
          friction: 0.6,
          edgeLength: [100, 220],
          layoutAnimation: true,
        },
        emphasis: {
          focus: 'adjacency',
          lineStyle: { width: 2.5 },
          itemStyle: { shadowBlur: 16 },
        },
        edgeSymbol: ['none', 'arrow'],
        edgeSymbolSize: [0, 8],
      },
    ],
  }

  chartInstance.setOption(option, true)
  chartInstance.resize()

  chartInstance.off('click')
  chartInstance.on('click', (params: any) => {
    if (params.dataType !== 'node') return
    const node = params.data
    if (node.sourceNewsId) {
      router.push(`/news/${node.sourceNewsId}`)
    }
  })
}

function handleResetView() {
  if (chartInstance) {
    chartInstance.dispatchAction({ type: 'restore' })
  }
}

function handleToggleLabels() {
  if (!chartInstance) return
  const option: any = {
    series: [{
      label: { show: showLabels.value },
      edgeLabel: { show: showLabels.value },
    }],
  }
  chartInstance.setOption(option)
}

function setupResizeObserver() {
  if (!graphRef.value) return
  if (resizeObserver) resizeObserver.disconnect()

  resizeObserver = new ResizeObserver((entries) => {
    if (entries.length === 0) return
    const { width, height } = entries[0].contentRect
    if (width >= 200 && height >= 200) {
      renderGraph()
      chartInstance?.resize()
    }
  })
  resizeObserver.observe(graphRef.value)
}

watch(
  () => [props.nodes, props.relationships],
  async () => {
    await nextTick()
    renderGraph()
  },
  { deep: true },
)

onMounted(async () => {
  await nextTick()
  setupResizeObserver()
  renderGraph()
  window.addEventListener('resize', () => chartInstance?.resize())
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', () => chartInstance?.resize())
  resizeObserver?.disconnect()
  resizeObserver = null
  chartInstance?.dispose()
  chartInstance = null
})
</script>

<style scoped lang="scss">
.timeline-graph {
  display: flex;
  flex-direction: column;
  gap: 12px;
  width: 100%;
  min-width: 0;
}

.graph-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
  padding: 10px 16px;
  background: var(--el-fill-color-lighter);
  border-radius: 8px;
  border: 1px solid var(--el-border-color-light);
}

.graph-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.legend-dot {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--legend-color);
  flex-shrink: 0;
}

.graph-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.graph-container {
  width: 100%;
  min-width: 320px;
  height: 480px;
  border: 1px solid var(--el-border-color-light);
  border-radius: 8px;
  background: var(--el-bg-color);
}

.graph-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 300px;
  border: 1px solid var(--el-border-color-light);
  border-radius: 8px;
}

.graph-hint {
  text-align: center;
  font-size: 12px;
  color: var(--el-text-color-secondary);
  padding: 4px 0;
}
</style>
