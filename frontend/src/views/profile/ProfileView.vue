<script setup lang="ts">
import { ref, onMounted } from 'vue'
import {
  User,
  Clock,
  Star,
  MagicStick,
  Grid,
  Files,
  PriceTag,
  ArrowRight,
} from '@element-plus/icons-vue'
import {
  type ProfileOverview,
  type BrowseHistoryItem,
  type FavoriteItem,
  type AIRecordItem,
  getProfileOverview,
  getBrowseHistory,
  getFavorites,
  getAIRecords,
} from '@/api/profile'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()

const activeTab = ref('overview')
const profileOverview = ref<ProfileOverview | null>(null)
const browseHistory = ref<BrowseHistoryItem[]>([])
const favorites = ref<FavoriteItem[]>([])
const aiRecords = ref<AIRecordItem[]>([])
const loading = ref(false)

const tabs = [
  { key: 'overview', label: '概览', icon: Grid },
  { key: 'history', label: '浏览历史', icon: Clock },
  { key: 'favorites', label: '收藏', icon: Star },
  { key: 'ai-records', label: 'AI 生成记录', icon: MagicStick },
]

async function loadOverview() {
  loading.value = true
  try {
    profileOverview.value = await getProfileOverview()
  } finally {
    loading.value = false
  }
}

async function loadBrowseHistory() {
  loading.value = true
  try {
    const result = await getBrowseHistory(1, 20)
    browseHistory.value = result.list
  } finally {
    loading.value = false
  }
}

async function loadFavorites() {
  loading.value = true
  try {
    const result = await getFavorites(1, 20)
    favorites.value = result.list
  } finally {
    loading.value = false
  }
}

async function loadAIRecords() {
  loading.value = true
  try {
    const result = await getAIRecords(1, 20)
    aiRecords.value = result.list
  } finally {
    loading.value = false
  }
}

function handleTabChange(key: string) {
  activeTab.value = key
  switch (key) {
    case 'overview':
      loadOverview()
      break
    case 'history':
      loadBrowseHistory()
      break
    case 'favorites':
      loadFavorites()
      break
    case 'ai-records':
      loadAIRecords()
      break
  }
}

onMounted(() => {
  loadOverview()
})
</script>

<template>
  <main class="page-container">
    <el-card class="user-info-card" shadow="never">
      <div class="user-info">
        <div class="avatar-wrapper">
          <el-avatar :size="80" :icon="User">
            {{ userStore.userInfo?.nickname?.charAt(0) || '用' }}
          </el-avatar>
        </div>
        <div class="user-details">
          <h1 class="user-name">{{ userStore.userInfo?.nickname }}</h1>
          <p class="user-role">
            <el-tag :type="userStore.isAdmin ? 'danger' : userStore.isEditor ? 'warning' : 'info'">
              {{ userStore.isAdmin ? '管理员' : userStore.isEditor ? '审核/编辑' : '普通用户' }}
            </el-tag>
          </p>
          <p class="user-meta">ID: {{ userStore.userInfo?.id }}</p>
        </div>
      </div>
    </el-card>

    <el-card class="stats-card" shadow="never">
      <div class="stats-grid">
        <div class="stat-item">
          <div class="stat-icon history-icon">
            <History :size="24" />
          </div>
          <div class="stat-content">
            <span class="stat-value">{{ profileOverview?.browse_count || 0 }}</span>
            <span class="stat-label">浏览记录</span>
          </div>
        </div>
        <div class="stat-item">
          <div class="stat-icon star-icon">
            <Star :size="24" />
          </div>
          <div class="stat-content">
            <span class="stat-value">{{ profileOverview?.favorite_count || 0 }}</span>
            <span class="stat-label">收藏</span>
          </div>
        </div>
        <div class="stat-item">
          <div class="stat-icon comment-icon">
            <Files :size="24" />
          </div>
          <div class="stat-content">
            <span class="stat-value">{{ profileOverview?.comment_count || 0 }}</span>
            <span class="stat-label">评论</span>
          </div>
        </div>
        <div class="stat-item">
          <div class="stat-icon ai-icon">
            <Sparkles :size="24" />
          </div>
          <div class="stat-content">
            <span class="stat-value">{{ profileOverview?.ai_generate_count || 0 }}</span>
            <span class="stat-label">AI 生成</span>
          </div>
        </div>
      </div>
    </el-card>

    <el-card class="content-card" shadow="never">
      <el-tabs v-model="activeTab" @tab-change="handleTabChange" class="profile-tabs">
        <el-tab-pane
          v-for="tab in tabs"
          :key="tab.key"
          :label="tab.label"
          :name="tab.key"
        >
          <template #label>
            <component :is="tab.icon" :size="18" class="tab-icon" />
            <span>{{ tab.label }}</span>
          </template>

          <div v-if="loading" class="loading-container">
            <el-spinner />
          </div>

          <template v-else-if="activeTab === 'overview'">
            <div class="overview-content">
              <p class="overview-desc">欢迎来到个人中心，这里展示您的互动记录和数据统计。</p>
              <div class="quick-actions">
                <el-button @click="handleTabChange('history')" type="primary" plain>
                  查看浏览历史
                </el-button>
                <el-button @click="handleTabChange('favorites')" type="primary" plain>
                  查看收藏
                </el-button>
                <el-button @click="handleTabChange('ai-records')" type="primary" plain>
                  查看 AI 记录
                </el-button>
              </div>
            </div>
          </template>

          <template v-else-if="activeTab === 'history'">
            <div v-if="browseHistory.length === 0" class="empty-state">
              <History :size="48" class="empty-icon" />
              <p>暂无浏览历史</p>
            </div>
            <div v-else class="list-container">
              <el-timeline mode="left">
                <el-timeline-item
                  v-for="item in browseHistory"
                  :key="item.news_id"
                  :timestamp="item.browse_time"
                  placement="bottom"
                >
                  <div class="timeline-content">
                    <el-tag>{{ item.category_name }}</el-tag>
                    <span class="timeline-title">{{ item.title }}</span>
                  </div>
                </el-timeline-item>
              </el-timeline>
            </div>
          </template>

          <template v-else-if="activeTab === 'favorites'">
            <div v-if="favorites.length === 0" class="empty-state">
              <Star :size="48" class="empty-icon" />
              <p>暂无收藏内容</p>
            </div>
            <div v-else class="favorites-list">
              <el-card
                v-for="item in favorites"
                :key="item.news_id"
                class="favorite-item"
                shadow="hover"
              >
                <div class="favorite-header">
                  <el-tag size="small">{{ item.category_name }}</el-tag>
                  <span class="favorite-source">{{ item.source }}</span>
                </div>
                <h3 class="favorite-title">{{ item.title }}</h3>
                <p class="favorite-summary">{{ item.summary }}</p>
                <div class="favorite-footer">
                  <Clock :size="14" />
                  <span>{{ item.publish_time }}</span>
                  <ArrowRight :size="18" class="chevron-icon" />
                </div>
              </el-card>
            </div>
          </template>

          <template v-else-if="activeTab === 'ai-records'">
            <div v-if="aiRecords.length === 0" class="empty-state">
              <Sparkles :size="48" class="empty-icon" />
              <p>暂无 AI 生成记录</p>
            </div>
            <div v-else class="ai-records-list">
              <el-card
                v-for="item in aiRecords"
                :key="item.id"
                class="ai-record-item"
                shadow="hover"
              >
                <div class="record-header">
                  <span class="record-id">记录 #{{ item.id }}</span>
                  <span v-if="item.create_time" class="record-time">{{ item.create_time }}</span>
                </div>
                <div class="record-input">
                  <PriceTag size="small" class="input-tag">输入文本</PriceTag>
                  <p>{{ item.input_text }}</p>
                </div>
                <div class="record-titles">
                  <PriceTag size="small" class="titles-tag">候选标题</PriceTag>
                  <div class="titles-list">
                    <span
                      v-for="(title, index) in item.candidate_titles"
                      :key="index"
                      class="title-item"
                    >
                      {{ title }}
                    </span>
                  </div>
                </div>
                <div class="record-summary">
                  <PriceTag size="small" class="summary-tag">生成摘要</PriceTag>
                  <p>{{ item.summary_short }}</p>
                </div>
              </el-card>
            </div>
          </template>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </main>
</template>

<style scoped>
.page-container {
  padding: 24px;
  max-width: 800px;
  margin: 0 auto;
}

.user-info-card {
  margin-bottom: 24px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 24px;
}

.avatar-wrapper {
  flex-shrink: 0;
}

.user-details {
  flex: 1;
}

.user-name {
  margin: 0 0 8px;
  font-size: 24px;
  font-weight: 600;
}

.user-role {
  margin: 0 0 8px;
}

.user-meta {
  margin: 0;
  color: var(--color-text-secondary);
  font-size: 14px;
}

.stats-card {
  margin-bottom: 24px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 16px;
  background: var(--color-bg-page);
  border-radius: 8px;
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 8px;
}

.history-icon {
  background: #e8f4fd;
  color: #409eff;
}

.star-icon {
  background: #fef7e0;
  color: #e6a23c;
}

.comment-icon {
  background: #e6f7ff;
  color: #1890ff;
}

.ai-icon {
  background: #f9f0ff;
  color: #722ed1;
}

.stat-content {
  text-align: center;
}

.stat-value {
  display: block;
  font-size: 24px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.stat-label {
  display: block;
  font-size: 13px;
  color: var(--color-text-secondary);
}

.content-card {
  min-height: 400px;
}

.profile-tabs {
  min-height: 350px;
}

.tab-icon {
  margin-right: 8px;
}

.loading-container {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 200px;
}

.overview-content {
  padding: 40px 24px;
  text-align: center;
}

.overview-desc {
  color: var(--color-text-secondary);
  margin-bottom: 24px;
}

.quick-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 24px;
  color: var(--color-text-secondary);
}

.empty-icon {
  margin-bottom: 16px;
  color: var(--color-text-placeholder);
}

.list-container {
  padding: 16px;
}

.timeline-content {
  display: flex;
  align-items: center;
  gap: 12px;
}

.timeline-title {
  flex: 1;
  font-size: 14px;
  color: var(--color-text-primary);
}

.favorites-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.favorite-item {
  cursor: pointer;
}

.favorite-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.favorite-source {
  font-size: 13px;
  color: var(--color-text-secondary);
}

.favorite-title {
  margin: 0 0 8px;
  font-size: 16px;
  font-weight: 500;
}

.favorite-summary {
  margin: 0 0 12px;
  font-size: 14px;
  color: var(--color-text-secondary);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.favorite-footer {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--color-text-secondary);
}

.chevron-icon {
  margin-left: auto;
  color: var(--color-text-placeholder);
}

.ai-records-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.ai-record-item {
  padding: 16px;
}

.record-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.record-id {
  font-weight: 500;
  color: var(--color-text-primary);
}

.record-time {
  font-size: 13px;
  color: var(--color-text-secondary);
}

.record-input,
.record-titles,
.record-summary {
  margin-bottom: 12px;
}

.record-input:last-child,
.record-titles:last-child,
.record-summary:last-child {
  margin-bottom: 0;
}

.input-tag,
.titles-tag,
.summary-tag {
  margin-bottom: 8px;
}

.record-input p,
.record-summary p {
  margin: 0;
  font-size: 14px;
  color: var(--color-text-primary);
}

.titles-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.title-item {
  padding: 4px 12px;
  background: var(--color-bg-page);
  border-radius: 4px;
  font-size: 13px;
  color: var(--color-text-primary);
}

@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .user-info {
    flex-direction: column;
    text-align: center;
  }

  .quick-actions {
    flex-direction: column;
  }
}
</style>
