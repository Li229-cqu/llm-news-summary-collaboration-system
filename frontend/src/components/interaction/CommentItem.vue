<template>
  <div class="comment-item" :class="{ 'comment-item--folded': isFolded, 'comment-item--child': level > 0 }">
    <div class="comment-item__avatar-col">
      <el-avatar :size="40" class="comment-item__avatar">{{ avatarText }}</el-avatar>
      <div v-if="level > 0" class="comment-item__branch-line"></div>
    </div>

    <div class="comment-item__body">
      <div class="comment-item__header">
        <div class="comment-item__user">
          <div class="comment-item__nickname-row">
            <span class="comment-item__nickname">{{ displayNickname }}</span>
            <el-tag v-if="comment.is_liked" size="small" effect="plain" type="success">已点赞</el-tag>
            <el-tag v-if="isFolded" size="small" effect="plain" type="warning">已折叠</el-tag>
            <el-tag v-if="isDeleted" size="small" effect="plain" type="info">已删除</el-tag>
          </div>
          <div class="comment-item__time">{{ comment.create_time }}</div>
        </div>
      </div>

      <div class="comment-item__content">
        {{ displayContent }}
      </div>

      <div v-if="mediaImages.length || mediaEmojis.length || mediaFiles.length" class="comment-item__media">
        <div v-if="mediaImages.length" class="comment-item__media-section">
          <span class="comment-item__media-label">图片</span>
          <div class="comment-item__image-grid">
            <a
              v-for="(image, index) in mediaImages"
              :key="`${comment.id}-image-${index}`"
              class="comment-item__image-link"
              :href="image"
              target="_blank"
              rel="noreferrer"
            >
              <img :src="image" alt="评论图片" />
            </a>
          </div>
        </div>

        <div v-if="mediaEmojis.length" class="comment-item__media-section">
          <span class="comment-item__media-label">表情</span>
          <div class="comment-item__emoji-list">
            <el-tag v-for="(emoji, index) in mediaEmojis" :key="`${comment.id}-emoji-${index}`" size="small" effect="plain">
              {{ emoji }}
            </el-tag>
          </div>
        </div>

        <div v-if="mediaFiles.length" class="comment-item__media-section">
          <span class="comment-item__media-label">附件</span>
          <div class="comment-item__file-list">
            <el-tag
              v-for="(file, index) in mediaFiles"
              :key="`${comment.id}-file-${index}`"
              size="small"
              type="info"
              effect="plain"
            >
              {{ file.name || file.url || '文件' }}
            </el-tag>
          </div>
        </div>
      </div>

      <div v-if="!isDeleted" class="comment-item__actions">
        <el-button text type="primary" :loading="loadingLike" @click="handleLike">
          点赞 {{ comment.like_count }}
        </el-button>
        <span class="comment-item__action-divider">·</span>
        <el-button text type="primary" @click="toggleReply">
          回复
        </el-button>
        <span v-if="canDelete" class="comment-item__action-divider">·</span>
        <el-popconfirm
          v-if="canDelete"
          title="确定删除这条评论吗？"
          confirm-button-text="删除"
          cancel-button-text="取消"
          @confirm="handleDelete"
        >
          <template #reference>
            <el-button text type="danger" :loading="loadingDelete">
              删除
            </el-button>
          </template>
        </el-popconfirm>
      </div>

      <div v-if="showReplyBox && !isDeleted" class="comment-item__reply-box">
        <CommentBox
          placeholder="写下你的回复"
          button-text="回复"
          :loading="loadingReply"
          @submit="handleReplySubmit"
        />
        <div class="comment-item__reply-actions">
          <el-button size="small" @click="closeReply">取消</el-button>
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
          :deleting-id="deletingId"
          :current-user-id="currentUserId"
          :current-user-role="currentUserRole"
          :level="level + 1"
          @like="handleLike"
          @reply="handleReplyEvent"
          @delete="handleDeleteEvent"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import CommentBox from './CommentBox.vue'

export interface CommentMediaJson {
  images?: string[]
  emojis?: string[]
  files?: Array<{
    name?: string
    url?: string
    type?: string
  }>
}

export interface CommentItemData {
  id: number
  post_id?: number
  news_id?: number
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
  media_json?: CommentMediaJson | string | null
}

const props = withDefaults(
  defineProps<{
    comment: CommentItemData
    replyingId?: number | null
    loadingLike?: boolean
    loadingReply?: boolean
    deletingId?: number | null
    currentUserId?: number | null
    currentUserRole?: string
    level?: number
  }>(),
  {
    replyingId: null,
    loadingLike: false,
    loadingReply: false,
    deletingId: null,
    currentUserId: null,
    currentUserRole: '',
    level: 0,
  },
)

const emit = defineEmits<{
  (event: 'like', comment: CommentItemData): void
  (event: 'reply', comment: CommentItemData, content: string, mediaJson?: CommentMediaJson | null): void
  (event: 'delete', comment: CommentItemData): void
}>()

const showReplyBox = computed(() => props.replyingId === props.comment.id)
const isFolded = computed(() => props.comment.status === 2)
const isDeleted = computed(() => props.comment.status === 4)
const isOwner = computed(() => props.currentUserId != null && props.currentUserId === props.comment.user_id)
const canDelete = computed(() => {
  if (isDeleted.value) {
    return false
  }
  const role = (props.currentUserRole || '').toLowerCase()
  return isOwner.value || role === 'admin' || role === 'editor'
})
const loadingDelete = computed(() => props.deletingId === props.comment.id)
const visibleReplies = computed(() => (props.level >= 1 ? [] : props.comment.replies ?? []))

const normalizedMedia = computed<CommentMediaJson>(() => {
  const raw = props.comment.media_json
  if (!raw) {
    return {}
  }
  if (typeof raw === 'string') {
    try {
      return JSON.parse(raw) as CommentMediaJson
    } catch {
      return {}
    }
  }
  return raw
})

const mediaImages = computed(() => normalizedMedia.value.images ?? [])
const mediaEmojis = computed(() => normalizedMedia.value.emojis ?? [])
const mediaFiles = computed(() => normalizedMedia.value.files ?? [])
const avatarText = computed(() => props.comment.nickname?.slice(0, 1) || 'U')
const displayNickname = computed(() => props.comment.nickname || props.comment.username || '用户')
const displayContent = computed(() => {
  if (isDeleted.value) {
    return '该评论已删除'
  }
  if (isFolded.value) {
    return '该评论已被折叠'
  }
  const text = (props.comment.content || '').trim()
  if (text) {
    return text
  }
  if (mediaImages.value.length || mediaEmojis.value.length || mediaFiles.value.length) {
    return '该评论仅包含富媒体内容'
  }
  return ''
})

function handleLike() {
  emit('like', props.comment)
}

function handleDelete() {
  emit('delete', props.comment)
}

function toggleReply() {
  if (showReplyBox.value) {
    emit('reply', props.comment, '')
  } else {
    emit('reply', props.comment, '__toggle__')
  }
}

function closeReply() {
  emit('reply', props.comment, '')
}

function handleReplySubmit(content: string, mediaJson: CommentMediaJson | null) {
  const value = content.trim()
  if (!value && !mediaJson) {
    return
  }
  emit('reply', props.comment, value || ' ', mediaJson)
}

function handleReplyEvent(comment: CommentItemData, content: string, mediaJson?: CommentMediaJson | null) {
  emit('reply', comment, content, mediaJson)
}

function handleDeleteEvent(comment: CommentItemData) {
  emit('delete', comment)
}
</script>

<style scoped>
.comment-item {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  gap: 12px;
  padding: 16px;
  border: 1px solid color-mix(in srgb, var(--color-border) 90%, transparent);
  border-radius: 18px;
  background: var(--color-bg-card);
  box-shadow: 0 1px 0 rgb(15 23 42 / 3%);
}

.comment-item--child {
  padding: 14px 14px 14px 0;
  border-color: color-mix(in srgb, var(--color-primary) 14%, var(--color-border));
  background: color-mix(in srgb, var(--color-primary) 3%, var(--color-bg-card));
}

.comment-item--folded {
  opacity: 0.9;
}

.comment-item__avatar-col {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.comment-item__avatar {
  flex-shrink: 0;
  box-shadow: 0 2px 8px rgb(15 23 42 / 8%);
}

.comment-item__branch-line {
  width: 2px;
  flex: 1;
  min-height: 28px;
  border-radius: 999px;
  background: linear-gradient(
    180deg,
    color-mix(in srgb, var(--color-primary) 36%, transparent),
    color-mix(in srgb, var(--color-primary) 8%, transparent)
  );
}

.comment-item__body {
  min-width: 0;
  display: grid;
  gap: 12px;
}

.comment-item__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.comment-item__user {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.comment-item__nickname-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.comment-item__nickname-row :deep(.el-tag) {
  border-radius: 999px;
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
  font-size: 15px;
  line-height: 1.9;
  white-space: pre-wrap;
  word-break: break-word;
}

.comment-item__media {
  display: grid;
  gap: 10px;
  padding: 12px 0 0;
}

.comment-item__media-section {
  display: grid;
  gap: 8px;
}

.comment-item__media-label {
  font-size: 12px;
  color: var(--color-text-secondary);
}

.comment-item__image-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.comment-item__image-link img {
  width: 96px;
  height: 96px;
  object-fit: cover;
  border-radius: 12px;
  border: 1px solid var(--color-border);
}

.comment-item__emoji-list,
.comment-item__file-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.comment-item__actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  align-items: center;
  color: var(--color-text-secondary);
}

.comment-item__actions :deep(.el-button) {
  color: var(--color-text-secondary);
}

.comment-item__action-divider {
  color: var(--color-text-secondary);
  opacity: 0.5;
}

.comment-item__reply-box {
  display: grid;
  gap: 10px;
  padding: 12px;
  border-radius: 16px;
  background: color-mix(in srgb, var(--color-primary) 4%, var(--color-bg-card));
  border: 1px solid color-mix(in srgb, var(--color-primary) 10%, var(--color-border));
}

.comment-item__reply-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.comment-item__replies {
  display: grid;
  gap: 12px;
  padding: 14px 0 0 16px;
  margin-left: 18px;
  border-left: 2px solid color-mix(in srgb, var(--color-primary) 12%, var(--color-border));
  position: relative;
}

.comment-item__replies::before {
  content: '';
  position: absolute;
  left: -2px;
  top: 0;
  width: 2px;
  height: 10px;
  background: color-mix(in srgb, var(--color-primary) 12%, var(--color-border));
}

@media (max-width: 640px) {
  .comment-item {
    grid-template-columns: 34px minmax(0, 1fr);
    padding: 14px;
    gap: 10px;
  }

  .comment-item--child {
    padding-right: 10px;
  }

  .comment-item__avatar-col {
    align-items: flex-start;
  }

  .comment-item__branch-line {
    margin-left: 16px;
  }

  .comment-item__actions {
    flex-wrap: wrap;
  }

  .comment-item__image-link img {
    width: 84px;
    height: 84px;
  }

  .comment-item__replies {
    margin-left: 10px;
    padding-left: 12px;
  }
}
</style>
