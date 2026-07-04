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
  type AutoClusterSkippedTopic,
  type AutoClusterTopicPreview,
  type ConfirmedTimelineTopic,
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
type EditableAutoClusterTopic = AutoClusterTopicPreview & {
  selected_for_publish: boolean
  keyword_text: string
}
const editableAutoClusterTopics = ref<EditableAutoClusterTopic[]>([])
const originalAutoClusterTopics = ref<EditableAutoClusterTopic[]>([])

// ── 推荐话题折叠状态 ────────────────────────────────────────────
const expandedTopicIndices = ref(new Set<number>())

function toggleTopicExpand(index: number) {
  const set = expandedTopicIndices.value
  if (set.has(index)) {
    set.delete(index)
  } else {
    set.add(index)
  }
  expandedTopicIndices.value = new Set(set)
}

function isTopicExpanded(index: number): boolean {
  return expandedTopicIndices.value.has(index)
}

const autoClusterTopics = computed(() => editableAutoClusterTopics.value)
const autoClusterSkippedTopics = computed(() => autoClusterPreview.value?.skipped_topics || [])
const selectedAutoClusterTopics = computed(() => autoClusterTopics.value.filter((topic) => topic.selected_for_publish))
const publishableAutoClusterTopics = computed(() => selectedAutoClusterTopics.value.filter((topic) => isTopicPublishable(topic)))
const autoClusterRecommendedCount = computed(() => (
  publishableAutoClusterTopics.value.length
))
const autoClusterSkippedCount = computed(() => (
  autoClusterPreview.value?.skipped_count
  ?? autoClusterPreview.value?.summary?.skipped_count
  ?? autoClusterSkippedTopics.value.length
))
const autoClusterCandidateCount = computed(() => (
  autoClusterPreview.value?.total_candidates
  ?? autoClusterPreview.value?.summary?.candidate_count
  ?? autoClusterTopics.value.length + autoClusterSkippedTopics.value.length
))
const autoClusterKUsed = computed(() => {
  const allTopics = [...autoClusterTopics.value, ...autoClusterSkippedTopics.value]
  return allTopics.find((item) => item.k_used)?.k_used
})
const autoClusterHasSplit = computed(() => (
  [...autoClusterTopics.value, ...autoClusterSkippedTopics.value].some((item) => item.split_from_large_cluster)
))
const canConfirmAutoCluster = computed(() => (
  !!autoClusterPreview.value?.success && publishableAutoClusterTopics.value.length > 0 && !autoClusterLoading.value
))

const qualityStatusLabelMap: Record<string, string> = {
  ok: '可推荐',
  broad_topic: '话题过宽',
  entity_mixed: '核心实体混杂',
  mixed_category: '分类混杂',
  too_small: '相关新闻过少',
  too_small_after_filter: '过滤后新闻不足',
  low_quality: '质量评分过低',
  low_coherence: '话题关联度较低',
  weak_name: '话题名过泛',
}

const qualityFlagLabelMap: Record<string, string> = {
  outlier_removed: '已剔除离群新闻',
  high_outlier_ratio: '离群新闻比例较高',
  low_entity_purity: '核心实体一致性偏低',
  low_category_purity: '分类纯度偏低',
  broad_topic: '话题过宽',
  strict_entity_match: '启用严格实体匹配',
  split_from_large_cluster: '由大簇拆分产生',
}

function qualityStatusLabel(status?: string) {
  if (!status) return '-'
  return qualityStatusLabelMap[status] || status
}

function qualityFlagLabel(flag?: string) {
  if (!flag) return '-'
  return qualityFlagLabelMap[flag] || flag
}

function getQualityStatusTagType(status?: string) {
  if (status === 'ok') return 'success'
  if (status === 'entity_mixed' || status === 'low_quality' || status === 'low_coherence') return 'danger'
  if (status === 'broad_topic' || status === 'mixed_category' || status === 'weak_name') return 'warning'
  if (status === 'too_small' || status === 'too_small_after_filter') return 'info'
  return 'info'
}

function formatScore(value?: number) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return '-'
  return Number(value).toFixed(2)
}

function formatPercent(value?: number) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return '-'
  const n = Number(value)
  const pct = Math.abs(n) <= 1 ? n * 100 : n
  return `${pct.toFixed(0)}%`
}

function formatRemoved(topic: AutoClusterTopicPreview | AutoClusterSkippedTopic) {
  const count = topic.removed_count ?? 0
  return count > 0 ? `已剔除 ${count} 条疑似不相关新闻` : '无剔除'
}

function getEventTitle(point: Record<string, any>) {
  return point?.event_title || point?.title || point?.name || '未命名事件点'
}

function getEventSummary(point: Record<string, any>) {
  return point?.event_summary || point?.summary || point?.description || ''
}

function getEventTime(point: Record<string, any>) {
  return point?.event_time || point?.time || point?.date || point?.publish_time || ''
}

function getEventNewsCount(point: Record<string, any>) {
  return point?.news_count ?? point?.source_news_ids?.length ?? point?.related_news?.length ?? null
}

function deepClone<T>(value: T): T {
  return JSON.parse(JSON.stringify(value ?? null))
}

function parseKeywordText(value?: string) {
  return Array.from(new Set(
    (value || '')
      .split(/[,，、\s]+/)
      .map((item) => item.trim())
      .filter(Boolean)
      .slice(0, 10),
  ))
}

function normalizeEventPoint(point: Record<string, any>) {
  return {
    ...point,
    event_title: getEventTitle(point),
    event_summary: getEventSummary(point),
    event_time: getEventTime(point),
    source_news_ids: Array.isArray(point?.source_news_ids) ? point.source_news_ids : [],
    representative_news_id: point?.representative_news_id ?? point?.source_news_id,
  }
}

function normalizeEditableTopic(topic: AutoClusterTopicPreview): EditableAutoClusterTopic {
  const keywordList = Array.isArray(topic.keyword_list)
    ? topic.keyword_list
    : parseKeywordText((topic as any).keyword_list)
  return {
    ...deepClone(topic),
    summary: topic.summary || '',
    keyword_list: keywordList,
    keyword_text: keywordList.join(', '),
    event_points: (topic.event_points || []).map((point) => normalizeEventPoint(point)),
    selected_for_publish: true,
  }
}

function resetEditableTopics(response: AutoClusterResponse) {
  const sourceTopics = response.topics || response.topics_to_insert || []
  const normalized = sourceTopics.map((topic) => normalizeEditableTopic(topic))
  editableAutoClusterTopics.value = deepClone(normalized)
  originalAutoClusterTopics.value = deepClone(normalized)
}

function resetEditableTopic(index: number) {
  const original = originalAutoClusterTopics.value[index]
  if (!original) return
  editableAutoClusterTopics.value[index] = deepClone(original)
}

function isTopicPublishable(topic: EditableAutoClusterTopic) {
  return !!topic.selected_for_publish && !!topic.topic_name?.trim() && (topic.news_ids?.length || 0) >= 2
}

function removeTopicNews(topic: EditableAutoClusterTopic, index: number) {
  if (!topic.news_ids?.[index]) return
  topic.news_ids.splice(index, 1)
  topic.representative_titles?.splice(index, 1)
  topic.news_count = topic.news_ids.length
}

function buildConfirmedTopicsFromPreview(): ConfirmedTimelineTopic[] {
  return publishableAutoClusterTopics.value.map((topic) => ({
    topic_name: topic.topic_name.trim(),
    summary: topic.summary || '',
    keyword_list: parseKeywordText(topic.keyword_text),
    news_ids: topic.news_ids || [],
    event_points: (topic.event_points || []).map((point) => ({
      event_title: getEventTitle(point),
      event_summary: getEventSummary(point),
      event_time: getEventTime(point),
      source_news_ids: Array.isArray(point.source_news_ids) ? point.source_news_ids : [],
      representative_news_id: point.representative_news_id ?? point.source_news_id,
      keywords: Array.isArray(point.keywords) ? point.keywords : [],
    })),
    quality_status: topic.quality_status,
    quality_score: topic.quality_score,
    quality_flags: topic.quality_flags,
    quality_reasons: topic.quality_reasons,
    core_entities: topic.core_entities,
    removed_news_ids: topic.removed_news_ids,
    removed_count: topic.removed_count,
    entity_purity: topic.entity_purity,
    category_purity: topic.category_purity,
    heat_score: topic.heat_score,
  }))
}

async function handleAutoClusterPreview() {
  autoClusterLoading.value = true
  try {
    const res = await autoClusterTimelineTopics({
      ...autoClusterForm,
      dry_run: true,
      confirm: false,
    })
    autoClusterPreview.value = res
    resetEditableTopics(res)
    if (res.success) {
      ElMessage.success(`预览完成，候选 ${autoClusterTopics.value.length} 个推荐话题`)
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
  const confirmedTopics = buildConfirmedTopicsFromPreview()
  if (confirmedTopics.length <= 0) {
    ElMessage.warning('当前没有可推荐发布的话题，请调整参数或检查新闻数据')
    return
  }
  try {
    await ElMessageBox.confirm(
      '将按当前编辑后的预览结果发布。未勾选的话题不会发布，已跳过质量不合格话题，已剔除的离群新闻不会绑定。确认发布后，系统会清理旧的自动话题并写入新的自动话题和事件脉络，人工话题不会被覆盖。是否继续？',
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
      confirmed_topics: confirmedTopics,
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
            <p style="margin:4px 0 0;font-size:13px;color:var(--color-text-secondary)">基于最近新闻自动聚类生成候选话题和事件脉络。请先预览，确认无误后再发布。</p>
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
            <el-button type="success" :loading="autoClusterPublishing" :disabled="!canConfirmAutoCluster || autoClusterPublishing" @click="handleAutoClusterConfirm">
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
        <el-alert
          v-if="autoClusterPreview.success && autoClusterRecommendedCount === 0"
          title="当前没有可推荐发布的话题，请调整参数或检查新闻数据。"
          type="warning"
          :closable="false"
          style="margin-bottom:12px"
        />

        <div class="auto-cluster-diagnosis-summary">
          <article>
            <span>候选话题总数</span>
            <strong>{{ autoClusterCandidateCount }}</strong>
          </article>
          <article>
            <span>推荐发布数量</span>
            <strong>{{ autoClusterRecommendedCount }}</strong>
          </article>
          <article>
            <span>跳过数量</span>
            <strong>{{ autoClusterSkippedCount }}</strong>
          </article>
          <article>
            <span>本次使用 k 值</span>
            <strong>{{ autoClusterKUsed ?? '-' }}</strong>
          </article>
          <article>
            <span>大簇拆分</span>
            <strong>{{ autoClusterHasSplit ? '有' : '无' }}</strong>
          </article>
          <article>
            <span>绑定新闻</span>
            <strong>{{ autoClusterPreview.summary?.updated_news_count ?? '-' }}</strong>
          </article>
        </div>

        <section class="auto-cluster-section">
          <div class="auto-cluster-section__title">
            <span>推荐话题</span>
            <el-tag type="success" size="small">{{ autoClusterTopics.length }} 个</el-tag>
          </div>
          <el-empty v-if="autoClusterTopics.length === 0" description="暂无推荐话题" />
          <div v-else class="auto-topic-list">
            <article v-for="(topic, topicIndex) in autoClusterTopics" :key="`${topic.topic_name}-${topicIndex}`" class="auto-topic-card">
              <!-- ── 折叠摘要行 ── -->
              <div class="auto-topic-card__header" style="cursor:pointer" @click="toggleTopicExpand(topicIndex)">
                <div style="flex:1;min-width:0">
                  <div class="auto-topic-card__summary-line">
                    <h4 class="auto-topic-card__title-inline">{{ topic.topic_name }}</h4>
                    <el-tag :type="getQualityStatusTagType(topic.quality_status)" size="small">
                      {{ qualityStatusLabel(topic.quality_status) }}
                    </el-tag>
                    <span class="auto-topic-card__stat">质量分 {{ formatScore(topic.quality_score) }}</span>
                    <span class="auto-topic-card__stat">新闻 {{ topic.news_count ?? '-' }}</span>
                    <span class="auto-topic-card__stat">事件点 {{ topic.event_point_count ?? topic.event_points?.length ?? '-' }}</span>
                    <span class="auto-topic-card__stat">热度 {{ topic.heat_score ?? '-' }}</span>
                  </div>
                  <div class="auto-topic-card__sub-line">
                    <span v-if="topic.core_entities?.length">
                      核心实体：{{ topic.core_entities.slice(0, 3).join(' / ') }}<template v-if="topic.core_entities.length > 3"> 等{{ topic.core_entities.length }}个</template>
                    </span>
                    <span v-else class="auto-topic-empty">暂无明确核心实体</span>
                    <span v-if="(topic.removed_count ?? 0) > 0" class="auto-topic-card__removed-mark">
                      · 已剔除 {{ topic.removed_count }} 条
                    </span>
                  </div>
                </div>
                <div class="auto-topic-card__actions">
                  <el-tag size="small" :type="topic.llm_used || topic.llm_polished ? 'success' : 'info'" effect="plain">
                    LLM {{ topic.llm_used || topic.llm_polished ? '已润色' : '未润色' }}
                  </el-tag>
                  <el-tag v-if="topic.strict_entity_match" size="small" type="warning" effect="plain">严格实体匹配</el-tag>
                  <el-tag v-if="topic.split_from_large_cluster" size="small" type="warning" effect="plain">大簇拆分</el-tag>
                  <el-switch
                    v-model="topic.selected_for_publish"
                    size="small"
                    active-text="发布"
                    inactive-text="不发布"
                    @click.stop
                  />
                  <el-button size="small" text type="primary" @click.stop="toggleTopicExpand(topicIndex)">
                    {{ isTopicExpanded(topicIndex) ? '收起 ▲' : '展开 ▼' }}
                  </el-button>
                </div>
              </div>

              <!-- ── 展开后的完整编辑详情 ── -->
              <template v-if="isTopicExpanded(topicIndex)">
                <el-alert
                  v-if="topic.selected_for_publish && !isTopicPublishable(topic)"
                  title="该话题缺少有效话题名或有效新闻少于 2 条，确认发布时不会提交。"
                  type="warning"
                  :closable="false"
                  class="auto-topic-edit-alert"
                />

                <div class="auto-topic-edit">
                  <el-form label-position="top" size="small">
                    <el-form-item label="话题名">
                      <el-input v-model="topic.topic_name" maxlength="50" show-word-limit placeholder="请输入话题名" />
                    </el-form-item>
                    <el-form-item label="话题摘要">
                      <el-input
                        v-model="topic.summary"
                        type="textarea"
                        maxlength="300"
                        show-word-limit
                        :autosize="{ minRows: 2, maxRows: 4 }"
                        placeholder="请输入话题摘要"
                      />
                    </el-form-item>
                    <el-form-item label="关键词（逗号分隔，最多 10 个）">
                      <el-input v-model="topic.keyword_text" placeholder="墨西哥, 世界杯, 国际足联" />
                    </el-form-item>
                  </el-form>
                </div>

                <div class="auto-topic-metrics">
                  <span>实体纯度 {{ formatPercent(topic.entity_purity) }}</span>
                  <span>分类纯度 {{ formatPercent(topic.category_purity) }}</span>
                  <span>簇内相似度 {{ formatPercent(topic.cluster_avg_similarity) }}</span>
                  <span>事件合并阈值 {{ formatPercent(topic.event_merge_threshold) }}</span>
                  <span>{{ formatRemoved(topic) }}</span>
                </div>

                <div class="auto-topic-entities">
                  <span class="auto-topic-label">核心实体</span>
                  <template v-if="topic.core_entities?.length">
                    <el-tag v-for="entity in topic.core_entities" :key="entity" size="small" effect="plain">
                      {{ entity }}
                    </el-tag>
                  </template>
                  <span v-else class="auto-topic-empty">暂无明确核心实体</span>
                </div>

                <div v-if="topic.quality_flags?.length" class="auto-topic-flags">
                  <span class="auto-topic-label">质量标记</span>
                  <el-tag v-for="flag in topic.quality_flags" :key="flag" size="small" :type="flag === 'high_outlier_ratio' ? 'danger' : 'info'" effect="plain">
                    {{ qualityFlagLabel(flag) }}
                  </el-tag>
                </div>

                <el-collapse v-if="(topic.removed_news_titles?.length || 0) > 0" class="auto-topic-collapse">
                  <el-collapse-item :title="`查看剔除新闻 (${topic.removed_count ?? topic.removed_news_titles?.length ?? 0})`" name="removed">
                    <ul class="auto-topic-title-list">
                      <li v-for="(title, index) in topic.removed_news_titles" :key="`${title}-${index}`">{{ title }}</li>
                    </ul>
                  </el-collapse-item>
                </el-collapse>

                <div v-if="topic.event_points?.length" class="event-preview">
                  <span class="auto-topic-label">事件点预览</span>
                  <div class="event-preview__list">
                    <article v-for="(point, index) in topic.event_points.slice(0, 6)" :key="index" class="event-preview__item">
                      <el-input v-model="point.event_title" size="small" maxlength="80" placeholder="事件点标题" />
                      <el-input
                        v-model="point.event_summary"
                        type="textarea"
                        size="small"
                        maxlength="300"
                        :autosize="{ minRows: 2, maxRows: 3 }"
                        placeholder="事件点摘要"
                      />
                      <span v-if="getEventTime(point)" class="event-preview__time">{{ getEventTime(point) }}</span>
                      <span v-if="getEventNewsCount(point)" class="event-preview__count">关联新闻 {{ getEventNewsCount(point) }}</span>
                    </article>
                  </div>
                </div>
                <div v-else class="auto-topic-empty auto-topic-no-events">暂无事件点</div>

                <div v-if="topic.representative_titles?.length" class="representative-preview">
                  <span class="auto-topic-label">代表新闻</span>
                  <div class="representative-preview__list">
                    <div v-for="(title, index) in topic.representative_titles.slice(0, 5)" :key="`${title}-${index}`" class="representative-preview__item">
                      <span>{{ title }}</span>
                      <el-button
                        size="small"
                        text
                        type="danger"
                        :disabled="!topic.news_ids?.[index]"
                        @click="removeTopicNews(topic, index)"
                      >
                        从发布列表移除
                      </el-button>
                    </div>
                  </div>
                </div>

                <div style="margin-top:12px;text-align:right">
                  <el-button size="small" text type="primary" @click="resetEditableTopic(topicIndex)">恢复自动结果</el-button>
                </div>
              </template>
            </article>
          </div>
        </section>

        <section class="auto-cluster-section">
          <div class="auto-cluster-section__title">
            <span>跳过话题</span>
            <el-tag type="info" size="small">{{ autoClusterSkippedTopics.length }} 个</el-tag>
          </div>
          <el-empty v-if="autoClusterSkippedTopics.length === 0" description="暂无跳过话题" />
          <div v-else class="auto-topic-list">
            <article v-for="topic in autoClusterSkippedTopics" :key="topic.topic_name" class="auto-topic-card auto-topic-card--skipped">
              <div class="auto-topic-card__header">
                <div>
                  <h4>{{ topic.topic_name }}</h4>
                  <div class="auto-topic-card__meta">
                    <el-tag :type="getQualityStatusTagType(topic.quality_status || topic.reason)" size="small">
                      {{ qualityStatusLabel(topic.quality_status || topic.reason) }}
                    </el-tag>
                    <span>跳过原因 {{ qualityStatusLabel(topic.reason || topic.quality_status) }}</span>
                    <span>质量分 {{ formatScore(topic.quality_score) }}</span>
                    <span>实体纯度 {{ formatPercent(topic.entity_purity) }}</span>
                    <span>{{ formatRemoved(topic) }}</span>
                  </div>
                </div>
              </div>

              <div class="auto-topic-entities">
                <span class="auto-topic-label">核心实体</span>
                <template v-if="topic.core_entities?.length">
                  <el-tag v-for="entity in topic.core_entities" :key="entity" size="small" effect="plain">
                    {{ entity }}
                  </el-tag>
                </template>
                <span v-else class="auto-topic-empty">暂无明确核心实体</span>
              </div>

              <div v-if="topic.quality_flags?.length" class="auto-topic-flags">
                <span class="auto-topic-label">质量标记</span>
                <el-tag v-for="flag in topic.quality_flags" :key="flag" size="small" :type="flag === 'high_outlier_ratio' ? 'danger' : 'info'" effect="plain">
                  {{ qualityFlagLabel(flag) }}
                </el-tag>
              </div>
              <div v-if="topic.quality_reasons?.length" class="auto-topic-reasons">
                <span class="auto-topic-label">质量原因</span>
                <span>{{ topic.quality_reasons.join(' / ') }}</span>
              </div>

              <el-collapse v-if="(topic.removed_news_titles?.length || 0) > 0" class="auto-topic-collapse">
                <el-collapse-item :title="`查看剔除新闻 (${topic.removed_count ?? topic.removed_news_titles?.length ?? 0})`" name="removed">
                  <ul class="auto-topic-title-list">
                    <li v-for="(title, index) in topic.removed_news_titles" :key="`${title}-${index}`">{{ title }}</li>
                  </ul>
                </el-collapse-item>
              </el-collapse>

              <div v-if="topic.representative_titles?.length" class="representative-preview">
                <span class="auto-topic-label">代表新闻</span>
                <ul class="auto-topic-title-list">
                  <li v-for="(title, index) in topic.representative_titles.slice(0, 3)" :key="`${title}-${index}`">{{ title }}</li>
                </ul>
              </div>
            </article>
          </div>
        </section>
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
        <div v-if="detailData.timeline_nodes.length === 0" style="color:var(--color-text-muted);padding:12px">
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
        <div v-else style="color:var(--color-text-muted);padding:12px">暂无来源新闻</div>
      </template>
    </el-drawer>

    <!-- source news drawer -->
    <el-drawer v-model="sourceNewsVisible" :title="`来源新闻 - ${sourceNewsTopicName}`" size="640px">
      <div v-if="loadingSourceNews" v-loading="loadingSourceNews" style="min-height:200px" />
      <template v-else-if="sourceNewsData">
        <p style="color:var(--color-text-muted);margin-bottom:8px">topic_id: {{ sourceNewsTopicId }}，共 {{ sourceNewsData.total }} 条</p>
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
.panel-header p { margin:4px 0 0; color:var(--color-text-muted); font-size:13px }

.summary-grid { display:grid; grid-template-columns:repeat(6,1fr); gap:12px; margin-bottom:16px }
.summary-card { background:var(--color-bg); border-radius:8px; padding:14px 12px; display:flex; flex-direction:column; gap:4px }
.summary-card span { font-size:12px; color:var(--color-text-muted) }
.summary-card strong { font-size:20px }

.filter-row { display:flex; gap:10px; flex-wrap:wrap; margin-bottom:16px; align-items:center }
.pager { margin-top:16px; justify-content:flex-end }
.tag-item { margin-right:4px }

.tl-nodes { display:flex; flex-direction:column; gap:12px }
.tl-node-card { border:1px solid var(--color-border) }
.tl-node-header { display:flex; gap:8px; align-items:center; margin-bottom:8px; font-size:12px }
.tl-node-time { color:var(--color-text-muted) }
.tl-node-importance { color:#f0ad4e; margin-left:auto }
.tl-node-card h5 { margin:0 0 4px; font-size:14px }
.tl-node-summary { margin:0 0 8px; color:var(--color-text-primary); font-size:13px }
.tl-node-source { font-size:12px; color:var(--color-text-muted) }

.json-block { background:#1e1e1e; color:#d4d4d4; padding:16px; border-radius:8px; font-size:12px; white-space:pre-wrap; word-break:break-all; max-height:calc(100vh - 160px); overflow:auto }

.auto-cluster-card { margin-bottom:20px; border:1px solid var(--color-border); border-radius:12px }
.auto-cluster-card__header { display:flex; align-items:center; justify-content:space-between }
.auto-cluster-form { margin-bottom:12px }
.auto-cluster-summary { display:flex; flex-wrap:wrap; gap:12px 24px; font-size:13px; color:var(--color-text-secondary) }
.auto-cluster-summary span { white-space:nowrap }
.auto-cluster-diagnosis-summary { display:grid; grid-template-columns:repeat(6,minmax(0,1fr)); gap:10px; margin:12px 0 16px }
.auto-cluster-diagnosis-summary article { border:1px solid var(--color-border); border-radius:8px; padding:10px 12px; background:var(--color-bg-hover); display:flex; flex-direction:column; gap:4px; min-width:0 }
.auto-cluster-diagnosis-summary span { color:var(--color-text-secondary); font-size:12px }
.auto-cluster-diagnosis-summary strong { font-size:18px; color:var(--color-text-primary) }
.auto-cluster-section { margin-top:16px }
.auto-cluster-section__title { display:flex; align-items:center; gap:8px; margin-bottom:10px; font-weight:700; color:var(--color-text-primary) }
.auto-topic-list { display:flex; flex-direction:column; gap:12px }
.auto-topic-card { border:1px solid var(--color-border); border-radius:8px; padding:14px; background:var(--color-bg-card) }
.auto-topic-card--skipped { background:#fcfcfd }
.auto-topic-card__header { display:flex; justify-content:space-between; align-items:flex-start; gap:12px; margin-bottom:10px }
.auto-topic-card__summary-line { display:flex; align-items:center; flex-wrap:wrap; gap:6px 10px; margin-bottom:4px }
.auto-topic-card__title-inline { margin:0; font-size:15px; color:var(--color-text-primary); line-height:1.4; word-break:break-word; white-space:nowrap }
.auto-topic-card__stat { color:var(--color-text-secondary); font-size:12px; white-space:nowrap }
.auto-topic-card__sub-line { display:flex; align-items:center; flex-wrap:wrap; gap:6px 10px; color:var(--color-text-secondary); font-size:12px }
.auto-topic-card__removed-mark { color:#e6a23c }
.auto-topic-card__actions { display:flex; align-items:center; flex-wrap:wrap; gap:6px; flex-shrink:0 }
.auto-topic-card h4 { margin:0 0 8px; font-size:15px; color:var(--color-text-primary); line-height:1.4; word-break:break-word }
.auto-topic-card__meta,
.auto-topic-metrics,
.auto-topic-entities,
.auto-topic-flags,
.auto-topic-reasons,
.auto-topic-card__badges { display:flex; align-items:center; flex-wrap:wrap; gap:6px 10px; color:var(--color-text-secondary); font-size:12px }
.auto-topic-card__badges { justify-content:flex-end; flex-shrink:0 }
.auto-topic-edit { margin:10px 0 12px; padding:10px; border:1px solid var(--color-border); border-radius:8px; background:#fbfdff }
.auto-topic-edit :deep(.el-form-item) { margin-bottom:10px }
.auto-topic-edit :deep(.el-form-item:last-child) { margin-bottom:0 }
.auto-topic-edit-alert { margin-bottom:10px }
.auto-topic-metrics { margin-bottom:10px; padding:8px 10px; background:var(--color-bg-hover); border-radius:6px }
.auto-topic-entities,
.auto-topic-flags,
.auto-topic-reasons { margin-top:8px }
.auto-topic-label { color:var(--color-text-primary); font-weight:600; margin-right:2px }
.auto-topic-empty { color:var(--color-text-muted) }
.auto-topic-collapse { margin-top:8px; border-top:1px solid var(--color-border); border-bottom:1px solid var(--color-border) }
.auto-topic-title-list { margin:6px 0 0; padding-left:18px; color:var(--color-text-secondary); font-size:12px; line-height:1.7 }
.auto-topic-title-list li { word-break:break-word }
.event-preview { margin-top:12px }
.event-preview__list { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:8px; margin-top:8px }
.event-preview__item { border:1px solid var(--color-border); border-radius:8px; padding:10px; background:var(--color-bg-hover); min-width:0 }
.event-preview__item { display:flex; flex-direction:column; gap:8px }
.event-preview__item div { display:flex; align-items:center; gap:6px; flex-wrap:wrap }
.event-preview__item strong { font-size:13px; color:var(--color-text-primary); line-height:1.4; word-break:break-word }
.event-preview__item p { margin:6px 0 0; color:var(--color-text-secondary); font-size:12px; line-height:1.5; display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden }
.event-preview__time,
.event-preview__count { color:var(--color-text-secondary); font-size:12px }
.auto-topic-no-events { margin-top:10px }
.representative-preview { margin-top:12px }
.representative-preview__list { display:flex; flex-direction:column; gap:6px; margin-top:6px }
.representative-preview__item { display:flex; align-items:flex-start; justify-content:space-between; gap:10px; padding:6px 8px; border:1px solid var(--color-border); border-radius:6px; color:var(--color-text-secondary); font-size:12px; line-height:1.5 }
.representative-preview__item span { word-break:break-word }
@media (max-width: 1200px) {
  .auto-cluster-diagnosis-summary { grid-template-columns:repeat(3,minmax(0,1fr)) }
  .event-preview__list { grid-template-columns:1fr }
}
@media (max-width: 720px) {
  .auto-cluster-diagnosis-summary { grid-template-columns:repeat(2,minmax(0,1fr)) }
  .auto-topic-card__header { flex-direction:column }
  .auto-topic-card__actions { justify-content:flex-start }
}
</style>
