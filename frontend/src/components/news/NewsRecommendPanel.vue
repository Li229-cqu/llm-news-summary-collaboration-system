<template>
  <section class="news-recommend-panel">
    <el-card class="news-recommend-panel__card" shadow="never">
      <div class="news-recommend-panel__ai">
        <div>
          <div class="news-recommend-panel__title">AI工具入口</div>
          <p class="news-recommend-panel__desc">一键生成新闻摘要、文章、观点分析等内容</p>
        </div>
        <el-button type="primary" @click="goToAiGenerate">立即生成</el-button>
      </div>
    </el-card>

    <el-card class="news-recommend-panel__card" shadow="never">
      <div class="news-recommend-panel__section-header">
        <div>
          <div class="news-recommend-panel__title">最近浏览</div>
          <p class="news-recommend-panel__desc">后续接入浏览历史</p>
        </div>
        <el-button text type="primary">查看全部</el-button>
      </div>

      <div v-if="recentItems.length" class="news-recommend-panel__recent-list">
        <div v-for="item in recentItems" :key="item.id" class="news-recommend-panel__recent-item">
          <span class="news-recommend-panel__recent-bullet"></span>
          <div class="news-recommend-panel__recent-text">
            <div class="news-recommend-panel__recent-title">{{ item.title }}</div>
            <div class="news-recommend-panel__recent-meta">{{ item.category_name }} · {{ item.publish_time }}</div>
          </div>
        </div>
      </div>

      <el-empty v-else description="后续接入浏览历史" />
    </el-card>
  </section>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import type { NewsCardItem } from './NewsCard.vue'

withDefaults(
  defineProps<{
    recentItems?: NewsCardItem[]
  }>(),
  {
    recentItems: () => [],
  },
)

const router = useRouter()

function goToAiGenerate() {
  router.push('/ai/title-summary')
}
</script>

<style scoped>
.news-recommend-panel {
  display: grid;
  gap: 16px;
}

.news-recommend-panel__card {
  border-color: var(--color-border);
  border-radius: var(--border-radius-card);
}

.news-recommend-panel__card :deep(.el-card__body) {
  display: grid;
  gap: 14px;
}

.news-recommend-panel__ai,
.news-recommend-panel__section-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 14px;
}

.news-recommend-panel__title {
  color: var(--color-text-primary);
  font-size: 16px;
  font-weight: 700;
}

.news-recommend-panel__desc {
  margin: 8px 0 0;
  color: var(--color-text-secondary);
  font-size: 13px;
  line-height: 1.7;
}

.news-recommend-panel__recent-list {
  display: grid;
  gap: 10px;
}

.news-recommend-panel__recent-item {
  display: flex;
  gap: 10px;
  align-items: flex-start;
}

.news-recommend-panel__recent-bullet {
  width: 8px;
  height: 8px;
  margin-top: 6px;
  border-radius: 999px;
  background: var(--color-primary);
  flex: 0 0 8px;
}

.news-recommend-panel__recent-title {
  color: var(--color-text-primary);
  font-size: 13px;
  line-height: 1.5;
}

.news-recommend-panel__recent-meta {
  margin-top: 2px;
  color: var(--color-text-secondary);
  font-size: 12px;
}

@media (max-width: 768px) {
  .news-recommend-panel__ai,
  .news-recommend-panel__section-header {
    flex-direction: column;
  }
}
</style>
