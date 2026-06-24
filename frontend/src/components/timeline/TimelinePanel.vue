<template>
  <div class="timeline-panel">
    <el-card class="timeline-panel__overview" shadow="never">
      <div class="timeline-panel__overview-top">
        <div>
          <div class="timeline-panel__label">话题概览</div>
          <h2 class="timeline-panel__title">{{ topicName }}</h2>
        </div>

        <el-tag type="primary" effect="plain">
          {{ timelineData.source === 'cache' ? '缓存时间线' : timelineData.source === 'ai-service' ? 'AI 生成' : '本地 mock' }}
        </el-tag>
      </div>

      <p class="timeline-panel__summary">{{ summaryText }}</p>

      <div class="timeline-panel__metrics">
        <div class="timeline-panel__metric">
          <span>热度</span>
          <strong>{{ heatScore }}</strong>
        </div>
        <div class="timeline-panel__metric">
          <span>节点数</span>
          <strong>{{ timelineData.timeline.length }}</strong>
        </div>
      </div>
    </el-card>

    <div class="timeline-panel__body">
      <section class="timeline-panel__timeline">
        <div class="timeline-panel__section-header">
          <h3>事件脉络</h3>
          <span>按时间顺序展示同一话题的关键节点</span>
        </div>

        <div v-if="!timelineData.timeline.length" class="timeline-panel__empty">
          <el-empty description="暂无时间线节点" />
        </div>

        <el-timeline v-else class="timeline-panel__timeline-list">
          <el-timeline-item
            v-for="node in timelineData.timeline"
            :key="node.event_id"
            :timestamp="node.event_time"
            placement="top"
          >
            <TimelineNodeCard :node="node" />
          </el-timeline-item>
        </el-timeline>
      </section>

      <aside class="timeline-panel__sources">
        <TimelineSourceNewsList :list="sourceNewsList" />
      </aside>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { TimelineNewsItem, TimelineResponse } from '@/api/timeline'
import TimelineNodeCard from './TimelineNodeCard.vue'
import TimelineSourceNewsList from './TimelineSourceNewsList.vue'

const props = defineProps<{
  timelineData: TimelineResponse
  sourceNewsList: TimelineNewsItem[]
}>()

const topicName = computed(() => props.timelineData.topic_name || '事件脉络')
const summaryText = computed(() => {
  const firstNode = props.timelineData.timeline[0]
  return firstNode?.event_summary || '该话题下的事件脉络会按时间顺序展示关键节点。'
})
const heatScore = computed(() => props.timelineData.timeline.length * 10 || 0)
</script>

<style scoped>
.timeline-panel {
  display: grid;
  gap: 18px;
}

.timeline-panel__overview {
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-card);
  background: var(--color-bg-card);
}

.timeline-panel__overview :deep(.el-card__body) {
  display: grid;
  gap: 14px;
  padding: 20px;
}

.timeline-panel__overview-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.timeline-panel__label {
  margin-bottom: 4px;
  color: var(--color-text-secondary);
  font-size: 12px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.timeline-panel__title {
  margin: 0;
  color: var(--color-text-primary);
  font-size: 24px;
  line-height: 1.4;
}

.timeline-panel__summary {
  margin: 0;
  color: var(--color-text-secondary);
  font-size: 14px;
  line-height: 1.9;
}

.timeline-panel__metrics {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.timeline-panel__metric {
  display: grid;
  gap: 4px;
  min-width: 120px;
  padding: 12px 14px;
  border: 1px solid var(--color-border);
  border-radius: 14px;
  background: var(--color-bg);
}

.timeline-panel__metric span {
  color: var(--color-text-secondary);
  font-size: 12px;
}

.timeline-panel__metric strong {
  color: var(--color-text-primary);
  font-size: 18px;
}

.timeline-panel__body {
  display: grid;
  grid-template-columns: minmax(0, 1.3fr) minmax(280px, 0.7fr);
  gap: 20px;
  align-items: start;
}

.timeline-panel__timeline,
.timeline-panel__sources {
  min-width: 0;
}

.timeline-panel__section-header {
  display: grid;
  gap: 4px;
  margin-bottom: 14px;
}

.timeline-panel__section-header h3 {
  margin: 0;
  color: var(--color-text-primary);
  font-size: 18px;
}

.timeline-panel__section-header span {
  color: var(--color-text-secondary);
  font-size: 13px;
}

.timeline-panel__timeline-list {
  padding-left: 8px;
}

.timeline-panel__empty {
  padding: 16px 0;
}

@media (max-width: 1024px) {
  .timeline-panel__body {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .timeline-panel__overview-top {
    flex-direction: column;
  }

  .timeline-panel__title {
    font-size: 20px;
  }
}
</style>
