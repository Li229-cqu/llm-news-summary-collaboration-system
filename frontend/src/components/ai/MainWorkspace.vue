<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { ElMessage, ElMessageBox, ElDialog } from 'element-plus'
import AIInputPanel from './AIInputPanel.vue'
import AIResultPanel from './AIResultPanel.vue'
import { aiApi, type AIGenerateRecordItem } from '@/api/ai'
import { Document as DocxDocument, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType } from 'docx'
import jsPDF from 'jspdf'

const props = defineProps<{
  loading: boolean
  uiMode: 'input' | 'history' | 'detail'
  historyDetailResult?: any
}>()

const emit = defineEmits<{
  (e: 'generate'): void
  (e: 'clear'): void
  (e: 'loadSample'): void
  (e: 'load-history-item', record: AIGenerateRecordItem): void
  (e: 'view-history-item', record: AIGenerateRecordItem): void
  (e: 'set-ui-mode', mode: 'input' | 'history' | 'detail'): void
}>()

const historyRecords = ref<AIGenerateRecordItem[]>([])
const historyLoading = ref(false)

const showExportDialog = ref(false)
const selectedExportFormat = ref<string>('')
const exportingRecord = ref<AIGenerateRecordItem | null>(null)
const exportingDetail = ref<any>(null)

const loadHistory = async () => {
  historyLoading.value = true
  try {
    const response = await aiApi.getRecords()
    historyRecords.value = response.records
  } catch (error) {
    ElMessage.error('加载历史记录失败')
  } finally {
    historyLoading.value = false
  }
}

const handleGenerate = () => {
  emit('generate')
}

const handleClear = () => {
  emit('clear')
}

const handleLoadSample = () => {
  emit('loadSample')
}

const handleLoadHistoryItem = (record: AIGenerateRecordItem) => {
  emit('load-history-item', record)
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

    await aiApi.deleteRecord(record.id)
    ElMessage.success('历史记录已删除')
    await loadHistory()
  } catch (error: any) {
    if (error.message !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const handleExportRecord = async (record: AIGenerateRecordItem) => {
  try {
    const detail = await aiApi.getRecordDetail(record.id)
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
        detail.result.candidate_titles.forEach((title: string, index: number) => {
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
            text: `问题：${detail.result.consistency.issues?.join('；') || '无'}`,
            spacing: { after: 50 },
          }),
          new Paragraph({
            text: `建议：${detail.result.consistency.suggestions?.join('；') || '无'}`,
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
        addSection('候选标题', detail.result.candidate_titles.map((t: string, i: number) => `${i + 1}. ${t}`).join('\n'))
      }
      
      const pdfSummary = detail.params.summary_length === 'short' ? detail.result.summary_short : detail.result.summary_long
      if (pdfSummary) {
        addSection('摘要', pdfSummary)
      }
      
      if (detail.result.consistency) {
        const consistencyText = `风险等级：${detail.result.consistency.risk_level}\n匹配度：${detail.result.consistency.score}\n问题：${detail.result.consistency.issues?.join('；') || '无'}\n建议：${detail.result.consistency.suggestions?.join('；') || '无'}`
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

const generateExportContent = (record: AIGenerateRecordItem, detail: any): string => {
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
    detail.result.candidate_titles.forEach((title: string, index: number) => {
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
    content += `问题：${detail.result.consistency.issues?.join('；') || '无'}\n`
    content += `建议：${detail.result.consistency.suggestions?.join('；') || '无'}\n\n`
  }
  
  if (detail.result.keywords && detail.result.keywords.length > 0) {
    content += `【关键词】\n${detail.result.keywords.join('、')}\n`
  }
  
  return content
}

const refreshHistory = () => {
  loadHistory()
}

onMounted(() => {
  if (props.uiMode === 'history') {
    loadHistory()
  }
})

watch(
  () => props.uiMode,
  (newMode) => {
    if (newMode === 'history') {
      loadHistory()
    }
  }
)

defineExpose({ refreshHistory })
</script>

<template>
  <div class="main-area">
    <template v-if="uiMode === 'input'">
      <AIInputPanel />
      
      <div class="action-wrapper">
        <div class="tips-section">
          <div class="tip-item">
            <span class="tip-dot"></span>
            <span>支持粘贴新闻正文，自动提取关键信息</span>
          </div>
          <div class="tip-item">
            <span class="tip-dot"></span>
            <span>可生成1-5个候选标题供选择</span>
          </div>
          <div class="tip-item">
            <span class="tip-dot"></span>
            <span>短摘要150字以内，长摘要300-800字</span>
          </div>
        </div>
        
        <div class="shortcuts-section">
          <button class="shortcut-btn" @click="handleClear">清空内容</button>
          <button class="shortcut-btn" @click="handleLoadSample">加载示例</button>
        </div>
        
        <el-button
          type="primary"
          size="large"
          class="generate-button"
          @click="handleGenerate"
          :loading="loading"
          :disabled="loading"
        >
          {{ loading ? '生成中...' : '生成标题和摘要' }}
        </el-button>
      </div>

      <AIResultPanel />
    </template>

    <template v-else-if="uiMode === 'history'">
      <div class="history-mode-header">
        <h3>生成记录</h3>
        <div class="header-actions">
          <el-button type="text" @click="loadHistory" :loading="historyLoading">刷新</el-button>
          <el-button type="text" @click="$emit('set-ui-mode', 'input')">返回输入模式</el-button>
        </div>
      </div>
      
      <div class="history-list-container">
        <div v-if="historyLoading" class="loading-state">
          <el-spinner />
          <span>加载中...</span>
        </div>
        
        <div v-else-if="historyRecords.length === 0" class="empty-state">
          <p class="empty-text">暂无生成记录</p>
          <p class="empty-description">生成标题和摘要后，记录将显示在这里</p>
        </div>
        
        <div v-else class="history-list">
          <div v-for="record in historyRecords" :key="record.id" class="history-item">
            <div class="item-content">
              <div class="item-title">
                {{ record.candidate_titles?.[0] || record.source_title }}
              </div>
              <div class="item-summary">{{ record.summary_short || '暂无摘要' }}</div>
              <div class="item-time">{{ record.created_at }}</div>
            </div>
            <div class="item-actions">
              <el-button type="text" size="small" @click="emit('view-history-item', record)">查看</el-button>
              <el-button type="text" size="small" @click="handleLoadHistoryItem(record)">复用</el-button>
              <el-button type="text" size="small" @click="handleDeleteRecord(record)">删除</el-button>
              <el-button type="text" size="small" @click="handleExportRecord(record)">导出</el-button>
            </div>
          </div>
        </div>
      </div>
    </template>

    <template v-else-if="uiMode === 'detail'">
      <div class="detail-mode-header">
        <h3>历史详情</h3>
        <div class="header-actions">
          <el-button type="text" @click="$emit('set-ui-mode', 'history')">返回历史列表</el-button>
          <el-button type="text" @click="$emit('set-ui-mode', 'input')">返回输入模式</el-button>
        </div>
      </div>
      
      <AIResultPanel :has-result="true" :override-result="historyDetailResult" />
    </template>
  </div>

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
</template>

<style scoped>
.main-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.action-wrapper {
  padding: 20px;
  background-color: #ffffff;
  border-radius: 10px;
  border: 1px solid #f0f0f0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.tips-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
  
  .tip-item {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 13px;
    color: #666666;
    
    .tip-dot {
      width: 4px;
      height: 4px;
      background-color: #ff4d4f;
      border-radius: 50%;
      flex-shrink: 0;
    }
  }
}

.shortcuts-section {
  display: flex;
  gap: 10px;
  
  .shortcut-btn {
    flex: 1;
    padding: 10px 16px;
    font-size: 13px;
    color: #666666;
    background-color: #f8f8f8;
    border: 1px solid #e8e8e8;
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.2s ease;
    
    &:hover {
      background-color: #fff5f5;
      border-color: #ffccc7;
      color: #ff4d4f;
    }
  }
}

.generate-button {
  width: 100%;
  height: 46px;
  font-size: 16px;
  font-weight: 600;
  border-radius: 8px;
  background: linear-gradient(135deg, #ff4d4f 0%, #ff7875 100%);
  border: none;
  transition: all 0.25s ease;
  
  &:hover:not(:disabled) {
    background: linear-gradient(135deg, #ff7875 0%, #ff4d4f 100%);
    transform: translateY(-1px);
    box-shadow: 0 6px 20px rgba(255, 77, 79, 0.4);
  }
  
  &:active:not(:disabled) {
    transform: translateY(0);
    box-shadow: 0 3px 10px rgba(255, 77, 79, 0.3);
  }
}

.history-mode-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  background-color: #ffffff;
  border-radius: 10px;
  border: 1px solid #f0f0f0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  position: sticky;
  top: 0;
  z-index: 10;
  
  h3 {
    margin: 0;
    font-size: 16px;
    font-weight: 600;
    color: #374151;
  }
}

.header-actions {
  display: flex;
  gap: 16px;
}

.history-list-container {
  background-color: #ffffff;
  border-radius: 10px;
  border: 1px solid #f0f0f0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  padding: 16px;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 40px 20px;
  color: #6b7280;
}

.empty-state {
  padding: 40px 20px;
  text-align: center;
  background-color: #f9fafb;
  border-radius: 6px;
  border: 1px dashed #e5e7eb;
}

.empty-text {
  margin: 0 0 8px;
  font-size: 15px;
  color: #374151;
  font-weight: 500;
}

.empty-description {
  margin: 0;
  font-size: 14px;
  color: #6b7280;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.history-item {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 16px;
  background-color: #f9fafb;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
  
  &:hover {
    border-color: #d1d5db;
  }
}

.item-content {
  flex: 1;
  min-width: 0;
}

.item-title {
  font-size: 15px;
  font-weight: 600;
  color: #374151;
  margin-bottom: 8px;
}

.item-summary {
  font-size: 13px;
  color: #6b7280;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
  margin-bottom: 8px;
}

.item-time {
  font-size: 12px;
  color: #9ca3af;
}

.item-actions {
  display: flex;
  flex-direction: row;
  gap: 8px;
  margin-left: 16px;
  flex-shrink: 0;
  align-self: center;
  
  :deep(.el-button) {
    padding: 6px 12px;
    font-size: 12px;
  }
}

.detail-mode-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  background-color: #ffffff;
  border-radius: 10px;
  border: 1px solid #f0f0f0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  position: sticky;
  top: 0;
  z-index: 10;
  
  h3 {
    margin: 0;
    font-size: 16px;
    font-weight: 600;
    color: #374151;
  }
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
  border: 1px solid transparent;
  border-radius: 6px;
  cursor: pointer;
  transition: border-color 0.2s ease;
  background-color: #f9fafb;

  &:hover {
    border-color: #d1d5db;
  }

  &.selected {
    border-color: #ff4d4f;
    background-color: #fff5f5;
  }
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
  color: #6b7280;
  margin-top: 2px;
}
</style>