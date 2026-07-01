<template>
  <article
    class="news-card"
    :class="{ 'news-card--text-only': !hasImage }"
    role="button"
    tabindex="0"
    @click="handleClick"
    @keyup.enter="handleClick"
  >
    <div v-if="hasImage" class="news-card__cover">
      <img
        class="news-card__image"
        :src="news.cover_image"
        :alt="news.title"
        @error="imageFailed = true"
      />
    </div>

    <div class="news-card__content">
      <!-- 顶部分类+来源（首页精简模式下隐藏） -->
      <div v-if="!compactHome" class="news-card__topline">
        <el-tag v-if="news.category_name" size="small" effect="plain">{{ news.category_name }}</el-tag>
        <span class="news-card__source">{{ news.source }}</span>
      </div>

      <h3 class="news-card__title">{{ news.title }}</h3>
      <p class="news-card__summary">{{ news.summary }}</p>

      <div v-if="news.recommendation_reason" class="news-card__reason">
        {{ news.recommendation_reason }}
      </div>

      <!-- 英文 tags（首页精简模式下隐藏） -->
      <div v-if="!compactHome && news.tags?.length" class="news-card__tags">
        <el-tag v-for="tag in news.tags" :key="tag" size="small" effect="light">
          {{ tag }}
        </el-tag>
      </div>

      <div class="news-card__meta">
        <!-- 首页精简模式：底部显示来源 -->
        <span v-if="compactHome && news.source" class="news-card__meta-source">{{ news.source }}</span>
        <span>{{ news.publish_time }}</span>
        <span>阅读 {{ news.view_count }}</span>
        <span>评论 {{ news.comment_count }}</span>
        <span>点赞 {{ news.like_count }}</span>
      </div>
    </div>
  </article>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'

export interface NewsCardItem {
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

const props = defineProps<{
  news: NewsCardItem
  /** 首页精简模式：隐藏顶部分类标签、来源、英文 tags */
  compactHome?: boolean
}>()

const emit = defineEmits<{
  (event: 'click', news: NewsCardItem): void
}>()

const imageFailed = ref(false)
const hasImage = computed(() => Boolean(props.news.cover_image && !imageFailed.value))

watch(
  () => props.news.cover_image,
  () => {
    imageFailed.value = false
  },
)

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

.news-card--text-only {
  grid-template-columns: minmax(0, 1fr);
  min-height: 0;
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

.news-card--text-only .news-card__summary {
  -webkit-line-clamp: 3;
}

.news-card__reason {
  display: flex;
  align-items: center;
  min-height: 26px;
  padding: 4px 8px;
  margin-top: 6px;
  border-radius: 4px;
  background: color-mix(in srgb, var(--color-primary) 8%, var(--color-bg));
  color: var(--color-primary);
  font-size: 12px;
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
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

/* 首页精简模式下来源文字轻强调 */
.news-card__meta-source {
  color: var(--color-text-primary);
  font-weight: 500;
}

.news-card__meta-source::after {
  content: '·';
  margin-left: 8px;
  color: var(--color-text-secondary);
  font-weight: 400;
}

@media (max-width: 860px) {
  .news-card {
    grid-template-columns: 1fr;
  }
}
</style>
