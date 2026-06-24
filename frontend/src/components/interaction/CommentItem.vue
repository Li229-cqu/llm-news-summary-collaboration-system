<template>
  <div class="comment-item" :class="{ 'comment-item--folded': isFolded }">
    <div class="comment-item__header">
      <div class="comment-item__user">
        <el-avatar :size="34">{{ comment.nickname?.slice(0, 1) || 'U' }}</el-avatar>
        <div>
          <div class="comment-item__nickname">{{ comment.nickname }}</div>
          <div class="comment-item__time">{{ comment.create_time }}</div>
        </div>
      </div>
      <el-tag v-if="comment.is_liked" size="small" effect="plain" type="success">已点赞</el-tag>
    </div>

    <div class="comment-item__content">
      {{ isFolded ? '该评论已被折叠' : comment.content }}
    </div>

    <div class="comment-item__actions">
      <el-button text type="primary" :loading="loadingLike" @click="handleLike">
        点赞 {{ comment.like_count }}
      </el-button>
      <el-button text type="primary" @click="toggleReply">
        回复
      </el-button>
    </div>

    <div v-if="showReplyBox" class="comment-item__reply-box">
      <el-input
        v-model="replyContent"
        type="textarea"
        :rows="3"
        placeholder="写下你的回复"
        :disabled="loadingReply"
        resize="none"
      />
      <div class="comment-item__reply-actions">
        <el-button size="small" @click="closeReply">取消</el-button>
        <el-button size="small" type="primary" :loading="loadingReply" @click="handleReply">
          回复
        </el-button>
      </div>
    </div>

    <div v-if="visibleReplies.length" class="comment-item__replies">
      <CommentItem
        v-for="reply in visibleReplies"
        :key="reply.id"
        :comment="reply"
        :replying-id="replyingId"
        :loading-like="loadingLike"
        :loading-reply="loadingReply"
        :level="level + 1"
        @like="handleLike"
        @reply="handleReplyEvent"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'

export interface CommentItemData {
  id: number
  news_id: number
  user_id: number
  username: string
  nickname: string
  avatar: string
  parent_id: number | null
  content: string
  like_count: number
  status: number
  create_time: string
  is_liked: boolean
  replies: CommentItemData[]
}

const props = withDefaults(
  defineProps<{
    comment: CommentItemData
    replyingId?: number | null
    loadingLike?: boolean
    loadingReply?: boolean
    level?: number
  }>(),
  {
    replyingId: null,
    loadingLike: false,
    loadingReply: false,
    level: 0,
  },
)

const emit = defineEmits<{
  (event: 'like', comment: CommentItemData): void
  (event: 'reply', comment: CommentItemData, content: string): void
}>()

const replyContent = ref('')
const showReplyBox = computed(() => props.replyingId === props.comment.id)
const isFolded = computed(() => props.comment.status === 2)
const visibleReplies = computed(() => (props.level >= 1 ? [] : props.comment.replies ?? []))

function handleLike() {
  emit('like', props.comment)
}

function toggleReply() {
  if (showReplyBox.value) {
    replyContent.value = ''
    emit('reply', props.comment, '')
  } else {
    emit('reply', props.comment, '__toggle__')
  }
}

function closeReply() {
  replyContent.value = ''
  emit('reply', props.comment, '')
}

function handleReply() {
  const value = replyContent.value.trim()
  if (!value) {
    return
  }

  emit('reply', props.comment, value)
  replyContent.value = ''
}

function handleReplyEvent(comment: CommentItemData, content: string) {
  emit('reply', comment, content)
}
</script>

<style scoped>
.comment-item {
  display: grid;
  gap: 12px;
  padding: 16px;
  border: 1px solid var(--color-border);
  border-radius: 16px;
  background: var(--color-bg-card);
}

.comment-item--folded {
  opacity: 0.9;
}

.comment-item__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.comment-item__user {
  display: flex;
  gap: 10px;
  align-items: center;
}

.comment-item__nickname {
  color: var(--color-text-primary);
  font-size: 14px;
  font-weight: 600;
}

.comment-item__time {
  color: var(--color-text-secondary);
  font-size: 12px;
}

.comment-item__content {
  color: var(--color-text-primary);
  font-size: 14px;
  line-height: 1.8;
}

.comment-item__actions {
  display: flex;
  gap: 8px;
}

.comment-item__actions :deep(.el-button) {
  color: var(--color-text-secondary);
}

.comment-item__reply-box {
  display: grid;
  gap: 10px;
  padding: 12px;
  border-radius: 14px;
  background: var(--color-bg);
}

.comment-item__reply-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.comment-item__replies {
  display: grid;
  gap: 12px;
  padding-left: 18px;
  border-left: 1px solid var(--color-border);
}

@media (max-width: 640px) {
  .comment-item {
    padding: 14px;
  }

  .comment-item__header {
    flex-direction: column;
  }

  .comment-item__actions {
    flex-wrap: wrap;
  }
}
</style>
