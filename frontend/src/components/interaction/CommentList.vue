<template>
  <section class="comment-list">
    <div class="comment-list__header" v-if="total > 0 || comments.length > 0">
      <div class="comment-list__title">评论流</div>
      <div class="comment-list__header-right">
        <div class="comment-list__meta">{{ total || comments.length }} 条内容</div>
        <el-button
            v-if="comments.length > 0"
            type="primary"
            link
            size="small"
            :loading="summarizing"
            @click="handleSummarize"
            class="comment-list__summary-btn"
          >
            <el-icon><Aim /></el-icon>
            AI 总结评论
          </el-button>
      </div>
    </div>

    <div v-if="summaryResult" class="comment-summary-card">
      <div class="comment-summary-card__header">
        <el-icon><ChatDotRound /></el-icon>
        <span class="comment-summary-card__title">AI 评论总结</span>
        <el-tag :type="summaryResult.source === 'llm' ? 'success' : 'info'" size="small">
          {{ summaryResult.source === 'llm' ? 'AI 生成' : '关键词匹配' }}
        </el-tag>
        <el-button
          type="text"
          size="small"
          class="comment-summary-card__close"
          @click="summaryResult = null"
        >
          <el-icon><Close /></el-icon>
        </el-button>
      </div>
      <div class="comment-summary-card__content">
        <p>{{ summaryResult.summary }}</p>
      </div>
      <div class="comment-summary-card__tags">
        <el-tag :type="getSentimentType(summaryResult.sentiment)" size="small">
          {{ getSentimentText(summaryResult.sentiment) }}
        </el-tag>
        <el-tag v-for="kw in summaryResult.keywords.slice(0, 3)" :key="kw" type="info" size="small">
          {{ kw }}
        </el-tag>
      </div>
      <div v-if="summaryResult.key_points.length" class="comment-summary-card__points">
        <div class="comment-summary-card__points-title">主要观点</div>
        <ul>
          <li v-for="(point, index) in summaryResult.key_points" :key="index">{{ point }}</li>
        </ul>
      </div>
    </div>

    <el-skeleton v-if="loading" animated :rows="6" />
    <el-empty v-else-if="!comments.length" description="暂无评论，欢迎抢首评" />
    <div v-else class="comment-list__items">
      <CommentItem
        v-for="comment in comments"
        :key="comment.id"
        :comment="comment"
        :replying-id="replyingId"
        :loading-like-id="loadingLikeId"
        :loading-reply="loadingReply"
        :deleting-id="deletingId"
        :current-user-id="currentUserId"
        :current-user-role="currentUserRole"
        :show-reply="showReply"
        :show-replies="showReplies"
        @like="handleLike"
        @reply="handleReply"
        @delete="handleDelete"
        @reload-comments="handleReloadComments"
      />
    </div>
    <div v-if="total > 0" class="comment-list__total">共 {{ total }} 条评论</div>
  </section>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Aim, ChatDotRound, Close } from '@element-plus/icons-vue'
import CommentItem, { type CommentItemData, type CommentMediaJson } from './CommentItem.vue'
import { generateCommentsSummary, type CommentsSummaryResponse } from '@/api/community'

const props = withDefaults(
  defineProps<{
    comments: CommentItemData[]
    loading?: boolean
    total?: number
    replyingId?: number | null
    loadingLikeId?: number | null
    loadingReply?: boolean
    deletingId?: number | null
    currentUserId?: number | null
    currentUserRole?: string
    showReply?: boolean
    showReplies?: boolean
  }>(),
  {
    loading: false,
    total: 0,
    replyingId: null,
    loadingLikeId: null,
    loadingReply: false,
    deletingId: null,
    currentUserId: null,
    currentUserRole: '',
    showReply: true,
    showReplies: true,
  },
)

const emit = defineEmits<{
  (event: 'like', comment: CommentItemData): void
  (event: 'reply', comment: CommentItemData, content: string, mediaJson?: CommentMediaJson | null): void
  (event: 'delete', comment: CommentItemData): void
  (event: 'reload-comments'): void
}>()

const summarizing = ref(false)
const summaryResult = ref<CommentsSummaryResponse | null>(null)

function collectAllComments(comments: CommentItemData[]): string[] {
  const result: string[] = []
  function traverse(items: CommentItemData[]) {
    for (const item of items) {
      if (item.content && item.content.trim()) {
        result.push(item.content.trim())
      }
      if (item.replies && item.replies.length > 0) {
        traverse(item.replies)
      }
    }
  }
  traverse(comments)
  return result
}

async function handleSummarize() {
  if (summarizing.value) return

  const allComments = collectAllComments(props.comments)
  if (allComments.length === 0) {
    ElMessage.info('暂无评论内容可总结')
    return
  }

  summarizing.value = true
  summaryResult.value = null

  try {
    const result = await generateCommentsSummary(allComments)
    summaryResult.value = result
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '总结失败，请稍后重试')
  } finally {
    summarizing.value = false
  }
}

function getSentimentType(sentiment: string) {
  switch (sentiment) {
    case 'positive': return 'success'
    case 'negative': return 'danger'
    default: return 'warning'
  }
}

function getSentimentText(sentiment: string) {
  switch (sentiment) {
    case 'positive': return '正面'
    case 'negative': return '负面'
    default: return '中立'
  }
}

function handleLike(comment: CommentItemData) {
  emit('like', comment)
}

function handleReply(comment: CommentItemData, content: string, mediaJson?: CommentMediaJson | null) {
  emit('reply', comment, content, mediaJson)
}

function handleDelete(comment: CommentItemData) {
  emit('delete', comment)
}

function handleReloadComments() {
  emit('reload-comments')
}
</script>

<style scoped>
.comment-list {
  display: grid;
  gap: 16px;
}

.comment-list :deep(.el-empty) {
  padding: 22px 0;
}

.comment-list__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 2px 2px 0;
}

.comment-list__header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.comment-list__title {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.comment-list__meta {
  color: var(--color-text-secondary);
  font-size: 12px;
}

.comment-list__summary-btn {
  display: flex;
  align-items: center;
  gap: 4px;
}

.comment-summary-card {
  background: linear-gradient(135deg, var(--color-bg) 0%, var(--color-border-light) 100%);
  border-radius: 10px;
  padding: 16px;
  margin-bottom: 8px;
}

.comment-summary-card__header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.comment-summary-card__title {
  font-weight: 600;
  font-size: 14px;
  color: var(--color-text-primary);
}

.comment-summary-card__close {
  margin-left: auto;
  padding: 0;
}

.comment-summary-card__content p {
  color: var(--color-text-primary);
  line-height: 1.6;
  margin: 0;
}

.comment-summary-card__tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
}

.comment-summary-card__points {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #e0e0e0;
}

.comment-summary-card__points-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: 8px;
}

.comment-summary-card__points ul {
  margin: 0;
  padding-left: 20px;
}

.comment-summary-card__points li {
  font-size: 13px;
  color: var(--color-text-secondary);
  line-height: 1.8;
}

.comment-list__items {
  display: grid;
  gap: 12px;
}

.comment-list__total {
  color: var(--color-text-secondary);
  font-size: 13px;
}

/* 消除 Element Plus 按钮蓝色 hover */
.comment-list :deep(.el-button--primary:hover) {
  color: #b91c1c;
}

.comment-list :deep(.el-button--primary.is-link:hover) {
  color: #b91c1c;
}
</style>
