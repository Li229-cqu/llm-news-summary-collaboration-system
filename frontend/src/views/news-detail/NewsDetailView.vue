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
              <ShareButton target-selector=".news-detail-main" :title="newsDetail?.title || ''" />
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
            :loading-like-id="commentLikeLoadingId"
            :loading-reply="submittingComment"
            :deleting-id="deletingCommentId"
            :current-user-id="userStore.userInfo?.id ?? null"
            :current-user-role="userStore.role"
            @like="handleLikeComment"
            @reply="handleReplyComment"
            @delete="handleDeleteComment"
            @reload-comments="loadComments"
          />
        </el-card>
      </section>

      <aside class="news-detail-aside">
        <NewsDetailSidePanel
          :recommended-news="recommendedNews"
          :timeline-topic-id="timelineTopicId"
          :timeline-topic-name="timelineTopicName"
          :timeline-news-count="newsDetail?.timeline_news_count ?? 0"
          @view-timeline="handleViewTimeline"
        />
      </aside>
    </div>

    <TimelineDrawer
      v-model="timelineDrawerVisible"
      :topic-id="selectedTopicId"
      :topic-name="selectedTopicName"
    />
  </main>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getNewsDetail, recordBrowse, type NewsDetail, type NewsItem } from '@/api/news'
import {
  createNewsComment,
  deleteNewsComment,
  favoriteNews,
  getNewsComments,
  likeComment,
  likeNews,
  replyComment,
  unfavoriteNews,
  unlikeNews,
} from '@/api/interaction'
import { useUserStore } from '@/stores/user'
import { useAIDraftStore } from '@/stores/aiDraft'
import NewsMeta from '@/components/news/NewsMeta.vue'
import NewsDetailContent from '@/components/news/NewsDetailContent.vue'
import NewsDetailSidePanel from '@/components/news/NewsDetailSidePanel.vue'
import TimelineDrawer from '@/components/timeline/TimelineDrawer.vue'
import LikeButton from '@/components/interaction/LikeButton.vue'
import FavoriteButton from '@/components/interaction/FavoriteButton.vue'
import ShareButton from '@/components/interaction/ShareButton.vue'
import CommentBox from '@/components/interaction/CommentBox.vue'
import CommentList from '@/components/interaction/CommentList.vue'
import type { CommentItemData as RichCommentItemData, CommentMediaJson } from '@/components/interaction/CommentItem.vue'

type ActionType = 'like' | 'unlike' | 'favorite' | 'unfavorite' | 'comment-like' | ''

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const aiDraft = useAIDraftStore()

type NewsDetailWithTopic = NewsDetail & { topic_id?: number | null }

const newsDetail = ref<NewsDetailWithTopic | null>(null)
const comments = ref<RichCommentItemData[]>([])
const loading = ref(false)
const loadingComments = ref(false)
const submittingComment = ref(false)
const actionLoading = ref<ActionType>('')
const deletingCommentId = ref<number | null>(null)
const commentLikeLoadingId = ref<number | null>(null)
const error = ref('')
const commentTotal = ref(0)
const replyingId = ref<number | null>(null)
const timelineDrawerVisible = ref(false)
const selectedTopicId = ref<number | string | null>(null)
const selectedTopicName = ref('')
const newsId = computed(() => String(route.params.id ?? '').trim())

const recommendedNews = computed<NewsItem[]>(() => newsDetail.value?.recommended_news ?? [])
const timelineTopicId = computed(() => newsDetail.value?.topic_id ?? null)
const timelineTopicName = computed(
  () => (newsDetail.value as (NewsDetailWithTopic & { topic_name?: string }) | null)?.topic_name || newsDetail.value?.category_name || '',
)

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
    newsDetail.value = result as NewsDetailWithTopic

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

function handleViewTimeline() {
  if (!userStore.isLoggedIn) {
    ElMessage.warning('请先登录后查看事件脉络')
    goToLogin()
    return
  }

  if (!timelineTopicId.value) {
    ElMessage.warning('当前新闻暂无事件脉络')
    return
  }

  selectedTopicId.value = timelineTopicId.value
  selectedTopicName.value = timelineTopicName.value
  timelineDrawerVisible.value = true
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

async function handleCreateComment(content: string, mediaJson?: CommentMediaJson | null) {
  if (!requireLogin() || !newsDetail.value) {
    return
  }

  submittingComment.value = true

  try {
    await createNewsComment(newsDetail.value.id, {
      content: content || ' ',
      media_json: mediaJson ?? null,
    })
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

async function handleReplyComment(comment: RichCommentItemData, content: string, mediaJson?: CommentMediaJson | null) {
  if (!requireLogin() || !newsDetail.value) {
    return
  }

  if (content === '__toggle__') {
    replyingId.value = replyingId.value === comment.id ? null : comment.id
    return
  }

  if (!content && !mediaJson) {
    replyingId.value = null
    return
  }

  submittingComment.value = true

  try {
    await replyComment(comment.id, { content, media_json: mediaJson ?? null })
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

async function handleLikeComment(comment: RichCommentItemData) {
  if (!requireLogin()) {
    return
  }

  commentLikeLoadingId.value = comment.id

  try {
    await likeComment(comment.id)
  } catch (requestError) {
    ElMessage.error(requestError instanceof Error ? requestError.message : '评论点赞失败')
  } finally {
    commentLikeLoadingId.value = null
  }
}

async function handleDeleteComment(comment: RichCommentItemData) {
  if (!requireLogin() || !newsDetail.value) {
    return
  }

  try {
    await ElMessageBox.confirm('确定删除这条评论吗？', '删除评论', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning',
    })
  } catch {
    return
  }

  deletingCommentId.value = comment.id
  try {
    const result = await deleteNewsComment(comment.id)
    await loadComments()
    newsDetail.value = {
      ...newsDetail.value,
      comment_count: result.comment_count ?? Math.max(0, newsDetail.value.comment_count - 1),
    }
    ElMessage.success('评论已删除')
  } catch (requestError) {
    ElMessage.error(requestError instanceof Error ? requestError.message : '删除评论失败')
  } finally {
    deletingCommentId.value = null
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
