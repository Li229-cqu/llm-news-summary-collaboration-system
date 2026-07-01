<template>
  <article class="news-detail-content">
    <!-- 标题优先展示 -->
    <h1 class="news-detail-content__title">{{ news.title }}</h1>

    <!-- 摘要卡片（标题之后） -->
    <div v-if="news.summary" class="news-detail-content__summary-block">
      <p class="news-detail-content__summary-label">摘要</p>
      <p class="news-detail-content__summary">{{ news.summary }}</p>
    </div>

    <!-- 封面图 -->
    <img
      v-if="news.cover_image && !imageFailed"
      class="news-detail-content__cover"
      :src="news.cover_image"
      :alt="news.title"
      @error="imageFailed = true"
    />

    <!-- 正文 -->
    <div class="news-detail-content__body">
      <p v-for="(paragraph, index) in paragraphs" :key="index">
        {{ paragraph }}
      </p>
    </div>
  </article>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'

export interface NewsDetailContentItem {
  title: string
  summary: string
  content: string
  cover_image?: string
  view_count?: number
}

const props = defineProps<{
  news: NewsDetailContentItem
}>()

const imageFailed = ref(false)

watch(
  () => props.news.cover_image,
  () => {
    imageFailed.value = false
  },
)

const paragraphs = computed(() =>
  props.news.content
    .split(/\n+/)
    .map((paragraph) => paragraph.trim())
    .filter(Boolean),
)
</script>

<style scoped>
.news-detail-content {
  display: grid;
  gap: 18px;
  width: 100%;
}

/* 标题 */
.news-detail-content__title {
  margin: 0;
  color: var(--color-text-primary);
  font-size: 30px;
  line-height: 1.35;
}

/* 摘要卡片（标题之后，左侧红色竖线） */
.news-detail-content__summary-block {
  display: grid;
  gap: 8px;
  padding: 14px 18px;
  border-left: 4px solid var(--color-primary);
  border-radius: 0 14px 14px 0;
  background: var(--color-primary-soft);
}

.news-detail-content__summary-label {
  margin: 0;
  color: var(--color-primary);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.06em;
}

.news-detail-content__summary {
  margin: 0;
  color: var(--color-text-primary);
  font-size: 15px;
  line-height: 1.85;
}

/* 封面图 */
.news-detail-content__cover {
  width: 100%;
  max-height: 420px;
  border-radius: 16px;
  object-fit: cover;
  background: var(--color-bg);
}

/* 正文：自然占满卡片 */
.news-detail-content__body {
  display: grid;
  gap: 20px;
}

.news-detail-content__body p {
  margin: 0;
  color: #374151;
  font-size: 17px;
  line-height: 2;
  text-align: justify;
  text-indent: 2em;
}

/* 暗色模式 */
:root.dark .news-detail-content__summary-block {
  background: color-mix(in srgb, var(--color-primary) 15%, #1f2933);
}

:root.dark .news-detail-content__body p {
  color: #d1d5db;
}

@media (max-width: 768px) {
  .news-detail-content__title {
    font-size: 24px;
  }

  .news-detail-content__body p {
    font-size: 15px;
  }
}
</style>
