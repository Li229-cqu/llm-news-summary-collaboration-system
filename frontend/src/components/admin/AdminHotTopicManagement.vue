<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  bindAdminTopicNews,
  createAdminTopic,
  getAdminHotTopicDetail,
  getAdminHotTopicList,
  getAdminHotTopicOptions,
  getAdminTopicCandidateNews,
  getAdminTopicDetail,
  getAdminTopicList,
  getAdminTopicOptions,
  getAdminTopicNews,
  hideAdminHotTopic,
  pinAdminHotTopic,
  refreshAdminHotTopicHeat,
  restoreAdminHotTopic,
  type AdminHotTopicDetail,
  type AdminHotTopicItem,
  type AdminHotTopicListResponse,
  type AdminHotTopicOptions,
  type AdminTopicDetail,
  type AdminTopicItem,
  type AdminTopicListResponse,
  type AdminTopicNewsItem,
  type AdminTopicOptions,
  type AdminTopicPayload,
  unbindAdminTopicNews,
  unpinAdminHotTopic,
  updateAdminHotTopicRank,
  updateAdminTopic,
  updateAdminTopicStatus,
} from '@/api/admin'

const emit = defineEmits<{ changed: [] }>()
const activeTab = ref<'hot' | 'topic'>('hot')
const loadingHot = ref(false)
const loadingTopic = ref(false)
const hotOptions = ref<AdminHotTopicOptions | null>(null)
const topicOptions = ref<AdminTopicOptions | null>(null)
const hotData = ref<AdminHotTopicListResponse | null>(null)
const topicData = ref<AdminTopicListResponse | null>(null)
const hotDetail = ref<AdminHotTopicDetail | null>(null)
const topicDetail = ref<AdminTopicDetail | null>(null)
const detailVisible = ref(false)
const topicDetailVisible = ref(false)
const rankDialogVisible = ref(false)
const topicDialogVisible = ref(false)
const topicNewsVisible = ref(false)
const bindNewsVisible = ref(false)
const currentHot = ref<AdminHotTopicItem | null>(null)
const currentTopic = ref<AdminTopicItem | null>(null)
const topicNews = ref<AdminTopicNewsItem[]>([])
const candidateNews = ref<AdminTopicNewsItem[]>([])
const selectedNewsIds = ref<number[]>([])
const rankForm = reactive({ rank_no: 1 })
const topicForm = reactive<AdminTopicPayload>({ topic_name: '', summary: '', keyword_list: [], heat_score: 0, status: 1 })
const topicKeywordInput = ref('')
const bindKeyword = ref('')

const hotQuery = reactive({ keyword: '', hot_type: '', target_type: '', status: null as number | null, is_hidden: null as boolean | null, page: 1, page_size: 10 })
const topicQuery = reactive({ keyword: '', status: null as number | null, has_news: null as boolean | null, page: 1, page_size: 10 })

const hotSummaryCards = computed(() => [
  { key: 'total', label: 'All hot items', value: hotData.value?.summary.total_count ?? 0 },
  { key: 'news', label: 'News hot', value: hotData.value?.summary.news_hot_count ?? 0 },
  { key: 'post', label: 'Community hot', value: hotData.value?.summary.community_hot_count ?? 0 },
  { key: 'topic', label: 'Topic hot', value: hotData.value?.summary.topic_hot_count ?? 0 },
  { key: 'hidden', label: 'Hidden', value: hotData.value?.summary.hidden_count ?? 0 },
])
const topicSummaryCards = computed(() => [
  { key: 'total', label: 'All topics', value: topicData.value?.summary.total_count ?? 0 },
  { key: 'enabled', label: 'Enabled', value: topicData.value?.summary.enabled_count ?? 0 },
  { key: 'disabled', label: 'Disabled', value: topicData.value?.summary.disabled_count ?? 0 },
  { key: 'with', label: 'With news', value: topicData.value?.summary.with_news_count ?? 0 },
  { key: 'without', label: 'Without news', value: topicData.value?.summary.without_news_count ?? 0 },
])

async function loadHotOptions() { hotOptions.value = await getAdminHotTopicOptions() }
async function loadTopicOptions() { topicOptions.value = await getAdminTopicOptions() }
async function loadHotList() {
  loadingHot.value = true
  try { hotData.value = await getAdminHotTopicList({ ...hotQuery }) } catch (error) { ElMessage.error(error instanceof Error ? error.message : 'Failed to load hot topics') } finally { loadingHot.value = false }
}
async function loadTopicList() {
  loadingTopic.value = true
  try { topicData.value = await getAdminTopicList({ ...topicQuery }) } catch (error) { ElMessage.error(error instanceof Error ? error.message : 'Failed to load topics') } finally { loadingTopic.value = false }
}
function resetHotQuery() { Object.assign(hotQuery, { keyword: '', hot_type: '', target_type: '', status: null, is_hidden: null, page: 1 }); void loadHotList() }
function resetTopicQuery() { Object.assign(topicQuery, { keyword: '', status: null, has_news: null, page: 1 }); void loadTopicList() }
async function openHotDetail(row: AdminHotTopicItem) { hotDetail.value = await getAdminHotTopicDetail(row.id); detailVisible.value = true }
function openRankDialog(row: AdminHotTopicItem) { currentHot.value = row; rankForm.rank_no = Math.max(row.rank_no || 1, 1); rankDialogVisible.value = true }
async function submitRank() {
  if (!currentHot.value) return
  await updateAdminHotTopicRank(currentHot.value.id, rankForm.rank_no)
  ElMessage.success('Rank updated')
  rankDialogVisible.value = false
  await loadHotList()
  emit('changed')
}
async function confirmHotAction(row: AdminHotTopicItem, action: 'hide' | 'restore' | 'pin' | 'unpin' | 'refresh') {
  const actionLabel = { hide: 'hide', restore: 'restore', pin: 'pin', unpin: 'unpin', refresh: 'refresh heat' }[action]
  await ElMessageBox.confirm(`Confirm to ${actionLabel} this item?`, 'Confirm', { type: 'warning' })
  if (action === 'hide') await hideAdminHotTopic(row.id)
  if (action === 'restore') await restoreAdminHotTopic(row.id)
  if (action === 'pin') await pinAdminHotTopic(row.id)
  if (action === 'unpin') await unpinAdminHotTopic(row.id)
  if (action === 'refresh') await refreshAdminHotTopicHeat(row.id)
  ElMessage.success('Action completed')
  await loadHotList()
  emit('changed')
}
function openTopicDialog(row?: AdminTopicItem) {
  currentTopic.value = row ?? null
  topicForm.topic_name = row?.topic_name ?? ''
  topicForm.summary = row?.summary ?? ''
  topicForm.keyword_list = [...(row?.keyword_list ?? [])]
  topicForm.heat_score = row?.heat_score ?? 0
  topicForm.status = row?.status ?? 1
  topicKeywordInput.value = Array.isArray(topicForm.keyword_list) ? topicForm.keyword_list.join(',') : String(topicForm.keyword_list || '')
  topicDialogVisible.value = true
}
async function submitTopic() {
  const payload: AdminTopicPayload = { topic_name: topicForm.topic_name.trim(), summary: topicForm.summary, keyword_list: topicKeywordInput.value, heat_score: topicForm.heat_score ?? 0, status: topicForm.status }
  if (!payload.topic_name) { ElMessage.warning('Topic name is required'); return }
  if (currentTopic.value) await updateAdminTopic(currentTopic.value.id, payload)
  else await createAdminTopic(payload)
  ElMessage.success('Saved')
  topicDialogVisible.value = false
  await loadTopicList()
  emit('changed')
}
async function confirmTopicStatus(row: AdminTopicItem) {
  const nextStatus = row.status === 1 ? 0 : 1
  await ElMessageBox.confirm(`Confirm to ${nextStatus === 1 ? 'enable' : 'disable'} this topic?`, 'Confirm', { type: 'warning' })
  await updateAdminTopicStatus(row.id, nextStatus)
  ElMessage.success('Status updated')
  await loadTopicList()
  emit('changed')
}
async function openTopicDetail(row: AdminTopicItem) { topicDetail.value = await getAdminTopicDetail(row.id); topicDetailVisible.value = true }
async function openTopicNews(row: AdminTopicItem) { currentTopic.value = row; const data = await getAdminTopicNews(row.id, { page_size: 20 }); topicNews.value = data.items; topicNewsVisible.value = true }
async function openBindNews(row: AdminTopicItem) { currentTopic.value = row; bindKeyword.value = ''; selectedNewsIds.value = []; await loadCandidateNews(); bindNewsVisible.value = true }
async function loadCandidateNews() { if (!currentTopic.value) return; const data = await getAdminTopicCandidateNews(currentTopic.value.id, { keyword: bindKeyword.value, page_size: 20 }); candidateNews.value = data.items }
function handleSelectionChange(rows: AdminTopicNewsItem[]) { selectedNewsIds.value = rows.map((item) => item.id) }
async function submitBindNews() {
  if (!currentTopic.value) return
  if (!selectedNewsIds.value.length) { ElMessage.warning('Please select news'); return }
  await bindAdminTopicNews(currentTopic.value.id, selectedNewsIds.value)
  ElMessage.success('News bound')
  bindNewsVisible.value = false
  await loadTopicList()
  emit('changed')
}
async function unbindNews(row: AdminTopicNewsItem) {
  if (!currentTopic.value) return
  await ElMessageBox.confirm('Confirm to remove this news from the topic?', 'Confirm', { type: 'warning' })
  await unbindAdminTopicNews(currentTopic.value.id, [row.id])
  ElMessage.success('News removed')
  await openTopicNews(currentTopic.value)
  await loadTopicList()
  emit('changed')
}
function openNews(row: AdminTopicNewsItem) { window.open(`/news/${row.id}`, '_blank') }
onMounted(async () => { await Promise.all([loadHotOptions(), loadTopicOptions()]); await loadHotList() })
</script>

<template>
  <section class="admin-hot-topic-management">
    <el-card shadow="never" class="module-card">
      <div class="panel-header"><div><h3>Hot Search and Topic Management</h3><p>Manage homepage hot list, community hot search, topics, keywords, and news-topic binding.</p></div><el-button type="primary" @click="activeTab === 'hot' ? loadHotList() : loadTopicList()">Refresh</el-button></div>
      <el-tabs v-model="activeTab" @tab-change="activeTab === 'topic' && !topicData && loadTopicList()">
        <el-tab-pane label="Hot search" name="hot">
          <div class="summary-grid"><article v-for="card in hotSummaryCards" :key="card.key" class="summary-card"><span>{{ card.label }}</span><strong>{{ card.value }}</strong></article></div>
          <el-alert v-if="hotOptions && !hotOptions.support.pin_supported" title="The current hot_topic table has no pin field. Pin buttons are disabled." type="info" show-icon :closable="false" />
          <el-alert v-if="hotOptions?.support.hide_uses_status" title="Hide uses hot_topic.status=0; restore uses status=1." type="info" show-icon :closable="false" />
          <div class="filter-row">
            <el-input v-model="hotQuery.keyword" placeholder="Title or tag" clearable />
            <el-select v-model="hotQuery.hot_type" placeholder="Hot type" clearable><el-option label="News hot" value="news_hot" /><el-option label="Community hot" value="community_hot" /><el-option label="Topic hot" value="topic_hot" /></el-select>
            <el-select v-model="hotQuery.target_type" placeholder="Target type" clearable><el-option v-for="item in hotOptions?.target_types || []" :key="item.value" :label="item.label" :value="item.value" /></el-select>
            <el-select v-model="hotQuery.status" placeholder="Status" clearable><el-option v-for="item in hotOptions?.statuses || []" :key="item.value" :label="item.label" :value="item.value" /></el-select>
            <el-select v-model="hotQuery.is_hidden" placeholder="Hidden" clearable><el-option label="Hidden" :value="true" /><el-option label="Visible" :value="false" /></el-select>
            <el-button type="primary" @click="hotQuery.page = 1; loadHotList()">Search</el-button><el-button @click="resetHotQuery">Reset</el-button>
          </div>
          <el-table v-loading="loadingHot" :data="hotData?.items || []" border>
            <el-table-column prop="rank_no" label="Rank" width="80" /><el-table-column prop="title" label="Title" min-width="220" show-overflow-tooltip /><el-table-column prop="hot_type" label="Hot type" width="130" /><el-table-column prop="target_type" label="Target" width="100" /><el-table-column prop="target_id" label="Target ID" width="90" /><el-table-column prop="tag" label="Tag" width="100" /><el-table-column prop="heat_score" label="Heat" width="100" />
            <el-table-column label="Status" width="100"><template #default="scope"><el-tag :type="scope.row.status === 1 ? 'success' : 'info'" size="small">{{ scope.row.status_label }}</el-tag></template></el-table-column>
            <el-table-column prop="updated_at" label="Updated" width="170" />
            <el-table-column label="Actions" width="360" fixed="right"><template #default="scope"><el-button size="small" text type="primary" @click="openHotDetail(scope.row)">Detail</el-button><el-button size="small" text type="primary" :disabled="!hotData?.support.manual_rank_supported" @click="openRankDialog(scope.row)">Rank</el-button><el-button size="small" text type="warning" :disabled="!hotData?.support.pin_supported" @click="confirmHotAction(scope.row, scope.row.is_pinned ? 'unpin' : 'pin')">{{ scope.row.is_pinned ? 'Unpin' : 'Pin' }}</el-button><el-button size="small" text :type="scope.row.is_hidden ? 'success' : 'danger'" @click="confirmHotAction(scope.row, scope.row.is_hidden ? 'restore' : 'hide')">{{ scope.row.is_hidden ? 'Restore' : 'Hide' }}</el-button><el-button size="small" text @click="confirmHotAction(scope.row, 'refresh')">Refresh heat</el-button></template></el-table-column>
          </el-table>
          <el-pagination class="pager" layout="total, prev, pager, next, sizes" :total="hotData?.total || 0" v-model:current-page="hotQuery.page" v-model:page-size="hotQuery.page_size" @current-change="loadHotList" @size-change="loadHotList" />
        </el-tab-pane>
        <el-tab-pane label="Topics" name="topic">
          <div class="summary-grid"><article v-for="card in topicSummaryCards" :key="card.key" class="summary-card"><span>{{ card.label }}</span><strong>{{ card.value }}</strong></article></div>
          <div class="filter-row"><el-input v-model="topicQuery.keyword" placeholder="Topic, summary, or keyword" clearable /><el-select v-model="topicQuery.status" placeholder="Status" clearable><el-option v-for="item in topicOptions?.status_options || []" :key="item.value" :label="item.label" :value="item.value" /></el-select><el-select v-model="topicQuery.has_news" placeholder="Has news" clearable><el-option label="With news" :value="true" /><el-option label="Without news" :value="false" /></el-select><el-button type="primary" @click="topicQuery.page = 1; loadTopicList()">Search</el-button><el-button @click="resetTopicQuery">Reset</el-button><el-button type="success" @click="openTopicDialog()">New topic</el-button></div>
          <el-table v-loading="loadingTopic" :data="topicData?.items || []" border>
            <el-table-column prop="topic_name" label="Topic" min-width="180" show-overflow-tooltip /><el-table-column label="Keywords" min-width="220"><template #default="scope"><el-tag v-for="tag in scope.row.keyword_list" :key="tag" size="small" effect="plain" class="tag-item">{{ tag }}</el-tag></template></el-table-column><el-table-column prop="summary" label="Summary" min-width="240" show-overflow-tooltip /><el-table-column prop="news_count" label="News" width="90" /><el-table-column prop="heat_score" label="Heat" width="90" /><el-table-column label="Status" width="100"><template #default="scope"><el-tag :type="scope.row.status === 1 ? 'success' : 'info'" size="small">{{ scope.row.status_label }}</el-tag></template></el-table-column><el-table-column prop="created_at" label="Created" width="170" />
            <el-table-column label="Actions" width="360" fixed="right"><template #default="scope"><el-button size="small" text type="primary" @click="openTopicDetail(scope.row)">Detail</el-button><el-button size="small" text type="primary" @click="openTopicNews(scope.row)">News</el-button><el-button size="small" text @click="openTopicDialog(scope.row)">Edit</el-button><el-button size="small" text :type="scope.row.status === 1 ? 'warning' : 'success'" @click="confirmTopicStatus(scope.row)">{{ scope.row.status === 1 ? 'Disable' : 'Enable' }}</el-button><el-button size="small" text type="success" @click="openBindNews(scope.row)">Bind news</el-button></template></el-table-column>
          </el-table>
          <el-pagination class="pager" layout="total, prev, pager, next, sizes" :total="topicData?.total || 0" v-model:current-page="topicQuery.page" v-model:page-size="topicQuery.page_size" @current-change="loadTopicList" @size-change="loadTopicList" />
        </el-tab-pane>
      </el-tabs>
    </el-card>
    <el-drawer v-model="detailVisible" title="Hot detail" size="520px"><el-descriptions v-if="hotDetail" :column="1" border><el-descriptions-item label="Title">{{ hotDetail.title }}</el-descriptions-item><el-descriptions-item label="Target type">{{ hotDetail.target_type }}</el-descriptions-item><el-descriptions-item label="Target content">{{ hotDetail.target_title || 'Missing target' }}</el-descriptions-item><el-descriptions-item label="Heat">{{ hotDetail.heat_score }}</el-descriptions-item><el-descriptions-item label="Status">{{ hotDetail.status_label }}</el-descriptions-item></el-descriptions></el-drawer>
    <el-dialog v-model="rankDialogVisible" title="Update rank" width="420px"><el-form label-width="90px"><el-form-item label="Rank"><el-input-number v-model="rankForm.rank_no" :min="1" /></el-form-item></el-form><template #footer><el-button @click="rankDialogVisible = false">Cancel</el-button><el-button type="primary" @click="submitRank">Save</el-button></template></el-dialog>
    <el-dialog v-model="topicDialogVisible" :title="currentTopic ? 'Edit topic' : 'New topic'" width="620px"><el-form label-width="100px"><el-form-item label="Topic"><el-input v-model="topicForm.topic_name" /></el-form-item><el-form-item label="Summary"><el-input v-model="topicForm.summary" type="textarea" :rows="3" /></el-form-item><el-form-item label="Keywords"><el-input v-model="topicKeywordInput" placeholder="Comma-separated keywords" /></el-form-item><el-form-item label="Heat"><el-input-number v-model="topicForm.heat_score" :min="0" /></el-form-item><el-form-item label="Status"><el-switch v-model="topicForm.status" :active-value="1" :inactive-value="0" active-text="Enabled" inactive-text="Disabled" /></el-form-item></el-form><template #footer><el-button @click="topicDialogVisible = false">Cancel</el-button><el-button type="primary" @click="submitTopic">Save</el-button></template></el-dialog>
    <el-drawer v-model="topicDetailVisible" title="Topic detail" size="560px"><el-descriptions v-if="topicDetail" :column="1" border><el-descriptions-item label="Topic">{{ topicDetail.topic_name }}</el-descriptions-item><el-descriptions-item label="Summary">{{ topicDetail.summary }}</el-descriptions-item><el-descriptions-item label="Keywords">{{ topicDetail.keyword_list.join(', ') }}</el-descriptions-item><el-descriptions-item label="News count">{{ topicDetail.news_count }}</el-descriptions-item><el-descriptions-item label="Status">{{ topicDetail.status_label }}</el-descriptions-item></el-descriptions></el-drawer>
    <el-drawer v-model="topicNewsVisible" title="Topic news" size="720px"><el-table :data="topicNews" border><el-table-column prop="id" label="ID" width="80" /><el-table-column prop="title" label="Title" min-width="240" show-overflow-tooltip /><el-table-column prop="category_name" label="Category" width="110" /><el-table-column prop="source" label="Source" width="120" /><el-table-column prop="publish_time" label="Published" width="170" /><el-table-column label="Actions" width="160"><template #default="scope"><el-button text type="primary" @click="openNews(scope.row)">Open</el-button><el-button text type="danger" @click="unbindNews(scope.row)">Remove</el-button></template></el-table-column></el-table></el-drawer>
    <el-dialog v-model="bindNewsVisible" title="Bind news to topic" width="760px"><div class="filter-row bind-filter"><el-input v-model="bindKeyword" placeholder="Search news" clearable /><el-button type="primary" @click="loadCandidateNews">Search</el-button></div><el-table :data="candidateNews" border @selection-change="handleSelectionChange"><el-table-column type="selection" width="48" /><el-table-column prop="id" label="ID" width="80" /><el-table-column prop="title" label="Title" min-width="260" show-overflow-tooltip /><el-table-column prop="source" label="Source" width="120" /><el-table-column prop="publish_time" label="Published" width="170" /></el-table><template #footer><el-button @click="bindNewsVisible = false">Cancel</el-button><el-button type="primary" @click="submitBindNews">Bind selected</el-button></template></el-dialog>
  </section>
</template>

<style scoped>
.admin-hot-topic-management { width: 100%; }
.module-card { border-radius: 18px; }
.panel-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; margin-bottom: 16px; }
.panel-header h3 { margin: 0 0 6px; color: var(--color-text-primary); }
.panel-header p { margin: 0; color: var(--color-text-secondary); }
.summary-grid { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 12px; margin: 12px 0 16px; }
.summary-card { padding: 14px; border: 1px solid var(--color-border-light); border-radius: 14px; background: var(--color-bg-page); }
.summary-card span { display: block; color: var(--color-text-secondary); font-size: 13px; }
.summary-card strong { display: block; margin-top: 8px; font-size: 24px; color: var(--color-text-primary); }
.filter-row { display: flex; flex-wrap: wrap; gap: 10px; margin: 16px 0; }
.filter-row .el-input { width: 240px; }
.filter-row .el-select { width: 150px; }
.bind-filter .el-input { width: 360px; }
.pager { margin-top: 16px; justify-content: flex-end; }
.tag-item { margin: 2px 4px 2px 0; }
@media (max-width: 1200px) { .summary-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
@media (max-width: 720px) { .summary-grid { grid-template-columns: 1fr; } .filter-row .el-input, .filter-row .el-select { width: 100%; } }
</style>
