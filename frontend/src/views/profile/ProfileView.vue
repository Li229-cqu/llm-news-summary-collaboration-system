<script setup lang="ts">
import { computed, nextTick, onActivated, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
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
  type WeeklyReportResponse,
  getAIRecords,
  getBrowseHistory,
  getComments,
  getFavorites,
  getProfileOverview,
  getSubscriptions,
  getWeeklyReport,
  updateSubscriptions,
} from '@/api/profile'
import { unfavoriteNews } from '@/api/interaction'
import { unfavoritePost } from '@/api/community'
import { changePasswordApi, getUserProfileApi, updateUserProfileApi, uploadAvatarApi } from '@/api/user'
import { useNavigationStateStore } from '@/stores/navigationState'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const navStore = useNavigationStateStore()

function saveProfileRoute() {
  navStore.saveProfileState({ routePath: route.fullPath, activeTab: activeTab.value })
}

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

// ===== 阅读报告 / 每周报告状态 =====
const weeklyReport = ref<WeeklyReportResponse | null>(null)
const weeklyReportLoading = ref(false)
const weeklyReportError = ref('')

// AI 来源标签
const aiSourceLabel = computed(() => {
  if (!weeklyReport.value?.ai_analysis?.enabled) return ''
  const s = weeklyReport.value.ai_analysis.source
  if (s === 'llm' || s === 'cache') return 'AI 生成'
  if (s === 'fallback') return '规则生成'
  return ''
})

async function loadWeeklyReport() {
  weeklyReportLoading.value = true
  weeklyReportError.value = ''
  try {
    weeklyReport.value = await getWeeklyReport()
  } catch (e: any) {
    weeklyReportError.value = e?.response?.data?.message || e?.message || '加载阅读报告失败'
    weeklyReport.value = null
  } finally {
    weeklyReportLoading.value = false
  }
}

// ===== 阅读报告辅助 computed =====
const topicBarColors = ['#d92d20', '#e53935', '#c62828', '#ef5350', '#b71c1c', '#94a3b8']

const maxDailyCount = computed(() => {
  if (!weeklyReport.value) return 1
  return Math.max(...weeklyReport.value.daily_activity.map(d => d.count), 1)
})

const mostActiveDate = computed(() => {
  if (!weeklyReport.value) return ''
  let max = 0, date = ''
  weeklyReport.value.daily_activity.forEach(d => { if (d.count > max) { max = d.count; date = d.date } })
  return date
})

function formatWeekDate(dateStr: string): string {
  if (!dateStr) return ''
  const parts = dateStr.split('-')
  return parts.length === 3 ? `${parseInt(parts[1])}/${parseInt(parts[2])}` : dateStr
}

// 雷达图计算
const radarLabels = ['阅读探索', '内容沉淀', '社区互动', 'AI 使用']
const radarAngles = [-90, -90 + 90, -90 + 180, -90 + 270]
const radarMaxR = 88

function radarPolar(cx: number, cy: number, r: number, angleDeg: number): [number, number] {
  const rad = (angleDeg * Math.PI) / 180
  return [cx + r * Math.cos(rad), cy + r * Math.sin(rad)]
}

const radarAxes = computed(() => radarAngles.map((angle, i) => {
  const [x, y] = radarPolar(120, 120, radarMaxR + 16, angle)
  const [lx, ly] = radarPolar(120, 120, radarMaxR + 26, angle)
  return { label: radarLabels[i], x, y, labelX: lx, labelY: ly }
}))

const radarDataPoints = computed(() => {
  if (!weeklyReport.value) return radarAngles.map(() => [120, 120] as [number, number])
  const scores = [weeklyReport.value.behavior_scores.reading, weeklyReport.value.behavior_scores.collecting, weeklyReport.value.behavior_scores.interaction, weeklyReport.value.behavior_scores.ai_usage]
  return radarAngles.map((angle, i) => {
    const r = (scores[i] / 100) * radarMaxR
    return radarPolar(120, 120, r, angle)
  })
})

const radarLegend = computed(() => {
  if (!weeklyReport.value) return []
  const s = weeklyReport.value.behavior_scores
  return [
    { key: 'reading', label: '阅读探索', score: s.reading, color: '#d92d20' },
    { key: 'collecting', label: '内容沉淀', score: s.collecting, color: '#f59e0b' },
    { key: 'interaction', label: '社区互动', score: s.interaction, color: '#10b981' },
    { key: 'ai_usage', label: 'AI 使用', score: s.ai_usage, color: '#e53935' },
  ]
})

function radarPoints(r: number): [number, number][] {
  return radarAngles.map(a => radarPolar(120, 120, r, a))
}

// 放大版雷达图（300x300 viewBox）
const radarMaxRLg = 115
const radarAnglesLg = [-90, -90 + 90, -90 + 180, -90 + 270]
function radarPolarLg(cx: number, cy: number, r: number, angleDeg: number): [number, number] {
  const rad = (angleDeg * Math.PI) / 180
  return [cx + r * Math.cos(rad), cy + r * Math.sin(rad)]
}
const radarAxesLg = computed(() => radarAnglesLg.map((angle, i) => {
  const [x, y] = radarPolarLg(150, 150, radarMaxRLg + 20, angle)
  const [lx, ly] = radarPolarLg(150, 150, radarMaxRLg + 34, angle)
  return { label: radarLabels[i], x, y, labelX: lx, labelY: ly }
}))
const radarDataPointsLg = computed(() => {
  if (!weeklyReport.value) return radarAnglesLg.map(() => [150, 150] as [number, number])
  const scores = [weeklyReport.value.behavior_scores.reading, weeklyReport.value.behavior_scores.collecting, weeklyReport.value.behavior_scores.interaction, weeklyReport.value.behavior_scores.ai_usage]
  return radarAnglesLg.map((angle, i) => {
    const r = (scores[i] / 100) * radarMaxRLg
    return radarPolarLg(150, 150, r, angle)
  })
})
function radarPointsLg(r: number): [number, number][] {
  return radarAnglesLg.map(a => radarPolarLg(150, 150, r, a))
}

// 足迹节点大小
function footprintNodeSize(count: number): number {
  if (count <= 0) return 18
  const maxCount = maxDailyCount.value || 1
  return Math.round(18 + (count / maxCount) * 30)
}

// 报告结束语
const reportClosingText = computed(() => {
  const title = weeklyReport.value?.persona?.title || '读者'
  const topics = weeklyReport.value?.topic_rank?.filter(t => t.name !== '其他').slice(0, 2).map(t => t.name).join('、') || '多个领域'
  return `作为「${title}」，你本周在${topics}等方向留下了清晰的阅读节奏。继续保持探索，系统会为你沉淀更完整的阅读画像。`
})

function handleResize() {}
onBeforeUnmount(() => { saveProfileRoute(); window.removeEventListener('resize', handleResize); revokePendingAvatarBlob() })

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
// 头像本地预览状态：选择文件后暂存，保存时才真正上传
const pendingAvatarFile = ref<File | null>(null)
const originalAvatar = ref('')

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
  { key: 'insights', label: '阅读报告', icon: Grid, desc: '近 7 天阅读分析与建议' },
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
interface CategorySegment { name: string; count: number; pct: number; gradient: string; tooltip: string }
// 新闻胶囊条：蓝紫科技色系渐变
// 新闻 & 帖子胶囊条：统一马卡龙配色
const CAPSULE_GRADIENTS = [
  'linear-gradient(135deg, #f8a4c8 0%, #f472b6 100%)',  // 柔粉
  'linear-gradient(135deg, #fbbf8c 0%, #f8966e 100%)',  // 蜜桃
  'linear-gradient(135deg, #c4b5fd 0%, #a78bfa 100%)',  // 薰衣草
  'linear-gradient(135deg, #a7f3d0 0%, #6ee7b7 100%)',  // 薄荷
  'linear-gradient(135deg, #bae6fd 0%, #7dd3fc 100%)',  // 天空
  'linear-gradient(135deg, #e5e7eb 0%, #9ca3af 100%)',  // "其他"
]
const browseCapsuleLoading = ref(false)
const newsCapsuleItems = ref<BrowseHistoryItem[]>([])
const postCapsuleItems = ref<BrowseHistoryItem[]>([])

function buildCategorySegments(items: BrowseHistoryItem[], defaultLabel: string, gradients: string[]): CategorySegment[] {
  const catMap = new Map<string, number>()
  let total = 0
  items.forEach(item => {
    const cat = (item as any).category_name || defaultLabel
    catMap.set(cat, (catMap.get(cat) || 0) + 1)
    total++
  })
  if (total === 0) return []
  const sorted = Array.from(catMap.entries()).sort((a, b) => b[1] - a[1])
  const hasOthers = sorted.length > 5
  const topEntries = hasOthers ? sorted.slice(0, 5) : sorted

  const result: CategorySegment[] = []
  let pctSum = 0
  for (let i = 0; i < topEntries.length; i++) {
    const [name, count] = topEntries[i]
    const isLast = i === topEntries.length - 1 && !hasOthers
    const pct = isLast ? 100 - pctSum : Math.round((count / total) * 100)
    const gradient = gradients[i] || gradients[gradients.length - 1]
    result.push({ name, count, pct, gradient, tooltip: `${name}：${count} 条，占比 ${pct}%` })
    pctSum += pct
  }
  if (hasOthers) {
    const otherCount = sorted.slice(5).reduce((s, [, c]) => s + c, 0)
    const otherPct = 100 - pctSum
    const otherGradient = gradients[gradients.length - 1] // "其他" 颜色
    result.push({ name: '其他', count: otherCount, pct: otherPct > 0 ? otherPct : 0, gradient: otherGradient, tooltip: `其他分类：${otherCount} 条，占比 ${otherPct > 0 ? otherPct : 0}%` })
  }
  return result
}

const newsCategorySegments = computed(() => buildCategorySegments(newsCapsuleItems.value, '未分类新闻', CAPSULE_GRADIENTS))
const postCategorySegments = computed(() => buildCategorySegments(postCapsuleItems.value, '帖子浏览', CAPSULE_GRADIENTS))
const newsCapsuleTotal = computed(() => newsCategorySegments.value.reduce((s, seg) => s + seg.count, 0))
const postCapsuleTotal = computed(() => postCategorySegments.value.reduce((s, seg) => s + seg.count, 0))

async function loadBrowseCapsuleData() {
  browseCapsuleLoading.value = true
  try {
    // 获取全部浏览记录用于分类统计（page_size=200 足够覆盖绝大多数用户）
    const [newsRes, postRes] = await Promise.all([
      getBrowseHistory(1, 200, 'news'),
      getBrowseHistory(1, 200, 'post'),
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
  // 保存原始头像用于取消时恢复
  originalAvatar.value = editForm.avatar
  // 清除未保存的头像状态
  clearPendingAvatar()
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

  // 仅本地预览，不调用上传 API；保存时才真正提交
  // 释放之前的 blob URL 防止内存泄漏
  revokePendingAvatarBlob()
  const blobUrl = URL.createObjectURL(file)
  pendingAvatarFile.value = file
  editForm.avatar = blobUrl
  return false
}

/** 释放暂存头像的 blob URL */
function revokePendingAvatarBlob() {
  if (editForm.avatar && editForm.avatar.startsWith('blob:')) {
    URL.revokeObjectURL(editForm.avatar)
  }
}

/** 清除未保存的头像状态 */
function clearPendingAvatar() {
  revokePendingAvatarBlob()
  pendingAvatarFile.value = null
}

/** 取消编辑：恢复原头像并关闭弹窗 */
function handleEditCancel() {
  // 恢复原始头像
  revokePendingAvatarBlob()
  editForm.avatar = originalAvatar.value
  clearPendingAvatar()
  editDialogVisible.value = false
}

/** 弹窗关闭时清理未保存的头像 */
function handleEditDialogClose() {
  // 弹窗关闭但可能是通过 X 按钮或 ESC 关闭的（非保存/取消路径）
  // 如果有 pending 文件说明没保存就关了，需要恢复
  if (pendingAvatarFile.value) {
    revokePendingAvatarBlob()
    editForm.avatar = originalAvatar.value
    clearPendingAvatar()
  }
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

  editLoading.value = true
  try {
    // 如果有未保存的头像文件，先上传获取 URL
    let avatarUrl = editForm.avatar || ''
    if (pendingAvatarFile.value) {
      try {
        const uploadResult = await uploadAvatarApi(pendingAvatarFile.value)
        avatarUrl = uploadResult.avatar_url || uploadResult.avatar
        editForm.avatar = avatarUrl
        // 清除暂存文件引用（blob URL 稍后统一释放）
        pendingAvatarFile.value = null
      } catch (uploadError) {
        const message = uploadError instanceof Error ? uploadError.message : '头像上传失败，请重试'
        ElMessage.error(message)
        editLoading.value = false
        // 上传失败不污染当前已保存头像，保留原值继续
        return
      }
    }

    const avatar = avatarUrl
    const isValidAvatar = avatar && !avatar.startsWith('data:image/') && !avatar.includes(';base64,') && !avatar.startsWith('blob:') && avatar.length <= 255

    const payload: Record<string, string> = {
      nickname: editForm.nickname.trim(),
      email: editForm.email.trim() || '',
      phone: editForm.phone.trim() || '',
    }
    if (isValidAvatar) {
      payload.avatar = avatar
    }

    const result = await updateUserProfileApi(payload)

    if (userStore.userInfo) {
      userStore.userInfo.nickname = result.nickname
      ;(userStore.userInfo as any).email = result.email ?? ''
      ;(userStore.userInfo as any).phone = result.phone ?? ''
      userStore.userInfo.avatar = result.avatar || ''
      userStore.setUserInfo(userStore.userInfo)
    }

    ElMessage.success('资料保存成功')

    // 释放 blob URL（已上传或无需上传）
    revokePendingAvatarBlob()

    // 重新加载完整用户资料以确保最新
    await loadCurrentUserProfile()

    editDialogVisible.value = false
  } catch (error) {
    const message = error instanceof Error ? error.message : '资料保存失败'
    ElMessage.error(message)
    // 保存失败时，如果上传过头像，后端已保存了文件+DB，需要重新同步
    // 重新加载用户资料确保 userStore 与 DB 一致
    await loadCurrentUserProfile()
    // 恢复编辑表单中的头像为当前已保存头像
    editForm.avatar = userStore.userInfo?.avatar || originalAvatar.value
    clearPendingAvatar()
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

  // 第一步：确认对话框，用户取消不提示错误
  try {
    await ElMessageBox.confirm(`确定要取消收藏《${item.title}》吗？`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
  } catch {
    // 用户主动取消确认框，静默返回
    return
  }

  // 第二步：调用后端取消收藏 API
  try {
    if (item.target_type === 'post') {
      await unfavoritePost(item.news_id)
    } else {
      await unfavoriteNews(item.news_id)
    }
    ElMessage.success('已取消收藏')
  } catch (error: any) {
    const message = error?.response?.data?.message || error?.message || '取消收藏失败，请重试'
    ElMessage.error(message)
    return
  }

  // 第三步：重新拉取数据确保与后端一致
  // 刷新左侧概览统计
  await loadProfileOverview()
  // 刷新收藏列表，处理分页回退
  await reloadFavoritesAfterRemove()
}

/** 取消收藏后重新加载收藏列表，处理最后一页清空后的回退 */
async function reloadFavoritesAfterRemove() {
  const newTotal = totalCount.value - 1
  if (newTotal <= 0) {
    await loadFavorites(1)
    return
  }
  const maxPage = Math.ceil(newTotal / pageSize)
  // 如果当前页超出最大页数，回退到上一页
  const targetPage = Math.min(currentPage.value, maxPage)
  await loadFavorites(targetPage)
}

/** 加载概览统计数据 */
async function loadProfileOverview() {
  try {
    profileOverview.value = await getProfileOverview()
  } catch (error) {
    console.error('加载概览统计失败:', error)
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
    // 切换 Tab 时刷新概览，确保收藏数与其他页面同步
    loadProfileOverview()
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
    // 切换 Tab 时刷新概览，确保收藏数与其他页面同步
    loadProfileOverview()
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
    loadProfileOverview()
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
  // 恢复上次离开时的个人中心子页面
  const last = navStore.profileLastState
  if (last.activeTab && last.activeTab !== activeTab.value) {
    activeTab.value = last.activeTab
  }
  await loadCurrentUserProfile()
  // Load overview stats for quick stats display
  await loadProfileOverview()
  // Auto-load default tab data so browse history shows immediately
  if (activeTab.value === 'history') {
    await loadBrowseHistory()
    loadBrowseCapsuleData()
  }
  // Load weekly report (non-blocking)
  loadWeeklyReport()
  window.addEventListener('resize', handleResize)
})

onActivated(async () => {
  await loadProfileOverview()

  if (activeTab.value === 'history') {
    await loadBrowseHistory(currentPage.value)
    loadBrowseCapsuleData()
  } else if (activeTab.value === 'favorites') {
    await loadFavorites(currentPage.value)
  } else if (activeTab.value === 'comments') {
    await loadComments(currentPage.value)
  } else if (activeTab.value === 'ai-records') {
    await loadAIRecords(currentPage.value)
  }
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
          <div class="sidebar-stat-item" @click="handleStatCardClick('history')" title="浏览过的新闻与帖子数量（去重）">
            <span class="sidebar-stat-num">{{ profileOverview?.browse_count ?? 0 }}</span>
            <span class="sidebar-stat-lbl">浏览</span>
          </div>
          <div class="sidebar-stat-item" @click="handleStatCardClick('favorites')" title="有效新闻与帖子收藏数量（不含已下架内容）">
            <span class="sidebar-stat-num">{{ profileOverview?.favorite_count ?? 0 }}</span>
            <span class="sidebar-stat-lbl">收藏</span>
          </div>
          <div class="sidebar-stat-item" @click="handleStatCardClick('comments')" title="新闻与帖子评论总量">
            <span class="sidebar-stat-num">{{ profileOverview?.comment_count ?? 0 }}</span>
            <span class="sidebar-stat-lbl">评论</span>
          </div>
          <div class="sidebar-stat-item" @click="handleStatCardClick('ai-records')" title="AI 标题摘要生成总量">
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

        <!-- ===== 阅读报告 / 近 7 天阅读报告 ===== -->
        <div v-if="activeTab === 'insights'" class="module-content">
          <!-- Loading -->
          <div v-if="weeklyReportLoading" class="report-loading">
            <el-skeleton :rows="6" animated />
          </div>

          <!-- Error -->
          <div v-else-if="weeklyReportError" class="report-error">
            <span class="report-error__icon">⚠️</span>
            <span class="report-error__text">{{ weeklyReportError }}</span>
            <el-button size="small" @click="loadWeeklyReport">重新加载</el-button>
          </div>

          <!-- Empty -->
          <div v-else-if="!weeklyReport || weeklyReport.empty" class="report-empty">
            <span class="report-empty__icon">📋</span>
            <span class="report-empty__title">最近 7 天还没有足够的阅读记录</span>
            <span class="report-empty__hint">浏览新闻、收藏内容或使用 AI 摘要后，这里会生成你的阅读报告</span>
          </div>

          <!-- Report Content -->
          <template v-else>
            <div class="weekly-report-scroll">
              <!-- 报告顶部标题区 -->
              <header class="report-scroll-header">
                <div class="report-scroll-header__bg"></div>
                <div class="report-scroll-header__inner">
                  <p class="report-scroll-header__eyebrow">READING REPORT</p>
                  <h1 class="report-scroll-header__title">阅读报告</h1>
                  <p class="report-scroll-header__subtitle">近 7 天阅读分析与建议</p>
                  <p class="report-scroll-header__desc">基于你近 7 天的浏览、收藏、评论与 AI 使用行为，自动生成个性化阅读画像</p>
                </div>
              </header>

              <!-- ===== 第一部分：本周总览 ===== -->
              <section class="report-scroll-section report-scroll-section--overview">
                <div class="report-section-header">
                  <span class="report-section-header__num">01</span>
                  <div>
                    <h2 class="report-section-header__title">本周总览</h2>
                    <p class="report-section-header__subtitle">这周的你，是什么样的读者？</p>
                  </div>
                </div>
                <div class="report-cover">
                  <div class="report-cover__bg"></div>
                  <div class="report-cover__content">
                    <div class="report-cover__persona">
                      <span class="report-cover__persona-badge">{{ weeklyReport.persona.title }}</span>
                      <span v-if="aiSourceLabel" class="report-cover__ai-tag">{{ aiSourceLabel }}</span>
                    </div>
                    <p class="report-cover__summary">{{ weeklyReport.ai_analysis?.enabled ? weeklyReport.ai_analysis.summary : weeklyReport.summary }}</p>
                  </div>
                </div>
                <div class="report-page__body report-page__body--overview">
                  <div class="overview-integrated">
                    <div class="overview-integrated__text">
                      <h3 class="overview-integrated__title">本周画像</h3>
                      <p class="overview-integrated__desc">{{ weeklyReport.ai_analysis?.page_analyses?.overview || weeklyReport.analysis_texts?.profile_analysis || weeklyReport.persona.description }}</p>
                      <p v-if="weeklyReport.ai_analysis?.reading_style" class="overview-integrated__style">「{{ weeklyReport.ai_analysis.reading_style }}」</p>
                      <div class="overview-integrated__dimensions">
                        <div class="ov-dim-item" v-for="d in radarLegend" :key="d.key">
                          <span class="ov-dim-item__dot" :style="{background:d.color}"></span>
                          <span class="ov-dim-item__label">{{ d.label }}</span>
                          <span class="ov-dim-item__score">{{ d.score }}</span>
                        </div>
                      </div>
                    </div>
                    <div class="overview-integrated__radar">
                      <svg viewBox="-20 -20 340 340" class="radar-svg radar-svg--large">
                        <polygon v-for="level in 4" :key="'grid-'+level" :points="radarPointsLg(55 + level * 22).join(' ')" fill="none" :stroke="level===4?'#cbd5e1':'#e5e7eb'" stroke-width="1.5"/>
                        <line v-for="(axis,ai) in radarAxesLg" :key="'ax-'+ai" :x1="150" :y1="150" :x2="axis.x" :y2="axis.y" stroke="#e5e7eb" stroke-width="1.5"/>
                        <polygon :points="radarDataPointsLg.join(' ')" fill="rgba(217,45,32,0.12)" stroke="var(--color-primary)" stroke-width="2.5"/>
                        <circle v-for="(pt,pi) in radarDataPointsLg" :key="'pt-'+pi" :cx="pt[0]" :cy="pt[1]" r="6" fill="var(--color-primary)"/>
                        <text v-for="(axis,ai) in radarAxesLg" :key="'lbl-'+ai" :x="axis.labelX" :y="axis.labelY" text-anchor="middle" font-size="13" font-weight="600" fill="#475569">{{ axis.label }}</text>
                      </svg>
                    </div>
                  </div>
                  <div v-if="weeklyReport.analysis_texts?.behavior_analysis" class="overview-behavior-bar">
                    <span class="overview-behavior-bar__title">行为画像解读</span>
                    <p class="overview-behavior-bar__text">{{ weeklyReport.analysis_texts.behavior_analysis }}</p>
                  </div>
                </div>
              </section>

              <!-- ===== 第二部分：阅读轨迹 ===== -->
              <section class="report-scroll-section report-scroll-section--trajectory">
                <div class="report-section-header">
                  <span class="report-section-header__num">02</span>
                  <div>
                    <h2 class="report-section-header__title">阅读轨迹</h2>
                    <p class="report-section-header__subtitle">这一周，你如何阅读？</p>
                  </div>
                </div>
                <div class="report-page__body">
                  <p class="page2-intro">{{ weeklyReport.ai_analysis?.page_analyses?.trajectory || ('这一周，你的阅读节奏整体较稳定，兴趣主要集中在' + (weeklyReport.topic_rank.slice(0,3).filter(t=>t.name!=='其他').map(t=>t.name).join('、') || '多个领域') + '，说明你更关注现实议题、产业变化与技术趋势。') }}</p>
                  <div class="report-card report-card--footprint">
                    <div class="report-card__header"><span class="report-card__title">阅读足迹</span><span class="report-card__subtitle">近 7 天每日浏览次数</span></div>
                    <div class="report-card__body">
                      <div class="footprint-timeline">
                        <div class="footprint-line"></div>
                        <div v-for="day in weeklyReport.daily_activity" :key="day.date" class="footprint-node-wrap">
                          <div class="footprint-node" :class="{ 'footprint-node--peak': day.count===maxDailyCount&&maxDailyCount>0, 'footprint-node--zero': day.count===0 }" :style="{ width: footprintNodeSize(day.count)+'px', height: footprintNodeSize(day.count)+'px' }">
                            <span v-if="day.count>0" class="footprint-node__count">{{ day.count }}</span>
                          </div>
                          <span class="footprint-node__date">{{ formatWeekDate(day.date) }}</span>
                        </div>
                      </div>
                      <div class="activity-summary">
                        <span class="activity-summary__key">活跃 <strong class="activity-summary__num">{{ weeklyReport.overview.active_days }}</strong> 天</span>
                        <span v-if="maxDailyCount>0"> · 最活跃 {{ formatWeekDate(mostActiveDate) }} · 共 <strong class="activity-summary__num">{{ weeklyReport.daily_activity.reduce((s,d)=>s+d.count,0) }}</strong> 次</span>
                      </div>
                      <div v-if="weeklyReport.analysis_texts?.activity_analysis" class="chart-insight">{{ weeklyReport.analysis_texts.activity_analysis }}</div>
                    </div>
                  </div>
                  <div class="report-card report-card--bubbles">
                    <div class="report-card__header"><span class="report-card__title">兴趣主题</span><span class="report-card__subtitle">近 7 天浏览内容分类分布</span></div>
                    <div class="report-card__body">
                      <div v-if="weeklyReport.topic_rank.length===0" class="report-card__empty">暂无数据</div>
                      <div v-else class="topic-list">
                        <div v-for="(topic, idx) in weeklyReport.topic_rank" :key="topic.name" class="topic-item">
                          <span class="topic-item__rank" :class="{ 'topic-item__rank--top3': idx < 3 }">{{ idx + 1 }}</span>
                          <span class="topic-item__name">{{ topic.name }}</span>
                          <div class="topic-item__bar-track"><div class="topic-item__bar-fill" :style="{ width: topic.percent + '%', background: topicBarColors[idx] || '#94a3b8' }"></div></div>
                          <span class="topic-item__count"><strong>{{ topic.count }}</strong></span>
                          <span class="topic-item__pct">{{ topic.percent }}%</span>
                        </div>
                      </div>
                      <div v-if="weeklyReport.analysis_texts?.topic_analysis" class="chart-insight">{{ weeklyReport.analysis_texts.topic_analysis }}</div>
                    </div>
                  </div>
                </div>
              </section>

              <!-- ===== 第三部分：阅读发现与建议 ===== -->
              <section class="report-scroll-section report-scroll-section--findings">
                <div class="report-section-header">
                  <span class="report-section-header__num">03</span>
                  <div>
                    <h2 class="report-section-header__title">阅读发现与建议</h2>
                    <p class="report-section-header__subtitle">这一周，你有哪些值得关注的阅读发现？</p>
                  </div>
                </div>
                <div class="report-page__body report-page__body--insights">
                  <p class="page3-intro">{{ weeklyReport.ai_analysis?.page_analyses?.conclusion || '这一周，你留下了这些阅读痕迹。从行为来看，你保持了稳定的信息获取节奏，也在积极使用 AI 工具提升效率。' }}</p>
                  <div class="report-card report-card--highlights">
                    <div class="report-card__header"><span class="report-card__title">阅读发现</span></div>
                    <div class="report-card__body">
                      <div v-if="weeklyReport.highlights.length===0" class="report-card__empty">暂无数据</div>
                      <div v-else class="highlight-narrative-list">
                        <div v-for="(hl, hIdx) in weeklyReport.highlights" :key="hl.label" class="highlight-narrative-item"><span class="highlight-narrative-item__icon">{{ String(hIdx + 1).padStart(2, '0') }}</span><div class="highlight-narrative-item__content"><span class="highlight-narrative-item__text">{{ hl.narrative||hl.desc }}</span></div></div>
                      </div>
                    </div>
                  </div>
                  <div v-if="weeklyReport.ai_analysis?.enabled" class="report-card report-card--ai-merged">
                    <div class="report-card__header"><span class="report-card__title">AI 给你的阅读回顾</span></div>
                    <div class="report-card__body">
                      <div class="ai-merged-grid">
                        <div class="ai-merged-col">
                          <span class="ai-merged-col__label">从你的行为中看到</span>
                          <div class="ai-insight-list">
                            <div v-for="(insight,idx) in weeklyReport.ai_analysis.insights" :key="'ins-'+idx" class="ai-insight-item"><span class="ai-insight-item__dot"></span><span>{{ insight }}</span></div>
                          </div>
                        </div>
                        <div class="ai-merged-col ai-merged-col--suggestions">
                          <span class="ai-merged-col__label">下一步可以这样阅读</span>
                          <div class="ai-insight-list">
                            <div v-for="(sg,idx) in weeklyReport.ai_analysis.suggestions" :key="'sug-'+idx" class="ai-insight-item"><span class="ai-insight-item__dot ai-insight-item__dot--suggestion"></span><span>{{ sg }}</span></div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                  <p class="report-closing">{{ weeklyReport.ai_analysis?.closing || reportClosingText }}</p>
                </div>
              </section>
            </div>
          </template>
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
            <div v-if="browseCapsuleLoading" class="capsule-loading">
              <div class="capsule-card capsule-card--news">
                <div class="capsule-card__skeleton"><el-skeleton :rows="2" animated /></div>
              </div>
              <div class="capsule-card capsule-card--post">
                <div class="capsule-card__skeleton"><el-skeleton :rows="2" animated /></div>
              </div>
            </div>
            <div v-else class="browse-capsule-panel">
              <!-- 新闻胶囊卡片 -->
              <div class="capsule-card capsule-card--news">
                <div class="capsule-card__header">
                  <div class="capsule-card__title-row">
                    <span class="capsule-card__icon capsule-card__icon--news"></span>
                    <span class="capsule-card__title">新闻分类分布</span>
                    <span v-if="newsCapsuleTotal > 0" class="capsule-card__badge">共 {{ newsCapsuleTotal }} 条</span>
                  </div>
                  <span class="capsule-card__subtitle">按浏览过的新闻分类去重统计</span>
                </div>
                <div v-if="newsCategorySegments.length > 0" class="capsule-card__body">
                  <div class="capsule-bar">
                    <div
                      v-for="seg in newsCategorySegments"
                      :key="seg.name"
                      class="capsule-seg"
                      :style="{ width: seg.pct + '%', background: seg.gradient }"
                      :title="seg.tooltip"
                    ></div>
                  </div>
                  <div class="capsule-legend">
                    <span
                      v-for="seg in newsCategorySegments"
                      :key="seg.name"
                      class="capsule-legend__item"
                      :title="seg.name"
                    >
                      <span class="capsule-legend__dot" :style="{ background: seg.gradient }"></span>
                      <span class="capsule-legend__name">{{ seg.name }}</span>
                      <span class="capsule-legend__count">{{ seg.count }}</span>
                      <span class="capsule-legend__pct">{{ seg.pct }}%</span>
                    </span>
                  </div>
                </div>
                <div v-else class="capsule-card__empty">
                  <span class="capsule-card__empty-icon">📊</span>
                  <span class="capsule-card__empty-text">暂无新闻浏览分类数据</span>
                  <span class="capsule-card__empty-hint">浏览新闻后将自动生成分类分布</span>
                </div>
              </div>

              <!-- 帖子胶囊卡片 -->
              <div class="capsule-card capsule-card--post">
                <div class="capsule-card__header">
                  <div class="capsule-card__title-row">
                    <span class="capsule-card__icon capsule-card__icon--post"></span>
                    <span class="capsule-card__title">帖子标签分布</span>
                    <span v-if="postCapsuleTotal > 0" class="capsule-card__badge">共 {{ postCapsuleTotal }} 条</span>
                  </div>
                  <span class="capsule-card__subtitle">按浏览过的帖子标签去重统计</span>
                </div>
                <div v-if="postCategorySegments.length > 0" class="capsule-card__body">
                  <div class="capsule-bar">
                    <div
                      v-for="seg in postCategorySegments"
                      :key="seg.name"
                      class="capsule-seg"
                      :style="{ width: seg.pct + '%', background: seg.gradient }"
                      :title="seg.tooltip"
                    ></div>
                  </div>
                  <div class="capsule-legend">
                    <span
                      v-for="seg in postCategorySegments"
                      :key="seg.name"
                      class="capsule-legend__item"
                      :title="seg.name"
                    >
                      <span class="capsule-legend__dot" :style="{ background: seg.gradient }"></span>
                      <span class="capsule-legend__name">{{ seg.name }}</span>
                      <span class="capsule-legend__count">{{ seg.count }}</span>
                      <span class="capsule-legend__pct">{{ seg.pct }}%</span>
                    </span>
                  </div>
                </div>
                <div v-else class="capsule-card__empty">
                  <span class="capsule-card__empty-icon">🏷️</span>
                  <span class="capsule-card__empty-text">暂无帖子浏览标签数据</span>
                  <span class="capsule-card__empty-hint">浏览社区帖子后将自动生成标签分布</span>
                </div>
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
              <el-button type="primary" @click="router.push('/ai-generate')">去生成</el-button>
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
                      {{ item.risk_level === 'high' ? '高质量' : item.risk_level === 'medium' ? '中质量' : '低质量' }}
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

    <el-dialog v-model="editDialogVisible" title="编辑资料" width="520px" class="edit-dialog" :close-on-click-modal="false" @close="handleEditDialogClose">
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
            <el-button @click="handleEditCancel">取消</el-button>
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
            <el-button @click="handleEditCancel">取消</el-button>
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
            {{ currentAIRecord.risk_level === 'high' ? '高质量' : currentAIRecord.risk_level === 'medium' ? '中质量' : '低质量' }}
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
  background: var(--color-bg);
}

/* ===== 左侧个人中心栏 ===== */
.profile-sidebar {
  height: 100%;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  padding: 24px 18px;
  background: var(--color-bg-card);
  border-right: 1px solid var(--color-border);
  gap: 20px;
}

.sidebar-user-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 28px 16px 20px;
  background: linear-gradient(180deg, var(--color-primary-soft) 0%, var(--color-bg-hover) 50%, var(--color-bg-card) 100%);
  border-radius: 18px;
  border: 1px solid var(--color-primary-light);
  gap: 12px;
}

.sidebar-avatar-col {
  flex-shrink: 0;
}

.sidebar-avatar {
  border: 4px solid var(--color-bg-card);
  box-shadow: 0 4px 20px rgba(217, 45, 32, 0.2), 0 0 0 2px var(--color-primary-light);
}

.sidebar-user-name {
  font-size: 20px;
  font-weight: 700;
  color: var(--color-text-primary);
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
  color: var(--color-text-secondary);
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
  background: var(--color-bg-hover);
}

.sidebar-stat-item:hover {
  background: var(--color-primary-soft);
}

.sidebar-stat-num {
  font-size: 18px;
  font-weight: 700;
  color: var(--color-primary);
  line-height: 1.2;
}

.sidebar-stat-lbl {
  font-size: 12px;
  color: var(--color-text-secondary);
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
  color: var(--color-text-muted);
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
  color: var(--color-text-secondary);
}

.sidebar-nav-item:hover {
  background: var(--color-primary-soft);
  color: var(--color-primary);
}

.sidebar-nav-item--active {
  background: var(--color-primary-soft);
  color: var(--color-primary);
  font-weight: 600;
  border: 1px solid var(--color-primary-light);
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
  color: var(--color-text-primary);
  display: flex;
  align-items: center;
  gap: 8px;
}

.module-desc {
  margin: 0;
  font-size: 13px;
  color: var(--color-text-muted);
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
  background: var(--color-bg-hover);
  border: 1px solid var(--color-border);
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.module-stat-card:hover {
  background: var(--color-primary-soft);
  border-color: var(--color-primary-light);
}

.module-stat-card--active {
  background: var(--color-primary-soft);
  border-color: var(--color-primary);
}

.module-stat-card__icon {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: var(--color-primary-soft);
  color: var(--color-primary);
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
  color: var(--color-text-primary);
  line-height: 1.2;
}

.module-stat-card__lbl {
  font-size: 12px;
  color: var(--color-text-muted);
}

/* ===== 阅读画像占位区 ===== */
.reading-portrait-placeholder {
  margin-bottom: 24px;
  padding: 24px;
  background: var(--color-bg-card);
  border-radius: 16px;
  border: 1px dashed var(--color-border);
}

.portrait-header {
  margin-bottom: 20px;
}

.portrait-title {
  margin: 0 0 6px;
  font-size: 18px;
  font-weight: 700;
  color: var(--color-text-primary);
  display: flex;
  align-items: center;
  gap: 8px;
}

.portrait-subtitle {
  margin: 0;
  font-size: 13px;
  color: var(--color-text-muted);
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
  background: var(--color-bg-hover);
  border-radius: 14px;
  border: 1px solid var(--color-border);
  text-align: center;
  transition: background 0.3s ease;
}

.portrait-skeleton-card:hover {
  background: var(--color-primary-soft);
}

.skeleton-icon-wrapper {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: var(--color-primary-soft);
  color: #fca5a5;
  display: flex;
  align-items: center;
  justify-content: center;
}

.skeleton-label {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-secondary);
}

.skeleton-hint {
  font-size: 12px;
  color: var(--color-text-muted);
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


/* -- 阅读报告矩阵 + 星轨 -- */


@media (max-width: 768px) {
  .insights-top-row { grid-template-columns: 1fr; }
  .matrix-grid { grid-template-columns: repeat(6, 28px); grid-template-rows: repeat(5, 28px); gap: 6px; }
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
  color: var(--color-text-secondary);
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
  color: var(--color-text-muted);
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
  color: var(--color-text-muted);
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
  outline: 2px solid var(--color-primary);
  transform: scale(1.1);
  z-index: 1;
}

.heat-selected {
  outline: 2.5px solid var(--color-primary) !important;
}

.heat-empty { background: transparent; outline: none; cursor: default; }

/* 蓝紫色热力 */


.heatmap-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 8px;
}

.heatmap-selected-info {
  font-size: 12px;
  color: var(--color-primary);
  font-weight: 500;
}

.heatmap-hint {
  font-size: 11px;
  color: var(--color-text-muted);
}

.heatmap-legend {
  display: flex;
  align-items: center;
  gap: 3px;
  margin-left: auto;
}

.legend-label {
  font-size: 10px;
  color: var(--color-text-muted);
}

.legend-dot {
  width: 12px;
  height: 12px;
  border-radius: 3px;
}

.legend-dot.heat-0 { background: var(--color-bg-hover); }
.legend-dot.heat-1 { background: var(--color-primary-light); }
.legend-dot.heat-2 { background: var(--color-primary-light); }
.legend-dot.heat-3 { background: #d92d20; }
.legend-dot.heat-4 { background: var(--color-primary); }

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
  width: 156px;
  height: 156px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow: 0 4px 16px rgba(0,0,0,0.06);
}

.ring-center {
  width: 92px;
  height: 92px;
  border-radius: 50%;
  background: var(--color-bg-card);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}

.ring-total {
  font-size: 28px;
  font-weight: 700;
  color: var(--color-text-primary);
  line-height: 1.1;
}

.ring-label {
  font-size: 11px;
  color: var(--color-text-muted);
  margin-top: 1px;
}

.ring-label {
  font-size: 11px;
  color: var(--color-text-muted);
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
  background: var(--color-bg-hover);
  color: var(--color-text-primary);
}

.legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

.legend-name {
  font-size: 13px;
  color: var(--color-text-secondary);
  width: 40px;
}

.legend-count {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.legend-pct {
  font-size: 12px;
  color: var(--color-text-muted);
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
  color: var(--color-primary);
}

.ai-insight__big-label {
  font-size: 14px;
  color: var(--color-text-secondary);
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
  color: var(--color-text-secondary);
  width: 56px;
  flex-shrink: 0;
}

.ai-bar-track {
  flex: 1;
  height: 10px;
  background: var(--color-bg-hover);
  border-radius: 5px;
  overflow: hidden;
}

.ai-bar-fill {
  height: 100%;
  border-radius: 5px;
  transition: width 0.6s ease;
}

.ai-bar-fill.news { background: #d92d20; }
.ai-bar-fill.manual { background: var(--color-primary); }

.ai-bar-val {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-primary);
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
  color: var(--color-text-secondary);
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
  color: var(--color-text-muted);
  flex-shrink: 0;
}

.last-title {
  color: var(--color-text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* ===== 浏览分类胶囊比例条 ===== */
.browse-capsule-panel {
  display: flex;
  flex-direction: column;
  gap: 14px;
  margin-bottom: 20px;
}

/* ---- 卡片容器 ---- */
.capsule-card {
  padding: 16px 18px;
  border-radius: 16px;
  border: 1px solid var(--color-border);
  background: linear-gradient(180deg, var(--color-bg-hover) 0%, var(--color-bg) 100%);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
  transition: box-shadow 0.25s ease, transform 0.25s ease;
}
.capsule-card:hover {
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.07);
  transform: translateY(-1px);
}
.capsule-card--news,
.capsule-card--post {
  border-left: none;
}
.capsule-card__skeleton {
  padding: 4px 0;
}

/* ---- 头部 ---- */
.capsule-card__header {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-bottom: 12px;
}
.capsule-card__title-row {
  display: flex;
  align-items: center;
  gap: 8px;
}
.capsule-card__icon {
  width: 10px;
  height: 10px;
  border-radius: 3px;
  flex-shrink: 0;
}
.capsule-card__icon--news {
  background: linear-gradient(135deg, #f472b6, #f8a4c8);
}
.capsule-card__icon--post {
  background: linear-gradient(135deg, #7dd3fc, #bae6fd);
}
.capsule-card__title {
  font-size: 14px;
  font-weight: 650;
  color: var(--color-text-primary);
}
.capsule-card__badge {
  margin-left: auto;
  font-size: 11px;
  font-weight: 500;
  color: var(--color-text-secondary);
  background: var(--color-bg-hover);
  padding: 2px 10px;
  border-radius: 20px;
  white-space: nowrap;
}
.capsule-card__subtitle {
  font-size: 11px;
  color: var(--color-text-muted);
  margin-left: 18px;
}

/* ---- 胶囊条 ---- */
.capsule-card__body {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.capsule-bar {
  display: flex;
  height: 16px;
  border-radius: 10px;
  overflow: hidden;
  gap: 2px;
  background: var(--color-border);
  padding: 1px;
}
.capsule-seg {
  transition: filter 0.22s ease, transform 0.22s ease;
  cursor: default;
  min-width: 4px;
}
.capsule-seg:first-child {
  border-radius: 9px 0 0 9px;
}
.capsule-seg:last-child {
  border-radius: 0 9px 9px 0;
}
.capsule-seg:hover {
  filter: brightness(1.18) saturate(1.1);
  transform: scaleY(1.25);
}

/* ---- 图例 ---- */
.capsule-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 6px 12px;
}
.capsule-legend__item {
  font-size: 12px;
  color: var(--color-text-secondary);
  display: inline-flex;
  align-items: center;
  gap: 4px;
  cursor: default;
  transition: color 0.18s;
  max-width: 100%;
}
.capsule-legend__item:hover {
  color: var(--color-text-primary);
}
.capsule-legend__dot {
  width: 9px;
  height: 9px;
  border-radius: 3px;
  flex-shrink: 0;
}
.capsule-legend__name {
  max-width: 80px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.capsule-legend__count {
  font-weight: 600;
  color: var(--color-text-secondary);
}
.capsule-legend__pct {
  color: var(--color-text-muted);
  font-size: 11px;
}

/* ---- 空状态 ---- */
.capsule-card__empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 16px 0 6px;
  color: var(--color-text-muted);
}
.capsule-card__empty-icon {
  font-size: 22px;
  opacity: 0.6;
}
.capsule-card__empty-text {
  font-size: 12px;
  color: var(--color-text-muted);
}
.capsule-card__empty-hint {
  font-size: 11px;
  color: var(--color-text-muted);
}

/* ---- loading ---- */
.capsule-loading {
  display: flex;
  flex-direction: column;
  gap: 14px;
  margin-bottom: 20px;
}

/* ===== 近 7 天阅读报告 ===== */
.report-loading, .report-error, .report-empty {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  padding: 48px 24px; gap: 12px;
}
.report-error__icon, .report-empty__icon { font-size: 36px; }
.report-error__text { font-size: 14px; color: var(--color-primary); }
.report-empty__title { font-size: 15px; font-weight: 600; color: var(--color-text-secondary); }
.report-empty__hint { font-size: 13px; color: var(--color-text-muted); text-align: center; }

/* ---- 翻页报告书 ---- */
/* 纵向滚动报告容器 */
.weekly-report-scroll { background: var(--color-bg-card); border-radius: 24px; box-shadow: 0 4px 24px rgba(0,0,0,0.06); padding: 36px 36px 48px; display: flex; flex-direction: column; gap: 40px; }

/* 报告顶部标题区 — 渐变封面卡片 */
.report-scroll-header { position: relative; text-align: center; padding: 36px 36px 32px; border-radius: 20px; overflow: hidden; margin-bottom: 0; background: linear-gradient(160deg, var(--color-primary-soft) 0%, var(--color-primary-soft) 30%, var(--color-bg-card) 70%, var(--color-bg-hover) 100%); border: 1px solid var(--color-primary-light); }
.report-scroll-header__bg { display: none; }
.report-scroll-header__inner { position: relative; z-index: 1; }
.report-scroll-header__eyebrow { font-size: 11px; font-weight: 700; letter-spacing: .18em; color: var(--color-primary); margin: 0 0 10px; text-transform: uppercase; }
.report-scroll-header__title { font-size: 34px; font-weight: 850; color: var(--color-text-primary); margin: 0 0 10px; letter-spacing: -0.5px; }
.report-scroll-header__subtitle { font-size: 15px; color: var(--color-text-secondary); margin: 0 0 8px; }
.report-scroll-header__desc { font-size: 13px; color: var(--color-text-muted); margin: 0; }

/* 每部分标题 — 含序号 */
.report-section-header { display: flex; align-items: center; gap: 16px; margin-bottom: 18px; padding-bottom: 16px; border-bottom: 2px solid var(--color-border-light); }
.report-section-header__num { flex-shrink: 0; display: grid; place-items: center; width: 42px; height: 42px; border-radius: 12px; background: linear-gradient(135deg, #d92d20, #b91c1c); color: #fff; font-size: 18px; font-weight: 800; letter-spacing: .02em; }
.report-section-header__title { font-size: 22px; font-weight: 750; color: var(--color-text-primary); margin: 0 0 3px; }
.report-section-header__subtitle { font-size: 14px; color: var(--color-text-secondary); margin: 0; }

/* 部分间距 */
.report-scroll-section { }
.report-scroll-section--trajectory { border-top: 1px solid var(--color-border-light); padding-top: 8px; }
.report-scroll-section--findings { border-top: 1px solid var(--color-border-light); padding-top: 8px; }
.report-page { min-height: auto; }

/* 关键数字强调 */
.activity-summary__num { font-size: 20px; font-weight: 800; color: var(--color-primary); }
.topic-item__count strong { font-size: 16px; color: var(--color-primary); font-weight: 700; }
.ov-dim-item__score { font-size: 20px; font-weight: 800; color: var(--color-text-primary); margin-left: auto; }
.ov-dim-item__label { font-weight: 600; }
.report-page__body { padding: 24px 30px; display: flex; flex-direction: column; gap: 20px; }
.report-page__body--overview { padding: 0 30px 24px; }
.report-page__body--insights { gap: 18px; }
.report-page-summary { font-size: 15px; color: var(--color-text-secondary); line-height: 1.7; margin: 0; padding: 12px 16px; background: var(--color-bg-hover); border-radius: 10px; border-left: 4px solid var(--color-primary); }
.report-closing { font-size: 14px; color: var(--color-text-muted); text-align: center; padding: 18px 12px 4px; margin: 0; line-height: 1.7; }

/* 第 2 页 intro */
.page2-intro { font-size: 16px; color: var(--color-text-primary); line-height: 1.8; margin: 0 0 8px; }
.page3-intro { font-size: 17px; color: var(--color-text-primary); line-height: 1.8; margin: 0 0 4px; }

/* 行为分析宽卡片 */
.overview-behavior-bar { margin-top: 8px; padding: 16px 20px; background: var(--color-bg-hover); border-radius: 12px; border-left: 4px solid var(--color-primary); }
.overview-behavior-bar__title { font-size: 15px; font-weight: 700; color: var(--color-text-secondary); display: block; margin-bottom: 6px; }
.overview-behavior-bar__text { font-size: 16px; color: var(--color-text-secondary); line-height: 1.8; margin: 0; }

/* 阅读发现与建议部分（第三部分）紧凑样式 */
.report-scroll-section--findings .page3-intro { font-size: 14px; line-height: 1.65; color: var(--color-text-secondary); }
.report-scroll-section--findings .highlight-narrative-item__text { font-size: 13px; line-height: 1.55; }
.report-scroll-section--findings .ai-insight-item { font-size: 13px; line-height: 1.55; }
.report-scroll-section--findings .report-card__title { font-size: 16px; }
.report-scroll-section--findings .report-card { padding: 14px 18px; margin-bottom: 14px; }
.report-scroll-section--findings .report-closing { font-size: 14px; line-height: 1.65; }

/* 封面卡 — 浅色报告风格 */
.report-cover { position: relative; border-radius: 22px; overflow: hidden; margin-bottom: 0; background: var(--color-bg-card); border: 1px solid var(--color-border); }
.report-cover__bg { display: none; }
.report-cover__content { position: relative; padding: 32px 30px 28px; color: var(--color-text-primary); }
.report-cover__title { font-size: 24px; font-weight: 750; margin: 0 0 4px; letter-spacing: -0.3px; color: var(--color-text-primary); }
.report-cover__subtitle { font-size: 14px; color: var(--color-text-secondary); margin: 0 0 16px; }
.report-cover__persona { margin-bottom: 12px; }
.report-cover__persona-badge { display: inline-block; padding: 6px 20px; background: linear-gradient(135deg, var(--color-primary-soft), var(--color-primary-light)); border-radius: 24px; font-size: 16px; font-weight: 700; color: var(--color-primary); }
.report-cover__ai-tag { display: inline-block; font-size: 11px; padding: 3px 10px; background: var(--color-primary-soft); color: var(--color-primary); border-radius: 12px; margin-left: 10px; vertical-align: middle; }
.report-cover__summary { font-size: 17px; line-height: 1.8; color: var(--color-text-secondary); margin: 0; }

/* 第 1 页：画像综合区 */
.overview-integrated { display: grid; grid-template-columns: 1fr 360px; gap: 32px; align-items: start; }
.overview-integrated__text { display: flex; flex-direction: column; gap: 14px; min-width: 0; }
.overview-integrated__title { font-size: 24px; font-weight: 750; color: var(--color-text-primary); margin: 0; }
.overview-integrated__desc { font-size: 16px; color: var(--color-text-secondary); line-height: 1.8; margin: 0; }
.overview-integrated__style { font-size: 16px; color: var(--color-primary); font-weight: 600; line-height: 1.7; margin: 0; padding: 8px 0; font-style: italic; }
.overview-integrated__dimensions { display: grid; grid-template-columns: 1fr 1fr; gap: 8px 16px; }
.ov-dim-item { display: flex; align-items: center; gap: 8px; font-size: 14px; color: var(--color-text-secondary); padding: 6px 10px; background: var(--color-bg-hover); border-radius: 8px; }
.ov-dim-item__dot { width: 10px; height: 10px; border-radius: 3px; flex-shrink: 0; }
.ov-dim-item__label { flex: 1; }
.ov-dim-item__score { font-weight: 700; color: var(--color-text-primary); font-size: 16px; }
.overview-integrated__insight { font-size: 16px; color: var(--color-text-secondary); line-height: 1.8; margin: 0; padding: 14px 18px; background: var(--color-bg-hover); border-radius: 10px; border-left: 4px solid var(--color-primary); }
.overview-integrated__radar { display: flex; align-items: flex-start; justify-content: center; padding-top: 24px; overflow: visible; }
.radar-svg--large { width: 340px; height: 340px; overflow: visible; }

/* 图表行 */
.report-charts-row { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 0; }

/* 通用卡片 */
.report-card { background: var(--color-bg-card); border-radius: 18px; border: 1px solid var(--color-border-light); box-shadow: 0 1px 3px rgba(0,0,0,0.04); overflow: hidden; }
.report-card--radar { overflow: visible; }
.report-card__header { padding: 16px 20px 12px; border-bottom: 1px solid var(--color-border-light); display: flex; align-items: baseline; gap: 8px; }
.report-card__title { font-size: 17px; font-weight: 700; color: var(--color-text-primary); }
.report-card__subtitle { font-size: 13px; color: var(--color-text-muted); }
.report-card__body { padding: 18px 20px; }
.report-card__empty { font-size: 14px; color: var(--color-text-muted); text-align: center; padding: 20px 0; }

/* 雷达图 */
.radar-wrap { display: flex; align-items: center; gap: 12px; }
.radar-svg { width: 200px; height: 200px; flex-shrink: 0; }
.radar-legend { display: flex; flex-direction: column; gap: 6px; }
.radar-legend__item { display: flex; align-items: center; gap: 6px; font-size: 13px; color: var(--color-text-secondary); }
.radar-legend__dot { width: 8px; height: 8px; border-radius: 2px; flex-shrink: 0; }
.radar-legend__score { margin-left: auto; font-weight: 650; color: var(--color-text-secondary); }

/* 足迹时间轴 */
.footprint-timeline { display: flex; align-items: flex-end; justify-content: space-between; padding: 16px 8px 8px; position: relative; min-height: 90px; }
.footprint-line { position: absolute; top: 50%; left: 8%; right: 8%; height: 2px; background: var(--color-border); transform: translateY(-50%); }
.footprint-node-wrap { display: flex; flex-direction: column; align-items: center; gap: 8px; z-index: 1; }
.footprint-node { border-radius: 50%; display: flex; align-items: center; justify-content: center; transition: all 0.3s ease; background: var(--color-primary-light); border: 2px solid var(--color-primary-light); min-width: 18px; min-height: 18px; }
.footprint-node--peak { background: #d92d20; border-color: var(--color-primary); box-shadow: 0 0 14px rgba(217,45,32,0.35); }
.footprint-node--zero { background: var(--color-bg-hover); border-color: #e5e7eb; }
.footprint-node__count { font-size: 13px; font-weight: 700; color: #fff; }
.footprint-node--zero .footprint-node__count { color: transparent; }
.footprint-node__date { font-size: 12px; color: var(--color-text-muted); }
.activity-summary { margin-top: 12px; font-size: 13px; color: var(--color-text-muted); }

/* 兴趣主题横向条形榜 */
.topic-list { display: flex; flex-direction: column; gap: 10px; }
.topic-item { display: flex; align-items: center; gap: 10px; }
.topic-item__rank { width: 22px; height: 22px; border-radius: 6px; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 700; background: var(--color-bg-hover); color: var(--color-text-muted); flex-shrink: 0; }
.topic-item__rank--top3 { background: var(--color-primary-soft); color: var(--color-primary); }
.topic-item__name { font-size: 13px; color: var(--color-text-secondary); width: 52px; flex-shrink: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.topic-item__bar-track { flex: 1; height: 12px; background: var(--color-bg-hover); border-radius: 6px; overflow: hidden; }
.topic-item__bar-fill { height: 100%; border-radius: 6px; min-width: 2px; transition: width 0.5s ease; }
.topic-item__count { font-size: 13px; font-weight: 600; color: var(--color-text-secondary); width: 22px; text-align: right; flex-shrink: 0; }
.topic-item__pct { font-size: 12px; color: var(--color-text-muted); width: 32px; text-align: right; flex-shrink: 0; }

/* AI 合并卡 */
.ai-merged-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
.ai-merged-col { display: flex; flex-direction: column; gap: 10px; }
.ai-merged-col__label { font-size: 14px; font-weight: 650; color: var(--color-text-secondary); padding-bottom: 4px; border-bottom: 2px solid var(--color-border-light); }

/* 阅读发现编号式列表 */
.highlight-narrative-list { display: flex; flex-direction: column; gap: 12px; }
.highlight-narrative-item { display: flex; gap: 14px; align-items: flex-start; padding: 14px 16px; background: var(--color-bg-hover); border-radius: 12px; border: 1px solid var(--color-border-light); }
.highlight-narrative-item__icon { font-size: 13px; font-weight: 800; color: var(--color-primary); background: var(--color-primary-soft); width: 28px; height: 28px; border-radius: 8px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; margin-top: 1px; }
.highlight-narrative-item__text { font-size: 15px; color: var(--color-text-primary); line-height: 1.65; }

/* 图表解读 */
.chart-insight { margin-top: 12px; padding: 14px 18px; background: var(--color-bg-hover); border-radius: 10px; border-left: 4px solid var(--color-primary); font-size: 16px; color: var(--color-text-secondary); line-height: 1.8; }

/* AI 洞察列表 */
.ai-insight-list { display: flex; flex-direction: column; gap: 10px; }
.ai-insight-item { display: flex; align-items: flex-start; gap: 10px; font-size: 15px; color: var(--color-text-secondary); line-height: 1.7; }
.ai-insight-item__dot { width: 6px; height: 6px; border-radius: 50%; background: var(--color-primary); flex-shrink: 0; margin-top: 6px; }
.ai-insight-item__dot--suggestion { background: #10b981; }

/* 响应式 */
@media (max-width: 768px) {
  .report-charts-row { grid-template-columns: 1fr; }
  .report-cover__title { font-size: 22px; }
  .report-cover__content { padding: 24px 20px 20px; }
  .report-cover__summary { font-size: 15px; }
  .radar-wrap { flex-direction: column; }
  .weekly-report-scroll { padding: 24px 20px 32px; gap: 28px; }
  .report-scroll-header__title { font-size: 26px; }
  .overview-integrated { grid-template-columns: 1fr; }
  .overview-integrated__radar { order: -1; padding-top: 0; }
  .radar-svg--large { width: 260px; height: 260px; }
  .ai-merged-grid { grid-template-columns: 1fr; }
  .report-page__body { padding: 16px 18px; }
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
  background: var(--color-bg-hover);
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
  color: var(--color-text-secondary);
  box-shadow: none;
}

.segmented-control :deep(.el-radio-button__original-radio:checked + .el-radio-button__inner) {
  background: var(--color-bg-card);
  color: var(--color-primary);
  box-shadow: 0 2px 8px rgba(217, 45, 32, 0.16);
}

.segmented-control :deep(.el-radio-button__inner:hover) {
  color: var(--color-primary);
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
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  cursor: pointer;
  transition: all 0.25s ease;
}

.record-item:hover {
  background: var(--color-primary-soft);
  border-color: var(--color-primary);
  box-shadow: 0 4px 16px rgba(217, 45, 32, 0.10);
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
  color: var(--color-primary);
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
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  transition: all 0.25s ease;
}

.ai-record-item:hover {
  border-color: var(--color-primary);
  box-shadow: 0 4px 16px rgba(217, 45, 32, 0.10);
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
  border: 1px solid var(--color-border);
  border-radius: 8px;
  background: var(--color-bg-card);
  color: var(--color-text-primary);
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
  background: var(--color-bg-hover);
  border-color: var(--color-primary);
  color: var(--color-primary);
}

.profile-pagination .page-btn.active {
  background: #d92d20;
  border-color: var(--color-primary);
  color: #fff;
  font-weight: 600;
  box-shadow: 0 2px 8px rgba(217, 45, 32, 0.25);
}

.profile-pagination .page-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
  background: var(--color-bg);
}

.profile-pagination .page-ellipsis {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  color: var(--color-text-muted);
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
    border-bottom: 1px solid var(--color-border);
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
