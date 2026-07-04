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
const isTimelineActive = computed(() => route.path.startsWith('/timeline'))
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

function goToTimeline() {
  router.push('/timeline')
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
            <div class="subscription-panel__header">
              <p class="subscription-panel__title">选择订阅</p>
              <p class="subscription-panel__desc">勾选你关注的新闻频道，我们将优先为你推荐</p>
            </div>
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
              <button class="sub-btn sub-btn--cancel" type="button" @click.stop="loadSubscriptionOptions">
                重置
              </button>
              <button
                class="sub-btn sub-btn--save"
                type="button"
                :disabled="savingSubscriptions"
                @click.stop="saveSubscriptions"
              >
                <span v-if="savingSubscriptions" class="sub-btn__spinner"></span>
                {{ savingSubscriptions ? '保存中...' : '保存订阅' }}
              </button>
            </div>
          </template>
        </div>
      </el-collapse-transition>
    </div>

    <!-- 事件脉络入口 -->
    <div class="app-sidebar__timeline">
      <button
        class="app-sidebar__timeline-trigger"
        :class="{ 'is-active': isTimelineActive }"
        type="button"
        @click="goToTimeline"
      >
        <span class="app-sidebar__dot" aria-hidden="true"></span>
        <div class="app-sidebar__timeline-text">
          <span class="app-sidebar__timeline-name">事件脉络</span>
          <span class="app-sidebar__timeline-desc">AI 聚合热点事件发展线</span>
        </div>
        <span class="app-sidebar__timeline-arrow">→</span>
      </button>
    </div>

  </aside>
</template>

<style scoped>
/* ========================================
   侧边栏容器
   ======================================== */
.app-sidebar {
  width: 100%;
  height: 100%;
  max-height: 100%;
  overflow-y: auto;
  padding: 16px 10px;
  background: var(--color-bg-card);
  border-radius: 16px;
  border: 1px solid var(--color-border);
}

/* ========================================
   标题区：新闻频道
   ======================================== */
.app-sidebar__title {
  padding: 0 12px 6px;
  margin: 0;
  color: var(--color-text-primary);
  font-size: 16px;
  font-weight: 700;
  letter-spacing: .02em;
}

.app-sidebar__title::before {
  content: '';
  display: inline-block;
  width: 3px;
  height: 15px;
  margin-right: 8px;
  border-radius: 2px;
  background: var(--color-primary);
  vertical-align: text-bottom;
}

/* title 下方副说明 */
.app-sidebar__title::after {
  content: '按频道快速浏览';
  display: block;
  margin-top: 4px;
  padding-left: 11px;
  color: var(--color-text-secondary);
  font-size: 12px;
  font-weight: 400;
  letter-spacing: 0;
}

/* ========================================
   el-menu 重置
   ======================================== */
.app-sidebar__menu {
  width: 100%;
  min-height: 0;
  border-right: 0;
  background: transparent;
  margin-top: 10px;
}

/* 分类菜单项 —— 卡片式频道按钮 */
.app-sidebar__menu :deep(.el-menu-item) {
  display: flex;
  align-items: center;
  gap: 10px;
  height: 40px;
  margin: 1px 0;
  padding: 0 12px !important;
  line-height: 40px;
  border-radius: 12px;
  color: var(--color-text-primary);
  font-size: 14px;
  transition:
    background .2s ease,
    color .2s ease,
    padding-left .2s ease;
}

/* hover：浅红底 + 轻微右移 */
.app-sidebar__menu :deep(.el-menu-item:hover) {
  color: var(--color-primary);
  background: color-mix(in srgb, var(--color-primary) 5%, var(--color-bg-card));
  padding-left: 16px !important;
}

/* active：红色强调背景 + 左侧红线 */
.app-sidebar__menu :deep(.el-menu-item.is-active) {
  color: #991b1b;
  background: color-mix(in srgb, var(--color-primary) 10%, var(--color-bg-card));
  font-weight: 600;
  box-shadow: inset 3px 0 0 var(--color-primary);
  padding-left: 16px !important;
}

/* 分类圆点指示器 */
.app-sidebar__dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--color-text-secondary);
  flex-shrink: 0;
  transition: background .2s ease, transform .2s ease;
}

.app-sidebar__menu :deep(.el-menu-item:hover) .app-sidebar__dot {
  background: var(--color-primary);
  transform: scale(1.3);
}

.app-sidebar__menu :deep(.el-menu-item.is-active) .app-sidebar__dot {
  background: var(--color-primary);
  transform: scale(1.3);
}

/* ========================================
   订阅区域
   ======================================== */
.app-sidebar__subscription {
  margin-top: 14px;
  padding: 0 2px;
  border-top: 1px solid color-mix(in srgb, var(--color-primary) 8%, var(--color-border));
  padding-top: 14px;
}

.app-sidebar__subscription-trigger {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  height: 40px;
  padding: 0 12px;
  border: 0;
  border-radius: 12px;
  background: transparent;
  color: var(--color-text-primary);
  font-size: 14px;
  text-align: left;
  cursor: pointer;
  transition:
    background .2s ease,
    color .2s ease,
    padding-left .2s ease;
}

.app-sidebar__subscription-trigger:hover {
  color: var(--color-primary);
  background: color-mix(in srgb, var(--color-primary) 5%, var(--color-bg-card));
  padding-left: 16px;
}

.app-sidebar__subscription-trigger.is-active {
  color: #991b1b;
  background: color-mix(in srgb, var(--color-primary) 10%, var(--color-bg-card));
  font-weight: 600;
  box-shadow: inset 3px 0 0 var(--color-primary);
  padding-left: 16px;
}

.app-sidebar__subscription-trigger.is-active .app-sidebar__dot {
  background: var(--color-primary);
}

.app-sidebar__subscription-trigger:hover .app-sidebar__dot {
  background: var(--color-primary);
  transform: scale(1.3);
}

.app-sidebar__subscription-action {
  margin-left: auto;
  color: var(--color-text-secondary);
  font-size: 12px;
  transition: color .2s ease;
}

.app-sidebar__subscription-trigger:hover .app-sidebar__subscription-action,
.app-sidebar__subscription-trigger.is-active .app-sidebar__subscription-action {
  color: var(--color-primary);
}

/* ========================================
   订阅展开面板
   ======================================== */
.app-sidebar__subscription-panel {
  margin: 8px 0 0;
  padding: 16px;
  border: 1px solid color-mix(in srgb, var(--color-primary) 18%, var(--color-border));
  border-radius: 16px;
  background: var(--color-bg-card);
}

/* 面板标题区 */
.subscription-panel__header {
  margin-bottom: 14px;
}

.subscription-panel__title {
  margin: 0;
  color: var(--color-text-primary);
  font-size: 14px;
  font-weight: 700;
}

.subscription-panel__desc {
  margin: 4px 0 0;
  color: var(--color-text-secondary);
  font-size: 12px;
  line-height: 1.5;
}

/* ========================================
   订阅分类 checkbox —— 红白胶囊选项
   ======================================== */
.subscription-list {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 8px;
}

.subscription-list :deep(.el-checkbox) {
  height: auto;
  margin-right: 0;
  white-space: normal;
}

/* 把 checkbox 伪装成胶囊标签 */
.subscription-list :deep(.el-checkbox__label) {
  padding: 6px 14px;
  border: 1px solid var(--color-border);
  border-radius: 999px;
  background: var(--color-bg-card);
  color: var(--color-text-primary);
  font-size: 13px;
  transition:
    background .18s ease,
    border-color .18s ease,
    color .18s ease;
  cursor: pointer;
}

/* 隐藏原生 checkbox 小方块 */
.subscription-list :deep(.el-checkbox__input) {
  display: none;
}

/* hover 时胶囊变浅红 */
.subscription-list :deep(.el-checkbox:hover .el-checkbox__label) {
  border-color: color-mix(in srgb, var(--color-primary) 35%, var(--color-border));
  background: color-mix(in srgb, var(--color-primary) 5%, var(--color-bg-card));
  color: var(--color-primary);
}

/* 选中态：红底白字 */
.subscription-list :deep(.el-checkbox.is-checked .el-checkbox__label) {
  border-color: var(--color-primary);
  background: var(--color-primary);
  color: #fff;
  font-weight: 500;
}

/* ========================================
   订阅按钮组
   ======================================== */
.app-sidebar__subscription-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 16px;
}

.sub-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 7px 16px;
  border: 1px solid transparent;
  border-radius: 10px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition:
    background .18s ease,
    border-color .18s ease,
    color .18s ease;
}

/* 取消/重置按钮 */
.sub-btn--cancel {
  border-color: color-mix(in srgb, var(--color-primary) 25%, var(--color-border));
  background: transparent;
  color: var(--color-text-secondary);
}

.sub-btn--cancel:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
  background: color-mix(in srgb, var(--color-primary) 5%, var(--color-bg-card));
}

/* 保存按钮：红底白字 */
.sub-btn--save {
  border-color: var(--color-primary);
  background: var(--color-primary);
  color: #fff;
}

.sub-btn--save:hover:not(:disabled) {
  background: #b91c1c;
  border-color: #b91c1c;
}

.sub-btn--save:disabled {
  opacity: .6;
  cursor: not-allowed;
}

.sub-btn__spinner {
  display: inline-block;
  width: 13px;
  height: 13px;
  border: 2px solid rgba(255,255,255,.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: sub-spin .7s linear infinite;
}

@keyframes sub-spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* 暗色模式适配 */
:root.dark .app-sidebar__subscription-panel {
  border-color: color-mix(in srgb, var(--color-primary) 16%, rgba(255,255,255,.08));
}

:root.dark .subscription-list :deep(.el-checkbox__label) {
  border-color: rgba(255,255,255,.1);
  background: transparent;
}

:root.dark .subscription-list :deep(.el-checkbox:hover .el-checkbox__label) {
  border-color: color-mix(in srgb, var(--color-primary) 40%, rgba(255,255,255,.15));
  background: color-mix(in srgb, var(--color-primary) 10%, transparent);
}

:root.dark .sub-btn--cancel {
  border-color: rgba(255,255,255,.12);
  color: #aeb8c4;
}

:root.dark .sub-btn--cancel:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
}

/* ========================================
   事件脉络入口
   ======================================== */
.app-sidebar__timeline {
  margin-top: 12px;
  padding: 0 2px;
  border-top: 1px solid color-mix(in srgb, var(--color-primary) 10%, transparent);
  padding-top: 12px;
}

.app-sidebar__timeline-trigger {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 6px 12px;
  border: 0;
  border-radius: 12px;
  background: transparent;
  color: var(--color-text-primary);
  text-align: left;
  cursor: pointer;
  transition:
    background .2s ease,
    color .2s ease,
    padding-left .2s ease;
}

.app-sidebar__timeline-trigger:hover {
  color: var(--color-primary);
  background: color-mix(in srgb, var(--color-primary) 5%, var(--color-bg-card));
  padding-left: 16px;
}

.app-sidebar__timeline-trigger.is-active {
  color: #991b1b;
  background: color-mix(in srgb, var(--color-primary) 10%, var(--color-bg-card));
  font-weight: 600;
  box-shadow: inset 3px 0 0 var(--color-primary);
  padding-left: 16px;
}

.app-sidebar__timeline-trigger.is-active .app-sidebar__dot {
  background: var(--color-primary);
}

.app-sidebar__timeline-trigger:hover .app-sidebar__dot {
  background: var(--color-primary);
  transform: scale(1.3);
}

.app-sidebar__timeline-text {
  display: flex;
  flex-direction: column;
  gap: 1px;
  min-width: 0;
}

.app-sidebar__timeline-name {
  font-size: 14px;
  font-weight: 500;
  line-height: 1.3;
}

.app-sidebar__timeline-trigger.is-active .app-sidebar__timeline-name {
  font-weight: 600;
}

.app-sidebar__timeline-desc {
  color: var(--color-text-secondary);
  font-size: 11px;
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.app-sidebar__timeline-arrow {
  margin-left: auto;
  color: var(--color-text-secondary);
  font-size: 13px;
  transition:
    color .2s ease,
    transform .2s ease;
}

.app-sidebar__timeline-trigger:hover .app-sidebar__timeline-arrow {
  color: var(--color-primary);
  transform: translateX(2px);
}

.app-sidebar__timeline-trigger.is-active .app-sidebar__timeline-arrow {
  color: var(--color-primary);
}

:root.dark .app-sidebar__timeline-trigger:hover {
  background: color-mix(in srgb, var(--color-primary) 8%, rgba(255,255,255,.04));
}

:root.dark .app-sidebar__timeline-trigger.is-active {
  background: color-mix(in srgb, var(--color-primary) 12%, rgba(255,255,255,.04));
}

:root.dark .app-sidebar__timeline-name {
  color: #e5e7eb;
}

:root.dark .app-sidebar__timeline-desc {
  color: var(--color-text-muted);
}

</style>
