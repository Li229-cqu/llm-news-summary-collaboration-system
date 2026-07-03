<template>
  <el-card class="timeline-node-card" shadow="never">
    <div class="timeline-node-card__header">
      <div class="timeline-node-card__time">{{ node.event_time }}</div>
      <div class="timeline-node-card__tags">
        <el-tag v-if="eventTypeTag" :type="eventTypeTag.type" size="small">{{ eventTypeTag.label }}</el-tag>
        <el-tag v-if="node.importance" type="info" size="small">
          重要性: {{ '★'.repeat(node.importance) }}
        </el-tag>
      </div>
    </div>

    <div class="timeline-node-card__title">{{ node.event_title }}</div>

    <div v-if="node.keywords?.length" class="timeline-node-card__keywords">
      <el-tag v-for="(keyword, index) in node.keywords.slice(0, 3)" :key="index" size="small" effect="plain">{{ keyword }}</el-tag>
    </div>

    <div class="timeline-node-card__footer">
      <div class="timeline-node-card__source">
        <span class="timeline-node-card__source-name">{{ node.source_name }}</span>
        <span class="timeline-node-card__source-title">{{ node.source_title }}</span>
      </div>
      <el-button v-if="node.source_news_id" type="primary" link @click="handleViewSource">查看新闻详情</el-button>
      <span v-else class="timeline-node-card__no-nav">暂无可跳转的来源新闻</span>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import type { TimelineNode } from '@/api/timeline'

const props = defineProps<{
  node: TimelineNode
}>()

const router = useRouter()

const eventTypeMap: Record<string, { label: string; type: string }> = {
  policy: { label: '政策', type: 'danger' },
  reaction: { label: '反应', type: 'warning' },
  breakthrough: { label: '突破', type: 'success' },
  outcome: { label: '结果', type: 'primary' },
  background: { label: '背景', type: 'info' },
  other: { label: '其他', type: 'default' },
}

const eventTypeTag = computed(() => {
  if (!props.node.event_type) return null
  return eventTypeMap[props.node.event_type] || eventTypeMap.other
})

function handleViewSource() {
  if (!props.node.source_news_id) return
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

.timeline-node-card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.timeline-node-card__time {
  color: var(--color-primary);
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.04em;
}

.timeline-node-card__tags {
  display: flex;
  gap: 6px;
}

.timeline-node-card__title {
  color: var(--color-text-primary);
  font-size: 16px;
  font-weight: 700;
  line-height: 1.5;
  word-break: break-word;
  overflow-wrap: anywhere;
  white-space: normal;
  overflow: visible;
}

.timeline-node-card__keywords {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
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
  color: var(--color-text-secondary);
  font-size: 12px;
  word-break: break-word;
}

.timeline-node-card__source-title {
  color: var(--color-text-primary);
}

.timeline-node-card__no-nav {
  color: var(--color-text-muted);
  font-size: 11px;
  white-space: nowrap;
}

@media (max-width: 640px) {
  .timeline-node-card__footer {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .timeline-node-card__header {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
