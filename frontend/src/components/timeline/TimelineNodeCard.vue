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
    <p class="timeline-node-card__summary">{{ node.event_summary }}</p>

    <div v-if="node.event_detail" class="timeline-node-card__detail">
      <div class="detail-toggle" @click="showDetail = !showDetail">
        <span>{{ showDetail ? '收起详情' : '展开详情' }}</span>
        <el-icon :size="14">
          <component :is="showDetail ? ArrowUp : ArrowDown" />
        </el-icon>
      </div>
      <div v-if="showDetail" class="detail-content">
        {{ node.event_detail }}
      </div>
    </div>

    <div v-if="node.keywords?.length" class="timeline-node-card__keywords">
      <el-tag v-for="(keyword, index) in node.keywords" :key="index" size="small" effect="plain">{{ keyword }}</el-tag>
    </div>

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
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowUp, ArrowDown } from '@element-plus/icons-vue'
import type { TimelineNode } from '@/api/timeline'

const props = defineProps<{
  node: TimelineNode
}>()

const showDetail = ref(false)

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
}

.timeline-node-card__summary {
  margin: 0;
  color: var(--color-text-secondary);
  font-size: 14px;
  line-height: 1.8;
}

.timeline-node-card__detail {
  margin-top: 4px;
}

.detail-toggle {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: var(--color-primary);
  cursor: pointer;
}

.detail-content {
  margin-top: 8px;
  padding: 12px;
  background: var(--color-bg);
  border-radius: 8px;
  font-size: 13px;
  color: var(--color-text-secondary);
  line-height: 1.8;
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
  
  .timeline-node-card__header {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
