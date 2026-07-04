<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAIDraftStore } from '@/stores/aiDraft'
import { useNewsEditorAgentStore } from '@/stores/newsEditorAgent'
import { useAIGenerateHistory } from '@/composables/useAIGenerateHistory'
import AIGenerateSidebar from './components/AIGenerateSidebar.vue'
import AIResultPanel from '@/components/ai/AIResultPanel.vue'
import type { AIGenerateRecordDetail } from '@/api/ai'
import {
  formatProviderModel,
  getAIGenerateSourceLabel,
  getAIGenerateSourceTagType,
  normalizeAIGenerateHistoryDetail,
} from '@/utils/normalizeAIGenerateResult'

const route = useRoute()
const router = useRouter()
const aiDraft = useAIDraftStore()
const agentStore = useNewsEditorAgentStore()

const {
  showExportDialog,
  selectedExportFormat,
  loadRecordDetail,
  deleteRecord,
  openExportDialog,
  confirmExport,
  getRiskLevelType,
  formatDate,
} = useAIGenerateHistory()

const detail = ref<AIGenerateRecordDetail | null>(null)
const loading = ref(false)
const notFound = ref(false)
const detailRiskLevel = computed(() => {
  const result = normalizedDetail.value?.standardResult
  if (!result) return undefined
  return result.has_consistency
    ? result.consistency?.risk_level
    : result.risk_level
})

onMounted(async () => {
  const id = route.params.id as string
  if (!id) {
    notFound.value = true
    return
  }

  loading.value = true
  const result = await loadRecordDetail(id)
  loading.value = false

  if (!result) {
    notFound.value = true
    return
  }
  detail.value = result
})

const normalizedDetail = computed(() => (detail.value ? normalizeAIGenerateHistoryDetail(detail.value) : null))

function handleReuse() {
  if (!detail.value) return
  aiDraft.clearSourceNews()
  aiDraft.clearResult()
  aiDraft.setInputText(detail.value.input_text)
  aiDraft.setParams(detail.value.params)
  agentStore.clearExecutionState()
  ElMessage.success('已复用历史输入，正在跳转生成页')
  router.push('/ai-generate')
}

async function handleDelete() {
  if (!detail.value) return
  const record = {
    id: detail.value.id,
    source: detail.value.source,
    source_news_id: detail.value.source_news_id,
    source_title: detail.value.source_title,
    title_count: detail.value.params?.title_count ?? 0,
    risk_level: detailRiskLevel.value ?? 'low',
    ai_source: detail.value.result?.generation_source || detail.value.result?.source,
    created_at: detail.value.created_at,
  }
  const success = await deleteRecord(record)
  if (success) {
    router.push('/ai-generate/history')
  }
}

function handleExport() {
  if (!detail.value) return
  openExportDialog({
    id: detail.value.id,
    source: detail.value.source,
    source_news_id: detail.value.source_news_id,
    source_title: detail.value.source_title,
    title_count: detail.value.params?.title_count ?? 0,
    risk_level: detailRiskLevel.value ?? 'low',
    ai_source: detail.value.result?.generation_source || detail.value.result?.source,
    created_at: detail.value.created_at,
  })
}

function getSourceLabel() {
  return getAIGenerateSourceLabel(normalizedDetail.value?.result?.generation_source, normalizedDetail.value?.result?.generation_source)
}

function getSourceTagType() {
  return getAIGenerateSourceTagType(normalizedDetail.value?.result?.generation_source, normalizedDetail.value?.result?.generation_source)
}
</script>

<template>
  <main class="detail-page">
    <header class="page-header">
      <div class="header-text">
        <h1>历史记录详情</h1>
        <p>查看生成结果的完整内容</p>
      </div>
    </header>

    <div class="main-content">
      <aside class="sidebar">
        <AIGenerateSidebar />
      </aside>

      <div class="main-area">
        <div v-if="loading" class="loading-state">
          <el-icon class="is-loading"><svg viewBox="0 0 1024 1024" width="1em" height="1em"><path d="M512 64a32 32 0 0 1 32 32v192a32 32 0 0 1-64 0V96a32 32 0 0 1 32-32z m0 640a32 32 0 0 1 32 32v192a32 32 0 1 1-64 0v-192a32 32 0 0 1 32-32z m448-192a32 32 0 0 1-32 32h-192a32 32 0 0 1 0-64h192a32 32 0 0 1 32 32zM320 512a32 32 0 0 1-32 32h-192a32 32 0 0 1 0-64h192a32 32 0 0 1 32 32z"/></svg></el-icon>
          <span>加载中...</span>
        </div>

        <div v-else-if="notFound" class="empty-state">
          <span class="empty-icon">🔍</span>
          <p class="empty-text">记录不存在</p>
          <p class="empty-desc">该历史记录可能已被删除</p>
          <el-button type="primary" @click="router.push('/ai-generate/history')">返回列表</el-button>
        </div>

        <template v-else-if="detail">
          <div class="action-bar">
            <el-button @click="router.push('/ai-generate/history')">← 返回列表</el-button>
            <div class="action-right">
              <el-button @click="handleReuse">复用此输入</el-button>
              <el-button @click="handleExport">下载</el-button>
              <el-button @click="handleDelete">删除</el-button>
            </div>
          </div>

          <section class="info-section">
            <div class="info-header">
              <h2>{{ detail.source_title || '暂无标题' }}</h2>
              <div class="info-tags">
                <el-tag v-if="detailRiskLevel" :type="getRiskLevelType(detailRiskLevel)" size="small">
                  {{ detailRiskLevel === 'low' ? '低质量' : detailRiskLevel === 'medium' ? '中质量' : '高质量' }}
                </el-tag>
                <el-tag :type="getSourceTagType()" size="small">
                  {{ getSourceLabel() }}
                </el-tag>
                <span v-if="formatProviderModel(normalizedDetail?.result?.provider, normalizedDetail?.result?.model)" class="provider-model">
                  {{ formatProviderModel(normalizedDetail?.result?.provider, normalizedDetail?.result?.model) }}
                </span>
              </div>
            </div>
            <div class="info-meta">
              <span>来源：{{ detail.source === 'manual' ? '手动输入' : '新闻导入' }}</span>
              <span>创建时间：{{ formatDate(detail.created_at) }}</span>
            </div>
          </section>

          <section class="content-section">
            <h3 class="section-title">输入文本</h3>
            <div class="text-block">{{ detail.input_text || '暂无输入内容' }}</div>
          </section>

          <section class="content-section">
            <h3 class="section-title">生成参数</h3>
            <div class="params-grid">
              <div class="param-item">
                <span class="param-label">标题数量</span>
                <span class="param-value">{{ detail.params?.title_count ?? '无' }}</span>
              </div>
              <div class="param-item">
                <span class="param-label">摘要类型</span>
                <span class="param-value">{{ detail.params?.summary_type === 'extract' ? '抽取式' : detail.params?.summary_type === 'generate' ? '生成式' : '无' }}</span>
              </div>
              <div class="param-item">
                <span class="param-label">标题风格</span>
                <span class="param-value">{{ detail.params?.title_style || '无' }}</span>
              </div>
              <div class="param-item">
                <span class="param-label">摘要风格</span>
                <span class="param-value">{{ detail.params?.summary_style || '无' }}</span>
              </div>
              <div class="param-item">
                <span class="param-label">摘要长度</span>
                <span class="param-value">
                  {{ detail.params?.summary_length === 'short' ? '短摘要' : detail.params?.summary_length === 'long' ? '长摘要' : '短摘要+长摘要' }}
                </span>
              </div>
            </div>
          </section>

          <section class="content-section">
            <h3 class="section-title">生成结果</h3>
            <AIResultPanel :has-result="true" :override-result="normalizedDetail?.standardResult ?? null" />
          </section>
        </template>
      </div>
    </div>

    <el-dialog v-model="showExportDialog" title="选择下载格式" width="400px" class="export-dialog">
      <div class="export-format-list">
        <div
          v-for="format in ['txt', 'docx', 'pdf']"
          :key="format"
          class="format-item"
          :class="{ selected: selectedExportFormat === format }"
          @click="selectedExportFormat = format"
        >
          <div class="format-icon">{{ format === 'txt' ? 'TXT' : format === 'docx' ? 'DOC' : 'PDF' }}</div>
          <div class="format-info">
            <div class="format-name">{{ format === 'txt' ? 'TXT 文本' : format === 'docx' ? 'Word 文档' : 'PDF 文档' }}</div>
            <div class="format-desc">{{ format === 'txt' ? '纯文本，便于编辑' : format === 'docx' ? '支持排版样式' : '适合打印分享' }}</div>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="showExportDialog = false">取消</el-button>
        <el-button type="primary" @click="confirmExport" :disabled="!selectedExportFormat">确定</el-button>
      </template>
    </el-dialog>
  </main>
</template>

<style scoped>
.detail-page {
  padding: 0;
  min-height: calc(100vh - 120px);
  display: flex;
  flex-direction: column;
}

.page-header {
  background: var(--color-bg-card);
  border: 1px solid var(--color-primary-light);
  border-radius: 22px;
  padding: 32px 40px;
  margin-bottom: 24px;
}

.header-text h1 {
  margin: 0;
  font-size: 26px;
  font-weight: 700;
  color: var(--color-text-primary);
}

.header-text p {
  margin: 6px 0 0;
  font-size: 14px;
  color: var(--color-text-secondary);
}

.main-content {
  padding: 0 24px 24px;
  display: flex;
  gap: 24px;
  flex: 1;
}

.sidebar {
  width: 220px;
  flex-shrink: 0;
  position: sticky;
  top: 0;
  align-self: flex-start;
}

.main-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.action-bar,
.info-section,
.content-section,
.loading-state,
.empty-state {
  background: var(--color-bg-card);
  border-radius: 10px;
  border: 1px solid var(--color-border);
}

.action-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
}

.action-right {
  display: flex;
  gap: 8px;
}

.info-section,
.content-section {
  padding: 20px 24px;
}

.info-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.info-header h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text-primary);
  flex: 1;
}

.info-tags {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  align-items: center;
}

.provider-model {
  font-size: 12px;
  color: var(--color-text-secondary);
}

.info-meta {
  display: flex;
  gap: 20px;
  font-size: 13px;
  color: var(--color-text-secondary);
  flex-wrap: wrap;
}

.section-title {
  margin: 0 0 14px;
  font-size: 16px;
  font-weight: 700;
  color: var(--color-text-primary);
}

.text-block {
  font-size: 14px;
  line-height: 1.8;
  color: var(--color-text-primary);
  white-space: pre-wrap;
  word-break: break-word;
  padding: 14px;
  background-color: var(--color-bg-hover);
  border-radius: 8px;
  border: 1px solid var(--color-border);
}

.params-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 12px;
}

.param-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 10px 14px;
  background-color: var(--color-bg-hover);
  border-radius: 8px;
  border: 1px solid var(--color-border);
}

.param-label {
  font-size: 12px;
  color: var(--color-text-secondary);
  font-weight: 500;
}

.param-value {
  font-size: 14px;
  color: var(--color-text-primary);
  font-weight: 600;
}

.loading-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 60px 20px;
  text-align: center;
  color: var(--color-text-secondary);
}

.empty-icon {
  font-size: 48px;
}

.empty-text {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.empty-desc {
  margin: 0;
  font-size: 14px;
  color: var(--color-text-secondary);
}

.export-dialog :deep(.el-dialog__body) {
  padding: 16px;
}

.export-format-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.format-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-radius: 6px;
  cursor: pointer;
  background-color: var(--color-bg-hover);
  border: 1px solid transparent;
}

.format-item.selected {
  border-color: #ff4d4f;
  background-color: var(--color-primary-soft);
}

.format-icon {
  font-size: 24px;
}

.format-info {
  flex: 1;
}

.format-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-primary);
}

.format-desc {
  font-size: 12px;
  color: var(--color-text-secondary);
  margin-top: 2px;
}

@media (max-width: 900px) {
  .main-content {
    flex-direction: column;
  }

  .sidebar {
    width: 100%;
    position: static;
  }

  .action-bar {
    flex-direction: column;
    gap: 8px;
  }

  .action-right {
    width: 100%;
    justify-content: flex-end;
  }
}
</style>
