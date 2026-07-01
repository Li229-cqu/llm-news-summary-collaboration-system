<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
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
  type ReadingTimelineResponse,
  type SubscriptionCategory,
  getAIRecords,
  getBrowseHistory,
  getComments,
  getFavorites,
  getProfileOverview,
  getReadingTimeline,
  getReadingTrajectory,
  getSubscriptions,
  updateSubscriptions,
} from '@/api/profile'
import { unfavoriteNews } from '@/api/interaction'
import { unfavoritePost } from '@/api/community'
import { changePasswordApi, getUserProfileApi, updateUserProfileApi, uploadAvatarApi } from '@/api/user'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()

const activeTab = ref('insights')
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

// ===== 阅读洞察状态 =====
const selectedReadingDay = ref<string | null>(null)
const readingTimelineLoading = ref(false)
const readingTimelineData = ref<ReadingTimelineResponse | null>(null)

const matrixDays = computed(() => {
  if (!readingTimelineData.value) return []
  const dateMap = new Map<string, number>()
  for (const item of readingTimelineData.value.items) dateMap.set(item.date, item.total_reads)
  const maxReads = Math.max(...Array.from(dateMap.values()), 1)
  const days: { date: string; reads: number; level: number }[] = []
  const now = new Date()
  for (let i = 29; i >= 0; i--) {
    const d = new Date(now); d.setDate(d.getDate() - i)
    const key = d.toISOString().slice(0, 10)
    const reads = dateMap.get(key) || 0
    let level = 0
    if (reads > 0) { const r = reads / maxReads; level = r <= 0.25 ? 1 : r <= 0.5 ? 2 : r <= 0.75 ? 3 : 4 }
    days.push({ date: key, reads, level })
  }
  return days
})

const selectedDayInfo = computed(() => {
  if (!selectedReadingDay.value || !readingTimelineData.value) return null
  const item = readingTimelineData.value.items.find(i => i.date === selectedReadingDay.value)
  return item ? { date: selectedReadingDay.value, reads: item.total_reads } : null
})


// ===== 主题阅读星环图 =====
const ringLoading = ref(false)
const hoveredRingCategory = ref<string | null>(null)
const selectedRingCategory = ref<string | null>(null)
interface RingCategoryRaw { name: string; count: number; color: string; news: { id?: number; title: string; readAt: string }[] }
interface RingCategory extends RingCategoryRaw { _startDeg: number; _arcDeg: number }
const ringCategoriesRaw = ref<RingCategoryRaw[]>([])

const ringTotal = computed(() => ringCategoriesRaw.value.reduce((s, c) => s + c.count, 0))

const ringCategories = computed<RingCategory[]>(() => {
  const total = ringTotal.value
  let currentDeg = 0
  return ringCategoriesRaw.value.map(cat => {
    const arcDeg = total > 0 ? Math.max((cat.count / total) * 360, 24) : 0
    const result: RingCategory = { ...cat, _startDeg: currentDeg, _arcDeg: arcDeg }
    currentDeg += arcDeg
    return result
  })
})


interface RingNewsDot { id?: number; title: string; readAt: string; cx: number; cy: number; color: string; lineX1: number; lineY1: number; lineX2: number; lineY2: number }
const ringNewsDots = computed<RingNewsDot[]>(() => {
  const dots: RingNewsDot[] = []
  ringCategories.value.forEach(cat => {
    cat.news.forEach((n, ni) => {
      const angle = cat._startDeg + cat._arcDeg * (ni + 1) / (cat.news.length + 1)
      const inner = ringPolar(270, 270, 155, angle)
      const outer = ringPolar(270, 270, 200, angle)
      dots.push({ id: n.id, title: n.title, readAt: n.readAt, cx: outer.x, cy: outer.y, color: cat.color, lineX1: inner.x, lineY1: inner.y, lineX2: outer.x, lineY2: outer.y })
    })
  })
  return dots
})
function ringDegToRad(deg: number) { return (deg * Math.PI) / 180 }
function ringPolar(cx: number, cy: number, r: number, angleDeg: number) {
  const rad = ringDegToRad(angleDeg - 90)
  return { x: cx + r * Math.cos(rad), y: cy + r * Math.sin(rad) }
}
function ringArcPath(cx: number, cy: number, innerR: number, outerR: number, startDeg: number, endDeg: number): string {
  const gap = 3; const s = startDeg + gap / 2; const e = endDeg - gap / 2; if (e <= s) return ''
  const o1 = ringPolar(cx, cy, outerR, s); const o2 = ringPolar(cx, cy, outerR, e)
  const i1 = ringPolar(cx, cy, innerR, e); const i2 = ringPolar(cx, cy, innerR, s)
  const large = (e - s) > 180 ? 1 : 0
  return `M ${o1.x} ${o1.y} A ${outerR} ${outerR} 0 ${large} 1 ${o2.x} ${o2.y} L ${i1.x} ${i1.y} A ${innerR} ${innerR} 0 ${large} 0 ${i2.x} ${i2.y} Z`
}

async function loadRingData() {
  ringLoading.value = true
  try {
    const trajectory = await getReadingTrajectory({ days: 30, limit: 80 })
    const newsList = (trajectory as any).recent_news || []
    const catMap = new Map<string, { count: number; news: { id?: number; title: string; readAt: string }[] }>()
    newsList.forEach((n: any) => {
      const cat = n.category_name || '未分类'
      if (!catMap.has(cat)) catMap.set(cat, { count: 0, news: [] })
      const entry = catMap.get(cat)!
      entry.count++
      if (entry.news.length < 3) entry.news.push({ id: n.news_id, title: (n.title || '').slice(0, 16), readAt: n.browse_time || '' })
    })
    const sorted = Array.from(catMap.entries()).sort((a, b) => b[1].count - a[1].count).slice(0, 5)
    const colors = ['#3b82f6', '#6366f1', '#8b5cf6', '#06b6d4', '#0ea5e9']
    ringCategoriesRaw.value = sorted.map(([name, data], i) => ({ name, count: data.count, color: colors[i] || '#94a3b8', news: data.news }))
  } catch { ringCategoriesRaw.value = [] }
  finally { ringLoading.value = false }
}

const behaviorTotal = computed(() => {
  const overview = profileOverview.value
  if (!overview) return 0
  return (overview.browse_count || 0) + (overview.favorite_count || 0) + (overview.comment_count || 0) + (overview.ai_generate_count || 0)
})

const behaviorRingSegments = computed(() => {
  const overview = profileOverview.value
  if (!overview || behaviorTotal.value === 0) return []
  const total = behaviorTotal.value
  return [
    { key: 'history' as const, label: '浏览', count: overview.browse_count, pct: Math.round((overview.browse_count / total) * 100), color: '#3b82f6' },
    { key: 'favorites' as const, label: '收藏', count: overview.favorite_count, pct: Math.round((overview.favorite_count / total) * 100), color: '#f59e0b' },
    { key: 'comments' as const, label: '评论', count: overview.comment_count, pct: Math.round((overview.comment_count / total) * 100), color: '#10b981' },
    { key: 'ai-records' as const, label: 'AI生成', count: overview.ai_generate_count, pct: Math.round((overview.ai_generate_count / total) * 100), color: '#8b5cf6' },
  ]
})

const behaviorConicGradient = computed(() => {
  if (behaviorRingSegments.value.length === 0) return 'conic-gradient(#e5e7eb 0deg 360deg)'
  let acc = 0
  const parts = behaviorRingSegments.value.map((s) => {
    const start = acc
    acc += (s.count / behaviorTotal.value) * 360
    return `${s.color} ${start.toFixed(1)}deg ${acc.toFixed(1)}deg`
  })
  return `conic-gradient(${parts.join(', ')})`
})

async function loadReadingInsights() {
  readingTimelineLoading.value = true
  try {
    readingTimelineData.value = await getReadingTimeline({ days: 30 })
  } catch {
    readingTimelineData.value = null
  } finally {
    readingTimelineLoading.value = false
  }
}

function handleBehaviorSegmentClick(tabKey: string) {
  handleStatCardClick(tabKey)
}

function handleResize() {}
onBeforeUnmount(() => { window.removeEventListener('resize', handleResize) })

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

const profileNavItems = [
  { key: 'insights', label: '阅读洞察', icon: Grid, desc: '活跃、行为与主题脉络' },
  { key: 'history', label: '浏览记录', icon: Clock, desc: '新闻与帖子足迹' },
  { key: 'favorites', label: '收藏记录', icon: Star, desc: '保存的新闻与帖子' },
  { key: 'comments', label: '评论记录', icon: ChatDotRound, desc: '你的互动发言' },
  { key: 'ai-records', label: 'AI 生成记录', icon: MagicStick, desc: '标题摘要历史' },
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

// ===== 浏览分类胶囊比例条 =====
interface CategorySegment { name: string; count: number; pct: number }
const catSegmentColors = ['#3b82f6', '#6366f1', '#8b5cf6', '#06b6d4', '#0ea5e9', '#94a3b8']
const browseCapsuleLoading = ref(false)
const newsCapsuleItems = ref<BrowseHistoryItem[]>([])
const postCapsuleItems = ref<BrowseHistoryItem[]>([])

function buildCategorySegments(items: BrowseHistoryItem[], defaultLabel: string): CategorySegment[] {
  const catMap = new Map<string, number>()
  let total = 0
  items.forEach(item => {
    const cat = (item as any).category_name || defaultLabel
    catMap.set(cat, (catMap.get(cat) || 0) + 1)
    total++
  })
  if (total === 0) return []
  const sorted = Array.from(catMap.entries()).sort((a, b) => b[1] - a[1])
  const top = sorted.slice(0, 5)
  const result = top.map(([name, count]) => ({ name, count, pct: Math.round((count / total) * 100) }))
  if (sorted.length > 5) {
    const otherCount = sorted.slice(5).reduce((s, [, c]) => s + c, 0)
    result.push({ name: '其他', count: otherCount, pct: Math.round((otherCount / total) * 100) })
  }
  return result
}

const newsCategorySegments = computed(() => buildCategorySegments(newsCapsuleItems.value, '未分类新闻'))
const postCategorySegments = computed(() => buildCategorySegments(postCapsuleItems.value, '帖子浏览'))

async function loadBrowseCapsuleData() {
  browseCapsuleLoading.value = true
  try {
    const [newsRes, postRes] = await Promise.all([
      getBrowseHistory(1, 50, 'news'),
      getBrowseHistory(1, 50, 'post'),
    ])
    newsCapsuleItems.value = (newsRes as any).list || []
    postCapsuleItems.value = (postRes as any).list || []
  } catch {
    newsCapsuleItems.value = []
    postCapsuleItems.value = []
  } finally {
    browseCapsuleLoading.value = false
  }
}

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
    loadBrowseCapsuleData()
  } else if (key === 'favorites') {
    loadFavorites()
  } else if (key === 'comments') {
    loadComments()
  } else if (key === 'ai-records') {
    loadAIRecords()
  }
}

function handleNavClick(key: string) {
  if (key === activeTab.value) return
  activeTab.value = key
  browseSearchKeyword.value = ''
  favoriteSearchKeyword.value = ''
  commentSearchKeyword.value = ''
  aiSearchKeyword.value = ''
  currentPage.value = 1
  if (key === 'history') {
    loadBrowseHistory()
    loadBrowseCapsuleData()
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
      loadBrowseCapsuleData()
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
  // Load reading insights (non-blocking)
  loadReadingInsights()
  loadRingData()
  window.addEventListener('resize', handleResize)
})
</script>

<template>
  <main class="profile-page">
    <!-- ===== 左侧个人中心栏 ===== -->
    <aside class="profile-sidebar">
      <div class="sidebar-user-card">
        <div class="sidebar-avatar-col">
          <el-avatar :size="88" :src="normalizeAvatarUrl(userStore.userInfo?.avatar)" :icon="User" class="sidebar-avatar">
            {{ userStore.userInfo?.nickname?.charAt(0) || '用' }}
          </el-avatar>
        </div>
        <div class="sidebar-user-name">{{ userStore.userInfo?.nickname || '未登录用户' }}</div>
        <div class="sidebar-user-role">
          <el-tag :type="userStore.isAdmin ? 'danger' : userStore.isEditor ? 'warning' : 'info'" effect="dark" round size="small">
            {{ userStore.isAdmin ? '管理员' : userStore.isEditor ? '审核/编辑' : '普通用户' }}
          </el-tag>
        </div>
        <div class="sidebar-user-meta">
          <span>ID: {{ userStore.userInfo?.id || '-' }}</span>
          <span v-if="(userStore.userInfo as any)?.email">{{ (userStore.userInfo as any)?.email }}</span>
        </div>
        <div class="sidebar-user-tags">
          <el-tag v-for="tag in readingTags" :key="tag" size="small" effect="plain" class="sidebar-reading-tag" :type="tag === '新用户' ? 'info' : ''">
            {{ tag }}
          </el-tag>
        </div>
        <div class="sidebar-user-stats">
          <div class="sidebar-stat-item" @click="handleStatCardClick('history')">
            <span class="sidebar-stat-num">{{ profileOverview?.browse_count ?? 0 }}</span>
            <span class="sidebar-stat-lbl">浏览</span>
          </div>
          <div class="sidebar-stat-item" @click="handleStatCardClick('favorites')">
            <span class="sidebar-stat-num">{{ profileOverview?.favorite_count ?? 0 }}</span>
            <span class="sidebar-stat-lbl">收藏</span>
          </div>
          <div class="sidebar-stat-item" @click="handleStatCardClick('comments')">
            <span class="sidebar-stat-num">{{ profileOverview?.comment_count ?? 0 }}</span>
            <span class="sidebar-stat-lbl">评论</span>
          </div>
          <div class="sidebar-stat-item" @click="handleStatCardClick('ai-records')">
            <span class="sidebar-stat-num">{{ profileOverview?.ai_generate_count ?? 0 }}</span>
            <span class="sidebar-stat-lbl">AI</span>
          </div>
        </div>
        <el-button class="sidebar-edit-btn" :icon="Edit" size="small" @click="openEditDialog()">编辑资料</el-button>
      </div>

      <nav class="sidebar-nav">
        <div class="sidebar-nav-title">导航</div>
        <div
          v-for="item in profileNavItems"
          :key="item.key"
          class="sidebar-nav-item"
          :class="{ 'sidebar-nav-item--active': activeTab === item.key }"
          @click="handleNavClick(item.key)"
        >
          <el-icon :size="18"><component :is="item.icon" /></el-icon>
          <span class="sidebar-nav-label">{{ item.label }}</span>
        </div>
      </nav>
    </aside>

    <!-- ===== 右侧主内容区 ===== -->
    <section class="profile-main-panel">
      <div class="profile-module-body">

        <!-- ===== 阅读洞察模块 ===== -->
        <div v-if="activeTab === 'insights'" class="module-content">
          <div class="module-header">
            <h2 class="module-title"><el-icon><Grid /></el-icon> 阅读洞察</h2>
            <p class="module-desc">基于浏览、收藏、评论和AI生成记录，分析你的阅读活跃度、行为偏好与主题脉络</p>
          </div>
          <!-- 上排：矩阵 + 能量环 -->
          <div class="insights-top-row">
            <div class="portrait-card">
              <div class="portrait-card__header">
                <span class="portrait-card__title"><el-icon><Files /></el-icon> 近 30 天阅读活跃矩阵</span>
              </div>
              <div class="portrait-card__body">
                <el-skeleton v-if="readingTimelineLoading" :rows="3" animated />
                <div v-else-if="!readingTimelineData || matrixDays.length === 0" class="portrait-empty">
                  <span class="portrait-empty__text">暂无阅读记录</span>
                </div>
                <div v-else class="activity-matrix">
                  <div class="matrix-grid">
                    <div
                      v-for="day in matrixDays"
                      :key="day.date"
                      class="matrix-cell"
                      :class="[`heat-${day.level}`, { 'matrix-cell--selected': selectedReadingDay === day.date }]"
                      :title="`${day.date}: ${day.reads} 次阅读`"
                      @click="selectedReadingDay = selectedReadingDay === day.date ? null : day.date"
                    ></div>
                  </div>
                  <div class="heatmap-footer">
                    <span v-if="selectedDayInfo" class="heatmap-selected-info">{{ selectedDayInfo.date }} · 阅读 {{ selectedDayInfo.reads }} 篇</span>
                    <span v-else class="heatmap-hint">点击日期查看当天活跃情况</span>
                    <div class="heatmap-legend">
                      <span class="legend-label">少</span>
                      <span class="legend-dot heat-0"></span><span class="legend-dot heat-1"></span><span class="legend-dot heat-2"></span><span class="legend-dot heat-3"></span><span class="legend-dot heat-4"></span>
                      <span class="legend-label">多</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div class="portrait-card">
              <div class="portrait-card__header">
                <span class="portrait-card__title"><el-icon><Setting /></el-icon> 行为能量环</span>
              </div>
              <div class="portrait-card__body">
                <div v-if="behaviorTotal === 0" class="portrait-empty">
                  <span class="portrait-empty__text">暂无行为数据</span>
                  <span class="portrait-empty__hint">开始你的第一次阅读吧</span>
                </div>
                <div v-else class="behavior-ring-wrap">
                  <div class="ring-chart" :style="{ background: behaviorConicGradient }">
                    <div class="ring-center">
                      <span class="ring-total">{{ behaviorTotal }}</span>
                      <span class="ring-label">总行为</span>
                    </div>
                  </div>
                  <div class="ring-legend">
                    <div v-for="seg in behaviorRingSegments" :key="seg.key" class="ring-legend-item" @click="handleBehaviorSegmentClick(seg.key)">
                      <span class="legend-dot" :style="{ background: seg.color }"></span>
                      <span class="legend-name">{{ seg.label }}</span>
                      <span class="legend-count">{{ seg.count }}</span>
                      <span class="legend-pct">{{ seg.pct }}%</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <!-- 下排：主题阅读星环图 -->
          <div class="portrait-card ring-card">
            <div class="portrait-card__header">
              <span class="portrait-card__title"><el-icon><View /></el-icon> 主题阅读星环</span>
              <span class="ring-subtitle">基于近30天浏览记录，展示你的高频阅读分类及其代表新闻</span>
            </div>
            <div class="portrait-card__body">
              <el-skeleton v-if="ringLoading" :rows="4" animated />
              <div v-else-if="ringCategories.length === 0" class="portrait-empty">
                <span class="portrait-empty__text">暂无足够阅读脉络数据</span>
                <span class="portrait-empty__hint">浏览更多新闻后，将生成你的主题阅读星环</span>
              </div>
              <div v-else class="ring-container">
                <svg viewBox="0 0 540 540" class="ring-svg">
                  <line v-for="(cat, ci) in ringCategories" :key="'cl-'+ci" :x1="270" :y1="270" :x2="ringPolar(270,270,133,cat._startDeg + cat._arcDeg/2).x" :y2="ringPolar(270,270,133,cat._startDeg + cat._arcDeg/2).y" stroke="#cbd5e1" stroke-width="1" opacity="0.4" />
                  <path v-for="(cat, ci) in ringCategories" :key="'seg-'+ci" :d="ringArcPath(270, 270, 112, 154, cat._startDeg, cat._startDeg + cat._arcDeg)" :fill="cat.color" :opacity="hoveredRingCategory === cat.name ? 1 : 0.85" style="cursor: pointer; transition: opacity 0.2s" @mouseenter="hoveredRingCategory = cat.name" @mouseleave="hoveredRingCategory = null" @click="selectedRingCategory = selectedRingCategory === cat.name ? null : cat.name" />
                  <line v-for="(dot, di) in ringNewsDots" :key="'nl-'+di" :x1="dot.lineX1" :y1="dot.lineY1" :x2="dot.lineX2" :y2="dot.lineY2" :stroke="dot.color" stroke-width="1" opacity="0.3" />
                  <circle v-for="(dot, di) in ringNewsDots" :key="'nd-'+di" :cx="dot.cx" :cy="dot.cy" r="6" :fill="dot.color" opacity="0.8" :style="{ cursor: dot.id ? 'pointer' : 'default' }" @click="dot.id ? router.push(`/news/${dot.id}`) : null"><title>{{ dot.title }} · {{ dot.readAt }}</title></circle>
                  <circle cx="270" cy="270" r="50" fill="#fff" stroke="#e5e7eb" stroke-width="2" />
                  <text x="270" y="262" text-anchor="middle" font-size="14" font-weight="700" fill="#1e293b">我的阅读</text>
                  <text x="270" y="282" text-anchor="middle" font-size="12" fill="#94a3b8">近30天 {{ ringTotal }} 条</text>
                </svg>
                <!-- 详情卡片 -->
                <div class="ring-detail">
                  <div v-if="selectedRingCategory" class="ring-detail-card">
                    <span class="ring-detail-name">{{ selectedRingCategory }}</span>
                    <span class="ring-detail-stat">阅读 {{ ringCategories.find(c => c.name === selectedRingCategory)?.count || 0 }} 条</span>
                    <div v-if="ringCategories.find(c => c.name === selectedRingCategory)?.news.length" class="ring-detail-news">
                      <div v-for="(n, ni) in ringCategories.find(c => c.name === selectedRingCategory)?.news" :key="ni" class="ring-detail-news-item" @click="n.id ? router.push(`/news/${n.id}`) : null" :style="{ cursor: n.id ? 'pointer' : 'default' }">
                        <span>{{ n.title }}</span><span class="ring-detail-time">{{ n.readAt }}</span>
                      </div>
                    </div>
                  </div>
                  <span v-else class="ring-detail-hint">悬停或点击分类色块，查看阅读脉络详情</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- ===== 记录模块 ===== -->
        <div v-else class="module-content">
          <div class="module-header">
            <h2 class="module-title">
              <el-icon><component :is="profileNavItems.find(i => i.key === activeTab)?.icon || Clock" /></el-icon>
              {{ profileNavItems.find(i => i.key === activeTab)?.label || '' }}
            </h2>
            <p class="module-desc">{{ profileNavItems.find(i => i.key === activeTab)?.desc || '' }}</p>
          </div>

          <div v-if="loadingTab === activeTab" class="loading-container">
            <el-skeleton :rows="6" animated />
          </div>

          <template v-else-if="activeTab === 'history'">
            <!-- ===== 浏览分类胶囊比例条 ===== -->
            <div class="browse-capsule-panel">
              <div v-if="browseCapsuleLoading" class="capsule-loading">
                <el-skeleton :rows="2" animated />
              </div>
              <div class="capsule-row">
                <span class="capsule-title">新闻浏览分类分布</span>
                <span class="capsule-subtitle">基于最近浏览记录样本统计</span>
                <div v-if="newsCategorySegments.length > 0" class="capsule-bar-wrap">
                  <div class="capsule-bar">
                    <div
                      v-for="(seg, idx) in newsCategorySegments"
                      :key="seg.name"
                      class="capsule-seg"
                      :style="{ width: seg.pct + '%', background: catSegmentColors[idx] || '#94a3b8' }"
                      :title="`${seg.name}: ${seg.count} 条 (${seg.pct}%)`"
                    ></div>
                  </div>
                  <div class="capsule-legend">
                    <span v-for="(seg, idx) in newsCategorySegments" :key="seg.name" class="capsule-legend-item">
                      <span class="capsule-dot" :style="{ background: catSegmentColors[idx] || '#94a3b8' }"></span>
                      {{ seg.name }} {{ seg.count }} 条 {{ seg.pct }}%
                    </span>
                  </div>
                </div>
                <div v-else class="capsule-empty">暂无新闻浏览分类数据</div>
              </div>
              <div class="capsule-row">
                <span class="capsule-title">帖子浏览标签分布</span>
                <span class="capsule-subtitle">基于当前已加载浏览记录统计</span>
                <div v-if="postCategorySegments.length > 0" class="capsule-bar-wrap">
                  <div class="capsule-bar">
                    <div
                      v-for="(seg, idx) in postCategorySegments"
                      :key="seg.name"
                      class="capsule-seg"
                      :style="{ width: seg.pct + '%', background: catSegmentColors[idx] || '#94a3b8' }"
                      :title="`${seg.name}: ${seg.count} 条 (${seg.pct}%)`"
                    ></div>
                  </div>
                  <div class="capsule-legend">
                    <span v-for="(seg, idx) in postCategorySegments" :key="seg.name" class="capsule-legend-item">
                      <span class="capsule-dot" :style="{ background: catSegmentColors[idx] || '#94a3b8' }"></span>
                      {{ seg.name }} {{ seg.count }} 条 {{ seg.pct }}%
                    </span>
                  </div>
                </div>
                <div v-else class="capsule-empty">暂无帖子浏览标签数据</div>
              </div>
            </div>

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

          <template v-else-if="activeTab === 'favorites'">
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

          <template v-else-if="activeTab === 'comments'">
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

          <template v-else-if="activeTab === 'ai-records'">
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

        </div>
      </div>
    </section>

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
/* ===== 全屏工作台 ===== */
.profile-page {
  height: calc(100vh - 64px);
  overflow: hidden;
  display: grid;
  grid-template-columns: 300px minmax(0, 1fr);
  background: #f5f7fb;
}

/* ===== 左侧个人中心栏 ===== */
.profile-sidebar {
  height: 100%;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  padding: 24px 18px;
  background: #fff;
  border-right: 1px solid #e5e7eb;
  gap: 20px;
}

.sidebar-user-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 28px 16px 20px;
  background: linear-gradient(180deg, #eef2ff 0%, #f8fafc 50%, #fff 100%);
  border-radius: 18px;
  border: 1px solid #e0e7ff;
  gap: 12px;
}

.sidebar-avatar-col {
  flex-shrink: 0;
}

.sidebar-avatar {
  border: 4px solid #fff;
  box-shadow: 0 4px 20px rgba(37, 99, 235, 0.2), 0 0 0 2px #bfdbfe;
}

.sidebar-user-name {
  font-size: 20px;
  font-weight: 700;
  color: #1e293b;
  line-height: 1.2;
}

.sidebar-user-role {
  margin-bottom: 4px;
}

.sidebar-user-meta {
  display: flex;
  flex-direction: column;
  gap: 3px;
  font-size: 13px;
  color: #64748b;
}

.sidebar-user-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  justify-content: center;
}

.sidebar-reading-tag {
  font-size: 12px;
}

.sidebar-user-stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 6px;
  width: 100%;
}

.sidebar-stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 8px 4px;
  border-radius: 10px;
  cursor: pointer;
  transition: background 0.2s;
  background: #f8fafc;
}

.sidebar-stat-item:hover {
  background: #eff6ff;
}

.sidebar-stat-num {
  font-size: 18px;
  font-weight: 700;
  color: #2563eb;
  line-height: 1.2;
}

.sidebar-stat-lbl {
  font-size: 12px;
  color: #64748b;
}

.sidebar-edit-btn {
  width: 100%;
  border-radius: 10px;
  height: 36px;
}

.sidebar-nav {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
  overflow-y: auto;
}

.sidebar-nav-title {
  font-size: 11px;
  font-weight: 600;
  color: #94a3b8;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  padding: 4px 8px 8px;
}

.sidebar-nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
  color: #64748b;
}

.sidebar-nav-item:hover {
  background: #f1f5f9;
  color: #2563eb;
}

.sidebar-nav-item--active {
  background: #eff6ff;
  color: #2563eb;
  font-weight: 600;
  border: 1px solid #bfdbfe;
}

.sidebar-nav-label {
  font-size: 14px;
}

/* ===== 右侧主内容区 ===== */
.profile-main-panel {
  height: 100%;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.profile-module-body {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

.module-header {
  margin-bottom: 20px;
}

.module-title {
  margin: 0 0 4px;
  font-size: 20px;
  font-weight: 700;
  color: #1e293b;
  display: flex;
  align-items: center;
  gap: 8px;
}

.module-desc {
  margin: 0;
  font-size: 13px;
  color: #94a3b8;
}

.module-content {
  height: 100%;
}

/* ===== 模块内统计小卡片 ===== */
.module-stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-bottom: 24px;
}

.module-stat-card {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 16px;
  background: #f8fafc;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.module-stat-card:hover {
  background: #f0f5ff;
  border-color: #bfdbfe;
}

.module-stat-card--active {
  background: #eff6ff;
  border-color: #2563eb;
}

.module-stat-card__icon {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: #eff6ff;
  color: #2563eb;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.module-stat-card__body {
  display: flex;
  flex-direction: column;
}

.module-stat-card__num {
  font-size: 20px;
  font-weight: 700;
  color: #1e293b;
  line-height: 1.2;
}

.module-stat-card__lbl {
  font-size: 12px;
  color: #94a3b8;
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

/* ===== 头像包装 ===== */
.avatar-wrapper {
  position: relative;
  flex-shrink: 0;
}

.user-avatar {
  border: 4px solid rgba(255, 255, 255, 0.95);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.2);
}

/* ===== 阅读画像区（insights 模块内） ===== */
.reading-portrait {
  margin-top: 0;
}

.portrait-header-right {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 16px;
}

.portrait-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.portrait-card {
  border: 1px solid #e5e7eb;
  border-radius: 14px;
  overflow: hidden;
  background: #fff;
  transition: box-shadow 0.3s ease;
}

.portrait-card:hover {
  box-shadow: 0 4px 16px rgba(15, 23, 42, 0.06);
}

.portrait-card__header {
  padding: 14px 18px 10px;
  border-bottom: 1px solid #f1f5f9;
}

.portrait-card__title {
  font-size: 14px;
  font-weight: 600;
  color: #475569;
  display: flex;
  align-items: center;
  gap: 6px;
}

.portrait-card__body {
  padding: 16px 18px;
  min-height: 220px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.portrait-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  color: #94a3b8;
}

.portrait-empty__icon {
  font-size: 32px;
}

.portrait-empty__text {
  font-size: 14px;
  font-weight: 500;
  color: #64748b;
}

.portrait-empty__hint {
  font-size: 12px;
  color: #cbd5e1;
}

/* -- 阅读洞察矩阵 + 星轨 -- */
.insights-top-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 16px;
}

.activity-matrix {
  display: flex;
  flex-direction: column;
  gap: 12px;
  align-items: center;
}

.matrix-grid {
  display: grid;
  grid-template-columns: repeat(6, 36px);
  grid-template-rows: repeat(5, 36px);
  gap: 8px;
}

.matrix-cell {
  border-radius: 10px;
  cursor: pointer;
  transition: transform 0.15s, outline 0.1s;
}

.matrix-cell:hover { transform: scale(1.15); z-index: 1; }
.matrix-cell--selected { outline: 2.5px solid #4338ca; }

.heat-0 { background: #f1f5f9; }
.heat-1 { background: #e0e7ff; }
.heat-2 { background: #a5b4fc; }
.heat-3 { background: #6366f1; }
.heat-4 { background: #4338ca; }

.ring-card { margin-top: 0; }
.ring-subtitle { font-size: 12px; color: #94a3b8; margin-left: 8px; }
.ring-container { display: flex; gap: 16px; align-items: flex-start; }
.ring-svg { width: 300px; height: 300px; flex-shrink: 0; }
.ring-detail { flex: 1; min-width: 0; padding-top: 8px; }
.ring-detail-card { display: flex; flex-direction: column; gap: 8px; }
.ring-detail-name { font-size: 15px; font-weight: 700; color: #1e293b; }
.ring-detail-stat { font-size: 13px; color: #64748b; }
.ring-detail-news { display: flex; flex-direction: column; gap: 6px; margin-top: 4px; }
.ring-detail-news-item { display: flex; justify-content: space-between; align-items: center; font-size: 13px; color: #475569; padding: 6px 8px; background: #f8fafc; border-radius: 6px; }
.ring-detail-news-item:hover { background: #eff6ff; }
.ring-detail-time { font-size: 11px; color: #94a3b8; flex-shrink: 0; }
.ring-detail-hint { font-size: 13px; color: #cbd5e1; }

@media (max-width: 768px) {
  .insights-top-row { grid-template-columns: 1fr; }
  .matrix-grid { grid-template-columns: repeat(6, 28px); grid-template-rows: repeat(5, 28px); gap: 6px; }
  .ring-container { flex-direction: column; align-items: center; }
  .ring-svg { width: 260px; height: 260px; }
}

/* -- 旧热力图样式保留用于兼容 -- */
.activity-calendar {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.heatmap-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.heatmap-title {
  font-size: 14px;
  font-weight: 600;
  color: #475569;
}

.heatmap-grid-wrap {
  --cell-size: 24px;
  --cell-gap: 6px;
  --cell-radius: 5px;
  display: flex;
  gap: 8px;
  justify-content: center;
  width: 100%;
}

.heatmap-grid-wrap.range-30 {
  --cell-size: 28px;
  --cell-gap: 7px;
  --cell-radius: 6px;
}

.heatmap-grid-wrap.range-60 {
  --cell-size: 23px;
  --cell-gap: 5px;
  --cell-radius: 5px;
}

.heatmap-y-labels {
  display: flex;
  flex-direction: column;
  gap: var(--cell-gap);
  padding-top: 22px;
  flex-shrink: 0;
}

.heatmap-y-labels span {
  height: var(--cell-size);
  font-size: 11px;
  color: #94a3b8;
  line-height: var(--cell-size);
  display: flex;
  align-items: center;
}

.heatmap-scroll {
  flex: 1;
  overflow-x: auto;
  padding-bottom: 2px;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.heatmap-months {
  display: grid;
  margin-bottom: 5px;
  width: 100%;
}

.heatmap-month-label {
  font-size: 11px;
  color: #94a3b8;
  white-space: nowrap;
}

.heatmap-board {
  display: flex;
  justify-content: center;
}

.heatmap-weeks {
  display: grid;
  grid-auto-flow: column;
  gap: var(--cell-gap);
}

.heatmap-cell {
  width: var(--cell-size);
  height: var(--cell-size);
  border-radius: var(--cell-radius);
  cursor: pointer;
  transition: outline 0.1s, transform 0.1s;
  outline: 1px solid rgba(255,255,255,0.7);
}

.heatmap-cell:hover {
  outline: 2px solid #6366f1;
  transform: scale(1.1);
  z-index: 1;
}

.heat-selected {
  outline: 2.5px solid #4338ca !important;
}

.heat-empty { background: transparent; outline: none; cursor: default; }

/* 蓝紫色热力 */
.heat-0 { background: #f1f5f9; }
.heat-1 { background: #e0e7ff; }
.heat-2 { background: #a5b4fc; }
.heat-3 { background: #6366f1; }
.heat-4 { background: #4338ca; }

.heatmap-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 8px;
}

.heatmap-selected-info {
  font-size: 12px;
  color: #4338ca;
  font-weight: 500;
}

.heatmap-hint {
  font-size: 11px;
  color: #cbd5e1;
}

.heatmap-legend {
  display: flex;
  align-items: center;
  gap: 3px;
  margin-left: auto;
}

.legend-label {
  font-size: 10px;
  color: #94a3b8;
}

.legend-dot {
  width: 12px;
  height: 12px;
  border-radius: 3px;
}

.legend-dot.heat-0 { background: #f1f5f9; }
.legend-dot.heat-1 { background: #e0e7ff; }
.legend-dot.heat-2 { background: #a5b4fc; }
.legend-dot.heat-3 { background: #6366f1; }
.legend-dot.heat-4 { background: #4338ca; }

/* -- 兴趣雷达 -- */
.radar-chart {
  width: 100%;
  height: 300px;
  min-height: 260px;
}

/* -- 行为能量环 -- */
.behavior-ring-wrap {
  display: flex;
  align-items: center;
  gap: 24px;
  width: 100%;
  justify-content: center;
}

.ring-chart {
  width: 150px;
  height: 150px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.ring-center {
  width: 90px;
  height: 90px;
  border-radius: 50%;
  background: #fff;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}

.ring-total {
  font-size: 26px;
  font-weight: 700;
  color: #1e293b;
  line-height: 1.1;
}

.ring-label {
  font-size: 11px;
  color: #94a3b8;
}

.ring-legend {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.ring-legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 6px;
  transition: background 0.2s ease;
}

.ring-legend-item:hover {
  background: #f1f5f9;
}

.legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

.legend-name {
  font-size: 13px;
  color: #475569;
  width: 40px;
}

.legend-count {
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
}

.legend-pct {
  font-size: 12px;
  color: #94a3b8;
}

/* -- AI 使用洞察 -- */
.ai-insight {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.ai-insight__total {
  display: flex;
  align-items: baseline;
  gap: 8px;
}

.ai-insight__big-num {
  font-size: 32px;
  font-weight: 700;
  color: #8b5cf6;
}

.ai-insight__big-label {
  font-size: 14px;
  color: #64748b;
}

.ai-insight__bars {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.ai-bar-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.ai-bar-label {
  font-size: 12px;
  color: #64748b;
  width: 56px;
  flex-shrink: 0;
}

.ai-bar-track {
  flex: 1;
  height: 10px;
  background: #f1f5f9;
  border-radius: 5px;
  overflow: hidden;
}

.ai-bar-fill {
  height: 100%;
  border-radius: 5px;
  transition: width 0.6s ease;
}

.ai-bar-fill.news { background: #3b82f6; }
.ai-bar-fill.manual { background: #8b5cf6; }

.ai-bar-val {
  font-size: 13px;
  font-weight: 600;
  color: #1e293b;
  width: 24px;
  text-align: right;
}

.ai-insight__risk {
  display: flex;
  align-items: center;
  gap: 10px;
}

.risk-label {
  font-size: 12px;
  color: #64748b;
}

.risk-tags {
  display: flex;
  gap: 6px;
}

.ai-insight__last {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
}

.last-label {
  color: #94a3b8;
  flex-shrink: 0;
}

.last-title {
  color: #64748b;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* ===== 浏览分类胶囊比例条 ===== */
.browse-capsule-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-bottom: 20px;
}

.capsule-row {
  padding: 14px 16px;
  background: #f8fafc;
  border-radius: 14px;
  border: 1px solid #e5e7eb;
}

.capsule-title {
  font-size: 13px;
  font-weight: 600;
  color: #475569;
  margin-right: 10px;
}

.capsule-subtitle {
  font-size: 11px;
  color: #94a3b8;
}

.capsule-bar-wrap {
  margin-top: 10px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.capsule-bar {
  display: flex;
  height: 16px;
  border-radius: 8px;
  overflow: hidden;
  gap: 2px;
}

.capsule-seg {
  transition: filter 0.2s;
  cursor: default;
}

.capsule-seg:hover {
  filter: brightness(1.15);
}

.capsule-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.capsule-legend-item {
  font-size: 12px;
  color: #64748b;
  display: flex;
  align-items: center;
  gap: 3px;
}

.capsule-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.capsule-empty {
  margin-top: 8px;
  font-size: 12px;
  color: #cbd5e1;
}

/* ===== 内容 Tab 区域 ===== */

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

@media (max-width: 900px) {
  .profile-page {
    grid-template-columns: 1fr;
    height: auto;
    overflow: visible;
  }

  .profile-sidebar {
    height: auto;
    flex-direction: column;
    gap: 12px;
    padding: 16px;
    border-right: none;
    border-bottom: 1px solid #e5e7eb;
  }

  .sidebar-user-card {
    flex-direction: row;
    flex-wrap: wrap;
    justify-content: center;
    gap: 12px;
    padding: 14px;
  }

  .sidebar-user-stats {
    width: auto;
    gap: 12px;
  }

  .sidebar-nav {
    flex-direction: row;
    flex-wrap: wrap;
    gap: 4px;
    overflow-x: auto;
  }

  .sidebar-nav-title {
    display: none;
  }

  .sidebar-nav-item {
    flex-shrink: 0;
    padding: 6px 10px;
  }

  .profile-main-panel {
    height: auto;
    overflow: visible;
  }

  .profile-module-body {
    overflow-y: visible;
    padding: 16px;
  }

  .module-stats-row {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .heatmap-grid-wrap { --cell-size: 18px; --cell-gap: 4px; }
  .heatmap-grid-wrap.range-30 { --cell-size: 22px; --cell-gap: 5px; }
  .heatmap-grid-wrap.range-60 { --cell-size: 18px; --cell-gap: 4px; }

  .portrait-grid {
    grid-template-columns: 1fr;
  }

  .behavior-ring-wrap {
    flex-direction: column;
    align-items: center;
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
  .module-stats-row {
    grid-template-columns: 1fr;
  }

  .portrait-grid {
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
