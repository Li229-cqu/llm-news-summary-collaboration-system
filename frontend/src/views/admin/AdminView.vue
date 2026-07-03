<script setup lang="ts">
import { computed, ref } from 'vue'
import { ElMessage } from 'element-plus'
import {
  DataBoard,
  Files,
  Grid,
  Message,
  Monitor,
  Setting,
  TrendCharts,
  User,
  UserFilled,
  Warning,
} from '@element-plus/icons-vue'
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

type AdminSection = 'dashboard' | 'analytics' | 'pending' | 'news' | 'posts' | 'comments' | 'hotTopics' | 'timelines' | 'users' | 'aiConfig' | 'config' | 'ops'

const userStore = useUserStore()

function normalizeAvatarUrl(url?: string | null): string {
  if (!url) return ''
  if (url.startsWith('http')) return url
  const base = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
  return base.replace(/\/+$/, '') + '/' + url.replace(/^\/+/, '')
}

const activeTab = ref<AdminSection>(userStore.isAdmin ? 'analytics' : 'pending')
const pendingCenterKey = ref(0)
const workbenchKey = ref(0)

const sidebarSections = computed(() => {
  const all = [
    { key: 'analytics', label: '数据看板', icon: DataBoard },
    { key: 'dashboard', label: '工作台', icon: Grid },
    { key: 'pending', label: '待审核中心', icon: Warning },
    { key: 'news', label: '新闻管理', icon: Files },
    { key: 'hotTopics', label: '热搜运营', icon: TrendCharts },
    { key: 'posts', label: '社区帖子管理', icon: Message },
    { key: 'comments', label: '评论管理', icon: Files },
    { key: 'timelines', label: 'Timeline 管理', icon: TrendCharts },
    { key: 'users', label: '用户与权限', icon: UserFilled },
    { key: 'aiConfig', label: 'AI 配置与记录', icon: Monitor },
    { key: 'config', label: '系统配置', icon: Setting },
    { key: 'ops', label: '系统运维', icon: DataBoard },
  ] as const

  if (!userStore.isAdmin) {
    return all.filter(item => ['pending', 'news', 'hotTopics', 'posts', 'comments', 'timelines'].includes(item.key))
  }

  return all
})

function loadDashboard() {
  workbenchKey.value += 1
}

async function loadSection(section: AdminSection) {
  const adminOnly: AdminSection[] = ['dashboard', 'analytics', 'users', 'aiConfig', 'config', 'ops']
  if (!userStore.isAdmin && adminOnly.includes(section)) {
    ElMessage.warning('当前账号无权访问该后台模块')
    activeTab.value = 'pending'
    return
  }

  activeTab.value = section
  if (section === 'pending') {
    pendingCenterKey.value += 1
  }
}

async function handleTabChange(tabKey: string) {
  await loadSection(tabKey as AdminSection)
}
</script>

<template>
  <main class="admin-container">
    <template v-if="userStore.isEditorOrAdmin">
      <div class="admin-layout">
        <aside class="admin-sidebar">
          <div class="sidebar-user-card">
            <div class="sidebar-avatar-col">
              <el-avatar :size="72" :src="normalizeAvatarUrl(userStore.userInfo?.avatar)" :icon="User">
                {{ userStore.userInfo?.nickname?.slice(0, 1) || 'A' }}
              </el-avatar>
            </div>
            <div class="sidebar-user-name">{{ userStore.userInfo?.nickname || '管理员' }}</div>
            <div class="sidebar-user-role">
              <el-tag :type="userStore.isAdmin ? 'danger' : 'warning'" effect="dark" round size="small">
                {{ userStore.isAdmin ? '管理员' : '审核 / 编辑' }}
              </el-tag>
            </div>
            <div class="sidebar-nav">
              <el-menu class="admin-menu" :default-active="activeTab" @select="handleTabChange">
                <el-menu-item v-for="item in sidebarSections" :key="item.key" :index="item.key">
                  <component :is="item.icon" :size="18" class="menu-icon" />
                  <span>{{ item.label }}</span>
                </el-menu-item>
              </el-menu>
            </div>
          </div>
        </aside>

        <section class="admin-main">
          <AdminWorkbench v-if="activeTab === 'dashboard'" :key="workbenchKey" @navigate="(tab: string) => loadSection(tab as AdminSection)" />
          <AdminAnalyticsDashboard v-if="activeTab === 'analytics'" @navigate="(tab: string) => loadSection(tab as AdminSection)" />
          <AdminPendingCenter v-if="activeTab === 'pending'" :key="pendingCenterKey" @changed="loadDashboard" />
          <AdminNewsManagement v-if="activeTab === 'news'" @changed="loadDashboard" />
          <AdminPostManagement v-if="activeTab === 'posts'" @changed="loadDashboard" />
          <AdminCommentReview v-if="activeTab === 'comments'" @changed="loadDashboard" />
          <AdminHotTopicManagement v-if="activeTab === 'hotTopics'" @changed="loadDashboard" />
          <AdminTimelineManagement v-if="activeTab === 'timelines'" @changed="loadDashboard" />
          <AdminUserManagement v-if="activeTab === 'users'" @changed="loadDashboard" />
          <AdminAIConfigManagement v-if="activeTab === 'aiConfig'" @changed="loadDashboard" />
          <AdminSystemConfigManagement v-if="activeTab === 'config'" @changed="loadDashboard" />
          <AdminOpsManagement v-if="activeTab === 'ops'" />
        </section>
      </div>
    </template>

    <el-card v-else class="unauthorized-card" shadow="never">
      <el-result icon="warning" title="当前账号无权访问管理后台" sub-title="该页面仅允许审核 / 编辑或管理员访问。" />
    </el-card>
  </main>
</template>

<style scoped>
.admin-container {
  height: calc(100vh - 64px);
  overflow: hidden;
  display: grid;
  grid-template-columns: 280px minmax(0, 1fr);
  background: #fef7f7;
}

.admin-layout {
  display: contents;
}

.admin-sidebar {
  height: 100%;
  overflow-y: auto;
  scrollbar-width: none;
  -ms-overflow-style: none;
  display: flex;
  flex-direction: column;
  padding: 24px 18px;
  background: var(--color-bg-card);
  border-right: 1px solid #f5dfdf;
  gap: 20px;
}

.admin-sidebar::-webkit-scrollbar {
  display: none;
}

.sidebar-user-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 28px 16px 20px;
  background: linear-gradient(180deg, #fef2f2 0%, #f8fafc 50%, #fff 100%);
  border-radius: 18px;
  border: 1px solid #f5dfdf;
  gap: 12px;
}

.sidebar-avatar-col {
  margin-bottom: 4px;
}

.sidebar-user-name {
  font-size: 20px;
  font-weight: 700;
  color: #1f2937;
}

.sidebar-user-role {
  margin-bottom: 8px;
}

.sidebar-nav {
  width: 100%;
}

.admin-menu {
  border-right: 0;
  background: transparent;
}

.admin-menu :deep(.el-menu-item) {
  gap: 10px;
  margin-bottom: 4px;
  border-radius: 10px;
  height: 42px;
  line-height: 42px;
  font-size: 14px;
}

.admin-menu :deep(.el-menu-item .menu-icon),
.admin-menu :deep(.el-menu-item svg),
.admin-menu :deep(.el-menu-item .el-icon) {
  width: 18px !important;
  height: 18px !important;
  flex: 0 0 18px !important;
  font-size: 18px !important;
}

.admin-main {
  height: 100%;
  overflow-y: auto;
  scrollbar-width: none;
  -ms-overflow-style: none;
  padding: 24px 28px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-width: 0;
}

.admin-main::-webkit-scrollbar {
  display: none;
}

.unauthorized-card {
  border-radius: 16px;
}

@media (max-width: 1100px) {
  .admin-container { height: auto; grid-template-columns: 1fr; display: block; }
  .admin-sidebar { height: auto; border-right: none; }
  .admin-main { height: auto; overflow-y: visible; }
}
</style>
