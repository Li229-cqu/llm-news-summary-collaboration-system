<template>
  <article class="news-card" role="button" tabindex="0" @click="handleClick" @keyup.enter="handleClick">
    <div class="news-card__cover">
      <img v-if="news.cover_image" class="news-card__image" :src="news.cover_image" :alt="news.title" />
      <div v-else class="news-card__placeholder">
        <span>暂无封面</span>
      </div>
    </div>

    <div class="news-card__content">
      <div class="news-card__topline">
        <el-tag v-if="news.category_name" size="small" effect="plain">{{ news.category_name }}</el-tag>
        <span class="news-card__source">{{ news.source }}</span>
      </div>

      <h3 class="news-card__title">{{ news.title }}</h3>
      <p class="news-card__summary">{{ news.summary }}</p>

      <div v-if="news.tags?.length" class="news-card__tags">
        <el-tag v-for="tag in news.tags" :key="tag" size="small" effect="light">
          {{ tag }}
        </el-tag>
      </div>

      <div class="news-card__meta">
        <span>{{ news.publish_time }}</span>
        <span>阅读 {{ news.view_count }}</span>
        <span>评论 {{ news.comment_count }}</span>
        <span>点赞 {{ news.like_count }}</span>
      </div>
    </div>
  </article>
</template>

<script setup lang="ts">
export interface NewsCardItem {
  id: number
  title: string
  summary: string
  category_name: string
  source: string
  author: string
  publish_time: string
  view_count: number
  like_count: number
  comment_count: number
  cover_image?: string
  tags?: string[]
}

const props = defineProps<{
  news: NewsCardItem
}>()

const emit = defineEmits<{
  (event: 'click', news: NewsCardItem): void
}>()

function handleClick() {
  emit('click', props.news)
}
</script>

<style scoped>
.news-card {
  display: grid;
  grid-template-columns: 178px minmax(0, 1fr);
  gap: 16px;
  min-height: 182px;
  padding: 16px;
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-card);
  background: var(--color-bg-card);
  box-shadow: 0 6px 18px rgb(15 23 42 / 5%);
  cursor: pointer;
  transition:
    transform 0.18s ease,
    box-shadow 0.18s ease,
    border-color 0.18s ease;
}

.news-card:hover,
.news-card:focus-visible {
  border-color: color-mix(in srgb, var(--color-primary) 35%, var(--color-border));
  box-shadow: 0 10px 22px rgb(15 23 42 / 10%);
  transform: translateY(-2px);
  outline: none;
}

.news-card__cover {
  overflow: hidden;
  min-height: 150px;
  border-radius: calc(var(--border-radius-card) - 4px);
  background: linear-gradient(135deg, color-mix(in srgb, var(--color-primary) 16%, var(--color-bg-card)), var(--color-bg));
}

.news-card__image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.news-card__placeholder {
  display: grid;
  place-items: center;
  min-height: 150px;
  color: var(--color-text-secondary);
  font-size: 13px;
  letter-spacing: 0.08em;
  background:
    linear-gradient(135deg, color-mix(in srgb, var(--color-primary) 8%, var(--color-bg-card)), var(--color-bg));
}

.news-card__content {
  display: grid;
  gap: 10px;
  min-width: 0;
}

.news-card__topline {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
}

.news-card__source {
  color: var(--color-text-secondary);
  font-size: 12px;
}

.news-card__title {
  margin: 0;
  color: var(--color-text-primary);
  font-size: 18px;
  line-height: 1.45;
}

.news-card__summary {
  display: -webkit-box;
  overflow: hidden;
  margin: 0;
  color: var(--color-text-secondary);
  font-size: 14px;
  line-height: 1.72;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.news-card__tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.news-card__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 10px 16px;
  margin-top: auto;
  color: var(--color-text-secondary);
  font-size: 12px;
}

@media (max-width: 860px) {
  .news-card {
    grid-template-columns: 1fr;
  }
}
</style>
