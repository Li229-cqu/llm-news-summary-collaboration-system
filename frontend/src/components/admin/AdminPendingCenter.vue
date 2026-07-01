<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Check,
  Delete,
  Filter,
  Minus,
  Refresh,
  Search,
} from '@element-plus/icons-vue'
import {
  type AdminPendingItem,
  type AdminPendingItemDetail,
  type AdminPendingItemType,
  type AdminPendingSummary,
  type AdminReviewAction,
  getPendingItemDetail,
  getPendingItems,
  reviewPendingItem,
} from '@/api/admin'

const emit = defineEmits<{
  changed: []
  'summary-change': [summary: AdminPendingSummary]
}>()

const tabs = [
  { key: 'all', label: '全部' },
  { key: 'news', label: '新闻' },
  { key: 'post', label: '帖子' },
  { key: 'comment', label: '评论' },
] as const

const statusTagType: Record<number, 'success' | 'warning' | 'info' | 'danger' | 'primary'> = {
  0: 'warning',
  1: 'success',
  2: 'info',
  3: 'warning',
  4: 'danger',
}

const actionLabels: Record<AdminReviewAction, string> = {
  approve: '通过',
  reject: '驳回',
  fold: '折叠',
  delete: '删除',
  restore: '恢复',
}

const activeTab = ref<AdminPendingItemType>('all')
const keyword = ref('')
const loading = ref(false)
const items = ref<AdminPendingItem[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const summary = ref<AdminPendingSummary>({
  pending_news_count: 0,
  pending_post_count: 0,
  pending_comment_count: 0,
  today_processed_count: 0,
})
const detailVisible = ref(false)
const detailLoading = ref(false)
const actionLoading = ref(false)
const detail = ref<AdminPendingItemDetail | null>(null)
const actionReason = ref('')

const currentTabLabel = computed(() => tabs.find(tab => tab.key === activeTab.value)?.label ?? '全部')

function emitSummary() {
  emit('summary-change', summary.value)
}

function normalizeText(value: unknown) {
  return String(value ?? '').trim()
}

function statusLabel(row: AdminPendingItem | AdminPendingItemDetail) {
  return row.status_label || '未知'
}

function actionButtons(row: AdminPendingItem | AdminPendingItemDetail): AdminReviewAction[] {
  if (row.status === 4) {
    return ['restore']
  }

  if (row.status === 1) {
    return ['fold', 'delete']
  }

  if (row.item_type === 'news') {
    return ['approve', 'reject', 'fold', 'delete']
  }

  return ['approve', 'reject', 'fold', 'delete']
}

async function loadItems(targetPage: number = page.value) {
  loading.value = true
  try {
    const result = await getPendingItems({
      type: activeTab.value,
      keyword: keyword.value.trim() || undefined,
      page: targetPage,
      pageSize: pageSize.value,
    })
    items.value = result.items || []
    total.value = result.total || 0
    page.value = result.page || targetPage
    pageSize.value = result.page_size || pageSize.value
    summary.value = result.summary || summary.value
    emitSummary()
  } catch (error) {
    items.value = []
    total.value = 0
    ElMessage.error(error instanceof Error ? error.message : '获取待审核数据失败')
  } finally {
    loading.value = false
  }
}

async function loadDetail(row: AdminPendingItem) {
  detailVisible.value = true
  detailLoading.value = true
  detail.value = null
  actionReason.value = ''
  try {
    detail.value = await getPendingItemDetail(row.item_type, row.id)
  } catch (error) {
    detail.value = null
    ElMessage.error(error instanceof Error ? error.message : '获取详情失败')
  } finally {
    detailLoading.value = false
  }
}

async function handleAction(action: AdminReviewAction, target?: AdminPendingItem | AdminPendingItemDetail) {
  const current = target || detail.value
  if (!current) return

  const actionText = actionLabels[action]
  const confirmText = `确定要${actionText}这条${current.item_type === 'news' ? '新闻' : current.item_type === 'post' ? '帖子' : '评论'}吗？`

  try {
    await ElMessageBox.confirm(confirmText, '审核确认', {
      type: action === 'delete' ? 'warning' : 'info',
      confirmButtonText: '确定',
      cancelButtonText: '取消',
    })
  } catch {
    return
  }

  actionLoading.value = true
  try {
    await reviewPendingItem(current.item_type, current.id, {
      action,
      reason: normalizeText(actionReason.value),
    })
    ElMessage.success('处理成功')
    await loadItems(page.value)
    emit('changed')
    if (detailVisible.value && detail.value?.id === current.id && detail.value.item_type === current.item_type) {
      detail.value = await getPendingItemDetail(current.item_type, current.id)
    }
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '处理失败')
  } finally {
    actionLoading.value = false
  }
}

function handleSearch() {
  page.value = 1
  void loadItems(1)
}

function handleReset() {
  keyword.value = ''
  page.value = 1
  void loadItems(1)
}

function handlePageChange(current: number) {
  page.value = current
  void loadItems(current)
}

watch(activeTab, () => {
  page.value = 1
  void loadItems(1)
})

onMounted(() => {
  void loadItems(1)
})
</script>

<template>
  <section class="pending-center">
    <el-card class="pending-card" shadow="never">
      <div class="pending-header">
        <div>
          <div class="pending-kicker">管理后台 · 待审核中心</div>
          <h3>待审核内容处理</h3>
          <p>新闻、帖子、评论统一在这里查看、审核和处理，数据直接来自数据库。</p>
        </div>
        <el-button :icon="Refresh" @click="loadItems(1)">刷新</el-button>
      </div>

      <div class="pending-summary-grid">
        <div class="summary-item">
          <span>待审新闻</span>
          <strong>{{ summary.pending_news_count }}</strong>
        </div>
        <div class="summary-item">
          <span>待审帖子</span>
          <strong>{{ summary.pending_post_count }}</strong>
        </div>
        <div class="summary-item">
          <span>待审评论</span>
          <strong>{{ summary.pending_comment_count }}</strong>
        </div>
        <div class="summary-item">
          <span>今日处理</span>
          <strong>{{ summary.today_processed_count }}</strong>
        </div>
      </div>

      <div class="pending-toolbar">
        <el-tabs v-model="activeTab" class="pending-tabs">
          <el-tab-pane v-for="tab in tabs" :key="tab.key" :label="tab.label" :name="tab.key" />
        </el-tabs>

        <div class="pending-search">
          <el-input
            v-model="keyword"
            clearable
            placeholder="搜索标题、内容、提交人"
            @keyup.enter="handleSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
          <el-button type="primary" @click="handleSearch">搜索</el-button>
          <el-button @click="handleReset">重置</el-button>
        </div>
      </div>

      <el-alert
        class="pending-tip"
        type="info"
        :closable="false"
        show-icon
        title="当前列表展示的是数据库中的真实待审/折叠/删除内容，不再使用 ?? 数据。"
      />

      <el-table v-loading="loading" :data="items" class="pending-table" border>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column label="类型" width="110">
          <template #default="scope">
            <el-tag effect="plain" :type="scope.row.item_type === 'news' ? 'success' : scope.row.item_type === 'post' ? 'warning' : 'info'">
              {{ scope.row.item_type === 'news' ? '新闻' : scope.row.item_type === 'post' ? '帖子' : '评论' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="title" label="标题 / 目标" min-width="240" />
        <el-table-column prop="submitter" label="提交人" width="140" />
        <el-table-column prop="source" label="来源" min-width="160" />
        <el-table-column prop="category_name" label="分类 / 话题" width="150" />
        <el-table-column prop="status_label" label="状态" width="110">
          <template #default="scope">
            <el-tag :type="statusTagType[scope.row.status] || 'info'" effect="plain">
              {{ statusLabel(scope.row) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="create_time" label="创建时间" width="180" />
        <el-table-column prop="update_time" label="更新时间" width="180" />
        <el-table-column label="操作" width="140" fixed="right">
          <template #default="scope">
            <el-button text type="primary" size="small" @click="loadDetail(scope.row)">查看</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pending-footer">
        <span>共 {{ total }} 条</span>
        <el-pagination
          background
          layout="prev, pager, next, total"
          :page-size="pageSize"
          :current-page="page"
          :total="total"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>

    <el-drawer
      v-model="detailVisible"
      :title="detail ? `待审核详情 · ${detail.item_type === 'news' ? '新闻' : detail.item_type === 'post' ? '帖子' : '评论'}` : '待审核详情'"
      size="720px"
      class="pending-drawer"
    >
      <div v-loading="detailLoading" class="detail-body">
        <template v-if="detail">
          <div class="detail-title-row">
            <h4>{{ detail.title || detail.source }}</h4>
            <el-tag :type="statusTagType[detail.status] || 'info'" effect="plain">{{ detail.status_label }}</el-tag>
          </div>

          <el-descriptions :column="1" border class="detail-desc" size="small">
            <el-descriptions-item label="类型">
              {{ detail.item_type === 'news' ? '新闻' : detail.item_type === 'post' ? '帖子' : '评论' }}
            </el-descriptions-item>
            <el-descriptions-item label="提交人">{{ detail.submitter }}</el-descriptions-item>
            <el-descriptions-item label="来源">{{ detail.source || '—' }}</el-descriptions-item>
            <el-descriptions-item label="分类 / 话题">{{ detail.category_name || detail.topic_name || '—' }}</el-descriptions-item>
            <el-descriptions-item label="创建时间">{{ detail.create_time || '—' }}</el-descriptions-item>
            <el-descriptions-item label="更新时间">{{ detail.update_time || '—' }}</el-descriptions-item>
          </el-descriptions>

          <div v-if="detail.item_type !== 'comment'" class="detail-section">
            <div class="section-label">正文 / 摘要</div>
            <p class="detail-content">{{ detail.content || detail.summary || '—' }}</p>
          </div>

          <div v-if="detail.item_type === 'comment'" class="detail-section">
            <div class="section-label">评论内容</div>
            <p class="detail-content">{{ detail.content || '—' }}</p>
          </div>

          <div v-if="detail.item_type === 'news'" class="detail-grid">
            <div class="detail-section">
              <div class="section-label">统计信息</div>
              <div class="detail-stats">
                <span>浏览 {{ detail.view_count ?? 0 }}</span>
                <span>点赞 {{ detail.like_count ?? 0 }}</span>
                <span>评论 {{ detail.comment_count ?? 0 }}</span>
                <span>收藏 {{ detail.favorite_count ?? 0 }}</span>
              </div>
            </div>
            <div class="detail-section">
              <div class="section-label">标签</div>
              <div class="tag-list">
                <el-tag v-for="tag in detail.tags || []" :key="tag" effect="plain">{{ tag }}</el-tag>
              </div>
            </div>
          </div>

          <div v-else-if="detail.item_type === 'post'" class="detail-grid">
            <div class="detail-section">
              <div class="section-label">关联新闻</div>
              <p class="detail-content">{{ detail.related_news_title || '—' }}</p>
            </div>
            <div class="detail-section">
              <div class="section-label">标签</div>
              <div class="tag-list">
                <el-tag v-for="tag in detail.tags || []" :key="tag" effect="plain">{{ tag }}</el-tag>
              </div>
            </div>
          </div>

          <div v-if="detail.item_type === 'comment'" class="detail-grid">
            <div class="detail-section">
              <div class="section-label">回复目标</div>
              <p class="detail-content">{{ detail.target_type === 'news' ? detail.news_id : detail.post_id || '—' }}</p>
            </div>
            <div class="detail-section">
              <div class="section-label">父级评论</div>
              <p class="detail-content">{{ detail.parent_content || '—' }}</p>
            </div>
          </div>

          <div class="detail-actions">
            <el-input
              v-model="actionReason"
              type="textarea"
              :rows="3"
              maxlength="200"
              show-word-limit
              placeholder="可填写处理备注"
            />
            <div class="action-row">
              <el-button
                v-for="action in actionButtons(detail)"
                :key="action"
                :type="action === 'approve' || action === 'restore' ? 'success' : action === 'delete' ? 'danger' : action === 'fold' ? 'warning' : 'primary'"
                :icon="action === 'approve' || action === 'restore' ? Check : action === 'delete' ? Delete : action === 'fold' ? Minus : Filter"
                :loading="actionLoading"
                @click="handleAction(action, detail)"
              >
                {{ actionLabels[action] }}
              </el-button>
            </div>
          </div>
        </template>

        <el-empty v-else description="暂无详情" />
      </div>
    </el-drawer>
  </section>
</template>

<style scoped>
.pending-center {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.pending-card {
  border-radius: 18px;
}

.pending-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;
}

.pending-kicker {
  margin-bottom: 8px;
  font-size: 12px;
  color: var(--color-primary);
}

.pending-header h3 {
  margin: 0 0 6px;
  color: var(--color-text-primary);
}

.pending-header p {
  margin: 0;
  color: var(--color-text-secondary);
}

.pending-summary-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}

.summary-item {
  padding: 14px;
  background: var(--color-bg-page);
  border: 1px solid var(--color-border-light);
  border-radius: 14px;
}

.summary-item span {
  display: block;
  margin-bottom: 8px;
  font-size: 13px;
  color: var(--color-text-secondary);
}

.summary-item strong {
  font-size: 24px;
  color: var(--color-text-primary);
}

.pending-toolbar {
  display: flex;
  flex-direction: column;
  gap: 14px;
  margin-bottom: 12px;
}

.pending-search {
  display: flex;
  gap: 12px;
  align-items: center;
}

.pending-search :deep(.el-input) {
  max-width: 360px;
}

.pending-tip {
  margin-bottom: 16px;
}

.pending-table {
  width: 100%;
}

.pending-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-top: 16px;
}

.detail-body {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.detail-title-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.detail-title-row h4 {
  margin: 0;
  font-size: 18px;
  color: var(--color-text-primary);
}

.detail-desc {
  width: 100%;
}

.detail-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 14px;
  border: 1px solid var(--color-border-light);
  border-radius: 14px;
  background: var(--color-bg-page);
}

.section-label {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-secondary);
}

.detail-content {
  margin: 0;
  line-height: 1.8;
  color: var(--color-text-primary);
  white-space: pre-wrap;
}

.detail-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 12px;
}

.detail-stats,
.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.detail-stats span {
  padding: 6px 10px;
  font-size: 13px;
  color: var(--color-text-secondary);
  background: rgba(64, 158, 255, 0.08);
  border-radius: 999px;
}

.detail-actions {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.action-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

@media (max-width: 1200px) {
  .pending-summary-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .pending-search {
    flex-direction: column;
    align-items: stretch;
  }

  .pending-search :deep(.el-input) {
    max-width: 100%;
  }
}

@media (max-width: 760px) {
  .pending-header {
    flex-direction: column;
  }

  .pending-summary-grid {
    grid-template-columns: 1fr;
  }

  .pending-footer {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
