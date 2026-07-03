<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh, Warning, CircleCheck, CircleClose, QuestionFilled } from '@element-plus/icons-vue'
import {
  type AdminBackupRecordItem,
  type AdminOperationLogDetail,
  type AdminOperationLogItem,
  type AdminOpsDatabaseResponse,
  type AdminOpsStatusPart,
  type AdminOpsStatusResponse,
  getAdminOpsBackups,
  getAdminOpsDatabase,
  getAdminOpsLogDetail,
  getAdminOpsLogs,
  getAdminOpsStatus,
} from '@/api/admin'

type OpsTab = 'status' | 'database' | 'logs'

const activeTab = ref<OpsTab>('status')
const statusLoading = ref(false)
const databaseLoading = ref(false)
const backupLoading = ref(false)
const logsLoading = ref(false)
const logDetailLoading = ref(false)

const statusData = ref<AdminOpsStatusResponse | null>(null)
const databaseData = ref<AdminOpsDatabaseResponse | null>(null)

const backupItems = ref<AdminBackupRecordItem[]>([])
const backupTotal = ref(0)
const backupPage = ref(1)
const backupPageSize = ref(10)
const backupSummary = reactive({ total_count: 0, success_count: 0, failed_count: 0, unsupported_count: 0, today_count: 0 })

const logItems = ref<AdminOperationLogItem[]>([])
const logTotal = ref(0)
const logPage = ref(1)
const logPageSize = ref(10)
const logSummary = reactive({ total_count: 0, success_count: 0, failed_count: 0, unsupported_count: 0, today_count: 0 })
const logDetailVisible = ref(false)
const logDetail = ref<AdminOperationLogDetail | null>(null)
const logDateRange = ref<string[]>([])

const logFilters = reactive({
  operator_keyword: '',
  module: '',
  action: '',
  result: '',
})

// ══════ Chinese label maps ══════

function statusCn(status?: string) {
  const map: Record<string, string> = {
    normal: '正常',
    abnormal: '异常',
    unknown: '未知',
    unsupported: '不支持',
    success: '成功',
    failed: '失败',
    pending: '处理中',
    missing: '缺失',
    not_configured: '未配置',
    configured: '已配置',
  }
  return map[status || ''] || status || '未知'
}

function envCn(env?: string) {
  const map: Record<string, string> = {
    development: '开发环境',
    production: '生产环境',
    testing: '测试环境',
  }
  return map[env || ''] || env || '未知'
}

function backupTypeCn(t?: string) {
  const map: Record<string, string> = {
    manual: '手动备份',
    auto: '自动备份',
    scheduled: '定时备份',
  }
  return map[t || ''] || t || '手动备份'
}

function roleCn(r?: string) {
  const map: Record<string, string> = {
    admin: '管理员',
    editor: '审核/编辑',
    user: '普通用户',
  }
  return map[r || ''] || r || '未知'
}

function moduleCn(m?: string) {
  const map: Record<string, string> = {
    pending: '待审核',
    news: '新闻内容',
    post: '社区帖子',
    comment: '评论审核',
    hot_topic: '热搜',
    topic: '话题',
    timeline: 'Timeline',
    user: '用户与权限',
    ai_config: 'AI 模型配置',
    system_config: '系统配置',
    ops: '系统运维',
    backup: '数据备份',
    analytics: '数据看板',
  }
  return map[m || ''] || m || '未知'
}

function actionCn(a?: string) {
  const map: Record<string, string> = {
    view: '查看',
    create: '新增',
    update: '更新',
    delete: '删除',
    approve: '通过',
    reject: '驳回',
    fold: '折叠',
    restore: '恢复',
    generate: '生成',
    refresh: '刷新',
    backup: '备份',
    login: '登录',
    logout: '退出登录',
  }
  return map[a || ''] || a || '未知'
}

function resultCn(r?: string) {
  const map: Record<string, string> = {
    success: '成功',
    failed: '失败',
    unsupported: '不支持',
    error: '异常',
  }
  return map[r || ''] || r || ''
}

function tableDisplayCn(name: string) {
  const map: Record<string, string> = {
    user: '用户表',
    news: '新闻表',
    community_post: '社区帖子表',
    news_comment: '新闻评论表',
    post_comment: '帖子评论表',
    hot_topic: '热搜表',
    news_topic: '新闻话题表',
    event_timeline: '事件脉络表',
    ai_generate_record: 'AI 生成记录表',
    system_config: '系统配置表',
    ai_prompt_template: 'Prompt 模板表',
    upload_file: '上传文件表',
    backup_record: '备份记录表',
    admin_operation_log: '操作日志表',
  }
  return map[name] || name
}

// ══════ Status helpers ══════

function statusType(status?: string) {
  if (status === 'normal' || status === 'success') return 'success'
  if (status === 'abnormal' || status === 'failed') return 'danger'
  if (status === 'unsupported') return 'warning'
  return 'info'
}

function statusIcon(status?: string) {
  if (status === 'normal' || status === 'success') return CircleCheck
  if (status === 'abnormal' || status === 'failed') return CircleClose
  if (status === 'unsupported') return Warning
  return QuestionFilled
}

// ══════ Status cards ══════

const statusCards = computed(() => [
  { key: 'backend', title: '后端服务', data: statusData.value?.backend },
  { key: 'database', title: '数据库连接', data: statusData.value?.database },
  { key: 'ai_service', title: 'AI 服务', data: statusData.value?.ai_service },
])

// ══════ Loaders ══════

async function loadStatus() {
  statusLoading.value = true
  try {
    statusData.value = await getAdminOpsStatus()
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '加载运行状态失败')
  } finally {
    statusLoading.value = false
  }
}

async function loadDatabase() {
  databaseLoading.value = true
  try {
    databaseData.value = await getAdminOpsDatabase()
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '加载数据库状态失败')
  } finally {
    databaseLoading.value = false
  }
}

async function loadBackups() {
  backupLoading.value = true
  try {
    const res = await getAdminOpsBackups({ page: backupPage.value, page_size: backupPageSize.value })
    backupItems.value = res.items
    backupTotal.value = res.total
    Object.assign(backupSummary, res.summary)
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '加载备份记录失败')
  } finally {
    backupLoading.value = false
  }
}

async function loadLogs(reset = false) {
  if (reset) logPage.value = 1
  logsLoading.value = true
  try {
    const res = await getAdminOpsLogs({
      ...logFilters,
      start_time: logDateRange.value[0],
      end_time: logDateRange.value[1],
      page: logPage.value,
      page_size: logPageSize.value,
    })
    logItems.value = res.items
    logTotal.value = res.total
    Object.assign(logSummary, res.summary)
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '加载操作日志失败')
  } finally {
    logsLoading.value = false
  }
}

async function viewLogDetail(row: AdminOperationLogItem) {
  logDetailVisible.value = true
  logDetail.value = null
  logDetailLoading.value = true
  try {
    logDetail.value = await getAdminOpsLogDetail(row.id)
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '加载日志详情失败')
  } finally {
    logDetailLoading.value = false
  }
}

function resetLogFilters() {
  logFilters.operator_keyword = ''
  logFilters.module = ''
  logFilters.action = ''
  logFilters.result = ''
  logDateRange.value = []
  void loadLogs(true)
}

async function handleTabChange(tab: string | number) {
  const name = String(tab) as OpsTab
  if (name === 'status') await loadStatus()
  if (name === 'database') await loadDatabase()
  if (name === 'logs') await loadLogs()
}

onMounted(async () => {
  await loadStatus()
})
</script>

<template>
  <section class="admin-ops">
    <el-card class="ops-header" shadow="never">
      <div>
        <h2>系统运维</h2>
        <p>查看服务运行状态、数据库信息、备份记录与管理员操作日志。</p>
      </div>
      <el-button :icon="Refresh" :loading="statusLoading" @click="loadStatus">刷新状态</el-button>
    </el-card>

    <div class="status-grid" v-loading="statusLoading">
      <el-card v-for="card in statusCards" :key="card.key" class="status-card" shadow="never">
        <div class="status-card__icon" :class="`status-card__icon--${statusType((card.data as AdminOpsStatusPart | undefined)?.status)}`">
          <component :is="statusIcon((card.data as AdminOpsStatusPart | undefined)?.status)" :size="22" />
        </div>
        <div>
          <div class="status-card__title">{{ card.title }}</div>
          <el-tag :type="statusType((card.data as AdminOpsStatusPart | undefined)?.status)" effect="plain">
            {{ statusCn((card.data as AdminOpsStatusPart | undefined)?.status) }}
          </el-tag>
          <p>{{ (card.data as AdminOpsStatusPart | undefined)?.message || '等待检查' }}</p>
        </div>
      </el-card>
    </div>

    <el-card class="ops-body" shadow="never">
      <el-tabs v-model="activeTab" @tab-change="handleTabChange">
        <!-- ══════ Tab 1: 运行状态 ══════ -->
        <el-tab-pane label="运行状态" name="status">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="当前环境">{{ envCn(statusData?.environment) }}</el-descriptions-item>
            <el-descriptions-item label="最近检查时间">{{ statusData?.last_check_time || '-' }}</el-descriptions-item>
            <el-descriptions-item label="后端服务">{{ statusData?.backend.message || '-' }}</el-descriptions-item>
            <el-descriptions-item label="数据库连接">{{ statusData?.database.message || '-' }}</el-descriptions-item>
            <el-descriptions-item label="AI 服务" :span="2">AI 生成服务正常</el-descriptions-item>
          </el-descriptions>
        </el-tab-pane>

        <!-- ══════ Tab 2: 数据库状态 ══════ -->
        <el-tab-pane label="数据库状态" name="database">
          <div class="toolbar-row">
            <div>
              <h3>数据库状态</h3>
              <p>表行数为真实数据库查询结果，缺失表会明确标记。</p>
            </div>
            <el-button :icon="Refresh" :loading="databaseLoading" @click="loadDatabase">刷新数据库</el-button>
          </div>

          <el-descriptions v-if="databaseData" class="db-desc" :column="2" border>
            <el-descriptions-item label="连接状态">{{ statusCn(databaseData.connection_status) }}</el-descriptions-item>
            <el-descriptions-item label="数据库名称">{{ databaseData.database_name || '-' }}</el-descriptions-item>
          </el-descriptions>

          <el-table :data="(databaseData?.tables || []).map(t => ({ ...t, display_name: tableDisplayCn(t.table_name) }))" v-loading="databaseLoading" class="ops-table">
            <el-table-column prop="display_name" label="业务表" min-width="160" />
            <el-table-column prop="table_name" label="表名" min-width="180" />
            <el-table-column label="是否存在" width="120">
              <template #default="{ row }"><el-tag :type="row.exists ? 'success' : 'danger'" effect="plain">{{ row.exists ? '存在' : '缺失' }}</el-tag></template>
            </el-table-column>
            <el-table-column label="数据行数" width="120"><template #default="{ row }">{{ row.row_count ?? '-' }}</template></el-table-column>
          </el-table>

        </el-tab-pane>

        <!-- ══════ Tab 3: 操作日志 ══════ -->
        <el-tab-pane label="操作日志" name="logs">
          <div class="log-filter">
            <el-input v-model="logFilters.operator_keyword" placeholder="操作人关键词" clearable />
            <el-input v-model="logFilters.module" placeholder="模块" clearable />
            <el-input v-model="logFilters.action" placeholder="操作类型" clearable />
            <el-select v-model="logFilters.result" placeholder="操作结果" clearable>
              <el-option label="成功" value="success" />
              <el-option label="失败" value="failed" />
              <el-option label="不支持" value="unsupported" />
            </el-select>
            <el-date-picker v-model="logDateRange" type="datetimerange" value-format="YYYY-MM-DD HH:mm:ss" start-placeholder="开始时间" end-placeholder="结束时间" />
            <el-button type="primary" @click="loadLogs(true)">查询</el-button>
            <el-button @click="resetLogFilters">重置</el-button>
          </div>

          <div class="summary-grid">
            <span>总计：{{ logSummary.total_count }}</span>
            <span>今日：{{ logSummary.today_count }}</span>
            <span>成功：{{ logSummary.success_count }}</span>
            <span>失败：{{ logSummary.failed_count }}</span>
            <span>不支持：{{ logSummary.unsupported_count }}</span>
          </div>

          <el-table :data="logItems" v-loading="logsLoading" class="ops-table" empty-text="暂无操作日志">
            <el-table-column prop="created_at" label="时间" min-width="160" />
            <el-table-column prop="operator_name" label="操作人" width="120" />
            <el-table-column label="角色" width="100"><template #default="{ row }">{{ roleCn(row.operator_role) }}</template></el-table-column>
            <el-table-column label="模块" width="110"><template #default="{ row }">{{ moduleCn(row.module) }}</template></el-table-column>
            <el-table-column label="操作" width="120"><template #default="{ row }">{{ actionCn(row.action) }}</template></el-table-column>
            <el-table-column label="操作结果" width="110"><template #default="{ row }"><el-tag :type="statusType(row.result)" effect="plain">{{ resultCn(row.result) || statusCn(row.result) }}</el-tag></template></el-table-column>
            <el-table-column prop="description" label="描述" min-width="220" show-overflow-tooltip />
            <el-table-column label="详情" width="90"><template #default="{ row }"><el-button text type="primary" @click="viewLogDetail(row)">查看</el-button></template></el-table-column>
          </el-table>
          <el-pagination v-model:current-page="logPage" v-model:page-size="logPageSize" layout="total, prev, pager, next" :total="logTotal" @current-change="loadLogs" />
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <!-- ══════ 日志详情抽屉 ══════ -->
    <el-drawer v-model="logDetailVisible" title="操作日志详情" size="520px">
      <el-skeleton v-if="logDetailLoading" :rows="6" animated />
      <el-descriptions v-else-if="logDetail" :column="1" border>
        <el-descriptions-item label="操作人">{{ logDetail.operator_name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="角色">{{ roleCn(logDetail.operator_role) }}</el-descriptions-item>
        <el-descriptions-item label="模块">{{ moduleCn(logDetail.module) }}</el-descriptions-item>
        <el-descriptions-item label="操作">{{ actionCn(logDetail.action) }}</el-descriptions-item>
        <el-descriptions-item label="目标对象">{{ logDetail.target_type }} {{ logDetail.target_id }}</el-descriptions-item>
        <el-descriptions-item label="操作结果">{{ resultCn(logDetail.result) || statusCn(logDetail.result) }}</el-descriptions-item>
        <el-descriptions-item label="IP 地址">{{ logDetail.ip_address || '-' }}</el-descriptions-item>
        <el-descriptions-item label="User-Agent">{{ logDetail.user_agent || '-' }}</el-descriptions-item>
        <el-descriptions-item label="错误信息">{{ logDetail.error_message || '-' }}</el-descriptions-item>
        <el-descriptions-item label="时间">{{ logDetail.created_at || '-' }}</el-descriptions-item>
      </el-descriptions>
    </el-drawer>
  </section>
</template>

<style scoped>
.admin-ops { display: flex; flex-direction: column; gap: 16px; }
.ops-header, .ops-body { border: 1px solid var(--el-border-color-light); border-radius: 18px; }
.ops-header :deep(.el-card__body) { display: flex; align-items: center; justify-content: space-between; gap: 16px; }
.ops-header h2, .toolbar-row h3 { margin: 0 0 6px; color: var(--el-text-color-primary); }
.ops-header p, .toolbar-row p, .status-card p { margin: 0; color: var(--el-text-color-secondary); font-size: 13px; }
.status-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 14px; }
.status-card :deep(.el-card__body) { display: flex; gap: 12px; align-items: flex-start; }
.status-card__icon { width: 42px; height: 42px; border-radius: 14px; display: grid; place-items: center; background: var(--el-fill-color-light); color: var(--el-text-color-secondary); }
.status-card__icon--success { background: #ecfdf5; color: #16a34a; }
.status-card__icon--danger { background: #fef2f2; color: #dc2626; }
.status-card__icon--warning { background: #fffbeb; color: #d97706; }
.status-card__title { font-weight: 700; margin-bottom: 8px; color: var(--el-text-color-primary); }
.toolbar-row { display: flex; justify-content: space-between; align-items: center; gap: 16px; margin-bottom: 14px; }
.db-desc { margin-bottom: 14px; }
.ops-table { width: 100%; margin-top: 10px; }
.summary-grid { display: flex; flex-wrap: wrap; gap: 10px; margin: 12px 0; color: var(--el-text-color-secondary); font-size: 13px; }
.summary-grid span { padding: 6px 10px; border-radius: 999px; background: var(--el-fill-color-light); }
.log-filter { display: grid; grid-template-columns: repeat(4, minmax(140px, 1fr)); gap: 10px; align-items: center; margin-bottom: 12px; }
.log-filter :deep(.el-date-editor) { grid-column: span 2; width: 100%; }
.el-pagination { margin-top: 14px; justify-content: flex-end; }
@media (max-width: 1080px) { .status-grid { grid-template-columns: 1fr; } .log-filter { grid-template-columns: 1fr; } .log-filter :deep(.el-date-editor) { grid-column: span 1; } .ops-header :deep(.el-card__body), .toolbar-row { align-items: flex-start; flex-direction: column; } }
</style>
