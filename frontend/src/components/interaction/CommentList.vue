<template>
  <section class="comment-list">
    <div class="comment-list__header" v-if="total > 0 || comments.length > 0">
      <div class="comment-list__title">评论流</div>
      <div class="comment-list__meta">{{ total || comments.length }} 条内容</div>
    </div>

    <el-skeleton v-if="loading" animated :rows="6" />
    <el-empty v-else-if="!comments.length" description="暂无评论，欢迎抢首评" />
    <div v-else class="comment-list__items">
      <CommentItem
        v-for="comment in comments"
        :key="comment.id"
        :comment="comment"
        :replying-id="replyingId"
        :loading-like="loadingLike"
        :loading-reply="loadingReply"
        :deleting-id="deletingId"
        :current-user-id="currentUserId"
        :current-user-role="currentUserRole"
        @like="handleLike"
        @reply="handleReply"
        @delete="handleDelete"
      />
    </div>
    <div v-if="total > 0" class="comment-list__total">共 {{ total }} 条评论</div>
  </section>
</template>

<script setup lang="ts">
import CommentItem, { type CommentItemData } from './CommentItem.vue'

const props = withDefaults(
  defineProps<{
    comments: CommentItemData[]
    loading?: boolean
    total?: number
    replyingId?: number | null
    loadingLike?: boolean
    loadingReply?: boolean
    deletingId?: number | null
    currentUserId?: number | null
    currentUserRole?: string
  }>(),
  {
    loading: false,
    total: 0,
    replyingId: null,
    loadingLike: false,
    loadingReply: false,
    deletingId: null,
    currentUserId: null,
    currentUserRole: '',
  },
)

const emit = defineEmits<{
  (event: 'like', comment: CommentItemData): void
  (event: 'reply', comment: CommentItemData, content: string): void
  (event: 'delete', comment: CommentItemData): void
}>()

function handleLike(comment: CommentItemData) {
  emit('like', comment)
}

function handleReply(comment: CommentItemData, content: string) {
  emit('reply', comment, content)
}

function handleDelete(comment: CommentItemData) {
  emit('delete', comment)
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

.comment-list__title {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.comment-list__meta {
  color: var(--color-text-secondary);
  font-size: 12px;
}

.comment-list__items {
  display: grid;
  gap: 12px;
}

.comment-list__total {
  color: var(--color-text-secondary);
  font-size: 13px;
}
</style>
