<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAIDraftStore } from '@/stores/aiDraft'
import { useNewsEditorAgentStore } from '@/stores/newsEditorAgent'
import { useAIGenerateHistory } from '@/composables/useAIGenerateHistory'
import AIGenerateSidebar from './components/AIGenerateSidebar.vue'
import type { AIGenerateRecordItem } from '@/api/ai'
import {
  formatProviderModel,
  getAIGenerateSourceLabel,
  getAIGenerateSourceTagType,
  type NormalizedAIGenerateHistoryRecord,
} from '@/utils/normalizeAIGenerateResult'

const router = useRouter()
const aiDraft = useAIDraftStore()
const agentStore = useNewsEditorAgentStore()

const {
  historyRecords,
  loading,
  showExportDialog,
  selectedExportFormat,
  loadHistory,
  loadRecordDetail,
  deleteRecord,
  openExportDialog,
  confirmExport,
  getRiskLevelType,
  formatDate,
} = useAIGenerateHistory()

onMounted(() => {
  loadHistory()
})

function handleViewDetail(record: AIGenerateRecordItem) {
  router.push(`/ai-generate/history/${record.id}`)
}

async function handleReuse(record: AIGenerateRecordItem) {
  const detail = await loadRecordDetail(record.id)
  if (!detail) return

  aiDraft.clearSourceNews()
  aiDraft.clearResult()
  aiDraft.setInputText(detail.input_text)
  aiDraft.setParams(detail.params)
  agentStore.clearExecutionState()
  ElMessage.success('已复用历史输入，正在跳转生成页')
  router.push('/ai-generate')
}

async function handleDelete(record: AIGenerateRecordItem) {
  await deleteRecord(record)
}

function handleExport(record: AIGenerateRecordItem) {
  openExportDialog(record)
}

function getPreviewTitle(record: NormalizedAIGenerateHistoryRecord): string {
  return record.displayTitle || record.candidate_titles?.[0] || record.source_title || '暂无标题'
}

function getPreviewSummary(record: NormalizedAIGenerateHistoryRecord): string {
  return record.displaySummary || record.standardResult.summary_short || record.standardResult.summary_long || '暂无摘要'
}

function getSourceLabel(record: NormalizedAIGenerateHistoryRecord): string {
  return getAIGenerateSourceLabel(record.displaySource, record.standardResult.generation_source)
}

function getSourceTagType(record: NormalizedAIGenerateHistoryRecord) {
  return getAIGenerateSourceTagType(record.displaySource, record.standardResult.generation_source)
}
</script>

<template>
  <main class="history-page">
    <header class="page-header">
      <div class="header-text">
        <h1>AI 生成历史</h1>
        <p>查看和管理所有生成记录</p>
      </div>
    </header>

    <div class="main-content">
      <aside class="sidebar">
        <AIGenerateSidebar />
      </aside>

      <div class="main-area">
        <div class="history-toolbar">
          <span class="record-count">共 {{ historyRecords.length }} 条记录</span>
          <el-button size="small" @click="loadHistory" :loading="loading">刷新</el-button>
        </div>

        <div v-if="!loading && historyRecords.length === 0" class="empty-state">
          <span class="empty-icon">🗂</span>
          <p class="empty-text">暂无生成记录</p>
          <p class="empty-desc">生成标题和摘要后，记录会显示在这里</p>
          <el-button type="primary" @click="router.push('/ai-generate')">去生成</el-button>
        </div>

        <div v-if="loading" class="loading-state">
          <el-icon class="is-loading"><svg viewBox="0 0 1024 1024" width="1em" height="1em"><path d="M512 64a32 32 0 0 1 32 32v192a32 32 0 0 1-64 0V96a32 32 0 0 1 32-32z m0 640a32 32 0 0 1 32 32v192a32 32 0 1 1-64 0v-192a32 32 0 0 1 32-32z m448-192a32 32 0 0 1-32 32h-192a32 32 0 0 1 0-64h192a32 32 0 0 1 32 32zM320 512a32 32 0 0 1-32 32h-192a32 32 0 0 1 0-64h192a32 32 0 0 1 32 32z"/></svg></el-icon>
          <span>加载中...</span>
        </div>

        <div v-if="!loading && historyRecords.length > 0" class="history-list">
          <div
            v-for="record in historyRecords"
            :key="record.id"
            class="history-card"
            @click="handleViewDetail(record)"
          >
            <div class="card-body">
              <div class="card-main">
                <div class="card-ai-title">{{ getPreviewTitle(record) }}</div>
                <div class="card-source-title">{{ record.source_title || '暂无来源标题' }}</div>
                <div class="card-summary">{{ getPreviewSummary(record) }}</div>
                <div class="card-meta">
                  <el-tag :type="getRiskLevelType(record.risk_level)" size="small">
                    {{ record.risk_level === 'high' ? '高质量' : record.risk_level === 'medium' ? '中质量' : '低质量' }}
                  </el-tag>
                  <el-tag :type="getSourceTagType(record)" size="small">
                    {{ getSourceLabel(record) }}
                  </el-tag>
                  <span v-if="formatProviderModel(record.standardResult.provider, record.standardResult.model)" class="meta-text">
                    {{ formatProviderModel(record.standardResult.provider, record.standardResult.model) }}
                  </span>
                  <span class="meta-text">{{ record.source === 'manual' ? '手动输入' : '新闻导入' }}</span>
                  <span class="meta-text">{{ record.title_count }} 个标题</span>
                  <span class="meta-text">{{ formatDate(record.created_at) }}</span>
                </div>
              </div>

              <div class="card-actions" @click.stop>
                <el-button type="text" size="small" @click="handleViewDetail(record)">查看</el-button>
                <el-button type="text" size="small" @click="handleReuse(record)">复用</el-button>
                <el-button type="text" size="small" @click="handleExport(record)">下载</el-button>
                <el-button type="text" size="small" class="btn-delete" @click="handleDelete(record)">删除</el-button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <el-dialog
      v-model="showExportDialog"
      title="选择下载格式"
      width="400px"
      class="export-dialog"
    >
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
.history-page {
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
  box-shadow: 0 4px 24px rgba(217, 45, 32, 0.06);
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
  gap: 16px;
}

.history-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: var(--color-bg-card);
  border-radius: 10px;
  border: 1px solid var(--color-border);
}

.record-count {
  font-size: 13px;
  color: var(--color-text-secondary);
}

.empty-state,
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 60px 20px;
  text-align: center;
  background: var(--color-bg-card);
  border-radius: 10px;
  border: 1px solid var(--color-border);
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

.history-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.history-card {
  background: var(--color-bg-card);
  border-radius: 10px;
  border: 1px solid var(--color-border);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  cursor: pointer;
}

.card-body {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  gap: 16px;
}

.card-main {
  flex: 1;
  min-width: 0;
}

.card-ai-title,
.card-source-title,
.card-summary {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.card-ai-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: 6px;
}

.card-source-title {
  font-size: 13px;
  color: var(--color-text-secondary);
  margin-bottom: 6px;
}

.card-summary {
  font-size: 13px;
  color: var(--color-text-secondary);
  margin-bottom: 10px;
}

.card-meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.meta-text {
  font-size: 12px;
  color: var(--color-text-muted);
}

.card-actions {
  display: flex;
  gap: 4px;
  flex-shrink: 0;
}

.card-actions :deep(.el-button) {
  padding: 4px 10px;
  font-size: 12px;
  color: var(--color-text-secondary);
}

.card-actions :deep(.el-button:hover) {
  color: var(--color-primary);
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
  border-color: var(--color-primary);
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

  .card-body {
    flex-direction: column;
    align-items: flex-start;
  }

  .card-actions {
    align-self: flex-end;
  }
}
</style>
