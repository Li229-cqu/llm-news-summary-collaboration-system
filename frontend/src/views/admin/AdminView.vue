<script setup lang="ts">import { ref, onMounted } from 'vue';
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
} from '@element-plus/icons-vue';
import {
 type AdminDashboard,
 type UserItem,
 getDashboard,
 getPendingPosts,
 getUsers,
 getSystemConfig,
} from '@/api/admin';
import { useUserStore } from '@/stores/user';
const userStore = useUserStore();
const activeTab = ref('dashboard');
const dashboard = ref<AdminDashboard | null>(null);
const pendingPosts = ref<any[]>([]);
const users = ref<UserItem[]>([]);
const systemConfig = ref<Record<string, unknown> | null>(null);
const loading = ref(false);
const tabs = [
 { key: 'dashboard', label: '概览', icon: Grid },
 { key: 'pending', label: '待审核', icon: Warning },
 { key: 'users', label: '用户管理', icon: UserFilled },
 { key: 'config', label: '系统配置', icon: Setting },
];
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
];
const editorFeatures = [
 { title: '内容审核', description: '审核待发布的新闻内容', icon: Warning },
 { title: '评论筛选', description: '管理和处理用户评论', icon: Message },
 { title: '社区帖子管理', description: '审核和管理社区帖子', icon: TrendCharts },
 { title: '热搜话题维护', description: '管理热门话题和搜索词', icon: PieChart },
];
const adminFeatures = [
 { title: '账号管理', description: '管理平台用户账号', icon: User },
 { title: '角色权限管理', description: '配置用户角色和权限', icon: Key },
 { title: '内容总管理', description: '全站内容统一管理', icon: DataBoard },
 { title: 'AI 模型配置', description: '配置 AI 服务参数', icon: Setting },
 { title: '提示词模板', description: '管理 AI 提示词模板', icon: Files },
 { title: '系统日志', description: '查看系统运行日志', icon: PieChart },
 { title: '数据备份与恢复', description: '数据维护和备份', icon: Refresh },
];
async function loadDashboard() {
 loading.value = true;
 try {
 dashboard.value = await getDashboard();
 updateStats();
 }
 finally {
 loading.value = false;
 }
}
function updateStats() {
 if (dashboard.value) {
 statsCards[0].value = dashboard.value.user_count;
 statsCards[1].value = dashboard.value.news_count;
 statsCards[2].value = dashboard.value.post_count;
 statsCards[3].value = dashboard.value.pending_count;
 }
}
async function loadPendingPosts() {
 loading.value = true;
 try {
 const result = await getPendingPosts(1, 20);
 pendingPosts.value = result.list;
 }
 finally {
 loading.value = false;
 }
}
async function loadUsers() {
 loading.value = true;
 try {
 const result = await getUsers(1, 20);
 users.value = result.list;
 }
 finally {
 loading.value = false;
 }
}
async function loadSystemConfig() {
 loading.value = true;
 try {
 systemConfig.value = await getSystemConfig();
 }
 finally {
 loading.value = false;
 }
}
function handleTabChange(key: string) {
 activeTab.value = key;
 switch (key) {
 case 'dashboard':
 loadDashboard();
 break;
 case 'pending':
 loadPendingPosts();
 break;
 case 'users':
 loadUsers();
 break;
 case 'config':
 loadSystemConfig();
 break;
 }
}
function getRoleLabel(role: string) {
 const roleMap: Record<string, string> = {
 user: '普通用户',
 editor: '审核编辑',
 admin: '管理员',
 };
 return roleMap[role] || role;
}
function getRoleType(role: string) {
 const typeMap: Record<string, string> = {
 user: 'info',
 editor: 'warning',
 admin: 'danger',
 };
 return typeMap[role] || 'info';
}
onMounted(() => {
 loadDashboard();
});
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
            :disabled="tab.key === 'users' && !userStore.isAdmin"
          >
            <template #label>
              <component :is="tab.icon" :size="18" class="tab-icon" />
              <span>{{ tab.label }}</span>
            </template>

            <div v-if="loading" class="loading-container">
              <el-spinner />
            </div>

            <template v-else-if="activeTab === 'dashboard'">
              <div class="dashboard-content">
                <section class="feature-section">
                  <h2>快速入口</h2>
                  <div class="feature-grid">
                    <el-card
                      v-for="feature in editorFeatures"
                      :key="feature.title"
                      class="feature-card"
                      shadow="hover"
                      @click="feature.title === '社区帖子管理' && handleTabChange('pending')"
                    >
                      <component :is="feature.icon" :size="28" class="feature-icon" />
                      <div class="feature-info">
                        <h3>{{ feature.title }}</h3>
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
                      :key="feature.title"
                      class="feature-card"
                      shadow="hover"
                      @click="feature.title === '账号管理' && handleTabChange('users')"
                    >
                      <component :is="feature.icon" :size="28" class="feature-icon admin-icon" />
                      <div class="feature-info">
                        <h3>{{ feature.title }}</h3>
                        <p>{{ feature.description }}</p>
                      </div>
                    </el-card>
                  </div>
                </section>
              </div>
            </template>

            <template v-else-if="activeTab === 'pending'">
              <div v-if="pendingPosts.length === 0" class="empty-state">
                <CheckCircle :size="48" class="empty-icon success" />
                <p>暂无待审核内容</p>
              </div>
              <div v-else class="pending-list">
                <el-table :data="pendingPosts" border>
                  <el-table-column prop="id" label="ID" width="80" />
                  <el-table-column prop="title" label="标题" min-width="200" />
                  <el-table-column prop="username" label="作者" width="120" />
                  <el-table-column
                    prop="create_time"
                    label="提交时间"
                    width="180"
                  />
                  <el-table-column label="操作" width="180">
                    <template #default>
                      <el-button size="small" type="success">通过</el-button>
                      <el-button size="small" type="danger">拒绝</el-button>
                    </template>
                  </el-table-column>
                </el-table>
              </div>
            </template>

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

            <template v-else-if="activeTab === 'config'">
              <div v-if="!userStore.isAdmin" class="unauthorized-section">
                <Lock :size="48" class="empty-icon" />
                <p>该功能仅管理员可访问</p>
              </div>
              <div v-else-if="!systemConfig" class="loading-container">
                <el-spinner />
              </div>
              <div v-else class="config-form">
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
}

.feature-icon {
  color: #409eff;
}

.feature-icon.admin-icon {
  color: #f56c6c;
}

.feature-info h3 {
  margin: 0 0 4px;
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
.users-list {
  padding: 16px;
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
