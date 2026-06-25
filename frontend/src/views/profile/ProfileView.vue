<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  ArrowRight,
  ChatDotRound,
  Clock,
  Files,
  Grid,
  MagicStick,
  Star,
  User,
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import {
  type AIRecordItem,
  type BrowseHistoryItem,
  type CommentRecordItem,
  type FavoriteItem,
  type ProfileOverview,
  getAIRecords,
  getBrowseHistory,
  getComments,
  getFavorites,
  getProfileOverview,
} from '@/api/profile'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()

const activeTab = ref('overview')
const loadingTab = ref('')

const profileOverview = ref<ProfileOverview | null>(null)
const browseHistory = ref<BrowseHistoryItem[]>([])
const favorites = ref<FavoriteItem[]>([])
const comments = ref<CommentRecordItem[]>([])
const aiRecords = ref<AIRecordItem[]>([])

const tabs = [
  { key: 'overview', label: '概览', icon: Grid },
  { key: 'history', label: '浏览历史', icon: Clock },
  { key: 'favorites', label: '收藏记录', icon: Star },
  { key: 'comments', label: '评论记录', icon: ChatDotRound },
  { key: 'ai-records', label: 'AI 生成记录', icon: MagicStick },
]

function goToNewsDetail(newsId: number) {
  router.push(`/news/${newsId}`)
}

async function loadOverview() {
  loadingTab.value = 'overview'
  try {
    profileOverview.value = await getProfileOverview()
  } catch (error) {
    console.error(error)
    ElMessage.error('加载个人中心概览失败，请稍后重试')
  } finally {
    loadingTab.value = ''
  }
}

async function loadBrowseHistory() {
  loadingTab.value = 'history'
  try {
    const result = await getBrowseHistory(1, 20)
    browseHistory.value = result.list
  } catch (error) {
    console.error(error)
    ElMessage.error('加载浏览历史失败，请稍后重试')
  } finally {
    loadingTab.value = ''
  }
}

async function loadFavorites() {
  loadingTab.value = 'favorites'
  try {
    const result = await getFavorites(1, 20)
    favorites.value = result.list
  } catch (error) {
    console.error(error)
    ElMessage.error('加载收藏记录失败，请稍后重试')
  } finally {
    loadingTab.value = ''
  }
}

async function loadComments() {
  loadingTab.value = 'comments'
  try {
    const result = await getComments(1, 20)
    comments.value = result.list
  } catch (error) {
    console.error(error)
    ElMessage.error('加载评论记录失败，请稍后重试')
  } finally {
    loadingTab.value = ''
  }
}

async function loadAIRecords() {
  loadingTab.value = 'ai-records'
  try {
    const result = await getAIRecords(1, 20)
    aiRecords.value = result.list
  } catch (error) {
    console.error(error)
    ElMessage.error('加载 AI 生成记录失败，请稍后重试')
  } finally {
    loadingTab.value = ''
  }
}

function handleTabChange(key: string) {
  activeTab.value = key
  if (key === 'overview') {
    loadOverview()
  } else if (key === 'history') {
    loadBrowseHistory()
  } else if (key === 'favorites') {
    loadFavorites()
  } else if (key === 'comments') {
    loadComments()
  } else if (key === 'ai-records') {
    loadAIRecords()
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
          <h1 class="user-name">{{ userStore.userInfo?.nickname || '未登录用户' }}</h1>
          <p class="user-role">
            <el-tag :type="userStore.isAdmin ? 'danger' : userStore.isEditor ? 'warning' : 'info'">
              {{
                userStore.isAdmin
                  ? '管理员'
                  : userStore.isEditor
                    ? '审核/编辑'
                    : '普通用户'
              }}
            </el-tag>
          </p>
          <p class="user-meta">ID: {{ userStore.userInfo?.id || '-' }}</p>
        </div>
      </div>
    </el-card>

    <el-card class="stats-card" shadow="never">
      <div class="stats-grid">
        <div class="stat-item">
          <div class="stat-icon history-icon">
            <Clock :size="24" />
          </div>
          <div class="stat-content">
            <span class="stat-value">{{ profileOverview?.browse_count ?? 0 }}</span>
            <span class="stat-label">浏览记录</span>
          </div>
        </div>
        <div class="stat-item">
          <div class="stat-icon star-icon">
            <Star :size="24" />
          </div>
          <div class="stat-content">
            <span class="stat-value">{{ profileOverview?.favorite_count ?? 0 }}</span>
            <span class="stat-label">收藏记录</span>
          </div>
        </div>
        <div class="stat-item">
          <div class="stat-icon comment-icon">
            <Files :size="24" />
          </div>
          <div class="stat-content">
            <span class="stat-value">{{ profileOverview?.comment_count ?? 0 }}</span>
            <span class="stat-label">评论记录</span>
          </div>
        </div>
        <div class="stat-item">
          <div class="stat-icon ai-icon">
            <MagicStick :size="24" />
          </div>
          <div class="stat-content">
            <span class="stat-value">{{ profileOverview?.ai_generate_count ?? 0 }}</span>
            <span class="stat-label">AI 生成</span>
          </div>
        </div>
      </div>
    </el-card>

    <el-card class="content-card" shadow="never">
      <el-tabs v-model="activeTab" class="profile-tabs" @tab-change="handleTabChange">
        <el-tab-pane v-for="tab in tabs" :key="tab.key" :name="tab.key">
          <template #label>
            <component :is="tab.icon" :size="18" class="tab-icon" />
            <span>{{ tab.label }}</span>
          </template>

          <div v-if="loadingTab === tab.key" class="loading-container">
            <el-skeleton :rows="6" animated />
          </div>

          <template v-else-if="tab.key === 'overview'">
            <div class="overview-content">
              <p class="overview-desc">
                欢迎来到个人中心，这里展示你的浏览、收藏、评论和 AI 生成记录。
              </p>
              <div class="quick-actions">
                <el-button type="primary" plain @click="handleTabChange('history')">
                  查看浏览历史
                </el-button>
                <el-button type="primary" plain @click="handleTabChange('favorites')">
                  查看收藏记录
                </el-button>
                <el-button type="primary" plain @click="handleTabChange('comments')">
                  查看评论记录
                </el-button>
                <el-button type="primary" plain @click="handleTabChange('ai-records')">
                  查看 AI 记录
                </el-button>
              </div>
            </div>
          </template>

          <template v-else-if="tab.key === 'history'">
            <div v-if="browseHistory.length === 0" class="empty-state">
              <Clock :size="48" class="empty-icon" />
              <p>暂无浏览历史</p>
            </div>
            <div v-else class="record-list">
              <el-card
                v-for="item in browseHistory"
                :key="`${item.news_id}-${item.browse_time}`"
                class="record-card"
                shadow="hover"
              >
                <div class="record-header">
                  <el-tag size="small">{{ item.category_name }}</el-tag>
                  <span class="record-source">{{ item.title }}</span>
                </div>
                <div class="record-footer">
                  <Clock :size="14" />
                  <span>{{ item.browse_time }}</span>
                  <el-button type="primary" link class="record-link" @click="goToNewsDetail(item.news_id)">
                    查看原文
                    <ArrowRight :size="14" />
                  </el-button>
                </div>
              </el-card>
            </div>
          </template>

          <template v-else-if="tab.key === 'favorites'">
            <div v-if="favorites.length === 0" class="empty-state">
              <Star :size="48" class="empty-icon" />
              <p>暂无收藏记录</p>
            </div>
            <div v-else class="record-list">
              <el-card
                v-for="item in favorites"
                :key="item.news_id"
                class="record-card"
                shadow="hover"
              >
                <div class="record-header">
                  <el-tag size="small">{{ item.category_name }}</el-tag>
                  <span class="record-source">{{ item.source }}</span>
                </div>
                <h3 class="record-title" @click="goToNewsDetail(item.news_id)">
                  {{ item.title }}
                </h3>
                <p class="record-summary">{{ item.summary }}</p>
                <div class="record-footer">
                  <Clock :size="14" />
                  <span>{{ item.publish_time }}</span>
                  <el-button type="primary" link class="record-link" @click="goToNewsDetail(item.news_id)">
                    查看详情
                    <ArrowRight :size="14" />
                  </el-button>
                </div>
              </el-card>
            </div>
          </template>

          <template v-else-if="tab.key === 'comments'">
            <div v-if="comments.length === 0" class="empty-state">
              <ChatDotRound :size="48" class="empty-icon" />
              <p>暂无评论记录</p>
            </div>
            <div v-else class="record-list">
              <el-card
                v-for="item in comments"
                :key="item.comment_id"
                class="record-card"
                shadow="hover"
              >
                <div class="record-header">
                  <el-tag size="small">{{ item.category_name }}</el-tag>
                  <span class="record-source">{{ item.news_title }}</span>
                </div>
                <p class="comment-content">{{ item.content }}</p>
                <div class="record-footer">
                  <Clock :size="14" />
                  <span>{{ item.create_time }}</span>
                  <span class="comment-like">点赞 {{ item.like_count }}</span>
                  <el-button type="primary" link class="record-link" @click="goToNewsDetail(item.news_id)">
                    查看原文
                    <ArrowRight :size="14" />
                  </el-button>
                </div>
              </el-card>
            </div>
          </template>

          <template v-else-if="tab.key === 'ai-records'">
            <div v-if="aiRecords.length === 0" class="empty-state">
              <MagicStick :size="48" class="empty-icon" />
              <p>暂无 AI 生成记录</p>
            </div>
            <div v-else class="record-list">
              <el-card
                v-for="item in aiRecords"
                :key="item.id"
                class="record-card"
                shadow="hover"
              >
                <div class="record-header">
                  <div class="record-header-main">
                    <el-tag size="small">AI 记录</el-tag>
                    <span class="record-ai-title">{{ item.source_title || `记录 #${item.id}` }}</span>
                  </div>
                  <el-tag
                    :type="item.risk_level === 'high' ? 'danger' : item.risk_level === 'medium' ? 'warning' : 'success'"
                    size="small"
                  >
                    {{ item.risk_level === 'high' ? '高风险' : item.risk_level === 'medium' ? '中风险' : '低风险' }}
                  </el-tag>
                </div>
                <div class="ai-input">
                  <span class="section-label">输入文本</span>
                  <p>{{ item.input_text }}</p>
                </div>
                <div class="ai-titles">
                  <span class="section-label">候选标题</span>
                  <div class="title-tags">
                    <el-tag v-for="(title, index) in item.candidate_titles" :key="index" size="small">
                      {{ title }}
                    </el-tag>
                  </div>
                </div>
                <div class="ai-summary">
                  <span class="section-label">生成摘要</span>
                  <p>{{ item.summary_short }}</p>
                </div>
                <div class="record-footer">
                  <Clock :size="14" />
                  <span>{{ item.create_time || '暂无时间' }}</span>
                  <span class="record-source">{{ item.source === 'news' ? '新闻导入' : '手动输入' }}</span>
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
  max-width: 980px;
  margin: 0 auto;
  padding: 24px;
}

.user-info-card,
.stats-card {
  margin-bottom: 24px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 24px;
}

.user-details {
  min-width: 0;
}

.user-name {
  margin: 0 0 8px;
  font-size: 24px;
  font-weight: 600;
}

.user-role,
.user-meta {
  margin: 0 0 8px;
}

.user-meta {
  color: var(--el-text-color-secondary);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  border-radius: 12px;
  background: var(--el-bg-color-page);
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.history-icon {
  background: #e8f4fd;
  color: #409eff;
}

.star-icon {
  background: #fdf6ec;
  color: #e6a23c;
}

.comment-icon {
  background: #ecf5ff;
  color: #409eff;
}

.ai-icon {
  background: #f4f1ff;
  color: #8b5cf6;
}

.stat-content {
  min-width: 0;
}

.stat-value {
  display: block;
  font-size: 24px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.stat-label {
  display: block;
  font-size: 13px;
  color: var(--el-text-color-secondary);
}

.content-card {
  min-height: 420px;
}

.tab-icon {
  margin-right: 6px;
}

.loading-container {
  padding: 24px 0;
}

.overview-content {
  padding: 24px 8px 8px;
  text-align: center;
}

.overview-desc {
  margin: 0 0 20px;
  color: var(--el-text-color-secondary);
}

.quick-actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 12px;
}

.empty-state {
  padding: 48px 16px;
  text-align: center;
  color: var(--el-text-color-secondary);
}

.empty-icon {
  margin-bottom: 12px;
  color: var(--el-text-color-placeholder);
}

.record-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 8px 0 0;
}

.record-card {
  cursor: default;
}

.record-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.record-header-main {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.record-source {
  color: var(--el-text-color-secondary);
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.record-ai-title,
.record-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.record-title {
  margin: 0 0 8px;
  cursor: pointer;
}

.record-title:hover {
  color: var(--el-color-primary);
}

.record-summary,
.comment-content,
.ai-input p,
.ai-summary p {
  margin: 0;
  color: var(--el-text-color-secondary);
  line-height: 1.7;
}

.record-footer {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 12px;
  color: var(--el-text-color-secondary);
  font-size: 13px;
  flex-wrap: wrap;
}

.record-link {
  margin-left: auto;
}

.comment-like {
  color: var(--el-text-color-secondary);
}

.section-label {
  display: inline-block;
  margin-bottom: 8px;
  font-size: 13px;
  color: var(--el-text-color-secondary);
}

.ai-input,
.ai-titles,
.ai-summary {
  margin-bottom: 12px;
}

.title-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

@media (max-width: 768px) {
  .page-container {
    padding: 16px;
  }

  .stats-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .user-info {
    flex-direction: column;
    align-items: flex-start;
  }

  .record-header,
  .record-footer {
    align-items: flex-start;
    flex-direction: column;
  }

  .record-link {
    margin-left: 0;
  }
}
</style>
