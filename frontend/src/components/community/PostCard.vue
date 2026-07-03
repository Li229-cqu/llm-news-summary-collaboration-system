<template>
  <el-card
    class="post-card"
    hover
    @click="$emit('view', post)"
  >
    <div class="post-header">
      <el-avatar
        :src="normalizeAvatarUrl(post.avatar)"
        :text="post.author.slice(0, 1)"
      />
      <div class="post-meta">
        <span class="post-author">{{ post.author }}</span>
        <span class="post-time">{{ formatTime(post.created_at) }}</span>
      </div>
    </div>
    <h3 class="post-title">{{ post.title }}</h3>
    <p class="post-content">{{ truncateContent(post.content, 100) }}</p>
    <div v-if="postImages.length" class="post-images" @click.stop>
      <div
        v-for="(img, idx) in displayImages"
        :key="idx"
        class="post-image-item"
        :class="{ 'post-image-item--single': postImages.length === 1 }"
      >
        <el-image
          :src="resolveImageUrl(img)"
          fit="cover"
          class="post-image-thumb"
          :preview-src-list="previewImageUrls"
          preview-teleported
        />
        <div v-if="isLastWithOverlay(idx)" class="post-image-overlay">
          <span>+{{ postImages.length - MAX_VISIBLE }}</span>
        </div>
      </div>
    </div>
    <div v-if="post.tags && post.tags.length" class="post-tags">
      <el-tag
        v-for="tag in post.tags"
        :key="tag"
        size="small"
        type="info"
      >
        {{ tag }}
      </el-tag>
    </div>
    <div
      v-if="post.related_news_title"
      class="post-related-news"
      @click.stop="handleOpenRelatedNews"
    >
      <el-icon><Link /></el-icon>
      <span>关联新闻：{{ post.related_news_title }}</span>
    </div>
    <div class="post-actions">
      <el-button
        text
        size="small"
        class="post-action-btn"
        @click.stop="$emit('view', post)"
      >
        <el-icon><View /></el-icon>
        <span>查看</span>
        <span class="action-count">{{ post.views }}</span>
      </el-button>

      <el-button
        text
        size="small"
        class="post-action-btn"
        :class="{ 'action-active': post.liked }"
        @click.stop="emit('like', post)"
      >
        <el-icon><Pointer /></el-icon>
        <span>{{ post.liked ? '已点赞' : '点赞' }}</span>
        <span class="action-count">{{ post.likes }}</span>
      </el-button>

      <el-button
        text
        size="small"
        class="post-action-btn"
        :class="{ 'action-favorited': post.is_favorited }"
        @click.stop="emit('favorite', post, $event)"
      >
        <el-icon>
          <StarFilled v-if="post.is_favorited" />
          <Star v-else />
        </el-icon>
        <span>{{ post.is_favorited ? '已收藏' : '收藏' }}</span>
        <span class="action-count">{{ post.favorite_count ?? 0 }}</span>
      </el-button>

      <el-button
        text
        size="small"
        class="post-action-btn"
        @click.stop="$emit('comment', post)"
      >
        <el-icon><ChatDotRound /></el-icon>
        <span>评论</span>
        <span class="action-count">{{ post.comments }}</span>
      </el-button>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import {
  View,
  Pointer,
  Star,
  StarFilled,
  ChatDotRound,
  Link,
} from '@element-plus/icons-vue'
import type { CommunityPost } from '@/api/community'
import { resolveImageUrl } from '@/utils/media'

const MAX_VISIBLE = 3

const props = defineProps<{
  post: CommunityPost
}>()

const emit = defineEmits<{
  (e: 'view', post: CommunityPost): void
  (e: 'like', post: CommunityPost): void
  (e: 'favorite', post: CommunityPost, event: Event): void
  (e: 'comment', post: CommunityPost): void
  (e: 'openRelatedNews', post: CommunityPost): void
}>()

const displayImages = computed(() => {
  if (!postImages.value.length) return []
  return postImages.value.slice(0, MAX_VISIBLE)
})

const postImages = computed(() => {
  return Array.isArray(props.post.images) ? props.post.images.filter(Boolean) : []
})

const previewImageUrls = computed(() =>
  postImages.value.map((url) => resolveImageUrl(url))
)

function isLastWithOverlay(idx: number): boolean {
  if (!postImages.value.length) return false
  return idx === MAX_VISIBLE - 1 && postImages.value.length > MAX_VISIBLE
}

function handleOpenRelatedNews() {
  emit('openRelatedNews', props.post)
}

function normalizeAvatarUrl(url?: string): string {
  if (!url) return ''
  if (url.startsWith('http://') || url.startsWith('https://') || url.startsWith('data:image/')) return url
  const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'
  return `${baseURL.replace(/\/$/, '')}/${url.replace(/^\//, '')}`
}

function formatTime(timeStr: string) {
  const date = new Date(timeStr)
  return date.toLocaleString('zh-CN', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function truncateContent(content: string, maxLength: number) {
  if (content.length <= maxLength) return content
  return content.slice(0, maxLength) + '...'
}
</script>

<style scoped>
.post-card {
  cursor: pointer;
  transition: all 0.3s;
  border: 1px solid #e3edf9;
  border-radius: 12px;
  box-shadow: 0 6px 18px rgba(34, 78, 130, 0.06);
}
.post-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}
.post-card :deep(.el-card__body) {
  padding: 22px 24px;
}

.post-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.post-meta {
  display: flex;
  flex-direction: column;
}

.post-author {
  font-weight: 500;
}

.post-time {
  font-size: 12px;
  color: #999;
}

.post-title {
  color: #111827;
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 8px;
  line-height: 1.45;
}

.post-content {
  color: #53657c;
  font-size: 14px;
  margin-bottom: 12px;
  line-height: 1.6;
}

/* 图片缩略图 */
.post-images {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}
.post-image-item {
  position: relative;
  width: 100px;
  height: 80px;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid var(--color-border);
  flex-shrink: 0;
}
.post-image-item--single {
  width: 180px;
  height: 120px;
}
.post-image-thumb {
  width: 100%;
  height: 100%;
}
.post-image-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 20px;
  font-weight: 700;
}

.post-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 12px;
}

.post-related-news {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 12px;
  padding: 8px 12px;
  background: #fef2f2;
  border-radius: 8px;
  font-size: 13px;
  color: #dc2626;
  cursor: pointer;
  transition: background 0.2s;
}
.post-related-news:hover {
  background: #fee2e2;
}

.post-actions {
  display: flex;
  gap: 42px;
  margin-top: 12px;
  padding-top: 12px;
  flex-wrap: wrap;
}

.post-action-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  color: #64748b;
  transition: color 0.3s;
}

.post-action-btn:hover {
  color: #dc2626;
}

.post-action-btn .action-count {
  color: #999;
  font-size: 13px;
}

.post-action-btn.action-active {
  color: #dc2626;
}

.post-action-btn.action-active .action-count {
  color: #dc2626;
}

.post-action-btn.action-favorited {
  color: #f59e0b;
}

.post-action-btn.action-favorited .action-count {
  color: #f59e0b;
}
</style>
