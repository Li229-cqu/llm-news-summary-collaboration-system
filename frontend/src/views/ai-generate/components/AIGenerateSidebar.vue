<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

const navItems = [
  {
    label: '开始生成',
    icon: '✏️',
    path: '/ai-generate',
    matchPaths: ['/ai-generate'],
  },
  {
    label: '生成历史',
    icon: '📋',
    path: '/ai-generate/history',
    matchPaths: ['/ai-generate/history', '/ai-generate/history/'],
  },
]

const activePath = computed(() => {
  const current = route.path
  // 精确匹配 /ai-generate（不含子路由）
  if (current === '/ai-generate') return '/ai-generate'
  // 子路由匹配到 history
  if (current.startsWith('/ai-generate/history')) return '/ai-generate/history'
  return '/ai-generate'
})

function navigate(path: string) {
  router.push(path)
}
</script>

<template>
  <nav class="sidebar-nav">
    <div class="sidebar-header">
      <span class="sidebar-label">AI 工作台</span>
    </div>

    <ul class="nav-list">
      <li
        v-for="item in navItems"
        :key="item.path"
        class="nav-item"
        :class="{ active: activePath === item.path }"
        @click="navigate(item.path)"
      >
        <span class="nav-icon">{{ item.icon }}</span>
        <span class="nav-label">{{ item.label }}</span>
      </li>
    </ul>
  </nav>
</template>

<style scoped>
.sidebar-nav {
  display: flex;
  flex-direction: column;
  background-color: #ffffff;
  border-radius: 12px;
  border: 1px solid #f1d4d4;
  box-shadow: 0 2px 12px rgba(217, 45, 32, 0.05);
  overflow: hidden;
}

.sidebar-header {
  padding: 18px 20px 14px;
  border-bottom: 2px solid #d92d20;
}

.sidebar-label {
  font-size: 16px;
  font-weight: 700;
  color: #1e293b;
}

.nav-list {
  list-style: none;
  margin: 0;
  padding: 8px 0;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 20px;
  margin: 2px 8px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  color: #4b5563;
  transition: all 0.2s ease;
  user-select: none;
}

.nav-item:hover {
  background-color: #fff5f5;
  color: #d92d20;
}

.nav-item.active {
  background-color: #fff1f0;
  color: #d92d20;
  font-weight: 600;
}

.nav-item.active::before {
  content: '';
  position: absolute;
  left: 8px;
  width: 3px;
  height: 20px;
  background-color: #d92d20;
  border-radius: 2px;
}

.nav-icon {
  font-size: 16px;
  width: 20px;
  text-align: center;
  flex-shrink: 0;
}

.nav-label {
  white-space: nowrap;
}
</style>
