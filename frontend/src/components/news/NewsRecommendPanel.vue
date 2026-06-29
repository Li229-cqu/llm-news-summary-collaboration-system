<template>
  <section class="news-recommend-panel">
    <el-card class="news-recommend-panel__card" shadow="never">
      <div class="news-recommend-panel__header">
        <div>
          <h3 class="news-recommend-panel__title">热点事件脉络</h3>
          <p class="news-recommend-panel__desc">查看新闻事件的发展过程，快速了解同一话题下的时间线</p>
        </div>
      </div>

      <el-skeleton v-if="loading" animated :rows="4" />
      <el-empty v-else-if="!topics.length" description="暂无事件脉络话题" />
      <div v-else class="news-recommend-panel__list">
        <div v-for="topic in topics" :key="topic.topic_id" class="news-recommend-panel__item">
          <div class="news-recommend-panel__item-main">
            <div class="news-recommend-panel__item-title">{{ topic.topic_name }}</div>
            <div class="news-recommend-panel__item-meta">
              <span>热度 {{ topic.heat_score }}</span>
              <span>{{ topic.news_count }} 篇新闻</span>
            </div>
          </div>
          <el-button type="primary" link @click="emitOpen(topic)">查看脉络</el-button>
        </div>
      </div>
    </el-card>
  </section>
</template>

<script setup lang="ts">
import type { TimelineTopic } from '@/api/timeline'

defineProps<{
  topics: TimelineTopic[]
  loading?: boolean
}>()

const emit = defineEmits<{
  (event: 'open', topic: TimelineTopic): void
}>()

function emitOpen(topic: TimelineTopic) {
  emit('open', topic)
}
</script>

<style scoped>
.news-recommend-panel {
  display: grid;
  gap: 16px;
}

.news-recommend-panel__card {
  border-color: var(--color-border);
  border-radius: var(--border-radius-card);
}

.news-recommend-panel__card :deep(.el-card__body) {
  display: grid;
  gap: 14px;
}

.news-recommend-panel__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 14px;
}

.news-recommend-panel__title {
  margin: 0;
  color: var(--color-text-primary);
  font-size: 16px;
  font-weight: 700;
}

.news-recommend-panel__desc {
  margin: 8px 0 0;
  color: var(--color-text-secondary);
  font-size: 13px;
  line-height: 1.7;
}

.news-recommend-panel__list {
  display: grid;
  gap: 10px;
}

.news-recommend-panel__item {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 14px;
  border: 1px solid var(--color-border);
  border-radius: 14px;
  background: var(--color-bg);
}

.news-recommend-panel__item-main {
  display: grid;
  gap: 6px;
  min-width: 0;
}

.news-recommend-panel__item-title {
  overflow: hidden;
  color: var(--color-text-primary);
  font-size: 14px;
  font-weight: 600;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.news-recommend-panel__item-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 6px 10px;
  color: var(--color-text-secondary);
  font-size: 12px;
}

@media (max-width: 768px) {
  .news-recommend-panel__item {
    flex-direction: column;
  }
}
</style>
