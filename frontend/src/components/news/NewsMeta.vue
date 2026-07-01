<template>
  <div class="news-meta">
    <span v-if="news.source" class="news-meta__source">{{ news.source }}</span>
    <span class="news-meta__sep">·</span>
    <span class="news-meta__time">{{ news.publish_time }}</span>
  </div>
</template>

<script setup lang="ts">
export interface NewsMetaItem {
  source: string
  publish_time: string
}

defineProps<{
  news: NewsMetaItem
}>()
</script>

<style scoped>
.news-meta {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 6px;
}

.news-meta__source {
  color: var(--color-text-primary);
  font-size: 14px;
  font-weight: 600;
}

.news-meta__sep {
  color: var(--color-text-secondary);
  font-size: 13px;
}

.news-meta__time {
  color: var(--color-text-secondary);
  font-size: 13px;
}
</style>
