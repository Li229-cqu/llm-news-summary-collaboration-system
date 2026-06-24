<template>
  <section class="comment-list">
    <el-skeleton v-if="loading" animated :rows="6" />
    <el-empty v-else-if="!comments.length" description="暂无评论" />
    <div v-else class="comment-list__items">
      <CommentItem
        v-for="comment in comments"
        :key="comment.id"
        :comment="comment"
        :replying-id="replyingId"
        :loading-like="loadingLike"
        :loading-reply="loadingReply"
        @like="handleLike"
        @reply="handleReply"
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
  }>(),
  {
    loading: false,
    total: 0,
    replyingId: null,
    loadingLike: false,
    loadingReply: false,
  },
)

const emit = defineEmits<{
  (event: 'like', comment: CommentItemData): void
  (event: 'reply', comment: CommentItemData, content: string): void
}>()

function handleLike(comment: CommentItemData) {
  emit('like', comment)
}

function handleReply(comment: CommentItemData, content: string) {
  emit('reply', comment, content)
}
</script>

<style scoped>
.comment-list {
  display: grid;
  gap: 16px;
}

.comment-list :deep(.el-empty) {
  padding: 20px 0;
}

.comment-list__items {
  display: grid;
  gap: 14px;
}

.comment-list__total {
  color: var(--color-text-secondary);
  font-size: 13px;
}
</style>
