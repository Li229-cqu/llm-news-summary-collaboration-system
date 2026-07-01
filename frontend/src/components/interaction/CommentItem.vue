<template>
  <div :id="`comment-${comment.id}`" class="comment-item" :class="{ 'comment-item--folded': isFolded, 'comment-item--child': level > 0 }">
    <div class="comment-item__avatar-col">
      <el-avatar :size="40" class="comment-item__avatar" :src="normalizedAvatar">{{ avatarText }}</el-avatar>
      <div v-if="level > 0" class="comment-item__branch-line"></div>
    </div>

    <div class="comment-item__body">
      <div class="comment-item__header">
        <div class="comment-item__user">
          <div class="comment-item__nickname-row">
            <span class="comment-item__nickname">{{ displayNickname }}</span>
            <el-tag v-if="localIsLiked" size="small" effect="plain" type="success">已点赞</el-tag>
            <el-tag v-if="isFolded" size="small" effect="plain" type="warning">已折叠</el-tag>
            <el-tag v-if="isDeleted" size="small" effect="plain" type="info">已删除</el-tag>
          </div>
          <div class="comment-item__time">{{ comment.create_time }}</div>
        </div>
      </div>

      <div v-if="replyQuote" class="comment-item__quote">
        <span class="comment-item__quote-arrow">→</span>
        <span class="comment-item__quote-user">@{{ replyQuote.nickname }}</span>
        <span class="comment-item__quote-content">"{{ replyQuote.content }}"</span>
      </div>

      <div class="comment-item__content">
        {{ displayContent }}
      </div>

      <div v-if="mediaImages.length || isolatedEmojis.length" class="comment-item__media">
        <div v-if="mediaImages.length" class="comment-item__image-grid">
          <el-image
            v-for="(image, index) in mediaImages"
            :key="`${comment.id}-image-${index}`"
            :src="normalizeCommentImageUrl(image)"
            :preview-src-list="mediaImages.map(normalizeCommentImageUrl)"
            fit="cover"
            class="comment-image-thumb"
            preview-teleported
          >
            <template #error>
              <div class="comment-image-error">加载失败</div>
            </template>
          </el-image>
        </div>

        <div v-if="isolatedEmojis.length" class="comment-emoji-inline">
          <span v-for="(emoji, index) in isolatedEmojis" :key="index">{{ emoji }}</span>
        </div>
      </div>

      <div v-if="!isDeleted" class="comment-item__actions">
        <el-button text type="primary" :loading="loadingLike" @click="handleLike">
          点赞 {{ localLikeCount }}
        </el-button>

        <el-button v-if="showReply" text type="primary" @click="toggleReply">
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

      <div v-if="showReply && showReplyBox && !isDeleted" class="comment-item__reply-box">
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

      <div v-if="showReplies && allReplies.length" class="comment-item__replies">
        <CommentItem
            v-for="reply in visibleReplies"
            :key="reply.id"
            :comment="reply"
            :replying-id="replyingId"
            :loading-like="loadingLikeIds.has(reply.id)"
            :loading-reply="loadingReply"
            :deleting-id="deletingId"
            :current-user-id="currentUserId"
            :current-user-role="currentUserRole"
            :level="level + 1"
            :root-comment-id="level === 0 ? props.comment.id : props.rootCommentId"
            :show-reply="showReply"
            :show-replies="showReplies"
            @like="handleChildLike"
            @reply="handleReplyEvent"
            @delete="handleDeleteEvent"
            @reload-comments="handleReloadComments"
          />

        <div class="comment-item__expand-btn">
          <el-button
            v-if="showExpandButton"
            text
            type="primary"
            @click="expandReplies"
          >
            展开更多评论
          </el-button>
          <el-button
            v-if="showCollapseButton"
            text
            type="primary"
            @click="collapseReplies"
          >
            收起以上评论
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import CommentBox from './CommentBox.vue'
import { isReplyForceVisible } from '@/utils/commentVisibility'

export interface LikeResult {
  comment_id: number
  liked: boolean
  like_count: number
}

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
  reply_to_user_id?: number | null
  reply_to_username?: string
  reply_to_nickname?: string
  reply_to_content?: string
}

const props = withDefaults(
  defineProps<{
    comment: CommentItemData
    replyingId?: number | null
    loadingLikeId?: number | null
    loadingReply?: boolean
    deletingId?: number | null
    currentUserId?: number | null
    currentUserRole?: string
    level?: number
    rootCommentId?: number | null
    showReply?: boolean
    showReplies?: boolean
  }>(),
  {
    replyingId: null,
    loadingLikeId: null,
    loadingReply: false,
    deletingId: null,
    currentUserId: null,
    currentUserRole: '',
    level: 0,
    rootCommentId: null,
    showReply: true,
    showReplies: true,
  },
)

const emit = defineEmits<{
  (event: 'like', comment: CommentItemData): void
  (event: 'like-done', result: LikeResult): void
  (event: 'reply', comment: CommentItemData, content: string, mediaJson?: CommentMediaJson | null): void
  (event: 'delete', comment: CommentItemData): void
  (event: 'reload-comments'): void
}>()

const expandedCount = ref(0)
const loadingLikeIds = new Set<number>()

interface ExpandState {
  expandedCount: number
}

const expandStateMap = new Map<number, ExpandState>()

watch(
  () => props.comment.id,
  (newId) => {
    const stored = expandStateMap.get(newId)
    expandedCount.value = stored?.expandedCount ?? 0
  },
  { immediate: true }
)

const localLikeCount = ref(props.comment.like_count)
const localIsLiked = ref(props.comment.is_liked)

watch(
  () => props.comment.like_count,
  (newVal) => {
    localLikeCount.value = newVal
  }
)

watch(
  () => props.comment.is_liked,
  (newVal) => {
    localIsLiked.value = newVal
  }
)

function getExpandedCount(): number {
  return expandedCount.value
}

function setExpandedCount(value: number): void {
  expandedCount.value = value
  expandStateMap.set(props.comment.id, { expandedCount: value })
}

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
const loadingLike = computed(() => props.loadingLikeId === props.comment.id)

const allReplies = computed(() => {
  if (props.level >= 1) {
    return []
  }
  const replies = props.comment.replies ?? []
  const flatReplies: CommentItemData[] = []
  const visited = new Set<number>()

  function collect(comment: CommentItemData) {
    if (visited.has(comment.id)) return
    visited.add(comment.id)
    flatReplies.push(comment)
    for (const child of comment.replies ?? []) {
      collect(child)
    }
  }

  for (const reply of replies) {
    collect(reply)
  }

  return flatReplies
})

const maxLikedReply = computed(() => {
  if (allReplies.value.length === 0) return null
  return allReplies.value.reduce((max, current) => {
    if (current.like_count > max.like_count) return current
    if (current.like_count === max.like_count) {
      return current.create_time < max.create_time ? current : max
    }
    return max
  })
})

const displayLimit = computed(() => {
  if (allReplies.value.length < 3) {
    return allReplies.value.length
  }
  const expanded = getExpandedCount()
  if (expanded === 0) {
    return 1
  }
  return 1 + expanded * 3
})

const visibleReplies = computed(() => {
  // 先按原有逻辑计算基础可见列表
  let baseVisible: CommentItemData[] = []
  if (allReplies.value.length === 0) {
    baseVisible = []
  } else if (allReplies.value.length < 3) {
    baseVisible = allReplies.value
  } else {
    const expanded = getExpandedCount()
    if (expanded === 0) {
      baseVisible = maxLikedReply.value ? [maxLikedReply.value] : []
    } else {
      const sortedReplies = [...allReplies.value].sort((a, b) => {
        if (b.like_count !== a.like_count) {
          return b.like_count - a.like_count
        }
        return a.create_time.localeCompare(b.create_time)
      })
      baseVisible = sortedReplies.slice(0, displayLimit.value)
    }
  }

  // 追加强制可见回复（当前会话刚发布的），不参与排序，追加到最后
  const extraReplies = allReplies.value.filter(reply =>
    isReplyForceVisible(reply.id) && !baseVisible.some(item => item.id === reply.id)
  )

  return [...baseVisible, ...extraReplies]
})

const showExpandButton = computed(() => {
  return allReplies.value.length >= 3 && visibleReplies.value.length < allReplies.value.length
})

const showCollapseButton = computed(() => {
  return getExpandedCount() > 0
})

function expandReplies() {
  setExpandedCount(getExpandedCount() + 1)
}

function collapseReplies() {
  setExpandedCount(0)
}

const replyQuote = computed(() => {
  const nickname = props.comment.reply_to_nickname
  const content = props.comment.reply_to_content
  if (!nickname || !content) {
    return null
  }
  const rootId = props.rootCommentId ?? props.comment.id
  const isDirectReplyToRoot = props.comment.parent_id === rootId
  if (isDirectReplyToRoot) {
    return null
  }
  return {
    nickname,
    content: content.length > 50 ? content.slice(0, 50) + '...' : content
  }
})

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

const mediaImages = computed(() => {
  const images = normalizedMedia.value.images ?? []
  return images.map(image => {
    if (image.startsWith('http://') || image.startsWith('https://')) {
      return image
    }
    if (image.startsWith('/')) {
      return image
    }
    return `/${image}`
  })
})
const mediaEmojis = computed(() => normalizedMedia.value.emojis ?? [])
const avatarText = computed(() => props.comment.nickname?.slice(0, 1) || 'U')
const displayNickname = computed(() => props.comment.nickname || props.comment.username || '用户')

const normalizedAvatar = computed(() => normalizeCommentImageUrl(props.comment.avatar))

/** true when content is empty but media_json.emojis exists — show emojis inline */
const isolatedEmojis = computed(() => {
  const hasContent = (props.comment.content || '').trim().length > 0
  return !hasContent && mediaEmojis.value.length > 0 ? mediaEmojis.value : []
})

function normalizeCommentImageUrl(url: string): string {
  if (!url) return ''
  if (url.startsWith('http://') || url.startsWith('https://')) return url
  const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
  return `${baseURL.replace(/\/+$/, '')}/${url.replace(/^\/+/, '')}`
}
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
  return ''
})

function handleLike() {
  const delta = localIsLiked.value ? -1 : 1
  localLikeCount.value = Math.max(0, localLikeCount.value + delta)
  localIsLiked.value = !localIsLiked.value
  emit('like', props.comment)
  emit('like-done', {
    comment_id: props.comment.id,
    liked: localIsLiked.value,
    like_count: localLikeCount.value,
  })
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

function handleChildLike(childComment: CommentItemData) {
  emit('like', childComment)
}

function handleReloadComments() {
  emit('reload-comments')
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
  gap: 8px;
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

.comment-item__quote {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 4px;
  padding: 6px 10px;
  background: color-mix(in srgb, var(--color-primary) 6%, var(--color-bg-card));
  border-radius: 8px;
  font-size: 13px;
  color: var(--color-text-secondary);
}

.comment-item__quote-arrow {
  color: var(--color-primary);
  font-weight: 500;
}

.comment-item__quote-user {
  color: var(--color-primary);
  font-weight: 500;
}

.comment-item__quote-content {
  color: var(--color-text-secondary);
}

.comment-item__content {
  color: var(--color-text-primary);
  font-size: 15px;
  line-height: 1.9;
  white-space: pre-wrap;
  word-break: break-word;
}

.comment-item__media {
  padding: 8px 0 0;
}

.comment-item__image-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.comment-image-thumb {
  width: 96px;
  height: 96px;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid var(--el-border-color-lighter);
  background: var(--el-fill-color-lighter);
  cursor: pointer;
}

.comment-image-error {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  color: var(--el-text-color-placeholder);
}

.comment-emoji-inline {
  display: flex;
  gap: 6px;
  font-size: 18px;
  line-height: 1.6;
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

/* 消除 Element Plus text 按钮的蓝色 hover */
.comment-item__actions :deep(.el-button:hover) {
  color: var(--color-primary);
}

.comment-item__actions :deep(.el-button--primary:hover) {
  color: var(--color-primary);
}

.comment-item__actions :deep(.el-button--danger) {
  color: var(--el-color-danger);
}

/* 回复框内取消按钮 hover */
.comment-item__reply-actions :deep(.el-button:hover) {
  color: var(--color-primary);
  border-color: var(--color-primary);
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
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
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

.comment-item__expand-btn {
  display: flex;
  gap: 16px;
  padding: 8px 0;
  text-align: left;
}

.comment-item__expand-btn :deep(.el-button) {
  color: var(--color-primary);
  font-size: 13px;
}

.comment-item__expand-btn :deep(.el-button:hover) {
  color: #b91c1c;
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

  .comment-image-thumb {
    width: 80px;
    height: 80px;
  }

  .comment-item__replies {
    margin-left: 10px;
    padding-left: 12px;
  }
}
</style>