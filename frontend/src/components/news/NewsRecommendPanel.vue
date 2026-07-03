<template>
  <section class="news-recommend-panel">
    <el-card class="news-recommend-panel__card" shadow="never">
      <!-- 标题区：红色竖线 + 标题 + 副标题 -->
      <div class="news-recommend-panel__header">
        <span class="news-recommend-panel__header-accent" aria-hidden="true"></span>
        <div class="news-recommend-panel__header-text">
          <h3 class="news-recommend-panel__title">热点事件脉络</h3>
          <p class="news-recommend-panel__desc">AI 聚合同一话题下的多篇新闻，提炼事件关键进展</p>
        </div>
      </div>

      <!-- 加载态：简洁骨架屏 -->
      <template v-if="loading">
        <div class="news-recommend-panel__skeleton">
          <div v-for="n in 3" :key="n" class="news-recommend-panel__skeleton-item">
            <el-skeleton animated>
              <template #template>
                <div class="skeleton-line skeleton-line--title"></div>
                <div class="skeleton-line skeleton-line--text"></div>
                <div class="skeleton-line skeleton-line--meta"></div>
              </template>
            </el-skeleton>
          </div>
        </div>
      </template>

      <!-- 空态 -->
      <el-empty v-else-if="!topics.length" description="暂无可追踪热点事件" :image-size="56" />

      <!-- 话题卡片列表 -->
      <div v-else class="news-recommend-panel__list">
        <article
          v-for="topic in topics"
          :key="topic.topic_id"
          class="news-recommend-panel__item"
        >
          <!-- 卡片主体信息 -->
          <div class="news-recommend-panel__item-body">
            <h4 class="news-recommend-panel__item-title">{{ topic.topic_name }}</h4>

            <p v-if="topic.summary" class="news-recommend-panel__item-summary">{{ topic.summary }}</p>

            <!-- 热度 + 新闻数 -->
            <div class="news-recommend-panel__item-meta">
              <span class="news-recommend-panel__item-meta-pill">热度 {{ topic.heat_score }}</span>
              <span class="news-recommend-panel__item-meta-pill">{{ topic.news_count }} 篇新闻</span>
            </div>

            <!-- 关键词标签 -->
            <div v-if="topic.keyword_list?.length" class="news-recommend-panel__item-keywords">
              <span
                v-for="(keyword, idx) in topic.keyword_list.slice(0, 3)"
                :key="idx"
                class="news-recommend-panel__item-keyword"
              >{{ keyword }}</span>
            </div>

            <!-- 事件节点预览提示（纯静态视觉，不请求真实节点） -->
            <div class="news-recommend-panel__item-stages">
              <span class="stage-marker"></span> 事件发生
              <span class="stage-marker stage-marker--middle"></span> 发展跟进
              <span class="stage-marker stage-marker--latest"></span> 最新动态
            </div>
          </div>

          <!-- 操作入口 -->
          <div class="news-recommend-panel__item-action" @click.stop="emitOpen(topic)">
            <span class="news-recommend-panel__item-action-text">展开脉络</span>
            <span class="news-recommend-panel__item-action-arrow">→</span>
          </div>
        </article>
      </div>
    </el-card>
  </section>
</template>

<script setup lang="ts">
import type { TimelineTopic } from '@/api/timeline'

defineProps<{
  topics: TimelineTopic[]
  loading?: boolean
}>()

const emit = defineEmits<{
  (event: 'open', topic: TimelineTopic): void
}>()

function emitOpen(topic: TimelineTopic) {
  emit('open', topic)
}
</script>

<style scoped>
/* ========================================
   整体卡片
   ======================================== */
.news-recommend-panel {
  display: grid;
  gap: 16px;
}

.news-recommend-panel__card {
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-card);
  background: var(--color-bg-card);
}

.news-recommend-panel__card :deep(.el-card__body) {
  display: grid;
  gap: 16px;
  padding: 20px;
}

/* ========================================
   标题区：红色竖线 + 标题 + 副标题
   ======================================== */
.news-recommend-panel__header {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.news-recommend-panel__header-accent {
  flex-shrink: 0;
  width: 4px;
  height: 40px;
  border-radius: 2px;
  background: var(--color-primary);
  margin-top: 2px;
}

.news-recommend-panel__header-text {
  min-width: 0;
}

.news-recommend-panel__title {
  margin: 0;
  color: var(--color-text-primary);
  font-size: 17px;
  font-weight: 700;
  line-height: 1.3;
}

.news-recommend-panel__desc {
  margin: 6px 0 0;
  color: var(--color-text-secondary);
  font-size: 13px;
  line-height: 1.7;
}

/* ========================================
   骨架屏
   ======================================== */
.news-recommend-panel__skeleton {
  display: grid;
  gap: 14px;
}

.news-recommend-panel__skeleton-item {
  padding: 12px 14px;
  border: 1px solid var(--color-border);
  border-radius: 14px;
  background: var(--color-bg);
}

.skeleton-line {
  height: 14px;
  border-radius: 7px;
  background: var(--el-fill-color);
  margin-bottom: 8px;
}

.skeleton-line--title {
  width: 65%;
  height: 16px;
}

.skeleton-line--text {
  width: 90%;
}

.skeleton-line--meta {
  width: 45%;
  height: 12px;
  margin-bottom: 0;
}

/* ========================================
   话题卡片列表
   ======================================== */
.news-recommend-panel__list {
  display: grid;
  gap: 10px;
}

/* ========================================
   单个话题预览卡片
   ======================================== */
.news-recommend-panel__item {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 14px 16px;
  border: 1px solid var(--color-border);
  border-radius: 14px;
  background: var(--color-bg);
  cursor: default;
  transition:
    transform 0.22s ease,
    border-color 0.22s ease,
    box-shadow 0.22s ease;
}

.news-recommend-panel__item:hover {
  transform: translateY(-2px);
  border-color: color-mix(in srgb, var(--color-primary) 45%, var(--color-border));
  box-shadow: 0 8px 22px rgba(217, 45, 32, 0.08);
}

/* --- 卡片主体 --- */
.news-recommend-panel__item-body {
  display: grid;
  gap: 8px;
  min-width: 0;
}

.news-recommend-panel__item-title {
  margin: 0;
  color: var(--color-text-primary);
  font-size: 15px;
  font-weight: 700;
  line-height: 1.45;
  transition: color 0.18s ease;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.news-recommend-panel__item:hover .news-recommend-panel__item-title {
  color: var(--color-primary);
}

.news-recommend-panel__item-summary {
  margin: 0;
  color: var(--color-text-secondary);
  font-size: 13px;
  line-height: 1.65;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

/* --- 热度 / 新闻数小标签 --- */
.news-recommend-panel__item-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.news-recommend-panel__item-meta-pill {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 10px;
  border-radius: 999px;
  border: 1px solid color-mix(in srgb, var(--color-primary) 18%, var(--color-border));
  background: color-mix(in srgb, var(--color-primary) 5%, var(--color-bg-card));
  color: var(--color-text-secondary);
  font-size: 12px;
  font-weight: 500;
  white-space: nowrap;
}

/* --- 关键词标签 --- */
.news-recommend-panel__item-keywords {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.news-recommend-panel__item-keyword {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 999px;
  border: 1px solid color-mix(in srgb, var(--color-primary) 20%, transparent);
  background: color-mix(in srgb, var(--color-primary) 6%, transparent);
  color: #b91c1c;
  font-size: 11px;
  font-weight: 500;
  white-space: nowrap;
  line-height: 1.6;
}

/* --- 事件节点预览提示（纯静态视觉） --- */
.news-recommend-panel__item-stages {
  display: flex;
  align-items: center;
  gap: 6px;
  padding-top: 2px;
  color: var(--color-text-secondary);
  font-size: 11px;
  letter-spacing: 0.02em;
}

.stage-marker {
  display: inline-block;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: color-mix(in srgb, var(--color-primary) 40%, transparent);
  flex-shrink: 0;
}

.stage-marker--middle {
  background: color-mix(in srgb, var(--color-primary) 70%, transparent);
}

.stage-marker--latest {
  width: 8px;
  height: 8px;
  background: var(--color-primary);
  box-shadow: 0 0 5px color-mix(in srgb, var(--color-primary) 35%, transparent);
}

/* --- 操作入口 --- */
.news-recommend-panel__item-action {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 6px;
  padding-top: 8px;
  border-top: 1px dashed color-mix(in srgb, var(--color-primary) 18%, var(--color-border));
  cursor: pointer;
  user-select: none;
  transition: color 0.18s ease;
}

.news-recommend-panel__item-action-text {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-primary);
  transition: color 0.18s ease;
}

.news-recommend-panel__item-action-arrow {
  display: inline-block;
  font-size: 14px;
  color: var(--color-primary);
  transition: transform 0.22s ease, color 0.18s ease;
}

.news-recommend-panel__item-action:hover .news-recommend-panel__item-action-text {
  color: #b91c1c;
}

.news-recommend-panel__item-action:hover .news-recommend-panel__item-action-arrow {
  transform: translateX(4px);
  color: #b91c1c;
}

/* ========================================
   暗色模式
   ======================================== */
:root.dark .news-recommend-panel__card {
  background: #1f2933;
  border-color: #3b2020;
}

:root.dark .news-recommend-panel__item {
  background: #263038;
  border-color: #334150;
}

:root.dark .news-recommend-panel__item:hover {
  border-color: color-mix(in srgb, var(--color-primary) 35%, #4a3540);
  box-shadow: 0 8px 22px rgba(0, 0, 0, 0.3);
}

:root.dark .news-recommend-panel__item-title {
  color: #e5e7eb;
}

:root.dark .news-recommend-panel__item:hover .news-recommend-panel__item-title {
  color: #f87171;
}

:root.dark .news-recommend-panel__item-summary {
  color: var(--color-text-muted);
}

:root.dark .news-recommend-panel__item-meta-pill {
  border-color: rgba(248, 113, 113, 0.2);
  background: rgba(248, 113, 113, 0.06);
  color: #aeb8c4;
}

:root.dark .news-recommend-panel__item-keyword {
  border-color: rgba(248, 113, 113, 0.22);
  background: rgba(248, 113, 113, 0.1);
  color: #fca5a5;
}

:root.dark .stage-marker {
  background: rgba(248, 113, 113, 0.35);
}

:root.dark .stage-marker--middle {
  background: rgba(248, 113, 113, 0.6);
}

:root.dark .stage-marker--latest {
  background: #d97979;
  box-shadow: 0 0 5px rgba(248, 113, 113, 0.25);
}

:root.dark .news-recommend-panel__item-action {
  border-top-color: rgba(248, 113, 113, 0.12);
}

:root.dark .news-recommend-panel__item-action-text,
:root.dark .news-recommend-panel__item-action-arrow {
  color: #f87171;
}

:root.dark .news-recommend-panel__item-action:hover .news-recommend-panel__item-action-text,
:root.dark .news-recommend-panel__item-action:hover .news-recommend-panel__item-action-arrow {
  color: #fca5a5;
}

:root.dark .news-recommend-panel__skeleton-item {
  background: #263038;
  border-color: #334150;
}

:root.dark .skeleton-line {
  background: rgba(255, 255, 255, 0.06);
}

:root.dark .news-recommend-panel__item-stages {
  color: var(--color-text-muted);
}

:root.dark .news-recommend-panel__desc {
  color: var(--color-text-muted);
}

/* ========================================
   响应式
   ======================================== */
@media (max-width: 768px) {
  .news-recommend-panel__card :deep(.el-card__body) {
    padding: 14px;
  }

  .news-recommend-panel__item {
    padding: 12px 14px;
  }

  .news-recommend-panel__item-title {
    font-size: 14px;
  }

  .news-recommend-panel__item-stages {
    font-size: 10px;
    gap: 4px;
    flex-wrap: wrap;
  }

  .news-recommend-panel__item-action {
    justify-content: flex-start;
  }
}
</style>
