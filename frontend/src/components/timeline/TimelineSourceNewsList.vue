<template>
  <section class="timeline-source-list">
    <div class="timeline-source-list__header">
      <h3>来源新闻</h3>
      <span>同一话题下的相关新闻</span>
    </div>

    <el-empty v-if="!list.length" description="暂无来源新闻" />

    <div v-else class="timeline-source-list__items">
      <button
        v-for="item in list"
        :key="item.id"
        type="button"
        class="timeline-source-list__item"
        @click="handleClick(item.id)"
      >
        <div class="timeline-source-list__title">{{ item.title }}</div>
        <div class="timeline-source-list__meta">
          <span>{{ item.source }}</span>
          <span>{{ item.publish_time }}</span>
        </div>
      </button>
    </div>
  </section>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import type { TimelineNewsItem } from '@/api/timeline'

defineProps<{
  list: TimelineNewsItem[]
}>()

const router = useRouter()

function handleClick(newsId: number) {
  router.push(`/news/${newsId}`)
}
</script>

<style scoped>
.timeline-source-list {
  display: grid;
  gap: 14px;
}

.timeline-source-list__header {
  display: grid;
  gap: 4px;
}

.timeline-source-list__header h3 {
  margin: 0;
  color: var(--color-text-primary);
  font-size: 18px;
}

.timeline-source-list__header span {
  color: var(--color-text-secondary);
  font-size: 13px;
}

.timeline-source-list__items {
  display: grid;
  gap: 10px;
}

.timeline-source-list__item {
  display: grid;
  gap: 8px;
  padding: 12px 14px;
  border: 1px solid var(--color-border);
  border-radius: 14px;
  background: var(--color-bg-card);
  color: inherit;
  text-align: left;
  cursor: pointer;
  transition:
    transform 0.16s ease,
    border-color 0.16s ease,
    box-shadow 0.16s ease;
}

.timeline-source-list__item:hover {
  border-color: color-mix(in srgb, var(--color-primary) 30%, var(--color-border));
  box-shadow: 0 8px 16px rgb(15 23 42 / 8%);
  transform: translateY(-1px);
}

.timeline-source-list__title {
  color: var(--color-text-primary);
  font-size: 14px;
  font-weight: 600;
  line-height: 1.5;
  word-break: break-word;
  overflow-wrap: anywhere;
}

.timeline-source-list__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 6px 10px;
  color: var(--color-text-secondary);
  font-size: 12px;
}
</style>
