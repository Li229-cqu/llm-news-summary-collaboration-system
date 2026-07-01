<template>
  <section class="news-hot-list">
    <div class="news-hot-list__header">
      <div>
        <h3 class="news-hot-list__title">
          <span class="news-hot-list__title-icon">🔥</span>
          热搜榜
          <span class="news-hot-list__title-rank">Top10</span>
        </h3>
        <p class="news-hot-list__desc">实时关注度排行</p>
      </div>
    </div>

    <el-skeleton v-if="loading" animated :rows="6" />
    <el-empty v-else-if="!list.length" description="暂无热榜数据" />
    <ol v-else class="news-hot-list__items">
      <li
        v-for="item in list"
        :key="item.id"
        class="news-hot-list__item"
        @click="handleClick(item.id)"
      >
        <div class="news-hot-list__rank" :class="rankClass(item.rank)">
          {{ String(item.rank).padStart(2, '0') }}
        </div>
        <div class="news-hot-list__content">
          <div class="news-hot-list__item-title">{{ item.title }}</div>
          <div class="news-hot-list__meta">
            <span>{{ item.category_name }}</span>
            <span>阅读 {{ item.view_count }}</span>
            <span>评论 {{ item.comment_count }}</span>
          </div>
        </div>
      </li>
    </ol>
  </section>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'

export interface HotNewsItem {
  id: number
  title: string
  category_name: string
  source: string
  view_count: number
  comment_count: number
  like_count?: number
  favorite_count?: number
  cover_image?: string
  publish_time?: string
  heat_score?: number
  rank: number
}

const props = defineProps<{
  list: HotNewsItem[]
  loading?: boolean
}>()

const router = useRouter()

/** 排名样式 class */
function rankClass(rank: number): string {
  if (rank === 1) return 'news-hot-list__rank--gold'
  if (rank === 2) return 'news-hot-list__rank--silver'
  if (rank === 3) return 'news-hot-list__rank--bronze'
  return ''
}

function handleClick(newsId: number) {
  router.push(`/news/${newsId}`)
}
</script>

<style scoped>
/* ========================================
   热搜榜容器
   ======================================== */
.news-hot-list {
  display: grid;
  gap: 14px;
}

/* ========================================
   标题行
   ======================================== */
.news-hot-list__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.news-hot-list__title {
  display: flex;
  align-items: center;
  gap: 6px;
  margin: 0;
  color: var(--color-text-primary);
  font-size: 18px;
  font-weight: 700;
}

.news-hot-list__title-icon {
  font-size: 18px;
}

.news-hot-list__title-rank {
  color: var(--color-primary);
  font-size: 14px;
  font-weight: 700;
}

.news-hot-list__desc {
  margin: 5px 0 0;
  color: var(--color-text-secondary);
  font-size: 13px;
}

/* ========================================
   热榜列表
   ======================================== */
.news-hot-list__items {
  display: grid;
  gap: 8px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.news-hot-list__item {
  display: grid;
  grid-template-columns: 36px minmax(0, 1fr);
  gap: 12px;
  padding: 12px 14px;
  border: 1px solid var(--color-border);
  border-radius: 14px;
  background: var(--color-bg-card);
  cursor: pointer;
  transition:
    transform .16s ease,
    border-color .16s ease,
    box-shadow .16s ease;
}

.news-hot-list__item:hover {
  border-color: color-mix(in srgb, var(--color-primary) 30%, var(--color-border));
  box-shadow: 0 8px 18px rgba(217, 45, 32, .08);
  transform: translateY(-1px);
}

/* ========================================
   排名徽章 —— 红白渐变体系
   ======================================== */
.news-hot-list__rank {
  display: grid;
  place-items: center;
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: var(--color-primary-soft);
  color: var(--color-primary);
  font-size: 16px;
  font-weight: 800;
  font-variant-numeric: tabular-nums;
  letter-spacing: .02em;
}

/* 第 1 名：红色强调 */
.news-hot-list__rank--gold {
  background: linear-gradient(135deg, #fecaca, #fca5a5);
  color: #991b1b;
  box-shadow: 0 2px 8px rgba(217, 45, 32, .22);
}

/* 第 2 名：橙红渐变 */
.news-hot-list__rank--silver {
  background: linear-gradient(135deg, #fed7aa, #fdba74);
  color: #9a3412;
  box-shadow: 0 2px 8px rgba(234, 88, 12, .16);
}

/* 第 3 名：玫红渐变 */
.news-hot-list__rank--bronze {
  background: linear-gradient(135deg, #fce7f3, #fbcfe8);
  color: #9d174d;
  box-shadow: 0 2px 8px rgba(219, 39, 119, .16);
}

/* ========================================
   新闻内容区
   ======================================== */
.news-hot-list__content {
  min-width: 0;
  display: grid;
  gap: 6px;
}

.news-hot-list__item-title {
  overflow: hidden;
  color: var(--color-text-primary);
  font-size: 14px;
  font-weight: 600;
  line-height: 1.4;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.news-hot-list__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 6px 10px;
  color: var(--color-text-secondary);
  font-size: 12px;
}

/* ========================================
   暗色模式适配
   ======================================== */
:root.dark .news-hot-list__rank--gold {
  background: linear-gradient(135deg, #3b1a1a, #5c1a1a);
  color: #fca5a5;
  box-shadow: 0 2px 8px rgba(217, 45, 32, .25);
}

:root.dark .news-hot-list__rank--silver {
  background: linear-gradient(135deg, #3b2210, #5c2d10);
  color: #fdba74;
  box-shadow: 0 2px 8px rgba(234, 88, 12, .18);
}

:root.dark .news-hot-list__rank--bronze {
  background: linear-gradient(135deg, #3b1a2c, #5c1a3c);
  color: #fbcfe8;
  box-shadow: 0 2px 8px rgba(219, 39, 119, .18);
}

:root.dark .news-hot-list__item:hover {
  box-shadow: 0 8px 18px rgba(0, 0, 0, .3);
}

/* ========================================
   响应式
   ======================================== */
@media (max-width: 768px) {
  .news-hot-list__item {
    grid-template-columns: 32px minmax(0, 1fr);
    padding: 10px 12px;
  }

  .news-hot-list__rank {
    width: 32px;
    height: 32px;
    font-size: 14px;
    border-radius: 8px;
  }
}
</style>
