<template>
  <article class="news-detail-content">
    <div class="news-detail-content__summary-block">
      <p class="news-detail-content__summary-label">摘要</p>
      <p v-if="news.summary" class="news-detail-content__summary">
        {{ news.summary }}
      </p>
    </div>

    <h1 class="news-detail-content__title">{{ news.title }}</h1>

    <div class="news-detail-content__body">
      <p v-for="(paragraph, index) in paragraphs" :key="index">
        {{ paragraph }}
      </p>
    </div>
  </article>
</template>

<script setup lang="ts">
import { computed } from 'vue'

export interface NewsDetailContentItem {
  title: string
  summary: string
  content: string
}

const props = defineProps<{
  news: NewsDetailContentItem
}>()

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
}

.news-detail-content__summary-block {
  display: grid;
  gap: 10px;
  padding: 16px 18px;
  border-radius: 16px;
  background: var(--color-primary-soft);
}

.news-detail-content__summary-label {
  margin: 0;
  color: var(--color-primary);
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.news-detail-content__summary {
  margin: 0;
  color: var(--color-text-primary);
  font-size: 14px;
  line-height: 1.85;
}

.news-detail-content__title {
  margin: 0;
  color: var(--color-text-primary);
  font-size: 30px;
  line-height: 1.35;
}

.news-detail-content__body {
  display: grid;
  gap: 16px;
}

.news-detail-content__body p {
  margin: 0;
  color: var(--color-text-primary);
  font-size: 16px;
  line-height: 2;
  text-align: justify;
}

@media (max-width: 768px) {
  .news-detail-content__title {
    font-size: 24px;
  }
}
</style>
