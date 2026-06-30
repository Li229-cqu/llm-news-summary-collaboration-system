<script setup lang="ts">
import { computed, nextTick, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  ArrowRight,
  ChatDotRound,
  Clock,
  Delete,
  Edit,
  Files,
  Grid,
  Key,
  MagicStick,
  Plus,
  Search,
  Setting,
  Star,
  SwitchButton,
  User,
  View,
  ZoomIn,
} from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  type AIRecordItem,
  type BrowseHistoryItem,
  type CommentRecordItem,
  type FavoriteItem,
  type ProfileOverview,
  type SubscriptionCategory,
  getAIRecords,
  getBrowseHistory,
  getComments,
  getFavorites,
  getProfileOverview,
  getSubscriptions,
  updateSubscriptions,
} from '@/api/profile'
import { unfavoriteNews } from '@/api/interaction'
import { unfavoritePost } from '@/api/community'
import { changePasswordApi, getUserProfileApi, updateUserProfileApi, uploadAvatarApi } from '@/api/user'
import { useUserStore } from '@/stores/user'
import ReadingTrajectory from '@/components/profile/ReadingTrajectory.vue'

const router = useRouter()
const userStore = useUserStore()

const activeTab = ref('history')
const loadingTab = ref('')

const browseType = ref<'news' | 'post'>('news')
const favoriteType = ref<'news' | 'post'>('news')
const commentType = ref<'news' | 'post'>('news')

const profileOverview = ref<ProfileOverview | null>(null)
const browseHistory = ref<BrowseHistoryItem[]>([])
const favorites = ref<FavoriteItem[]>([])
const comments = ref<CommentRecordItem[]>([])
const aiRecords = ref<AIRecordItem[]>([])
const subscriptions = ref<SubscriptionCategory[]>([])

const readingTags = computed(() => {
  const tags: string[] = []
  if ((profileOverview.value?.browse_count ?? 0) > 0) tags.push('新闻探索者')
  if ((profileOverview.value?.favorite_count ?? 0) > 0) tags.push('内容收藏者')
  if ((profileOverview.value?.comment_count ?? 0) > 0) tags.push('社区互动者')
  if ((profileOverview.value?.ai_generate_count ?? 0) > 0) tags.push('AI 摘要使用者')
  if (tags.length === 0) tags.push('新用户')
  return tags
})

const statCards = [
  { key: 'history', icon: Clock, label: '浏览历史', count: () => profileOverview.value?.browse_count ?? 0, desc: '新闻与帖子浏览足迹' },
  { key: 'favorites', icon: Star, label: '收藏记录', count: () => profileOverview.value?.favorite_count ?? 0, desc: '保存的新闻与社区帖子' },
  { key: 'comments', icon: ChatDotRound, label: '评论记录', count: () => profileOverview.value?.comment_count ?? 0, desc: '你的新闻与社区互动' },
  { key: 'ai-records', icon: MagicStick, label: 'AI生成记录', count: () => profileOverview.value?.ai_generate_count ?? 0, desc: '标题摘要生成历史' },
]

const browseSearchKeyword = ref('')
const favoriteSearchKeyword = ref('')
const commentSearchKeyword = ref('')
const aiSearchKeyword = ref('')
const currentPage = ref(1)
const pageSize = 10
const totalCount = ref(0)

const editDialogVisible = ref(false)
const activeEditTab = ref<'profile' | 'password'>('profile')
const editLoading = ref(false)
const editForm = reactive({
  nickname: '',
  email: '',
  phone: '',
  avatar: '',
})

// accountDialog removed — merged into editDialog
const passwordForm = reactive({
  old_password: '',
  new_password: '',
  confirm_password: '',
})
const passwordLoading = ref(false)

const aiDetailVisible = ref(false)
const currentAIRecord = ref<AIRecordItem | null>(null)

const categoryIcons: Record<string, string> = {
  technology: '💻',
  finance: '💰',
  sports: '⚽',
  entertainment: '🎬',
  health: '🏥',
  education: '📚',
  travel: '✈️',
  food: '🍔',
  science: '🔬',
  military: '🎖️',
  history: '📜',
  culture: '🎭',
  auto: '🚗',
  game: '🎮',
  fashion: '👗',
  social: '👥',
}

const categoryDescs: Record<string, string> = {
  technology: '科技前沿、互联网动态、数码产品',
  finance: '财经资讯、股市行情、投资理财',
  sports: '体育赛事、运动健身、足球篮球',
  entertainment: '娱乐八卦、影视音乐、明星动态',
  health: '健康养生、医疗资讯、心理健康',
  education: '教育资讯、学习方法、考试信息',
  travel: '旅游攻略、景点推荐、出行指南',
  food: '美食菜谱、餐饮推荐、健康饮食',
  science: '科学探索、研究发现、科普知识',
  military: '军事新闻、国防建设、武器装备',
  history: '历史故事、人物传记、文化遗产',
  culture: '文化艺术、文学作品、传统习俗',
  auto: '汽车资讯、新车发布、用车指南',
  game: '游戏资讯、电竞比赛、攻略评测',
  fashion: '时尚潮流、穿搭指南、美妆护肤',
  social: '社会热点、民生关注、公益活动',
}

const tabs = [
  { key: 'history', label: '浏览历史', icon: Clock },
  { key: 'favorites', label: '收藏记录', icon: Star },
  { key: 'comments', label: '评论记录', icon: ChatDotRound },
  { key: 'ai-records', label: 'AI 生成记录', icon: MagicStick },
  { key: 'trajectory', label: '阅读脉络', icon: View },
]

const filteredBrowseHistory = computed(() => {
  if (!browseSearchKeyword.value) return browseHistory.value
  const query = browseSearchKeyword.value.toLowerCase()
  return browseHistory.value.filter((item) =>
    item.title.toLowerCase().includes(query) ||
    (item as any).summary?.toLowerCase().includes(query) ||
    (item as any).source?.toLowerCase().includes(query) ||
    (item as any).category_name?.toLowerCase().includes(query)
  )
})

const filteredFavorites = computed(() => {
  if (!favoriteSearchKeyword.value) return favorites.value
  const query = favoriteSearchKeyword.value.toLowerCase()
  return favorites.value.filter(
    (item) =>
      item.title.toLowerCase().includes(query) ||
      item.summary.toLowerCase().includes(query) ||
      item.source.toLowerCase().includes(query)
  )
})

const filteredComments = computed(() => {
  if (!commentSearchKeyword.value) return comments.value
  const query = commentSearchKeyword.value.toLowerCase()
  return comments.value.filter(
    (item) =>
      item.content.toLowerCase().includes(query) ||
      item.news_title.toLowerCase().includes(query) ||
      (item.target_title || '').toLowerCase().includes(query)
  )
})

const filteredAIRecords = computed(() => {
  if (!aiSearchKeyword.value) return aiRecords.value
  const query = aiSearchKeyword.value.toLowerCase()
  return aiRecords.value.filter(
    (item) =>
      item.input_text.toLowerCase().includes(query) ||
      item.source_title.toLowerCase().includes(query) ||
      item.summary_short.toLowerCase().includes(query) ||
      (item.summary_long && item.summary_long.toLowerCase().includes(query)) ||
      item.candidate_titles.some((t) => t.toLowerCase().includes(query))
  )
})

function goToNewsDetail(newsId: number) {
  router.push(`/news/${newsId}`)
}

function handleBrowseItemClick(item: BrowseHistoryItem) {
  if (item.type === 'post') {
    router.push('/community')
    return
  }
  router.push(`/news/${item.news_id}`)
}

function handleCommentItemClick(item: CommentRecordItem) {
  if (item.type === 'post') {
    router.push('/community')
    return
  }
  router.push(`/news/${item.news_id}`)
}

function handleFavoriteClick(item: FavoriteItem) {
  if (item.target_type === 'post') {
    ElMessage.info('帖子详情页暂未开放')
    return
  }
  router.push(`/news/${item.news_id}`)
}

function clearBrowseSearch() {
  browseSearchKeyword.value = ''
  currentPage.value = 1
}

function clearFavoriteSearch() {
  favoriteSearchKeyword.value = ''
  currentPage.value = 1
}

function clearCommentSearch() {
  commentSearchKeyword.value = ''
  currentPage.value = 1
}

function clearAISearch() {
  aiSearchKeyword.value = ''
  currentPage.value = 1
}

async function openEditDialog(tab: 'profile' | 'password' = 'profile') {
  activeEditTab.value = tab
  await loadCurrentUserProfile()
  editForm.nickname = userStore.userInfo?.nickname || ''
  editForm.email = (userStore.userInfo as any)?.email || ''
  editForm.phone = (userStore.userInfo as any)?.phone || ''
  editForm.avatar = userStore.userInfo?.avatar || ''
  passwordForm.old_password = ''
  passwordForm.new_password = ''
  passwordForm.confirm_password = ''
  editDialogVisible.value = true
}

function openAccountDialog() {
  openEditDialog('password')
}


async function handleChangePassword() {
  if (!passwordForm.old_password) {
    ElMessage.warning('请输入原密码')
    return
  }
  if (!passwordForm.new_password) {
    ElMessage.warning('请输入新密码')
    return
  }
  if (passwordForm.new_password.length < 6) {
    ElMessage.warning('新密码长度不能少于6位')
    return
  }
  if (passwordForm.new_password !== passwordForm.confirm_password) {
    ElMessage.warning('两次输入的新密码不一致')
    return
  }
  passwordLoading.value = true
  try {
    await changePasswordApi({
      old_password: passwordForm.old_password,
      new_password: passwordForm.new_password,
      confirm_password: passwordForm.confirm_password,
    })
    ElMessage.success('密码修改成功，请重新登录')
    // 清空密码表单，但不清空资料表单
    passwordForm.old_password = ''
    passwordForm.new_password = ''
    passwordForm.confirm_password = ''
    editDialogVisible.value = false
    setTimeout(() => {
      userStore.logout()
      router.push('/login')
    }, 1000)
  } catch (error: any) {
    console.error('修改密码失败:', error)
    const errorMsg = error?.response?.data?.message || error?.message || '修改密码失败，请重试'
    ElMessage.error(errorMsg)
  } finally {
    passwordLoading.value = false
  }
}

async function loadCurrentUserProfile() {
  try {
    const profile = await getUserProfileApi()
    if (userStore.userInfo) {
      userStore.userInfo.nickname = profile.nickname
      userStore.userInfo.email = profile.email
      userStore.userInfo.phone = profile.phone
      userStore.userInfo.avatar = profile.avatar
      userStore.setUserInfo(userStore.userInfo)
    }
  } catch (error) {
    console.error('加载用户资料失败:', error)
  }
}

async function handleAvatarChange(file: File) {
  const ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
  const isLt2M = file.size / 1024 / 1024 < 2

  if (!ALLOWED_TYPES.includes(file.type)) {
    ElMessage.error('仅支持 jpg/png/gif/webp 格式图片')
    return false
  }
  if (!isLt2M) {
    ElMessage.error('图片大小不能超过 2MB')
    return false
  }

  try {
    const result = await uploadAvatarApi(file)
    const avatarUrl = result.avatar_url || result.avatar
    editForm.avatar = avatarUrl
    if (userStore.userInfo) {
      userStore.userInfo.avatar = avatarUrl
      userStore.setUserInfo(userStore.userInfo)
    }
    ElMessage.success('头像上传成功')
  } catch (error) {
    const message = error instanceof Error ? error.message : '头像上传失败'
    ElMessage.error(message)
  }
  return false
}

async function handleEditSubmit() {
  if (!editForm.nickname.trim()) {
    ElMessage.warning('昵称不能为空')
    return
  }

  if (editForm.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(editForm.email)) {
    ElMessage.warning('请输入有效的邮箱地址')
    return
  }

  if (editForm.phone && !/^1[3-9]\d{9}$/.test(editForm.phone)) {
    ElMessage.warning('请输入有效的手机号码')
    return
  }

  const avatar = editForm.avatar || ''
  const isValidAvatar = avatar && !avatar.startsWith('data:image/') && !avatar.includes(';base64,') && avatar.length <= 255

  const payload: Record<string, string> = {
    nickname: editForm.nickname.trim(),
    email: editForm.email.trim() || '',
    phone: editForm.phone.trim() || '',
  }
  if (isValidAvatar) {
    payload.avatar = avatar
  }

  editLoading.value = true
  try {
    const result = await updateUserProfileApi(payload)

    if (userStore.userInfo) {
      userStore.userInfo.nickname = result.nickname
      ;(userStore.userInfo as any).email = result.email ?? ''
      ;(userStore.userInfo as any).phone = result.phone ?? ''
      userStore.userInfo.avatar = result.avatar || ''
      userStore.setUserInfo(userStore.userInfo)
    }

    ElMessage.success('资料保存成功')

    // 重新加载完整用户资料以确保最新
    await loadCurrentUserProfile()

    editDialogVisible.value = false
  } catch (error) {
    const message = error instanceof Error ? error.message : '资料保存失败'
    ElMessage.error(message)
  } finally {
    editLoading.value = false
  }
}

function openAIRecordDetail(record: AIRecordItem) {
  currentAIRecord.value = record
  aiDetailVisible.value = true
}

async function handleRemoveFavorite(item: FavoriteItem, event: Event) {
  event.stopPropagation()
  try {
    await ElMessageBox.confirm(`确定要取消收藏《${item.title}》吗？`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
    if (item.target_type === 'post') {
      await unfavoritePost(item.news_id)
    } else {
      await unfavoriteNews(item.news_id)
    }
    favorites.value = favorites.value.filter((f) => f.news_id !== item.news_id)
    totalCount.value--
    if (profileOverview.value) {
      profileOverview.value.favorite_count--
    }
    ElMessage.success('已取消收藏')
  } catch {
  }
}

function handleRemoveHistory(item: BrowseHistoryItem, event: Event) {
  event.stopPropagation()
  ElMessageBox.confirm(`确定要删除这条浏览记录吗？`, '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning',
  })
    .then(() => {
      browseHistory.value = browseHistory.value.filter(
        (h) => !(h.news_id === item.news_id && h.browse_time === item.browse_time)
      )
      totalCount.value--
      if (profileOverview.value) {
        profileOverview.value.browse_count--
      }
      ElMessage.success('删除成功')
    })
    .catch(() => {})
}

function getCategoryIcon(code: string) {
  return categoryIcons[code] || '📰'
}

function getCategoryDesc(code: string) {
  return categoryDescs[code] || '精彩新闻内容'
}

function normalizeAvatarUrl(url?: string): string {
  if (!url) return ''
  if (url.startsWith('http://') || url.startsWith('https://') || url.startsWith('data:image/')) {
    return url
  }
  if (url.startsWith('/uploads/')) {
    const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'
    return baseURL.replace(/\/$/, '') + url
  }
  return url
}

async function loadBrowseHistory(page = 1) {
  loadingTab.value = 'history'
  try {
    const result = await getBrowseHistory(page, pageSize, browseType.value)
    browseHistory.value = result.list
    totalCount.value = result.total
    currentPage.value = page
  } catch (error) {
    console.error(error)
    ElMessage.error('加载浏览历史失败，请稍后重试')
  } finally {
    loadingTab.value = ''
  }
}

async function loadFavorites(page = 1) {
  loadingTab.value = 'favorites'
  try {
    const result = await getFavorites(page, pageSize, favoriteType.value)
    favorites.value = result.list
    totalCount.value = result.total
    currentPage.value = page
  } catch (error) {
    console.error(error)
    ElMessage.error('加载收藏记录失败，请稍后重试')
  } finally {
    loadingTab.value = ''
  }
}

async function loadComments(page = 1) {
  loadingTab.value = 'comments'
  try {
    const result = await getComments(page, pageSize, commentType.value)
    comments.value = result.list
    totalCount.value = result.total
    currentPage.value = page
  } catch (error) {
    console.error(error)
    ElMessage.error('加载评论记录失败，请稍后重试')
  } finally {
    loadingTab.value = ''
  }
}

async function loadAIRecords(page = 1) {
  loadingTab.value = 'ai-records'
  try {
    const result = await getAIRecords(page, pageSize)
    aiRecords.value = result.list
    totalCount.value = result.total
    currentPage.value = page
  } catch (error) {
    console.error(error)
    ElMessage.error('加载 AI 生成记录失败，请稍后重试')
  } finally {
    loadingTab.value = ''
  }
}


function handlePageChange(page: number) {
  if (activeTab.value === 'history') {
    loadBrowseHistory(page)
  } else if (activeTab.value === 'favorites') {
    loadFavorites(page)
  } else if (activeTab.value === 'comments') {
    loadComments(page)
  } else if (activeTab.value === 'ai-records') {
    loadAIRecords(page)
  }
}

function handleTabChange(key: string) {
  activeTab.value = key
  browseSearchKeyword.value = ''
  favoriteSearchKeyword.value = ''
  commentSearchKeyword.value = ''
  aiSearchKeyword.value = ''
  currentPage.value = 1
  if (key === 'history') {
    loadBrowseHistory()
  } else if (key === 'favorites') {
    loadFavorites()
  } else if (key === 'comments') {
    loadComments()
  } else if (key === 'ai-records') {
    loadAIRecords()
  }
}

function handleClearHistory() {
  ElMessageBox.confirm('确定要清空所有浏览历史吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning',
  })
    .then(() => {
      browseHistory.value = []
      totalCount.value = 0
      ElMessage.success('浏览历史已清空')
    })
    .catch(() => {})
}

async function handleStatCardClick(targetTab: string) {
  activeTab.value = targetTab
  browseSearchKeyword.value = ''
  favoriteSearchKeyword.value = ''
  commentSearchKeyword.value = ''
  aiSearchKeyword.value = ''
  currentPage.value = 1
  await nextTick()
  if (targetTab === 'history') {
    loadBrowseHistory()
  } else if (targetTab === 'favorites') {
    loadFavorites()
  } else if (targetTab === 'comments') {
    loadComments()
  } else if (targetTab === 'ai-records') {
    loadAIRecords()
  }
}

function getVisiblePages(current: number, total: number): (number | string)[] {
  if (total <= 7) {
    return Array.from({ length: total }, (_, i) => i + 1)
  }
  const pages: (number | string)[] = [1]
  const start = Math.max(2, current - 2)
  const end = Math.min(total - 1, current + 2)

  if (start > 2) {
    pages.push('...')
  }
  for (let i = start; i <= end; i++) {
    pages.push(i)
  }
  if (end < total - 1) {
    pages.push('...')
  }
  pages.push(total)
  return pages
}

onMounted(async () => {
  await loadCurrentUserProfile()
  // Load overview stats for quick stats display in header (not for overview tab)
  try {
    profileOverview.value = await getProfileOverview()
  } catch (error) {
    console.error('加载概览统计失败:', error)
  }
  // Auto-load default tab data so browse history shows immediately
  if (activeTab.value === 'history') {
    await loadBrowseHistory()
  }
})
</script>

<template>
  <main class="page-container">
    <!-- ===== 顶部个人名片横幅 ===== -->
    <div class="dashboard-hero">
      <div class="hero-bg"></div>
      <div class="hero-content">
        <div class="hero-left">
          <div class="hero-avatar-col">
            <div class="avatar-wrapper">
              <el-avatar :size="88" :src="normalizeAvatarUrl(userStore.userInfo?.avatar)" :icon="User" class="user-avatar">
                {{ userStore.userInfo?.nickname?.charAt(0) || '用' }}
              </el-avatar>
            </div>
          </div>
          <div class="hero-info-col">
            <div class="hero-name-row">
              <h1 class="hero-name">{{ userStore.userInfo?.nickname || '未登录用户' }}</h1>
              <el-tag :type="userStore.isAdmin ? 'danger' : userStore.isEditor ? 'warning' : 'info'" effect="dark" round size="default">
                {{ userStore.isAdmin ? '管理员' : userStore.isEditor ? '审核/编辑' : '普通用户' }}
              </el-tag>
            </div>
            <div class="hero-meta-row">
              <span class="hero-meta-item">
                <el-icon><User /></el-icon>
                <span>ID: {{ userStore.userInfo?.id || '-' }}</span>
              </span>
              <span v-if="(userStore.userInfo as any)?.email" class="hero-meta-item">
                <el-icon><Message /></el-icon>
                <span>{{ (userStore.userInfo as any)?.email }}</span>
              </span>
            </div>
            <div class="hero-tags-row">
              <el-tag
                v-for="tag in readingTags"
                :key="tag"
                size="small"
                effect="plain"
                class="hero-reading-tag"
                :type="tag === '新用户' ? 'info' : ''"
              >
                {{ tag }}
              </el-tag>
            </div>
            <p class="hero-desc">欢迎回来，继续探索你的新闻阅读足迹</p>
          </div>
        </div>
        <div class="hero-right">
          <el-button class="hero-edit-btn" :icon="Edit" @click="openEditDialog()">
            编辑资料
          </el-button>
        </div>
      </div>

      <!-- ===== 数据概览卡片 ===== -->
      <div class="dashboard-stats">
        <div
          v-for="card in statCards"
          :key="card.key"
          class="dash-stat-card"
          :class="{ 'dash-stat-card--active': activeTab === card.key }"
          @click="handleStatCardClick(card.key)"
        >
          <div class="dash-stat-card__icon">
            <el-icon :size="24"><component :is="card.icon" /></el-icon>
          </div>
          <div class="dash-stat-card__body">
            <span class="dash-stat-card__count">{{ card.count() }}</span>
            <span class="dash-stat-card__label">{{ card.label }}</span>
            <span class="dash-stat-card__desc">{{ card.desc }}</span>
          </div>
          <div class="dash-stat-card__hint">点击查看 →</div>
        </div>
      </div>
    </div>

    <!-- ===== 阅读画像占位区 ===== -->
    <div class="reading-portrait-placeholder">
      <div class="portrait-header">
        <h2 class="portrait-title">
          <el-icon><Grid /></el-icon>
          阅读画像
        </h2>
        <p class="portrait-subtitle">基于你的浏览、收藏、评论和 AI 生成记录，展示你的阅读趋势与兴趣分布</p>
      </div>
      <div class="portrait-skeletons">
        <div class="portrait-skeleton-card">
          <div class="skeleton-icon-wrapper">
            <el-icon :size="32"><Files /></el-icon>
          </div>
          <span class="skeleton-label">最近 7 天阅读趋势</span>
          <span class="skeleton-hint">将在下一阶段接入阅读时间线数据</span>
        </div>
        <div class="portrait-skeleton-card">
          <div class="skeleton-icon-wrapper">
            <el-icon :size="32"><Grid /></el-icon>
          </div>
          <span class="skeleton-label">兴趣分类分布</span>
          <span class="skeleton-hint">将在下一阶段展示常读分类</span>
        </div>
        <div class="portrait-skeleton-card">
          <div class="skeleton-icon-wrapper">
            <el-icon :size="32"><Setting /></el-icon>
          </div>
          <span class="skeleton-label">我的订阅</span>
          <span class="skeleton-hint">将在后续展示订阅分类</span>
        </div>
        <div class="portrait-skeleton-card">
          <div class="skeleton-icon-wrapper">
            <el-icon :size="32"><MagicStick /></el-icon>
          </div>
          <span class="skeleton-label">AI 使用概览</span>
          <span class="skeleton-hint">将在后续展示 AI 生成偏好</span>
        </div>
      </div>
    </div>

    <!-- ===== 内容记录 Tab 区域 ===== -->
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

          <template v-else-if="tab.key === 'history'">
            <div class="tab-toolbar">
              <div class="search-bar-wrapper">
                <el-radio-group v-model="browseType" size="small" class="segmented-control" @change="browseSearchKeyword = ''; currentPage = 1; browseHistory = []; totalCount = 0; loadBrowseHistory()">
                  <el-radio-button value="news">新闻</el-radio-button>
                  <el-radio-button value="post">帖子</el-radio-button>
                </el-radio-group>
                <el-input
                  v-model="browseSearchKeyword"
                  placeholder="搜索浏览历史..."
                  :prefix-icon="Search"
                  class="search-input"
                  @keyup.enter="currentPage = 1"
                />
                <el-button type="primary" @click="currentPage = 1">搜索</el-button>
                <el-button @click="clearBrowseSearch">清空</el-button>
              </div>
              <el-button type="danger" plain :disabled="browseHistory.length === 0" @click="handleClearHistory">
                清空历史
              </el-button>
            </div>

            <div v-if="browseType === 'post' && browseHistory.length === 0" class="empty-state compact-empty">
              <p class="empty-text">暂无帖子浏览记录</p>
              <p class="empty-desc">浏览社区帖子后将在这里显示</p>
            </div>
            <div v-else-if="browseHistory.length === 0" class="empty-state compact-empty">
              <p class="empty-text">暂无浏览历史</p>
              <p class="empty-desc">去首页看看精彩新闻吧</p>
              <el-button type="primary" @click="router.push('/')">返回首页</el-button>
            </div>
            <div v-else-if="filteredBrowseHistory.length === 0" class="empty-state compact-empty">
              <p class="empty-text">未找到匹配的浏览记录</p>
              <p class="empty-desc">请尝试其他关键词</p>
            </div>
            <div v-else class="record-list">
              <div
                v-for="item in filteredBrowseHistory"
                :key="`${item.news_id}-${item.browse_time}`"
                class="record-item"
                @click="handleBrowseItemClick(item)"
              >
                <div class="record-main">
                  <el-tag size="small" class="record-tag">{{ item.type === 'post' ? '帖子浏览' : item.category_name }}</el-tag>
                  <h3 class="record-title">{{ item.target_title || item.title }}</h3>
                </div>
                <div class="record-meta">
                  <span>{{ item.browse_time }}</span>
                </div>
                <div class="record-actions">
                  <el-button
                    type="danger"
                    text
                    :icon="Delete"
                    size="small"
                    class="delete-btn"
                    @click="handleRemoveHistory(item, $event)"
                  >
                    删除
                  </el-button>
                  <ArrowRight :size="18" class="record-arrow" />
                </div>
              </div>
            </div>

            <div v-if="totalCount > pageSize && filteredBrowseHistory.length > 0" class="profile-pagination">
              <button class="page-btn" :disabled="currentPage <= 1" @click="handlePageChange(1)" title="首页">&lt;&lt;</button>
              <button class="page-btn" :disabled="currentPage <= 1" @click="handlePageChange(currentPage - 1)" title="上一页">&lt;</button>
              <template v-for="item in getVisiblePages(currentPage, Math.ceil(totalCount / pageSize))" :key="item">
                <span v-if="item === '...'" class="page-ellipsis">...</span>
                <button v-else class="page-btn" :class="{ active: item === currentPage }" @click="handlePageChange(Number(item))">{{ item }}</button>
              </template>
              <button class="page-btn" :disabled="currentPage >= Math.ceil(totalCount / pageSize)" @click="handlePageChange(currentPage + 1)" title="下一页">&gt;</button>
              <button class="page-btn" :disabled="currentPage >= Math.ceil(totalCount / pageSize)" @click="handlePageChange(Math.ceil(totalCount / pageSize))" title="尾页">&gt;&gt;</button>
            </div>
          </template>

          <template v-else-if="tab.key === 'favorites'">
            <div class="tab-toolbar">
              <div class="search-bar-wrapper">
                <el-radio-group v-model="favoriteType" size="small" class="segmented-control" @change="favoriteSearchKeyword = ''; currentPage = 1; favorites = []; totalCount = 0; loadFavorites()">
                  <el-radio-button value="news">新闻</el-radio-button>
                  <el-radio-button value="post">帖子</el-radio-button>
                </el-radio-group>
                <el-input
                  v-model="favoriteSearchKeyword"
                  placeholder="搜索收藏内容..."
                  :prefix-icon="Search"
                  class="search-input"
                  @keyup.enter="currentPage = 1"
                />
                <el-button type="primary" @click="currentPage = 1">搜索</el-button>
                <el-button @click="clearFavoriteSearch">清空</el-button>
              </div>
            </div>

            <div v-if="favorites.length === 0" class="empty-state compact-empty">
              <p class="empty-text">{{ favoriteType === 'news' ? '暂无新闻收藏记录' : '暂无帖子收藏记录' }}</p>
              <p class="empty-desc">看到喜欢的就收藏起来吧</p>
            </div>
            <div v-else-if="filteredFavorites.length === 0" class="empty-state compact-empty">
              <p class="empty-text">未找到匹配的收藏记录</p>
              <p class="empty-desc">请尝试其他关键词</p>
            </div>
            <div v-else class="record-list">
              <div
                v-for="item in filteredFavorites"
                :key="item.news_id"
                class="record-item record-item-detailed"
                @click="handleFavoriteClick(item)"
              >
                <div class="record-main">
                  <div class="record-header-row">
                    <el-tag size="small" class="record-tag">{{ item.category_name }}</el-tag>
                    <el-button
                      type="danger"
                      text
                      :icon="Star"
                      size="small"
                      class="favorite-remove-btn"
                      @click="handleRemoveFavorite(item, $event)"
                    >
                      取消收藏
                    </el-button>
                  </div>
                  <h3 class="record-title">{{ item.title }}</h3>
                  <p class="record-summary">{{ item.summary }}</p>
                </div>
                <div class="record-meta">
                  <span class="record-source">{{ item.source }}</span>
                  <span>收藏于 {{ item.favorited_at || item.publish_time }}</span>
                </div>
              </div>
            </div>

            <div v-if="totalCount > pageSize && filteredFavorites.length > 0" class="profile-pagination">
              <button class="page-btn" :disabled="currentPage <= 1" @click="handlePageChange(1)" title="首页">&lt;&lt;</button>
              <button class="page-btn" :disabled="currentPage <= 1" @click="handlePageChange(currentPage - 1)" title="上一页">&lt;</button>
              <template v-for="item in getVisiblePages(currentPage, Math.ceil(totalCount / pageSize))" :key="item">
                <span v-if="item === '...'" class="page-ellipsis">...</span>
                <button v-else class="page-btn" :class="{ active: item === currentPage }" @click="handlePageChange(Number(item))">{{ item }}</button>
              </template>
              <button class="page-btn" :disabled="currentPage >= Math.ceil(totalCount / pageSize)" @click="handlePageChange(currentPage + 1)" title="下一页">&gt;</button>
              <button class="page-btn" :disabled="currentPage >= Math.ceil(totalCount / pageSize)" @click="handlePageChange(Math.ceil(totalCount / pageSize))" title="尾页">&gt;&gt;</button>
            </div>
          </template>

          <template v-else-if="tab.key === 'comments'">
            <div class="tab-toolbar">
              <div class="search-bar-wrapper">
                <el-radio-group v-model="commentType" size="small" class="segmented-control" @change="commentSearchKeyword = ''; currentPage = 1; comments = []; totalCount = 0; loadComments()">
                  <el-radio-button value="news">新闻评论</el-radio-button>
                  <el-radio-button value="post">帖子评论</el-radio-button>
                </el-radio-group>
                <el-input
                  v-model="commentSearchKeyword"
                  placeholder="搜索评论内容..."
                  :prefix-icon="Search"
                  class="search-input"
                  @keyup.enter="currentPage = 1"
                />
                <el-button type="primary" @click="currentPage = 1">搜索</el-button>
                <el-button @click="clearCommentSearch">清空</el-button>
              </div>
            </div>

            <div v-if="comments.length === 0" class="empty-state compact-empty">
              <p class="empty-text">{{ commentType === 'news' ? '暂无新闻评论记录' : '暂无帖子评论记录' }}</p>
              <p class="empty-desc">{{ commentType === 'news' ? '去新闻详情页发表你的看法吧' : '去社区帖子中发表你的看法吧' }}</p>
            </div>
            <div v-else-if="filteredComments.length === 0" class="empty-state compact-empty">
              <p class="empty-text">未找到匹配的评论记录</p>
              <p class="empty-desc">请尝试其他关键词</p>
            </div>
            <div v-else class="record-list">
              <div
                v-for="item in filteredComments"
                :key="item.comment_id"
                class="record-item record-item-detailed"
              >
                <div class="record-main">
                  <div class="record-header-row">
                    <el-tag size="small" class="record-tag">{{ item.type === 'post' ? '帖子评论' : item.category_name }}</el-tag>
                  </div>
                  <h3
                    class="record-title link-title"
                    @click="handleCommentItemClick(item)"
                  >
                    {{ item.type === 'post' ? item.target_title : item.news_title }}
                  </h3>
                  <div class="comment-box">
                    <p class="comment-content">{{ item.content }}</p>
                  </div>
                </div>
                <div class="record-meta">
                  <span>{{ item.create_time }}</span>
                  <span class="like-count">
                    <Star :size="14" />
                    {{ item.like_count }}
                  </span>
                </div>
              </div>
            </div>

            <div v-if="totalCount > pageSize && filteredComments.length > 0" class="profile-pagination">
              <button class="page-btn" :disabled="currentPage <= 1" @click="handlePageChange(1)" title="首页">&lt;&lt;</button>
              <button class="page-btn" :disabled="currentPage <= 1" @click="handlePageChange(currentPage - 1)" title="上一页">&lt;</button>
              <template v-for="item in getVisiblePages(currentPage, Math.ceil(totalCount / pageSize))" :key="item">
                <span v-if="item === '...'" class="page-ellipsis">...</span>
                <button v-else class="page-btn" :class="{ active: item === currentPage }" @click="handlePageChange(Number(item))">{{ item }}</button>
              </template>
              <button class="page-btn" :disabled="currentPage >= Math.ceil(totalCount / pageSize)" @click="handlePageChange(currentPage + 1)" title="下一页">&gt;</button>
              <button class="page-btn" :disabled="currentPage >= Math.ceil(totalCount / pageSize)" @click="handlePageChange(Math.ceil(totalCount / pageSize))" title="尾页">&gt;&gt;</button>
            </div>
          </template>

          <template v-else-if="tab.key === 'ai-records'">
            <div class="tab-toolbar">
              <div class="search-bar-wrapper">
                <el-input
                  v-model="aiSearchKeyword"
                  placeholder="搜索 AI 记录..."
                  :prefix-icon="Search"
                  class="search-input"
                  @keyup.enter="currentPage = 1"
                />
                <el-button type="primary" @click="currentPage = 1">搜索</el-button>
                <el-button @click="clearAISearch">清空</el-button>
              </div>
            </div>

            <div v-if="aiRecords.length === 0" class="empty-state compact-empty">
              <p class="empty-text">暂无 AI 生成记录</p>
              <p class="empty-desc">去体验 AI 智能摘要功能吧</p>
              <el-button type="primary" @click="router.push('/ai/title-summary')">去生成</el-button>
            </div>
            <div v-else-if="filteredAIRecords.length === 0" class="empty-state compact-empty">
              <p class="empty-text">未找到匹配的 AI 记录</p>
              <p class="empty-desc">请尝试其他关键词</p>
            </div>
            <div v-else class="record-list">
              <div v-for="item in filteredAIRecords" :key="item.id" class="ai-record-item">
                <div class="ai-record-header">
                  <div class="ai-record-title-row">
                    <el-tag type="warning" size="small" effect="dark">AI 记录</el-tag>
                    <span class="ai-record-title">{{ item.source_title || `记录 #${item.id}` }}</span>
                  </div>
                  <div class="ai-record-header-actions">
                    <el-tag
                      :type="item.risk_level === 'high' ? 'danger' : item.risk_level === 'medium' ? 'warning' : 'success'"
                      size="small"
                    >
                      {{ item.risk_level === 'high' ? '高风险' : item.risk_level === 'medium' ? '中风险' : '低风险' }}
                    </el-tag>
                    <el-button type="primary" text :icon="ZoomIn" size="small" @click="openAIRecordDetail(item)">
                      查看详情
                    </el-button>
                  </div>
                </div>

                <div class="ai-record-section">
                  <span class="section-label">输入文本</span>
                  <p class="section-content line-clamp-2">{{ item.input_text }}</p>
                </div>

                <div class="ai-record-section">
                  <span class="section-label">候选标题</span>
                  <div class="title-tags">
                    <el-tag v-for="(title, index) in item.candidate_titles.slice(0, 3)" :key="index" size="small" type="info">
                      {{ title }}
                    </el-tag>
                    <el-tag v-if="item.candidate_titles.length > 3" size="small">
                      +{{ item.candidate_titles.length - 3 }}
                    </el-tag>
                  </div>
                </div>

                <div class="ai-record-section">
                  <span class="section-label">生成摘要</span>
                  <p class="section-content line-clamp-3">{{ item.summary_short }}</p>
                </div>

                <div class="ai-record-footer">
                  <span class="source-tag">{{ item.source === 'news' ? '新闻导入' : '手动输入' }}</span>
                  <span class="record-time">
                    {{ item.create_time || '暂无时间' }}
                  </span>
                </div>
              </div>
            </div>

            <div v-if="totalCount > pageSize && filteredAIRecords.length > 0" class="profile-pagination">
              <button class="page-btn" :disabled="currentPage <= 1" @click="handlePageChange(1)" title="首页">&lt;&lt;</button>
              <button class="page-btn" :disabled="currentPage <= 1" @click="handlePageChange(currentPage - 1)" title="上一页">&lt;</button>
              <template v-for="item in getVisiblePages(currentPage, Math.ceil(totalCount / pageSize))" :key="item">
                <span v-if="item === '...'" class="page-ellipsis">...</span>
                <button v-else class="page-btn" :class="{ active: item === currentPage }" @click="handlePageChange(Number(item))">{{ item }}</button>
              </template>
              <button class="page-btn" :disabled="currentPage >= Math.ceil(totalCount / pageSize)" @click="handlePageChange(currentPage + 1)" title="下一页">&gt;</button>
              <button class="page-btn" :disabled="currentPage >= Math.ceil(totalCount / pageSize)" @click="handlePageChange(Math.ceil(totalCount / pageSize))" title="尾页">&gt;&gt;</button>
            </div>
          </template>

          <template v-else-if="tab.key === 'trajectory'">
            <ReadingTrajectory />
          </template>

        </el-tab-pane>
      </el-tabs>
    </el-card>

    <el-dialog v-model="editDialogVisible" title="编辑资料" width="520px" class="edit-dialog" :close-on-click-modal="false">
      <el-tabs v-model="activeEditTab" class="edit-tabs">
        <el-tab-pane label="基本资料" name="profile">
          <el-form :model="editForm" label-width="80px" class="edit-form">
            <el-form-item label="头像">
              <div class="avatar-upload-section">
                <div class="avatar-preview-wrapper">
                  <el-avatar :size="80" :src="normalizeAvatarUrl(editForm.avatar)" :icon="User" class="avatar-preview">
                    {{ editForm.nickname?.charAt(0) || '用' }}
                  </el-avatar>
                </div>
                <el-upload
                  class="avatar-uploader"
                  :show-file-list="false"
                  :before-upload="handleAvatarChange"
                  accept="image/*"
                >
                  <el-button type="primary" :icon="Plus" size="small">上传头像</el-button>
                  <div class="upload-tip">支持 JPG、PNG 格式，大小不超过 2MB</div>
                </el-upload>
              </div>
            </el-form-item>
            <el-form-item label="昵称">
              <el-input v-model="editForm.nickname" placeholder="请输入昵称" maxlength="20" show-word-limit />
            </el-form-item>
            <el-form-item label="邮箱">
              <el-input v-model="editForm.email" placeholder="请输入邮箱" />
            </el-form-item>
            <el-form-item label="手机号">
              <el-input v-model="editForm.phone" placeholder="请输入手机号" />
            </el-form-item>
          </el-form>
          <div class="dialog-footer">
            <el-button @click="editDialogVisible = false">取消</el-button>
            <el-button type="primary" :loading="editLoading" @click="handleEditSubmit">保存</el-button>
          </div>
        </el-tab-pane>
        <el-tab-pane label="修改密码" name="password">
          <el-form :model="passwordForm" label-width="100px" class="edit-form">
            <el-form-item label="原密码">
              <el-input v-model="passwordForm.old_password" type="password" placeholder="请输入原密码" show-password />
            </el-form-item>
            <el-form-item label="新密码">
              <el-input v-model="passwordForm.new_password" type="password" placeholder="请输入新密码（至少6位）" show-password />
            </el-form-item>
            <el-form-item label="确认密码">
              <el-input v-model="passwordForm.confirm_password" type="password" placeholder="请再次输入新密码" show-password />
            </el-form-item>
            <el-alert
              title="密码修改成功后需要重新登录"
              type="info"
              :closable="false"
              size="small"
              class="password-tip"
            />
          </el-form>
          <div class="dialog-footer">
            <el-button @click="editDialogVisible = false">取消</el-button>
            <el-button type="primary" :loading="passwordLoading" @click="handleChangePassword">确认修改</el-button>
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-dialog>

    <el-dialog v-model="aiDetailVisible" title="AI 生成详情" width="700px" class="ai-detail-dialog">
      <div v-if="currentAIRecord" class="detail-body">
        <!-- 标题行 -->
        <div class="detail-header">
          <div class="detail-header-left">
            <span class="detail-source-label">
              {{ currentAIRecord.source === 'news' ? '新闻导入' : '手动输入' }}
            </span>
            <span class="detail-header-title">{{ currentAIRecord.source_title || `记录 #${currentAIRecord.id}` }}</span>
          </div>
          <el-tag
            size="small"
            :type="currentAIRecord.risk_level === 'high' ? 'danger' : currentAIRecord.risk_level === 'medium' ? 'warning' : 'success'"
          >
            {{ currentAIRecord.risk_level === 'high' ? '高风险' : currentAIRecord.risk_level === 'medium' ? '中风险' : '低风险' }}
          </el-tag>
        </div>

        <!-- 输入文本 -->
        <div class="detail-card">
          <div class="detail-card-title">输入文本</div>
          <div class="detail-card-body">
            <p>{{ currentAIRecord.input_text }}</p>
          </div>
        </div>

        <!-- 候选标题 -->
        <div class="detail-card">
          <div class="detail-card-title">候选标题</div>
          <div class="detail-card-body">
            <div class="title-list">
              <div
                v-for="(title, index) in currentAIRecord.candidate_titles"
                :key="index"
                class="title-item"
              >
                <span class="title-index">{{ index + 1 }}</span>
                <span class="title-text">{{ title }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 简短摘要 -->
        <div class="detail-card">
          <div class="detail-card-title">简短摘要</div>
          <div class="detail-card-body">
            <p>{{ currentAIRecord.summary_short }}</p>
          </div>
        </div>

        <!-- 详细摘要 -->
        <div v-if="currentAIRecord.summary_long" class="detail-card">
          <div class="detail-card-title">详细摘要</div>
          <div class="detail-card-body">
            <p>{{ currentAIRecord.summary_long }}</p>
          </div>
        </div>

        <!-- 底部元信息 -->
        <div class="detail-meta">
          <span class="detail-time">
            {{ currentAIRecord.create_time || '暂无时间' }}
          </span>
        </div>
      </div>
    </el-dialog>
  </main>
</template>

<style scoped>
.page-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 24px 24px;
}

/* ===== 顶部个人名片横幅 ===== */
.dashboard-hero {
  position: relative;
  margin-bottom: 24px;
  border-radius: 20px;
  overflow: hidden;
}

.hero-bg {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 220px;
  background: linear-gradient(135deg, #1d4ed8 0%, #2563eb 50%, #6366f1 100%);
}

.hero-bg::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background:
    radial-gradient(circle at 20% 50%, rgba(255,255,255,0.08) 0%, transparent 50%),
    radial-gradient(circle at 80% 30%, rgba(255,255,255,0.05) 0%, transparent 40%);
}

.hero-content {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 24px;
  padding: 32px 32px 24px;
}

.hero-left {
  display: flex;
  align-items: flex-start;
  gap: 24px;
  flex: 1;
  min-width: 0;
}

.hero-avatar-col {
  flex-shrink: 0;
}

.avatar-wrapper {
  position: relative;
  flex-shrink: 0;
}

.user-avatar {
  border: 4px solid rgba(255, 255, 255, 0.95);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.2);
}

.hero-info-col {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.hero-name-row {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.hero-name {
  margin: 0;
  font-size: 26px;
  font-weight: 700;
  color: #fff;
  text-shadow: 0 2px 8px rgba(0, 0, 0, 0.25);
  line-height: 1.3;
}

.hero-meta-row {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.hero-meta-item {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  color: rgba(255, 255, 255, 0.85);
  font-size: 13px;
}

.hero-tags-row {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.hero-reading-tag {
  background: rgba(255, 255, 255, 0.2) !important;
  border-color: rgba(255, 255, 255, 0.35) !important;
  color: #fff !important;
  font-weight: 500;
}

.hero-desc {
  margin: 0;
  color: rgba(255, 255, 255, 0.9);
  font-size: 14px;
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.15);
}

.hero-right {
  flex-shrink: 0;
  display: flex;
  align-items: flex-start;
  padding-top: 4px;
}

.hero-edit-btn {
  background: rgba(255, 255, 255, 0.2);
  border: 1.5px solid rgba(255, 255, 255, 0.4);
  color: #fff;
  font-weight: 600;
  backdrop-filter: blur(8px);
  border-radius: 10px;
  padding: 8px 20px;
  transition: all 0.25s ease;
}

.hero-edit-btn:hover {
  background: rgba(255, 255, 255, 0.3) !important;
  border-color: rgba(255, 255, 255, 0.6) !important;
  color: #fff !important;
  transform: translateY(-1px);
}

/* ===== 数据概览卡片 ===== */
.dashboard-stats {
  position: relative;
  z-index: 2;
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  padding: 0 24px 24px;
  margin-top: -12px;
}

.dash-stat-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 20px 18px;
  background: #fff;
  border-radius: 16px;
  border: 1px solid #e5e7eb;
  cursor: pointer;
  user-select: none;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04);
}

.dash-stat-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 24px rgba(37, 99, 235, 0.12);
  border-color: #bfdbfe;
}

.dash-stat-card--active {
  border-color: #2563eb;
  background: #f0f5ff;
  box-shadow: 0 4px 16px rgba(37, 99, 235, 0.15);
}

.dash-stat-card--active .dash-stat-card__icon {
  background: #2563eb;
  color: #fff;
}

.dash-stat-card__icon {
  width: 48px;
  height: 48px;
  border-radius: 14px;
  background: #eff6ff;
  color: #2563eb;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: all 0.3s ease;
}

.dash-stat-card__body {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.dash-stat-card__count {
  font-size: 26px;
  font-weight: 700;
  color: #1e293b;
  line-height: 1.2;
}

.dash-stat-card__label {
  font-size: 14px;
  font-weight: 600;
  color: #475569;
}

.dash-stat-card__desc {
  font-size: 12px;
  color: #94a3b8;
}

.dash-stat-card__hint {
  font-size: 12px;
  color: #cbd5e1;
  flex-shrink: 0;
  transition: color 0.3s ease;
}

.dash-stat-card:hover .dash-stat-card__hint {
  color: #2563eb;
}

/* ===== 阅读画像占位区 ===== */
.reading-portrait-placeholder {
  margin-bottom: 24px;
  padding: 24px;
  background: #fff;
  border-radius: 16px;
  border: 1px dashed #cbd5e1;
}

.portrait-header {
  margin-bottom: 20px;
}

.portrait-title {
  margin: 0 0 6px;
  font-size: 18px;
  font-weight: 700;
  color: #1e293b;
  display: flex;
  align-items: center;
  gap: 8px;
}

.portrait-subtitle {
  margin: 0;
  font-size: 13px;
  color: #94a3b8;
}

.portrait-skeletons {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.portrait-skeleton-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  padding: 24px 16px;
  background: #f8fafc;
  border-radius: 14px;
  border: 1px solid #e5e7eb;
  text-align: center;
  transition: background 0.3s ease;
}

.portrait-skeleton-card:hover {
  background: #f0f5ff;
}

.skeleton-icon-wrapper {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: #eff6ff;
  color: #93c5fd;
  display: flex;
  align-items: center;
  justify-content: center;
}

.skeleton-label {
  font-size: 14px;
  font-weight: 600;
  color: #475569;
}

.skeleton-hint {
  font-size: 12px;
  color: #cbd5e1;
}

/* ===== 内容 Tab 区域 ===== */
.content-card {
  border-radius: 16px;
  overflow: hidden;
  border-color: #e5e7eb;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.06);
}

.content-card :deep(.el-card__body) {
  padding: 0 8px 8px;
}

.profile-tabs :deep(.el-tabs__header) {
  margin: 0;
  padding: 0 24px;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.profile-tabs :deep(.el-tabs__nav-wrap::after) {
  display: none;
}

.profile-tabs :deep(.el-tabs__item) {
  height: 56px;
  font-size: 15px;
  color: var(--el-text-color-secondary);
}

.profile-tabs :deep(.el-tabs__item.is-active) {
  color: #2563eb;
  font-weight: 600;
}

.profile-tabs :deep(.el-tabs__item:hover) {
  color: #2563eb;
}

.profile-tabs :deep(.el-tabs__active-bar) {
  background-color: #2563eb;
}

.profile-tabs :deep(.el-tab-pane) {
  padding-top: 4px;
}

.profile-tabs :deep(.el-tab-pane) {
  width: 100%;
}

.profile-tabs :deep(.el-tabs__content) {
  width: 100%;
}

.tab-icon {
  margin-right: 6px;
}

.loading-container {
  padding: 24px;
}

.tab-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 20px;
  padding: 12px 16px;
  background: var(--el-fill-color-lighter);
  border-radius: 12px;
  border: 1px solid var(--el-border-color-lighter);
}

.search-input {
  width: 280px;
  max-width: 320px;
}

.search-bar-wrapper {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.compact-empty {
  padding: 48px 16px;
}

.compact-empty :deep(.el-empty__image) {
  display: none;
}

.empty-state {
  padding: 64px 16px;
  text-align: center;
}

.empty-icon {
  margin-bottom: 16px;
  color: var(--el-text-color-placeholder);
}

.empty-text {
  margin: 0 0 8px;
  font-size: 18px;
  font-weight: 500;
  color: var(--el-text-color-primary);
}

.empty-desc {
  margin: 0 0 20px;
  color: var(--el-text-color-secondary);
  font-size: 14px;
}

.segmented-control {
  display: inline-flex;
  background: #f1f5f9;
  border-radius: 999px;
  padding: 3px;
}

.segmented-control :deep(.el-radio-button) {
  margin: 0;
}

.segmented-control :deep(.el-radio-button__inner) {
  border: none;
  background: transparent;
  border-radius: 999px;
  padding: 6px 18px;
  font-size: 14px;
  font-weight: 500;
  color: #64748b;
  box-shadow: none;
}

.segmented-control :deep(.el-radio-button__original-radio:checked + .el-radio-button__inner) {
  background: #ffffff;
  color: #2563eb;
  box-shadow: 0 2px 8px rgba(37, 99, 235, 0.16);
}

.segmented-control :deep(.el-radio-button__inner:hover) {
  color: #2563eb;
}

.record-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.record-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 14px;
  border-radius: 14px;
  background: #fff;
  border: 1px solid #e5e7eb;
  cursor: pointer;
  transition: all 0.25s ease;
}

.record-item:hover {
  background: #f8fafc;
  border-color: #2563eb;
  box-shadow: 0 4px 16px rgba(37, 99, 235, 0.10);
  transform: translateY(-2px);
}

.record-item-detailed {
  flex-direction: column;
  align-items: flex-start;
  gap: 8px;
  padding: 10px 14px;
}

.record-main {
  flex: 1;
  min-width: 0;
  width: 100%;
}

.record-tag {
  margin-bottom: 6px;
}

.record-title {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
}

.link-title {
  cursor: pointer;
}

.link-title:hover {
  color: var(--el-color-primary);
}

.record-summary {
  margin: 4px 0 0;
  color: var(--el-text-color-secondary);
  font-size: 14px;
  line-height: 1.5;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
}

.record-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--el-text-color-secondary);
  font-size: 13px;
  flex-wrap: wrap;
}

.record-source {
  margin-right: 4px;
}

.record-arrow {
  color: var(--el-text-color-placeholder);
  flex-shrink: 0;
  transition: transform 0.25s ease, color 0.25s ease;
}

.record-item:hover .record-arrow {
  transform: translateX(4px);
  color: #2563eb;
}

.comment-box {
  margin-top: 10px;
  padding: 12px 16px;
  background: var(--el-fill-color-lighter);
  border-radius: 8px;
  border-left: 3px solid var(--el-color-primary);
}

.comment-content {
  margin: 0;
  color: var(--el-text-color-primary);
  font-size: 14px;
  line-height: 1.7;
}

.like-count {
  display: flex;
  align-items: center;
  gap: 4px;
}

.ai-record-item {
  padding: 20px;
  border-radius: 14px;
  background: #fff;
  border: 1px solid #e5e7eb;
  transition: all 0.25s ease;
}

.ai-record-item:hover {
  border-color: #2563eb;
  box-shadow: 0 4px 16px rgba(37, 99, 235, 0.10);
  transform: translateY(-2px);
}

.ai-record-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.ai-record-title-row {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
  flex: 1;
}

.ai-record-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.ai-record-section {
  margin-bottom: 14px;
}

.section-label {
  display: inline-block;
  margin-bottom: 8px;
  font-size: 13px;
  font-weight: 500;
  color: var(--el-text-color-secondary);
}

.section-content {
  margin: 0;
  color: var(--el-text-color-primary);
  font-size: 14px;
  line-height: 1.7;
}

.title-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.ai-record-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 16px;
  padding-top: 12px;
  border-top: 1px solid var(--el-border-color-lighter);
}

.source-tag {
  font-size: 13px;
  color: var(--el-text-color-secondary);
}

.record-time {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: var(--el-text-color-secondary);
}

.profile-pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 4px;
  margin-top: 32px;
  padding-bottom: 8px;
  flex-wrap: wrap;
}

.profile-pagination .page-btn {
  min-width: 36px;
  height: 36px;
  padding: 0 8px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  background: #fff;
  color: #374151;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  user-select: none;
}

.profile-pagination .page-btn:hover:not(:disabled):not(.active) {
  background: #f3f4f6;
  border-color: #2563eb;
  color: #2563eb;
}

.profile-pagination .page-btn.active {
  background: #2563eb;
  border-color: #2563eb;
  color: #fff;
  font-weight: 600;
  box-shadow: 0 2px 8px rgba(37, 99, 235, 0.25);
}

.profile-pagination .page-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
  background: #f9fafb;
}

.profile-pagination .page-ellipsis {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  color: #9ca3af;
  font-size: 14px;
  user-select: none;
}

.edit-dialog :deep(.el-dialog__header) {
  padding: 20px 24px;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.edit-dialog :deep(.el-dialog__body) {
  padding: 24px;
}

.edit-dialog :deep(.el-dialog__footer) {
  padding: 16px 24px;
  border-top: 1px solid var(--el-border-color-lighter);
}

.edit-form {
  margin: 0;
}

.avatar-upload-section {
  display: flex;
  align-items: center;
  gap: 20px;
}

.avatar-preview-wrapper {
  flex-shrink: 0;
}

.avatar-preview {
  border: 3px solid var(--el-border-color-lighter);
}

.avatar-uploader {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.upload-tip {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.record-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.delete-btn {
  opacity: 0;
  transition: opacity 0.3s ease;
}

.record-item:hover .delete-btn {
  opacity: 1;
}

.record-header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 8px;
}

.favorite-remove-btn {
  flex-shrink: 0;
}

.line-clamp-2 {
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
}

.line-clamp-3 {
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  line-clamp: 3;
  -webkit-box-orient: vertical;
}

.ai-record-header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}

.ai-detail-dialog :deep(.el-dialog__header) {
  padding: 18px 24px;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.ai-detail-dialog :deep(.el-dialog__body) {
  padding: 20px 24px 24px;
  max-height: 72vh;
  overflow-y: auto;
}

.detail-body {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.detail-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.detail-header-left {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
  flex: 1;
}

.detail-source-label {
  flex-shrink: 0;
  font-size: 12px;
  color: #fff;
  background: var(--el-color-warning);
  padding: 2px 8px;
  border-radius: 4px;
  font-weight: 500;
}

.detail-header-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.detail-card {
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 8px;
  overflow: hidden;
}

.detail-card-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  padding: 10px 14px;
  background: var(--el-fill-color-lighter);
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.detail-card-body {
  padding: 14px;
}

.detail-card-body p {
  margin: 0;
  color: var(--el-text-color-regular);
  font-size: 14px;
  line-height: 1.7;
}

.title-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.title-item {
  display: flex;
  align-items: baseline;
  gap: 8px;
  padding: 8px 10px;
  border-radius: 6px;
  background: var(--el-fill-color-lighter);
  transition: background 0.2s;
}

.title-item:hover {
  background: var(--el-color-primary-light-9);
}

.title-index {
  flex-shrink: 0;
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: var(--el-color-primary-light-8);
  color: var(--el-color-primary);
  font-size: 12px;
  font-weight: 600;
}

.title-text {
  font-size: 14px;
  color: var(--el-text-color-regular);
  line-height: 1.5;
}

.detail-meta {
  display: flex;
  justify-content: flex-end;
  padding-top: 12px;
  border-top: 1px solid var(--el-border-color-lighter);
}

.detail-time {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: var(--el-text-color-secondary);
}

@media (max-width: 768px) {
  .page-container {
    padding: 0 16px 16px;
  }

  .hero-content {
    flex-direction: column;
    padding: 24px 20px 20px;
  }

  .hero-left {
    flex-direction: column;
    align-items: center;
    text-align: center;
  }

  .hero-name-row {
    justify-content: center;
  }

  .hero-meta-row {
    justify-content: center;
  }

  .hero-tags-row {
    justify-content: center;
  }

  .hero-right {
    padding-top: 0;
    width: 100%;
    display: flex;
    justify-content: center;
  }

  .dashboard-stats {
    grid-template-columns: repeat(2, 1fr);
  }

  .portrait-skeletons {
    grid-template-columns: repeat(2, 1fr);
  }

  .dash-stat-card {
    padding: 14px;
  }

  .tab-toolbar {
    flex-direction: column;
    align-items: stretch;
  }

  .search-input {
    max-width: none;
  }
}

@media (max-width: 480px) {
  .dashboard-stats {
    grid-template-columns: 1fr;
  }

  .portrait-skeletons {
    grid-template-columns: 1fr;
  }

  .dash-stat-card__count {
    font-size: 22px;
  }

  .hero-name {
    font-size: 22px;
  }
}

.edit-tabs {
  margin-bottom: 8px;
}

.edit-form {
  padding: 8px 0;
  margin: 0;
}

.password-tip {
  margin-top: 8px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--el-border-color-lighter);
  margin-top: 8px;
}
</style>
