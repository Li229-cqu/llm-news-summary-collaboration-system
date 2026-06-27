<template>
  <div class="news-list">
    <el-skeleton v-if="loading" animated :rows="6" />
    <el-empty v-else-if="!list.length" :description="emptyText" />
    <div v-else class="news-list__grid">
      <NewsCard
        v-for="item in list"
        :key="item.id"
        :news="item"
        @click="handleCardClick"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import NewsCard from './NewsCard.vue'

export interface NewsListItem {
  id: number
  title: string
  summary: string
  category_name: string
  source: string
  author?: string
  editor?: string
  publish_time: string
  view_count: number
  like_count: number
  comment_count: number
  favorite_count?: number
  status?: number
  cover_image?: string
  tags?: string[]
  recommendation_reason?: string
  recommendation_score?: number
}

defineProps<{
  list: NewsListItem[]
  loading?: boolean
  emptyText?: string
}>()

const router = useRouter()

function handleCardClick(news: NewsListItem) {
  router.push(`/news/${news.id}`)
}
</script>

<style scoped>
.news-list {
  min-width: 0;
}

.news-list__grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

@media (max-width: 1200px) {
  .news-list__grid {
    grid-template-columns: 1fr;
  }
}
</style>
