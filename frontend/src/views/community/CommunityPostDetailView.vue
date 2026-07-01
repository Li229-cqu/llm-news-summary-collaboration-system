<template>
  <main class="post-detail-page">
    <div class="detail-header">
      <el-button text @click="goBack">
        <el-icon><ArrowLeft /></el-icon>
        返回社区
      </el-button>
      <el-breadcrumb separator="/">
        <el-breadcrumb-item :to="{ path: '/community' }">社区广场</el-breadcrumb-item>
        <el-breadcrumb-item>帖子详情</el-breadcrumb-item>
      </el-breadcrumb>
    </div>

    <div v-if="loading" class="loading-area"><el-spinner /></div>

    <div v-else-if="error" class="empty-area">
      <el-empty :description="error" />
    </div>

    <div v-else-if="post" class="detail-layout">
      <!-- 左侧主内容区 -->
      <div class="detail-main">
        <!-- 帖子内容卡片 -->
        <el-card class="detail-card" shadow="never">
          <div class="post-header">
            <el-avatar :src="normalizeAvatarUrl(post.avatar)" :text="post.author.slice(0, 1)" :size="44" />
            <div class="post-meta">
              <span class="post-author">{{ post.author }}</span>
              <span class="post-time">{{ formatTime(post.created_at) }}</span>
            </div>
          </div>
          <h1 class="post-title">{{ post.title }}</h1>
          <div class="post-content">{{ post.content }}</div>
          <div v-if="post.tags && post.tags.length" class="post-tags">
            <el-tag v-for="tag in post.tags" :key="tag" size="small" type="info">{{ tag }}</el-tag>
          </div>
          <div
            v-if="post.related_news_title"
            class="post-related-news"
            @click.stop="handleRelatedNewsClick"
          >
            <el-icon><Link /></el-icon>
            <span>关联新闻：{{ post.related_news_title }}</span>
          </div>
          <div class="post-stats">
            <span>{{ post.views }} 阅读</span>
            <span>{{ post.likes }} 点赞</span>
            <span>{{ post.comments }} 评论</span>
            <span>{{ post.favorite_count ?? 0 }} 收藏</span>
          </div>
          <div class="post-actions-bar">
            <el-button
              :class="{ 'action-active': post.liked }"
              @click="handleLike"
            >
              <el-icon><Pointer /></el-icon>
              {{ post.liked ? '已点赞' : '点赞' }}
            </el-button>
            <el-button
              :class="{ 'action-favorited': post.is_favorited }"
              @click="handleFavorite"
            >
              <el-icon>
                <StarFilled v-if="post.is_favorited" />
                <Star v-else />
              </el-icon>
              {{ post.is_favorited ? '已收藏' : '收藏' }}
            </el-button>
          </div>
        </el-card>

        <!-- AI 评论总结 -->
        <el-card class="detail-card comment-summary-section" shadow="never" v-if="comments.length > 0">
          <div class="summary-header">
            <span class="summary-title">AI 评论总结</span>
            <el-button
              type="primary"
              link
              size="small"
              :loading="loadingCommentsSummary"
              @click="handleGenerateSummary"
            >
              <el-icon><Aim /></el-icon>
              {{ commentsSummary ? '重新总结' : 'AI 总结评论' }}
            </el-button>
          </div>
          <div v-if="loadingCommentsSummary" class="loading-container"><el-spinner /></div>
          <div v-else-if="commentsSummary" class="summary-body">
            <div class="summary-content"><p>{{ commentsSummary.summary }}</p></div>
            <div class="summary-tags">
              <el-tag :type="getSentimentType(commentsSummary.sentiment)" size="small">
                {{ getSentimentText(commentsSummary.sentiment) }}
              </el-tag>
              <el-tag v-for="kw in commentsSummary.keywords.slice(0, 3)" :key="kw" type="info" size="small">
                {{ kw }}
              </el-tag>
            </div>
            <div v-if="commentsSummary.key_points && commentsSummary.key_points.length" class="summary-points">
              <div class="summary-points-title">主要观点</div>
              <ul>
                <li v-for="(point, idx) in commentsSummary.key_points" :key="idx">{{ point }}</li>
              </ul>
            </div>
          </div>
          <div v-else class="summary-hint">点击上方按钮生成 AI 评论总结</div>
        </el-card>

        <!-- 评论区域 -->
        <el-card class="detail-card" shadow="never">
          <div class="comments-header">
            <h3>评论 ({{ post.comments }})</h3>
            <span class="comments-hint">支持图片和表情</span>
          </div>

          <!-- 发表评论 -->
          <div class="comment-composer">
            <el-input
              v-model="newCommentText"
              type="textarea"
              :rows="3"
              placeholder="写下你的评论..."
              maxlength="1000"
              show-word-limit
            />
            <div class="composer-actions">
              <div class="composer-tools">
                <el-button text @click="toggleEmojiPicker">
                  <el-icon><PictureFilled /></el-icon>
                </el-button>
                <el-button text @click="triggerImageUpload">
                  <el-icon><PictureFilled /></el-icon>
                </el-button>
                <input
                  ref="imageUploadRef"
                  type="file"
                  accept="image/*"
                  style="display:none"
                  @change="handleImageSelect"
                />
                <span v-if="selectedImageName" class="image-name">{{ selectedImageName }}</span>
              </div>
              <el-button
                type="primary"
                :loading="submittingComment"
                :disabled="!newCommentText.trim() && !selectedImageFile"
                @click="handleCreateComment"
              >
                发表评论
              </el-button>
            </div>
          </div>

          <div v-if="loadingComments" class="loading-container"><el-spinner /></div>
          <div v-else-if="comments.length === 0" class="empty-state">
            <el-empty description="暂无评论，快来发第一条吧" />
          </div>
          <div v-else class="comments-list">
            <CommentItem
              v-for="comment in comments"
              :key="comment.id"
              :comment="comment"
              :replying-id="replyingCommentId"
              :loading-like-id="commentLikeLoadingId"
              :loading-reply="commentReplyLoadingId === comment.id"
              :deleting-id="commentDeleteLoadingId"
              :current-user-id="currentUserId"
              :current-user-role="currentUserRole"
              @like="handleCommentLike"
              @reply="handleCommentReply"
              @delete="handleCommentDelete"
              @reload-comments="loadComments"
            />
          </div>
        </el-card>
      </div>

      <!-- 右侧辅助栏 -->
      <div class="detail-sidebar">
        <el-card v-if="post.related_news_title" class="sidebar-card" shadow="never">
          <h4 class="sidebar-card-title">关联新闻</h4>
          <div class="sidebar-related-news" @click="handleRelatedNewsClick">
            <el-icon><Link /></el-icon>
            <span>{{ post.related_news_title }}</span>
          </div>
        </el-card>

        <el-card class="sidebar-card" shadow="never">
          <h4 class="sidebar-card-title">作者</h4>
          <div class="sidebar-author">
            <el-avatar :src="normalizeAvatarUrl(post.avatar)" :text="post.author.slice(0, 1)" :size="36" />
            <div class="author-info">
              <span class="author-name">{{ post.author }}</span>
              <span class="author-time">发布于 {{ formatTime(post.created_at) }}</span>
            </div>
          </div>
        </el-card>

        <HotTopicsSidebar
          :list="hotSearchList"
          :loading="loadingHotSearch"
          @open-hot-topic="handleHotSearchClick"
        />
      </div>
    </div>
  </main>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, Link, Pointer, Star, StarFilled, Aim, PictureFilled } from '@element-plus/icons-vue'
import {
  getPostDetail,
  getComments,
  createComment,
  replyComment,
  deleteComment,
  likeComment,
  toggleLike,
  toggleFavorite,
  unfavoritePost,
  getHotSearch,
  generateCommentsSummary,
  getCommentsSummary,
  type CommunityPost,
  type HotSearchItem,
  type CommentsSummaryResponse,
} from '@/api/community'
import { useUserStore } from '@/stores/user'
import HotTopicsSidebar from '@/components/community/HotTopicsSidebar.vue'
import CommentItem, {
  type CommentItemData as RichCommentItemData,
  type CommentMediaJson,
} from '@/components/interaction/CommentItem.vue'
import { markReplyForceVisible, scrollToComment } from '@/utils/commentVisibility'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const currentUserId = computed(() => userStore.userInfo?.id ?? null)
const currentUserRole = computed(() => userStore.role)

// ─── Post Data ──────────────────────────────────
const { id } = route.params
const post = ref<CommunityPost | null>(null)
const loading = ref(true)
const error = ref('')

// ─── Comments ──────────────────────────────────
const comments = ref<RichCommentItemData[]>([])
const loadingComments = ref(false)
const submittingComment = ref(false)
const newCommentText = ref('')
const replyingCommentId = ref<number | null>(null)
const commentLikeLoadingId = ref<number | null>(null)
const commentReplyLoadingId = ref<number | null>(null)
const commentDeleteLoadingId = ref<number | null>(null)
const selectedImageFile = ref<File | null>(null)
const selectedImageName = ref('')
const imageUploadRef = ref<HTMLInputElement>()

// ─── AI Summary ─────────────────────────────────
const commentsSummary = ref<CommentsSummaryResponse | null>(null)
const loadingCommentsSummary = ref(false)

// ─── Hot Search ─────────────────────────────────
const hotSearchList = ref<HotSearchItem[]>([])
const loadingHotSearch = ref(false)

// ─── Navigation ─────────────────────────────────
function goBack() {
  router.push('/community')
}

// ─── Load Data ──────────────────────────────────
async function loadPostDetail() {
  loading.value = true
  error.value = ''
  try {
    const result = await getPostDetail(Number(id))
    post.value = result
    await loadComments()
  } catch {
    error.value = '帖子不存在或加载失败'
    post.value = null
  } finally {
    loading.value = false
  }
}

async function loadComments() {
  if (!post.value) return
  loadingComments.value = true
  try {
    const result = await getComments(post.value.id)
    comments.value = result.list || []
  } finally {
    loadingComments.value = false
  }
}

async function loadHotSearch() {
  loadingHotSearch.value = true
  try {
    hotSearchList.value = await getHotSearch({ limit: 10 })
  } finally {
    loadingHotSearch.value = false
  }
}

// ─── Like ───────────────────────────────────────
async function handleLike() {
  if (!post.value) return
  try {
    const result = await toggleLike(post.value.id)
    post.value.likes = result.count
    post.value.liked = result.liked
  } catch { console.error('点赞失败') }
}

// ─── Favorite ───────────────────────────────────
async function handleFavorite() {
  if (!post.value) return
  try {
    if (post.value.is_favorited) {
      const result = await unfavoritePost(post.value.id)
      post.value.is_favorited = false
      post.value.favorite_count = result.favorite_count
    } else {
      const result = await toggleFavorite(post.value.id)
      post.value.is_favorited = result.is_favorited
      post.value.favorite_count = result.favorite_count
    }
  } catch { console.error('收藏操作失败') }
}

// ─── Comment ────────────────────────────────────
async function handleCreateComment() {
  if (!post.value) return
  const content = newCommentText.value.trim()
  if (!content && !selectedImageFile.value) return

  let mediaJson: CommentMediaJson | null = null
  if (selectedImageFile.value) {
    mediaJson = { images: [selectedImageFile.value.name] }
  }

  submittingComment.value = true
  try {
    const newComment = await createComment(post.value.id, {
      content: content || ' ',
      media_json: mediaJson,
    })
    const item: RichCommentItemData = { ...newComment, replies: newComment.replies || [] }
    comments.value.unshift(item)
    post.value.comment_count = (post.value.comment_count || 0) + 1
    post.value.comments = (post.value.comments || 0) + 1
    newCommentText.value = ''
    selectedImageFile.value = null
    selectedImageName.value = ''
    markReplyForceVisible(item.id)
    await nextTick()
    scrollToComment(item.id)
  } catch {
    ElMessage.error('评论失败，请稍后重试')
  } finally {
    submittingComment.value = false
  }
}

async function handleCommentLike(comment: RichCommentItemData) {
  if (!post.value) return
  commentLikeLoadingId.value = comment.id
  try {
    await likeComment(comment.id)
  } catch {
    ElMessage.error('评论点赞失败')
  } finally {
    commentLikeLoadingId.value = null
  }
}

async function handleCommentReply(comment: RichCommentItemData, content: string, mediaJson?: CommentMediaJson | null) {
  if (!post.value) return
  if (content === '__toggle__') {
    replyingCommentId.value = replyingCommentId.value === comment.id ? null : comment.id
    return
  }
  if (!content.trim() && !mediaJson) { replyingCommentId.value = null; return }

  commentReplyLoadingId.value = comment.id
  try {
    const newReply = await replyComment(comment.id, { content, media_json: mediaJson })
    replyingCommentId.value = null
    const item: RichCommentItemData = { ...newReply, replies: newReply.replies || [] }
    const parent = findPostCommentById(comments.value, comment.id)
    if (parent) {
      if (!parent.replies) parent.replies = []
      parent.replies.push(item)
    } else {
      comments.value.unshift(item)
    }
    if (post.value) {
      post.value.comment_count = (post.value.comment_count || 0) + 1
      post.value.comments = (post.value.comments || 0) + 1
    }
    markReplyForceVisible(item.id)
    await nextTick()
    scrollToComment(item.id)
  } catch {
    ElMessage.error('回复评论失败')
  } finally {
    commentReplyLoadingId.value = null
  }
}

function findPostCommentById(list: RichCommentItemData[], id: number): RichCommentItemData | null {
  for (const item of list) {
    if (item.id === id) return item
    if (item.replies) {
      const found = findPostCommentById(item.replies, id)
      if (found) return found
    }
  }
  return null
}

async function handleCommentDelete(comment: RichCommentItemData) {
  if (!post.value) return
  try {
    await ElMessageBox.confirm('确定删除这条评论吗？', '删除评论', {
      confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning',
    })
  } catch { return }
  commentDeleteLoadingId.value = comment.id
  try {
    const result = await deleteComment(comment.id)
    await loadComments()
    post.value.comment_count = result.comment_count ?? Math.max(0, (post.value.comment_count || 0) - 1)
    post.value.comments = post.value.comment_count || 0
    ElMessage.success('评论已删除')
  } catch {
    ElMessage.error('删除评论失败')
  } finally {
    commentDeleteLoadingId.value = null
  }
}

// ─── AI Summary ─────────────────────────────────
async function handleGenerateSummary() {
  if (!post.value) return
  const allComments = collectCommentContents(comments.value)
  if (allComments.length === 0) { ElMessage.info('暂无评论内容可总结'); return }
  loadingCommentsSummary.value = true
  try {
    commentsSummary.value = await generateCommentsSummary(allComments)
  } catch {
    commentsSummary.value = null
    ElMessage.error('总结失败')
  } finally {
    loadingCommentsSummary.value = false
  }
}

function collectCommentContents(items: RichCommentItemData[]): string[] {
  const result: string[] = []
  function traverse(list: RichCommentItemData[]) {
    for (const item of list) {
      if (item.content?.trim()) result.push(item.content.trim())
      if (item.replies?.length) traverse(item.replies)
    }
  }
  traverse(items)
  return result
}

// ─── Related News ───────────────────────────────
function handleRelatedNewsClick() {
  if (post.value?.related_news_id) {
    router.push(`/news/${post.value.related_news_id}`)
  }
}

// ─── Hot Search ─────────────────────────────────
function handleHotSearchClick(item: HotSearchItem) {
  if (item.target_type === 'post' || item.target_type === 'community_post') {
    router.push(`/community/posts/${item.target_id}`)
  }
}

// ─── Image / Emoji ──────────────────────────────
function toggleEmojiPicker() {}
function triggerImageUpload() { imageUploadRef.value?.click() }
function handleImageSelect(e: Event) {
  const input = e.target as HTMLInputElement
  if (input.files?.[0]) {
    selectedImageFile.value = input.files[0]
    selectedImageName.value = input.files[0].name
  }
}

// ─── Utils ──────────────────────────────────────
function normalizeAvatarUrl(url?: string): string {
  if (!url) return ''
  if (url.startsWith('http://') || url.startsWith('https://') || url.startsWith('data:image/')) return url
  const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'
  return `${baseURL.replace(/\/$/, '')}/${url.replace(/^\//, '')}`
}
function formatTime(timeStr: string) {
  const date = new Date(timeStr)
  return date.toLocaleString('zh-CN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}
function getSentimentType(sentiment: string) {
  switch (sentiment) { case 'positive': return 'success'; case 'negative': return 'danger'; default: return 'warning' }
}
function getSentimentText(sentiment: string) {
  switch (sentiment) { case 'positive': return '正面'; case 'negative': return '负面'; default: return '中立' }
}

import { nextTick } from 'vue'

onMounted(() => {
  loadPostDetail()
  loadHotSearch()
})
</script>

<style scoped>
.post-detail-page {
  max-width: 1280px;
  margin: 0 auto;
  padding: 24px 32px 56px;
  min-height: 100vh;
  background:
    radial-gradient(circle at 18% 10%, rgba(220, 38, 38, 0.08), transparent 28%),
    linear-gradient(180deg, #fef2f2 0%, #fef7f7 100%);
}

/* ── Header ── */
.detail-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
}

.loading-area, .empty-area {
  display: flex;
  justify-content: center;
  padding: 80px 0;
}

/* ── Layout ── */
.detail-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 360px;
  gap: 28px;
  align-items: start;
}

.detail-main {
  display: flex;
  flex-direction: column;
  gap: 20px;
  min-width: 0;
}

.detail-card {
  border: 1px solid rgba(210, 222, 238, 0.86);
  border-radius: 12px;
  box-shadow: 0 8px 24px rgba(34, 78, 130, 0.08);
  background: rgba(255, 255, 255, 0.94);
}
.detail-card :deep(.el-card__body) { padding: 24px 28px; }

/* ── Post Content ── */
.post-header {
  display: flex; align-items: center; gap: 12px; margin-bottom: 16px;
}
.post-meta { display: flex; flex-direction: column; }
.post-author { font-weight: 600; font-size: 15px; }
.post-time { font-size: 12px; color: #999; }

.post-title {
  font-size: 24px; font-weight: 700; color: #111827; margin: 0 0 16px; line-height: 1.4;
}
.post-content {
  color: #333; line-height: 1.8; font-size: 15px; margin-bottom: 16px; white-space: pre-wrap; word-break: break-word;
}
.post-tags { margin-bottom: 16px; display: flex; flex-wrap: wrap; gap: 8px; }

.post-related-news {
  display: flex; align-items: center; gap: 6px; margin-bottom: 16px;
  padding: 10px 14px; background: #fef2f2; border-radius: 8px;
  font-size: 14px; color: #dc2626; cursor: pointer;
}
.post-related-news:hover { background: #fee2e2; }

.post-stats {
  display: flex; gap: 28px; margin-bottom: 16px; color: #999; font-size: 14px;
}
.post-actions-bar {
  display: flex; gap: 12px; padding-top: 16px; border-top: 1px solid #e5e7eb;
}
.post-actions-bar .action-active { color: #dc2626; }
.post-actions-bar .action-favorited { color: #f59e0b; }

/* ── Summary ── */
.summary-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }
.summary-title { font-weight: 700; font-size: 16px; color: #1f2937; }
.summary-body {}
.summary-content p { color: #333; line-height: 1.7; margin: 0 0 12px; }
.summary-tags { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 8px; }
.summary-points { margin-top: 12px; padding-top: 12px; border-top: 1px solid #e0e0e0; }
.summary-points-title { font-size: 13px; font-weight: 600; color: #374151; margin-bottom: 8px; }
.summary-points ul { margin: 0; padding-left: 20px; }
.summary-points li { font-size: 13px; color: #6b7280; line-height: 1.8; }
.summary-hint { color: #9ca3af; font-size: 14px; text-align: center; padding: 16px 0; }

/* ── Comments ── */
.comments-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px; }
.comments-header h3 { margin: 0; font-size: 18px; font-weight: 700; color: #1f2937; }
.comments-hint { font-size: 12px; color: #9ca3af; }

.comment-composer {
  margin-bottom: 24px; padding-bottom: 24px; border-bottom: 1px solid #e5e7eb;
}
.composer-actions {
  display: flex; align-items: center; justify-content: space-between; margin-top: 12px;
}
.composer-tools { display: flex; align-items: center; gap: 4px; }
.image-name { font-size: 12px; color: #6b7280; margin-left: 4px; }

.loading-container { display: flex; justify-content: center; padding: 24px; }
.empty-state { padding: 24px; }

.comments-list {
  display: flex; flex-direction: column; gap: 16px;
}

/* ── Sidebar ── */
.detail-sidebar {
  display: flex; flex-direction: column; gap: 18px;
}
.sidebar-card {
  border: 1px solid rgba(210, 222, 238, 0.86);
  border-radius: 12px;
  box-shadow: 0 8px 24px rgba(34, 78, 130, 0.08);
  background: rgba(255, 255, 255, 0.94);
}
.sidebar-card-title { font-size: 16px; font-weight: 700; color: #111827; margin: 0 0 12px; }
.sidebar-related-news {
  display: flex; align-items: center; gap: 6px; color: #dc2626;
  font-size: 14px; cursor: pointer; line-height: 1.5;
}
.sidebar-related-news:hover { color: #b91c1c; }
.sidebar-author { display: flex; align-items: center; gap: 10px; }
.author-info { display: flex; flex-direction: column; }
.author-name { font-weight: 600; font-size: 14px; color: #1f2937; }
.author-time { font-size: 12px; color: #9ca3af; }

/* ── Responsive ── */
@media (max-width: 1100px) {
  .detail-layout { grid-template-columns: 1fr; }
}
@media (max-width: 768px) {
  .post-detail-page { padding: 16px; }
}
</style>
