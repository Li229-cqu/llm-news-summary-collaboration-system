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

const subscriptionExpanded = ref(false)
const loadingSubscriptions = ref(false)
const savingSubscriptions = ref(false)
const subscriptionCategories = ref<SubscriptionCategory[]>([])
const selectedSubscriptionIds = ref<number[]>([])

const activeCategory = computed(() => String(route.query.category_id ?? ''))
const isSubscriptionActive = computed(() => route.query.tab === 'subscription')

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
  delete nextQuery.keyword
  delete nextQuery.tab
  delete nextQuery.subscription_updated

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

function selectSubscriptionTab() {
  const nextQuery = { ...route.query }
  delete nextQuery.keyword
  delete nextQuery.category_id
  delete nextQuery.subscription_updated
  nextQuery.tab = 'subscription'

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

async function loadSubscriptionOptions() {
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

async function handleSubscriptionClick() {
  selectSubscriptionTab()

  if (!ensureLogin()) {
    subscriptionExpanded.value = false
    return
  }

  subscriptionExpanded.value = !subscriptionExpanded.value
  if (subscriptionExpanded.value && !subscriptionCategories.value.length) {
    await loadSubscriptionOptions()
  }
}

async function saveSubscriptions() {
  savingSubscriptions.value = true
  try {
    const data = await updateSubscriptions(selectedSubscriptionIds.value)
    subscriptionCategories.value = data.categories
    selectedSubscriptionIds.value = [...data.subscribed_category_ids]
    ElMessage.success('订阅已更新')
    if (isSubscriptionActive.value) {
      router.replace({
        path: '/home',
        query: {
          ...route.query,
          tab: 'subscription',
          subscription_updated: String(Date.now()),
        },
      })
    }
  } catch {
    ElMessage.error('订阅更新失败，请稍后重试')
  } finally {
    savingSubscriptions.value = false
  }
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

    <div class="app-sidebar__subscription">
      <button
        class="app-sidebar__subscription-trigger"
        :class="{ 'is-active': isSubscriptionActive }"
        type="button"
        @click="handleSubscriptionClick"
      >
        <span class="app-sidebar__dot" aria-hidden="true"></span>
        <span>订阅</span>
        <span class="app-sidebar__subscription-action">{{ subscriptionExpanded ? '收起' : '展开' }}</span>
      </button>

      <el-collapse-transition>
        <div v-show="subscriptionExpanded" class="app-sidebar__subscription-panel">
          <el-skeleton v-if="loadingSubscriptions" animated :rows="3" />
          <el-empty
            v-else-if="!subscriptionCategories.length"
            description="暂无可订阅分类"
          />
          <template v-else>
            <el-checkbox-group v-model="selectedSubscriptionIds" class="subscription-list">
              <el-checkbox
                v-for="category in subscriptionCategories"
                :key="category.id"
                :label="category.id"
              >
                {{ category.name }}
              </el-checkbox>
            </el-checkbox-group>
            <div class="app-sidebar__subscription-footer">
              <el-button size="small" plain @click.stop="loadSubscriptionOptions">重置</el-button>
              <el-button size="small" type="primary" :loading="savingSubscriptions" @click.stop="saveSubscriptions">
                保存订阅
              </el-button>
            </div>
          </template>
        </div>
      </el-collapse-transition>
    </div>
  </aside>
</template>

<style scoped>
.app-sidebar {
  width: 100%;
  padding: 20px 0;
}

.app-sidebar__title {
  padding: 0 20px 12px;
  color: var(--color-text-secondary);
  font-size: 13px;
}

.app-sidebar__menu {
  width: 100%;
  min-height: 160px;
  border-right: 0;
}

.app-sidebar__menu :deep(.el-menu-item) {
  gap: 10px;
  height: 44px;
  padding: 0 20px !important;
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

.app-sidebar__subscription {
  padding: 0 12px;
}

.app-sidebar__subscription-trigger {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  height: 44px;
  padding: 0 8px;
  border: 0;
  border-radius: 8px;
  background: transparent;
  color: var(--color-text-primary);
  font-size: 14px;
  text-align: left;
  cursor: pointer;
}

.app-sidebar__subscription-trigger:hover,
.app-sidebar__subscription-trigger.is-active {
  color: var(--color-primary);
  background: var(--color-primary-soft);
}

.app-sidebar__subscription-trigger.is-active .app-sidebar__dot {
  background: var(--color-primary);
}

.app-sidebar__subscription-action {
  margin-left: auto;
  color: var(--color-text-secondary);
  font-size: 12px;
}

.app-sidebar__subscription-panel {
  margin: 8px 0 0;
  padding: 12px;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  background: var(--color-bg-card);
}

.app-sidebar__subscription-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 12px;
}

.subscription-list {
  display: grid;
  gap: 10px;
}

.subscription-list :deep(.el-checkbox) {
  height: auto;
  margin-right: 0;
  white-space: normal;
}
</style>
