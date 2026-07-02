<template>
  <div class="post-detail-panel">
    <!-- 返回列表 -->
    <div class="panel-back-bar" @click="$emit('back')">
      <el-button text>
        <el-icon><ArrowLeft /></el-icon>
        返回列表
      </el-button>
    </div>

    <!-- 加载/报错 -->
    <div v-if="loading" class="panel-loading"><el-spinner /></div>
    <div v-else-if="error" class="panel-empty"><el-empty :description="error" /></div>

    <!-- 详情主体 -->
    <div v-else-if="post" class="panel-body">
      <!-- 帖子内容卡片 -->
      <el-card class="post-card-detail" shadow="never">
        <div class="post-header">
          <el-avatar :src="normalizeAvatarUrl(post.avatar)" :text="post.author.slice(0, 1)" :size="44" />
          <div class="post-meta">
            <span class="post-author">{{ post.author }}</span>
            <span class="post-time">{{ formatTime(post.created_at) }}</span>
          </div>
        </div>
        <h1 class="post-title">{{ post.title }}</h1>
        <div class="post-content">{{ post.content }}</div>

        <!-- 帖子图片 -->
        <div v-if="detailImages.length" class="post-images">
          <div class="post-images-title">图片</div>
          <div class="post-images-grid">
            <el-image
              v-for="(img, idx) in detailImages" :key="idx"
              :src="resolveImageUrl(img)" fit="contain"
              class="post-detail-image"
              :preview-src-list="detailPreviewUrls" preview-teleported
            />
          </div>
        </div>

        <!-- 标签 -->
        <div v-if="post.tags && post.tags.length" class="post-tags">
          <el-tag v-for="tag in post.tags" :key="tag" size="small" type="info">{{ tag }}</el-tag>
        </div>

        <!-- 关联新闻 -->
        <div v-if="post.related_news_title" class="post-related-news" @click.stop="handleRelatedNewsClick">
          <el-icon><Link /></el-icon>
          <span>关联新闻：{{ post.related_news_title }}</span>
        </div>

        <!-- 统计数据 -->
        <div class="post-stats">
          <span>{{ post.views }} 阅读</span>
          <span>{{ post.likes }} 点赞</span>
          <span>{{ post.comments }} 评论</span>
          <span>{{ post.favorite_count ?? 0 }} 收藏</span>
        </div>

        <!-- 点赞/收藏按钮 -->
        <div class="post-actions-bar">
          <el-button :class="{ 'action-active': post.liked }" @click="handleLike">
            <el-icon><Pointer /></el-icon>
            {{ post.liked ? '已点赞' : '点赞' }}
          </el-button>
          <el-button :class="{ 'action-favorited': post.is_favorited }" @click="handleFavorite">
            <el-icon><StarFilled v-if="post.is_favorited" /><Star v-else /></el-icon>
            {{ post.is_favorited ? '已收藏' : '收藏' }}
          </el-button>
        </div>
      </el-card>

      <!-- AI 评论总结 -->
      <el-card v-if="comments.length > 0" class="post-card-detail" shadow="never">
        <div class="summary-header">
          <span class="summary-title">AI 评论总结</span>
          <el-button type="primary" link size="small" :loading="loadingCommentsSummary" @click="handleGenerateSummary">
            <el-icon><Aim /></el-icon>
            {{ commentsSummary ? '重新总结' : 'AI 总结评论' }}
          </el-button>
        </div>
        <div v-if="loadingCommentsSummary" class="loading-container"><el-spinner /></div>
        <div v-else-if="commentsSummary" class="summary-body">
          <div class="summary-content"><p>{{ commentsSummary.summary }}</p></div>
          <div class="summary-tags">
            <el-tag :type="getSentimentType(commentsSummary.sentiment)" size="small">{{ getSentimentText(commentsSummary.sentiment) }}</el-tag>
            <el-tag v-for="kw in commentsSummary.keywords.slice(0, 3)" :key="kw" type="info" size="small">{{ kw }}</el-tag>
          </div>
          <div v-if="commentsSummary.key_points?.length" class="summary-points">
            <div class="summary-points-title">主要观点</div>
            <ul><li v-for="(point, idx) in commentsSummary.key_points" :key="idx">{{ point }}</li></ul>
          </div>
        </div>
        <div v-else class="summary-hint">点击上方按钮生成 AI 评论总结</div>
      </el-card>

      <!-- 评论区域 -->
      <el-card class="post-card-detail" shadow="never">
        <div class="comments-header">
          <h3>评论 ({{ post.comments }})</h3>
          <span class="comments-hint">支持图片和表情</span>
        </div>

        <!-- 发表评论 -->
        <div class="comment-composer">
          <el-input v-model="newCommentText" type="textarea" :rows="3" placeholder="写下你的评论..." maxlength="1000" show-word-limit />
          <div class="composer-actions">
            <div class="composer-tools">
              <el-button text @click="toggleEmojiPicker"><el-icon><PictureFilled /></el-icon></el-button>
              <el-button text @click="triggerImageUpload"><el-icon><PictureFilled /></el-icon></el-button>
              <input ref="imageUploadRef" type="file" accept="image/*" style="display:none" @change="handleImageSelect" />
              <span v-if="selectedImageName" class="image-name">{{ selectedImageName }}</span>
            </div>
            <el-button type="primary" :loading="submittingComment" :disabled="!newCommentText.trim() && !selectedImageFile" @click="handleCreateComment">
              发表评论
            </el-button>
          </div>
        </div>

        <!-- 评论列表 -->
        <div v-if="loadingComments" class="loading-container"><el-spinner /></div>
        <div v-else-if="comments.length === 0" class="empty-state"><el-empty description="暂无评论，快来发第一条吧" /></div>
        <div v-else class="comments-list">
          <CommentItem
            v-for="comment in comments" :key="comment.id"
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
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
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
  generateCommentsSummary,
  type CommunityPost,
  type CommentsSummaryResponse,
} from '@/api/community'
import { useUserStore } from '@/stores/user'
import CommentItem, {
  type CommentItemData as RichCommentItemData,
  type CommentMediaJson,
} from '@/components/interaction/CommentItem.vue'
import { markReplyForceVisible, scrollToComment } from '@/utils/commentVisibility'
import { resolveImageUrl } from '@/utils/media'

const props = defineProps<{
  postId: number | string
}>()

const emit = defineEmits<{
  (e: 'back'): void
  (e: 'updated'): void
  (e: 'openRelatedNews', newsId: number | string): void
}>()

const router = useRouter()
const userStore = useUserStore()
const currentUserId = computed(() => userStore.userInfo?.id ?? null)
const currentUserRole = computed(() => userStore.role)

// ─── Post Data ──
const post = ref<CommunityPost | null>(null)
const loading = ref(true)
const error = ref('')

// ─── Comments ──
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

// ─── AI Summary ──
const commentsSummary = ref<CommentsSummaryResponse | null>(null)
const loadingCommentsSummary = ref(false)

// ─── Images ──
const detailImages = computed(() => {
  const imgs = post.value?.images
  return Array.isArray(imgs) ? imgs.filter(Boolean) : []
})
const detailPreviewUrls = computed(() =>
  detailImages.value.map(url => resolveImageUrl(url))
)

// ─── Load ──
watch(() => props.postId, () => { loadPostDetail(); commentsSummary.value = null }, { immediate: true })

async function loadPostDetail() {
  loading.value = true; error.value = ''
  try {
    post.value = await getPostDetail(Number(props.postId))
    await loadComments()
  } catch {
    error.value = '帖子不存在或加载失败'; post.value = null
  } finally { loading.value = false }
}

async function loadComments() {
  if (!post.value) return; loadingComments.value = true
  try { comments.value = (await getComments(post.value.id)).list || [] } finally { loadingComments.value = false }
}

// ─── Like ──
async function handleLike() {
  if (!post.value) return
  try { const r = await toggleLike(post.value.id); post.value.likes = r.count; post.value.liked = r.liked; emit('updated') } catch { console.error('点赞失败') }
}

// ─── Favorite ──
async function handleFavorite() {
  if (!post.value) return
  try {
    if (post.value.is_favorited) { const r = await unfavoritePost(post.value.id); post.value.is_favorited = false; post.value.favorite_count = r.favorite_count }
    else { const r = await toggleFavorite(post.value.id); post.value.is_favorited = r.is_favorited; post.value.favorite_count = r.favorite_count }
    emit('updated')
  } catch { console.error('收藏操作失败') }
}

// ─── Comment ──
async function handleCreateComment() {
  if (!post.value) return; const content = newCommentText.value.trim()
  if (!content && !selectedImageFile.value) return
  let mediaJson: CommentMediaJson | null = null
  if (selectedImageFile.value) mediaJson = { images: [selectedImageFile.value.name] }
  submittingComment.value = true
  try {
    const newComment = await createComment(post.value.id, { content: content || ' ', media_json: mediaJson })
    const item: RichCommentItemData = { ...newComment, replies: newComment.replies || [] }
    comments.value.unshift(item)
    post.value.comment_count = (post.value.comment_count || 0) + 1; post.value.comments = (post.value.comments || 0) + 1
    newCommentText.value = ''; selectedImageFile.value = null; selectedImageName.value = ''
    markReplyForceVisible(item.id); await nextTick(); scrollToComment(item.id); emit('updated')
  } catch { ElMessage.error('评论失败，请稍后重试') } finally { submittingComment.value = false }
}

async function handleCommentLike(comment: RichCommentItemData) {
  commentLikeLoadingId.value = comment.id
  try { await likeComment(comment.id) } catch { ElMessage.error('评论点赞失败') } finally { commentLikeLoadingId.value = null }
}

async function handleCommentReply(comment: RichCommentItemData, content: string, mediaJson?: CommentMediaJson | null) {
  if (!post.value) return
  if (content === '__toggle__') { replyingCommentId.value = replyingCommentId.value === comment.id ? null : comment.id; return }
  if (!content.trim() && !mediaJson) { replyingCommentId.value = null; return }
  commentReplyLoadingId.value = comment.id
  try {
    const newReply = await replyComment(comment.id, { content, media_json: mediaJson })
    replyingCommentId.value = null
    const item: RichCommentItemData = { ...newReply, replies: newReply.replies || [] }
    const parent = findPostCommentById(comments.value, comment.id)
    if (parent) { if (!parent.replies) parent.replies = []; parent.replies.push(item) }
    else { comments.value.unshift(item) }
    if (post.value) { post.value.comment_count = (post.value.comment_count || 0) + 1; post.value.comments = (post.value.comments || 0) + 1 }
    markReplyForceVisible(item.id); await nextTick(); scrollToComment(item.id); emit('updated')
  } catch { ElMessage.error('回复评论失败') } finally { commentReplyLoadingId.value = null }
}

function findPostCommentById(list: RichCommentItemData[], id: number): RichCommentItemData | null {
  for (const item of list) { if (item.id === id) return item; if (item.replies) { const found = findPostCommentById(item.replies, id); if (found) return found } }
  return null
}

async function handleCommentDelete(comment: RichCommentItemData) {
  if (!post.value) return
  try { await ElMessageBox.confirm('确定删除这条评论吗？', '删除评论', { confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning' }) } catch { return }
  commentDeleteLoadingId.value = comment.id
  try {
    const result = await deleteComment(comment.id)
    await loadComments()
    post.value.comment_count = result.comment_count ?? Math.max(0, (post.value.comment_count || 0) - 1)
    post.value.comments = post.value.comment_count || 0
    ElMessage.success('评论已删除'); emit('updated')
  } catch { ElMessage.error('删除评论失败') } finally { commentDeleteLoadingId.value = null }
}

// ─── AI Summary ──
async function handleGenerateSummary() {
  if (!post.value) return
  const allComments = collectCommentContents(comments.value)
  if (allComments.length === 0) { ElMessage.info('暂无评论内容可总结'); return }
  loadingCommentsSummary.value = true
  try { commentsSummary.value = await generateCommentsSummary(allComments) } catch { commentsSummary.value = null; ElMessage.error('总结失败') } finally { loadingCommentsSummary.value = false }
}

function collectCommentContents(items: RichCommentItemData[]): string[] {
  const result: string[] = []
  function traverse(list: RichCommentItemData[]) { for (const item of list) { if (item.content?.trim()) result.push(item.content.trim()); if (item.replies?.length) traverse(item.replies) } }
  traverse(items); return result
}

// ─── Related News ──
function handleRelatedNewsClick() {
  if (post.value?.related_news_id) emit('openRelatedNews', post.value.related_news_id)
}

// ─── Image / Emoji ──
function toggleEmojiPicker() {}
function triggerImageUpload() { imageUploadRef.value?.click() }
function handleImageSelect(e: Event) {
  const input = e.target as HTMLInputElement
  if (input.files?.[0]) { selectedImageFile.value = input.files[0]; selectedImageName.value = input.files[0].name }
}

// ─── Utils ──
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
</script>

<style scoped>
.post-detail-panel { width: 100%; }
.panel-back-bar { margin-bottom: 16px; }
.panel-loading, .panel-empty { display: flex; justify-content: center; padding: 80px 0; }
.panel-body { display: flex; flex-direction: column; gap: 20px; }

.post-card-detail {
  border: 1px solid rgba(210, 222, 238, 0.86);
  border-radius: 12px;
  box-shadow: 0 8px 24px rgba(34, 78, 130, 0.08);
  background: rgba(255, 255, 255, 0.94);
}
.post-card-detail :deep(.el-card__body) { padding: 24px 28px; }

.post-header { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
.post-meta { display: flex; flex-direction: column; }
.post-author { font-weight: 600; font-size: 15px; }
.post-time { font-size: 12px; color: #999; }
.post-title { font-size: 24px; font-weight: 700; color: #111827; margin: 0 0 16px; line-height: 1.4; }
.post-content { color: #333; line-height: 1.8; font-size: 15px; margin-bottom: 16px; white-space: pre-wrap; word-break: break-word; }

.post-images { margin-bottom: 16px; }
.post-images-title { font-size: 15px; font-weight: 600; color: #374151; margin-bottom: 10px; }
.post-images-grid { display: flex; flex-wrap: wrap; gap: 12px; }
.post-detail-image { max-width: 100%; max-height: 400px; border-radius: 8px; border: 1px solid #e5e7eb; cursor: zoom-in; width: auto; }

.post-tags { margin-bottom: 16px; display: flex; flex-wrap: wrap; gap: 8px; }
.post-related-news { display: flex; align-items: center; gap: 6px; margin-bottom: 16px; padding: 10px 14px; background: #fef2f2; border-radius: 8px; font-size: 14px; color: #dc2626; cursor: pointer; }
.post-related-news:hover { background: #fee2e2; }
.post-stats { display: flex; gap: 28px; margin-bottom: 16px; color: #999; font-size: 14px; }
.post-actions-bar { display: flex; gap: 12px; padding-top: 16px; border-top: 1px solid #e5e7eb; }
.post-actions-bar .action-active { color: #dc2626; }
.post-actions-bar .action-favorited { color: #f59e0b; }

/* Summary */
.summary-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }
.summary-title { font-weight: 700; font-size: 16px; color: #1f2937; }
.summary-content p { color: #333; line-height: 1.7; margin: 0 0 12px; }
.summary-tags { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 8px; }
.summary-points { margin-top: 12px; padding-top: 12px; border-top: 1px solid #e0e0e0; }
.summary-points-title { font-size: 13px; font-weight: 600; color: #374151; margin-bottom: 8px; }
.summary-points ul { margin: 0; padding-left: 20px; }
.summary-points li { font-size: 13px; color: #6b7280; line-height: 1.8; }
.summary-hint { color: #9ca3af; font-size: 14px; text-align: center; padding: 16px 0; }

/* Comments */
.comments-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px; }
.comments-header h3 { margin: 0; font-size: 18px; font-weight: 700; color: #1f2937; }
.comments-hint { font-size: 12px; color: #9ca3af; }
.comment-composer { margin-bottom: 24px; padding-bottom: 24px; border-bottom: 1px solid #e5e7eb; }
.composer-actions { display: flex; align-items: center; justify-content: space-between; margin-top: 12px; }
.composer-tools { display: flex; align-items: center; gap: 4px; }
.image-name { font-size: 12px; color: #6b7280; margin-left: 4px; }
.loading-container { display: flex; justify-content: center; padding: 24px; }
.empty-state { padding: 24px; }
.comments-list { display: flex; flex-direction: column; gap: 16px; }
</style>
