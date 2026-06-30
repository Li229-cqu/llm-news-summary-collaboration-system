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
import { Document as DocxDocument, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType } from 'docx'
import jsPDF from 'jspdf'

declare global {
  interface Window {
    __exportFormat?: string
  }
}

const aiDraft = useAIDraftStore()

const historyRecords = ref<AIGenerateRecordItem[]>([])
const loading = ref(false)
const selectedRecord = ref<AIGenerateRecordDetail | null>(null)
const showDetailDialog = ref(false)

const showExportDialog = ref(false)
const selectedExportFormat = ref<string>('')
const exportingRecord = ref<AIGenerateRecordItem | null>(null)
const exportingDetail = ref<AIGenerateRecordDetail | null>(null)

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

const generateExportContent = (record: AIGenerateRecordItem, detail: AIGenerateRecordDetail): string => {
  let content = `【来源标题】${record.source_title}\n`
  content += `【来源】${record.source === 'manual' ? '手动输入' : '新闻详情导入'}\n`
  content += `【风险等级】${record.risk_level === 'low' ? '低风险' : record.risk_level === 'medium' ? '中风险' : '高风险'}\n`
  content += `【创建时间】${record.created_at}\n`
  content += `【标题数量】${record.title_count}\n\n`
  
  content += `=== 输入文本 ===\n${detail.input_text}\n\n`
  
  content += `=== 生成参数 ===\n`
  content += `标题数量：${detail.params.title_count}\n`
  content += `摘要类型：${detail.params.summary_type}\n`
  content += `标题风格：${detail.params.title_style}\n`
  content += `摘要风格：${detail.params.summary_style}\n`
  content += `摘要长度：${detail.params.summary_length}\n\n`
  
  content += `=== 生成结果 ===\n\n`
  
  if (detail.result.candidate_titles && detail.result.candidate_titles.length > 0) {
    content += `【候选标题】\n`
    detail.result.candidate_titles.forEach((title, index) => {
      content += `${index + 1}. ${title}\n`
    })
    content += '\n'
  }
  
  const summaryText = detail.params.summary_length === 'short' ? detail.result.summary_short : detail.result.summary_long
  if (summaryText) {
    content += `【摘要】\n${summaryText}\n\n`
  }
  
  if (detail.result.consistency) {
    content += `【一致性分析】\n`
    content += `风险等级：${detail.result.consistency.risk_level}\n`
    content += `匹配度：${detail.result.consistency.score}\n`
    content += `问题：${detail.result.consistency.issues.join('；') || '无'}\n`
    content += `建议：${detail.result.consistency.suggestions.join('；') || '无'}\n\n`
  }
  
  if (detail.result.keywords && detail.result.keywords.length > 0) {
    content += `【关键词】\n${detail.result.keywords.join('、')}\n`
  }
  
  return content
}

const handleExportRecord = async (record: AIGenerateRecordItem) => {
  try {
    const detail = await getAIRecordDetail(record.id)
    exportingRecord.value = record
    exportingDetail.value = detail
    selectedExportFormat.value = ''
    showExportDialog.value = true
  } catch (error) {
    ElMessage.error('获取记录详情失败')
  }
}

const confirmExport = async () => {
  if (!selectedExportFormat.value) {
    ElMessage.warning('请先选择导出格式')
    return
  }
  
  const record = exportingRecord.value
  const detail = exportingDetail.value
  if (!record || !detail) {
    ElMessage.error('导出数据异常')
    return
  }
  
  const content = generateExportContent(record, detail)
  const fileName = `ai-record-${record.id}-${new Date().toISOString().split('T')[0]}`
  const format = selectedExportFormat.value
  
  try {
    if (format === 'txt') {
      const blob = new Blob([content], { type: 'text/plain;charset=utf-8' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${fileName}.txt`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    } else if (format === 'docx') {
      const docChildren: Paragraph[] = [
        new Paragraph({
          text: record.source_title,
          heading: HeadingLevel.HEADING_1,
          alignment: AlignmentType.CENTER,
          spacing: { after: 200 },
        }),
        new Paragraph({
          children: [
            new TextRun({ text: `来源：${record.source === 'manual' ? '手动输入' : '新闻详情导入'}  ` }),
            new TextRun({ text: `风险等级：${record.risk_level === 'low' ? '低风险' : record.risk_level === 'medium' ? '中风险' : '高风险'}  ` }),
            new TextRun({ text: `创建时间：${record.created_at}` }),
          ],
          spacing: { after: 200 },
        }),
        new Paragraph({
          text: '输入文本',
          heading: HeadingLevel.HEADING_2,
          spacing: { after: 100 },
        }),
        new Paragraph({
          text: detail.input_text,
          spacing: { after: 200 },
        }),
        new Paragraph({
          text: '生成参数',
          heading: HeadingLevel.HEADING_2,
          spacing: { after: 100 },
        }),
        new Paragraph({
          text: `标题数量：${detail.params.title_count} | 摘要类型：${detail.params.summary_type} | 标题风格：${detail.params.title_style}`,
          spacing: { after: 50 },
        }),
        new Paragraph({
          text: `摘要风格：${detail.params.summary_style} | 摘要长度：${detail.params.summary_length}`,
          spacing: { after: 200 },
        }),
        new Paragraph({
          text: '生成结果',
          heading: HeadingLevel.HEADING_2,
          spacing: { after: 100 },
        }),
      ]
      
      if (detail.result.candidate_titles && detail.result.candidate_titles.length > 0) {
        docChildren.push(
          new Paragraph({
            text: '候选标题',
            heading: HeadingLevel.HEADING_3,
            spacing: { after: 50 },
          })
        )
        detail.result.candidate_titles.forEach((title, index) => {
          docChildren.push(
            new Paragraph({
              text: `${index + 1}. ${title}`,
              spacing: { after: 50 },
            })
          )
        })
      }
      
      const docxSummary = detail.params.summary_length === 'short' ? detail.result.summary_short : detail.result.summary_long
      if (docxSummary) {
        docChildren.push(
          new Paragraph({
            text: '摘要',
            heading: HeadingLevel.HEADING_3,
            spacing: { after: 50 },
          }),
          new Paragraph({
            text: docxSummary,
            spacing: { after: 200 },
          })
        )
      }
      
      if (detail.result.consistency) {
        docChildren.push(
          new Paragraph({
            text: '一致性分析',
            heading: HeadingLevel.HEADING_3,
            spacing: { after: 50 },
          }),
          new Paragraph({
            text: `风险等级：${detail.result.consistency.risk_level} | 匹配度：${detail.result.consistency.score}`,
            spacing: { after: 50 },
          }),
          new Paragraph({
            text: `问题：${detail.result.consistency.issues.join('；') || '无'}`,
            spacing: { after: 50 },
          }),
          new Paragraph({
            text: `建议：${detail.result.consistency.suggestions.join('；') || '无'}`,
            spacing: { after: 200 },
          })
        )
      }
      
      if (detail.result.keywords && detail.result.keywords.length > 0) {
        docChildren.push(
          new Paragraph({
            text: '关键词',
            heading: HeadingLevel.HEADING_3,
            spacing: { after: 50 },
          }),
          new Paragraph({
            text: detail.result.keywords.join('、'),
          })
        )
      }
      
      const doc = new DocxDocument({
        creator: 'LLM News System',
        title: record.source_title,
        sections: [
          {
            properties: {},
            children: docChildren,
          },
        ],
      })
      
      const blob = await Packer.toBlob(doc)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${fileName}.docx`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    } else if (format === 'pdf') {
      const pdf = new jsPDF({
        orientation: 'portrait',
        unit: 'mm',
        format: 'a4',
      })
      
      const fontSize = 10
      const lineHeight = 14
      const margin = 20
      const maxWidth = pdf.internal.pageSize.getWidth() - margin * 2
      let y = margin
      
      pdf.setFontSize(16)
      pdf.setTextColor(0, 0, 0)
      pdf.text(record.source_title, margin, y)
      y += 20
      
      pdf.setFontSize(10)
      pdf.setTextColor(100, 100, 100)
      pdf.text(`来源：${record.source === 'manual' ? '手动输入' : '新闻详情导入'} | 风险等级：${record.risk_level === 'low' ? '低风险' : record.risk_level === 'medium' ? '中风险' : '高风险'} | 创建时间：${record.created_at}`, margin, y)
      y += 15
      
      const addSection = (title: string, text: string) => {
        pdf.setFontSize(12)
        pdf.setTextColor(0, 0, 0)
        pdf.text(title, margin, y)
        y += 10
        
        pdf.setFontSize(fontSize)
        pdf.setTextColor(50, 50, 50)
        const lines = pdf.splitTextToSize(text, maxWidth)
        lines.forEach((line: string) => {
          if (y > pdf.internal.pageSize.getHeight() - margin) {
            pdf.addPage()
            y = margin
          }
          pdf.text(line, margin, y)
          y += lineHeight
        })
        y += 10
      }
      
      addSection('输入文本', detail.input_text)
      
      const paramsText = `标题数量：${detail.params.title_count}\n摘要类型：${detail.params.summary_type}\n标题风格：${detail.params.title_style}\n摘要风格：${detail.params.summary_style}\n摘要长度：${detail.params.summary_length}`
      addSection('生成参数', paramsText)
      
      if (detail.result.candidate_titles && detail.result.candidate_titles.length > 0) {
        addSection('候选标题', detail.result.candidate_titles.map((t, i) => `${i + 1}. ${t}`).join('\n'))
      }
      
      const pdfSummary = detail.params.summary_length === 'short' ? detail.result.summary_short : detail.result.summary_long
      if (pdfSummary) {
        addSection('摘要', pdfSummary)
      }
      
      if (detail.result.consistency) {
        const consistencyText = `风险等级：${detail.result.consistency.risk_level}\n匹配度：${detail.result.consistency.score}\n问题：${detail.result.consistency.issues.join('；') || '无'}\n建议：${detail.result.consistency.suggestions.join('；') || '无'}`
        addSection('一致性分析', consistencyText)
      }
      
      if (detail.result.keywords && detail.result.keywords.length > 0) {
        addSection('关键词', detail.result.keywords.join('、'))
      }
      
      pdf.save(`${fileName}.pdf`)
    }
    
    ElMessage.success('导出成功')
    showExportDialog.value = false
    selectedExportFormat.value = ''
  } catch (error) {
    ElMessage.error('导出失败')
  }
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
            <div class="header-tags">
              <el-tag :type="record.ai_source === 'llm' ? 'success' : 'info'" size="small">
                {{ record.ai_source === 'llm' ? '真实AI' : 'Mock演示' }}
              </el-tag>
              <el-tag :type="getRiskLevelType(record.risk_level)" size="small">
                {{ record.risk_level === 'low' ? '低风险' : record.risk_level === 'medium' ? '中风险' : '高风险' }}
              </el-tag>
            </div>
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
            @click="handleExportRecord(record)"
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

    <!-- 导出格式选择对话框 -->
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
            {{ format === 'txt' ? '📄' : format === 'docx' ? '📝' : '📑' }}
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
  justify-content: space-between;
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

.header-tags {
  display: flex;
  align-items: center;
  gap: 8px;
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

.export-dialog :deep(.el-dialog__body) {
  padding: 20px;
}

.export-format-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.format-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border: 2px solid transparent;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
  background-color: var(--color-bg);

  &:hover {
    background-color: rgba(64, 158, 255, 0.05);
  }

  &.selected {
    border-color: var(--color-primary);
    background-color: rgba(64, 158, 255, 0.08);
  }
}

.format-icon {
  font-size: 28px;
}

.format-info {
  flex: 1;
}

.format-name {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.format-desc {
  font-size: 12px;
  color: var(--color-text-secondary);
  margin-top: 4px;
}
</style>
