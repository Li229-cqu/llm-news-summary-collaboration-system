<template>
  <aside class="news-detail-side-panel">
    <el-card class="news-detail-side-panel__card" shadow="never">
      <div class="news-detail-side-panel__timeline">
        <div class="news-detail-side-panel__title">事件脉络</div>
        <p class="news-detail-side-panel__desc">
          {{ timelineDescription }}
        </p>
        <el-button
          :type="isTimelineAvailable ? 'primary' : 'info'"
          :disabled="!isTimelineAvailable"
          @click="handleViewTimeline"
        >
          {{ timelineButtonText }}
        </el-button>
      </div>
    </el-card>

    <el-card class="news-detail-side-panel__card" shadow="never">
      <div class="news-detail-side-panel__ai">
        <div class="news-detail-side-panel__title">AI 工具入口</div>
        <p class="news-detail-side-panel__desc">点击可跳转到 AI 标题和摘要生成页</p>
        <el-button type="primary" @click="goToAiGenerate">用 AI 生成标题和摘要</el-button>
      </div>
    </el-card>

    <el-card class="news-detail-side-panel__card" shadow="never">
      <RelatedNewsList title="相关文章" :list="relatedNews" />
    </el-card>

    <el-card class="news-detail-side-panel__card" shadow="never">
      <RelatedNewsList title="推荐阅读" :list="recommendedNews" />
    </el-card>
  </aside>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import RelatedNewsList, { type RelatedNewsItem } from './RelatedNewsList.vue'

const props = defineProps<{
  relatedNews: RelatedNewsItem[]
  recommendedNews: RelatedNewsItem[]
  timelineTopicId?: number | null
  timelineTopicName?: string
  timelineNewsCount?: number
}>()

const emit = defineEmits<{
  (event: 'viewTimeline'): void
}>()

const router = useRouter()

const hasTimelineTopic = computed(() => !!props.timelineTopicId)
const isTimelineAvailable = computed(() => hasTimelineTopic.value && (props.timelineNewsCount ?? 0) >= 2)
const timelineDescription = computed(() => {
  if (!hasTimelineTopic.value) return '当前新闻暂无事件脉络'
  if ((props.timelineNewsCount ?? 0) <= 1) return '新闻数量不足，无法生成脉络'
  return `查看当前新闻所属话题的时间线脉络（共 ${props.timelineNewsCount} 条新闻）`
})
const timelineButtonText = computed(() => {
  if (!hasTimelineTopic.value) return '当前新闻暂无事件脉络'
  if ((props.timelineNewsCount ?? 0) <= 1) return '新闻数量不足'
  return `查看本事件脉络（共 ${props.timelineNewsCount} 条新闻）`
})

function goToAiGenerate() {
  router.push('/ai/title-summary')
}

function handleViewTimeline() {
  if (!props.timelineTopicId) {
    return
  }

  emit('viewTimeline')
}
</script>

<style scoped>
.news-detail-side-panel {
  display: grid;
  gap: 16px;
}

.news-detail-side-panel__card {
  border-color: var(--color-border);
  border-radius: var(--border-radius-card);
}

.news-detail-side-panel__card :deep(.el-card__body) {
  display: grid;
  gap: 14px;
}

.news-detail-side-panel__ai,
.news-detail-side-panel__timeline {
  display: grid;
  gap: 10px;
}

.news-detail-side-panel__title {
  color: var(--color-text-primary);
  font-size: 16px;
  font-weight: 700;
}

.news-detail-side-panel__desc {
  margin: 0;
  color: var(--color-text-secondary);
  font-size: 13px;
  line-height: 1.7;
}
</style>
