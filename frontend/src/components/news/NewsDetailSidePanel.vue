<template>
  <aside class="news-detail-side-panel">
    <el-card class="news-detail-side-panel__card" shadow="never">
      <div class="news-detail-side-panel__timeline">
        <div class="news-detail-side-panel__title">事件脉络</div>
        <p class="news-detail-side-panel__desc">
          {{ timelineTopicId ? '查看当前新闻所属话题的时间线脉络' : '当前新闻暂无事件脉络' }}
        </p>
        <el-button
          :type="timelineTopicId ? 'primary' : 'info'"
          :disabled="!timelineTopicId"
          @click="handleViewTimeline"
        >
          {{ timelineTopicId ? '查看本事件脉络' : '当前新闻暂无事件脉络' }}
        </el-button>
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
import RelatedNewsList, { type RelatedNewsItem } from './RelatedNewsList.vue'

const props = defineProps<{
  relatedNews: RelatedNewsItem[]
  recommendedNews: RelatedNewsItem[]
  timelineTopicId?: number | null
  timelineTopicName?: string
}>()

const emit = defineEmits<{
  (event: 'viewTimeline'): void
}>()

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
