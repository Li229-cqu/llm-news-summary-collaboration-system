<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useRoute, useRouter } from 'vue-router'
import { getNewsCategories, type NewsCategory } from '@/api/news'
import {
  getSubscriptions,
  updateSubscriptions,
  type SubscriptionCategory,
} from '@/api/profile'
import { useUserStore } from '@/stores/user'

interface SidebarCategory {
  id: string
  name: string
  code: string
}

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const categories = ref<SidebarCategory[]>([
  { id: '', name: '推荐', code: 'recommend' },
])
const loadingCategories = ref(false)

const subscriptionVisible = ref(false)
const loadingSubscriptions = ref(false)
const savingSubscriptions = ref(false)
const subscriptionCategories = ref<SubscriptionCategory[]>([])
const selectedSubscriptionIds = ref<number[]>([])

const activeCategory = computed(() => String(route.query.category_id ?? ''))

function normalizeCategory(category: NewsCategory): SidebarCategory {
  if (category.code === 'recommend') {
    return {
      id: '',
      name: category.name || '推荐',
      code: category.code,
    }
  }

  return {
    id: String(category.id),
    name: category.name,
    code: category.code,
  }
}

async function loadCategories() {
  loadingCategories.value = true
  try {
    const data = await getNewsCategories()
    const enabledCategories = data
      .filter((item) => item.status === 1)
      .sort((a, b) => a.sort - b.sort || a.id - b.id)
      .map(normalizeCategory)

    categories.value = enabledCategories.length
      ? enabledCategories
      : [{ id: '', name: '推荐', code: 'recommend' }]
  } catch {
    categories.value = [
      { id: '', name: '推荐', code: 'recommend' },
      { id: '2', name: '时政', code: 'politics' },
      { id: '3', name: '社会', code: 'society' },
      { id: '4', name: '财经', code: 'finance' },
      { id: '5', name: '科技', code: 'technology' },
      { id: '6', name: '体育', code: 'sports' },
      { id: '7', name: '娱乐', code: 'entertainment' },
      { id: '8', name: '国际', code: 'world' },
    ]
  } finally {
    loadingCategories.value = false
  }
}

function selectCategory(categoryId: string) {
  const nextQuery = { ...route.query }

  if (categoryId) {
    nextQuery.category_id = categoryId
  } else {
    delete nextQuery.category_id
  }

  router.push({
    path: '/home',
    query: nextQuery,
  })
}

function ensureLogin() {
  if (userStore.isLoggedIn) {
    return true
  }

  ElMessage.warning('请先登录后再使用订阅管理')
  router.push({
    path: '/login',
    query: { redirect: route.fullPath },
  })
  return false
}

async function openSubscriptionDialog() {
  if (!ensureLogin()) {
    return
  }

  subscriptionVisible.value = true
  loadingSubscriptions.value = true
  try {
    const data = await getSubscriptions()
    subscriptionCategories.value = data.categories
    selectedSubscriptionIds.value = [...data.subscribed_category_ids]
  } catch {
    ElMessage.error('订阅信息加载失败，请稍后重试')
  } finally {
    loadingSubscriptions.value = false
  }
}

async function saveSubscriptions() {
  savingSubscriptions.value = true
  try {
    const data = await updateSubscriptions(selectedSubscriptionIds.value)
    subscriptionCategories.value = data.categories
    selectedSubscriptionIds.value = [...data.subscribed_category_ids]
    ElMessage.success('订阅已更新')
    subscriptionVisible.value = false
  } catch {
    ElMessage.error('订阅更新失败，请稍后重试')
  } finally {
    savingSubscriptions.value = false
  }
}

function goProfile() {
  if (!ensureLogin()) {
    return
  }
  router.push('/profile')
}

onMounted(loadCategories)
</script>

<template>
  <aside class="app-sidebar">
    <div class="app-sidebar__title">新闻分类</div>
    <el-menu
      v-loading="loadingCategories"
      class="app-sidebar__menu"
      :default-active="activeCategory"
      @select="selectCategory"
    >
      <el-menu-item v-for="category in categories" :key="category.code" :index="category.id">
        <span class="app-sidebar__dot" aria-hidden="true"></span>
        <span>{{ category.name }}</span>
      </el-menu-item>
    </el-menu>

    <div class="app-sidebar__quick-links">
      <el-card class="app-sidebar__quick-card" shadow="never" @click="goProfile">
        <span class="app-sidebar__quick-title">生成历史</span>
        <span class="app-sidebar__quick-description">查看个人中心中的 AI 生成记录</span>
      </el-card>
      <el-card class="app-sidebar__quick-card" shadow="never" @click="openSubscriptionDialog">
        <span class="app-sidebar__quick-title">订阅管理</span>
        <span class="app-sidebar__quick-description">管理关注的新闻分类</span>
      </el-card>
    </div>

    <el-dialog v-model="subscriptionVisible" title="订阅管理" width="420px">
      <el-skeleton v-if="loadingSubscriptions" animated :rows="4" />
      <el-empty
        v-else-if="!subscriptionCategories.length"
        description="暂无可订阅分类"
      />
      <el-checkbox-group v-else v-model="selectedSubscriptionIds" class="subscription-list">
        <el-checkbox
          v-for="category in subscriptionCategories"
          :key="category.id"
          :label="category.id"
        >
          {{ category.name }}
        </el-checkbox>
      </el-checkbox-group>

      <template #footer>
        <el-button @click="subscriptionVisible = false">取消</el-button>
        <el-button type="primary" :loading="savingSubscriptions" @click="saveSubscriptions">
          保存
        </el-button>
      </template>
    </el-dialog>
  </aside>
</template>

<style scoped>
.app-sidebar {
  padding: 20px 0;
}

.app-sidebar__title {
  padding: 0 20px 12px;
  color: var(--color-text-secondary);
  font-size: 13px;
}

.app-sidebar__menu {
  min-height: 160px;
  border-right: 0;
}

.app-sidebar__menu :deep(.el-menu-item) {
  gap: 10px;
  height: 44px;
  line-height: 44px;
}

.app-sidebar__menu :deep(.el-menu-item.is-active) {
  color: var(--color-primary);
  background: var(--color-primary-soft);
}

.app-sidebar__dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--color-text-secondary);
}

.app-sidebar__menu :deep(.el-menu-item.is-active) .app-sidebar__dot {
  background: var(--color-primary);
}

.app-sidebar__quick-links {
  display: grid;
  gap: 10px;
  margin-top: 16px;
  padding: 16px;
}

.app-sidebar__quick-card {
  border-color: var(--color-border);
  cursor: pointer;
  transition:
    border-color 0.18s ease,
    box-shadow 0.18s ease,
    transform 0.18s ease;
}

.app-sidebar__quick-card:hover {
  border-color: color-mix(in srgb, var(--color-primary) 35%, var(--color-border));
  box-shadow: 0 8px 18px rgb(15 23 42 / 8%);
  transform: translateY(-1px);
}

.app-sidebar__quick-card :deep(.el-card__body) {
  display: grid;
  gap: 4px;
  padding: 12px;
}

.app-sidebar__quick-title {
  color: var(--color-text-primary);
  font-size: 14px;
  font-weight: 600;
}

.app-sidebar__quick-description {
  color: var(--color-text-secondary);
  font-size: 12px;
  line-height: 1.5;
}

.subscription-list {
  display: grid;
  gap: 10px;
}

.subscription-list :deep(.el-checkbox) {
  height: auto;
}
</style>
