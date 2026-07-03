<template>
  <article class="news-detail-content">
    <NewsAudioPlayer :segments="speechSegments" />

    <!-- 标题优先展示 -->
    <h1 class="news-detail-content__title">{{ news.title }}</h1>

    <!-- 分类 + 话题 + 标签 -->
    <div v-if="hasMeta" class="news-detail-content__meta">
      <el-tag v-if="news.category_name" size="small" effect="plain">{{ news.category_name }}</el-tag>
      <el-tag v-if="news.topic_name" size="small" type="success" effect="light">{{ news.topic_name }}</el-tag>
      <el-tag v-for="tag in displayTags" :key="tag" size="small" type="info" effect="light">{{ tag }}</el-tag>
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
import NewsAudioPlayer from './NewsAudioPlayer.vue'
import type { SpeechSegment } from '@/composables/useSpeech'

export interface NewsDetailContentItem {
  title: string
  summary: string
  content: string
  cover_image?: string
  view_count?: number
  category_name?: string
  topic_name?: string | null
  tags?: string[]
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

const speechSegments = computed((): SpeechSegment[] => {
  const result: SpeechSegment[] = []
  let index = 0

  if (props.news.title?.trim()) {
    result.push({ id: index++, text: props.news.title.trim(), type: 'title' })
  }

  paragraphs.value.forEach((paragraph) => {
    if (paragraph.trim()) {
      result.push({ id: index++, text: paragraph.trim(), type: 'paragraph' })
    }
  })

  return result
})

const displayTags = computed(() => {
  if (!props.news.tags?.length) return []
  const categoryName = props.news.category_name
  const topicName = props.news.topic_name
  return props.news.tags.filter(t => t !== categoryName && t !== topicName && t.length >= 2)
})

const hasMeta = computed(() =>
  props.news.category_name || props.news.topic_name || displayTags.value.length > 0
)
</script>

<style scoped>
.news-detail-content {
  display: grid;
  gap: 18px;
  width: 100%;
}

.news-detail-content__title {
  margin: 0;
  color: var(--color-text-primary);
  font-size: 30px;
  line-height: 1.35;
  word-break: break-word;
  overflow-wrap: anywhere;
}

/* 分类/话题/标签 */
.news-detail-content__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.news-detail-content__cover {
  width: 100%;
  max-width: 100%;
  height: auto;
  max-height: 600px;
  border-radius: 16px;
  object-fit: contain;
  background: var(--color-bg);
}

.news-detail-content__body {
  display: grid;
  gap: 20px;
}

.news-detail-content__body :deep(img) {
  max-width: 100%;
  height: auto;
  object-fit: contain;
  border-radius: 12px;
  margin: 12px 0;
}

.news-detail-content__body p {
  margin: 0;
  color: var(--color-text-primary);
  font-size: 17px;
  line-height: 2;
  text-align: justify;
  text-indent: 2em;
}

:root.dark .news-detail-content__body p {
  color: #d1d5db;
}

@media (max-width: 768px) {
  .news-detail-content__title { font-size: 24px; }
  .news-detail-content__body p { font-size: 15px; }
}
</style>
