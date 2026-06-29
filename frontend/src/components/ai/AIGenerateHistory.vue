<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAIDraftStore } from '@/stores/aiDraft'
import {
  getAIHistory,
  getAIRecordDetail,
  deleteAIRecord,
  type AIGenerateRecordItem,
  type AIGenerateRecordDetail,
} from '@/api/ai'
import AIResultPanel from './AIResultPanel.vue'

const aiDraft = useAIDraftStore()

const historyRecords = ref<AIGenerateRecordItem[]>([])
const loading = ref(false)
const selectedRecord = ref<AIGenerateRecordDetail | null>(null)
const showDetailDialog = ref(false)

const loadHistory = async () => {
  loading.value = true
  try {
    const response = await getAIHistory()
    historyRecords.value = response.records
  } catch (error) {
    ElMessage.error('加载历史记录失败')
  } finally {
    loading.value = false
  }
}

const handleViewRecord = async (record: AIGenerateRecordItem) => {
  try {
    selectedRecord.value = await getAIRecordDetail(record.id)
    showDetailDialog.value = true
  } catch (error) {
    ElMessage.error('获取记录详情失败')
  }
}

const handleReuseRecord = async (record: AIGenerateRecordItem) => {
  try {
    const detail = await getAIRecordDetail(record.id)
    aiDraft.setInputText(detail.input_text)
    aiDraft.setParams(detail.params)
    ElMessage.success('已复用历史输入，可重新生成')
  } catch (error) {
    ElMessage.error('复用历史失败')
  }
}

const handleDeleteRecord = async (record: AIGenerateRecordItem) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除这条历史记录吗？`,
      '警告',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )

    await deleteAIRecord(record.id)
    ElMessage.success('历史记录已删除')
    await loadHistory()
  } catch (error: any) {
    if (error.message !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const handleExportRecord = () => {
  ElMessage.info('导出功能后续接入')
}

const getRiskLevelType = (level: string) => {
  const map: Record<string, string> = {
    'low': 'success',
    'medium': 'warning',
    'high': 'danger',
  }
  return map[level] || 'info'
}

const formatDate = (dateString: string) => {
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)

  if (diffMins < 60) {
    return `${diffMins} 分钟前`
  } else if (diffHours < 24) {
    return `${diffHours} 小时前`
  } else if (diffDays < 7) {
    return `${diffDays} 天前`
  } else {
    return date.toLocaleDateString('zh-CN')
  }
}

function getFirstTitle(record: any): string {
  if (Array.isArray(record.candidate_titles) && record.candidate_titles.length > 0) {
    return record.candidate_titles[0]
  }
  return ''
}

onMounted(() => {
  loadHistory()
})

defineExpose({ loadHistory })
</script>

<template>
  <el-card class="app-card history-panel">
    <template #header>
      <div class="card-header">
        <span class="title">📚 生成历史</span>
        <el-button type="text" @click="loadHistory" :loading="loading">
          刷新
        </el-button>
      </div>
    </template>

    <!-- 空状态 -->
    <div v-if="historyRecords.length === 0" class="empty-state">
      <p class="empty-text">暂无生成历史</p>
      <p class="empty-description">生成标题和摘要后，记录将显示在这里</p>
    </div>

    <!-- 历史列表 -->
    <div v-else class="history-list">
      <div v-for="record in historyRecords" :key="record.id" class="history-item">
        <div class="item-main">
          <!-- 生成标题预览（置顶） -->
          <div v-if="getFirstTitle(record)" class="history-title">
            {{ getFirstTitle(record) }}
          </div>

          <div class="item-header">
            <div class="item-title">{{ record.source_title }}</div>
            <el-tag :type="getRiskLevelType(record.risk_level)" size="small">
              {{ record.risk_level === 'low' ? '低风险' : record.risk_level === 'medium' ? '中风险' : '高风险' }}
            </el-tag>
          </div>

          <div class="item-meta">
            <span class="meta-item">
              来源：{{ record.source === 'manual' ? '手动输入' : '新闻详情导入' }}
            </span>
            <span class="meta-item">标题数：{{ record.title_count }}</span>
            <span class="meta-item">{{ formatDate(record.created_at) }}</span>
          </div>
        </div>

        <div class="item-actions">
          <el-button
            type="text"
            size="small"
            @click="handleViewRecord(record)"
          >
            查看
          </el-button>
          <el-button
            type="text"
            size="small"
            @click="handleReuseRecord(record)"
          >
            复用
          </el-button>
          <el-button
            type="text"
            size="small"
            @click="handleDeleteRecord(record)"
          >
            删除
          </el-button>
          <el-button
            type="text"
            size="small"
            @click="handleExportRecord"
          >
            导出
          </el-button>
        </div>
      </div>
    </div>

    <!-- 详情弹窗 -->
    <el-dialog
      v-model="showDetailDialog"
      title="生成结果详情"
      width="80%"
      class="detail-dialog"
    >
      <div v-if="selectedRecord" class="detail-content">
        <div class="detail-header">
          <h3>{{ selectedRecord.source_title }}</h3>
          <el-tag :type="getRiskLevelType(selectedRecord.result.consistency.risk_level)">
            {{ selectedRecord.result.consistency.risk_level === 'low' ? '低风险' : selectedRecord.result.consistency.risk_level === 'medium' ? '中风险' : '高风险' }}
          </el-tag>
        </div>

        <div class="detail-section">
          <h4>输入文本</h4>
          <p class="input-text">{{ selectedRecord.input_text }}</p>
        </div>

        <div class="detail-section">
          <h4>生成参数</h4>
          <div class="params-grid">
            <div class="param-item">
              <span class="param-label">标题数量：</span>
              <span>{{ selectedRecord.params.title_count }}</span>
            </div>
            <div class="param-item">
              <span class="param-label">摘要类型：</span>
              <span>{{ selectedRecord.params.summary_type }}</span>
            </div>
            <div class="param-item">
              <span class="param-label">标题风格：</span>
              <span>{{ selectedRecord.params.title_style }}</span>
            </div>
            <div class="param-item">
              <span class="param-label">摘要风格：</span>
              <span>{{ selectedRecord.params.summary_style }}</span>
            </div>
            <div class="param-item">
              <span class="param-label">摘要长度：</span>
              <span>{{ selectedRecord.params.summary_length }}</span>
            </div>
          </div>
        </div>

        <!-- 结果展示 -->
        <div class="result-section">
          <AIResultPanel :has-result="true" :override-result="selectedRecord.result" />
        </div>
      </div>
    </el-dialog>
  </el-card>
</template>

<style scoped>
.history-panel {
  margin-bottom: 16px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.title {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.empty-state {
  padding: 40px 20px;
  text-align: center;
  background-color: rgba(64, 158, 255, 0.05);
  border-radius: 4px;
}

.empty-text {
  margin: 0 0 8px;
  font-size: 16px;
  color: var(--color-text-primary);
  font-weight: 500;
}

.empty-description {
  margin: 0;
  font-size: 14px;
  color: var(--color-text-secondary);
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.history-item {
  padding: 12px;
  background-color: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: 4px;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  transition: all 0.3s;

  &:hover {
    background-color: rgba(64, 158, 255, 0.02);
    border-color: var(--color-primary);
  }
}

.item-main {
  flex: 1;
}

.item-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.item-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-primary);
  flex: 1;
  word-break: break-word;
}

.history-title {
  font-size: 15px;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 8px;
  line-height: 1.45;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.item-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  font-size: 12px;
  color: var(--color-text-secondary);
}

.meta-item {
  white-space: nowrap;
}

.item-actions {
  display: flex;
  gap: 4px;
  margin-left: 16px;
  flex-shrink: 0;
}

.item-actions :deep(.el-button) {
  padding: 4px 8px;
}

.detail-dialog :deep(.el-dialog__body) {
  max-height: 70vh;
  overflow-y: auto;
}

.detail-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.detail-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--color-border);
}

.detail-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-primary);
  flex: 1;
}

.detail-section {
  padding: 12px;
  background-color: var(--color-bg);
  border-radius: 4px;
}

.detail-section h4 {
  margin: 0 0 8px;
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.input-text {
  margin: 0;
  font-size: 14px;
  line-height: 1.8;
  color: var(--color-text-primary);
  white-space: pre-wrap;
  word-break: break-word;
}

.params-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 12px;
}

.param-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.param-label {
  font-weight: 600;
  font-size: 12px;
  color: var(--color-primary);
}

.result-section {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid var(--color-border);
}
</style>
