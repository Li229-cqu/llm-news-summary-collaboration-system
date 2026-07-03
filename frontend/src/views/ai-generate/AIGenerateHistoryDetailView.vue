<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAIDraftStore } from '@/stores/aiDraft'
import { useAIGenerateHistory } from '@/composables/useAIGenerateHistory'
import AIGenerateSidebar from './components/AIGenerateSidebar.vue'
import AIResultPanel from '@/components/ai/AIResultPanel.vue'
import type { AIGenerateRecordDetail } from '@/api/ai'

const route = useRoute()
const router = useRouter()
const aiDraft = useAIDraftStore()

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

/** 复用 → 跳回生成页 */
function handleReuse() {
  if (!detail.value) return
  aiDraft.setInputText(detail.value.input_text)
  aiDraft.setParams(detail.value.params)
  ElMessage.success('已复用历史输入，正在跳转生成页')
  router.push('/ai-generate')
}

/** 删除后返回列表 */
async function handleDelete() {
  if (!detail.value) return
  const record = {
    id: detail.value.id,
    source: detail.value.source,
    source_news_id: detail.value.source_news_id,
    source_title: detail.value.source_title,
    title_count: detail.value.params?.title_count ?? 0,
    risk_level: detail.value.result?.consistency?.risk_level ?? 'low',
    ai_source: detail.value.result?.source,
    created_at: detail.value.created_at,
  }
  const success = await deleteRecord(record)
  if (success) {
    router.push('/ai-generate/history')
  }
}

/** 导出 */
function handleExport() {
  if (!detail.value) return
  openExportDialog({
    id: detail.value.id,
    source: detail.value.source,
    source_news_id: detail.value.source_news_id,
    source_title: detail.value.source_title,
    title_count: detail.value.params?.title_count ?? 0,
    risk_level: detail.value.result?.consistency?.risk_level ?? 'low',
    ai_source: detail.value.result?.source,
    created_at: detail.value.created_at,
  })
}
</script>

<template>
  <main class="detail-page">
    <header class="page-header">
      <div class="header-content">
        <div class="header-text">
          <h1>历史记录详情</h1>
          <p>查看生成结果的完整内容</p>
        </div>
      </div>
    </header>

    <div class="main-content">
      <aside class="sidebar">
        <AIGenerateSidebar />
      </aside>

      <div class="main-area">
        <!-- 加载中 -->
        <div v-if="loading" class="loading-state">
          <el-icon class="is-loading"><svg viewBox="0 0 1024 1024" width="1em" height="1em"><path d="M512 64a32 32 0 0 1 32 32v192a32 32 0 0 1-64 0V96a32 32 0 0 1 32-32z m0 640a32 32 0 0 1 32 32v192a32 32 0 1 1-64 0v-192a32 32 0 0 1 32-32z m448-192a32 32 0 0 1-32 32h-192a32 32 0 0 1 0-64h192a32 32 0 0 1 32 32zM320 512a32 32 0 0 1-32 32h-192a32 32 0 0 1 0-64h192a32 32 0 0 1 32 32z"/></svg></el-icon>
          <span>加载中...</span>
        </div>

        <!-- 未找到 -->
        <div v-else-if="notFound" class="empty-state">
          <span class="empty-icon">🔍</span>
          <p class="empty-text">记录不存在</p>
          <p class="empty-desc">该历史记录可能已被删除</p>
          <el-button type="primary" @click="router.push('/ai-generate/history')">返回列表</el-button>
        </div>

        <!-- 详情内容 -->
        <template v-else-if="detail">
          <!-- 操作栏 -->
          <div class="action-bar">
            <el-button @click="router.push('/ai-generate/history')">
              ← 返回列表
            </el-button>
            <div class="action-right">
              <el-button type="primary" @click="handleReuse">复用此输入</el-button>
              <el-button @click="handleExport">导出</el-button>
              <el-button class="btn-delete" @click="handleDelete">删除</el-button>
            </div>
          </div>

          <!-- 基本信息 -->
          <section class="info-section">
            <div class="info-header">
              <h2>{{ detail.source_title }}</h2>
              <div class="info-tags">
                <el-tag :type="getRiskLevelType(detail.result?.consistency?.risk_level ?? 'low')" size="small">
                  {{ (detail.result?.consistency?.risk_level ?? 'low') === 'low' ? '低风险' : (detail.result?.consistency?.risk_level ?? 'low') === 'medium' ? '中风险' : '高风险' }}
                </el-tag>
                <el-tag
                  :type="detail.result?.source === 'llm' ? 'success' : 'info'"
                  size="small"
                >
                  {{ detail.result?.source === 'llm' ? '真实AI' : 'Mock演示' }}
                </el-tag>
              </div>
            </div>
            <div class="info-meta">
              <span>来源：{{ detail.source === 'manual' ? '手动输入' : '新闻详情导入' }}</span>
              <span>创建时间：{{ formatDate(detail.created_at) }}</span>
            </div>
          </section>

          <!-- 输入文本 -->
          <section class="content-section">
            <h3 class="section-title">输入文本</h3>
            <div class="text-block">{{ detail.input_text }}</div>
          </section>

          <!-- 生成参数 -->
          <section class="content-section">
            <h3 class="section-title">生成参数</h3>
            <div class="params-grid">
              <div class="param-item">
                <span class="param-label">标题数量</span>
                <span class="param-value">{{ detail.params?.title_count }}</span>
              </div>
              <div class="param-item">
                <span class="param-label">摘要类型</span>
                <span class="param-value">{{ detail.params?.summary_type === 'extract' ? '抽取式' : '生成式' }}</span>
              </div>
              <div class="param-item">
                <span class="param-label">标题风格</span>
                <span class="param-value">{{ detail.params?.title_style }}</span>
              </div>
              <div class="param-item">
                <span class="param-label">摘要风格</span>
                <span class="param-value">{{ detail.params?.summary_style }}</span>
              </div>
              <div class="param-item">
                <span class="param-label">摘要长度</span>
                <span class="param-value">{{ detail.params?.summary_length === 'short' ? '短摘要' : detail.params?.summary_length === 'long' ? '长摘要' : '长+短摘要' }}</span>
              </div>
            </div>
          </section>

          <!-- 生成结果 -->
          <section class="content-section">
            <h3 class="section-title">生成结果</h3>
            <AIResultPanel :has-result="true" :override-result="detail.result" />
          </section>
        </template>
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
.detail-page {
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
  gap: 20px;
}

/* 操作栏 */
.action-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: var(--color-bg-card);
  border-radius: 10px;
  border: 1px solid #f0f0f0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.action-right {
  display: flex;
  gap: 8px;
}

.btn-delete {
  color: #ef4444 !important;
  border-color: #fecaca !important;
}

.btn-delete:hover {
  background-color: #fef2f2 !important;
}

/* 基本信息 */
.info-section {
  padding: 20px 24px;
  background: var(--color-bg-card);
  border-radius: 10px;
  border: 1px solid #f0f0f0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
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
  flex-shrink: 0;
}

.info-meta {
  display: flex;
  gap: 20px;
  font-size: 13px;
  color: var(--color-text-secondary);
}

/* 内容区 */
.content-section {
  padding: 20px 24px;
  background: var(--color-bg-card);
  border-radius: 10px;
  border: 1px solid #f0f0f0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.section-title {
  margin: 0 0 14px;
  font-size: 16px;
  font-weight: 700;
  color: var(--color-text-primary);
  padding-left: 10px;
  position: relative;
}

.section-title::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 4px;
  height: 18px;
  background-color: #d92d20;
  border-radius: 2px;
}

.text-block {
  font-size: 14px;
  line-height: 1.8;
  color: #374151;
  white-space: pre-wrap;
  word-break: break-word;
  padding: 14px;
  background-color: var(--color-bg-hover);
  border-radius: 8px;
  border: 1px solid #f0f0f0;
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
  border: 1px solid #f0f0f0;
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

/* 加载中 / 空状态 */
.loading-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 60px 20px;
  text-align: center;
  background: var(--color-bg-card);
  border-radius: 10px;
  border: 1px solid #f0f0f0;
  color: var(--color-text-secondary);
}

.empty-state {
  gap: 12px;
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
