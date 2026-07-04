<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Download } from '@element-plus/icons-vue'
import { useAIDraftStore } from '@/stores/aiDraft'
import { deleteAIRecord, getAIHistory, getAIRecordDetail, type AIGenerateRecordItem } from '@/api/ai'
import Step7AuditPanel from '@/components/agent/Step7AuditPanel.vue'
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
              <el-tag :type="record.risk_level === 'low' ? 'success' : record.risk_level === 'medium' ? 'warning' : 'danger'" size="small" effect="light">
                {{ record.risk_level === 'low' ? '低风险' : record.risk_level === 'medium' ? '中风险' : '高风险' }}
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
            <el-button size="small" type="primary" plain @click="emit('view-detail', record.id)">查看</el-button>
            <el-button size="small" plain @click="handleReuse(record)">复用</el-button>
            <el-button size="small" plain :icon="Download" :loading="exportingId === record.id" @click="handleExport(record)">下载</el-button>
            <el-button size="small" type="danger" plain @click="handleDelete(record)">删除</el-button>
          </div>
        </div>
      </div>
    </template>

    <template v-if="mode === 'detail'">
      <el-skeleton v-if="detailLoading" animated :rows="8" />
      <el-alert v-else-if="detailError" :title="detailError" type="error" show-icon />
      <template v-else-if="detail">
        <div class="gh__detail">
          <section class="gh__sec">
            <h3 class="gh__sec-title">输入原文</h3>
            <p class="gh__text">{{ detail.input_text || '暂无输入内容' }}</p>
          </section>

          <section class="gh__sec">
            <h3 class="gh__sec-title">生成参数</h3>
            <div class="gh__tags">
              <span class="gh__tag">标题 {{ detail.params.title_count ?? '无' }} 个</span>
              <span class="gh__tag">{{ detail.params.summary_type === 'extract' ? '抽取式' : detail.params.summary_type === 'generate' ? '生成式' : '无' }}</span>
              <span class="gh__tag">{{ detail.params.title_style || '无' }}</span>
              <span class="gh__tag">{{ detail.params.summary_style || '无' }}</span>
              <span class="gh__tag">
                {{ detail.params.summary_length === 'short' ? '短摘要' : detail.params.summary_length === 'long' ? '长摘要' : '短摘要+长摘要' }}
              </span>
            </div>
          </section>

          <section class="gh__sec" v-if="detail.standardResult.candidate_titles.length">
            <h3 class="gh__sec-title">候选标题</h3>
            <div class="gh__titles">
              <p v-for="(title, index) in detail.standardResult.candidate_titles" :key="index" class="gh__title-item">{{ index + 1 }}. {{ title }}</p>
            </div>
          </section>

          <section class="gh__sec" v-if="detail.standardResult.summary_short">
            <h3 class="gh__sec-title">短摘要</h3>
            <p class="gh__text">{{ detail.standardResult.summary_short }}</p>
          </section>

          <section class="gh__sec" v-if="detail.standardResult.summary_long">
            <h3 class="gh__sec-title">长摘要</h3>
            <p class="gh__text">{{ detail.standardResult.summary_long }}</p>
          </section>

          <section class="gh__sec" v-if="detail.standardResult.summary_points.length">
            <h3 class="gh__sec-title">摘要要点</h3>
            <div class="gh__titles">
              <p v-for="(point, index) in detail.standardResult.summary_points" :key="index" class="gh__title-item">{{ index + 1 }}. {{ point }}</p>
            </div>
          </section>

          <section class="gh__sec" v-if="detail.standardResult.keywords.length">
            <h3 class="gh__sec-title">关键词</h3>
            <div class="gh__tags">
              <el-tag v-for="(keyword, index) in detail.standardResult.keywords" :key="index" size="small" :type="index === 0 ? '' : 'info'">
                {{ keyword }}
              </el-tag>
            </div>
          </section>

          <section class="gh__sec" v-if="detail.standardResult.elements && (detail.standardResult.elements.who || detail.standardResult.elements.what || detail.standardResult.elements.when || detail.standardResult.elements.where || detail.standardResult.elements.why || detail.standardResult.elements.how)">
            <h3 class="gh__sec-title">新闻六要素</h3>
            <div class="gh__elements">
              <div class="gh__el"><span class="gh__el-k">人物</span><span>{{ detail.standardResult.elements.who || '无' }}</span></div>
              <div class="gh__el"><span class="gh__el-k">事件</span><span>{{ detail.standardResult.elements.what || '无' }}</span></div>
              <div class="gh__el"><span class="gh__el-k">时间</span><span>{{ detail.standardResult.elements.when || '无' }}</span></div>
              <div class="gh__el"><span class="gh__el-k">地点</span><span>{{ detail.standardResult.elements.where || '无' }}</span></div>
              <div class="gh__el"><span class="gh__el-k">原因</span><span>{{ detail.standardResult.elements.why || '无' }}</span></div>
              <div class="gh__el"><span class="gh__el-k">方式</span><span>{{ detail.standardResult.elements.how || '无' }}</span></div>
            </div>
          </section>

          <section class="gh__sec" v-if="detail.standardResult.has_consistency">
            <h3 class="gh__sec-title">一致性检查</h3>
            <Step7AuditPanel :consistency-data="detail.standardResult.consistency" />
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
.gh__card-title { padding: 2px 10px; background: #f3f4f6; border-radius: 4px; font-size: 13px; color: #6b7280; }
.gh__card-extra { font-size: 12px; color: #6b7280; margin-bottom: 6px; }
.gh__card-time { font-size: 12px; color: #9ca3af; }
.gh__card-acts { display: flex; flex-direction: column; gap: 8px; flex-shrink: 0; width: 80px; }
.gh__card-acts .el-button { width: 100%; margin-left: 0; }
.gh__detail { display: flex; flex-direction: column; gap: 14px; }
.gh__sec { background: var(--color-bg-card); border: 1px solid var(--color-border); border-radius: 10px; padding: 16px 20px; }
.gh__sec-title { margin: 0 0 8px; font-size: 15px; font-weight: 600; color: var(--color-text-primary); }
.gh__text { margin: 0; font-size: 14px; line-height: 1.75; color: var(--color-text-secondary); white-space: pre-line; }
.gh__tags { display: flex; flex-wrap: wrap; gap: 6px; }
.gh__tag { padding: 3px 10px; background: #f3f4f6; border-radius: 6px; font-size: 13px; color: #6b7280; }
.gh__titles { display: flex; flex-direction: column; gap: 4px; }
.gh__title-item { margin: 0; padding: 6px 10px; background: #f9fafb; border-radius: 6px; font-size: 14px; color: var(--color-text-primary); }
.gh__elements { display: grid; grid-template-columns: 1fr 1fr; gap: 6px; }
.gh__el { font-size: 14px; color: var(--color-text-secondary); display: flex; gap: 6px; }
.gh__el-k { font-weight: 600; color: var(--color-text-primary); flex-shrink: 0; min-width: 32px; }
@media (max-width: 900px) {
  .gh__card { flex-direction: column; }
  .gh__card-acts { width: 100%; flex-direction: row; flex-wrap: wrap; }
}
</style>
