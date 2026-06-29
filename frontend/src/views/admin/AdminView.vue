<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  User,
  UserFilled,
  Files,
  Message,
  TrendCharts,
  Setting,
  Lock,
  DataBoard,
  Clock,
  Check,
  Warning,
  Grid,
  Key,
  InfoFilled,
  PieChart,
  Refresh,
  Edit,
  Delete,
  Plus,
  Top,
  Bottom,


} from '@element-plus/icons-vue'
import {
  type AdminDashboard,
  type UserItem,
  type PendingPostItem,
  type HotTopicItem,
  type HotTopicForm,
  type SimpleHotTopicItem,
  type SimpleHotTopicForm,
  type SimpleHotTopicUpdateForm,
  getDashboard,
  getPendingPosts,
  getUsers,
  getSystemConfig,
  approvePost,
  rejectPost,
  getNewsHotRanking,
  createNewsHot,
  updateNewsHot,
  deleteNewsHot,
  getCommunityHotTopics,
  createCommunityHot,
  updateCommunityHot,
  deleteCommunityHot,
  getHotTopics,
  createHotTopic,
  updateHotTopic,
  deleteHotTopic,
} from '@/api/admin'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
const activeTab = ref('dashboard')
const dashboard = ref<AdminDashboard | null>(null)
const pendingPosts = ref<PendingPostItem[]>([])
const pendingTotal = ref(0)
const pendingPage = ref(1)
const pendingPageSize = ref(10)
const users = ref<UserItem[]>([])
const systemConfig = ref<Record<string, unknown> | null>(null)
const newsHotList = ref<HotTopicItem[]>([])
const communityHotList = ref<HotTopicItem[]>([])
const hotTopicSubTab = ref<'news' | 'community'>('news')

const loading = ref(false)
const auditLoading = ref<Record<number, boolean>>({})

// 热搜对话框
const hotTopicDialogVisible = ref(false)
const hotTopicDialogTitle = ref('添加热搜话题')
const hotTopicForm = ref<HotTopicForm>({
  title: '',
  heat_score: 0,
  target_type: 'news',
  target_id: undefined,
  tag: '',
  rank_no: 0,
  status: 1,
})
const editingHotTopicId = ref<number | null>(null)

// 简化热搜管理
const simpleHotList = ref<SimpleHotTopicItem[]>([])
const simpleHotTotal = ref(0)
const simpleHotPage = ref(1)
const simpleHotPageSize = ref(20)
const simpleHotDialogVisible = ref(false)
const simpleHotDialogTitle = ref('添加热搜关键词')
const simpleHotForm = ref<SimpleHotTopicForm>({ keyword: '', heat: 0 })
const editingSimpleHotId = ref<number | null>(null)

// 驳回对话框
const rejectDialogVisible = ref(false)
const rejectReason = ref('')
const rejectingPostId = ref<number | null>(null)

const tabs = [
  { key: 'dashboard', label: '概览', icon: Grid },
  { key: 'pending', label: '帖子审核', icon: Warning },
  { key: 'hot-topics', label: '热搜管理', icon: PieChart },
  { key: 'users', label: '用户管理', icon: UserFilled },
  { key: 'config', label: '系统配置', icon: Setting },
]

const statsCards = [
  {
    title: '用户总数',
    value: 0,
    icon: User,
    color: 'primary',
    bgColor: '#e8f4fd',
    iconColor: '#409eff',
  },
  {
    title: '新闻数量',
    value: 0,
    icon: Files,
    color: 'success',
    bgColor: '#f0f9eb',
    iconColor: '#67c23a',
  },
  {
    title: '社区帖子',
    value: 0,
    icon: Message,
    color: 'warning',
    bgColor: '#fef7e0',
    iconColor: '#e6a23c',
  },
  {
    title: '待审核',
    value: 0,
    icon: Warning,
    color: 'danger',
    bgColor: '#fef0f0',
    iconColor: '#f56c6c',
  },
]

const editorFeatures = [
  {
    key: 'content-audit',
    title: '内容审核',
    description: '审核待发布的帖子内容',
    icon: Warning,
    targetTab: 'pending',
    status: 'available',
    adminOnly: false,
  },
  {
    key: 'community-posts',
    title: '社区帖子管理',
    description: '审核和管理社区帖子',
    icon: TrendCharts,
    targetTab: 'pending',
    status: 'available',
    adminOnly: false,
  },
  {
    key: 'hot-topics',
    title: '热搜话题维护',
    description: '管理热门话题和搜索词',
    icon: PieChart,
    targetTab: 'hot-topics',
    status: 'available',
    adminOnly: false,
  },
  {
    key: 'comment-filter',
    title: '评论筛选',
    description: '管理和处理用户评论',
    icon: Message,
    status: 'coming-soon',
    adminOnly: false,
  },
]

const adminFeatures = [
  {
    key: 'account-mgmt',
    title: '账号管理',
    description: '管理平台用户账号',
    icon: User,
    targetTab: 'users',
    status: 'available',
    adminOnly: true,
  },
  {
    key: 'ai-config',
    title: 'AI 模型配置',
    description: '配置 AI 服务参数',
    icon: Setting,
    targetTab: 'config',
    status: 'available',
    adminOnly: true,
  },
  {
    key: 'prompt-template',
    title: '提示词模板',
    description: '管理 AI 提示词模板',
    icon: Files,
    targetTab: 'config',
    status: 'available',
    adminOnly: true,
  },
  {
    key: 'role-permission',
    title: '角色权限管理',
    description: '配置用户角色和权限',
    icon: Key,
    status: 'coming-soon',
    adminOnly: true,
  },
  {
    key: 'content-mgmt',
    title: '内容总管理',
    description: '全站内容统一管理',
    icon: DataBoard,
    status: 'coming-soon',
    adminOnly: true,
  },
  {
    key: 'system-logs',
    title: '系统日志',
    description: '查看系统运行日志',
    icon: PieChart,
    status: 'coming-soon',
    adminOnly: true,
  },
  {
    key: 'backup-recovery',
    title: '数据备份与恢复',
    description: '数据维护和备份',
    icon: Refresh,
    status: 'coming-soon',
    adminOnly: true,
  },
]

function updateStats() {
  if (dashboard.value) {
    statsCards[0].value = dashboard.value.user_count
    statsCards[1].value = dashboard.value.news_count
    statsCards[2].value = dashboard.value.post_count
    statsCards[3].value = dashboard.value.pending_count
  }
}

async function loadDashboard() {
  loading.value = true
  try {
    dashboard.value = await getDashboard()
    updateStats()
  } finally {
    loading.value = false
  }
}

async function loadPendingPosts() {
  loading.value = true
  try {
    const result = await getPendingPosts(pendingPage.value, pendingPageSize.value)
    pendingPosts.value = result.list
    pendingTotal.value = result.total
  } finally {
    loading.value = false
  }
}

async function handleApprove(postId: number) {
  try {
    await ElMessageBox.confirm('确认通过该帖子的审核？', '审核通过', {
      confirmButtonText: '确认通过',
      cancelButtonText: '取消',
      type: 'success',
    })
  } catch {
    return
  }

  auditLoading.value[postId] = true
  try {
    const result = await approvePost(postId)
    ElMessage.success(result.message || '审核通过')
    await loadPendingPosts()
    await loadDashboard()
  } catch (err: any) {
    ElMessage.error(err?.message || '操作失败')
  } finally {
    auditLoading.value[postId] = false
  }
}

function openRejectDialog(postId: number) {
  rejectingPostId.value = postId
  rejectReason.value = ''
  rejectDialogVisible.value = true
}

async function handleReject() {
  const postId = rejectingPostId.value
  if (!postId) return

  auditLoading.value[postId] = true
  rejectDialogVisible.value = false
  try {
    const result = await rejectPost(postId, rejectReason.value || undefined)
    ElMessage.success(result.message || '已驳回')
    await loadPendingPosts()
    await loadDashboard()
  } catch (err: any) {
    ElMessage.error(err?.message || '操作失败')
  } finally {
    auditLoading.value[postId] = false
    rejectingPostId.value = null
    rejectReason.value = ''
  }
}

function handlePendingPageChange(page: number) {
  pendingPage.value = page
  loadPendingPosts()
}

// ==================== 热搜管理 ====================

async function loadNewsHot() {
  loading.value = true
  try {
    const result = await getNewsHotRanking(1, 20)
    newsHotList.value = result.list
  } finally {
    loading.value = false
  }
}

async function loadCommunityHot() {
  loading.value = true
  try {
    const result = await getCommunityHotTopics(1, 20)
    communityHotList.value = result.list
  } finally {
    loading.value = false
  }
}

function openHotTopicDialog(topic?: HotTopicItem) {
  if (topic) {
    editingHotTopicId.value = topic.id
    hotTopicDialogTitle.value = '编辑热搜'
    hotTopicForm.value = {
      title: topic.title,
      heat_score: topic.heat_score,
      target_type: topic.target_type || '',
      target_id: topic.target_id,
      tag: topic.tag || '',
      rank_no: topic.rank_no,
      status: topic.status,
    }
  } else {
    editingHotTopicId.value = null
    hotTopicDialogTitle.value = hotTopicSubTab.value === 'news' ? '添加新闻热搜' : '添加社区热搜'
    hotTopicForm.value = {
      title: '',
      heat_score: 0,
      target_type: hotTopicSubTab.value === 'news' ? 'news' : 'community',
      target_id: undefined,
      tag: '',
      rank_no: 0,
      status: 1,
    }
  }
  hotTopicDialogVisible.value = true
}

async function handleHotTopicSave() {
  if (!hotTopicForm.value.title.trim()) {
    ElMessage.warning('标题不能为空')
    return
  }

  const isNews = hotTopicSubTab.value === 'news'
  loading.value = true
  hotTopicDialogVisible.value = false
  try {
    if (editingHotTopicId.value) {
      if (isNews) {
        await updateNewsHot(editingHotTopicId.value, hotTopicForm.value)
      } else {
        await updateCommunityHot(editingHotTopicId.value, hotTopicForm.value)
      }
      ElMessage.success('已更新')
    } else {
      if (isNews) {
        await createNewsHot(hotTopicForm.value)
      } else {
        await createCommunityHot(hotTopicForm.value)
      }
      ElMessage.success('已添加')
    }
    if (isNews) await loadNewsHot()
    else await loadCommunityHot()
    await loadDashboard()
  } catch (err: any) {
    ElMessage.error(err?.message || '操作失败')
  } finally {
    loading.value = false
  }
}

async function handleDeleteHotTopic(topic: HotTopicItem) {
  try {
    await ElMessageBox.confirm(
      `确认删除「${topic.title}」？`,
      '删除确认',
      { confirmButtonText: '确认删除', cancelButtonText: '取消', type: 'warning' }
    )
  } catch {
    return
  }

  const isNews = hotTopicSubTab.value === 'news'
  loading.value = true
  try {
    if (isNews) {
      await deleteNewsHot(topic.id)
    } else {
      await deleteCommunityHot(topic.id)
    }
    ElMessage.success('已删除')
    if (isNews) await loadNewsHot()
    else await loadCommunityHot()
    await loadDashboard()
  } catch (err: any) {
    ElMessage.error(err?.message || '操作失败')
  } finally {
    loading.value = false
  }
}

// ==================== 简化热搜管理（E2） ====================

async function loadSimpleHotTopics() {
  loading.value = true
  try {
    const result = await getHotTopics(simpleHotPage.value, simpleHotPageSize.value)
    simpleHotList.value = result.list
    simpleHotTotal.value = result.total
  } finally {
    loading.value = false
  }
}

function openSimpleHotDialog(topic?: SimpleHotTopicItem) {
  if (topic) {
    editingSimpleHotId.value = topic.id
    simpleHotDialogTitle.value = '编辑热搜关键词'
    simpleHotForm.value = {
      keyword: topic.keyword,
      heat: topic.heat,
    }
  } else {
    editingSimpleHotId.value = null
    simpleHotDialogTitle.value = '添加热搜关键词'
    simpleHotForm.value = { keyword: '', heat: 0 }
  }
  simpleHotDialogVisible.value = true
}

async function handleSimpleHotSave() {
  if (!simpleHotForm.value.keyword.trim()) {
    ElMessage.warning('关键词不能为空')
    return
  }

  loading.value = true
  simpleHotDialogVisible.value = false
  try {
    if (editingSimpleHotId.value) {
      await updateHotTopic(editingSimpleHotId.value, simpleHotForm.value as SimpleHotTopicUpdateForm)
      ElMessage.success('已更新')
    } else {
      await createHotTopic(simpleHotForm.value)
      ElMessage.success('已添加')
    }
    await loadSimpleHotTopics()
  } catch (err: any) {
    ElMessage.error(err?.message || '操作失败')
  } finally {
    loading.value = false
  }
}

async function handleTogglePin(topic: SimpleHotTopicItem) {
  loading.value = true
  try {
    await updateHotTopic(topic.id, { is_pinned: !topic.is_pinned })
    ElMessage.success(topic.is_pinned ? '已取消置顶' : '已置顶')
    await loadSimpleHotTopics()
  } catch (err: any) {
    ElMessage.error(err?.message || '操作失败')
  } finally {
    loading.value = false
  }
}

async function handleToggleStatus(topic: SimpleHotTopicItem) {
  const newStatus = topic.status === 1 ? 0 : 1
  const actionLabel = newStatus === 1 ? '上架' : '下架'
  try {
    await ElMessageBox.confirm(
      `确认${actionLabel}「${topic.keyword}」？`,
      `${actionLabel}确认`,
      { confirmButtonText: `确认${actionLabel}`, cancelButtonText: '取消', type: 'warning' }
    )
  } catch {
    return
  }

  loading.value = true
  try {
    await updateHotTopic(topic.id, { status: newStatus })
    ElMessage.success(`已${actionLabel}`)
    await loadSimpleHotTopics()
  } catch (err: any) {
    ElMessage.error(err?.message || '操作失败')
  } finally {
    loading.value = false
  }
}

async function handleDeleteSimpleHot(topic: SimpleHotTopicItem) {
  try {
    await ElMessageBox.confirm(
      `确认删除「${topic.keyword}」？`,
      '删除确认',
      { confirmButtonText: '确认删除', cancelButtonText: '取消', type: 'warning' }
    )
  } catch {
    return
  }

  loading.value = true
  try {
    await deleteHotTopic(topic.id)
    ElMessage.success('已删除')
    await loadSimpleHotTopics()
  } catch (err: any) {
    ElMessage.error(err?.message || '操作失败')
  } finally {
    loading.value = false
  }
}

function handleSimpleHotPageChange(page: number) {
  simpleHotPage.value = page
  loadSimpleHotTopics()
}

async function loadUsers() {
  loading.value = true
  try {
    const result = await getUsers(1, 20)
    users.value = result.list
  } finally {
    loading.value = false
  }
}

async function loadSystemConfig() {
  loading.value = true
  try {
    systemConfig.value = await getSystemConfig()
  } finally {
    loading.value = false
  }
}

function handleTabChange(key: string) {
  activeTab.value = key
  switch (key) {
    case 'dashboard':
      loadDashboard()
      break
    case 'pending':
      loadPendingPosts()
      break
    case 'hot-topics':
      loadSimpleHotTopics()
      break
    case 'users':
      loadUsers()
      break
    case 'config':
      loadSystemConfig()
      break
  }
}

function handleFeatureClick(feature: any) {
  if (feature.adminOnly && !userStore.isAdmin) {
    ElMessage.warning('需要管理员权限访问此功能')
    return
  }

  if (feature.status === 'coming-soon') {
    ElMessage.info(`${feature.title}功能待开发，敬请期待`)
    return
  }

  if (feature.targetTab) {
    handleTabChange(feature.targetTab)
    return
  }

  ElMessage.info(`${feature.title}功能待开发`)
}

function getRoleLabel(role: string) {
  const roleMap: Record<string, string> = {
    user: '普通用户',
    editor: '审核编辑',
    admin: '管理员',
  }
  return roleMap[role] || role
}

function getRoleType(role: string) {
  const typeMap: Record<string, string> = {
    user: 'info',
    editor: 'warning',
    admin: 'danger',
  }
  return typeMap[role] || 'info'
}

function getStatusLabel(status: number) {
  const map: Record<number, string> = {
    0: '待审核',
    1: '已发布',
    2: '已驳回',
    3: '待审核',
  }
  return map[status] || '未知'
}

function getStatusType(status: number) {
  const map: Record<number, string> = {
    0: 'warning',
    1: 'success',
    2: 'danger',
    3: 'warning',
  }
  return map[status] || 'info'
}

function getHotStatusLabel(status: number) {
  return status === 1 ? '显示中' : '已下架'
}

function getHotStatusType(status: number) {
  return status === 1 ? 'success' : 'info'
}

function getTargetTypeLabel(type: string | undefined | null) {
  const map: Record<string, string> = {
    news: '新闻热搜',
    news_topic: '新闻话题',
    community: '社区热搜',
    community_post: '社区帖子',
    keyword: '关键词',
  }
  return map[type || ''] || type || '未分类'
}

function getTargetTypeTag(type: string | undefined | null) {
  const source = (type || '').toLowerCase()
  if (source.startsWith('news')) return 'primary'
  if (source.startsWith('community')) return 'success'
  return 'info'
}

function truncateContent(content: string, maxLen: number = 80) {
  if (!content) return ''
  return content.length > maxLen ? content.slice(0, maxLen) + '...' : content
}

onMounted(() => {
  loadDashboard()
})
</script>

<template>
  <main class="admin-container">
    <template v-if="userStore.isEditorOrAdmin">
      <div class="admin-header">
        <div class="header-left">
          <h1>管理后台</h1>
          <p>欢迎回来，{{ userStore.userInfo?.nickname }}</p>
        </div>
        <div class="header-right">
          <el-tag :type="userStore.isAdmin ? 'danger' : 'warning'">
            {{ userStore.isAdmin ? '管理员' : '审核/编辑' }}
          </el-tag>
        </div>
      </div>

      <el-card class="stats-grid-card" shadow="never">
        <div class="stats-grid">
          <div
            v-for="(stat, index) in statsCards"
            :key="index"
            class="stat-card"
            :style="{ '--bg-color': stat.bgColor }"
          >
            <div class="stat-icon" :style="{ background: stat.bgColor, color: stat.iconColor }">
              <component :is="stat.icon" :size="24" />
            </div>
            <div class="stat-info">
              <span class="stat-value">{{ stat.value }}</span>
              <span class="stat-label">{{ stat.title }}</span>
            </div>
          </div>
        </div>
      </el-card>

      <el-card class="content-card" shadow="never">
        <el-tabs v-model="activeTab" @tab-change="handleTabChange" class="admin-tabs">
          <el-tab-pane
            v-for="tab in tabs"
            :key="tab.key"
            :label="tab.label"
            :name="tab.key"
            :disabled="(tab.key === 'users' || tab.key === 'config') && !userStore.isAdmin"
          >
            <template #label>
              <component :is="tab.icon" :size="18" class="tab-icon" />
              <span>{{ tab.label }}</span>
            </template>

            <div v-if="loading" class="loading-container">
              <el-spinner />
            </div>

            <!-- 概览 Tab -->
            <template v-else-if="activeTab === 'dashboard'">
              <div class="dashboard-content">
                <section class="feature-section">
                  <h2>编辑/审核功能</h2>
                  <div class="feature-grid">
                    <el-card
                      v-for="feature in editorFeatures"
                      :key="feature.key"
                      class="feature-card"
                      :class="{
                        'feature-card-available': feature.status === 'available',
                        'feature-card-coming': feature.status === 'coming-soon',
                      }"
                      shadow="hover"
                      @click="handleFeatureClick(feature)"
                    >
                      <component :is="feature.icon" :size="28" class="feature-icon" />
                      <div class="feature-info">
                        <div class="feature-title-row">
                          <h3>{{ feature.title }}</h3>
                          <el-tag
                            v-if="feature.status === 'coming-soon'"
                            size="small"
                            type="info"
                          >
                            待开发
                          </el-tag>
                        </div>
                        <p>{{ feature.description }}</p>
                      </div>
                    </el-card>
                  </div>
                </section>

                <section v-if="userStore.isAdmin" class="feature-section">
                  <h2>管理员功能</h2>
                  <div class="feature-grid admin-grid">
                    <el-card
                      v-for="feature in adminFeatures"
                      :key="feature.key"
                      class="feature-card"
                      :class="{
                        'feature-card-available': feature.status === 'available',
                        'feature-card-coming': feature.status === 'coming-soon',
                      }"
                      shadow="hover"
                      @click="handleFeatureClick(feature)"
                    >
                      <component :is="feature.icon" :size="28" class="feature-icon admin-icon" />
                      <div class="feature-info">
                        <div class="feature-title-row">
                          <h3>{{ feature.title }}</h3>
                          <el-tag
                            v-if="feature.status === 'coming-soon'"
                            size="small"
                            type="info"
                          >
                            待开发
                          </el-tag>
                        </div>
                        <p>{{ feature.description }}</p>
                      </div>
                    </el-card>
                  </div>
                </section>
              </div>
            </template>

            <!-- 帖子审核 Tab -->
            <template v-else-if="activeTab === 'pending'">
              <div v-if="pendingPosts.length === 0" class="empty-state">
                <p>暂无待审核内容</p>
              </div>
              <div v-else class="pending-list">
                <el-table :data="pendingPosts" border stripe>
                  <el-table-column prop="id" label="ID" width="70" />
                  <el-table-column prop="title" label="标题" min-width="180" show-overflow-tooltip />
                  <el-table-column label="内容摘要" min-width="200" show-overflow-tooltip>
                    <template #default="scope">
                      {{ truncateContent(scope.row.content, 100) }}
                    </template>
                  </el-table-column>
                  <el-table-column prop="username" label="作者" width="110" />
                  <el-table-column label="状态" width="90">
                    <template #default="scope">
                      <el-tag :type="getStatusType(scope.row.status)" size="small">
                        {{ getStatusLabel(scope.row.status) }}
                      </el-tag>
                    </template>
                  </el-table-column>
                  <el-table-column prop="create_time" label="提交时间" width="170" />
                  <el-table-column label="操作" width="220" fixed="right">
                    <template #default="scope">
                      <el-button
                        size="small"
                        type="success"
                        :loading="auditLoading[scope.row.id]"
                        @click="handleApprove(scope.row.id)"
                      >
                        通过
                      </el-button>
                      <el-button
                        size="small"
                        type="danger"
                        :loading="auditLoading[scope.row.id]"
                        @click="openRejectDialog(scope.row.id)"
                      >
                        驳回
                      </el-button>
                    </template>
                  </el-table-column>
                </el-table>
                <div v-if="pendingTotal > pendingPageSize" class="pagination-wrapper">
                  <el-pagination
                    v-model:current-page="pendingPage"
                    :page-size="pendingPageSize"
                    :total="pendingTotal"
                    layout="total, prev, pager, next"
                    @current-change="handlePendingPageChange"
                  />
                </div>
              </div>
            </template>

            <!-- 热搜管理 Tab -->
            <template v-else-if="activeTab === 'hot-topics'">
              <div class="hot-topics-header">
                <el-button type="primary" :icon="Plus" @click="openSimpleHotDialog()">
                  添加热搜关键词
                </el-button>
              </div>
              <div v-if="loading" class="empty-state">
                <p>加载中...</p>
              </div>
              <div v-else-if="simpleHotList.length === 0" class="empty-state">
                <p>暂无热搜关键词，点击添加</p>
              </div>
              <div v-else class="hot-topics-list">
                <el-table :data="simpleHotList" border stripe>
                  <el-table-column label="置顶" width="70" align="center">
                    <template #default="scope">
                      <el-button
                        :type="scope.row.is_pinned ? 'warning' : ''"
                        :icon="Top"
                        size="small"
                        circle
                        @click="handleTogglePin(scope.row)"
                      />
                    </template>
                  </el-table-column>
                  <el-table-column prop="keyword" label="关键词" min-width="180" show-overflow-tooltip />
                  <el-table-column prop="heat" label="热度值" width="100" sortable />
                  <el-table-column label="状态" width="100">
                    <template #default="scope">
                      <el-switch
                        :model-value="scope.row.status === 1"
                        active-text="显示"
                        inactive-text="下架"
                        @change="handleToggleStatus(scope.row)"
                      />
                    </template>
                  </el-table-column>
                  <el-table-column prop="create_time" label="创建时间" width="170" />
                  <el-table-column label="操作" width="180" fixed="right">
                    <template #default="scope">
                      <el-button size="small" type="primary" :icon="Edit" @click="openSimpleHotDialog(scope.row)">
                        编辑
                      </el-button>
                      <el-button size="small" type="danger" :icon="Delete" @click="handleDeleteSimpleHot(scope.row)">
                        删除
                      </el-button>
                    </template>
                  </el-table-column>
                </el-table>
                <div v-if="simpleHotTotal > simpleHotPageSize" class="pagination-wrapper">
                  <el-pagination
                    v-model:current-page="simpleHotPage"
                    :page-size="simpleHotPageSize"
                    :total="simpleHotTotal"
                    layout="total, prev, pager, next"
                    @current-change="handleSimpleHotPageChange"
                  />
                </div>
              </div>
            </template>

            <!-- 用户管理 Tab -->
            <template v-else-if="activeTab === 'users'">
              <div v-if="!userStore.isAdmin" class="unauthorized-section">
                <Lock :size="48" class="empty-icon" />
                <p>该功能仅管理员可访问</p>
              </div>
              <div v-else-if="users.length === 0" class="empty-state">
                <User :size="48" class="empty-icon" />
                <p>暂无用户数据</p>
              </div>
              <div v-else class="users-list">
                <el-table :data="users" border>
                  <el-table-column prop="id" label="ID" width="80" />
                  <el-table-column prop="username" label="用户名" width="120" />
                  <el-table-column prop="nickname" label="昵称" width="120" />
                  <el-table-column prop="role" label="角色" width="120">
                    <template #default="scope">
                      <el-tag :type="getRoleType(scope.row.role)">
                        {{ getRoleLabel(scope.row.role) }}
                      </el-tag>
                    </template>
                  </el-table-column>
                  <el-table-column prop="status" label="状态" width="100">
                    <template #default="scope">
                      <span :class="scope.row.status === 1 ? 'status-active' : 'status-inactive'">
                        {{ scope.row.status === 1 ? '正常' : '禁用' }}
                      </span>
                    </template>
                  </el-table-column>
                  <el-table-column label="操作" width="180">
                    <template #default>
                      <el-button size="small" type="primary">编辑</el-button>
                      <el-button size="small" type="danger">删除</el-button>
                    </template>
                  </el-table-column>
                </el-table>
              </div>
            </template>

            <!-- 系统配置 Tab -->
            <template v-else-if="activeTab === 'config'">
              <div v-if="!userStore.isAdmin" class="unauthorized-section">
                <Lock :size="48" class="empty-icon" />
                <p>该功能仅管理员可访问</p>
              </div>
              <div v-else-if="!systemConfig" class="loading-container">
                <el-spinner />
              </div>
              <div v-else class="config-form">
                <el-alert
                  type="info"
                  title="演示配置"
                  description="当前配置为后端默认演示值，暂未接入数据库配置表。正式环境建议读取数据库或配置文件。"
                  :closable="false"
                  style="margin-bottom: 24px"
                />
                <el-form label-width="160px">
                  <el-form-item label="站点名称">
                    <el-input :value="systemConfig.site_name" disabled />
                  </el-form-item>
                  <el-form-item label="站点描述">
                    <el-input :value="systemConfig.site_description" disabled />
                  </el-form-item>
                  <el-form-item label="最大上传大小(MB)">
                    <el-input :value="systemConfig.max_upload_size" disabled />
                  </el-form-item>
                  <el-form-item label="默认每页条数">
                    <el-input :value="systemConfig.default_page_size" disabled />
                  </el-form-item>
                  <el-form-item label="AI服务启用">
                    <el-switch
                      :model-value="systemConfig.ai_service_enabled === true"
                      disabled
                    />
                  </el-form-item>
                  <el-form-item label="自动审核启用">
                    <el-switch
                      :model-value="systemConfig.auto_approve_enabled === true"
                      disabled
                    />
                  </el-form-item>
                  <el-form-item>
                    <el-button type="primary">保存配置</el-button>
                  </el-form-item>
                </el-form>
              </div>
            </template>
          </el-tab-pane>
        </el-tabs>
      </el-card>

      <!-- 驳回理由对话框 -->
      <el-dialog v-model="rejectDialogVisible" title="驳回帖子" width="480px">
        <el-form>
          <el-form-item label="驳回理由（可选）">
            <el-input
              v-model="rejectReason"
              type="textarea"
              :rows="3"
              placeholder="填写驳回理由，帮助作者了解原因"
            />
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="rejectDialogVisible = false">取消</el-button>
          <el-button type="danger" @click="handleReject">确认驳回</el-button>
        </template>
      </el-dialog>

      <!-- 热搜关键词对话框（简化版） -->
      <el-dialog v-model="simpleHotDialogVisible" :title="simpleHotDialogTitle" width="480px">
        <el-form :model="simpleHotForm" label-width="100px">
          <el-form-item label="关键词" required>
            <el-input v-model="simpleHotForm.keyword" placeholder="如：AI人工智能" maxlength="100" />
          </el-form-item>
          <el-form-item label="热度值">
            <el-input-number v-model="simpleHotForm.heat" :min="0" :max="999999" />
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="simpleHotDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleSimpleHotSave">
            {{ editingSimpleHotId ? '保存修改' : '确认添加' }}
          </el-button>
        </template>
      </el-dialog>
    </template>

    <el-card v-else class="unauthorized-card" shadow="never">
      <el-result
        icon="warning"
        title="当前账号无权限访问"
        sub-title="该页面仅允许审核/编辑或管理员访问。"
      />
    </el-card>
  </main>
</template>

<style scoped>
.admin-container {
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
}

.admin-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.header-left h1 {
  margin: 0 0 8px;
  font-size: 24px;
}

.header-left p {
  margin: 0;
  color: var(--color-text-secondary);
}

.stats-grid-card {
  margin-bottom: 24px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
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
}

.stat-info {
  display: flex;
  flex-direction: column;
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.stat-label {
  font-size: 13px;
  color: var(--color-text-secondary);
}

.content-card {
  min-height: 500px;
}

.admin-tabs {
  min-height: 450px;
}

.tab-icon {
  margin-right: 8px;
}

.loading-container {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 300px;
}

.dashboard-content {
  padding: 16px;
}

.feature-section {
  margin-bottom: 24px;
}

.feature-section h2 {
  margin: 0 0 16px;
  font-size: 18px;
  font-weight: 600;
}

.feature-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.feature-grid.admin-grid {
  grid-template-columns: repeat(3, 1fr);
}

.feature-card {
  display: flex;
  align-items: center;
  gap: 16px;
  cursor: pointer;
  padding: 16px;
  transition: all 0.3s ease;
}

.feature-card-available {
  background: var(--color-bg-page);
  border: 1px solid var(--color-border-light);
}

.feature-card-available:hover {
  border-color: #409eff;
  box-shadow: 0 2px 12px rgba(64, 158, 255, 0.15);
}

.feature-card-coming {
  opacity: 0.6;
  background: var(--color-bg-page);
  border: 1px dashed var(--color-border-light);
}

.feature-card-coming:hover {
  opacity: 0.8;
}

.feature-icon {
  color: #409eff;
}

.feature-icon.admin-icon {
  color: #f56c6c;
}

.feature-info {
  display: flex;
  flex-direction: column;
  width: 100%;
}

.feature-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.feature-info h3 {
  margin: 0;
  font-size: 16px;
}

.feature-info p {
  margin: 0;
  font-size: 13px;
  color: var(--color-text-secondary);
}

.empty-state,
.unauthorized-section {
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

.empty-icon.success {
  color: #67c23a;
}

.pending-list,
.users-list,
.hot-topics-list {
  padding: 16px;
}

.pagination-wrapper {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}

.hot-topics-header {
  padding: 16px 16px 0;
  display: flex;
  justify-content: flex-end;
}

.hot-topics-header {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 16px;
}

.hot-topics-split {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  padding: 16px;
}

.hot-panel {
  border: 1px solid var(--color-border-light, #e4e7ed);
  border-radius: 8px;
  overflow: hidden;
}

.hot-panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: var(--color-bg-page, #f5f7fa);
  border-bottom: 1px solid var(--color-border-light, #e4e7ed);
}

.hot-panel-header h3 {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
}

.hot-panel-desc {
  font-size: 12px;
  color: var(--color-text-secondary, #909399);
}

.empty-state.small {
  padding: 40px 16px;
}

.empty-state.small p {
  font-size: 14px;
}

.rank-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 600;
}

.rank-badge.rank-top {
  background: #f56c6c;
  color: #fff;
}

.rank-badge.rank-normal {
  background: #f0f0f0;
  color: #909399;
}

.stat-inline {
  font-size: 12px;
  margin-right: 6px;
  color: var(--color-text-secondary, #909399);
}

.form-tip {
  margin-left: 8px;
  font-size: 12px;
  color: var(--color-text-secondary);
}

.text-muted {
  color: var(--color-text-placeholder);
}

.status-active {
  color: #67c23a;
}

.status-inactive {
  color: #909399;
}

.config-form {
  padding: 24px;
  max-width: 600px;
}

.unauthorized-card {
  max-width: 560px;
  margin: 48px auto;
}

@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .feature-grid,
  .feature-grid.admin-grid {
    grid-template-columns: 1fr;
  }

  .admin-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
}
</style>
