<template>
  <el-card class="timeline-node-card" shadow="never">
    <div class="timeline-node-card__time">{{ node.event_time }}</div>
    <div class="timeline-node-card__title">{{ node.event_title }}</div>
    <p class="timeline-node-card__summary">{{ node.event_summary }}</p>

    <div class="timeline-node-card__footer">
      <div class="timeline-node-card__source">
        <span class="timeline-node-card__source-name">{{ node.source_name }}</span>
        <span class="timeline-node-card__source-title">{{ node.source_title }}</span>
      </div>
      <el-button type="primary" link @click="handleViewSource">查看原文</el-button>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import type { TimelineNode } from '@/api/timeline'

const props = defineProps<{
  node: TimelineNode
}>()

const router = useRouter()

function handleViewSource() {
  router.push(`/news/${props.node.source_news_id}`)
}
</script>

<style scoped>
.timeline-node-card {
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-card);
  background: var(--color-bg-card);
}

.timeline-node-card :deep(.el-card__body) {
  display: grid;
  gap: 10px;
  padding: 16px;
}

.timeline-node-card__time {
  color: var(--color-primary);
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.04em;
}

.timeline-node-card__title {
  color: var(--color-text-primary);
  font-size: 16px;
  font-weight: 700;
  line-height: 1.5;
}

.timeline-node-card__summary {
  margin: 0;
  color: var(--color-text-secondary);
  font-size: 14px;
  line-height: 1.8;
}

.timeline-node-card__footer {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 12px;
}

.timeline-node-card__source {
  display: grid;
  gap: 2px;
  min-width: 0;
}

.timeline-node-card__source-name,
.timeline-node-card__source-title {
  overflow: hidden;
  color: var(--color-text-secondary);
  font-size: 12px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.timeline-node-card__source-title {
  color: var(--color-text-primary);
}

@media (max-width: 640px) {
  .timeline-node-card__footer {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
