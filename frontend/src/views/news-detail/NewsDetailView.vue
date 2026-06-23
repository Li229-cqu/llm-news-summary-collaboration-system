<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElLoading } from 'element-plus'
import { getNewsDetail, type NewsDetail } from '@/api/news'
import { useAIDraftStore } from '@/stores/aiDraft'

const route = useRoute()
const router = useRouter()
const aiDraft = useAIDraftStore()

const newsId = computed(() => route.params.id)
const newsDetail = ref<NewsDetail | null>(null)
const loading = ref(true)
const error = ref('')

const loadNewsDetail = async () => {
  if (!newsId.value) {
    error.value = '无效的新闻 ID'
    loading.value = false
    return
  }

  try {
    loading.value = true
    error.value = ''
    newsDetail.value = await getNewsDetail(newsId.value)

    if (newsDetail.value?.id) {
      await recordBrowseEvent()
    }
  } catch (err) {
    error.value = '加载新闻失败，请稍后重试'
    ElMessage.error(error.value)
  } finally {
    loading.value = false
  }
}

const recordBrowseEvent = async () => {
  try {
    const { recordBrowse } = await import('@/api/news')
    await recordBrowse(newsId.value)
  } catch {
    // 浏览记录失败不影响页面显示
  }
}

const handleGenerateWithAI = () => {
  if (!newsDetail.value?.content || newsDetail.value.content.trim().length === 0) {
    ElMessage.warning('当前新闻正文为空，无法导入 AI 生成页')
    return
  }

  aiDraft.setFromNews({
    id: newsDetail.value.id,
    title: newsDetail.value.title,
    content: newsDetail.value.content,
  })

  router.push({
    path: '/ai/title-summary',
    query: { source: 'news', newsId: newsDetail.value.id },
  })
}

onMounted(() => {
  loadNewsDetail()
})
</script>

<template>
  <main class="page-container">
    <!-- 页面标题 -->
    <el-card class="app-card page-header">
      <h1>新闻详情</h1>
      <p>查看完整的新闻内容、评论和相关功能。</p>
    </el-card>

    <!-- 加载状态 -->
    <el-card v-if="loading" class="app-card">
      <el-skeleton :rows="5" animated />
    </el-card>

    <!-- 错误提示 -->
    <el-card v-else-if="error" class="app-card">
      <el-alert :title="error" type="error" :closable="false" show-icon />
    </el-card>

    <!-- 新闻内容 -->
    <div v-else-if="newsDetail" class="news-content">
      <!-- 新闻标题区 -->
      <el-card class="app-card news-header">
        <h2 class="news-title">{{ newsDetail.title }}</h2>
        <div class="news-meta">
          <span v-if="newsDetail.source" class="meta-item">来源：{{ newsDetail.source }}</span>
          <span v-if="newsDetail.author" class="meta-item">作者：{{ newsDetail.author }}</span>
          <span v-if="newsDetail.publish_time" class="meta-item">
            发布时间：{{ newsDetail.publish_time }}
          </span>
          <span v-if="newsDetail.category_name" class="meta-item">
            分类：{{ newsDetail.category_name }}
          </span>
        </div>
      </el-card>

      <!-- 新闻正文区 -->
      <el-card class="app-card news-body">
        <div class="news-content-text">
          {{ newsDetail.content }}
        </div>

        <!-- 新闻正文下方操作区 -->
        <div class="news-actions">
          <el-button
            type="primary"
            @click="handleGenerateWithAI"
            icon="Sparkles"
          >
            ✨ 用 AI 生成标题和摘要
          </el-button>
          <el-button type="default" disabled>
            👍 点赞 ({{ newsDetail.like_count }})
          </el-button>
          <el-button type="default" disabled>
            ⭐ 收藏 ({{ newsDetail.favorite_count }})
          </el-button>
        </div>
      </el-card>

      <!-- 评论区占位 -->
      <el-card class="app-card comments-section">
        <template #header>
          <div class="section-header">
            <span>💬 评论区</span>
          </div>
        </template>
        <div class="placeholder-content">
          <p class="placeholder-text">评论功能暂未开放</p>
          <p class="placeholder-description">敬请期待</p>
        </div>
      </el-card>

      <!-- 相关新闻占位 -->
      <el-card class="app-card related-news-section">
        <template #header>
          <div class="section-header">
            <span>📰 相关新闻</span>
          </div>
        </template>
        <div class="placeholder-content">
          <p class="placeholder-text">相关新闻推荐功能暂未开放</p>
          <p class="placeholder-description">敬请期待</p>
        </div>
      </el-card>
    </div>

    <!-- 空状态 -->
    <el-card v-else class="app-card">
      <el-empty description="无法加载新闻内容" />
    </el-card>
  </main>
</template>

<style scoped>
.page-container {
  padding: 24px;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h1 {
  margin-top: 0;
  margin-bottom: 8px;
  font-size: 24px;
  color: var(--color-text-primary);
}

.page-header p {
  margin: 0;
  color: var(--color-text-secondary);
  font-size: 14px;
}

.news-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* 新闻标题区 */
.news-header {
  margin-bottom: 0;
}

.news-title {
  margin: 0 0 12px;
  font-size: 20px;
  font-weight: 600;
  color: var(--color-text-primary);
  line-height: 1.6;
}

.news-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
}

.meta-item {
  font-size: 13px;
  color: var(--color-text-secondary);
}

/* 新闻正文区 */
.news-body {
  margin-bottom: 0;
}

.news-content-text {
  line-height: 1.8;
  color: var(--color-text-primary);
  font-size: 15px;
  margin-bottom: 24px;
  white-space: pre-wrap;
  word-break: break-word;
}

.news-actions {
  display: flex;
  gap: 8px;
  padding-top: 16px;
  border-top: 1px solid var(--color-border);
}

.news-actions :deep(.el-button) {
  flex: 1;
}

/* 评论区和相关新闻 */
.comments-section,
.related-news-section {
  margin-bottom: 16px;
}

.comments-section:last-child,
.related-news-section:last-child {
  margin-bottom: 0;
}

.section-header {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.placeholder-content {
  padding: 40px 20px;
  text-align: center;
  background-color: rgba(64, 158, 255, 0.05);
  border-radius: 4px;
}

.placeholder-text {
  margin: 0 0 8px;
  font-size: 16px;
  color: var(--color-text-primary);
  font-weight: 500;
}

.placeholder-description {
  margin: 0;
  font-size: 14px;
  color: var(--color-text-secondary);
}
</style>
