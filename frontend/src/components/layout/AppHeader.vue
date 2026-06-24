<template>
  <header class="app-header">
    <RouterLink class="app-header__brand" to="/home">
      基于大语言模型的智能新闻摘要与协同互动系统
    </RouterLink>

    <el-menu
      class="app-header__menu"
      mode="horizontal"
      router
      :ellipsis="false"
      :default-active="$route.path"
    >
      <el-menu-item index="/home">首页</el-menu-item>
      <el-menu-item index="/ai/title-summary">AI 生成</el-menu-item>
      <el-menu-item index="/community">社区</el-menu-item>
      <el-menu-item index="/profile">个人中心</el-menu-item>
      <el-menu-item v-if="userStore.isEditorOrAdmin" index="/admin">管理后台</el-menu-item>
    </el-menu>

    <div class="app-header__actions">
      <el-input class="app-header__search" placeholder="搜索新闻、话题或关键词" clearable />
      <el-button
        circle
        :aria-label="themeStore.theme === 'light' ? '切换至深色模式' : '切换至浅色模式'"
        @click="themeStore.toggleTheme"
      >
        {{ themeStore.theme === 'light' ? '◐' : '☼' }}
      </el-button>
      <el-dropdown v-if="userStore.isLoggedIn && userStore.userInfo" trigger="click" @command="handleUserCommand">
        <div class="app-header__user-state app-header__user-trigger">
          <el-avatar aria-label="用户头像">
            {{ userStore.userInfo.nickname.slice(0, 1) }}
          </el-avatar>
          <span>{{ userStore.userInfo.nickname }}</span>
          <el-tag size="small" effect="plain">{{ getRoleLabel(userStore.role) }}</el-tag>
        </div>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="profile">个人中心</el-dropdown-item>
            <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>

      <RouterLink v-else class="app-header__user-state app-header__login-link" to="/login">
        <el-avatar aria-label="用户头像占位">U</el-avatar>
        <span>未登录</span>
      </RouterLink>
    </div>
  </header>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { logoutApi } from '@/api/auth'
import { useThemeStore } from '@/stores/theme'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const themeStore = useThemeStore()
const userStore = useUserStore()

function getRoleLabel(role: string) {
  const roleLabels: Record<string, string> = {
    user: '普通用户',
    editor: '审核/编辑',
    admin: '管理员',
  }

  return roleLabels[role] ?? role
}

async function handleUserCommand(command: string) {
  if (command === 'profile') {
    await router.push('/profile')
    return
  }

  if (command === 'logout') {
    try {
      await logoutApi()
    } catch {
      // Mock 退出登录失败时仍清理本地状态，避免保留失效登录态。
    } finally {
      userStore.clearUser()
      ElMessage.success('已退出登录')
      await router.push('/home')
    }
  }
}
</script>

<style scoped>
.app-header {
  display: flex;
  align-items: center;
  width: 100%;
  min-width: 0;
  height: var(--header-height);
  flex: 0 0 var(--header-height);
  gap: 24px;
  padding: 0 24px;
  background: var(--color-bg-card);
  border-bottom: 1px solid var(--color-border);
}

.app-header__brand {
  flex: 0 1 360px;
  min-width: 0;
  overflow: hidden;
  color: var(--color-text-primary);
  font-size: 17px;
  font-weight: 600;
  text-decoration: none;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.app-header__menu {
  --el-menu-active-color: var(--color-primary);
  --el-menu-hover-bg-color: var(--color-primary-soft);
  flex: 0 1 auto;
  min-width: 0;
  height: var(--header-height);
  border-bottom: 0;
}

.app-header__actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
  min-width: 0;
  margin-left: auto;
}

.app-header__search {
  width: 220px;
}

.app-header__user-state {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--color-text-secondary);
  font-size: 14px;
  white-space: nowrap;
}

.app-header__user-trigger {
  cursor: pointer;
  outline: none;
}

.app-header__login-link {
  text-decoration: none;
}

@media (max-width: 1100px) {
  .app-header {
    gap: 12px;
    padding: 0 16px;
  }

  .app-header__brand {
    flex-basis: 240px;
  }

  .app-header__search {
    width: 160px;
  }

  .app-header__user-state span {
    display: none;
  }
}

@media (max-width: 840px) {
  .app-header__search {
    display: none;
  }

  .app-header__brand {
    flex-basis: 180px;
    font-size: 15px;
  }

  .app-header__menu :deep(.el-menu-item) {
    padding: 0 10px;
  }
}
</style>
