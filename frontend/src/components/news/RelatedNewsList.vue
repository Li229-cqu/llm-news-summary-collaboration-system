<template>
  <section class="related-news-list">
    <div class="related-news-list__header">
      <h3>{{ title }}</h3>
    </div>

    <el-skeleton v-if="loading" animated :rows="4" />
    <el-empty v-else-if="!list.length" description="暂无内容" />
    <div v-else class="related-news-list__items">
      <article
        v-for="item in list"
        :key="item.id"
        class="related-news-list__item"
        @click="handleClick(item.id)"
      >
        <div class="related-news-list__title">{{ item.title }}</div>
        <div class="related-news-list__meta">
          <span>{{ item.source }}</span>
          <span class="related-news-list__tag" v-if="item.recommend_source === 'related'">相关推荐</span>
          <span class="related-news-list__tag related-news-list__tag--hot" v-if="item.recommend_source === 'hot'">热门推荐</span>
          <span>阅读 {{ item.view_count }}</span>
        </div>
      </article>
    </div>
  </section>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'

export interface RelatedNewsItem {
  id: number
  title: string
  source: string
  view_count: number
  recommend_source?: 'related' | 'hot'
}

defineProps<{
  title: string
  list: RelatedNewsItem[]
  loading?: boolean
}>()

const router = useRouter()

function handleClick(newsId: number) {
  router.push(`/news/${newsId}`)
}
</script>

<style scoped>
.related-news-list {
  display: grid;
  gap: 14px;
}

.related-news-list__header h3 {
  margin: 0;
  color: var(--color-text-primary);
  font-size: 16px;
}

.related-news-list__items {
  display: grid;
  gap: 10px;
}

.related-news-list__item {
  display: grid;
  gap: 8px;
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

.related-news-list__item:hover {
  border-color: color-mix(in srgb, var(--color-primary) 30%, var(--color-border));
  box-shadow: 0 8px 16px rgb(15 23 42 / 8%);
  transform: translateY(-1px);
}

.related-news-list__title {
  overflow: hidden;
  color: var(--color-text-primary);
  font-size: 14px;
  font-weight: 600;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.related-news-list__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 12px;
  color: var(--color-text-secondary);
  font-size: 12px;
}

.related-news-list__tag {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 500;
  color: var(--color-primary);
  background: var(--color-primary-soft);
  border: 1px solid color-mix(in srgb, var(--color-primary) 18%, var(--color-border));
}

.related-news-list__tag--hot {
  color: #d92d20;
  background: #fff1f0;
  border-color: #fecaca;
}
</style>
