<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
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
import { changePasswordApi, getUserProfileApi, updateUserProfileApi, uploadAvatarApi } from '@/api/user'
import { useUserStore } from '@/stores/user'
import ReadingTrajectory from '@/components/profile/ReadingTrajectory.vue'

const router = useRouter()
const userStore = useUserStore()

const activeTab = ref('overview')
const loadingTab = ref('')

const browseType = ref<'news' | 'post'>('news')
const favoriteType = ref<'news' | 'post'>('news')

const profileOverview = ref<ProfileOverview | null>(null)
const browseHistory = ref<BrowseHistoryItem[]>([])
const favorites = ref<FavoriteItem[]>([])
const comments = ref<CommentRecordItem[]>([])
const aiRecords = ref<AIRecordItem[]>([])
const subscriptions = ref<SubscriptionCategory[]>([])

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
  { key: 'overview', label: '概览', icon: Grid },
  { key: 'history', label: '浏览历史', icon: Clock },
  { key: 'favorites', label: '收藏记录', icon: Star },
  { key: 'comments', label: '评论记录', icon: ChatDotRound },
  { key: 'ai-records', label: 'AI 生成记录', icon: MagicStick },
  { key: 'trajectory', label: '阅读脉络', icon: View },
  { key: 'subscriptions', label: '订阅管理', icon: SwitchButton },
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
      item.news_title.toLowerCase().includes(query)
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
    await unfavoriteNews(item.news_id)
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
    return 'http://127.0.0.1:8000' + url
  }
  return url
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

async function loadBrowseHistory(page = 1) {
  loadingTab.value = 'history'
  try {
    const result = await getBrowseHistory(page, pageSize)
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
    const result = await getComments(page, pageSize)
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

async function loadSubscriptions() {
  loadingTab.value = 'subscriptions'
  try {
    const result = await getSubscriptions()
    subscriptions.value = result.categories
  } catch (error) {
    console.error(error)
    ElMessage.error('加载订阅信息失败，请稍后重试')
  } finally {
    loadingTab.value = ''
  }
}

async function handleSubscriptionChange(category: SubscriptionCategory) {
  try {
    const subscribedIds = subscriptions.value
      .filter((c) => c.subscribed)
      .map((c) => c.id)
    await updateSubscriptions(subscribedIds)
    ElMessage.success(
      category.subscribed ? `已订阅 ${category.name}` : `已取消订阅 ${category.name}`
    )
  } catch (error) {
    console.error(error)
    category.subscribed = !category.subscribed
    ElMessage.error('更新订阅失败，请稍后重试')
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
  } else if (key === 'subscriptions') {
    loadSubscriptions()
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

onMounted(async () => {
  await loadCurrentUserProfile()
  loadOverview()
})
</script>

<template>
  <main class="page-container">
    <div class="profile-header">
      <div class="header-bg"></div>
      <div class="header-content">
        <div class="user-profile">
          <div class="avatar-wrapper">
            <el-avatar :size="96" :src="normalizeAvatarUrl(userStore.userInfo?.avatar)" :icon="User" class="user-avatar">
              {{ userStore.userInfo?.nickname?.charAt(0) || '用' }}
            </el-avatar>
            <div class="avatar-edit" @click="openEditDialog()" title="更换头像">
              <Edit :size="16" />
            </div>
          </div>
          <div class="user-info">
            <div class="user-name-row">
              <h1 class="user-name">{{ userStore.userInfo?.nickname || '未登录用户' }}</h1>
              <el-button
                type="primary"
                :icon="Edit"
                size="small"
                class="edit-btn"
                @click="openEditDialog()"
              >
                编辑资料
              </el-button>
            </div>
            <div class="user-tags">
              <el-tag :type="userStore.isAdmin ? 'danger' : userStore.isEditor ? 'warning' : 'info'" effect="dark" round>
                {{
                  userStore.isAdmin
                    ? '管理员'
                    : userStore.isEditor
                      ? '审核/编辑'
                      : '普通用户'
                }}
              </el-tag>
              <span class="user-id">ID: {{ userStore.userInfo?.id || '-' }}</span>
            </div>
            <p class="user-desc">欢迎回来，继续探索精彩内容</p>
          </div>
        </div>
        <div class="quick-stats">
          <div class="quick-stat-item">
            <span class="quick-stat-num">{{ profileOverview?.browse_count ?? 0 }}</span>
            <span class="quick-stat-label">浏览</span>
          </div>
          <div class="divider"></div>
          <div class="quick-stat-item">
            <span class="quick-stat-num">{{ profileOverview?.favorite_count ?? 0 }}</span>
            <span class="quick-stat-label">收藏</span>
          </div>
          <div class="divider"></div>
          <div class="quick-stat-item">
            <span class="quick-stat-num">{{ profileOverview?.comment_count ?? 0 }}</span>
            <span class="quick-stat-label">评论</span>
          </div>
          <div class="divider"></div>
          <div class="quick-stat-item">
            <span class="quick-stat-num">{{ profileOverview?.ai_generate_count ?? 0 }}</span>
            <span class="quick-stat-label">AI生成</span>
          </div>
        </div>
      </div>
    </div>

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
              <div class="overview-welcome">
                <h2 class="welcome-title">
                  你好，{{ userStore.userInfo?.nickname || '用户' }} 👋
                </h2>
                <p class="welcome-desc">
                  这里是你的个人中心，可以查看你的浏览历史、收藏记录、评论和 AI 生成记录。
                </p>
              </div>

              <div class="stats-grid">
                <div class="stat-card stat-history" @click="handleTabChange('history')">
                  <div class="stat-icon-wrapper">
                    <Clock :size="28" class="stat-icon" />
                  </div>
                  <div class="stat-info">
                    <span class="stat-num">{{ profileOverview?.browse_count ?? 0 }}</span>
                    <span class="stat-label">浏览记录</span>
                  </div>
                  <ArrowRight :size="20" class="stat-arrow" />
                </div>

                <div class="stat-card stat-star" @click="handleTabChange('favorites')">
                  <div class="stat-icon-wrapper">
                    <Star :size="28" class="stat-icon" />
                  </div>
                  <div class="stat-info">
                    <span class="stat-num">{{ profileOverview?.favorite_count ?? 0 }}</span>
                    <span class="stat-label">收藏记录</span>
                  </div>
                  <ArrowRight :size="20" class="stat-arrow" />
                </div>

                <div class="stat-card stat-comment" @click="handleTabChange('comments')">
                  <div class="stat-icon-wrapper">
                    <ChatDotRound :size="28" class="stat-icon" />
                  </div>
                  <div class="stat-info">
                    <span class="stat-num">{{ profileOverview?.comment_count ?? 0 }}</span>
                    <span class="stat-label">评论记录</span>
                  </div>
                  <ArrowRight :size="20" class="stat-arrow" />
                </div>

                <div class="stat-card stat-ai" @click="handleTabChange('ai-records')">
                  <div class="stat-icon-wrapper">
                    <MagicStick :size="28" class="stat-icon" />
                  </div>
                  <div class="stat-info">
                    <span class="stat-num">{{ profileOverview?.ai_generate_count ?? 0 }}</span>
                    <span class="stat-label">AI 生成</span>
                  </div>
                  <ArrowRight :size="20" class="stat-arrow" />
                </div>
              </div>

              <div class="function-entries">
                <h3 class="section-title">功能入口</h3>
                <div class="entry-grid">
                  <div class="entry-card" @click="handleTabChange('subscriptions')">
                    <div class="entry-icon entry-icon-subscribe">
                      <SwitchButton :size="24" />
                    </div>
                    <div class="entry-info">
                      <span class="entry-title">订阅管理</span>
                      <span class="entry-desc">管理你的新闻分类订阅</span>
                    </div>
                  </div>
                  <div class="entry-card" @click="openAccountDialog">
                    <div class="entry-icon entry-icon-setting">
                      <Setting :size="24" />
                    </div>
                    <div class="entry-info">
                      <span class="entry-title">账号设置</span>
                      <span class="entry-desc">修改密码和账号安全</span>
                    </div>
                  </div>
                  <div class="entry-card" @click="router.push('/ai/title-summary')">
                    <div class="entry-icon entry-icon-ai">
                      <MagicStick :size="24" />
                    </div>
                    <div class="entry-info">
                      <span class="entry-title">AI 摘要</span>
                      <span class="entry-desc">使用 AI 生成新闻摘要</span>
                    </div>
                  </div>
                  <div class="entry-card" @click="router.push('/community')">
                    <div class="entry-icon entry-icon-community">
                      <Files :size="24" />
                    </div>
                    <div class="entry-info">
                      <span class="entry-title">社区动态</span>
                      <span class="entry-desc">查看和发布社区帖子</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </template>

          <template v-else-if="tab.key === 'history'">
            <div class="tab-toolbar">
              <div class="search-bar-wrapper">
                <el-radio-group v-model="browseType" size="small" @change="browseSearchKeyword = ''; currentPage = 1">
                  <el-radio-button value="news">新闻</el-radio-button>
                  <el-radio-button value="post">帖子</el-radio-button>
                </el-radio-group>
                <el-input
                  v-if="browseType === 'news'"
                  v-model="browseSearchKeyword"
                  placeholder="搜索浏览历史..."
                  :prefix-icon="Search"
                  class="search-input"
                  @keyup.enter="currentPage = 1"
                />
                <el-button v-if="browseType === 'news'" type="primary" @click="currentPage = 1">搜索</el-button>
                <el-button v-if="browseType === 'news'" @click="clearBrowseSearch">清空</el-button>
              </div>
              <el-button type="danger" plain :disabled="browseHistory.length === 0" @click="handleClearHistory">
                清空历史
              </el-button>
            </div>

            <div v-if="browseType === 'post'" class="empty-state">
              <Clock :size="64" class="empty-icon" />
              <p class="empty-text">暂无帖子浏览记录</p>
              <p class="empty-desc">浏览社区帖子后将在这里显示</p>
            </div>
            <div v-else-if="browseHistory.length === 0" class="empty-state">
              <Clock :size="64" class="empty-icon" />
              <p class="empty-text">暂无浏览历史</p>
              <p class="empty-desc">去首页看看精彩新闻吧</p>
              <el-button type="primary" @click="router.push('/')">返回首页</el-button>
            </div>
            <div v-else-if="filteredBrowseHistory.length === 0" class="empty-state">
              <Clock :size="64" class="empty-icon" />
              <p class="empty-text">未找到匹配的浏览记录</p>
              <p class="empty-desc">请尝试其他关键词</p>
            </div>
            <div v-else class="record-list">
              <div
                v-for="item in filteredBrowseHistory"
                :key="`${item.news_id}-${item.browse_time}`"
                class="record-item"
                @click="goToNewsDetail(item.news_id)"
              >
                <div class="record-main">
                  <el-tag size="small" class="record-tag">{{ item.category_name }}</el-tag>
                  <h3 class="record-title">{{ item.title }}</h3>
                </div>
                <div class="record-meta">
                  <Clock :size="14" />
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

            <div v-if="totalCount > pageSize" class="pagination-wrapper">
              <el-pagination
                v-model:current-page="currentPage"
                :page-size="pageSize"
                :total="totalCount"
                layout="prev, pager, next, total"
                @current-change="handlePageChange"
              />
            </div>
          </template>

          <template v-else-if="tab.key === 'favorites'">
            <div class="tab-toolbar">
              <div class="search-bar-wrapper">
                <el-radio-group v-model="favoriteType" size="small" @change="favoriteSearchKeyword = ''; currentPage = 1; loadFavorites()">
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

            <div v-if="favorites.length === 0" class="empty-state">
              <Star :size="64" class="empty-icon" />
              <p class="empty-text">{{ favoriteType === 'news' ? '暂无新闻收藏记录' : '暂无帖子收藏记录' }}</p>
              <p class="empty-desc">看到喜欢的就收藏起来吧</p>
            </div>
            <div v-else-if="filteredFavorites.length === 0" class="empty-state">
              <Star :size="64" class="empty-icon" />
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
                  <Clock :size="14" />
                  <span>收藏于 {{ item.favorited_at || item.publish_time }}</span>
                </div>
                <ArrowRight :size="18" class="record-arrow" />
              </div>
            </div>

            <div v-if="totalCount > pageSize" class="pagination-wrapper">
              <el-pagination
                v-model:current-page="currentPage"
                :page-size="pageSize"
                :total="totalCount"
                layout="prev, pager, next, total"
                @current-change="handlePageChange"
              />
            </div>
          </template>

          <template v-else-if="tab.key === 'comments'">
            <div class="tab-toolbar">
              <div class="search-bar-wrapper">
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

            <div v-if="comments.length === 0" class="empty-state">
              <ChatDotRound :size="64" class="empty-icon" />
              <p class="empty-text">暂无评论记录</p>
              <p class="empty-desc">去新闻详情页发表你的看法吧</p>
            </div>
            <div v-else-if="filteredComments.length === 0" class="empty-state">
              <ChatDotRound :size="64" class="empty-icon" />
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
                  <el-tag size="small" class="record-tag">{{ item.category_name }}</el-tag>
                  <h3 class="record-title link-title" @click="goToNewsDetail(item.news_id)">
                    {{ item.news_title }}
                  </h3>
                  <div class="comment-box">
                    <p class="comment-content">{{ item.content }}</p>
                  </div>
                </div>
                <div class="record-meta">
                  <Clock :size="14" />
                  <span>{{ item.create_time }}</span>
                  <span class="like-count">
                    <Star :size="14" />
                    {{ item.like_count }}
                  </span>
                </div>
              </div>
            </div>

            <div v-if="totalCount > pageSize" class="pagination-wrapper">
              <el-pagination
                v-model:current-page="currentPage"
                :page-size="pageSize"
                :total="totalCount"
                layout="prev, pager, next, total"
                @current-change="handlePageChange"
              />
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

            <div v-if="filteredAIRecords.length === 0" class="empty-state">
              <MagicStick :size="64" class="empty-icon" />
              <p class="empty-text">{{ aiSearchKeyword ? '未找到匹配的 AI 记录' : '暂无 AI 生成记录' }}</p>
              <p class="empty-desc">{{ aiSearchKeyword ? '请尝试其他关键词' : '去体验 AI 智能摘要功能吧' }}</p>
              <el-button v-if="!aiSearchKeyword" type="primary" @click="router.push('/ai/title-summary')">去生成</el-button>
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
                    <Clock :size="14" />
                    {{ item.create_time || '暂无时间' }}
                  </span>
                </div>
              </div>
            </div>

            <div v-if="totalCount > pageSize" class="pagination-wrapper">
              <el-pagination
                v-model:current-page="currentPage"
                :page-size="pageSize"
                :total="totalCount"
                layout="prev, pager, next, total"
                @current-change="handlePageChange"
              />
            </div>
          </template>

          <template v-else-if="tab.key === 'trajectory'">
            <ReadingTrajectory />
          </template>

          <template v-else-if="tab.key === 'subscriptions'">
            <div class="subscriptions-content">
              <div class="subscriptions-header">
                <h3 class="section-title">新闻分类订阅</h3>
                <p class="section-desc">选择你感兴趣的新闻分类，获取个性化推荐</p>
              </div>

              <div class="subscription-grid">
                <div
                  v-for="category in subscriptions"
                  :key="category.id"
                  class="subscription-card"
                  :class="{ active: category.subscribed }"
                  @click="category.subscribed = !category.subscribed; handleSubscriptionChange(category)"
                >
                  <div class="subscription-icon">{{ getCategoryIcon(category.code) }}</div>
                  <div class="subscription-info">
                    <span class="subscription-name">{{ category.name }}</span>
                    <span class="subscription-desc">{{ getCategoryDesc(category.code) }}</span>
                  </div>
                  <el-switch
                    v-model="category.subscribed"
                    active-color="var(--el-color-primary)"
                    @click.stop
                    @change="handleSubscriptionChange(category)"
                  />
                </div>
              </div>

              <div class="subscription-tip">
                <el-alert
                  title="订阅提示"
                  type="info"
                  :closable="false"
                  show-icon
                >
                  <template #default>
                    订阅你感兴趣的分类后，首页将优先展示相关分类的新闻内容。
                  </template>
                </el-alert>
              </div>
            </div>
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

    <el-dialog v-model="aiDetailVisible" title="AI 生成详情" width="640px" class="ai-detail-dialog">
      <div v-if="currentAIRecord" class="ai-detail-content">
        <div class="ai-detail-header">
          <div class="ai-detail-title-row">
            <el-tag type="warning" effect="dark">AI 记录</el-tag>
            <span class="ai-detail-title">
              {{ currentAIRecord.source_title || `记录 #${currentAIRecord.id}` }}
            </span>
          </div>
          <el-tag
            :type="currentAIRecord.risk_level === 'high' ? 'danger' : currentAIRecord.risk_level === 'medium' ? 'warning' : 'success'"
          >
            {{ currentAIRecord.risk_level === 'high' ? '高风险' : currentAIRecord.risk_level === 'medium' ? '中风险' : '低风险' }}
          </el-tag>
        </div>

        <div class="ai-detail-section">
          <div class="detail-section-label">
            <View :size="16" />
            <span>输入文本</span>
          </div>
          <div class="detail-section-content">
            <p>{{ currentAIRecord.input_text }}</p>
          </div>
        </div>

        <div class="ai-detail-section">
          <div class="detail-section-label">
            <MagicStick :size="16" />
            <span>候选标题</span>
          </div>
          <div class="detail-section-content">
            <div class="candidate-tags">
              <el-tag
                v-for="(title, index) in currentAIRecord.candidate_titles"
                :key="index"
                type="info"
                class="candidate-tag"
              >
                {{ title }}
              </el-tag>
            </div>
          </div>
        </div>

        <div class="ai-detail-section">
          <div class="detail-section-label">
            <Files :size="16" />
            <span>简短摘要</span>
          </div>
          <div class="detail-section-content">
            <p>{{ currentAIRecord.summary_short }}</p>
          </div>
        </div>

        <div v-if="currentAIRecord.summary_long" class="ai-detail-section">
          <div class="detail-section-label">
            <Files :size="16" />
            <span>详细摘要</span>
          </div>
          <div class="detail-section-content">
            <p>{{ currentAIRecord.summary_long }}</p>
          </div>
        </div>

        <div class="ai-detail-footer">
          <span class="source-tag">{{ currentAIRecord.source === 'news' ? '新闻导入' : '手动输入' }}</span>
          <span class="record-time">
            <Clock :size="14" />
            {{ currentAIRecord.create_time || '暂无时间' }}
          </span>
        </div>
      </div>
    </el-dialog>
  </main>
</template>

<style scoped>
.page-container {
  max-width: 1080px;
  margin: 0 auto;
  padding: 0 24px 24px;
}

.profile-header {
  position: relative;
  margin-bottom: 24px;
  border-radius: 16px;
  overflow: hidden;
}

.header-bg {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 180px;
  background: linear-gradient(135deg, #4a5fc9 0%, #5a3580 50%, #c95ed6 100%);
  opacity: 1;
}

.header-bg::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(180deg, rgba(0, 0, 0, 0.05) 0%, rgba(0, 0, 0, 0.15) 100%);
}

.header-bg::before {
  content: '';
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 60%);
  animation: float 20s ease-in-out infinite;
}

@keyframes float {
  0%, 100% { transform: translate(0, 0) rotate(0deg); }
  50% { transform: translate(30px, -30px) rotate(180deg); }
}

.header-content {
  position: relative;
  z-index: 1;
  padding: 40px 32px 32px;
}

.user-profile {
  display: flex;
  align-items: center;
  gap: 24px;
  margin-bottom: 24px;
}

.avatar-wrapper {
  position: relative;
  flex-shrink: 0;
}

.user-avatar {
  border: 4px solid rgba(255, 255, 255, 0.9);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
}

.avatar-edit {
  position: absolute;
  bottom: 0;
  right: 0;
  width: 32px;
  height: 32px;
  background: #fff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #667eea;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  transition: all 0.3s ease;
}

.avatar-edit:hover {
  transform: scale(1.1);
  background: #667eea;
  color: #fff;
}

.user-info {
  flex: 1;
  min-width: 0;
}

.user-name-row {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 8px;
}

.user-name {
  margin: 0;
  font-size: 28px;
  font-weight: 700;
  color: #fff;
  text-shadow: 0 2px 8px rgba(0, 0, 0, 0.25);
}

.edit-btn {
  background: rgba(255, 255, 255, 0.25);
  border-color: rgba(255, 255, 255, 0.4);
  color: #fff;
  backdrop-filter: blur(10px);
  font-weight: 500;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
}

.edit-btn:hover {
  background: rgba(255, 255, 255, 0.35) !important;
  border-color: rgba(255, 255, 255, 0.6) !important;
  color: #fff !important;
}

.user-tags {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.user-id {
  color: rgba(255, 255, 255, 0.92);
  font-size: 14px;
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}

.user-desc {
  margin: 0;
  color: rgba(255, 255, 255, 0.95);
  font-size: 15px;
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}

.quick-stats {
  display: flex;
  align-items: center;
  justify-content: space-around;
  padding: 20px 32px;
  background: rgba(0, 0, 0, 0.15);
  backdrop-filter: blur(20px);
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.quick-stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.quick-stat-num {
  font-size: 28px;
  font-weight: 700;
  color: #fff;
  text-shadow: 0 2px 6px rgba(0, 0, 0, 0.25);
}

.quick-stat-label {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.92);
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}

.divider {
  width: 1px;
  height: 40px;
  background: rgba(255, 255, 255, 0.25);
}

.content-card {
  border-radius: 16px;
  overflow: hidden;
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

.overview-content {
  padding: 8px 4px 24px;
}

.overview-welcome {
  margin-bottom: 32px;
}

.welcome-title {
  margin: 0 0 8px;
  font-size: 22px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.welcome-desc {
  margin: 0;
  color: var(--el-text-color-secondary);
  font-size: 15px;
  line-height: 1.6;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
  margin-bottom: 36px;
}

.stat-card {
  position: relative;
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  border-radius: 12px;
  background: var(--el-bg-color-page);
  cursor: pointer;
  transition: all 0.3s ease;
  overflow: hidden;
}

.stat-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  border-radius: 12px 12px 0 0;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
}

.stat-card:hover::before {
  opacity: 1;
}

.stat-history::before {
  background: linear-gradient(90deg, #409eff, #66b1ff);
}

.stat-star::before {
  background: linear-gradient(90deg, #e6a23c, #f5dab1);
}

.stat-comment::before {
  background: linear-gradient(90deg, #67c23a, #95d475);
}

.stat-ai::before {
  background: linear-gradient(90deg, #8b5cf6, #c4b5fd);
}

.stat-icon-wrapper {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.stat-history .stat-icon-wrapper {
  background: linear-gradient(135deg, #ecf5ff, #d9ecff);
  color: #409eff;
}

.stat-star .stat-icon-wrapper {
  background: linear-gradient(135deg, #fdf6ec, #faecd8);
  color: #e6a23c;
}

.stat-comment .stat-icon-wrapper {
  background: linear-gradient(135deg, #f0f9eb, #e1f3d8);
  color: #67c23a;
}

.stat-ai .stat-icon-wrapper {
  background: linear-gradient(135deg, #f4f1ff, #e9d8fd);
  color: #8b5cf6;
}

.stat-info {
  flex: 1;
  min-width: 0;
}

.stat-num {
  display: block;
  font-size: 26px;
  font-weight: 700;
  color: var(--el-text-color-primary);
  line-height: 1.2;
}

.stat-label {
  display: block;
  font-size: 14px;
  color: var(--el-text-color-secondary);
  margin-top: 4px;
}

.stat-arrow {
  color: var(--el-text-color-placeholder);
  transition: transform 0.3s ease;
}

.stat-card:hover .stat-arrow {
  transform: translateX(4px);
  color: var(--el-color-primary);
}

.function-entries {
  margin-top: 8px;
}

.section-title {
  margin: 0 0 4px;
  font-size: 18px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.section-desc {
  margin: 0 0 20px;
  color: var(--el-text-color-secondary);
  font-size: 14px;
}

.entry-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
}

.entry-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 18px;
  border-radius: 12px;
  border: 1px solid var(--el-border-color-lighter);
  cursor: pointer;
  transition: all 0.3s ease;
}

.entry-card:hover {
  border-color: var(--el-color-primary-light-5);
  background: var(--el-color-primary-light-9);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.1);
}

.entry-icon {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  color: #fff;
}

.entry-icon-subscribe {
  background: linear-gradient(135deg, #667eea, #764ba2);
}

.entry-icon-setting {
  background: linear-gradient(135deg, #f093fb, #f5576c);
}

.entry-icon-ai {
  background: linear-gradient(135deg, #4facfe, #00f2fe);
}

.entry-icon-community {
  background: linear-gradient(135deg, #43e97b, #38f9d7);
}

.entry-info {
  flex: 1;
  min-width: 0;
}

.entry-title {
  display: block;
  font-size: 15px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  margin-bottom: 2px;
}

.entry-desc {
  display: block;
  font-size: 12px;
  color: var(--el-text-color-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.tab-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 20px;
  padding: 0 4px;
}

.search-input {
  max-width: 320px;
}

.search-bar-wrapper {
  display: flex;
  align-items: center;
  gap: 8px;
}

.search-bar-wrapper > :nth-child(3) {
  margin-left: -2px;
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

.record-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.record-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 18px 20px;
  border-radius: 12px;
  background: var(--el-bg-color-page);
  cursor: pointer;
  transition: all 0.3s ease;
}

.record-item:hover {
  background: var(--el-fill-color-light);
  transform: translateX(4px);
}

.record-item-detailed {
  flex-direction: column;
  align-items: flex-start;
  gap: 12px;
}

.record-main {
  flex: 1;
  min-width: 0;
  width: 100%;
}

.record-tag {
  margin-bottom: 8px;
}

.record-title {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  line-height: 1.5;
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
  margin: 8px 0 0;
  color: var(--el-text-color-secondary);
  font-size: 14px;
  line-height: 1.6;
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
  transition: transform 0.3s ease;
}

.record-item:hover .record-arrow {
  transform: translateX(4px);
  color: var(--el-color-primary);
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
  border-radius: 12px;
  background: var(--el-bg-color-page);
  transition: all 0.3s ease;
}

.ai-record-item:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
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

.pagination-wrapper {
  display: flex;
  justify-content: center;
  margin-top: 28px;
}

.subscriptions-content {
  padding: 8px 4px 24px;
}

.subscriptions-header {
  margin-bottom: 24px;
}

.subscription-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.subscription-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18px 20px;
  border-radius: 12px;
  border: 2px solid var(--el-border-color-lighter);
  background: var(--el-bg-color-page);
  transition: all 0.3s ease;
}

.subscription-card:hover {
  border-color: var(--el-color-primary-light-5);
}

.subscription-card.active {
  border-color: var(--el-color-primary);
  background: var(--el-color-primary-light-9);
}

.subscription-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.subscription-name {
  font-size: 16px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.subscription-code {
  font-size: 13px;
  color: var(--el-text-color-secondary);
}

.subscription-tip {
  max-width: 600px;
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

.subscription-card {
  cursor: pointer;
}

.subscription-icon {
  font-size: 32px;
  flex-shrink: 0;
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--el-fill-color-light);
  border-radius: 12px;
  transition: all 0.3s ease;
}

.subscription-card:hover .subscription-icon {
  transform: scale(1.1);
  background: var(--el-color-primary-light-8);
}

.subscription-card.active .subscription-icon {
  background: var(--el-color-primary-light-8);
}

.subscription-desc {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  line-height: 1.4;
}

.ai-detail-dialog :deep(.el-dialog__header) {
  padding: 20px 24px;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.ai-detail-dialog :deep(.el-dialog__body) {
  padding: 24px;
}

.ai-detail-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.ai-detail-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.ai-detail-title-row {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
  flex: 1;
}

.ai-detail-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.ai-detail-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.detail-section-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.detail-section-content {
  padding: 16px;
  background: var(--el-fill-color-lighter);
  border-radius: 8px;
  border-left: 3px solid var(--el-color-primary);
}

.detail-section-content p {
  margin: 0;
  color: var(--el-text-color-primary);
  font-size: 14px;
  line-height: 1.8;
}

.candidate-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.candidate-tag {
  font-size: 13px;
  padding: 4px 12px;
}

.ai-detail-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: 16px;
  border-top: 1px solid var(--el-border-color-lighter);
}

@media (max-width: 768px) {
  .page-container {
    padding: 0 16px 16px;
  }

  .header-content {
    padding: 24px 20px 20px;
  }

  .user-profile {
    flex-direction: column;
    text-align: center;
  }

  .user-name-row {
    justify-content: center;
    flex-wrap: wrap;
  }

  .user-tags {
    justify-content: center;
  }

  .quick-stats {
    padding: 16px;
  }

  .quick-stat-num {
    font-size: 22px;
  }

  .stats-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .entry-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .subscription-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
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
  .stats-grid {
    grid-template-columns: 1fr;
  }

  .entry-grid {
    grid-template-columns: 1fr;
  }

  .subscription-grid {
    grid-template-columns: 1fr;
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
