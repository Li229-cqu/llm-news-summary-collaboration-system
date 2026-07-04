<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Download } from '@element-plus/icons-vue'

import { useAIDraftStore } from '@/stores/aiDraft'
import { deleteAIRecord, getAIHistory, getAIRecordDetail, type AIGenerateRecordItem } from '@/api/ai'

import { exportRecordToWord } from '@/utils/exportWord'
import {
  formatProviderModel,
  getAIGenerateSourceLabel,
  getAIGenerateSourceTagType,
  normalizeAIGenerateHistoryDetail,
  normalizeAIGenerateHistoryRecord,
  type NormalizedAIGenerateHistoryDetail,
  type NormalizedAIGenerateHistoryRecord,
} from '@/utils/normalizeAIGenerateResult'

const props = defineProps<{ mode: 'list' | 'detail'; recordId?: number | null }>()
const emit = defineEmits<{
  (e: 'back-to-input'): void
  (e: 'back-to-list'): void
  (e: 'view-detail', id: number | string): void
  (e: 'reuse', record: NormalizedAIGenerateHistoryDetail): void
}>()

const aiDraft = useAIDraftStore()

const records = ref<NormalizedAIGenerateHistoryRecord[]>([])
const listLoading = ref(false)
const detail = ref<NormalizedAIGenerateHistoryDetail | null>(null)
const detailLoading = ref(false)
const detailError = ref('')
const exportingId = ref<number | string | null>(null)
const exportingDetail = ref(false)
const sourceExpanded = ref(false)

async function loadHistory() {
  listLoading.value = true
  try {
    const response = await getAIHistory()
    records.value = (response.records || []).map(record => normalizeAIGenerateHistoryRecord(record))
  } catch {
    ElMessage.error('加载历史记录失败')
  } finally {
    listLoading.value = false
  }
}

async function loadDetail(id: number) {
  detailLoading.value = true
  detailError.value = ''
  try {
    const raw = await getAIRecordDetail(id)
    detail.value = normalizeAIGenerateHistoryDetail(raw)
  } catch (error: any) {
    detailError.value = error?.message || '加载失败'
  } finally {
    detailLoading.value = false
  }
}

watch(() => props.recordId, (value) => {
  if (props.mode === 'detail' && value) {
    loadDetail(value)
  }
})

onMounted(() => {
  if (props.mode === 'list') loadHistory()
  if (props.mode === 'detail' && props.recordId) loadDetail(props.recordId)
})

defineExpose({ loadHistory, loadDetail })

async function handleDelete(record: AIGenerateRecordItem) {
  try {
    await ElMessageBox.confirm('确定删除这条历史记录吗？', '删除', { type: 'warning' })
    await deleteAIRecord(record.id)
    ElMessage.success('已删除')
    await loadHistory()
  } catch {
    /* cancel */
  }
}

async function handleReuse(record: AIGenerateRecordItem) {
  try {
    const raw = await getAIRecordDetail(record.id)
    const normalized = normalizeAIGenerateHistoryDetail(raw)
    aiDraft.clearResult()
    aiDraft.setInputText(normalized.input_text)
    aiDraft.setParams(normalized.params as any)
    ElMessage.success('已复用历史输入')
    emit('reuse', normalized)
    emit('back-to-input')
  } catch {
    ElMessage.error('复用失败')
  }
}

async function handleExport(record: AIGenerateRecordItem) {
  exportingId.value = record.id
  try {
    const raw = await getAIRecordDetail(record.id)
    await exportRecordToWord(normalizeAIGenerateHistoryDetail(raw))
    ElMessage.success('Word 文档已下载')
  } catch {
    ElMessage.error('导出失败')
  } finally {
    exportingId.value = null
  }
}

async function handleExportDetail() {
  if (!detail.value) return
  exportingDetail.value = true
  try {
    await exportRecordToWord(detail.value)
    ElMessage.success('Word 文档已下载')
  } catch {
    ElMessage.error('导出失败')
  } finally {
    exportingDetail.value = false
  }
}

function getPreviewTitle(record: NormalizedAIGenerateHistoryRecord) {
  return record.displayTitle || record.candidate_titles?.[0] || record.source_title || '暂无标题'
}

function getPreviewSummary(record: NormalizedAIGenerateHistoryRecord) {
  return record.displaySummary || record.standardResult.summary_short || record.standardResult.summary_long || '暂无摘要'
}

function getSourceLabel(record: NormalizedAIGenerateHistoryRecord) {
  return getAIGenerateSourceLabel(record.displaySource, record.standardResult.generation_source)
}

function getSourceTagType(record: NormalizedAIGenerateHistoryRecord) {
  return getAIGenerateSourceTagType(record.displaySource, record.standardResult.generation_source)
}
</script>

<template>
  <div class="gh">
    <div class="gh__bar" v-if="mode === 'list' || mode === 'detail'">
      <div class="gh__bar-left">
        <template v-if="mode === 'list'">
          <el-button text size="default" class="gh__back-btn" @click="emit('back-to-input')">← 返回编辑</el-button>
          <span class="gh__count" v-if="records.length">{{ records.length }} 条记录</span>
        </template>
        <template v-if="mode === 'detail'">
          <el-button text size="default" class="gh__back-btn" @click="emit('back-to-list')">← 历史记录</el-button>
          <el-button text size="default" class="gh__back-btn" @click="emit('back-to-input')">← 返回编辑</el-button>
        </template>
      </div>
      <div class="gh__bar-right">
        <el-button
          v-if="mode === 'detail' && detail"
          size="small"
          type="primary"
          plain
          :icon="Download"
          :loading="exportingDetail"
          @click="handleExportDetail"
        >
          导出 Word
        </el-button>
      </div>
    </div>

    <template v-if="mode === 'list'">
      <el-skeleton v-if="listLoading" animated :rows="4" />
      <el-empty v-else-if="!records.length" description="暂无生成记录" />
      <div v-else class="gh__cards">
        <div v-for="record in records" :key="record.id" class="gh__card">
          <div class="gh__card-body">
            <div class="gh__card-head">
              <span class="gh__card-src">{{ getPreviewTitle(record) }}</span>
              <el-tag :type="record.risk_level === 'high' ? 'danger' : record.risk_level === 'medium' ? 'warning' : 'success'" size="small" effect="light">
                {{ record.risk_level === 'high' ? '高质量' : record.risk_level === 'medium' ? '中质量' : '低质量' }}
              </el-tag>
              <el-tag :type="getSourceTagType(record)" size="small" effect="light">
                {{ getSourceLabel(record) }}
              </el-tag>
            </div>
            <p class="gh__card-sum" v-if="getPreviewSummary(record)">{{ getPreviewSummary(record).slice(0, 120) }}</p>
            <div class="gh__card-titles" v-if="record.candidate_titles?.length">
              <span v-for="(title, index) in record.candidate_titles.slice(0, 2)" :key="index" class="gh__card-title">{{ title }}</span>
            </div>
            <div class="gh__card-extra" v-if="formatProviderModel(record.standardResult.provider, record.standardResult.model)">
              {{ formatProviderModel(record.standardResult.provider, record.standardResult.model) }}
            </div>
            <span class="gh__card-time">{{ record.created_at }}</span>
          </div>

          <div class="gh__card-acts">
            <el-button size="small" plain @click="emit('view-detail', record.id)">查看</el-button>
            <el-button size="small" plain @click="handleReuse(record)">复用</el-button>
            <el-button size="small" plain @click="handleExport(record)">下载</el-button>
            <el-button size="small" plain @click="handleDelete(record)">删除</el-button>
          </div>
        </div>
      </div>
    </template>

    <template v-if="mode === 'detail'">
      <el-skeleton v-if="detailLoading" animated :rows="8" />
      <el-alert v-else-if="detailError" :title="detailError" type="error" show-icon />
      <template v-else-if="detail">
        <!-- 标题头部卡片 -->
        <section class="ghd__hero">
          <div class="ghd__hero-row">
            <h1 class="ghd__hero-title">{{ detail.source_title || 'AI 生成结果' }}</h1>
            <div class="ghd__hero-badges">
              <el-tag
                :type="detail.risk_level === 'high' ? 'danger' : detail.risk_level === 'medium' ? 'warning' : 'success'"
                size="small" effect="dark" round
              >
                {{ detail.risk_level === 'high' ? '高质量' : detail.risk_level === 'medium' ? '中质量' : '低质量' }}
              </el-tag>
            </div>
          </div>
          <div class="ghd__hero-meta">
            <span v-if="formatProviderModel(detail.standardResult.provider, detail.standardResult.model)" class="ghd__hero-meta-item">
              {{ formatProviderModel(detail.standardResult.provider, detail.standardResult.model) }}
            </span>
            <span class="ghd__hero-meta-item">{{ detail.created_at }}</span>
            <span class="ghd__hero-meta-item">{{ detail.title_count ?? detail.params?.title_count ?? '—' }} 个标题</span>
          </div>
        </section>

        <div class="ghd__grid">
          <!-- 原文 -->
          <section class="ghd__card">
            <h3 class="ghd__card-title">原文</h3>
            <template v-if="detail.input_text">
              <p class="ghd__card-text">{{ sourceExpanded ? detail.input_text : detail.input_text.slice(0, 200) + (detail.input_text.length > 200 ? '…' : '') }}</p>
              <el-button
                v-if="detail.input_text.length > 200"
                class="ghd__card-expand"
                type="text"
                @click="sourceExpanded = !sourceExpanded"
              >
                {{ sourceExpanded ? '收起' : ' 展开全部（共 ' + detail.input_text.length + ' 字）' }}
              </el-button>
            </template>
            <p v-else class="ghd__card-text ghd__card-text--empty">暂无原文内容</p>
          </section>

          <!-- 生成参数 -->
          <section class="ghd__card">
            <h3 class="ghd__card-title">生成参数</h3>
            <div class="ghd__kw-list">
              <el-tag type="info" round>标题数 {{ detail.params.title_count ?? '无' }}</el-tag>
              <el-tag type="info" round>{{ detail.params.summary_type === 'extract' ? '抽取式' : detail.params.summary_type === 'generate' ? '生成式' : '无' }}</el-tag>
              <el-tag type="info" round>{{ detail.params.title_style || '默认' }}</el-tag>
              <el-tag type="info" round>{{ detail.params.summary_style || '默认' }}</el-tag>
              <el-tag type="info" round>{{ detail.params.summary_length === 'short' ? '短摘要' : detail.params.summary_length === 'long' ? '长摘要' : '短+长' }}</el-tag>
            </div>
          </section>

          <!-- 候选标题 -->
          <section class="ghd__card" v-if="detail.standardResult.candidate_titles.length">
            <h3 class="ghd__card-title">候选标题</h3>
            <div class="ghd__titles">
              <div v-for="(title, index) in detail.standardResult.candidate_titles" :key="index" class="ghd__title-row">
                <span class="ghd__title-num">{{ index + 1 }}</span>
                <span class="ghd__title-text">{{ title }}</span>
              </div>
            </div>
          </section>

          <!-- 短摘要 -->
          <section class="ghd__card" v-if="detail.standardResult.summary_short">
            <h3 class="ghd__card-title">短摘要</h3>
            <p class="ghd__card-text">{{ detail.standardResult.summary_short }}</p>
          </section>

          <!-- 长摘要 -->
          <section class="ghd__card" v-if="detail.standardResult.summary_long">
            <h3 class="ghd__card-title">长摘要</h3>
            <p class="ghd__card-text">{{ detail.standardResult.summary_long }}</p>
          </section>

          <!-- 摘要要点 -->
          <section class="ghd__card" v-if="detail.standardResult.summary_points.length">
            <h3 class="ghd__card-title">摘要要点</h3>
            <div class="ghd__points">
              <div v-for="(point, index) in detail.standardResult.summary_points" :key="index" class="ghd__point-row">
                <span class="ghd__point-dot"></span>
                <span>{{ point }}</span>
              </div>
            </div>
          </section>

          <!-- 关键词 -->
          <section class="ghd__card" v-if="detail.standardResult.keywords.length">
            <h3 class="ghd__card-title">关键词</h3>
            <div class="ghd__kw-list">
              <el-tag v-for="(keyword, index) in detail.standardResult.keywords" :key="index" size="default" type="info" round>
                {{ keyword }}
              </el-tag>
            </div>
          </section>

          <!-- 新闻六要素 -->
          <section class="ghd__card" v-if="detail.standardResult.elements && (detail.standardResult.elements.who || detail.standardResult.elements.what || detail.standardResult.elements.when || detail.standardResult.elements.where || detail.standardResult.elements.why || detail.standardResult.elements.how)">
            <h3 class="ghd__card-title">新闻六要素</h3>
            <div class="ghd__elements">
              <div class="ghd__el"><span class="ghd__el-k">人物</span><span class="ghd__el-v">{{ detail.standardResult.elements.who || '—' }}</span></div>
              <div class="ghd__el"><span class="ghd__el-k">事件</span><span class="ghd__el-v">{{ detail.standardResult.elements.what || '—' }}</span></div>
              <div class="ghd__el"><span class="ghd__el-k">时间</span><span class="ghd__el-v">{{ detail.standardResult.elements.when || '—' }}</span></div>
              <div class="ghd__el"><span class="ghd__el-k">地点</span><span class="ghd__el-v">{{ detail.standardResult.elements.where || '—' }}</span></div>
              <div class="ghd__el"><span class="ghd__el-k">原因</span><span class="ghd__el-v">{{ detail.standardResult.elements.why || '—' }}</span></div>
              <div class="ghd__el"><span class="ghd__el-k">方式</span><span class="ghd__el-v">{{ detail.standardResult.elements.how || '—' }}</span></div>
            </div>
          </section>
        </div>
      </template>
    </template>
  </div>
</template>

<style scoped>
.gh { max-width: 100%; }
.gh__bar { display: flex; align-items: center; gap: 8px; margin-bottom: 14px; flex-wrap: wrap; justify-content: space-between; }
.gh__bar-left { display: flex; align-items: center; gap: 8px; }
.gh__bar-right { display: flex; align-items: center; gap: 8px; flex-shrink: 0; }
.gh__back-btn { font-size: 15px; font-weight: 500; }
.gh__count { font-size: 14px; color: var(--color-text-secondary); }
.gh__cards { display: flex; flex-direction: column; gap: 10px; }
.gh__card {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: 10px;
  padding: 16px 18px;
  display: flex;
  flex-direction: row;
  align-items: stretch;
  gap: 16px;
}
.gh__card-body { flex: 1; min-width: 0; }
.gh__card-head { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; flex-wrap: wrap; }
.gh__card-src { font-size: 16px; font-weight: 600; color: var(--color-text-primary); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.gh__card-sum { margin: 0 0 6px; font-size: 14px; color: var(--color-text-secondary); line-height: 1.6; }
.gh__card-titles { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 6px; }
.gh__card-title { padding: 2px 10px; background: var(--color-bg-hover); border-radius: 4px; font-size: 13px; color: var(--color-text-secondary); }
.gh__card-extra { font-size: 12px; color: var(--color-text-secondary); margin-bottom: 6px; }
.gh__card-time { font-size: 12px; color: var(--color-text-muted); }
.gh__card-acts { display: flex; flex-direction: column; gap: 8px; flex-shrink: 0; width: 80px; }
.gh__card-acts .el-button { width: 100%; margin-left: 0; }
/* ===== Detail: Hero Header ===== */
.ghd__hero {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: 14px;
  padding: 22px 28px;
  margin-bottom: 20px;
}
.ghd__hero-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 10px;
}
.ghd__hero-title {
  margin: 0;
  font-size: 17px;
  font-weight: 600;
  color: var(--color-text-primary);
  line-height: 1.5;
  flex: 1;
  min-width: 0;
}
.ghd__hero-badges {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
  flex-wrap: wrap;
}
.ghd__hero-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 4px 14px;
  font-size: 12px;
  color: var(--color-text-muted);
}
.ghd__hero-meta-item {
  display: inline-flex;
  align-items: center;
  gap: 3px;
}

/* ===== Detail: Card Grid ===== */
.ghd__grid {
  display: flex;
  flex-direction: column;
  gap: 18px;
}
.ghd__card {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: 14px;
  padding: 20px 24px;
  transition: border-color 0.15s;
}
.ghd__card:hover {
  border-color: var(--color-primary-light);
}
.ghd__card-title {
  margin: 0 0 14px;
  font-size: 16px;
  font-weight: 700;
  color: var(--color-text-primary);
  display: flex;
  align-items: center;
  gap: 8px;
}

.ghd__card-text {
  margin: 0;
  font-size: 14px;
  line-height: 1.8;
  color: var(--color-text-secondary);
  white-space: pre-line;
}
.ghd__card-text--empty {
  color: var(--color-text-muted);
  font-style: italic;
}
.ghd__card-expand {
  margin-top: 10px;
  padding: 4px 0;
  font-size: 13px;
  color: var(--color-primary);
  font-weight: 500;
}


/* ===== Detail: Titles ===== */
.ghd__titles {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.ghd__title-row {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px 14px;
  background: var(--color-bg-hover);
  border-radius: 10px;
  border-left: 3px solid var(--color-primary-light);
  transition: border-color 0.15s;
}
.ghd__title-row:hover {
  border-left-color: var(--color-primary);
}
.ghd__title-num {
  flex-shrink: 0;
  width: 24px;
  height: 24px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: var(--color-primary);
  color: #fff;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 700;
}
.ghd__title-text {
  flex: 1;
  font-size: 14px;
  line-height: 1.65;
  color: var(--color-text-primary);
  word-break: break-word;
}

/* ===== Detail: Points ===== */
.ghd__points {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.ghd__point-row {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  font-size: 14px;
  line-height: 1.7;
  color: var(--color-text-secondary);
}
.ghd__point-dot {
  flex-shrink: 0;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--color-primary);
  margin-top: 8px;
}

/* ===== Detail: Keywords ===== */
.ghd__kw-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

/* ===== Detail: Elements ===== */
.ghd__elements {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}
.ghd__el {
  display: flex;
  align-items: baseline;
  gap: 8px;
  padding: 12px 14px;
  background: var(--color-bg-hover);
  border-radius: 10px;
  font-size: 14px;
}
.ghd__el-k {
  font-weight: 700;
  color: var(--color-text-primary);
  flex-shrink: 0;
  font-size: 13px;
}
.ghd__el-v {
  color: var(--color-text-secondary);
  word-break: break-word;
}

/* ===== Responsive ===== */
@media (max-width: 900px) {
  .gh__card { flex-direction: column; }
  .gh__card-acts { width: 100%; flex-direction: row; flex-wrap: wrap; }
  .ghd__hero { padding: 16px; }
  .ghd__elements { grid-template-columns: 1fr; }
  .ghd__card { padding: 14px 16px; }
}
</style>
