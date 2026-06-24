<template>
  <aside class="news-detail-side-panel">
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
import { useRouter } from 'vue-router'
import RelatedNewsList, { type RelatedNewsItem } from './RelatedNewsList.vue'

defineProps<{
  relatedNews: RelatedNewsItem[]
  recommendedNews: RelatedNewsItem[]
}>()

const router = useRouter()

function goToAiGenerate() {
  router.push('/ai/title-summary')
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

.news-detail-side-panel__ai {
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
