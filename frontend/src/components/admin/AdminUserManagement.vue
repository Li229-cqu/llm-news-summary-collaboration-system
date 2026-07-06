<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import PaginationBar from '@/components/common/PaginationBar.vue'
import {
  type AdminUserDetail,
  type AdminUserListResponse,
  type AdminUserOptions,
  type AdminUserActionResult,
  type AdminUserRoleRequest,
  type AdminUserStatusRequest,
  type UserItem,
  changeUserRole,
  changeUserStatus,
  getAdminUserOptions,
  getUserDetail,
  getUsers,
} from '@/api/admin'
import { useUserStore } from '@/stores/user'

const emit = defineEmits<{ (e: 'changed'): void }>()
const userStore = useUserStore()

// ── state ──────────────────────────────────────────────────────
const userOptions = ref<AdminUserOptions | null>(null)
const userData = ref<AdminUserListResponse | null>(null)
const loading = ref(false)

const query = reactive({
  keyword: '',
  role: '' as string,
  status: null as number | null,
  start_time: '' as string,
  end_time: '' as string,
  page: 1,
  page_size: 10,
})

// detail drawer
const detailVisible = ref(false)
const detailData = ref<AdminUserDetail | null>(null)
const loadingDetail = ref(false)

// role dialog
const roleDialogVisible = ref(false)
const roleTarget = ref<UserItem | null>(null)
const selectedRole = ref('')
const changingRole = ref(false)

// ── computed ────────────────────────────────────────────────────
const summaryCards = computed(() => {
  const s = userData.value?.summary
  return [
    { key: 'total', label: '用户总数', value: s?.total_count ?? '--' },
    { key: 'admin', label: '管理员', value: s?.admin_count ?? '--' },
    { key: 'editor', label: '审核/编辑', value: s?.editor_count ?? '--' },
    { key: 'user', label: '普通用户', value: s?.user_count ?? '--' },
    { key: 'active', label: '正常账号', value: s?.active_count ?? '--' },
    { key: 'disabled', label: '已禁用', value: s?.disabled_count ?? '--' },
  ]
})

function roleTagType(role: string) {
  const map: Record<string, string> = { user: 'info', editor: 'warning', admin: 'danger' }
  return map[role] || 'info'
}

function roleLabel(role: string) {
  const map: Record<string, string> = {
    user: '普通用户',
    editor: '审核/编辑',
    admin: '管理员',
  }
  return map[role] || role
}

function isOwnRow(row: UserItem) {
  return userStore.userInfo?.id === row.id
}

// ── load ────────────────────────────────────────────────────────
async function loadOptions() {
  try {
    userOptions.value = await getAdminUserOptions()
  } catch (error) {
    userOptions.value = null
    ElMessage.error(error instanceof Error ? error.message : '用户选项加载失败')
  }
}

async function loadList() {
  loading.value = true
  try {
    userData.value = await getUsers({
      keyword: query.keyword || undefined,
      role: query.role || undefined,
      status: query.status ?? undefined,
      start_time: query.start_time || undefined,
      end_time: query.end_time || undefined,
      page: query.page,
      page_size: query.page_size,
    })
  } catch (e) {
    ElMessage.error(e instanceof Error ? e.message : '加载失败')
  } finally {
    loading.value = false
  }
}

function resetQuery() {
  query.keyword = ''
  query.role = ''
  query.status = null
  query.start_time = ''
  query.end_time = ''
  query.page = 1
  void loadList()
}

// ── detail ─────────────────────────────────────────────────────
async function openDetail(row: UserItem) {
  detailVisible.value = true
  loadingDetail.value = true
  try {
    detailData.value = await getUserDetail(row.id)
  } catch (e) {
    ElMessage.error(e instanceof Error ? e.message : '加载详情失败')
  } finally {
    loadingDetail.value = false
  }
}

// ── role ───────────────────────────────────────────────────────
function openRoleDialog(row: UserItem) {
  roleTarget.value = row
  selectedRole.value = row.role
  roleDialogVisible.value = true
}

async function confirmChangeRole() {
  if (!roleTarget.value) return
  try {
    await ElMessageBox.confirm(
      `确认将用户“${roleTarget.value.username}”的角色修改为“${roleLabel(selectedRole.value)}”？`,
      '确认修改角色',
      { type: 'warning', confirmButtonText: '确认修改', cancelButtonText: '取消' },
    )
  } catch {
    return
  }
  changingRole.value = true
  try {
    const payload: AdminUserRoleRequest = { role: selectedRole.value as AdminUserRoleRequest['role'] }
    const r = await changeUserRole(roleTarget.value.id, payload)
    ElMessage.success(r.message || '角色修改成功')
    roleDialogVisible.value = false
    await loadList()
    emit('changed')
  } catch (e) {
    ElMessage.error(e instanceof Error ? e.message : '修改角色失败')
  } finally {
    changingRole.value = false
  }
}

// ── status ─────────────────────────────────────────────────────
async function confirmToggleStatus(row: UserItem) {
  const isEnable = row.status !== 1
  const actionLabel = isEnable ? '启用' : '禁用'
  await ElMessageBox.confirm(
    `确认${actionLabel}用户「${row.username}」？`,
    `确认${actionLabel}`,
    { type: 'warning' },
  )
  try {
    const payload: AdminUserStatusRequest = { status: isEnable ? 1 : 0 }
    const r = await changeUserStatus(row.id, payload)
    ElMessage.success(r.message || `${actionLabel}成功`)
    await loadList()
    emit('changed')
  } catch (e) {
    ElMessage.error(e instanceof Error ? e.message : `${actionLabel}失败`)
  }
}

// ── mount ───────────────────────────────────────────────────────
onMounted(async () => {
  await Promise.allSettled([loadOptions(), loadList()])
})
</script>

<template>
  <div class="admin-user-mgmt">
    <!-- header -->
    <div class="panel-header">
      <div>
        <h3>用户与权限</h3>
        <p>管理系统用户账号、角色权限、账号状态与用户行为数据。</p>
      </div>
      <el-button type="primary" @click="loadList">刷新</el-button>
    </div>

    <!-- summary cards -->
    <div class="summary-grid">
      <article v-for="card in summaryCards" :key="card.key" class="summary-card">
        <span>{{ card.label }}</span>
        <strong>{{ card.value }}</strong>
      </article>
    </div>

    <!-- filters -->
    <div class="filter-row">
      <el-input v-model="query.keyword" placeholder="用户名 / 昵称" clearable style="width:200px" />
      <el-select v-model="query.role" placeholder="角色" clearable style="width:140px">
        <el-option v-for="o in userOptions?.roles || []" :key="o.value" :label="o.label" :value="o.value" />
      </el-select>
      <el-select v-model="query.status" placeholder="状态" clearable style="width:120px">
        <el-option v-for="o in userOptions?.statuses || []" :key="o.value" :label="o.label" :value="o.value" />
      </el-select>
      <el-date-picker
        v-model="query.start_time"
        type="date"
        placeholder="注册开始"
        value-format="YYYY-MM-DD"
        style="width:150px"
      />
      <el-date-picker
        v-model="query.end_time"
        type="date"
        placeholder="注册截止"
        value-format="YYYY-MM-DD"
        style="width:150px"
      />
      <el-button type="primary" @click="query.page = 1; loadList()">查询</el-button>
      <el-button @click="resetQuery">重置</el-button>
    </div>

    <!-- table -->
    <el-table v-loading="loading" :data="userData?.items || []" border>
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="username" label="用户名" min-width="140" show-overflow-tooltip />
      <el-table-column prop="nickname" label="昵称" min-width="140" show-overflow-tooltip />
      <el-table-column label="角色" width="110">
        <template #default="scope">
          <el-tag :type="roleTagType(scope.row.role)" size="small">{{ roleLabel(scope.row.role) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="90">
        <template #default="scope">
          <el-tag size="small" :type="scope.row.status === 1 ? 'success' : 'danger'">
            {{ scope.row.status === 1 ? '正常' : '已禁用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="create_time" label="注册时间" width="170" />
      <el-table-column label="操作" width="280" fixed="right">
        <template #default="scope">
          <el-button size="small" text type="primary" @click="openDetail(scope.row)">详情</el-button>
          <el-tooltip
            v-if="isOwnRow(scope.row)"
            content="不能修改自己的角色"
            placement="top"
          >
            <span>
              <el-button size="small" text type="warning" disabled>角色</el-button>
            </span>
          </el-tooltip>
          <el-button v-else size="small" text type="warning" @click="openRoleDialog(scope.row)">角色</el-button>
          <el-tooltip
            v-if="isOwnRow(scope.row)"
            content="不能禁用自己的账号"
            placement="top"
          >
            <span>
              <el-button size="small" text :type="scope.row.status === 1 ? 'danger' : 'success'" disabled>
                {{ scope.row.status === 1 ? '禁用' : '启用' }}
              </el-button>
            </span>
          </el-tooltip>
          <el-button
            v-else
            size="small"
            text
            :type="scope.row.status === 1 ? 'danger' : 'success'"
            @click="confirmToggleStatus(scope.row)"
          >
            {{ scope.row.status === 1 ? '禁用' : '启用' }}
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <PaginationBar :current-page="query.page" :total-pages="Math.ceil((userData?.total || 0) / query.page_size)" @change="(p: number) => { query.page = p; loadList(); }" />

    <!-- detail drawer -->
    <el-drawer v-model="detailVisible" title="用户详情" size="600px">
      <div v-if="loadingDetail" v-loading="loadingDetail" style="min-height:200px" />
      <template v-else-if="detailData">
        <h4 style="margin:0 0 12px">基础信息</h4>
        <el-descriptions :column="2" border size="small">
          <el-descriptions-item label="用户ID">{{ detailData.id }}</el-descriptions-item>
          <el-descriptions-item label="用户名">{{ detailData.username }}</el-descriptions-item>
          <el-descriptions-item label="昵称">{{ detailData.nickname }}</el-descriptions-item>
          <el-descriptions-item label="角色">
            <el-tag :type="roleTagType(detailData.role)" size="small">{{ roleLabel(detailData.role) }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag size="small" :type="detailData.status === 1 ? 'success' : 'danger'">
              {{ detailData.status === 1 ? '正常' : '已禁用' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="邮箱">{{ detailData.email || '--' }}</el-descriptions-item>
          <el-descriptions-item label="手机号">{{ detailData.phone || '--' }}</el-descriptions-item>
          <el-descriptions-item label="注册时间">{{ detailData.create_time || '--' }}</el-descriptions-item>
          <el-descriptions-item label="最近更新">{{ detailData.updated_at || '--' }}</el-descriptions-item>
        </el-descriptions>

        <h4 style="margin:16px 0 8px">行为统计</h4>
        <div class="behavior-grid">
          <div class="behavior-item">
            <span class="behavior-num">{{ detailData.behavior.post_count }}</span>
            <span class="behavior-label">社区帖子</span>
          </div>
          <div class="behavior-item">
            <span class="behavior-num">{{ detailData.behavior.comment_count }}</span>
            <span class="behavior-label">评论数</span>
          </div>
          <div class="behavior-item">
            <span class="behavior-num">{{ detailData.behavior.ai_generation_count }}</span>
            <span class="behavior-label">AI 生成</span>
          </div>
          <div class="behavior-item">
            <span class="behavior-num">{{ detailData.behavior.browse_count }}</span>
            <span class="behavior-label">浏览记录</span>
          </div>
          <div class="behavior-item">
            <span class="behavior-num">{{ detailData.behavior.favorite_count }}</span>
            <span class="behavior-label">收藏数</span>
          </div>
        </div>

      </template>
    </el-drawer>

    <!-- role change dialog -->
    <el-dialog
      v-model="roleDialogVisible"
      title="修改角色"
      width="420px"
      :close-on-click-modal="false"
    >
      <div v-if="roleTarget" style="margin-bottom:12px;color:#606266">
        用户：<strong>{{ roleTarget.username }}</strong>（{{ roleTarget.nickname }}）<br />
        当前角色：<el-tag :type="roleTagType(roleTarget.role)" size="small">{{ roleLabel(roleTarget.role) }}</el-tag>
      </div>
      <el-form label-width="80px">
        <el-form-item label="新角色">
          <el-select v-model="selectedRole" style="width:100%">
            <el-option
              v-for="o in userOptions?.roles || []"
              :key="o.value"
              :label="o.label"
              :value="o.value"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="roleDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="changingRole" @click="confirmChangeRole">确认修改</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.admin-user-mgmt { padding: 0; }
.panel-header { display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:16px }
.panel-header h3 { margin:0; font-size:18px }
.panel-header p { margin:4px 0 0; color:var(--color-text-muted); font-size:13px }

.summary-grid { display:grid; grid-template-columns:repeat(6,1fr); gap:12px; margin-bottom:16px }
.summary-card { background: var(--color-bg); border-radius:8px; padding:14px 12px; display:flex; flex-direction:column; gap:4px }
.summary-card span { font-size:12px; color:var(--color-text-muted) }
.summary-card strong { font-size:20px }

.filter-row { display:flex; gap:10px; flex-wrap:wrap; margin-bottom:16px; align-items:center }
.pager { margin-top:16px; justify-content:flex-end }

.behavior-grid { display:grid; grid-template-columns:repeat(5,1fr); gap:10px }
.behavior-item { background: var(--color-bg); border-radius:8px; padding:16px 12px; text-align:center; display:flex; flex-direction:column; gap:4px }
.behavior-num { font-size:22px; font-weight:600; color:var(--color-text-primary) }
.behavior-label { font-size:12px; color:var(--color-text-muted) }
</style>
