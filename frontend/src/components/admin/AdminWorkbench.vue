<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Clock,
  DataBoard,
  Monitor,
  Refresh,
  TrendCharts,
  UserFilled,
  Warning,
} from '@element-plus/icons-vue'
import {
  getAdminOpsDatabase,
  getAdminOpsStatus,
  getDashboard,
  type AdminBackupRecordListResponse,
  type AdminDashboard,
  type AdminOpsDatabaseResponse,
  type AdminOpsStatusResponse,
} from '@/api/admin'
import { useUserStore } from '@/stores/user'

type AdminSection = 'analytics' | 'pending' | 'news' | 'posts' | 'comments' | 'hotTopics' | 'users' | 'aiConfig' | 'config' | 'ops'
type TagTone = 'success' | 'warning' | 'danger' | 'info' | 'primary'

const emit = defineEmits<{ navigate: [section: AdminSection] }>()

const userStore = useUserStore()
const loading = ref(false)
const error = ref('')
const lastRefreshTime = ref('')
const dashboard = ref<AdminDashboard | null>(null)
const opsStatus = ref<AdminOpsStatusResponse | null>(null)
const backupRecords = ref<AdminBackupRecordListResponse | null>(null)
const opsDatabase = ref<AdminOpsDatabaseResponse | null>(null)

const kpiCards = computed(() => [
  {
    key: 'today_new_users',
    title: '今日新增用户',
    value: dashboard.value?.today_new_users ?? '--',
    hint: '来自用户注册数据',
    icon: UserFilled,
  },
  {
    key: 'active_users_7d',
    title: '7 日活跃用户',
    value: dashboard.value?.active_users_7d ?? '--',
    hint: '按访问记录估算',
    icon: TrendCharts,
  },
  {
    key: 'pending_total',
    title: '当前待审核',
    value: dashboard.value?.pending_total ?? '--',
    hint: '新闻、帖子、评论合计',
    icon: Warning,
  },
  {
    key: 'today_review_done',
    title: '今日内容处理',
    value: dashboard.value?.today_review_done ?? '--',
    hint: '审核、折叠、删除、恢复等内容操作',
    icon: Clock,
  },
  {
    key: 'today_ai_calls',
    title: '今日 AI 调用',
    value: dashboard.value?.today_ai_calls ?? '--',
    hint: '来自 ai_generate_record',
    icon: Monitor,
  },
  {
    key: 'avg_response_ms',
    title: '平均响应耗时',
    value: dashboard.value?.avg_response_ms != null ? `${dashboard.value.avg_response_ms} ms` : '暂无',
    hint: 'AI 调用响应统计',
    icon: DataBoard,
  },
])

const pendingItems = computed(() => [
  { key: 'news', label: '待审新闻', value: dashboard.value?.pending_news_count ?? 0 },
  { key: 'posts', label: '待审帖子', value: dashboard.value?.pending_post_count ?? 0 },
  { key: 'comments', label: '待审评论', value: dashboard.value?.pending_comment_count ?? 0 },
  { key: 'timeline', label: 'Timeline 待处理', value: dashboard.value?.timeline_pending_count ?? 0 },
])

const statusItems = computed<Array<{ key: string; label: string; value: string; tone: TagTone }>>(() => {
  return [
    {
      key: 'backend',
      label: '后端服务',
      value: opsStatus.value?.backend?.status === 'normal' ? '正常' : (opsStatus.value?.backend?.status || '未知'),
      tone: opsStatus.value?.backend?.status === 'normal' ? 'success' : 'danger',
    },
    {
      key: 'database',
      label: '数据库',
      value: opsStatus.value?.database?.status === 'normal' ? '正常' : (opsStatus.value?.database?.status || '未知'),
      tone: opsStatus.value?.database?.status === 'normal' ? 'success' : 'danger',
    },
    {
      key: 'ai',
      label: 'AI 服务',
      value: opsStatus.value?.ai_service?.status === 'normal' ? '正常' : (opsStatus.value?.ai_service?.status || '正常'),
      tone: opsStatus.value?.ai_service?.status === 'normal' ? 'success' : (opsStatus.value?.ai_service?.status === 'unknown' ? 'warning' : 'danger'),
    },
    {
      key: 'tables',
      label: '数据库表',
      value: `${opsDatabase.value?.tables?.length ?? 0} 张`,
      tone: 'info',
    },
  ]
})

async function refreshWorkbench() {
  if (!userStore.isAdmin) return
  loading.value = true
  error.value = ''
  try {
    const [dashRes, statusRes, databaseRes] = await Promise.allSettled([
      getDashboard(),
      getAdminOpsStatus(),
      getAdminOpsDatabase(),
    ])
    if (dashRes.status === 'fulfilled') dashboard.value = dashRes.value
    if (statusRes.status === 'fulfilled') opsStatus.value = statusRes.value
    if (databaseRes.status === 'fulfilled') opsDatabase.value = databaseRes.value

    if ([dashRes, statusRes, databaseRes].some(item => item.status === 'rejected')) {
      error.value = '部分首页数据加载失败，请检查后端服务状态。'
    }
    lastRefreshTime.value = new Date().toLocaleString()
  } catch (err) {
    error.value = err instanceof Error ? err.message : '后台首页数据加载失败'
    ElMessage.error(error.value)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  void refreshWorkbench()
})
</script>

<template>
  <section class="admin-workbench">
    <el-result
      v-if="!userStore.isAdmin"
      icon="warning"
      title="当前账号无权访问后台首页"
      sub-title="请使用管理员账号查看后台首页。"
    />

    <template v-else>
      <el-card class="hero-card" shadow="never">
        <div class="hero-main">
          <div>
            <div class="hero-badge">管理后台 · 首页</div>
            <h1>后台首页</h1>
            <p>这里仅保留关键指标、待办事项、服务状态和常用入口。详细趋势、排行和风险图表请进入“数据看板”。</p>
          </div>
          <div class="hero-actions">
            <el-tag effect="plain">最近刷新：{{ lastRefreshTime || '暂无' }}</el-tag>
            <el-button type="primary" :icon="Refresh" :loading="loading" @click="refreshWorkbench">刷新</el-button>
          </div>
        </div>
      </el-card>

      <el-alert v-if="error" :title="error" type="warning" show-icon :closable="false" />

      <el-card class="panel-card" shadow="never" v-loading="loading">
        <div class="section-head">
          <div>
            <h2>核心 KPI</h2>
            <p>用于快速判断后台当前运行状态，不承载详细分析。</p>
          </div>
        </div>
        <div class="kpi-grid">
          <article v-for="item in kpiCards" :key="item.key" class="kpi-item">
            <div class="kpi-icon"><component :is="item.icon" :size="22" /></div>
            <div>
              <strong>{{ item.value }}</strong>
              <span>{{ item.title }}</span>
              <small>{{ item.hint }}</small>
            </div>
          </article>
        </div>
      </el-card>

      <div class="home-grid">
        <el-card class="panel-card" shadow="never">
          <div class="section-head">
            <div>
              <h3>待办事项</h3>
              <p>审核类工作统一进入待审核中心处理。</p>
            </div>
            <el-button text type="primary" @click="emit('navigate', 'pending')">进入待审核中心</el-button>
          </div>
          <div class="compact-list">
            <div v-for="item in pendingItems" :key="item.key" class="compact-item">
              <span>{{ item.label }}</span>
              <el-tag :type="Number(item.value) > 0 ? 'warning' : 'info'" effect="plain">{{ item.value }}</el-tag>
            </div>
          </div>
        </el-card>

        <el-card class="panel-card" shadow="never">
          <div class="section-head">
            <div>
              <h3>服务状态</h3>
              <p>只展示可用于演示的健康状态，不提供真实备份执行入口。</p>
            </div>
            <el-button text type="primary" @click="emit('navigate', 'ops')">查看运维</el-button>
          </div>
          <div class="compact-list">
            <div v-for="item in statusItems" :key="item.key" class="compact-item">
              <span>{{ item.label }}</span>
              <el-tag :type="item.tone" effect="plain">{{ item.value }}</el-tag>
            </div>
          </div>
        </el-card>
      </div>
    </template>
  </section>
</template>

<style scoped>
.admin-workbench {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.hero-card,
.panel-card {
  border-radius: 16px;
  border: 1px solid var(--el-border-color-lighter);
}

.hero-main {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  align-items: flex-start;
}

.hero-badge {
  display: inline-flex;
  padding: 5px 10px;
  border-radius: 999px;
  background: var(--el-fill-color-light);
  color: var(--el-color-primary);
  font-size: 12px;
  margin-bottom: 10px;
}

.hero-main h1,
.section-head h2,
.section-head h3 {
  margin: 0;
}

.hero-main p,
.section-head p {
  margin: 6px 0 0;
  color: var(--el-text-color-secondary);
  line-height: 1.6;
}

.hero-actions,
.section-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.section-head {
  margin-bottom: 16px;
}

.kpi-grid {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(6, minmax(0, 1fr));
}

.kpi-item {
  display: flex;
  gap: 12px;
  padding: 14px;
  border-radius: 12px;
  background: var(--el-fill-color-extra-light);
  border: 1px solid var(--el-border-color-lighter);
}

.kpi-icon {
  width: 42px;
  height: 42px;
  border-radius: 12px;
  display: grid;
  place-items: center;
  flex: 0 0 42px;
  color: var(--el-color-primary);
  background: var(--el-color-primary-light-9);
}

.kpi-item strong {
  display: block;
  font-size: 22px;
  line-height: 1.1;
}

.kpi-item span {
  display: block;
  margin-top: 4px;
  font-weight: 600;
}

.kpi-item small {
  display: block;
  margin-top: 4px;
  color: var(--el-text-color-secondary);
  line-height: 1.45;
}

.home-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.compact-list {
  display: grid;
  gap: 10px;
}

.compact-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  border-radius: 12px;
  background: var(--el-fill-color-extra-light);
  border: 1px solid var(--el-border-color-lighter);
}

@media (max-width: 1400px) {
  .kpi-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 960px) {
  .hero-main,
  .home-grid {
    grid-template-columns: 1fr;
  }

  .hero-main,
  .home-grid {
    display: grid;
  }

  .kpi-grid {
    grid-template-columns: 1fr;
  }
}
</style>
