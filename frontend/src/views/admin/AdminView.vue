<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import {
  ArrowRight,
  Clock,
  DataBoard,
  Files,
  Grid,
  Key,
  Lock,
  Message,
  Monitor,
  PieChart,
  Refresh,
  Setting,
  TrendCharts,
  User,
  UserFilled,
  Warning,
} from '@element-plus/icons-vue'
import {
  type AdminDashboard,
  getDashboard,
  getAdminAnalyticsTrends,
  getAdminOpsStatus,
  getAdminOpsBackups,
} from '@/api/admin'
import { type AdminAnalyticsTrendsResponse, type AdminTrendPoint } from '@/api/admin'
import * as echarts from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { BarChart, LineChart } from 'echarts/charts'
import { GridComponent, LegendComponent, TitleComponent, TooltipComponent } from 'echarts/components'

echarts.use([CanvasRenderer, LineChart, BarChart, TitleComponent, TooltipComponent, LegendComponent, GridComponent])
import AdminPendingCenter from '@/components/admin/AdminPendingCenter.vue'
import AdminNewsManagement from '@/components/admin/AdminNewsManagement.vue'
import AdminPostManagement from '@/components/admin/AdminPostManagement.vue'
import AdminCommentReview from '@/components/admin/AdminCommentReview.vue'
import AdminHotTopicManagement from '@/components/admin/AdminHotTopicManagement.vue'
import AdminTimelineManagement from '@/components/admin/AdminTimelineManagement.vue'
import AdminUserManagement from '@/components/admin/AdminUserManagement.vue'
import AdminAIConfigManagement from '@/components/admin/AdminAIConfigManagement.vue'
import AdminSystemConfigManagement from '@/components/admin/AdminSystemConfigManagement.vue'
import AdminOpsManagement from '@/components/admin/AdminOpsManagement.vue'
import AdminAnalyticsDashboard from '@/components/admin/AdminAnalyticsDashboard.vue'
import AdminWorkbench from '@/components/admin/AdminWorkbench.vue'
import { useUserStore } from '@/stores/user'

type AdminSection = 'dashboard' | 'pending' | 'news' | 'posts' | 'comments' | 'hotTopics' | 'timelines' | 'users' | 'aiConfig' | 'config' | 'ops' | 'analytics'
type FeatureStatus = 'available' | 'coming-soon'
type TrendRange = '7d' | '30d' | '90d'

interface FeatureCard {
  key: string
  title: string
  description: string
  icon: unknown
  status: FeatureStatus
  targetTab?: AdminSection
  adminOnly?: boolean
}

interface MetricCard {
  key: string
  title: string
  value: string | number
  hint: string
  icon: unknown
  bg: string
  color: string
}

interface TodoCard {
  key: string
  title: string
  count: string | number
  hint: string
  targetTab?: AdminSection
  disabled?: boolean
}

interface StatusCard {
  key: string
  title: string
  value: string
  tone: 'success' | 'warning' | 'info' | 'danger'
  hint: string
  icon: unknown
}

interface QuickEntry {
  key: string
  title: string
  description: string
  icon: unknown
  status: FeatureStatus
  targetTab?: AdminSection
  adminOnly?: boolean
}

const userStore = useUserStore()
const activeTab = ref<AdminSection>(userStore.isAdmin ? 'dashboard' : 'pending')
const dashboard = ref<AdminDashboard | null>(null)
const pendingCenterKey = ref(0)
const workbenchKey = ref(0)
const loadingState = reactive<Record<AdminSection, boolean>>({
  dashboard: false,
  pending: false,
  news: false,
  posts: false,
  comments: false,
  hotTopics: false,
  timelines: false,
  users: false,
  aiConfig: false,
  config: false,
  ops: false,
  analytics: false,
})
const sectionError = reactive<Record<AdminSection, string | null>>({
  dashboard: null,
  pending: null,
  news: null,
  posts: null,
  comments: null,
  hotTopics: null,
  timelines: null,
  users: null,
  aiConfig: null,
  config: null,
  ops: null,
  analytics: null,
})
const lastLoadedAt = ref('')
const trendRange = ref<TrendRange>('7d')
const trendRanges = [
  { key: '7d', label: '7 天' },
  { key: '30d', label: '30 天' },
  { key: '90d', label: '90 天' },
] as const
const trendsData = ref<AdminAnalyticsTrendsResponse | null>(null)
const trendsLoading = ref(false)
const opsStatusData = ref<{ backend?: { status: string; message: string }; database?: { status: string; message: string }; ai_service?: { status: string; message: string } } | null>(null)
const backupData = ref<{ items: Array<{ status: string; created_at?: string | null }> } | null>(null)

// trend chart refs
const trendContentChartRef = ref<HTMLDivElement>()
const trendReviewChartRef = ref<HTMLDivElement>()
let trendContentChart: echarts.ECharts | null = null
let trendReviewChart: echarts.ECharts | null = null

const sectionTitles: Record<AdminSection, string> = {
  dashboard: '工作台',
  analytics: '数据看板',
  pending: '待审核',
  news: '新闻内容管理',
  posts: '社区帖子管理',
  comments: '评论审核',
  hotTopics: '热搜与话题管理',
  timelines: 'Timeline 管理',
  users: '用户与权限',
  aiConfig: 'AI 模型与规则',
  config: '系统配置',
  ops: '系统运维',
}

const sidebarSections = computed(() => {
  const all = [
    { key: 'dashboard', label: '工作台', icon: Grid },
    { key: 'analytics', label: '数据看板', icon: DataBoard },
    { key: 'pending', label: '待审核', icon: Warning },
    { key: 'news', label: '新闻内容管理', icon: Files },
    { key: 'posts', label: '社区帖子管理', icon: Message },
    { key: 'comments', label: '评论审核', icon: Files },
    { key: 'hotTopics', label: '热搜与话题管理', icon: TrendCharts },
    { key: 'timelines', label: 'Timeline 管理', icon: TrendCharts },
    { key: 'users', label: '用户与权限', icon: UserFilled },
    { key: 'aiConfig', label: 'AI 模型与规则', icon: Monitor },
    { key: 'config', label: '系统配置', icon: Setting },
    { key: 'ops', label: '系统运维', icon: DataBoard },
  ] as const
  if (!userStore.isAdmin) {
    return all.filter(item => item.key !== 'dashboard' && item.key !== 'users' && item.key !== 'aiConfig' && item.key !== 'config' && item.key !== 'ops' && item.key !== 'analytics')
  }
  return all
})

const editorQuickEntries: QuickEntry[] = [
  {
    key: 'news-audit',
    title: '内容审核',
    description: '处理新闻、帖子和评论的待审核内容',
    icon: Warning,
    targetTab: 'pending',
    status: 'available',
  },
  {
    key: 'post-audit',
    title: '帖子审核',
    description: '查看社区帖子审核状态',
    icon: Message,
    targetTab: 'pending',
    status: 'available',
  },
  {
    key: 'comment-audit',
    title: '评论审核',
    description: '查看评论折叠和删除状态',
    icon: Files,
    status: 'coming-soon',
  },
  {
    key: 'timeline-refresh',
    title: 'Timeline 管理',
    description: '查看事件脉络相关任务状态',
    icon: TrendCharts,
    targetTab: 'timelines',
    status: 'available',
  },
]

const adminQuickEntries: QuickEntry[] = [
  {
    key: 'news-audit',
    title: '内容审核',
    description: '处理新闻、帖子和评论的待审核内容',
    icon: Warning,
    targetTab: 'pending',
    status: 'available',
  },
  {
    key: 'topic-config',
    title: '话题维护',
    description: '维护热搜话题和事件脉络配置',
    icon: TrendCharts,
    targetTab: 'hotTopics',
    status: 'available',
  },
  {
    key: 'user-mgmt',
    title: '用户管理',
    description: '查看系统用户和角色信息',
    icon: UserFilled,
    targetTab: 'users',
    status: 'available',
  },
  {
    key: 'ai-config',
    title: 'AI 配置',
    description: '查看 AI 服务相关配置',
    icon: Setting,
    targetTab: 'config',
    status: 'available',
  },
  {
    key: 'ops',
    title: '系统运维',
    description: '查看服务状态、数据库、备份和操作日志',
    icon: DataBoard,
    targetTab: 'ops',
    status: 'available',
    adminOnly: true,
  },
]

const metricCards = computed<MetricCard[]>(() => [
  {
    key: 'today_new_users',
    title: '今日新增用户',
    value: dashboard.value?.today_new_users ?? '--',
    hint: dashboard.value ? '今日注册' : '等待加载',
    icon: User,
    bg: '#e8f4fd',
    color: '#409eff',
  },
  {
    key: 'active_users_7d',
    title: '7 天活跃用户',
    value: dashboard.value?.active_users_7d ?? '--',
    hint: dashboard.value ? '按浏览记录估算' : '等待加载',
    icon: UserFilled,
    bg: '#e0f2fe',
    color: '#0284c7',
  },
  {
    key: 'today_review_done',
    title: '今日审核完成',
    value: dashboard.value?.today_review_done ?? '--',
    hint: dashboard.value ? '已审核操作数' : '等待加载',
    icon: Warning,
    bg: '#fef7e0',
    color: '#e6a23c',
  },
  {
    key: 'pending_total',
    title: '当前待处理',
    value: dashboard.value?.pending_total ?? '--',
    hint: dashboard.value ? '需审核内容总数' : '等待加载',
    icon: Clock,
    bg: '#fef0f0',
    color: '#f56c6c',
  },
  {
    key: 'today_ai_calls',
    title: '今日 AI 调用',
    value: dashboard.value?.today_ai_calls ?? '--',
    hint: dashboard.value ? 'AI 生成调用次数' : '等待加载',
    icon: Monitor,
    bg: '#f5f7ff',
    color: '#6a78ff',
  },
  {
    key: 'avg_response_ms',
    title: '平均响应时延',
    value: dashboard.value?.avg_response_ms != null ? `${dashboard.value.avg_response_ms} ms` : '暂未记录',
    hint: 'AI 生成平均耗时',
    icon: TrendCharts,
    bg: '#f7f0ff',
    color: '#a46bff',
  },
])

const todoCards = computed<TodoCard[]>(() => [
  {
    key: 'news-audit',
    title: '新闻待审核',
    count: dashboard.value?.pending_news_count ?? dashboard.value?.pending_total ?? '--',
    hint: '状态异常的新闻内容',
    targetTab: 'pending',
  },
  {
    key: 'post-audit',
    title: '帖子审核',
    count: dashboard.value?.pending_post_count ?? dashboard.value?.pending_total ?? '--',
    hint: '待审核的社区帖子',
    targetTab: 'pending',
  },
  {
    key: 'comment-audit',
    title: '评论审核',
    count: dashboard.value?.pending_comment_count ?? '--',
    hint: '来自新闻和帖子评论',
    targetTab: 'comments',
  },
  {
    key: 'hot-config',
    title: '热搜维护',
    count: '--',
    hint: '进入热搜与话题管理',
    targetTab: 'hotTopics',
  },
  {
    key: 'timeline-refresh',
    title: 'Timeline 管理',
    count: dashboard.value?.timeline_pending_count ?? '--',
    hint: '未生成或失败的 Timeline',
    targetTab: 'timelines',
  },
])

const statusCards = computed<StatusCard[]>(() => [
  {
    key: 'backend',
    title: '后端服务',
    value: opsStatusData.value?.backend?.status === 'normal' ? '正常' : (opsStatusData.value?.backend?.status || '未知'),
    tone: opsStatusData.value?.backend?.status === 'normal' ? 'success' : 'danger',
    hint: opsStatusData.value?.backend?.message || '—',
    icon: Monitor,
  },
  {
    key: 'database',
    title: '数据库',
    value: opsStatusData.value?.database?.status === 'normal' ? '正常' : (opsStatusData.value?.database?.status || '未知'),
    tone: opsStatusData.value?.database?.status === 'normal' ? 'success' : 'danger',
    hint: opsStatusData.value?.database?.message || '—',
    icon: DataBoard,
  },
  {
    key: 'ai',
    title: 'AI 服务',
    value: opsStatusData.value?.ai_service?.status === 'normal' ? '正常' : (opsStatusData.value?.ai_service?.status === 'unknown' ? '未知' : '异常'),
    tone: opsStatusData.value?.ai_service?.status === 'normal' ? 'success' : (opsStatusData.value?.ai_service?.status === 'unknown' ? 'info' : 'warning'),
    hint: opsStatusData.value?.ai_service?.message || 'AI 服务健康检查状态',
    icon: Setting,
  },
  {
    key: 'backup',
    title: '备份状态',
    value: backupData.value?.items?.[0]?.status === 'success' ? '正常' : (backupData.value?.items?.[0]?.status === 'unsupported' ? '不支持' : (backupData.value?.items?.[0]?.status || '未知')),
    tone: backupData.value?.items?.[0]?.status === 'success' ? 'success' : 'warning',
    hint: backupData.value?.items?.[0]?.created_at ? `最近备份：${backupData.value.items[0].created_at}` : '暂无备份记录',
    icon: Clock,
  },
])

const quickEntries = computed(() => (userStore.isAdmin ? adminQuickEntries : editorQuickEntries))
const sectionTitle = computed(() => sectionTitles[activeTab.value])
const trendEmptyText = computed(() => `${trendRangeLabel.value} 暂无趋势数据`)
const trendRangeLabel = computed(() => {
  if (trendRange.value === '7d') return '近 7 天'
  if (trendRange.value === '30d') return '近 30 天'
  return '近 90 天'
})

function setSectionLoading(section: AdminSection, value: boolean) {
  loadingState[section] = value
}

async function loadDashboard() {
  workbenchKey.value += 1
}

async function loadTrends() {
  trendsLoading.value = true
  try {
    const now = new Date()
    const start = new Date()
    const days = trendRange.value === '30d' ? 30 : (trendRange.value === '90d' ? 90 : 7)
    start.setDate(start.getDate() - days)
    const fmt = (d: Date) => d.toISOString().slice(0, 10) + ' 00:00:00'
    trendsData.value = await getAdminAnalyticsTrends({ start_time: fmt(start), end_time: fmt(now) })
    await nextTick()
    renderTrendCharts()
  } catch { trendsData.value = null }
  finally { trendsLoading.value = false }
}

function renderTrendCharts() {
  if (!trendContentChart && trendContentChartRef.value) {
    trendContentChart = echarts.init(trendContentChartRef.value)
  }
  if (!trendReviewChart && trendReviewChartRef.value) {
    trendReviewChart = echarts.init(trendReviewChartRef.value)
  }

  if (trendContentChart && trendsData.value?.content_trend?.length) {
    const data = trendsData.value.content_trend
    trendContentChart.setOption({
      tooltip: { trigger: 'axis' },
      legend: { data: ['新闻', '帖子', '评论'], top: 0 },
      grid: { left: 36, right: 12, top: 32, bottom: 24 },
      xAxis: { type: 'category', data: data.map(d => d.date.slice(5)), axisLabel: { rotate: 30, fontSize: 10 } },
      yAxis: { type: 'value', minInterval: 1 },
      series: [
        { name: '新闻', type: 'line', data: data.map(d => d.news_count), smooth: true, symbol: 'none' },
        { name: '帖子', type: 'line', data: data.map(d => d.post_count), smooth: true, symbol: 'none' },
        { name: '评论', type: 'bar', data: data.map(d => d.comment_count), barMaxWidth: 10 },
      ],
    }, true)
  } else if (trendContentChart) {
    trendContentChart.clear()
  }

  if (trendReviewChart && trendsData.value?.content_trend?.length) {
    const data = trendsData.value.content_trend
    const totalDaily = data.map(d => d.news_count + d.post_count + d.comment_count)
    trendReviewChart.setOption({
      tooltip: { trigger: 'axis' },
      legend: { data: ['新增内容总量', 'AI 调用'], top: 0 },
      grid: { left: 36, right: 12, top: 32, bottom: 24 },
      xAxis: { type: 'category', data: data.map(d => d.date.slice(5)), axisLabel: { rotate: 30, fontSize: 10 } },
      yAxis: { type: 'value', minInterval: 1 },
      series: [
        { name: '新增内容总量', type: 'bar', data: totalDaily, barMaxWidth: 12 },
        { name: 'AI 调用', type: 'line', data: data.map(d => d.ai_count), smooth: true, symbol: 'none' },
      ],
    }, true)
  } else if (trendReviewChart) {
    trendReviewChart.clear()
  }
}

function handleTrendRangeChange(range: TrendRange) {
  trendRange.value = range
  loadTrends()
}

// init charts on mount, but only after DOM is ready
onMounted(async () => {
  await loadDashboard()
  await loadTrends()
  await nextTick()
  if (trendContentChartRef.value) trendContentChart = echarts.init(trendContentChartRef.value)
  if (trendReviewChartRef.value) trendReviewChart = echarts.init(trendReviewChartRef.value)
  renderTrendCharts()
  window.addEventListener('resize', onResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  trendContentChart?.dispose()
  trendReviewChart?.dispose()
})

function onResize() {
  trendContentChart?.resize()
  trendReviewChart?.resize()
}

async function loadSection(section: AdminSection) {
  if (!userStore.isAdmin && (section === 'dashboard' || section === 'analytics')) {
    ElMessage.warning('当前账号无权访问工作台')
    activeTab.value = 'pending'
    return
  }

  activeTab.value = section

  switch (section) {
    case 'dashboard':
      break
    case 'pending':
      pendingCenterKey.value += 1
      break
    case 'news':
      break
    case 'posts':
      break
    case 'comments':
      break
    case 'hotTopics':
      break
    case 'timelines':
      break
    case 'users':
      break
    case 'aiConfig':
      break
    case 'config':
      break
    case 'ops':
      break
    case 'analytics':
      break
  }
}

async function handleTabChange(tabKey: string) {
  await loadSection(tabKey as AdminSection)
}

async function handleQuickEntryClick(entry: QuickEntry) {
  if (entry.adminOnly && !userStore.isAdmin) {
    ElMessage.warning('当前账号无权访问工作台')
    return
  }

  if (entry.status === 'coming-soon' || !entry.targetTab) {
    ElMessage.info(`${entry.title} 将在后续阶段接入真实业务接口`)
    return
  }

  await loadSection(entry.targetTab)
}

function getRoleLabel(role: string) {
  const roleMap: Record<string, string> = {
    user: '普通用户',
    editor: '审核/编辑',
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

function formatCount(value: string | number) {
  return value === '--' ? '--' : String(value)
}

onMounted(() => {
  void loadSection(activeTab.value)
})
</script>

<template>
  <main class="admin-container">
    <template v-if="userStore.isEditorOrAdmin">
      <header class="workbench-hero">
        <div class="hero-copy">
          <div class="hero-badge">管理后台</div>
          <h1>后台管理工作台</h1>
          <p>集中查看系统运行状态，并处理待审核内容。</p>
          <div class="hero-meta">
            <el-tag :type="userStore.isAdmin ? 'danger' : 'warning'" effect="plain">
              当前角色：{{ userStore.isAdmin ? '管理员' : '审核/编辑' }}
            </el-tag>
            <el-tag effect="plain">最近刷新：{{ lastLoadedAt || '暂无' }}</el-tag>
          </div>
        </div>

        <div class="hero-actions">
          <el-button type="primary" :icon="Refresh" @click="loadSection(activeTab)">查看</el-button>
          <el-button plain :icon="Clock" @click="handleTrendRangeChange('7d')">近 7 天</el-button>
          <el-button plain :icon="Clock" @click="handleTrendRangeChange('30d')">近 30 天</el-button>
          <el-button plain :icon="Clock" @click="handleTrendRangeChange('90d')">近 90 天</el-button>
        </div>
      </header>

      <div class="admin-layout">
        <aside class="admin-sidebar">
          <el-card class="sidebar-card profile-card" shadow="never">
            <div class="profile-row">
              <el-avatar :size="44">
                {{ userStore.userInfo?.nickname?.slice(0, 1) || 'A' }}
              </el-avatar>
              <div class="profile-meta">
                <strong>{{ userStore.userInfo?.nickname }}</strong>
                <span>{{ getRoleLabel(userStore.role) }}</span>
              </div>
            </div>
            <p class="profile-hint">根据当前角色展示可访问的后台能力。</p>
          </el-card>

          <el-card class="sidebar-card menu-card" shadow="never">
            <div class="sidebar-title">功能导航</div>
            <el-menu class="admin-menu" :default-active="activeTab" @select="handleTabChange">
              <el-menu-item v-for="item in sidebarSections" :key="item.key" :index="item.key">
                <component :is="item.icon" :size="18" class="menu-icon" />
                <span>{{ item.label }}</span>
              </el-menu-item>
            </el-menu>
          </el-card>

          <el-card class="sidebar-card role-card" shadow="never">
            <div class="sidebar-title">权限说明</div>
            <div class="role-group">
              <div class="role-group__title">审核/编辑权限</div>
              <div class="role-group__items">
                <el-tag v-for="item in ['内容审核', '评论管理', '社区管理', '热搜维护', 'Timeline 管理']" :key="item" size="small" effect="plain">
                  {{ item }}
                </el-tag>
              </div>
            </div>
            <div v-if="userStore.isAdmin" class="role-group">
              <div class="role-group__title">管理员权限</div>
              <div class="role-group__items">
                <el-tag v-for="item in ['账号管理', '角色权限', '系统配置', 'AI 配置', '日志查看', '数据备份', '内容总览']" :key="item" size="small" effect="plain">
                  {{ item }}
                </el-tag>
              </div>
            </div>
          </el-card>
        </aside>

        <section class="admin-main">
          <AdminWorkbench :key="workbenchKey" v-if="activeTab === 'dashboard'" />

          <AdminAnalyticsDashboard v-if="activeTab === 'analytics'" @navigate="(tab: string) => loadSection(tab as AdminSection)" />

          <AdminPendingCenter
            v-if="activeTab === 'pending'"
            :key="pendingCenterKey"
            @changed="loadDashboard"
          />

          <AdminNewsManagement
            v-if="activeTab === 'news'"
            @changed="loadDashboard"
          />

          <AdminPostManagement
            v-if="activeTab === 'posts'"
            @changed="loadDashboard"
          />

          <AdminCommentReview
            v-if="activeTab === 'comments'"
            @changed="loadDashboard"
          />

          <AdminHotTopicManagement
            v-if="activeTab === 'hotTopics'"
            @changed="loadDashboard"
          />

          <AdminTimelineManagement
            v-if="activeTab === 'timelines'"
            @changed="loadDashboard"
          />

          <AdminUserManagement v-if="activeTab === 'users'" @changed="loadDashboard" />

          <AdminAIConfigManagement v-if="activeTab === 'aiConfig'" @changed="loadDashboard" />

          <AdminSystemConfigManagement v-if="activeTab === 'config'" @changed="loadDashboard" />

          <AdminOpsManagement v-if="activeTab === 'ops'" />
        </section>
      </div>
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
  width: 100%;
  max-width: 1480px;
  margin: 0 auto;
  padding: 20px 24px;
  min-height: 100vh;
}

.workbench-hero {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 24px;
  padding: 18px 24px;
  margin-bottom: 20px;
  background: linear-gradient(135deg, rgba(64, 158, 255, 0.12), rgba(103, 194, 58, 0.08));
  border: 1px solid var(--color-border-light);
  border-radius: 20px;
}

.hero-copy {
  min-width: 0;
}

.hero-badge {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  margin-bottom: 12px;
  font-size: 12px;
  color: var(--color-primary);
  background: rgba(64, 158, 255, 0.1);
  border-radius: 999px;
}

.hero-copy h1 {
  margin: 0 0 8px;
  font-size: 22px;
  color: var(--color-text-primary);
}

.hero-copy p {
  margin: 0;
  color: var(--color-text-secondary);
}

.hero-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 16px;
}

.hero-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  justify-content: flex-end;
}

.admin-layout {
  display: grid;
  grid-template-columns: 240px minmax(0, 1fr);
  gap: 20px;
  align-items: start;
}

.admin-sidebar {
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-width: 0;
  position: sticky;
  top: 88px;
  align-self: start;
  height: auto;
  max-height: none;
  overflow: visible;
}

.admin-sidebar .sidebar-card {
  overflow: visible;
  height: auto;
  max-height: none;
}

.admin-sidebar .menu-card {
  display: flex;
  flex-direction: column;
  overflow: visible;
}

.admin-sidebar .menu-card :deep(.el-card__body) {
  display: flex;
  flex-direction: column;
  overflow: visible;
}

.admin-sidebar .admin-menu {
  overflow: visible;
  max-height: none;
}

.admin-sidebar .profile-card,
.admin-sidebar .role-card {
  flex: 0 0 auto;
  overflow: visible;
}

.sidebar-card {
  border-radius: 18px;
}

.sidebar-title {
  margin-bottom: 12px;
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.profile-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.profile-meta {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.profile-meta strong {
  color: var(--color-text-primary);
}

.profile-meta span,
.profile-hint {
  color: var(--color-text-secondary);
  font-size: 13px;
}

.profile-hint {
  margin: 14px 0 0;
  line-height: 1.6;
}

.admin-menu {
  border-right: 0;
}

.admin-menu :deep(.el-menu-item) {
  gap: 10px;
  margin-bottom: 6px;
  border-radius: 10px;
  height: 44px;
  line-height: 44px;
}
.admin-menu :deep(.el-menu-item .menu-icon),
.admin-menu :deep(.el-menu-item svg),
.admin-menu :deep(.el-menu-item .el-icon) {
  width: 20px !important;
  height: 20px !important;
  flex: 0 0 20px !important;
  font-size: 20px !important;
}
.admin-menu :deep(.el-menu-item img) {
  width: 20px !important;
  height: 20px !important;
  object-fit: contain;
}

.role-group + .role-group {
  margin-top: 16px;
}

.role-group__title {
  margin-bottom: 10px;
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-secondary);
}

.role-group__items {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.admin-main {
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-width: 0;
  overflow: visible;
}

.stats-card,
.panel-card,
.unauthorized-card {
  border-radius: 18px;
}

.section-heading,
.panel-header,
.todo-item__title-row,
.status-item__title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.section-heading h2,
.panel-header h3 {
  margin: 0 0 6px;
  color: var(--color-text-primary);
}

.section-heading p,
.panel-header p {
  margin: 0;
  color: var(--color-text-secondary);
}

.quick-card :deep(.el-card__body) {
  overflow: hidden;
}

.section-alert {
  margin: 16px 0;
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 14px;
}

.metric-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 16px;
  background: var(--color-bg-page);
  border: 1px solid var(--color-border-light);
  border-radius: 16px;
}

.metric-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  border-radius: 14px;
  flex: 0 0 auto;
}
.metric-icon :deep(svg),
.metric-icon svg {
  width: 22px !important;
  height: 22px !important;
}

.metric-content {
  min-width: 0;
}

.metric-value {
  font-size: 24px;
  font-weight: 700;
  line-height: 1.1;
  color: var(--color-text-primary);
}

.metric-title {
  margin-top: 4px;
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.metric-hint {
  margin-top: 4px;
  font-size: 12px;
  color: var(--color-text-secondary);
}

.middle-grid {
  display: grid;
  grid-template-columns: 1.1fr 1fr 1.1fr;
  gap: 16px;
}

.bottom-grid {
  display: grid;
  grid-template-columns: 1.2fr 1fr;
  gap: 16px;
}

.chart-box {
  width: 100%;
  height: 280px;
  min-height: 280px;
}

.todo-list,
.status-list,
.quick-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.todo-item {
  display: flex;
  align-items: center;
  gap: 14px;
  width: 100%;
  padding: 14px 16px;
  text-align: left;
  border: 1px solid var(--color-border-light);
  border-radius: 16px;
  background: var(--color-bg-page);
  cursor: pointer;
  transition: all 0.25s ease;
  white-space: nowrap;
  min-width: 0;
}

.todo-item:hover {
  border-color: #409eff;
  box-shadow: 0 8px 24px rgba(64, 158, 255, 0.12);
  transform: translateY(-1px);
}

.todo-item--disabled {
  cursor: not-allowed;
  opacity: 0.68;
}

.quick-item {
  display: flex;
  align-items: center;
  gap: 14px;
  width: 100%;
  padding: 12px 14px;
  text-align: left;
  border: 1px solid var(--color-border-light);
  border-radius: 16px;
  background: var(--color-bg-page);
  cursor: pointer;
  transition: all 0.25s ease;
  min-width: 0;
}

.quick-item:hover {
  border-color: #409eff;
  box-shadow: 0 8px 24px rgba(64, 158, 255, 0.12);
  transform: translateY(-1px);
}

.quick-item--coming-soon {
  opacity: 0.72;
}

.quick-item--admin {
  border-style: dashed;
}

.quick-item__icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 12px;
  color: #409eff;
  background: rgba(64, 158, 255, 0.12);
  flex: 0 0 auto;
}
.quick-item__icon :deep(svg),
.quick-item__icon svg {
  width: 20px !important;
  height: 20px !important;
}

.quick-item__arrow {
  margin-left: auto;
  color: var(--color-text-placeholder);
  width: 16px;
  height: 16px;
  flex: 0 0 16px;
}
.quick-item__arrow :deep(svg),
.quick-item__arrow svg {
  width: 16px !important;
  height: 16px !important;
}

.quick-item__body {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.quick-item__body span {
  font-size: 13px;
  color: var(--color-text-secondary);
  line-height: 1.5;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.quick-item__title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.quick-item__title-row strong {
  white-space: nowrap;
}

.todo-item__arrow {
  margin-left: auto;
  color: var(--color-text-placeholder);
  width: 16px;
  height: 16px;
  flex: 0 0 16px;
}
.todo-item__arrow :deep(svg),
.todo-item__arrow svg {
  width: 16px !important;
  height: 16px !important;
}

.todo-item__body {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.todo-item__body span {
  font-size: 13px;
  color: var(--color-text-secondary);
  line-height: 1.5;
}

.status-item__body {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.status-item__body span {
  font-size: 13px;
  color: var(--color-text-secondary);
  line-height: 1.5;
}

.status-item {
  display: flex;
  gap: 14px;
  padding: 14px;
  background: var(--color-bg-page);
  border: 1px solid var(--color-border-light);
  border-radius: 16px;
}

.status-item__icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 12px;
  flex: 0 0 auto;
}
.status-item__icon :deep(svg),
.status-item__icon svg {
  width: 20px !important;
  height: 20px !important;
}

.status-item__icon--success {
  color: #67c23a;
  background: rgba(103, 194, 58, 0.12);
}

.status-item__icon--warning {
  color: #e6a23c;
  background: rgba(230, 162, 60, 0.12);
}

.status-item__icon--info {
  color: #409eff;
  background: rgba(64, 158, 255, 0.12);
}

.status-item__icon--danger {
  color: #f56c6c;
  background: rgba(245, 108, 108, 0.12);
}

.panel-card {
  min-width: 0;
  overflow: hidden;
}

.range-tabs {
  display: flex;
  gap: 10px;
  margin-bottom: 14px;
}

.range-tag {
  cursor: pointer;
}

.pending-table {
  width: 100%;
}

.module-card {
  margin-top: 4px;
}

.config-form {
  padding-top: 8px;
}

.section-loading,
.empty-wrap {
  padding: 20px 0;
  max-height: 300px;
}
.empty-wrap :deep(.el-empty__image) {
  max-width: 80px;
}
.empty-wrap :deep(.el-empty__image svg) {
  width: 80px !important;
  height: 80px !important;
}

.unauthorized-card {
  max-width: 560px;
  margin: 48px auto;
}

@media (max-width: 1360px) {
  .metric-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .middle-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .bottom-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 1100px) {
  .admin-layout {
    grid-template-columns: 1fr;
  }

  .admin-sidebar {
    order: 2;
  }

  .admin-main {
    order: 1;
  }
}

@media (max-width: 960px) {
  .metric-grid,
  .middle-grid {
    grid-template-columns: 1fr;
  }

  .workbench-hero {
    flex-direction: column;
  }

  .hero-actions {
    justify-content: flex-start;
  }
}
.panel-card--empty {
  min-height: 280px;
  max-height: 320px;
}
.panel-card--empty :deep(.el-empty) {
  padding: 20px 0;
}
.panel-card--empty :deep(.el-empty__image) {
  max-width: 80px;
}
.panel-card--empty :deep(.el-empty__image svg) {
  width: 80px !important;
  height: 80px !important;
}
</style>
