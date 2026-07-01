<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance } from 'element-plus'
import {
  getAdminNewsDetail,
  getAdminNewsList,
  getAdminNewsOptions,
  updateAdminNews,
  updateAdminNewsTopic,
  reviewAdminNews,
  featureAdminNews,
  unfeatureAdminNews,
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
const topicLoading = ref(false)
const errorMessage = ref('')
const list = ref<AdminNewsItem[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const summary = ref<AdminNewsListResponse['summary'] | null>(null)
const options = ref<AdminNewsOptions>({ categories: [], topics: [], sources: [], feature_supported: false })
const detailVisible = ref(false)
const editVisible = ref(false)
const topicVisible = ref(false)
const currentNews = ref<AdminNewsDetail | null>(null)
const editFormRef = ref<FormInstance>()

const filters = reactive({
  keyword: '',
  category_id: null as number | null,
  source: '',
  status: null as number | null,
  is_featured: null as boolean | null,
  has_topic: null as boolean | null,
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

const topicForm = reactive({
  topic_id: null as number | null,
})

const statusOptions = [
  { label: '\u5df2\u4e0b\u67b6', value: 0 },
  { label: '\u5df2\u53d1\u5e03', value: 1 },
  { label: '\u5df2\u6298\u53e0', value: 2 },
  { label: '\u5f85\u5ba1\u6838', value: 3 },
  { label: '\u5df2\u5220\u9664', value: 4 },
]

const editRules = {
  title: [{ required: true, message: '\u8bf7\u8f93\u5165\u65b0\u95fb\u6807\u9898', trigger: 'blur' }],
  content: [{ required: true, message: '\u8bf7\u8f93\u5165\u65b0\u95fb\u6b63\u6587', trigger: 'blur' }],
}

const summaryCards = computed(() => [
  { key: 'total', label: '\u5168\u90e8\u65b0\u95fb', value: summary.value?.total_count ?? 0 },
  { key: 'pending', label: '\u5f85\u5ba1\u6838', value: summary.value?.pending_count ?? 0 },
  { key: 'published', label: '\u5df2\u53d1\u5e03', value: summary.value?.published_count ?? 0 },
  { key: 'offline', label: '\u5df2\u4e0b\u67b6', value: summary.value?.offline_count ?? 0 },
  { key: 'unbound', label: '\u672a\u7ed1\u5b9a\u8bdd\u9898', value: summary.value?.unbound_topic_count ?? 0 },
])

function statusTagType(status: number) {
  if (status === 1) return 'success'
  if (status === 3) return 'warning'
  if (status === 0 || status === 4) return 'danger'
  return 'info'
}

function parseTags(text: string) {
  return text
    .split(/[,?\n]/)
    .map(item => item.trim())
    .filter(Boolean)
}

async function loadOptions() {
  options.value = await getAdminNewsOptions()
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
      is_featured: options.value.feature_supported ? filters.is_featured : null,
      has_topic: filters.has_topic,
      start_time: start,
      end_time: end,
      page: page.value,
      page_size: pageSize.value,
    })
    list.value = result.items
    total.value = result.total
    summary.value = result.summary
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '\u65b0\u95fb\u5217\u8868\u52a0\u8f7d\u5931\u8d25'
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
  filters.is_featured = null
  filters.has_topic = null
  filters.date_range = []
  void loadNews(1)
}

async function openDetail(row: AdminNewsItem) {
  detailVisible.value = true
  detailLoading.value = true
  try {
    currentNews.value = await getAdminNewsDetail(row.id)
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '\u65b0\u95fb\u8be6\u60c5\u52a0\u8f7d\u5931\u8d25')
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
    ElMessage.error(error instanceof Error ? error.message : '\u65b0\u95fb\u52a0\u8f7d\u5931\u8d25')
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
    ElMessage.success('\u4fdd\u5b58\u6210\u529f')
    editVisible.value = false
    await loadNews(page.value)
    emit('changed')
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '\u4fdd\u5b58\u5931\u8d25')
  } finally {
    editLoading.value = false
  }
}

function openTopic(row: AdminNewsItem) {
  currentNews.value = row as AdminNewsDetail
  topicForm.topic_id = row.topic_id ?? null
  topicVisible.value = true
}

async function submitTopic() {
  if (!currentNews.value) return
  topicLoading.value = true
  try {
    await updateAdminNewsTopic(currentNews.value.id, topicForm.topic_id)
    ElMessage.success('\u8bdd\u9898\u7ed1\u5b9a\u5df2\u66f4\u65b0')
    topicVisible.value = false
    await loadNews(page.value)
    emit('changed')
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '\u8bdd\u9898\u7ed1\u5b9a\u5931\u8d25')
  } finally {
    topicLoading.value = false
  }
}

async function runStatusAction(row: AdminNewsItem, action: AdminReviewAction) {
  const actionLabel: Record<AdminReviewAction, string> = {
    approve: '\u901a\u8fc7',
    reject: '\u9000\u56de',
    fold: '\u6298\u53e0',
    delete: '\u5220\u9664',
    restore: '\u6062\u590d',
  }
  try {
    await ElMessageBox.confirm(`\u786e\u8ba4${actionLabel[action]}\u8be5\u65b0\u95fb\uff1f`, '\u64cd\u4f5c\u786e\u8ba4', {
      type: action === 'delete' ? 'warning' : 'info',
      confirmButtonText: '\u786e\u5b9a',
      cancelButtonText: '\u53d6\u6d88',
    })
  } catch {
    return
  }
  actionLoading.value = true
  try {
    await reviewAdminNews(row.id, { action, reason: `admin news ${action}` })
    ElMessage.success('\u5904\u7406\u6210\u529f')
    await loadNews(page.value)
    emit('changed')
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '\u5904\u7406\u5931\u8d25')
  } finally {
    actionLoading.value = false
  }
}

async function toggleFeature(row: AdminNewsItem, featured: boolean) {
  if (!options.value.feature_supported) {
    ElMessage.warning('\u5f53\u524d\u6570\u636e\u8868\u6682\u4e0d\u652f\u6301\u7cbe\u9009\u5b57\u6bb5')
    return
  }
  actionLoading.value = true
  try {
    if (featured) await featureAdminNews(row.id)
    else await unfeatureAdminNews(row.id)
    ElMessage.success('\u5904\u7406\u6210\u529f')
    await loadNews(page.value)
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '\u5904\u7406\u5931\u8d25')
  } finally {
    actionLoading.value = false
  }
}

function availableActions(row: AdminNewsItem) {
  if (row.status === 3) return ['approve', 'reject'] as AdminReviewAction[]
  if (row.status === 1) return ['reject'] as AdminReviewAction[]
  if (row.status === 0 || row.status === 4) return ['restore', 'delete'] as AdminReviewAction[]
  return ['restore'] as AdminReviewAction[]
}

onMounted(async () => {
  try {
    await loadOptions()
  } finally {
    await loadNews(1)
  }
})
</script>

<template>
  <section class="admin-news-management">
    <el-card class="news-panel" shadow="never">
      <template #header>
        <div class="panel-header">
          <div>
            <h2>&#26032;&#38395;&#20869;&#23481;&#31649;&#29702;</h2>
            <p>&#31649;&#29702;&#26032;&#38395;&#20869;&#23481;&#12289;&#23457;&#26680;&#29366;&#24577;&#12289;&#20998;&#31867;&#19982;&#35805;&#39064;&#24402;&#23646;&#12290;</p>
          </div>
          <el-button type="primary" @click="loadNews(1)">&#21047;&#26032;</el-button>
        </div>
      </template>

      <div class="summary-grid">
        <article v-for="card in summaryCards" :key="card.key" class="summary-card">
          <span>{{ card.label }}</span>
          <strong>{{ card.value }}</strong>
        </article>
      </div>

      <el-alert
        v-if="!options.feature_supported"
        class="feature-alert"
        type="info"
        show-icon
        :closable="false"
        title="&#24403;&#21069; news &#34920;&#26242;&#19981;&#25903;&#25345;&#31934;&#36873;&#23383;&#27573;&#65292;&#31934;&#36873;&#25805;&#20316;&#24050;&#31105;&#29992;&#12290;"
      />

      <div class="filter-bar">
        <el-input v-model="filters.keyword" clearable placeholder="&#25628;&#32034;&#26631;&#39064;&#12289;&#25688;&#35201;&#12289;&#27491;&#25991;&#25110;&#26469;&#28304;" />
        <el-select v-model="filters.category_id" clearable filterable placeholder="&#20998;&#31867;">
          <el-option v-for="item in options.categories" :key="item.id" :label="item.name" :value="item.id" />
        </el-select>
        <el-select v-model="filters.source" clearable filterable allow-create placeholder="&#26469;&#28304;">
          <el-option v-for="item in options.sources" :key="item" :label="item" :value="item" />
        </el-select>
        <el-select v-model="filters.status" clearable placeholder="&#29366;&#24577;">
          <el-option v-for="item in statusOptions" :key="item.value" :label="item.label" :value="item.value" />
        </el-select>
        <el-select v-model="filters.has_topic" clearable placeholder="&#35805;&#39064;&#32465;&#23450;">
          <el-option label="&#24050;&#32465;&#23450;" :value="true" />
          <el-option label="&#26410;&#32465;&#23450;" :value="false" />
        </el-select>
        <el-select v-model="filters.is_featured" clearable :disabled="!options.feature_supported" placeholder="&#31934;&#36873;">
          <el-option label="&#24050;&#31934;&#36873;" :value="true" />
          <el-option label="&#26410;&#31934;&#36873;" :value="false" />
        </el-select>
        <el-date-picker
          v-model="filters.date_range"
          type="datetimerange"
          value-format="YYYY-MM-DD HH:mm:ss"
          start-placeholder="&#24320;&#22987;&#26102;&#38388;"
          end-placeholder="&#32467;&#26463;&#26102;&#38388;"
        />
        <div class="filter-actions">
          <el-button type="primary" @click="handleSearch">&#26597;&#35810;</el-button>
          <el-button @click="handleReset">&#37325;&#32622;</el-button>
        </div>
      </div>

      <el-alert v-if="errorMessage" :title="errorMessage" type="error" show-icon :closable="false" class="error-alert" />

      <el-table v-loading="loading" :data="list" border class="news-table" empty-text="No news data">
        <el-table-column prop="title" label="Title" min-width="240" show-overflow-tooltip />
        <el-table-column prop="category_name" label="Tags" width="120" />
        <el-table-column prop="source" label="Tags" min-width="130" show-overflow-tooltip />
        <el-table-column prop="publish_time" label="Publish Time" width="170" />
        <el-table-column prop="view_count" label="Tags" width="80" />
        <el-table-column prop="like_count" label="Tags" width="80" />
        <el-table-column prop="comment_count" label="Tags" width="80" />
        <el-table-column prop="favorite_count" label="Tags" width="80" />
        <el-table-column label="Tags" width="110">
          <template #default="scope">
            <el-tag :type="statusTagType(scope.row.status)" effect="plain">{{ scope.row.status_label }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="Tags" width="90">
          <template #default="scope">
            <el-tag v-if="options.feature_supported" :type="scope.row.is_featured ? 'success' : 'info'" effect="plain">
              {{ scope.row.is_featured ? '?' : '?' }}
            </el-tag>
            <el-tag v-else type="info" effect="plain">Unsupported</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="Tags" min-width="140" show-overflow-tooltip>
          <template #default="scope">{{ scope.row.topic_name || scope.row.topic_id || 'Unbound' }}</template>
        </el-table-column>
        <el-table-column label="Tags" width="330" fixed="right">
          <template #default="scope">
            <el-button size="small" text type="primary" @click="openDetail(scope.row)">-</el-button>
            <el-button size="small" text type="primary" @click="openEdit(scope.row)">-</el-button>
            <el-button
              v-for="action in availableActions(scope.row)"
              :key="action"
              size="small"
              text
              :type="action === 'delete' || action === 'reject' ? 'danger' : 'primary'"
              :loading="actionLoading"
              @click="runStatusAction(scope.row, action)"
            >
              {{ action === 'approve' ? '-' : action === 'reject' ? '-' : action === 'delete' ? '-' : action === 'restore' ? '-' : '-' }}
            </el-button>
            <el-button size="small" text :disabled="!options.feature_supported" @click="toggleFeature(scope.row, !scope.row.is_featured)">
              {{ scope.row.is_featured ? 'Unfeature' : 'Feature' }}
            </el-button>
            <el-button size="small" text @click="openTopic(scope.row)">Bind Topic</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-row">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @current-change="loadNews"
          @size-change="() => loadNews(1)"
        />
      </div>
    </el-card>

    <el-drawer v-model="detailVisible" title="News Detail" size="720px">
      <el-skeleton v-if="detailLoading" animated :rows="8" />
      <div v-else-if="currentNews" class="detail-body">
        <h2>{{ currentNews.title }}</h2>
        <div v-if="currentNews.cover_image" class="cover"><img :src="currentNews.cover_image" alt="cover" /></div>
        <el-empty v-else description="No cover image" />
        <el-descriptions :column="2" border>
          <el-descriptions-item label="Tags">{{ currentNews.source }}</el-descriptions-item>
          <el-descriptions-item label="Tags">{{ currentNews.editor || currentNews.source }}</el-descriptions-item>
          <el-descriptions-item label="Publish Time">{{ currentNews.publish_time || '-' }}</el-descriptions-item>
          <el-descriptions-item label="Tags">{{ currentNews.category_name || currentNews.category_id || '-' }}</el-descriptions-item>
          <el-descriptions-item label="Tags">{{ currentNews.status_label }}</el-descriptions-item>
          <el-descriptions-item label="Tags">{{ currentNews.topic_name || currentNews.topic_id || 'Unbound' }}</el-descriptions-item>
          <el-descriptions-item label="Tags">{{ currentNews.view_count }}</el-descriptions-item>
          <el-descriptions-item label="-/-/-">{{ currentNews.like_count }} / {{ currentNews.comment_count }} / {{ currentNews.favorite_count }}</el-descriptions-item>
          <el-descriptions-item label="Publish Time">{{ currentNews.create_time || '-' }}</el-descriptions-item>
          <el-descriptions-item label="Publish Time">{{ currentNews.update_time || '-' }}</el-descriptions-item>
        </el-descriptions>
        <section><h3>Summary</h3><p>{{ currentNews.summary || 'No summary' }}</p></section>
        <section><h3>Content</h3><div class="content-text">{{ currentNews.content || 'No content' }}</div></section>
        <section><h3>Tags</h3><el-tag v-for="tag in currentNews.tags" :key="tag" effect="plain">{{ tag }}</el-tag><span v-if="!currentNews.tags.length">No tags</span></section>
      </div>
    </el-drawer>

    <el-dialog v-model="editVisible" title="Edit News" width="760px" destroy-on-close>
      <el-form ref="editFormRef" :model="editForm" :rules="editRules" label-width="110px">
        <el-form-item label="Tags" prop="title"><el-input v-model="editForm.title" /></el-form-item>
        <el-form-item label="Tags"><el-input v-model="editForm.summary" type="textarea" :rows="3" /></el-form-item>
        <el-form-item label="Tags" prop="content"><el-input v-model="editForm.content" type="textarea" :rows="8" /></el-form-item>
        <el-form-item label="Tags"><el-input v-model="editForm.source" /></el-form-item>
        <el-form-item label="Tags">
          <el-select v-model="editForm.category_id" clearable filterable>
            <el-option v-for="item in options.categories" :key="item.id" :label="item.name" :value="item.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="Cover URL"><el-input v-model="editForm.cover_image" /></el-form-item>
        <el-form-item label="Tags"><el-input v-model="editForm.tagsText" placeholder="Separate tags with commas" /></el-form-item>
        <el-form-item label="Publish Time"><el-date-picker v-model="editForm.publish_time" type="datetime" value-format="YYYY-MM-DD HH:mm:ss" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editVisible = false">-</el-button>
        <el-button type="primary" :loading="editLoading" @click="submitEdit">-</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="topicVisible" title="Bind Topic" width="460px">
      <p class="topic-title">{{ currentNews?.title }}</p>
      <el-select v-model="topicForm.topic_id" clearable filterable placeholder="Select or clear topic">
        <el-option v-for="item in options.topics" :key="item.id" :label="item.topic_name" :value="item.id" />
      </el-select>
      <template #footer>
        <el-button @click="topicVisible = false">-</el-button>
        <el-button type="primary" :loading="topicLoading" @click="submitTopic">-</el-button>
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
.feature-alert, .error-alert { margin-bottom: 16px; }
.filter-bar { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; margin-bottom: 16px; }
.filter-actions { display: flex; gap: 8px; }
.news-table { width: 100%; }
.pagination-row { display: flex; justify-content: flex-end; margin-top: 16px; }
.detail-body { display: flex; flex-direction: column; gap: 18px; }
.detail-body h2 { margin: 0; line-height: 1.4; }
.cover { width: 100%; max-height: 260px; overflow: hidden; border-radius: 10px; border: 1px solid var(--color-border-light); }
.cover img { display: block; width: 100%; height: 100%; object-fit: cover; }
.content-text { white-space: pre-wrap; line-height: 1.8; max-height: 360px; overflow: auto; padding: 12px; background: var(--color-bg-page); border-radius: 10px; }
.topic-title { margin-top: 0; color: var(--color-text-secondary); }
@media (max-width: 1200px) { .summary-grid { grid-template-columns: repeat(2, 1fr); } .filter-bar { grid-template-columns: 1fr; } }
</style>
