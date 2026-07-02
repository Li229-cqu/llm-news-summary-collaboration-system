<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getAdminHotTopicDetail,
  getAdminHotTopicList,
  getAdminHotTopicOptions,
  hideAdminHotTopic,
  refreshAdminHotTopicHeat,
  restoreAdminHotTopic,
  type AdminHotTopicDetail,
  type AdminHotTopicItem,
  type AdminHotTopicListResponse,
  type AdminHotTopicOptions,
  updateAdminHotTopicRank,
} from '@/api/admin'

const emit = defineEmits<{ changed: [] }>()

const loadingHot = ref(false)
const hotOptions = ref<AdminHotTopicOptions | null>(null)
const hotData = ref<AdminHotTopicListResponse | null>(null)
const hotDetail = ref<AdminHotTopicDetail | null>(null)
const detailVisible = ref(false)
const rankDialogVisible = ref(false)
const currentHot = ref<AdminHotTopicItem | null>(null)
const rankForm = reactive({ rank_no: 1 })

const hotQuery = reactive({ keyword: '', hot_type: '', target_type: '', status: null as number | null, is_hidden: null as boolean | null, page: 1, page_size: 10 })

const hotSummaryCards = computed(() => [
  { key: 'total', label: '热搜总数', value: hotData.value?.summary.total_count ?? 0 },
  { key: 'news', label: '新闻热搜', value: hotData.value?.summary.news_hot_count ?? 0 },
  { key: 'post', label: '社区热搜', value: hotData.value?.summary.community_hot_count ?? 0 },
  { key: 'hidden', label: '已隐藏', value: hotData.value?.summary.hidden_count ?? 0 },
])

async function loadHotOptions() { hotOptions.value = await getAdminHotTopicOptions() }
async function loadHotList() {
  loadingHot.value = true
  try {
    hotData.value = await getAdminHotTopicList({ ...hotQuery })
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '热搜列表加载失败')
  } finally {
    loadingHot.value = false
  }
}
function resetHotQuery() {
  Object.assign(hotQuery, { keyword: '', hot_type: '', target_type: '', status: null, is_hidden: null, page: 1 })
  void loadHotList()
}
async function openHotDetail(row: AdminHotTopicItem) {
  hotDetail.value = await getAdminHotTopicDetail(row.id)
  detailVisible.value = true
}
function openRankDialog(row: AdminHotTopicItem) {
  currentHot.value = row
  rankForm.rank_no = Math.max(row.rank_no || 1, 1)
  rankDialogVisible.value = true
}
async function submitRank() {
  if (!currentHot.value) return
  await updateAdminHotTopicRank(currentHot.value.id, rankForm.rank_no)
  ElMessage.success('排序已更新')
  rankDialogVisible.value = false
  await loadHotList()
  emit('changed')
}
async function confirmHotAction(row: AdminHotTopicItem, action: 'hide' | 'restore' | 'refresh') {
  const actionLabel = { hide: '隐藏', restore: '恢复', refresh: '刷新热度' }[action]
  await ElMessageBox.confirm(`确认${actionLabel}该热搜项？`, '操作确认', { type: 'warning' })
  if (action === 'hide') await hideAdminHotTopic(row.id)
  if (action === 'restore') await restoreAdminHotTopic(row.id)
  if (action === 'refresh') await refreshAdminHotTopicHeat(row.id)
  ElMessage.success('操作完成')
  await loadHotList()
  emit('changed')
}

onMounted(async () => {
  await loadHotOptions()
  await loadHotList()
})
</script>

<template>
  <section class="admin-hot-topic-management">
    <el-card shadow="never" class="module-card">
      <div class="panel-header">
        <div>
          <h3>热搜运营</h3>
          <p>管理首页热搜、社区热榜等运营展示内容，维护热搜词、热度、显示状态等。</p>
        </div>
        <el-button type="primary" @click="loadHotList()">刷新</el-button>
      </div>

      <div class="summary-grid">
        <article v-for="card in hotSummaryCards" :key="card.key" class="summary-card">
          <span>{{ card.label }}</span>
          <strong>{{ card.value }}</strong>
        </article>
      </div>
      <div class="filter-row">
        <el-input v-model="hotQuery.keyword" placeholder="标题或标签" clearable />
        <el-select v-model="hotQuery.hot_type" placeholder="热搜类型" clearable>
          <el-option label="新闻热搜" value="news_hot" />
          <el-option label="社区热搜" value="community_hot" />
        </el-select>
        <el-select v-model="hotQuery.target_type" placeholder="对象类型" clearable>
          <el-option v-for="item in hotOptions?.target_types || []" :key="item.value" :label="item.label" :value="item.value" />
        </el-select>
        <el-select v-model="hotQuery.status" placeholder="状态" clearable>
          <el-option v-for="item in hotOptions?.statuses || []" :key="item.value" :label="item.label" :value="item.value" />
        </el-select>
        <el-select v-model="hotQuery.is_hidden" placeholder="是否隐藏" clearable>
          <el-option label="已隐藏" :value="true" />
          <el-option label="可见" :value="false" />
        </el-select>
        <el-button type="primary" @click="hotQuery.page = 1; loadHotList()">查询</el-button>
        <el-button @click="resetHotQuery">重置</el-button>
      </div>
      <el-table v-loading="loadingHot" :data="hotData?.items || []" border empty-text="暂无热搜数据">
        <el-table-column prop="rank_no" label="排序" width="80" />
        <el-table-column prop="title" label="标题" min-width="220" show-overflow-tooltip />
        <el-table-column prop="hot_type" label="热搜类型" width="130" />
        <el-table-column prop="target_type" label="对象" width="100" />
        <el-table-column prop="target_id" label="对象 ID" width="90" />
        <el-table-column prop="tag" label="标签" width="100" />
        <el-table-column prop="heat_score" label="热度" width="100" />
        <el-table-column label="状态" width="100">
          <template #default="scope"><el-tag :type="scope.row.status === 1 ? 'success' : 'info'" size="small">{{ scope.row.status_label }}</el-tag></template>
        </el-table-column>
        <el-table-column prop="updated_at" label="更新时间" width="170" />
        <el-table-column label="操作" width="280" fixed="right">
          <template #default="scope">
            <el-button size="small" text type="primary" @click="openHotDetail(scope.row)">详情</el-button>
            <el-button size="small" text type="primary" :disabled="!hotData?.support.manual_rank_supported" @click="openRankDialog(scope.row)">排序</el-button>
            <el-button size="small" text :type="scope.row.is_hidden ? 'success' : 'danger'" @click="confirmHotAction(scope.row, scope.row.is_hidden ? 'restore' : 'hide')">{{ scope.row.is_hidden ? '恢复' : '隐藏' }}</el-button>
            <el-button size="small" text @click="confirmHotAction(scope.row, 'refresh')">刷新热度</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination class="pager" layout="total, prev, pager, next, sizes" :total="hotData?.total || 0" v-model:current-page="hotQuery.page" v-model:page-size="hotQuery.page_size" @current-change="loadHotList" @size-change="loadHotList" />
    </el-card>

    <el-drawer v-model="detailVisible" title="热搜详情" size="520px">
      <el-descriptions v-if="hotDetail" :column="1" border>
        <el-descriptions-item label="标题">{{ hotDetail.title }}</el-descriptions-item>
        <el-descriptions-item label="对象类型">{{ hotDetail.target_type }}</el-descriptions-item>
        <el-descriptions-item label="关联内容">{{ hotDetail.target_title || '关联内容不存在' }}</el-descriptions-item>
        <el-descriptions-item label="热度">{{ hotDetail.heat_score }}</el-descriptions-item>
        <el-descriptions-item label="状态">{{ hotDetail.status_label }}</el-descriptions-item>
      </el-descriptions>
    </el-drawer>
    <el-dialog v-model="rankDialogVisible" title="调整排序" width="420px">
      <el-form label-width="90px"><el-form-item label="排序"><el-input-number v-model="rankForm.rank_no" :min="1" /></el-form-item></el-form>
      <template #footer><el-button @click="rankDialogVisible = false">取消</el-button><el-button type="primary" @click="submitRank">保存</el-button></template>
    </el-dialog>
  </section>
</template>

<style scoped>
.admin-hot-topic-management { width: 100%; }
.module-card { border-radius: 18px; }
.panel-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; margin-bottom: 16px; }
.panel-header h3 { margin: 0 0 6px; color: var(--color-text-primary); }
.panel-header p { margin: 0; color: var(--color-text-secondary); }
.summary-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; margin: 12px 0 16px; }
.summary-card { padding: 14px; border: 1px solid var(--color-border-light); border-radius: 14px; background: var(--color-bg-page); }
.summary-card span { display: block; color: var(--color-text-secondary); font-size: 13px; }
.summary-card strong { display: block; margin-top: 8px; font-size: 24px; color: var(--color-text-primary); }
.filter-row { display: flex; flex-wrap: wrap; gap: 10px; margin: 16px 0; }
.filter-row .el-input { width: 240px; }
.filter-row .el-select { width: 150px; }
.pager { margin-top: 16px; justify-content: flex-end; }
@media (max-width: 1200px) { .summary-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
@media (max-width: 720px) { .summary-grid { grid-template-columns: 1fr; } .filter-row .el-input, .filter-row .el-select { width: 100%; } }
</style>
