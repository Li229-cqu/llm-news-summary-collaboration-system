<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getAdminPostDetail,
  getAdminPostList,
  getAdminPostOptions,
  reviewAdminPost,
  type AdminPostDetail,
  type AdminPostItem,
  type AdminPostListResponse,
  type AdminPostOptions,
  type AdminReviewAction,
} from '@/api/admin'

const emit = defineEmits<{ changed: [] }>()

const loading = ref(false)
const actionLoading = ref(false)
const detailLoading = ref(false)
const errorMessage = ref('')
const list = ref<AdminPostItem[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const summary = ref<AdminPostListResponse['summary'] | null>(null)
const options = ref<AdminPostOptions>({ statuses: [], tags: [], feature_supported: false })
const detailVisible = ref(false)
const currentPost = ref<AdminPostDetail | null>(null)

const filters = reactive({
  keyword: '',
  user_id: null as number | null,
  username: '',
  status: null as number | null,
  tag: '',
  related_news_id: null as number | null,
  date_range: [] as string[],
})

const summaryCards = computed(() => [
  { key: 'total', label: '\u5168\u90e8\u5e16\u5b50', value: summary.value?.total_count ?? 0 },
  { key: 'pending', label: '\u5f85\u5ba1\u6838', value: summary.value?.pending_count ?? 0 },
  { key: 'normal', label: '\u6b63\u5e38\u5e16\u5b50', value: summary.value?.normal_count ?? 0 },
  { key: 'folded', label: '\u5df2\u6298\u53e0', value: summary.value?.folded_count ?? 0 },
  { key: 'deleted', label: '\u5df2\u5220\u9664', value: summary.value?.deleted_count ?? 0 },
])

function statusTagType(status: number) {
  if (status === 1) return 'success'
  if (status === 3) return 'warning'
  if (status === 2) return 'info'
  if (status === 0 || status === 4) return 'danger'
  return 'info'
}

async function loadOptions() {
  options.value = await getAdminPostOptions()
}

async function loadPosts(targetPage = page.value) {
  loading.value = true
  errorMessage.value = ''
  try {
    page.value = targetPage
    const [start, end] = filters.date_range || []
    const result = await getAdminPostList({
      keyword: filters.keyword,
      user_id: filters.user_id,
      username: filters.username,
      status: filters.status,
      tag: filters.tag,
      related_news_id: filters.related_news_id,
      start_time: start,
      end_time: end,
      page: page.value,
      page_size: pageSize.value,
    })
    list.value = result.items
    total.value = result.total
    summary.value = result.summary
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '\u793e\u533a\u5e16\u5b50\u5217\u8868\u52a0\u8f7d\u5931\u8d25'
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  void loadPosts(1)
}

function handleReset() {
  filters.keyword = ''
  filters.user_id = null
  filters.username = ''
  filters.status = null
  filters.tag = ''
  filters.related_news_id = null
  filters.date_range = []
  void loadPosts(1)
}

async function openDetail(row: AdminPostItem) {
  detailVisible.value = true
  detailLoading.value = true
  try {
    currentPost.value = await getAdminPostDetail(row.id)
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '\u5e16\u5b50\u8be6\u60c5\u52a0\u8f7d\u5931\u8d25')
  } finally {
    detailLoading.value = false
  }
}

async function runStatusAction(row: AdminPostItem, action: AdminReviewAction) {
  const actionLabel: Record<AdminReviewAction, string> = {
    approve: '\u901a\u8fc7',
    reject: '\u9000\u56de',
    fold: '\u6298\u53e0',
    delete: '\u5220\u9664',
    restore: '\u6062\u590d',
  }
  try {
    await ElMessageBox.confirm(`\u786e\u8ba4${actionLabel[action]}\u8be5\u5e16\u5b50\uff1f`, '\u64cd\u4f5c\u786e\u8ba4', {
      type: action === 'delete' || action === 'reject' ? 'warning' : 'info',
      confirmButtonText: '\u786e\u5b9a',
      cancelButtonText: '\u53d6\u6d88',
    })
  } catch {
    return
  }
  actionLoading.value = true
  try {
    await reviewAdminPost(row.id, { action, reason: `admin post ${action}` })
    ElMessage.success('\u5904\u7406\u6210\u529f')
    await loadPosts(page.value)
    emit('changed')
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '\u5904\u7406\u5931\u8d25')
  } finally {
    actionLoading.value = false
  }
}

function availableActions(row: AdminPostItem) {
  if (row.status === 3) return ['approve', 'fold', 'delete'] as AdminReviewAction[]
  if (row.status === 1) return ['fold', 'delete'] as AdminReviewAction[]
  if (row.status === 2) return ['restore', 'delete'] as AdminReviewAction[]
  if (row.status === 4 || row.status === 0) return ['restore'] as AdminReviewAction[]
  return ['restore'] as AdminReviewAction[]
}

onMounted(async () => {
  try {
    await loadOptions()
  } finally {
    await loadPosts(1)
  }
})
</script>

<template>
  <section class="admin-post-management">
    <el-card class="post-panel" shadow="never">
      <template #header>
        <div class="panel-header">
          <div>
            <h2>&#31038;&#21306;&#24086;&#23376;&#31649;&#29702;</h2>
            <p>&#31649;&#29702;&#31038;&#21306;&#24086;&#23376;&#29366;&#24577;&#12289;&#25240;&#21472;&#24674;&#22797;&#19982;&#36829;&#35268;&#20869;&#23481;&#22788;&#29702;&#12290;</p>
          </div>
          <el-button type="primary" @click="loadPosts(1)">&#21047;&#26032;</el-button>
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
          <el-input v-model="filters.keyword" clearable placeholder="&#25628;&#32034;&#26631;&#39064;&#12289;&#27491;&#25991;&#25110;&#26631;&#31614;" class="filter-keyword" />
          <el-input v-model="filters.username" clearable placeholder="&#21457;&#24086;&#29992;&#25143;" class="filter-input" />
          <el-select v-model="filters.status" clearable placeholder="&#29366;&#24577;" class="filter-select">
            <el-option v-for="item in options.statuses" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
          <el-select v-model="filters.tag" clearable filterable allow-create placeholder="&#26631;&#31614;" class="filter-select">
            <el-option v-for="item in options.tags" :key="item" :label="item" :value="item" />
          </el-select>
        </div>
        <div class="filter-row-2">
          <el-input v-model="filters.related_news_id" clearable placeholder="&#20851;&#32852;&#26032;&#38395;" class="filter-input" />
          <el-date-picker
            v-model="filters.date_range"
            type="datetimerange"
            value-format="YYYY-MM-DD HH:mm:ss"
            start-placeholder="&#24320;&#22987;&#26102;&#38388;"
            end-placeholder="&#32467;&#26463;&#26102;&#38388;"
            class="filter-date-range"
          />
          <div class="filter-actions">
            <el-button type="primary" @click="handleSearch">&#26597;&#35810;</el-button>
            <el-button @click="handleReset">&#37325;&#32622;</el-button>
          </div>
        </div>
      </div>

      <el-alert v-if="errorMessage" :title="errorMessage" type="error" show-icon :closable="false" class="error-alert" />

      <el-table v-loading="loading" :data="list" border class="post-table" empty-text="暂无社区帖子数据">
        <el-table-column prop="title" label="&#24086;&#23376;&#26631;&#39064;" min-width="220" show-overflow-tooltip />
        <el-table-column prop="author_name" label="&#21457;&#24086;&#29992;&#25143;" width="130" show-overflow-tooltip />
        <el-table-column label="&#26631;&#31614;" min-width="160" show-overflow-tooltip>
          <template #default="scope">
            <el-tag v-for="tag in scope.row.tags.slice(0, 3)" :key="tag" size="small" effect="plain" class="tag-item">{{ tag }}</el-tag>
            <span v-if="!scope.row.tags.length">-</span>
          </template>
        </el-table-column>
        <el-table-column label="&#20851;&#32852;&#26032;&#38395;" min-width="150" show-overflow-tooltip>
          <template #default="scope">{{ scope.row.related_news_title || scope.row.related_news_id || '-' }}</template>
        </el-table-column>
        <el-table-column prop="like_count" label="&#28857;&#36190;" width="76" />
        <el-table-column prop="comment_count" label="&#35780;&#35770;" width="76" />
        <el-table-column prop="favorite_count" label="&#25910;&#34255;" width="76" />
        <el-table-column prop="heat_score" label="&#28909;&#24230;" width="76" />
        <el-table-column label="&#29366;&#24577;" width="100">
          <template #default="scope">
            <el-tag :type="statusTagType(scope.row.status)" effect="plain">{{ scope.row.status_label }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="create_time" label="&#21457;&#24067;&#26102;&#38388;" width="170" />
        <el-table-column label="&#25805;&#20316;" width="310" fixed="right">
          <template #default="scope">
            <el-button size="small" text type="primary" @click="openDetail(scope.row)">&#26597;&#30475;</el-button>
            <el-button
              v-for="action in availableActions(scope.row)"
              :key="action"
              size="small"
              text
              :type="action === 'delete' || action === 'reject' ? 'danger' : 'primary'"
              :loading="actionLoading"
              @click="runStatusAction(scope.row, action)"
            >
              {{ action === 'approve' ? '\u901a\u8fc7' : action === 'fold' ? '\u6298\u53e0' : action === 'delete' ? '\u5220\u9664' : action === 'restore' ? '\u6062\u590d' : '\u9000\u56de' }}
            </el-button>
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
          @current-change="loadPosts"
          @size-change="() => loadPosts(1)"
        />
      </div>
    </el-card>

    <el-drawer v-model="detailVisible" title="社区帖子详情" size="720px">
      <el-skeleton v-if="detailLoading" animated :rows="8" />
      <div v-else-if="currentPost" class="detail-body">
        <h2>{{ currentPost.title }}</h2>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="发布用户">{{ currentPost.author_name || currentPost.user_id || '-' }}</el-descriptions-item>
          <el-descriptions-item label="用户 ID">{{ currentPost.user_id || '-' }}</el-descriptions-item>
          <el-descriptions-item label="关联新闻">{{ currentPost.related_news_title || currentPost.related_news_id || '-' }}</el-descriptions-item>
          <el-descriptions-item label="话题">{{ currentPost.topic_name || currentPost.topic_id || '-' }}</el-descriptions-item>
          <el-descriptions-item label="状态">{{ currentPost.status_label }}</el-descriptions-item>
          <el-descriptions-item label="热度">{{ currentPost.heat_score }}</el-descriptions-item>
          <el-descriptions-item label="点赞/评论/收藏">{{ currentPost.like_count }} / {{ currentPost.comment_count }} / {{ currentPost.favorite_count }}</el-descriptions-item>
          <el-descriptions-item label="发布时间">{{ currentPost.create_time || '-' }}</el-descriptions-item>
          <el-descriptions-item label="更新时间">{{ currentPost.update_time || '-' }}</el-descriptions-item>
        </el-descriptions>
        <section>
          <h3>帖子正文</h3>
          <div class="content-text">{{ currentPost.content || '暂无正文' }}</div>
        </section>
        <section>
          <h3>标签</h3>
          <el-tag v-for="tag in currentPost.tags" :key="tag" effect="plain" class="tag-item">{{ tag }}</el-tag>
          <span v-if="!currentPost.tags.length">暂无标签</span>
        </section>
        <section>
          <h3>最近评论</h3>
          <div v-if="currentPost.recent_comments.length" class="comment-list">
            <article v-for="comment in currentPost.recent_comments" :key="comment.id" class="comment-item">
              <strong>{{ comment.username || comment.user_id || '用户' }}</strong>
              <span>{{ comment.create_time || '-' }} · {{ comment.status_label }} · {{ comment.like_count }} 赞</span>
              <p>{{ comment.content }}</p>
            </article>
          </div>
          <el-empty v-else description="暂无最近评论" />
        </section>
      </div>
    </el-drawer>
  </section>
</template>

<style scoped>
.admin-post-management { width: 100%; }
.post-panel { border-radius: 16px; }
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
.filter-input { width: 200px; }
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
.post-table { width: 100%; }
.tag-item { margin: 0 4px 4px 0; }
.pagination-row { display: flex; justify-content: flex-end; margin-top: 16px; }
.detail-body { display: flex; flex-direction: column; gap: 18px; }
.detail-body h2 { margin: 0; line-height: 1.4; }
.content-text { white-space: pre-wrap; line-height: 1.8; max-height: 360px; overflow: auto; padding: 12px; background: var(--color-bg-page); border-radius: 10px; }
.comment-list { display: flex; flex-direction: column; gap: 10px; }
.comment-item { padding: 12px; border: 1px solid var(--color-border-light); border-radius: 12px; background: var(--color-bg-page); }
.comment-item strong { display: block; color: var(--color-text-primary); }
.comment-item span { display: block; margin-top: 4px; color: var(--color-text-secondary); font-size: 12px; }
.comment-item p { margin: 8px 0 0; line-height: 1.6; }
@media (max-width: 1200px) { .summary-grid { grid-template-columns: repeat(2, 1fr); } .filter-bar { grid-template-columns: 1fr; } }
</style>
