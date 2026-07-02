<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  type AdminTimelineDetailResponse,
  type AdminTimelineItem,
  type AdminTimelineListResponse,
  type AdminTimelineOptionsResponse,
  type AdminTimelineSourceNewsItem,
  type AdminTimelineSourceNewsResponse,
  clearAdminTimelineCache,
  generateAdminTimeline,
  getAdminTimelineDetail,
  getAdminTimelineList,
  getAdminTimelineOptions,
  getAdminTimelineSourceNews,
  refreshAdminTimeline,
} from '@/api/admin'
import {
  type AutoClusterResponse,
  autoClusterTimelineTopics,
} from '@/api/timeline'

const emit = defineEmits<{ (e: 'changed'): void }>()
const router = useRouter()

// ── 自动生成事件脉络 ────────────────────────────────────────────
const autoClusterForm = reactive({
  days: 30,
  max_news: 1000,
  max_write_topics: 8,
  use_llm_polish: true,
})
const autoClusterLoading = ref(false)
const autoClusterPublishing = ref(false)
const autoClusterPreview = ref<AutoClusterResponse | null>(null)

async function handleAutoClusterPreview() {
  autoClusterLoading.value = true
  try {
    const res = await autoClusterTimelineTopics({
      ...autoClusterForm,
      dry_run: true,
      confirm: false,
    })
    autoClusterPreview.value = res
    if (res.success) {
      ElMessage.success(`预览完成，候选 ${res.topics?.length ?? 0} 个话题`)
    } else {
      ElMessage.warning(res.message || '预览失败')
    }
  } catch (e: any) {
    ElMessage.error(e?.message || '自动生成预览失败')
  } finally {
    autoClusterLoading.value = false
  }
}

async function handleAutoClusterConfirm() {
  if (!autoClusterPreview.value?.success) {
    ElMessage.warning('请先预览生成结果')
    return
  }
  try {
    await ElMessageBox.confirm(
      '确认发布后，系统会清理旧的自动话题并写入新的自动话题和事件脉络。人工话题不会被覆盖。是否继续？',
      '确认发布自动事件脉络',
      { confirmButtonText: '确认发布', cancelButtonText: '取消', type: 'warning' },
    )
  } catch { return }

  autoClusterPublishing.value = true
  try {
    const res = await autoClusterTimelineTopics({
      ...autoClusterForm,
      dry_run: false,
      confirm: true,
    })
    if (res.success) {
      ElMessage.success('自动事件脉络发布成功')
      autoClusterPreview.value = null
      loadList()
    } else {
      ElMessage.error(res.message || '发布失败')
    }
  } catch (e: any) {
    ElMessage.error(e?.message || '自动事件脉络发布失败')
  } finally {
    autoClusterPublishing.value = false
  }
}

// ── state ──────────────────────────────────────────────────────
const timelineOptions = ref<AdminTimelineOptionsResponse | null>(null)
const timelineData = ref<AdminTimelineListResponse | null>(null)
const loading = ref(false)

const query = reactive({
  keyword: '',
  generate_status: '' as string,
  news_count_type: '' as string,
  has_cache: null as boolean | null,
  cache_error: null as boolean | null,
  page: 1,
  page_size: 10,
})

// detail / drawer state
const detailVisible = ref(false)
const detailData = ref<AdminTimelineDetailResponse | null>(null)
const loadingDetail = ref(false)

const sourceNewsVisible = ref(false)
const sourceNewsData = ref<AdminTimelineSourceNewsResponse | null>(null)
const sourceNewsTopicName = ref('')
const sourceNewsTopicId = ref(0)
const loadingSourceNews = ref(false)

const jsonVisible = ref(false)
const jsonText = ref('')

// ── computed ────────────────────────────────────────────────────
const summaryCards = computed(() => {
  const s = timelineData.value?.summary
  return [
    { key: 'topic_count', label: '全部主题', value: s?.topic_count ?? '--' },
    { key: 'generated', label: '已生成 Timeline', value: s?.generated_count ?? '--' },
    { key: 'not_generated', label: '未生成 Timeline', value: s?.not_generated_count ?? '--' },
    { key: 'failed', label: '生成失败', value: s?.failed_count ?? '--' },
    { key: 'insufficient', label: '相关新闻不足', value: s?.insufficient_news_count ?? '--' },
    { key: 'cache_error', label: '缓存异常', value: s?.cache_error_count ?? '--' },
  ]
})

const statusTagType = (status: string) => {
  if (status === 'generated') return 'success'
  if (status === 'generated (fallback)') return 'warning'
  if (status === 'failed') return 'danger'
  if (status === 'generating') return 'info'
  return 'info'
}

const cacheTagType = (status: string) => {
  if (status === 'normal') return 'success'
  if (status === 'no_cache') return 'info'
  return 'danger'
}

// ── load ────────────────────────────────────────────────────────
async function loadOptions() {
  timelineOptions.value = await getAdminTimelineOptions()
}

async function loadList() {
  loading.value = true
  try {
    timelineData.value = await getAdminTimelineList({ ...query })
  } catch (e) {
    ElMessage.error(e instanceof Error ? e.message : '加载失败')
  } finally {
    loading.value = false
  }
}

function resetQuery() {
  Object.assign(query, { keyword: '', generate_status: '', news_count_type: '', has_cache: null, cache_error: null, page: 1 })
  void loadList()
}

// ── detail ──────────────────────────────────────────────────────
async function openDetail(row: AdminTimelineItem) {
  detailVisible.value = true
  loadingDetail.value = true
  try {
    detailData.value = await getAdminTimelineDetail(row.topic_id)
  } catch (e) {
    ElMessage.error(e instanceof Error ? e.message : '加载详情失败')
  } finally {
    loadingDetail.value = false
  }
}

// ── source news ─────────────────────────────────────────────────
async function openSourceNews(row: AdminTimelineItem) {
  sourceNewsTopicId.value = row.topic_id
  sourceNewsTopicName.value = row.topic_name
  sourceNewsVisible.value = true
  loadingSourceNews.value = true
  try {
    sourceNewsData.value = await getAdminTimelineSourceNews(row.topic_id)
  } catch (e) {
    ElMessage.error(e instanceof Error ? e.message : '加载来源新闻失败')
  } finally {
    loadingSourceNews.value = false
  }
}

// ── actions ─────────────────────────────────────────────────────
async function confirmGenerate(row: AdminTimelineItem) {
  if (row.news_count < 2) {
    ElMessage.warning('该话题下新闻少于 2 篇，无法生成 Timeline')
    return
  }
  await ElMessageBox.confirm(`确认为「${row.topic_name}」生成 Timeline？`, '确认生成', { type: 'warning' })
  try {
    const r = await generateAdminTimeline(row.topic_id)
    ElMessage.success(r.message || '生成成功')
    await loadList()
    emit('changed')
  } catch (e) {
    ElMessage.error(e instanceof Error ? e.message : '生成失败')
  }
}

async function confirmRefresh(row: AdminTimelineItem) {
  if (row.news_count < 2) {
    ElMessage.warning('该话题下新闻少于 2 篇，无法刷新 Timeline')
    return
  }
  await ElMessageBox.confirm(`确认刷新「${row.topic_name}」的 Timeline？`, '确认刷新', { type: 'warning' })
  try {
    const r = await refreshAdminTimeline(row.topic_id)
    ElMessage.success(r.message || '刷新成功')
    await loadList()
    emit('changed')
  } catch (e) {
    ElMessage.error(e instanceof Error ? e.message : '刷新失败')
  }
}

async function confirmClearCache(row: AdminTimelineItem) {
  await ElMessageBox.confirm(`确认清理「${row.topic_name}」的 Timeline 缓存？`, '确认清理', { type: 'warning' })
  try {
    const r = await clearAdminTimelineCache(row.topic_id)
    ElMessage.success(r.message || '清理成功')
    await loadList()
    emit('changed')
  } catch (e) {
    ElMessage.error(e instanceof Error ? e.message : '清理失败')
  }
}

function openJson(row: AdminTimelineItem) {
  void (async () => {
    try {
      const d = await getAdminTimelineDetail(row.topic_id)
      jsonText.value = d.raw_json || '暂无 JSON 数据'
      jsonVisible.value = true
    } catch (e) {
      ElMessage.error(e instanceof Error ? e.message : '加载 JSON 失败')
    }
  })()
}

// ── mount ───────────────────────────────────────────────────────
onMounted(async () => {
  await Promise.all([loadOptions(), loadList()])
})
</script>

<template>
  <div class="admin-timeline-mgmt">
    <!-- header -->
    <div class="panel-header">
      <div>
        <h3>Timeline 管理</h3>
        <p>管理事件脉络时间线生成状态、来源新闻、缓存结果与异常刷新。</p>
      </div>
      <el-button type="primary" @click="loadList">刷新</el-button>
    </div>

    <!-- 自动生成事件脉络 -->
    <el-card class="auto-cluster-card" shadow="never">
      <template #header>
        <div class="auto-cluster-card__header">
          <div>
            <span style="font-weight:700;font-size:16px">自动生成事件脉络</span>
            <p style="margin:4px 0 0;font-size:13px;color:#64748b">基于最近新闻自动聚类生成候选话题和事件脉络。请先预览，确认无误后再发布。</p>
          </div>
        </div>
      </template>

      <!-- 参数表单 -->
      <div class="auto-cluster-form">
        <el-form :inline="true" :model="autoClusterForm" size="small">
          <el-form-item label="最近天数">
            <el-input-number v-model="autoClusterForm.days" :min="1" :max="90" />
          </el-form-item>
          <el-form-item label="最大新闻数">
            <el-input-number v-model="autoClusterForm.max_news" :min="20" :max="5000" :step="100" />
          </el-form-item>
          <el-form-item label="最大话题数">
            <el-input-number v-model="autoClusterForm.max_write_topics" :min="1" :max="20" />
          </el-form-item>
          <el-form-item label="LLM 润色">
            <el-switch v-model="autoClusterForm.use_llm_polish" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :loading="autoClusterLoading" :disabled="autoClusterPublishing" @click="handleAutoClusterPreview">
              {{ autoClusterLoading ? '生成中...' : '预览生成' }}
            </el-button>
            <el-button type="success" :loading="autoClusterPublishing" :disabled="autoClusterLoading" @click="handleAutoClusterConfirm">
              {{ autoClusterPublishing ? '发布中...' : '确认发布' }}
            </el-button>
          </el-form-item>
        </el-form>
      </div>

      <!-- 预览结果 -->
      <template v-if="autoClusterPreview">
        <el-alert
          :type="autoClusterPreview.success ? 'success' : 'warning'"
          :title="autoClusterPreview.message || ''"
          :closable="false"
          style="margin-bottom:12px"
        />
        <div v-if="autoClusterPreview.summary" class="auto-cluster-summary">
          <span>手动话题 {{ autoClusterPreview.summary.manual_topic_count ?? '-' }}</span>
          <span>活跃自动话题 {{ autoClusterPreview.summary.auto_active_count ?? '-' }}</span>
          <span>本次将写入 {{ autoClusterPreview.summary.write_topic_count ?? autoClusterPreview.topics?.length ?? '-' }} 个</span>
          <span>绑定新闻 {{ autoClusterPreview.summary.updated_news_count ?? '-' }}</span>
        </div>
        <el-table v-if="autoClusterPreview.topics?.length" :data="autoClusterPreview.topics" size="small" style="margin-top:8px" max-height="400">
          <el-table-column prop="topic_name" label="话题名" min-width="140" />
          <el-table-column prop="heat_score" label="热度" width="70" />
          <el-table-column prop="news_count" label="新闻" width="60" />
          <el-table-column prop="event_point_count" label="事件点" width="70" />
          <el-table-column prop="quality_status" label="质量" width="80">
            <template #default="{ row }">
              <el-tag :type="row.quality_status==='ok'?'success':'warning'" size="small">{{ row.quality_status }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="LLM" width="60">
            <template #default="{ row }">{{ row.llm_used ? '是' : '否' }}</template>
          </el-table-column>
          <el-table-column label="代表新闻" min-width="200">
            <template #default="{ row }">
              <span v-for="(t,i) in (row.representative_titles||[]).slice(0,2)" :key="i" style="display:block;font-size:12px;color:#64748b">{{ t?.slice(0,50) }}</span>
            </template>
          </el-table-column>
        </el-table>
        <div v-if="autoClusterPreview.skipped_topics?.length" style="margin-top:8px">
          <span style="font-size:13px;color:#909399">已跳过：</span>
          <el-tag v-for="s in autoClusterPreview.skipped_topics" :key="s.topic_name" size="small" type="info" style="margin:2px 4px">
            {{ s.topic_name }} ({{ s.reason }})
          </el-tag>
        </div>
        <div v-if="autoClusterPreview.warnings?.length" style="margin-top:8px">
          <el-alert v-for="(w,i) in autoClusterPreview.warnings" :key="i" :title="w" type="warning" :closable="false" style="margin-bottom:4px" />
        </div>
      </template>
    </el-card>

    <!-- summary cards -->
    <div class="summary-grid">
      <article v-for="card in summaryCards" :key="card.key" class="summary-card">
        <span>{{ card.label }}</span>
        <strong>{{ card.value }}</strong>
      </article>
    </div>

    <!-- filters -->
    <div class="filter-row">
      <el-input v-model="query.keyword" placeholder="主题名称或关键词" clearable style="width:200px" />
      <el-select v-model="query.generate_status" placeholder="生成状态" clearable style="width:160px">
        <el-option v-for="o in timelineOptions?.status_options || []" :key="o.value" :label="o.label" :value="o.value" />
      </el-select>
      <el-select v-model="query.news_count_type" placeholder="关联新闻数" clearable style="width:160px">
        <el-option v-for="o in timelineOptions?.news_count_options || []" :key="o.value" :label="o.label" :value="o.value" />
      </el-select>
      <el-select v-model="query.has_cache" placeholder="是否有缓存" clearable style="width:140px">
        <el-option label="有缓存" :value="true" />
        <el-option label="无缓存" :value="false" />
      </el-select>
      <el-select v-model="query.cache_error" placeholder="缓存异常" clearable style="width:140px">
        <el-option label="有异常" :value="true" />
        <el-option label="无异常" :value="false" />
      </el-select>
      <el-button type="primary" @click="query.page = 1; loadList()">查询</el-button>
      <el-button @click="resetQuery">重置</el-button>
    </div>

    <!-- table -->
    <el-table v-loading="loading" :data="timelineData?.items || []" border>
      <el-table-column prop="topic_name" label="事件主题" min-width="200" show-overflow-tooltip />
      <el-table-column label="关键词" min-width="200">
        <template #default="scope">
          <el-tag v-for="tag in scope.row.keyword_list" :key="tag" size="small" effect="plain" class="tag-item">{{ tag }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="news_count" label="关联新闻数" width="110" align="center" />
      <el-table-column label="Timeline 状态" width="140">
        <template #default="scope">
          <el-tag :type="statusTagType(scope.row.generate_status)" size="small">{{ scope.row.generate_status_label }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="缓存状态" width="120">
        <template #default="scope">
          <el-tag :type="cacheTagType(scope.row.cache_status)" size="small">{{ scope.row.cache_status_label }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="source_news_count" label="来源新闻数" width="110" align="center" />
      <el-table-column prop="generated_at" label="最近生成时间" width="170" />
      <el-table-column prop="updated_at" label="最近更新时间" width="170" />
      <el-table-column label="操作" width="380" fixed="right">
        <template #default="scope">
          <el-button v-if="scope.row.cache_status !== 'no_cache'" size="small" text type="primary" @click="openDetail(scope.row)">查看时间线</el-button>
          <el-button size="small" text type="primary" @click="openSourceNews(scope.row)">来源新闻</el-button>
          <el-button v-if="scope.row.cache_status === 'no_cache' || scope.row.generate_status === 'not_generated' || scope.row.generate_status === 'failed'" size="small" text type="success" :disabled="scope.row.news_count < 2" @click="confirmGenerate(scope.row)">生成</el-button>
          <el-button v-if="scope.row.cache_status !== 'no_cache'" size="small" text type="warning" :disabled="scope.row.news_count < 2" @click="confirmRefresh(scope.row)">刷新</el-button>
          <el-button v-if="scope.row.cache_status !== 'no_cache'" size="small" text @click="openJson(scope.row)">JSON</el-button>
          <el-button v-if="scope.row.cache_status !== 'no_cache'" size="small" text type="danger" @click="confirmClearCache(scope.row)">清理缓存</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      class="pager"
      layout="total, prev, pager, next, sizes"
      :total="timelineData?.total || 0"
      v-model:current-page="query.page"
      v-model:page-size="query.page_size"
      @current-change="loadList"
      @size-change="loadList"
    />

    <!-- detail drawer -->
    <el-drawer v-model="detailVisible" title="Timeline 详情" size="640px">
      <div v-if="loadingDetail" v-loading="loadingDetail" style="min-height:200px" />
      <template v-else-if="detailData">
        <el-descriptions :column="2" border size="small">
          <el-descriptions-item label="事件主题">{{ detailData.topic_name }}</el-descriptions-item>
          <el-descriptions-item label="生成状态">
            <el-tag :type="statusTagType(detailData.generate_status)" size="small">{{ detailData.generate_status_label }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="生成时间">{{ detailData.generated_at || '--' }}</el-descriptions-item>
          <el-descriptions-item label="更新时间">{{ detailData.updated_at || '--' }}</el-descriptions-item>
          <el-descriptions-item label="来源新闻数">{{ detailData.source_news_ids.length }}</el-descriptions-item>
          <el-descriptions-item label="缓存校验">
            <el-tag v-if="detailData.cache_check.json_valid && detailData.cache_check.source_news_valid" type="success" size="small">正常</el-tag>
            <el-tag v-else type="danger" size="small">{{ detailData.cache_check.message }}</el-tag>
          </el-descriptions-item>
        </el-descriptions>

        <h4 style="margin:16px 0 8px">Timeline 节点 ({{ detailData.timeline_nodes.length }})</h4>
        <div v-if="detailData.timeline_nodes.length === 0" style="color:#909399;padding:12px">
          {{ detailData.generate_status === 'not_generated' ? '暂无时间线结果' : '暂无节点' }}
        </div>
        <div v-else class="tl-nodes">
          <el-card v-for="node in detailData.timeline_nodes" :key="node.event_id" shadow="never" size="small" class="tl-node-card">
            <div class="tl-node-header">
              <span class="tl-node-time">{{ node.event_time }}</span>
              <el-tag size="small" effect="plain">{{ node.event_type }}</el-tag>
              <span class="tl-node-importance">{{ '★'.repeat(node.importance) }}{{ '☆'.repeat(5 - node.importance) }}</span>
            </div>
            <h5>{{ node.event_title }}</h5>
            <p class="tl-node-summary">{{ node.event_summary }}</p>
            <div class="tl-node-source">
              来源: <a :href="`/news/${node.source_news_id}`" target="_blank">{{ node.source_title }}</a> ({{ node.source_name }})
            </div>
          </el-card>
        </div>

        <h4 style="margin:16px 0 8px">来源新闻 ({{ detailData.source_news.length }})</h4>
        <el-table v-if="detailData.source_news.length" :data="detailData.source_news as any[]" border size="small">
          <el-table-column prop="id" label="ID" width="60" />
          <el-table-column prop="title" label="标题" min-width="200" show-overflow-tooltip />
          <el-table-column prop="source" label="来源" width="100" />
          <el-table-column prop="publish_time" label="发布时间" width="160" />
          <el-table-column prop="status_label" label="状态" width="80" />
        </el-table>
        <div v-else style="color:#909399;padding:12px">暂无来源新闻</div>
      </template>
    </el-drawer>

    <!-- source news drawer -->
    <el-drawer v-model="sourceNewsVisible" :title="`来源新闻 - ${sourceNewsTopicName}`" size="640px">
      <div v-if="loadingSourceNews" v-loading="loadingSourceNews" style="min-height:200px" />
      <template v-else-if="sourceNewsData">
        <p style="color:#909399;margin-bottom:8px">topic_id: {{ sourceNewsTopicId }}，共 {{ sourceNewsData.total }} 条</p>
        <el-table :data="sourceNewsData.items" border size="small">
          <el-table-column prop="id" label="ID" width="60" />
          <el-table-column prop="title" label="标题" min-width="200" show-overflow-tooltip />
          <el-table-column prop="source" label="来源" width="100" />
          <el-table-column prop="publish_time" label="发布时间" width="160" />
          <el-table-column label="状态" width="80">
            <template #default="scope">
              <el-tag size="small" :type="scope.row.status === 1 ? 'success' : 'info'">{{ scope.row.status_label }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="在缓存中" width="90" align="center">
            <template #default="scope">
              <el-tag size="small" :type="scope.row.in_source_news_ids ? 'success' : 'info'">
                {{ scope.row.in_source_news_ids ? '是' : '否' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="80">
            <template #default="scope">
              <el-button size="small" text type="primary" @click="router.push(`/news/${scope.row.id}`)">查看</el-button>
            </template>
          </el-table-column>
        </el-table>
      </template>
    </el-drawer>

    <!-- json viewer drawer -->
    <el-drawer v-model="jsonVisible" title="Timeline JSON" size="640px">
      <pre v-if="jsonText" class="json-block">{{ jsonText }}</pre>
      <el-empty v-else description="暂无 JSON 数据" />
    </el-drawer>
  </div>
</template>

<style scoped>
.admin-timeline-mgmt { padding: 0; }
.panel-header { display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:16px }
.panel-header h3 { margin:0; font-size:18px }
.panel-header p { margin:4px 0 0; color:#909399; font-size:13px }

.summary-grid { display:grid; grid-template-columns:repeat(6,1fr); gap:12px; margin-bottom:16px }
.summary-card { background:#f5f7fa; border-radius:8px; padding:14px 12px; display:flex; flex-direction:column; gap:4px }
.summary-card span { font-size:12px; color:#909399 }
.summary-card strong { font-size:20px }

.filter-row { display:flex; gap:10px; flex-wrap:wrap; margin-bottom:16px; align-items:center }
.pager { margin-top:16px; justify-content:flex-end }
.tag-item { margin-right:4px }

.tl-nodes { display:flex; flex-direction:column; gap:12px }
.tl-node-card { border:1px solid #ebeef5 }
.tl-node-header { display:flex; gap:8px; align-items:center; margin-bottom:8px; font-size:12px }
.tl-node-time { color:#909399 }
.tl-node-importance { color:#f0ad4e; margin-left:auto }
.tl-node-card h5 { margin:0 0 4px; font-size:14px }
.tl-node-summary { margin:0 0 8px; color:#606266; font-size:13px }
.tl-node-source { font-size:12px; color:#909399 }

.json-block { background:#1e1e1e; color:#d4d4d4; padding:16px; border-radius:8px; font-size:12px; white-space:pre-wrap; word-break:break-all; max-height:calc(100vh - 160px); overflow:auto }

.auto-cluster-card { margin-bottom:20px; border:1px solid var(--color-border); border-radius:12px }
.auto-cluster-card__header { display:flex; align-items:center; justify-content:space-between }
.auto-cluster-form { margin-bottom:12px }
.auto-cluster-summary { display:flex; flex-wrap:wrap; gap:12px 24px; font-size:13px; color:#64748b }
.auto-cluster-summary span { white-space:nowrap }
</style>
