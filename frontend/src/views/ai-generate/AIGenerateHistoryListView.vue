<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAIDraftStore } from '@/stores/aiDraft'
import { useAIGenerateHistory } from '@/composables/useAIGenerateHistory'
import AIGenerateSidebar from './components/AIGenerateSidebar.vue'
import type { AIGenerateRecordItem } from '@/api/ai'

const router = useRouter()
const aiDraft = useAIDraftStore()

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

/** 跳转到历史详情页 */
function handleViewDetail(record: AIGenerateRecordItem) {
  router.push(`/ai-generate/history/${record.id}`)
}

/** 复用历史输入 → 跳回生成页并载入内容 */
async function handleReuse(record: AIGenerateRecordItem) {
  const detail = await loadRecordDetail(record.id)
  if (!detail) return

  aiDraft.setInputText(detail.input_text)
  aiDraft.setParams(detail.params)
  ElMessage.success('已复用历史输入，正在跳转生成页')
  router.push('/ai-generate')
}

/** 删除 */
async function handleDelete(record: AIGenerateRecordItem) {
  await deleteRecord(record)
}

/** 导出 */
function handleExport(record: AIGenerateRecordItem) {
  openExportDialog(record)
}

/** 列表项首标题 */
function getFirstTitle(record: AIGenerateRecordItem): string {
  if (Array.isArray(record.candidate_titles) && record.candidate_titles.length > 0) {
    return record.candidate_titles[0]
  }
  return ''
}
</script>

<template>
  <main class="history-page">
    <header class="page-header">
      <div class="header-content">
        <div class="header-text">
          <h1>AI 生成历史</h1>
          <p>查看和管理所有历史生成记录</p>
        </div>
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

        <!-- 空状态 -->
        <div v-if="!loading && historyRecords.length === 0" class="empty-state">
          <span class="empty-icon">📭</span>
          <p class="empty-text">暂无生成记录</p>
          <p class="empty-desc">生成标题和摘要后，记录将显示在这里</p>
          <el-button type="primary" @click="router.push('/ai-generate')">去生成</el-button>
        </div>

        <!-- 加载中 -->
        <div v-if="loading" class="loading-state">
          <el-icon class="is-loading"><svg viewBox="0 0 1024 1024" width="1em" height="1em"><path d="M512 64a32 32 0 0 1 32 32v192a32 32 0 0 1-64 0V96a32 32 0 0 1 32-32z m0 640a32 32 0 0 1 32 32v192a32 32 0 1 1-64 0v-192a32 32 0 0 1 32-32z m448-192a32 32 0 0 1-32 32h-192a32 32 0 0 1 0-64h192a32 32 0 0 1 32 32zM320 512a32 32 0 0 1-32 32h-192a32 32 0 0 1 0-64h192a32 32 0 0 1 32 32z"/></svg></el-icon>
          <span>加载中...</span>
        </div>

        <!-- 历史列表 -->
        <div v-if="!loading && historyRecords.length > 0" class="history-list">
          <div
            v-for="record in historyRecords"
            :key="record.id"
            class="history-card"
            @click="handleViewDetail(record)"
          >
            <div class="card-body">
              <div class="card-main">
                <div v-if="getFirstTitle(record)" class="card-ai-title">
                  {{ getFirstTitle(record) }}
                </div>
                <div class="card-source-title">{{ record.source_title }}</div>
                <div class="card-meta">
                  <el-tag :type="getRiskLevelType(record.risk_level)" size="small">
                    {{ record.risk_level === 'low' ? '低风险' : record.risk_level === 'medium' ? '中风险' : '高风险' }}
                  </el-tag>
                  <el-tag
                    :type="record.ai_source === 'llm' ? 'success' : 'info'"
                    size="small"
                  >
                    {{ record.ai_source === 'llm' ? '真实AI' : 'Mock演示' }}
                  </el-tag>
                  <span class="meta-text">{{ record.source === 'manual' ? '手动输入' : '新闻导入' }}</span>
                  <span class="meta-text">{{ record.title_count }} 个标题</span>
                  <span class="meta-text">{{ formatDate(record.created_at) }}</span>
                </div>
              </div>

              <div class="card-actions" @click.stop>
                <el-button type="text" size="small" @click="handleViewDetail(record)">查看</el-button>
                <el-button type="text" size="small" @click="handleReuse(record)">复用</el-button>
                <el-button type="text" size="small" @click="handleExport(record)">导出</el-button>
                <el-button type="text" size="small" class="btn-delete" @click="handleDelete(record)">删除</el-button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 导出格式弹窗 -->
    <el-dialog
      v-model="showExportDialog"
      title="选择导出格式"
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
          <div class="format-icon">
            {{ format === 'txt' ? 'TXT' : format === 'docx' ? 'DOC' : 'PDF' }}
          </div>
          <div class="format-info">
            <div class="format-name">{{ format === 'txt' ? 'TXT 文本' : format === 'docx' ? 'Word 文档' : 'PDF 文档' }}</div>
            <div class="format-desc">{{ format === 'txt' ? '纯文本格式，便于编辑' : format === 'docx' ? '支持排版样式' : '适合打印分享' }}</div>
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
  border: 1px solid #f1d4d4;
  border-radius: 22px;
  padding: 32px 40px;
  margin-bottom: 24px;
  box-shadow: 0 4px 24px rgba(217, 45, 32, 0.06);
}

.header-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-text h1 {
  margin: 0;
  font-size: 26px;
  font-weight: 700;
  color: var(--color-text-primary);
  letter-spacing: -0.5px;
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
  border: 1px solid #f0f0f0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.record-count {
  font-size: 13px;
  color: var(--color-text-secondary);
}

/* 空状态 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 60px 20px;
  text-align: center;
  background: var(--color-bg-card);
  border-radius: 10px;
  border: 1px solid #f0f0f0;
}

.empty-icon {
  font-size: 48px;
}

.empty-text {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #374151;
}

.empty-desc {
  margin: 0;
  font-size: 14px;
  color: var(--color-text-secondary);
}

/* 加载中 */
.loading-state {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 60px 20px;
  color: var(--color-text-secondary);
  font-size: 14px;
  background: var(--color-bg-card);
  border-radius: 10px;
  border: 1px solid #f0f0f0;
}

/* 历史列表 */
.history-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.history-card {
  background: var(--color-bg-card);
  border-radius: 10px;
  border: 1px solid #f0f0f0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
  cursor: pointer;
}

.history-card:hover {
  border-color: #f1d4d4;
  box-shadow: 0 4px 16px rgba(217, 45, 32, 0.08);
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

.card-ai-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: 6px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.card-source-title {
  font-size: 13px;
  color: var(--color-text-secondary);
  margin-bottom: 10px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
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
  color: #d92d20;
}

.card-actions :deep(.btn-delete:hover) {
  color: #ef4444;
}

/* 导出弹窗 */
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
  border: 1px solid transparent;
  border-radius: 6px;
  cursor: pointer;
  transition: border-color 0.2s ease;
  background-color: var(--color-bg-hover);
}

.format-item:hover {
  border-color: #d1d5db;
}

.format-item.selected {
  border-color: #ff4d4f;
  background-color: #fff5f5;
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
  color: #374151;
}

.format-desc {
  font-size: 12px;
  color: var(--color-text-secondary);
  margin-top: 2px;
}

/* Element Plus 主题色覆盖 */
:deep(.el-button--primary) {
  --el-button-bg-color: #ff4d4f;
  --el-button-border-color: #ff4d4f;
  --el-button-hover-bg-color: #ff7875;
  --el-button-hover-border-color: #ff7875;
  --el-button-active-bg-color: #d9363e;
  --el-button-active-border-color: #d9363e;
}

:deep(.el-tag--primary) {
  --el-tag-bg-color: #fff5f5;
  --el-tag-border-color: #ffe4e4;
  --el-tag-text-color: #ff4d4f;
}

:deep(.el-tag--success) {
  --el-tag-bg-color: #f0fff4;
  --el-tag-border-color: #c6f6d5;
  --el-tag-text-color: #38a169;
}

:deep(.el-tag--warning) {
  --el-tag-bg-color: #fffaf0;
  --el-tag-border-color: #feebc8;
  --el-tag-text-color: #d69e2e;
}

:deep(.el-tag--danger) {
  --el-tag-bg-color: #fff5f5;
  --el-tag-border-color: #ffe4e4;
  --el-tag-text-color: #ff4d4f;
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
