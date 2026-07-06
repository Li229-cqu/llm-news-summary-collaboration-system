<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance } from 'element-plus'
import PaginationBar from '@/components/common/PaginationBar.vue'
import {
  featureAdminNews,
  getAdminNewsDetail,
  getAdminNewsList,
  getAdminNewsOptions,
  reviewAdminNews,
  unfeatureAdminNews,
  updateAdminNews,
  type AdminNewsDetail,
  type AdminNewsItem,
  type AdminNewsListResponse,
  type AdminNewsOptions,
  type AdminReviewAction,
} from '@/api/admin'

const emit = defineEmits<{ changed: [] }>()

const loading = ref(false)
const actionLoading = ref(false)
const detailLoading = ref(false)
const editLoading = ref(false)
const errorMessage = ref('')
const list = ref<AdminNewsItem[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const summary = ref<AdminNewsListResponse['summary'] | null>(null)
const options = ref<AdminNewsOptions>({ categories: [], topics: [], sources: [], feature_supported: false })
const detailVisible = ref(false)
const editVisible = ref(false)
const currentNews = ref<AdminNewsDetail | null>(null)
const editFormRef = ref<FormInstance>()

const filters = reactive({
  keyword: '',
  category_id: null as number | null,
  source: '',
  status: null as number | null,
  date_range: [] as string[],
})

const editForm = reactive({
  title: '',
  summary: '',
  content: '',
  source: '',
  category_id: null as number | null,
  cover_image: '',
  tagsText: '',
  publish_time: '',
})

const statusOptions = [
  { label: '已下架', value: 0 },
  { label: '已发布', value: 1 },
  { label: '已折叠', value: 2 },
  { label: '待审核', value: 3 },
  { label: '已删除', value: 4 },
]

const editRules = {
  title: [{ required: true, message: '请输入新闻标题', trigger: 'blur' }],
  content: [{ required: true, message: '请输入新闻正文', trigger: 'blur' }],
}

const summaryCards = computed(() => [
  { key: 'total', label: '全部新闻', value: summary.value?.total_count ?? 0 },
  { key: 'pending', label: '待审核', value: summary.value?.pending_count ?? 0 },
  { key: 'published', label: '已发布', value: summary.value?.published_count ?? 0 },
  { key: 'offline', label: '已下架', value: summary.value?.offline_count ?? 0 },
])

function statusTagType(status: number) {
  if (status === 1) return 'success'
  if (status === 3) return 'warning'
  if (status === 0 || status === 4) return 'danger'
  return 'info'
}

function parseTags(text: string) {
  return text
    .split(/[,，\n]/)
    .map(item => item.trim())
    .filter(Boolean)
}

async function loadOptions() {
  try {
    options.value = await getAdminNewsOptions()
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '新闻选项加载失败')
  }
}

async function loadNews(targetPage = page.value) {
  loading.value = true
  errorMessage.value = ''
  try {
    page.value = targetPage
    const [start, end] = filters.date_range || []
    const result = await getAdminNewsList({
      keyword: filters.keyword,
      category_id: filters.category_id,
      source: filters.source,
      status: filters.status,
      is_featured: undefined,
      start_time: start,
      end_time: end,
      page: page.value,
      page_size: pageSize.value,
    })
    list.value = result.items
    total.value = result.total
    summary.value = result.summary
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '新闻列表加载失败'
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  void loadNews(1)
}

function handleReset() {
  filters.keyword = ''
  filters.category_id = null
  filters.source = ''
  filters.status = null
  filters.date_range = []
  void loadNews(1)
}

async function openDetail(row: AdminNewsItem) {
  detailVisible.value = true
  detailLoading.value = true
  try {
    currentNews.value = await getAdminNewsDetail(row.id)
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '新闻详情加载失败')
  } finally {
    detailLoading.value = false
  }
}

async function openEdit(row: AdminNewsItem) {
  editLoading.value = true
  try {
    const detail = await getAdminNewsDetail(row.id)
    currentNews.value = detail
    editForm.title = detail.title
    editForm.summary = detail.summary
    editForm.content = detail.content
    editForm.source = detail.source
    editForm.category_id = detail.category_id ?? null
    editForm.cover_image = detail.cover_image
    editForm.tagsText = detail.tags.join(', ')
    editForm.publish_time = detail.publish_time || ''
    editVisible.value = true
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '新闻加载失败')
  } finally {
    editLoading.value = false
  }
}

async function submitEdit() {
  if (!currentNews.value) return
  const valid = await editFormRef.value?.validate().catch(() => false)
  if (!valid) return
  editLoading.value = true
  try {
    await updateAdminNews(currentNews.value.id, {
      title: editForm.title,
      summary: editForm.summary,
      content: editForm.content,
      source: editForm.source,
      category_id: editForm.category_id,
      cover_image: editForm.cover_image,
      tags: parseTags(editForm.tagsText),
      publish_time: editForm.publish_time || null,
    })
    ElMessage.success('保存成功')
    editVisible.value = false
    await loadNews(page.value)
    emit('changed')
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '保存失败')
  } finally {
    editLoading.value = false
  }
}

async function runStatusAction(row: AdminNewsItem, action: AdminReviewAction) {
  const actionLabel: Record<AdminReviewAction, string> = {
    approve: '通过',
    reject: row.status === 1 ? '下架' : '退回',
    fold: '折叠',
    delete: '删除',
    restore: '恢复',
  }
  try {
    await ElMessageBox.confirm(`确认${actionLabel[action]}该新闻？`, '操作确认', {
      type: action === 'delete' ? 'warning' : 'info',
      confirmButtonText: '确定',
      cancelButtonText: '取消',
    })
  } catch {
    return
  }
  actionLoading.value = true
  try {
    await reviewAdminNews(row.id, { action, reason: `admin news ${action}` })
    ElMessage.success('处理成功')
    await loadNews(page.value)
    emit('changed')
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '处理失败')
  } finally {
    actionLoading.value = false
  }
}

async function toggleFeature(row: AdminNewsItem, featured: boolean) {
  if (!options.value.feature_supported) {
    ElMessage.warning('当前 news 表暂不支持精选字段')
    return
  }
  actionLoading.value = true
  try {
    if (featured) await featureAdminNews(row.id)
    else await unfeatureAdminNews(row.id)
    ElMessage.success('处理成功')
    await loadNews(page.value)
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '处理失败')
  } finally {
    actionLoading.value = false
  }
}

function availableActions(row: AdminNewsItem) {
  if (row.status === 3) return [] as AdminReviewAction[]
  if (row.status === 1) return ['reject'] as AdminReviewAction[]
  if (row.status === 0 || row.status === 4) return ['restore', 'delete'] as AdminReviewAction[]
  return ['restore'] as AdminReviewAction[]
}

onMounted(async () => {
  await Promise.allSettled([loadOptions(), loadNews(1)])
})
</script>

<template>
  <section class="admin-news-management">
    <el-card class="news-panel" shadow="never">
      <template #header>
        <div class="panel-header">
          <div>
            <h2>新闻内容管理</h2>
            <p>管理新闻列表、编辑内容、上下架；待审核新闻统一在待审核中心处理。</p>
          </div>
          <el-button type="primary" @click="loadNews(1)">刷新</el-button>
        </div>
      </template>

      <div class="summary-grid">
        <article v-for="card in summaryCards" :key="card.key" class="summary-card">
          <span>{{ card.label }}</span>
          <strong>{{ card.value }}</strong>
        </article>
      </div>

      <div class="filter-bar">
        <div class="filter-row-1">
          <el-input v-model="filters.keyword" clearable placeholder="搜索标题、摘要、正文或来源" class="filter-keyword" />
          <el-select v-model="filters.category_id" clearable filterable placeholder="分类" class="filter-select">
            <el-option v-for="item in options.categories" :key="item.id" :label="item.name" :value="item.id" />
          </el-select>
          <el-select v-model="filters.source" clearable filterable allow-create placeholder="来源" class="filter-select">
            <el-option v-for="item in options.sources" :key="item" :label="item" :value="item" />
          </el-select>
          <el-select v-model="filters.status" clearable placeholder="状态" class="filter-select">
            <el-option v-for="item in statusOptions" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
        </div>
        <div class="filter-row-2">
          <el-date-picker
            v-model="filters.date_range"
            type="datetimerange"
            value-format="YYYY-MM-DD HH:mm:ss"
            start-placeholder="开始时间"
            end-placeholder="结束时间"
            class="filter-date-range"
          />
          <div class="filter-actions">
            <el-button type="primary" @click="handleSearch">查询</el-button>
            <el-button @click="handleReset">重置</el-button>
          </div>
        </div>
      </div>

      <el-alert v-if="errorMessage" :title="errorMessage" type="error" show-icon :closable="false" class="error-alert" />

      <el-table v-loading="loading" :data="list" border class="news-table" empty-text="暂无新闻数据">
        <el-table-column prop="title" label="标题" min-width="240" show-overflow-tooltip />
        <el-table-column prop="category_name" label="分类" width="120" />
        <el-table-column prop="source" label="来源" min-width="130" show-overflow-tooltip />
        <el-table-column prop="publish_time" label="发布时间" width="170" />
        <el-table-column prop="view_count" label="浏览" width="80" />
        <el-table-column prop="like_count" label="点赞" width="80" />
        <el-table-column prop="comment_count" label="评论" width="80" />
        <el-table-column prop="favorite_count" label="收藏" width="80" />
        <el-table-column label="状态" width="110">
          <template #default="scope">
            <el-tag :type="statusTagType(scope.row.status)" effect="plain">{{ scope.row.status_label }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="270" fixed="right">
          <template #default="scope">
            <el-button size="small" text type="primary" @click="openDetail(scope.row)">查看</el-button>
            <el-button size="small" text type="primary" @click="openEdit(scope.row)">编辑</el-button>
            <el-button
              v-for="action in availableActions(scope.row)"
              :key="action"
              size="small"
              text
              :type="action === 'delete' || action === 'reject' ? 'danger' : 'primary'"
              :loading="actionLoading"
              @click="runStatusAction(scope.row, action)"
            >
              {{ action === 'approve' ? '通过' : action === 'reject' ? '下架' : action === 'delete' ? '删除' : action === 'restore' ? '恢复' : '折叠' }}
            </el-button>
            <el-button v-if="scope.row.status === 3" size="small" text disabled>待审核中心处理</el-button>
          </template>
        </el-table-column>
      </el-table>

      <PaginationBar
        :current-page="page"
        :total-pages="Math.ceil(total / pageSize)"
        @change="loadNews"
      />
    </el-card>

    <el-drawer v-model="detailVisible" title="新闻详情" size="720px">
      <el-skeleton v-if="detailLoading" animated :rows="8" />
      <div v-else-if="currentNews" class="detail-body">
        <h2>{{ currentNews.title }}</h2>
        <div v-if="currentNews.cover_image" class="cover"><img :src="currentNews.cover_image" alt="新闻封面" /></div>
        <el-empty v-else description="暂无封面图" />
        <el-descriptions :column="2" border>
          <el-descriptions-item label="来源">{{ currentNews.source }}</el-descriptions-item>
          <el-descriptions-item label="编辑">{{ currentNews.editor || currentNews.source }}</el-descriptions-item>
          <el-descriptions-item label="发布时间">{{ currentNews.publish_time || '-' }}</el-descriptions-item>
          <el-descriptions-item label="分类">{{ currentNews.category_name || currentNews.category_id || '-' }}</el-descriptions-item>
          <el-descriptions-item label="状态">{{ currentNews.status_label }}</el-descriptions-item>
          <el-descriptions-item label="浏览量">{{ currentNews.view_count }}</el-descriptions-item>
          <el-descriptions-item label="点赞/评论/收藏">{{ currentNews.like_count }} / {{ currentNews.comment_count }} / {{ currentNews.favorite_count }}</el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ currentNews.create_time || '-' }}</el-descriptions-item>
          <el-descriptions-item label="更新时间">{{ currentNews.update_time || '-' }}</el-descriptions-item>
        </el-descriptions>
        <section><h3>摘要</h3><p>{{ currentNews.summary || '暂无摘要' }}</p></section>
        <section><h3>正文</h3><div class="content-text">{{ currentNews.content || '暂无正文' }}</div></section>
        <section><h3>标签</h3><el-tag v-for="tag in currentNews.tags" :key="tag" effect="plain">{{ tag }}</el-tag><span v-if="!currentNews.tags.length">暂无标签</span></section>
      </div>
    </el-drawer>

    <el-dialog v-model="editVisible" title="编辑新闻" width="760px" destroy-on-close>
      <el-form ref="editFormRef" :model="editForm" :rules="editRules" label-width="110px">
        <el-form-item label="标题" prop="title"><el-input v-model="editForm.title" /></el-form-item>
        <el-form-item label="摘要"><el-input v-model="editForm.summary" type="textarea" :rows="3" /></el-form-item>
        <el-form-item label="正文" prop="content"><el-input v-model="editForm.content" type="textarea" :rows="8" /></el-form-item>
        <el-form-item label="来源"><el-input v-model="editForm.source" /></el-form-item>
        <el-form-item label="分类">
          <el-select v-model="editForm.category_id" clearable filterable>
            <el-option v-for="item in options.categories" :key="item.id" :label="item.name" :value="item.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="封面 URL"><el-input v-model="editForm.cover_image" /></el-form-item>
        <el-form-item label="标签"><el-input v-model="editForm.tagsText" placeholder="多个标签用逗号分隔" /></el-form-item>
        <el-form-item label="发布时间"><el-date-picker v-model="editForm.publish_time" type="datetime" value-format="YYYY-MM-DD HH:mm:ss" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editVisible = false">取消</el-button>
        <el-button type="primary" :loading="editLoading" @click="submitEdit">保存</el-button>
      </template>
    </el-dialog>
  </section>
</template>

<style scoped>
.admin-news-management { width: 100%; }
.news-panel { border-radius: 16px; }
.panel-header { display: flex; justify-content: space-between; gap: 16px; align-items: flex-start; }
.panel-header h2 { margin: 0 0 6px; }
.panel-header p { margin: 0; color: var(--color-text-secondary); }
.summary-grid { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 12px; margin-bottom: 16px; }
.summary-card { padding: 14px; border: 1px solid var(--color-border-light); border-radius: 12px; background: var(--color-bg-page); }
.summary-card span { display: block; color: var(--color-text-secondary); font-size: 13px; }
.summary-card strong { display: block; margin-top: 6px; font-size: 22px; color: var(--color-text-primary); }
.error-alert { margin-bottom: 16px; }
.filter-bar {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 16px;
}
.filter-row-1, .filter-row-2 {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
}
.filter-keyword { width: 320px; }
.filter-select { width: 200px; }
.filter-date-range { width: 400px; }
.filter-row-2 .filter-actions {
  display: flex;
  gap: 8px;
}
.filter-actions .el-button:first-child {
  background: var(--el-color-primary);
  border-color: var(--el-color-primary);
  color: #fff;
}
.news-table { width: 100%; }
.pagination-row { display: flex; justify-content: flex-end; margin-top: 16px; }
.detail-body { display: flex; flex-direction: column; gap: 18px; }
.cover img { width: 100%; max-height: 260px; object-fit: cover; border-radius: 10px; }
.content-text { white-space: pre-wrap; line-height: 1.7; }
@media (max-width: 1200px) { .summary-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); } }
@media (max-width: 960px) {
  .summary-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .filter-row-1, .filter-row-2 { flex-direction: column; align-items: stretch; }
  .filter-keyword, .filter-select, .filter-date-range { width: 100%; }
}
</style>
