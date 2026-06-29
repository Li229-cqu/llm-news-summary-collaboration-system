<template>
  <section class="news-hot-list">
    <div class="news-hot-list__header">
      <div>
        <h3>新闻热榜 Top10</h3>
        <span>根据浏览、点赞、收藏和评论综合排序</span>
      </div>
      <el-button link type="primary" @click="handleRefresh">换一换</el-button>
    </div>

    <el-skeleton v-if="loading" animated :rows="6" />
    <el-empty v-else-if="!list.length" description="暂无热榜数据" />
    <ol v-else class="news-hot-list__items">
      <li
        v-for="item in list"
        :key="item.id"
        class="news-hot-list__item"
        :class="`news-hot-list__item--rank-${item.rank}`"
        @click="handleClick(item.id)"
      >
        <div class="news-hot-list__rank">{{ item.rank }}</div>
        <div class="news-hot-list__content">
          <div class="news-hot-list__title">{{ item.title }}</div>
          <div class="news-hot-list__meta">
            <span>{{ item.category_name }}</span>
            <span>热度 {{ item.heat_score ?? item.view_count }}</span>
            <span>阅读 {{ item.view_count }}</span>
            <span>评论 {{ item.comment_count }}</span>
          </div>
        </div>
      </li>
    </ol>
  </section>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'

export interface HotNewsItem {
  id: number
  title: string
  category_name: string
  source: string
  view_count: number
  comment_count: number
  like_count?: number
  favorite_count?: number
  cover_image?: string
  publish_time?: string
  heat_score?: number
  rank: number
}

defineProps<{
  list: HotNewsItem[]
  loading?: boolean
}>()

const emit = defineEmits<{
  (event: 'refresh'): void
}>()

const router = useRouter()

function handleClick(newsId: number) {
  router.push(`/news/${newsId}`)
}

function handleRefresh() {
  emit('refresh')
}
</script>

<style scoped>
.news-hot-list {
  display: grid;
  gap: 14px;
}

.news-hot-list__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.news-hot-list__header h3 {
  margin: 0;
  color: var(--color-text-primary);
  font-size: 18px;
}

.news-hot-list__header span {
  color: var(--color-text-secondary);
  font-size: 13px;
}

.news-hot-list__items {
  display: grid;
  gap: 10px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.news-hot-list__item {
  display: grid;
  grid-template-columns: 32px minmax(0, 1fr);
  gap: 12px;
  padding: 12px 14px;
  border: 1px solid var(--color-border);
  border-radius: 14px;
  background: var(--color-bg-card);
  cursor: pointer;
  transition:
    transform 0.16s ease,
    border-color 0.16s ease,
    box-shadow 0.16s ease;
}

.news-hot-list__item:hover {
  border-color: color-mix(in srgb, var(--color-primary) 30%, var(--color-border));
  box-shadow: 0 8px 16px rgb(15 23 42 / 8%);
  transform: translateY(-1px);
}

.news-hot-list__item--rank-1 {
  border-color: color-mix(in srgb, #f59e0b 40%, var(--color-border));
  background: linear-gradient(135deg, color-mix(in srgb, #f59e0b 10%, var(--color-bg-card)), var(--color-bg-card));
}

.news-hot-list__item--rank-2 {
  border-color: color-mix(in srgb, #94a3b8 40%, var(--color-border));
}

.news-hot-list__item--rank-3 {
  border-color: color-mix(in srgb, #c084fc 38%, var(--color-border));
}

.news-hot-list__rank {
  display: grid;
  place-items: center;
  width: 32px;
  height: 32px;
  border-radius: 999px;
  background: var(--color-primary-soft);
  color: var(--color-primary);
  font-weight: 700;
}

.news-hot-list__item--rank-1 .news-hot-list__rank {
  background: color-mix(in srgb, #f59e0b 18%, white);
  color: #b45309;
}

.news-hot-list__item--rank-2 .news-hot-list__rank {
  background: color-mix(in srgb, #94a3b8 18%, white);
  color: #475569;
}

.news-hot-list__item--rank-3 .news-hot-list__rank {
  background: color-mix(in srgb, #c084fc 18%, white);
  color: #7c3aed;
}

.news-hot-list__content {
  min-width: 0;
}

.news-hot-list__title {
  overflow: hidden;
  color: var(--color-text-primary);
  font-size: 14px;
  font-weight: 600;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.news-hot-list__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 6px 10px;
  margin-top: 6px;
  color: var(--color-text-secondary);
  font-size: 12px;
}
</style>
