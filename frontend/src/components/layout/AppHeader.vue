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

    <form v-if="isHomePage" class="app-header__search" @submit.prevent="handleSearch">
      <el-input
        v-model="searchKeyword"
        class="app-header__search-input"
        clearable
        placeholder="搜索新闻、标题、摘要、来源、标签"
        @keyup.enter="handleSearch"
      />
      <el-button type="primary" :icon="Search" @click="handleSearch">搜索</el-button>
      <el-button plain @click="handleReset">重置</el-button>
    </form>

    <div class="app-header__actions">
      <el-button
        circle
        :aria-label="themeStore.theme === 'light' ? '切换至深色模式' : '切换至浅色模式'"
        @click="themeStore.toggleTheme"
      >
        {{ themeStore.theme === 'light' ? '☀' : '☾' }}
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
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Search } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { logoutApi } from '@/api/auth'
import { useThemeStore } from '@/stores/theme'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const route = useRoute()
const themeStore = useThemeStore()
const userStore = useUserStore()
const searchStorageKey = 'home_global_search_keyword'
const searchKeyword = ref('')
const isHomePage = computed(() => route.name === 'home')

onMounted(() => {
  const routeKeyword = typeof route.query.keyword === 'string' ? route.query.keyword.trim() : ''
  const storedKeyword = sessionStorage.getItem(searchStorageKey)?.trim() || ''

  if (route.path === '/home' && !routeKeyword) {
    searchKeyword.value = ''
    sessionStorage.removeItem(searchStorageKey)
    return
  }

  searchKeyword.value = routeKeyword || storedKeyword
})

watch(
  () => [route.path, route.query.keyword],
  ([path, keyword]) => {
    const normalizedKeyword = typeof keyword === 'string' ? keyword.trim() : ''

    if (normalizedKeyword) {
      searchKeyword.value = normalizedKeyword
      sessionStorage.setItem(searchStorageKey, normalizedKeyword)
      return
    }

    if (path === '/home') {
      searchKeyword.value = ''
      sessionStorage.removeItem(searchStorageKey)
    }
  },
)

function getRoleLabel(role: string) {
  const roleLabels: Record<string, string> = {
    user: '普通用户',
    editor: '审核/编辑',
    admin: '管理员',
  }

  return roleLabels[role] ?? role
}

async function handleSearch() {
  const keyword = searchKeyword.value.trim()

  if (!keyword) {
    await handleReset()
    return
  }

  sessionStorage.setItem(searchStorageKey, keyword)
  await router.push({
    path: '/home',
    query: { keyword },
  })
}

async function handleReset() {
  searchKeyword.value = ''
  sessionStorage.removeItem(searchStorageKey)
  await router.push({ path: '/home', query: {} })
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
  gap: 16px;
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

.app-header__search {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 320px;
  max-width: 520px;
  flex: 1 1 420px;
}

.app-header__search-input {
  flex: 1 1 auto;
  min-width: 0;
}

.app-header__actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
  min-width: 0;
  margin-left: auto;
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

  .app-header__user-state span {
    display: none;
  }

  .app-header__search {
    min-width: 220px;
  }
}

@media (max-width: 840px) {
  .app-header__brand {
    flex-basis: 180px;
    font-size: 15px;
  }

  .app-header__menu :deep(.el-menu-item) {
    padding: 0 10px;
  }

  .app-header__search {
    display: none;
  }
}
</style>
