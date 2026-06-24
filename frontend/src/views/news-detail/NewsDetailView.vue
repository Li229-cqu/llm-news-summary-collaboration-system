<template>
  <main class="news-detail-page">
    <el-skeleton v-if="loading" animated :rows="10" />

    <el-alert v-else-if="error" :title="error" type="error" show-icon>
      <template #default>
        <div class="news-detail-page__error-actions">
          <el-button type="primary" @click="goHome">返回首页</el-button>
        </div>
      </template>
    </el-alert>

    <el-empty v-else-if="!newsDetail" description="新闻不存在">
      <el-button type="primary" @click="goHome">返回首页</el-button>
    </el-empty>

    <div v-else class="news-detail-layout">
      <section class="news-detail-main">
        <el-card class="news-detail-card" shadow="never">
          <div class="news-detail-card__header">
            <el-button text type="primary" @click="goHome">返回首页</el-button>
            <div class="news-detail-card__header-actions">
              <ShareButton />
              <el-button type="primary" plain @click="goToAiGenerate">用 AI 生成标题和摘要</el-button>
            </div>
          </div>

          <NewsMeta :news="newsDetail" />
          <NewsDetailContent :news="newsDetail" />

          <div class="news-detail-actions">
            <LikeButton
              :news-id="newsDetail.id"
              :liked="newsDetail.is_liked"
              :count="newsDetail.like_count"
              :loading="actionLoading === 'like' || actionLoading === 'unlike'"
              @toggle="handleLikeToggle"
            />
            <FavoriteButton
              :news-id="newsDetail.id"
              :favorited="newsDetail.is_favorited"
              :count="newsDetail.favorite_count"
              :loading="actionLoading === 'favorite' || actionLoading === 'unfavorite'"
              @toggle="handleFavoriteToggle"
            />
          </div>
        </el-card>

        <el-card class="news-detail-card news-detail-card--comments" shadow="never">
          <div class="news-detail-section-title">
            <span>评论区</span>
            <span class="news-detail-section-title__count">共 {{ commentTotal }} 条</span>
          </div>
          <CommentBox
            placeholder="写下你的评论"
            button-text="发布评论"
            :loading="submittingComment"
            @submit="handleCreateComment"
          />
          <CommentList
            :comments="comments"
            :loading="loadingComments"
            :total="commentTotal"
            :replying-id="replyingId"
            :loading-like="actionLoading === 'comment-like'"
            :loading-reply="submittingComment"
            @like="handleLikeComment"
            @reply="handleReplyComment"
          />
        </el-card>
      </section>

      <aside class="news-detail-aside">
        <NewsDetailSidePanel :related-news="relatedNews" :recommended-news="recommendedNews" />
      </aside>
    </div>
  </main>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getNewsDetail, recordBrowse, type NewsDetail, type NewsItem } from '@/api/news'
import {
  createNewsComment,
  favoriteNews,
  getNewsComments,
  likeComment,
  likeNews,
  replyComment,
  unfavoriteNews,
  unlikeNews,
  type CommentItem,
} from '@/api/interaction'
import { useUserStore } from '@/stores/user'
import { useAIDraftStore } from '@/stores/aiDraft'
import NewsMeta from '@/components/news/NewsMeta.vue'
import NewsDetailContent from '@/components/news/NewsDetailContent.vue'
import NewsDetailSidePanel from '@/components/news/NewsDetailSidePanel.vue'
import LikeButton from '@/components/interaction/LikeButton.vue'
import FavoriteButton from '@/components/interaction/FavoriteButton.vue'
import ShareButton from '@/components/interaction/ShareButton.vue'
import CommentBox from '@/components/interaction/CommentBox.vue'
import CommentList from '@/components/interaction/CommentList.vue'

type ActionType = 'like' | 'unlike' | 'favorite' | 'unfavorite' | 'comment-like' | ''

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const aiDraft = useAIDraftStore()

const newsDetail = ref<NewsDetail | null>(null)
const comments = ref<CommentItem[]>([])
const loading = ref(false)
const loadingComments = ref(false)
const submittingComment = ref(false)
const actionLoading = ref<ActionType>('')
const error = ref('')
const commentTotal = ref(0)
const replyingId = ref<number | null>(null)
const newsId = computed(() => String(route.params.id ?? '').trim())

const relatedNews = computed<NewsItem[]>(() => newsDetail.value?.related_news ?? [])
const recommendedNews = computed<NewsItem[]>(() => newsDetail.value?.recommended_news ?? [])

async function loadNewsDetail() {
  if (!newsId.value) {
    newsDetail.value = null
    error.value = '无效的新闻 ID'
    return
  }

  loading.value = true
  error.value = ''

  try {
    const result = await getNewsDetail(newsId.value)
    newsDetail.value = result

    try {
      await recordBrowse(newsId.value)
    } catch {
      // 浏览记录失败不影响正文展示
    }

    await loadComments()
  } catch (requestError) {
    newsDetail.value = null
    comments.value = []
    commentTotal.value = 0

    const message = requestError instanceof Error ? requestError.message : '获取新闻详情失败'
    error.value = message.includes('404') || message.includes('不存在') ? '新闻不存在' : message
    ElMessage.error(error.value)
  } finally {
    loading.value = false
  }
}

async function loadComments() {
  if (!newsId.value) {
    comments.value = []
    commentTotal.value = 0
    return
  }

  loadingComments.value = true

  try {
    const result = await getNewsComments(newsId.value)
    comments.value = result.list
    commentTotal.value = result.total
  } catch (requestError) {
    comments.value = []
    commentTotal.value = 0
    ElMessage.error(requestError instanceof Error ? requestError.message : '获取评论失败')
  } finally {
    loadingComments.value = false
  }
}

function goHome() {
  router.push('/home')
}

function goToLogin() {
  router.push({
    path: '/login',
    query: {
      redirect: route.fullPath,
    },
  })
}

function requireLogin() {
  if (userStore.isLoggedIn) {
    return true
  }

  ElMessage.warning('请先登录后再操作')
  goToLogin()
  return false
}

function goToAiGenerate() {
  if (!newsDetail.value?.content?.trim()) {
    ElMessage.warning('当前新闻正文为空，无法导入 AI 生成')
    return
  }

  aiDraft.setFromNews({
    id: newsDetail.value.id,
    title: newsDetail.value.title,
    content: newsDetail.value.content,
  })

  sessionStorage.setItem(
    'ai_draft_from_news',
    JSON.stringify({
      source: 'news',
      news_id: newsDetail.value.id,
      title: newsDetail.value.title,
      summary: newsDetail.value.summary,
      content: newsDetail.value.content,
      category_name: newsDetail.value.category_name,
      source_name: newsDetail.value.source,
      publish_time: newsDetail.value.publish_time,
    }),
  )

  router.push({
    path: '/ai/title-summary',
    query: {
      source: 'news',
      newsId: newsDetail.value.id,
    },
  })
}

async function handleLikeToggle(newsIdValue: number | string) {
  if (!requireLogin() || !newsDetail.value) {
    return
  }

  actionLoading.value = newsDetail.value.is_liked ? 'unlike' : 'like'

  try {
    const result = newsDetail.value.is_liked ? await unlikeNews(newsIdValue) : await likeNews(newsIdValue)
    newsDetail.value = {
      ...newsDetail.value,
      is_liked: result.status,
      like_count: result.like_count ?? newsDetail.value.like_count,
    }
  } catch (requestError) {
    ElMessage.error(requestError instanceof Error ? requestError.message : '操作失败')
  } finally {
    actionLoading.value = ''
  }
}

async function handleFavoriteToggle(newsIdValue: number | string) {
  if (!requireLogin() || !newsDetail.value) {
    return
  }

  actionLoading.value = newsDetail.value.is_favorited ? 'unfavorite' : 'favorite'

  try {
    const result = newsDetail.value.is_favorited
      ? await unfavoriteNews(newsIdValue)
      : await favoriteNews(newsIdValue)

    newsDetail.value = {
      ...newsDetail.value,
      is_favorited: result.status,
      favorite_count: result.favorite_count ?? newsDetail.value.favorite_count,
    }
  } catch (requestError) {
    ElMessage.error(requestError instanceof Error ? requestError.message : '操作失败')
  } finally {
    actionLoading.value = ''
  }
}

async function handleCreateComment(content: string) {
  if (!requireLogin() || !newsDetail.value) {
    return
  }

  submittingComment.value = true

  try {
    await createNewsComment(newsDetail.value.id, { content })
    await loadComments()
    newsDetail.value = {
      ...newsDetail.value,
      comment_count: newsDetail.value.comment_count + 1,
    }
  } catch (requestError) {
    ElMessage.error(requestError instanceof Error ? requestError.message : '评论发布失败')
  } finally {
    submittingComment.value = false
  }
}

async function handleReplyComment(comment: CommentItem, content: string) {
  if (!requireLogin() || !newsDetail.value) {
    return
  }

  if (content === '__toggle__') {
    replyingId.value = replyingId.value === comment.id ? null : comment.id
    return
  }

  if (!content) {
    replyingId.value = null
    return
  }

  submittingComment.value = true

  try {
    await replyComment(comment.id, { content })
    replyingId.value = null
    await loadComments()
    newsDetail.value = {
      ...newsDetail.value,
      comment_count: newsDetail.value.comment_count + 1,
    }
  } catch (requestError) {
    ElMessage.error(requestError instanceof Error ? requestError.message : '回复失败')
  } finally {
    submittingComment.value = false
  }
}

async function handleLikeComment(comment: CommentItem) {
  if (!requireLogin()) {
    return
  }

  actionLoading.value = 'comment-like'

  try {
    await likeComment(comment.id)
    await loadComments()
  } catch (requestError) {
    ElMessage.error(requestError instanceof Error ? requestError.message : '评论点赞失败')
  } finally {
    actionLoading.value = ''
  }
}

watch(
  () => route.params.id,
  () => {
    loadNewsDetail()
  },
  { immediate: true },
)

onMounted(() => {
  if (!userStore.userInfo) {
    userStore.loadFromStorage()
  }
})
</script>

<style scoped>
.news-detail-page {
  width: 100%;
  box-sizing: border-box;
}

.news-detail-layout {
  display: flex;
  align-items: flex-start;
  gap: 20px;
  width: 100%;
}

.news-detail-main {
  flex: 1;
  min-width: 0;
  display: grid;
  gap: 20px;
}

.news-detail-aside {
  width: 320px;
  flex: 0 0 320px;
  min-width: 0;
}

.news-detail-card {
  border-color: var(--color-border);
  border-radius: var(--border-radius-card);
  background: var(--color-bg-card);
}

.news-detail-card :deep(.el-card__body) {
  display: grid;
  gap: 18px;
  padding: 20px;
}

.news-detail-card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.news-detail-card__header-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: center;
}

.news-detail-card--comments :deep(.el-card__body) {
  gap: 14px;
}

.news-detail-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  padding-top: 4px;
}

.news-detail-section-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  color: var(--color-text-primary);
  font-size: 18px;
  font-weight: 600;
}

.news-detail-section-title__count {
  color: var(--color-text-secondary);
  font-size: 13px;
  font-weight: 400;
}

.news-detail-page__error-actions {
  margin-top: 12px;
}

@media (max-width: 1200px) {
  .news-detail-layout {
    flex-direction: column;
  }

  .news-detail-aside {
    width: 100%;
    flex: none;
  }
}

@media (max-width: 640px) {
  .news-detail-card__header {
    flex-direction: column;
    align-items: flex-start;
  }

  .news-detail-card__header-actions,
  .news-detail-actions {
    width: 100%;
  }

  .news-detail-card__header-actions :deep(.el-button),
  .news-detail-actions :deep(.el-button) {
    width: 100%;
  }

  .news-detail-actions {
    flex-direction: column;
  }
}
</style>
