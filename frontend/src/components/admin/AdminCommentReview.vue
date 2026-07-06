<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getAdminCommentDetail,
  getAdminCommentList,
  getAdminCommentOptions,
  reviewAdminComment,
  type AdminCommentDetail,
  type AdminCommentItem,
  type AdminCommentListResponse,
  type AdminCommentOptions,
  type AdminReviewAction,
} from '@/api/admin'

const emit = defineEmits<{ changed: [] }>()

type CommentTab = 'all' | 'news' | 'post' | 'pending' | 'folded' | 'deleted'

const loading = ref(false)
const actionLoading = ref(false)
const detailLoading = ref(false)
const errorMessage = ref('')
const activeTab = ref<CommentTab>('all')
const list = ref<AdminCommentItem[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const summary = ref<AdminCommentListResponse['summary'] | null>(null)
const options = ref<AdminCommentOptions>({ statuses: [], types: [], report_supported: false })
const detailVisible = ref(false)
const currentComment = ref<AdminCommentDetail | null>(null)

const filters = reactive({
  keyword: '',
  user_id: null as number | null,
  username: '',
  type: 'all' as 'all' | 'news' | 'post',
  status: null as number | null,
  news_id: null as number | null,
  post_id: null as number | null,
  has_parent: null as boolean | null,
  date_range: [] as string[],
})

const tabItems = computed(() => [
  { key: 'all', label: '\u5168\u90e8\u8bc4\u8bba' },
  { key: 'news', label: '\u65b0\u95fb\u8bc4\u8bba' },
  { key: 'post', label: '\u793e\u533a\u8bc4\u8bba' },
  { key: 'pending', label: '\u5f85\u590d\u6838' },
  { key: 'folded', label: '\u5df2\u6298\u53e0' },
  { key: 'deleted', label: '\u5df2\u5220\u9664' },
])

const summaryCards = computed(() => [
  { key: 'total', label: '\u5168\u90e8\u8bc4\u8bba', value: summary.value?.total_count ?? 0 },
  { key: 'news', label: '\u65b0\u95fb\u8bc4\u8bba', value: summary.value?.news_comment_count ?? 0 },
  { key: 'post', label: '\u793e\u533a\u8bc4\u8bba', value: summary.value?.post_comment_count ?? 0 },
  { key: 'folded', label: '\u5df2\u6298\u53e0', value: summary.value?.folded_count ?? 0 },
  { key: 'deleted', label: '\u5df2\u5220\u9664', value: summary.value?.deleted_count ?? 0 },
])

type CommentMediaJson = {
  images?: string[]
  emojis?: string[]
}

function parseMediaJson(value: unknown): CommentMediaJson | null {
  if (!value) return null
  if (typeof value === 'object') return value as CommentMediaJson
  if (typeof value !== 'string') return null
  const raw = value.trim()
  if (!raw) return null
  try {
    return JSON.parse(raw) as CommentMediaJson
  } catch {
    return null
  }
}

function getMediaImages(value: unknown): string[] {
  return parseMediaJson(value)?.images?.filter(Boolean) ?? []
}

function normalizeMediaImageUrl(image: string): string {
  if (image.startsWith('http://') || image.startsWith('https://') || image.startsWith('data:image/')) return image
  if (image.startsWith('/')) return image
  return `/${image}`
}

function statusTagType(status: number) {
  if (status === 1) return 'success'
  if (status === 3) return 'warning'
  if (status === 2) return 'info'
  if (status === 0 || status === 4) return 'danger'
  return 'info'
}

function buildQuery(targetPage = page.value) {
  const [start, end] = filters.date_range || []
  let queryType = filters.type
  let queryStatus = filters.status
  if (activeTab.value === 'news') queryType = 'news'
  if (activeTab.value === 'post') queryType = 'post'
  if (activeTab.value === 'pending') queryStatus = 3
  if (activeTab.value === 'folded') queryStatus = 2
  if (activeTab.value === 'deleted') queryStatus = 4
  return {
    type: queryType,
    keyword: filters.keyword,
    user_id: filters.user_id,
    username: filters.username,
    status: queryStatus,
    news_id: filters.news_id,
    post_id: filters.post_id,
    has_parent: filters.has_parent,
    start_time: start,
    end_time: end,
    page: targetPage,
    page_size: pageSize.value,
  }
}

async function loadOptions() {
  try {
    options.value = await getAdminCommentOptions()
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '评论选项加载失败')
  }
}

async function loadComments(targetPage = page.value) {
  loading.value = true
  errorMessage.value = ''
  try {
    page.value = targetPage
    const result = await getAdminCommentList(buildQuery(page.value))
    list.value = result.items
    total.value = result.total
    summary.value = result.summary
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '\u8bc4\u8bba\u5217\u8868\u52a0\u8f7d\u5931\u8d25'
  } finally {
    loading.value = false
  }
}

function handleTabChange(name: string | number) {
  activeTab.value = name as CommentTab
  void loadComments(1)
}

function handleSearch() {
  void loadComments(1)
}

function handleReset() {
  filters.keyword = ''
  filters.user_id = null
  filters.username = ''
  filters.type = 'all'
  filters.status = null
  filters.news_id = null
  filters.post_id = null
  filters.has_parent = null
  filters.date_range = []
  activeTab.value = 'all'
  void loadComments(1)
}

async function openDetail(row: AdminCommentItem) {
  detailVisible.value = true
  detailLoading.value = true
  try {
    currentComment.value = await getAdminCommentDetail(row.comment_type, row.id)
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '\u8bc4\u8bba\u8be6\u60c5\u52a0\u8f7d\u5931\u8d25')
  } finally {
    detailLoading.value = false
  }
}

async function runStatusAction(row: AdminCommentItem, action: AdminReviewAction) {
  const actionLabel: Record<AdminReviewAction, string> = {
    approve: '\u901a\u8fc7',
    reject: '\u9000\u56de',
    fold: '\u6298\u53e0',
    delete: '\u5220\u9664',
    restore: '\u6062\u590d',
  }
  try {
    await ElMessageBox.confirm(`\u786e\u8ba4${actionLabel[action]}\u8be5\u8bc4\u8bba\uff1f`, '\u64cd\u4f5c\u786e\u8ba4', {
      type: action === 'delete' || action === 'reject' ? 'warning' : 'info',
      confirmButtonText: '\u786e\u5b9a',
      cancelButtonText: '\u53d6\u6d88',
    })
  } catch {
    return
  }
  actionLoading.value = true
  try {
    await reviewAdminComment(row.comment_type, row.id, { action, reason: `admin comment ${action}` })
    ElMessage.success('\u5904\u7406\u6210\u529f')
    await loadComments(page.value)
    emit('changed')
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '\u5904\u7406\u5931\u8d25')
  } finally {
    actionLoading.value = false
  }
}

function availableActions(row: AdminCommentItem) {
  if (row.status === 3) return [] as AdminReviewAction[]
  if (row.status === 1) return ['fold', 'delete'] as AdminReviewAction[]
  if (row.status === 2) return ['restore', 'delete'] as AdminReviewAction[]
  if (row.status === 4 || row.status === 0) return ['restore'] as AdminReviewAction[]
  return ['restore'] as AdminReviewAction[]
}

onMounted(async () => {
  await Promise.allSettled([loadOptions(), loadComments(1)])
})
</script>

<template>
  <section class="admin-comment-review">
    <el-card class="comment-panel" shadow="never">
      <template #header>
        <div class="panel-header">
          <div>
            <h2>&#35780;&#35770;&#23457;&#26680;</h2>
            <p>&#32479;&#19968;&#31649;&#29702;&#26032;&#38395;&#35780;&#35770;&#19982;&#31038;&#21306;&#35780;&#35770;&#65292;&#22788;&#29702;&#36829;&#35268;&#35780;&#35770;&#12289;&#25240;&#21472;&#20869;&#23481;&#21644;&#21024;&#38500;&#35760;&#24405;&#12290;</p>
          </div>
          <el-button type="primary" @click="loadComments(1)">&#21047;&#26032;</el-button>
        </div>
      </template>

      <div class="summary-grid">
        <article v-for="card in summaryCards" :key="card.key" class="summary-card">
          <span>{{ card.label }}</span>
          <strong>{{ card.value }}</strong>
        </article>
      </div>

      <el-tabs :model-value="activeTab" class="type-tabs" @tab-change="handleTabChange">
        <el-tab-pane v-for="tab in tabItems" :key="tab.key" :name="tab.key" :label="tab.label" />
      </el-tabs>

      <div class="filter-bar">
        <div class="filter-row-1">
          <el-input v-model="filters.keyword" clearable placeholder="搜索评论内容" class="filter-keyword" />
          <el-input v-model="filters.username" clearable placeholder="评论用户" class="filter-input" />
          <el-select v-model="filters.type" clearable placeholder="评论类型" class="filter-select">
            <el-option label="全部" value="all" />
            <el-option label="新闻评论" value="news" />
            <el-option label="社区评论" value="post" />
          </el-select>
          <el-select v-model="filters.status" clearable placeholder="状态" class="filter-select">
            <el-option v-for="item in options.statuses" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
        </div>
        <div class="filter-row-2">
          <el-input-number v-model="filters.user_id" :min="1" controls-position="right" placeholder="用户 ID" class="filter-small-input" />
          <el-input-number v-model="filters.news_id" :min="1" controls-position="right" placeholder="新闻 ID" class="filter-small-input" />
          <el-input-number v-model="filters.post_id" :min="1" controls-position="right" placeholder="帖子 ID" class="filter-small-input" />
          <el-select v-model="filters.has_parent" clearable placeholder="是否回复" class="filter-select">
            <el-option label="回复评论" :value="true" />
            <el-option label="一级评论" :value="false" />
          </el-select>
        </div>
        <div class="filter-row-3">
          <el-date-picker v-model="filters.date_range" type="datetimerange" value-format="YYYY-MM-DD HH:mm:ss" start-placeholder="开始时间" end-placeholder="结束时间" class="filter-date-range" />
          <div class="filter-actions">
            <el-button type="primary" @click="handleSearch">查询</el-button>
            <el-button @click="handleReset">重置</el-button>
          </div>
        </div>
      </div>

      <el-alert v-if="errorMessage" :title="errorMessage" type="error" show-icon :closable="false" class="error-alert" />

      <el-table v-loading="loading" :data="list" border class="comment-table" empty-text="暂无评论数据">
        <el-table-column prop="content_preview" label="&#35780;&#35770;&#20869;&#23481;" min-width="240" show-overflow-tooltip />
        <el-table-column label="&#22270;&#29255;" width="80">
          <template #default="scope">
            <el-tag v-if="getMediaImages(scope.row.media_json).length" type="success" size="small">含图</el-tag>
            <span v-else class="muted-text">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="author_name" label="&#35780;&#35770;&#29992;&#25143;" width="130" show-overflow-tooltip />
        <el-table-column label="&#35780;&#35770;&#31867;&#22411;" width="120">
          <template #default="scope"><el-tag effect="plain">{{ scope.row.comment_type_label }}</el-tag></template>
        </el-table-column>
        <el-table-column label="&#25152;&#23646;&#23545;&#35937;" min-width="180" show-overflow-tooltip>
          <template #default="scope">{{ scope.row.target_title || scope.row.target_id || '-' }}</template>
        </el-table-column>
        <el-table-column label="&#29238;&#35780;&#35770;" width="110">
          <template #default="scope">{{ scope.row.parent_id ? '\u56de\u590d\u8bc4\u8bba' : '\u4e00\u7ea7\u8bc4\u8bba' }}</template>
        </el-table-column>
        <el-table-column prop="like_count" label="&#28857;&#36190;" width="76" />
        <el-table-column prop="reply_count" label="&#22238;&#22797;" width="76" />
        <el-table-column label="&#29366;&#24577;" width="100">
          <template #default="scope"><el-tag :type="statusTagType(scope.row.status)" effect="plain">{{ scope.row.status_label }}</el-tag></template>
        </el-table-column>
        <el-table-column prop="create_time" label="&#21457;&#24067;&#26102;&#38388;" width="170" />
        <el-table-column label="&#25805;&#20316;" width="250" fixed="right">
          <template #default="scope">
            <el-button size="small" text type="primary" @click="openDetail(scope.row)">&#26597;&#30475;</el-button>
            <el-button v-for="action in availableActions(scope.row)" :key="action" size="small" text :type="action === 'delete' || action === 'reject' ? 'danger' : 'primary'" :loading="actionLoading" @click="runStatusAction(scope.row, action)">
              {{ action === 'approve' ? '\u901a\u8fc7' : action === 'fold' ? '\u6298\u53e0' : action === 'delete' ? '\u5220\u9664' : action === 'restore' ? '\u6062\u590d' : '\u9000\u56de' }}
            </el-button>
            <el-button v-if="scope.row.status === 3" size="small" text disabled>待审核中心处理</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-row">
        <el-pagination v-model:current-page="page" v-model:page-size="pageSize" :total="total" :page-sizes="[10, 20, 50, 100]" layout="total, sizes, prev, pager, next, jumper" @current-change="loadComments" @size-change="() => loadComments(1)" />
      </div>
    </el-card>

    <el-drawer v-model="detailVisible" title="评论详情" size="720px">
      <el-skeleton v-if="detailLoading" animated :rows="8" />
      <div v-else-if="currentComment" class="detail-body">
        <h2>{{ currentComment.content_preview }}</h2>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="评论用户">{{ currentComment.author_name || currentComment.user_id || '-' }}</el-descriptions-item>
          <el-descriptions-item label="用户 ID">{{ currentComment.user_id || '-' }}</el-descriptions-item>
          <el-descriptions-item label="评论类型">{{ currentComment.comment_type_label }}</el-descriptions-item>
          <el-descriptions-item label="所属对象">{{ currentComment.target_title || currentComment.target_id || '-' }}</el-descriptions-item>
          <el-descriptions-item label="父评论">{{ currentComment.parent_content || '一级评论' }}</el-descriptions-item>
          <el-descriptions-item label="点赞/回复">{{ currentComment.like_count }} / {{ currentComment.reply_count }}</el-descriptions-item>
          <el-descriptions-item label="状态">{{ currentComment.status_label }}</el-descriptions-item>
          <el-descriptions-item label="发布时间">{{ currentComment.create_time || '-' }}</el-descriptions-item>
          <el-descriptions-item label="更新时间">{{ currentComment.update_time || '-' }}</el-descriptions-item>
        </el-descriptions>
        <section><h3>评论内容</h3><div class="content-text">{{ currentComment.content || '暂无内容' }}</div></section>
        <section v-if="getMediaImages(currentComment.media_json).length">
          <h3>评论图片</h3>
          <div class="image-grid">
            <el-image
              v-for="(image, index) in getMediaImages(currentComment.media_json)"
              :key="`comment-image-${index}`"
              :src="normalizeMediaImageUrl(image)"
              :preview-src-list="getMediaImages(currentComment.media_json).map(normalizeMediaImageUrl)"
              fit="cover"
              class="image-thumb"
            />
          </div>
        </section>
        <section>


          <h3>上下文</h3>
          <el-alert v-if="currentComment.context?.missing" type="warning" :closable="false" title="所属内容不存在或已删除" />
          <el-descriptions v-else :column="1" border>
            <el-descriptions-item label="标题">{{ currentComment.context.target_title || '-' }}</el-descriptions-item>
            <el-descriptions-item label="来源">{{ currentComment.context.target_source || '-' }}</el-descriptions-item>
            <el-descriptions-item label="发布时间">{{ currentComment.context.target_publish_time || '-' }}</el-descriptions-item>
            <el-descriptions-item label="摘要">{{ currentComment.context.target_summary || '-' }}</el-descriptions-item>
          </el-descriptions>
        </section>
        <section>
          <h3>子回复</h3>
          <div v-if="currentComment.replies.length" class="reply-list">
            <article v-for="reply in currentComment.replies" :key="reply.id" class="reply-item">
              <strong>{{ reply.username || reply.user_id || '匿名用户' }}</strong>
              <span>{{ reply.create_time || '-' }} · {{ reply.status_label }} · {{ reply.like_count }} 赞</span>
              <p>{{ reply.content }}</p>
              <div v-if="getMediaImages(reply.media_json).length" class="reply-images">
                <el-image
                  v-for="(image, index) in getMediaImages(reply.media_json)"
                  :key="`reply-${reply.id}-image-${index}`"
                  :src="normalizeMediaImageUrl(image)"
                  :preview-src-list="getMediaImages(reply.media_json).map(normalizeMediaImageUrl)"
                  fit="cover"
                  class="reply-image-thumb"
                />
              </div>
            </article>
          </div>
          <el-empty v-else description="暂无子回复" />
        </section>
      </div>
    </el-drawer>
  </section>
</template>

<style scoped>
.admin-comment-review { width: 100%; }
.comment-panel { border-radius: 16px; }
.panel-header { display: flex; justify-content: space-between; gap: 16px; align-items: flex-start; }
.panel-header h2 { margin: 0 0 6px; }
.panel-header p { margin: 0; color: var(--color-text-secondary); }
.summary-grid { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 12px; margin-bottom: 16px; }
.summary-card { padding: 14px; border: 1px solid var(--color-border-light); border-radius: 12px; background: var(--color-bg-page); }
.summary-card span { display: block; color: var(--color-text-secondary); font-size: 13px; }
.summary-card strong { display: block; margin-top: 6px; font-size: 22px; color: var(--color-text-primary); }
.info-alert, .error-alert { margin-bottom: 16px; }
.type-tabs { margin-bottom: 10px; }
.filter-bar {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 16px;
}
.filter-row-1, .filter-row-2, .filter-row-3 {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
}
.filter-keyword { width: 320px; }
.filter-input { width: 200px; }
.filter-small-input { width: 150px; }
.filter-select { width: 200px; }
.filter-date-range { width: 400px; }
.filter-actions {
  display: flex;
  gap: 8px;
}
.filter-actions .el-button:first-child {
  background: var(--el-color-primary);
  border-color: var(--el-color-primary);
  color: #fff;
}
.comment-table { width: 100%; }
.pagination-row { display: flex; justify-content: flex-end; margin-top: 16px; }
.detail-body { display: flex; flex-direction: column; gap: 18px; }
.detail-body h2 { margin: 0; line-height: 1.5; }
.content-text { white-space: pre-wrap; line-height: 1.8; max-height: 260px; overflow: auto; padding: 12px; background: var(--color-bg-page); border-radius: 10px; }
.reply-list { display: flex; flex-direction: column; gap: 10px; }
.reply-item { padding: 12px; border: 1px solid var(--color-border-light); border-radius: 12px; background: var(--color-bg-page); }
.reply-item strong { display: block; color: var(--color-text-primary); }
.reply-item span { display: block; margin-top: 4px; color: var(--color-text-secondary); font-size: 12px; }
.reply-item p { margin: 8px 0 0; line-height: 1.6; }
.image-grid { display: flex; flex-wrap: wrap; gap: 10px; }
.image-thumb { width: 120px; height: 120px; border-radius: 10px; overflow: hidden; border: 1px solid var(--color-border-light); background: var(--color-bg-page); }
.reply-images { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 10px; }
.reply-image-thumb { width: 96px; height: 96px; border-radius: 8px; overflow: hidden; border: 1px solid var(--color-border-light); background: var(--color-bg-page); }
.muted-text { color: var(--color-text-secondary); }
@media (max-width: 1200px) { .summary-grid { grid-template-columns: repeat(2, 1fr); } .filter-bar { grid-template-columns: 1fr; } }
</style>
