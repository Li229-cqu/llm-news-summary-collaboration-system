<template>
  <div class="interactions-panel">
    <!-- 二级 Tab -->
    <div class="sub-tabs">
      <button
        v-for="tab in subTabs"
        :key="tab.key"
        :class="['sub-tab', { active: activeTab === tab.key }]"
        @click="switchTab(tab.key)"
      >
        {{ tab.label }}
      </button>
    </div>

    <!-- 点赞列表 -->
    <div v-if="activeTab === 'likes'" class="interaction-list">
      <div v-if="loading" class="loading-area"><el-spinner /></div>
      <div v-else-if="likes.length === 0" class="empty-area">
        <el-empty description="暂时还没有收到点赞" :image-size="60" />
      </div>
      <div v-else class="interaction-items">
        <div v-for="item in likes" :key="item.id" class="interaction-card">
          <el-avatar :src="normalizeAvatarUrl(item.actor_avatar)" :text="item.actor_nickname.slice(0, 1)" :size="40" />
          <div class="interaction-body">
            <div class="interaction-text">
              <span class="actor-name">{{ item.actor_nickname }}</span>
              <span class="action-desc">赞了你的帖子</span>
            </div>
            <div class="interaction-time">{{ formatRelativeTime(item.action_time) }}</div>
            <div class="target-post-card" @click="openPostDetail(item.target_post_id)">
              <div class="target-post-text">
                <span class="target-post-title">{{ item.target_post_title }}</span>
                <span v-if="item.related_news_title" class="target-post-news">
                  <el-icon><Link /></el-icon>{{ item.related_news_title }}
                </span>
              </div>
            </div>
          </div>
        </div>
        <PaginationBar v-if="likesTotal > pageSize" :current-page="likesPage" :total-pages="Math.ceil(likesTotal / pageSize)" @change="(p: number) => loadLikes(p)"
        />
      </div>
    </div>

    <!-- 评论列表 -->
    <div v-else-if="activeTab === 'comments'" class="interaction-list">
      <div v-if="loading" class="loading-area"><el-spinner /></div>
      <div v-else-if="comments.length === 0" class="empty-area">
        <el-empty description="暂时还没有收到评论" :image-size="60" />
      </div>
      <div v-else class="interaction-items">
        <div v-for="item in comments" :key="item.id" class="interaction-card">
          <el-avatar :src="normalizeAvatarUrl(item.actor_avatar)" :text="item.actor_nickname.slice(0, 1)" :size="40" />
          <div class="interaction-body">
            <div class="interaction-text">
              <span class="actor-name">{{ item.actor_nickname }}</span>
              <span class="action-desc">评论了你的帖子</span>
            </div>
            <div class="interaction-time">{{ formatRelativeTime(item.action_time) }}</div>
            <div class="comment-content">{{ item.comment_content }}</div>
            <div class="target-post-card" @click="openPostDetail(item.target_post_id)">
              <div class="target-post-text">
                <span class="target-post-title">{{ item.target_post_title }}</span>
                <span v-if="item.related_news_title" class="target-post-news">
                  <el-icon><Link /></el-icon>{{ item.related_news_title }}
                </span>
              </div>
            </div>
          </div>
        </div>
        <PaginationBar v-if="commentsTotal > pageSize" :current-page="commentsPage" :total-pages="Math.ceil(commentsTotal / pageSize)" @change="(p: number) => loadComments(p)"
        />
      </div>
    </div>

    <!-- 收藏列表 -->
    <div v-if="activeTab === 'favorites'" class="interaction-list">
      <div v-if="loading" class="loading-area"><el-spinner /></div>
      <div v-else-if="favorites.length === 0" class="empty-area">
        <el-empty description="暂时还没有收到收藏" :image-size="60" />
      </div>
      <div v-else class="interaction-items">
        <div v-for="item in favorites" :key="item.id" class="interaction-card">
          <el-avatar :src="normalizeAvatarUrl(item.actor_avatar)" :text="item.actor_nickname.slice(0, 1)" :size="40" />
          <div class="interaction-body">
            <div class="interaction-text">
              <span class="actor-name">{{ item.actor_nickname }}</span>
              <span class="action-desc">收藏了你的帖子</span>
            </div>
            <div class="interaction-time">{{ formatRelativeTime(item.action_time) }}</div>
            <div class="target-post-card" @click="openPostDetail(item.target_post_id)">
              <div class="target-post-text">
                <span class="target-post-title">{{ item.target_post_title }}</span>
                <span v-if="item.related_news_title" class="target-post-news">
                  <el-icon><Link /></el-icon>{{ item.related_news_title }}
                </span>
              </div>
            </div>
          </div>
        </div>
        <PaginationBar v-if="favoritesTotal > pageSize" :current-page="favoritesPage" :total-pages="Math.ceil(favoritesTotal / pageSize)" @change="(p: number) => loadFavorites(p)"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import PaginationBar from '@/components/common/PaginationBar.vue'
import { Link } from '@element-plus/icons-vue'
import {
  getMyReceivedLikes,
  getMyReceivedComments,
  getMyReceivedFavorites,
  type ReceivedInteractionItem,
} from '@/api/community'

const emit = defineEmits<{
  (e: 'openPostDetail', postId: number): void
}>()

const subTabs = [
  { key: 'likes', label: '点赞' },
  { key: 'comments', label: '评论' },
  { key: 'favorites', label: '收藏' },
]

const activeTab = ref<'likes' | 'comments' | 'favorites'>('likes')
const loading = ref(false)
const pageSize = 10

const likes = ref<ReceivedInteractionItem[]>([])
const likesPage = ref(1)
const likesTotal = ref(0)

const comments = ref<ReceivedInteractionItem[]>([])
const commentsPage = ref(1)
const commentsTotal = ref(0)

const favorites = ref<ReceivedInteractionItem[]>([])
const favoritesPage = ref(1)
const favoritesTotal = ref(0)

function switchTab(tab: string) {
  activeTab.value = tab as 'likes' | 'comments' | 'favorites'
  if (tab === 'likes' && likes.value.length === 0) loadLikes(1)
  else if (tab === 'comments' && comments.value.length === 0) loadComments(1)
  else if (tab === 'favorites' && favorites.value.length === 0) loadFavorites(1)
}

async function loadLikes(page = 1) {
  loading.value = true
  likesPage.value = page
  try {
    const res = await getMyReceivedLikes({ page, page_size: pageSize })
    likes.value = res.list || []
    likesTotal.value = res.total
  } catch {
    ElMessage.error('获取点赞列表失败')
  } finally {
    loading.value = false
  }
}

async function loadComments(page = 1) {
  loading.value = true
  commentsPage.value = page
  try {
    const res = await getMyReceivedComments({ page, page_size: pageSize })
    comments.value = res.list || []
    commentsTotal.value = res.total
  } catch {
    ElMessage.error('获取评论列表失败')
  } finally {
    loading.value = false
  }
}

async function loadFavorites(page = 1) {
  loading.value = true
  favoritesPage.value = page
  try {
    const res = await getMyReceivedFavorites({ page, page_size: pageSize })
    favorites.value = res.list || []
    favoritesTotal.value = res.total
  } catch {
    ElMessage.error('获取收藏列表失败')
  } finally {
    loading.value = false
  }
}

function openPostDetail(postId: number) {
  emit('openPostDetail', postId)
}

function normalizeAvatarUrl(url?: string): string {
  if (!url) return ''
  if (url.startsWith('http://') || url.startsWith('https://') || url.startsWith('data:image/')) return url
  const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'
  return `${baseURL.replace(/\/$/, '')}/${url.replace(/^\//, '')}`
}

function formatRelativeTime(timeStr: string) {
  const now = Date.now()
  const d = new Date(timeStr).getTime()
  const diff = now - d
  const min = Math.floor(diff / 60000)
  if (min < 1) return '刚刚'
  if (min < 60) return `${min}分钟前`
  const hour = Math.floor(min / 60)
  if (hour < 24) return `${hour}小时前`
  const day = Math.floor(hour / 24)
  if (day < 30) return `${day}天前`
  return new Date(timeStr).toLocaleDateString('zh-CN')
}

onMounted(() => {
  loadLikes(1)
})
</script>

<style scoped>
.interactions-panel {
  min-height: 300px;
}

.sub-tabs {
  display: flex;
  gap: 32px;
  margin-bottom: 20px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--color-border);
}

.sub-tab {
  position: relative;
  border: 0;
  background: transparent;
  color: #53657c;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  padding: 4px 0;
  transition: color 0.2s;
}
.sub-tab.active {
  color: #dc2626;
}
.sub-tab.active::after {
  content: '';
  position: absolute;
  left: 0;
  right: 0;
  bottom: -13px;
  height: 3px;
  border-radius: 999px;
  background: #dc2626;
}
.sub-tab:hover {
  color: #dc2626;
}

.loading-area {
  display: flex;
  justify-content: center;
  padding: 48px;
}

.empty-area {
  padding: 48px;
}

.interaction-items {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.interaction-card {
  display: flex;
  gap: 14px;
  padding: 14px 16px;
  border: 1px solid #e3edf9;
  border-radius: 12px;
  background: var(--color-bg-card);
  transition: box-shadow 0.2s;
}
.interaction-card:hover {
  box-shadow: 0 4px 12px rgba(130, 34, 34, 0.06);
}

.interaction-body {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.interaction-text {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.actor-name {
  font-weight: 600;
  font-size: 14px;
  color: var(--color-text-primary);
}

.action-desc {
  font-size: 14px;
  color: var(--color-text-secondary);
}

.interaction-time {
  font-size: 12px;
  color: var(--color-text-muted);
}

.comment-content {
  margin-top: 4px;
  padding: 8px 10px;
  background: var(--color-bg-hover);
  border-radius: 6px;
  font-size: 13px;
  color: #374151;
  line-height: 1.5;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.target-post-card {
  margin-top: 4px;
  padding: 8px 10px;
  background: var(--color-primary-soft);
  border: 1px solid #f5dfdf;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.15s;
}
.target-post-card:hover {
  background: #fee2e2;
}

.target-post-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.target-post-title {
  font-size: 13px;
  font-weight: 500;
  color: #dc2626;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.target-post-news {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: var(--color-text-secondary);
}

.pagination {
  margin-top: 16px;
  display: flex;
  justify-content: center;
}
</style>
