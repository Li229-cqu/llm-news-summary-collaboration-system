/**
 * AI 生成历史共享逻辑 composable。
 * 提取自 AIGenerateHistory.vue，供历史列表页、历史详情页复用。
 */
import { ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getAIHistory,
  getAIRecordDetail,
  deleteAIRecord,
  type AIGenerateRecordItem,
  type AIGenerateRecordDetail,
} from '@/api/ai'
import { Document as DocxDocument, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType } from 'docx'
import jsPDF from 'jspdf'

export function useAIGenerateHistory() {
  const historyRecords = ref<AIGenerateRecordItem[]>([])
  const loading = ref(false)

  const showExportDialog = ref(false)
  const selectedExportFormat = ref<string>('')
  const exportingRecord = ref<AIGenerateRecordItem | null>(null)
  const exportingDetail = ref<AIGenerateRecordDetail | null>(null)

  // ========== 数据加载 ==========

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

  const loadRecordDetail = async (recordId: number | string) => {
    try {
      return await getAIRecordDetail(recordId)
    } catch (error) {
      ElMessage.error('获取记录详情失败')
      return null
    }
  }

  // ========== 删除 ==========

  const deleteRecord = async (record: AIGenerateRecordItem) => {
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
      return true
    } catch (error: any) {
      if (error.message !== 'cancel') {
        ElMessage.error('删除失败')
      }
      return false
    }
  }

  // ========== 导出 ==========

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

    const summaryText = detail.params.summary_length === 'short'
      ? detail.result.summary_short
      : detail.result.summary_long
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

  const openExportDialog = async (record: AIGenerateRecordItem) => {
    try {
      const detail = await loadRecordDetail(record.id)
      if (!detail) return
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

        const docxSummary = detail.params.summary_length === 'short'
          ? detail.result.summary_short
          : detail.result.summary_long
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

        const pdfSummary = detail.params.summary_length === 'short'
          ? detail.result.summary_short
          : detail.result.summary_long
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

  // ========== 工具函数 ==========

  const getRiskLevelType = (level: string): 'success' | 'warning' | 'danger' | 'info' => {
    const map: Record<string, 'success' | 'warning' | 'danger' | 'info'> = {
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

  return {
    // 状态
    historyRecords,
    loading,
    showExportDialog,
    selectedExportFormat,
    exportingRecord,
    exportingDetail,
    // 方法
    loadHistory,
    loadRecordDetail,
    deleteRecord,
    openExportDialog,
    confirmExport,
    generateExportContent,
    getRiskLevelType,
    formatDate,
  }
}
