<template>
  <el-card v-if="isLoggedIn" class="recommendation-panel" shadow="never">
    <div class="recommendation-panel__header">
      <h3 class="recommendation-panel__title">为你推荐</h3>
      <p class="recommendation-panel__desc">基于你的浏览、收藏、点赞推荐</p>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="recommendation-panel__loading">
      <el-skeleton animated :rows="3" />
    </div>

    <!-- 错误状态 -->
    <el-alert
      v-else-if="error"
      type="warning"
      :description="error"
      :closable="false"
      class="recommendation-panel__error"
    />

    <!-- 空状态 -->
    <el-empty
      v-else-if="!recommendations.length"
      description="暂无个性化推荐，先去浏览几篇新闻吧"
      :image-size="80"
    />

    <!-- 推荐列表 -->
    <div v-else class="recommendation-panel__list">
      <article
        v-for="news in recommendations"
        :key="news.id"
        class="recommendation-panel__item"
        role="button"
        tabindex="0"
        @click="goToNews(news.id)"
        @keyup.enter="goToNews(news.id)"
      >
        <div v-if="news.cover_image && !failedImages.has(news.id)" class="recommendation-panel__cover">
          <img
            class="recommendation-panel__image"
            :src="news.cover_image"
            :alt="news.title"
            @error="handleImageError(news.id)"
          />
        </div>

        <div class="recommendation-panel__content">
          <div class="recommendation-panel__topline">
            <el-tag v-if="news.category_name" size="small" effect="plain">
              {{ news.category_name }}
            </el-tag>
            <span class="recommendation-panel__source">{{ news.source }}</span>
          </div>

          <h4 class="recommendation-panel__item-title">{{ news.title }}</h4>
          <p class="recommendation-panel__summary">{{ news.summary }}</p>

          <div v-if="news.recommendation_reason" class="recommendation-panel__reason">
            {{ news.recommendation_reason }}
          </div>

          <div class="recommendation-panel__meta">
            <span>{{ news.publish_time }}</span>
            <span>阅读 {{ news.view_count }}</span>
          </div>
        </div>
      </article>
    </div>
  </el-card>

  <!-- 未登录提示 -->
  <el-card v-else class="recommendation-panel" shadow="never">
    <div class="recommendation-panel__login-prompt">
      <div class="recommendation-panel__login-content">
        <h3 class="recommendation-panel__title">为你推荐</h3>
        <p class="recommendation-panel__desc">登录后查看基于你的浏览、收藏、点赞的个性化推荐</p>
      </div>
      <el-button type="primary" @click="goToLogin">去登录</el-button>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { getRecommendations } from '@/api/profile'
import type { NewsItem } from '@/api/news'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()

const isLoggedIn = ref(false)
const loading = ref(false)
const error = ref('')
const recommendations = ref<NewsItem[]>([])
const failedImages = ref(new Set<number>())

// 检查登录状态
function checkLogin() {
  isLoggedIn.value = userStore.isLoggedIn
}

// 加载推荐
async function loadRecommendations() {
  if (!isLoggedIn.value) {
    return
  }

  loading.value = true
  error.value = ''

  try {
    const result = await getRecommendations(10)
    recommendations.value = result.list || []
  } catch (err) {
    error.value = '推荐内容暂时加载失败'
    console.error('加载推荐失败:', err)
  } finally {
    loading.value = false
  }
}

// 图片加载失败
function handleImageError(newsId: number) {
  failedImages.value.add(newsId)
}

// 跳转到新闻详情
function goToNews(newsId: number) {
  router.push(`/news/${newsId}`)
}

// 跳转到登录
function goToLogin() {
  router.push({
    path: '/login',
    query: { redirect: router.currentRoute.value.fullPath },
  })
}

onMounted(() => {
  checkLogin()
  loadRecommendations()
})
</script>

<style scoped>
.recommendation-panel {
  border-color: var(--color-border);
  border-radius: var(--border-radius-card);
}

.recommendation-panel :deep(.el-card__body) {
  display: grid;
  gap: 12px;
  padding: 18px;
}

.recommendation-panel__header {
  padding-bottom: 12px;
  border-bottom: 1px solid var(--color-border);
}

.recommendation-panel__title {
  margin: 0;
  color: var(--color-text-primary);
  font-size: 16px;
  font-weight: 700;
}

.recommendation-panel__desc {
  margin: 6px 0 0;
  color: var(--color-text-secondary);
  font-size: 12px;
  line-height: 1.6;
}

.recommendation-panel__login-prompt {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.recommendation-panel__login-content {
  min-width: 0;
}

.recommendation-panel__loading {
  padding: 12px 0;
}

.recommendation-panel__error {
  margin-top: 8px;
}

.recommendation-panel__list {
  display: grid;
  gap: 10px;
}

.recommendation-panel__item {
  display: grid;
  grid-template-columns: 80px minmax(0, 1fr);
  gap: 10px;
  padding: 10px;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  background: var(--color-bg-card);
  cursor: pointer;
  transition:
    transform 0.12s ease,
    border-color 0.12s ease,
    box-shadow 0.12s ease;
}

.recommendation-panel__item:hover {
  border-color: color-mix(in srgb, var(--color-primary) 35%, var(--color-border));
  box-shadow: 0 4px 12px rgb(15 23 42 / 8%);
  transform: translateY(-1px);
}

.recommendation-panel__cover {
  overflow: hidden;
  min-height: 80px;
  border-radius: 6px;
  background: linear-gradient(135deg, color-mix(in srgb, var(--color-primary) 16%, var(--color-bg-card)), var(--color-bg));
}

.recommendation-panel__image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.recommendation-panel__content {
  display: grid;
  gap: 6px;
  min-width: 0;
}

.recommendation-panel__topline {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
}

.recommendation-panel__source {
  color: var(--color-text-secondary);
  font-size: 11px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.recommendation-panel__item-title {
  margin: 0;
  color: var(--color-text-primary);
  font-size: 13px;
  font-weight: 600;
  line-height: 1.4;
  display: -webkit-box;
  overflow: hidden;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.recommendation-panel__summary {
  display: -webkit-box;
  overflow: hidden;
  margin: 0;
  color: var(--color-text-secondary);
  font-size: 12px;
  line-height: 1.5;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.recommendation-panel__reason {
  padding: 4px 8px;
  margin-top: 4px;
  border-radius: 4px;
  background: color-mix(in srgb, var(--color-primary) 8%, var(--color-bg));
  color: var(--color-primary);
  font-size: 11px;
  line-height: 1.4;
}

.recommendation-panel__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 6px 10px;
  margin-top: auto;
  color: var(--color-text-secondary);
  font-size: 11px;
}

@media (max-width: 768px) {
  .recommendation-panel__item {
    grid-template-columns: 70px minmax(0, 1fr);
    gap: 8px;
  }

  .recommendation-panel__item-title {
    font-size: 12px;
  }

  .recommendation-panel__meta {
    font-size: 10px;
  }
}
</style>
