/**
 * AI 生成历史记录共享逻辑。
 * 统一把列表、详情、复用、导出都收敛到标准结果结构。
 */
import { ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import jsPDF from 'jspdf'
import {
  deleteAIRecord,
  getAIHistory,
  getAIRecordDetail,
  type AIGenerateRecordItem,
} from '@/api/ai'
import {
  formatProviderModel,
  getAIGenerateSourceLabel,
  normalizeAIGenerateHistoryDetail,
  normalizeAIGenerateHistoryRecord,
  type NormalizedAIGenerateHistoryDetail,
  type NormalizedAIGenerateHistoryRecord,
} from '@/utils/normalizeAIGenerateResult'
import { exportRecordToWord } from '@/utils/exportWord'

type ExportFormat = 'txt' | 'docx' | 'pdf'

export function useAIGenerateHistory() {
  const historyRecords = ref<NormalizedAIGenerateHistoryRecord[]>([])
  const loading = ref(false)

  const showExportDialog = ref(false)
  const selectedExportFormat = ref<ExportFormat | ''>('')
  const exportingRecord = ref<NormalizedAIGenerateHistoryRecord | null>(null)
  const exportingDetail = ref<NormalizedAIGenerateHistoryDetail | null>(null)

  const loadHistory = async () => {
    loading.value = true
    try {
      const response = await getAIHistory()
      historyRecords.value = (response.records || []).map(record => normalizeAIGenerateHistoryRecord(record))
    } catch {
      ElMessage.error('加载历史记录失败')
    } finally {
      loading.value = false
    }
  }

  const loadRecordDetail = async (recordId: number | string) => {
    try {
      const detail = await getAIRecordDetail(recordId)
      return normalizeAIGenerateHistoryDetail(detail)
    } catch {
      ElMessage.error('获取记录详情失败')
      return null
    }
  }

  const deleteRecord = async (record: AIGenerateRecordItem) => {
    try {
      await ElMessageBox.confirm('确定要删除这条历史记录吗？', '警告', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      })

      await deleteAIRecord(record.id)
      ElMessage.success('历史记录已删除')
      await loadHistory()
      return true
    } catch (error: any) {
      if (error?.message !== 'cancel') {
        ElMessage.error('删除失败')
      }
      return false
    }
  }

  function formatRiskLabel(level: string) {
    if (level === 'low') return '低风险'
    if (level === 'medium') return '中风险'
    if (level === 'high') return '高风险'
    return '未知'
  }

  function formatSummaryForExport(detail: NormalizedAIGenerateHistoryDetail) {
    const result = detail.standardResult
    const lines: string[] = []

    if (result.candidate_titles.length > 0) {
      lines.push('【候选标题】')
      result.candidate_titles.forEach((title, index) => {
        lines.push(`${index + 1}. ${title}`)
      })
      lines.push('')
    }

    if (result.summary_short) {
      lines.push('【短摘要】')
      lines.push(result.summary_short)
      lines.push('')
    }

    if (result.summary_long) {
      lines.push('【长摘要】')
      lines.push(result.summary_long)
      lines.push('')
    }

    if (result.summary_points.length > 0) {
      lines.push('【摘要要点】')
      result.summary_points.forEach((point, index) => {
        lines.push(`${index + 1}. ${point}`)
      })
      lines.push('')
    }

    if (result.keywords.length > 0) {
      lines.push('【关键词】')
      lines.push(result.keywords.join('、'))
      lines.push('')
    }

    const elements = result.elements
    if (elements.who || elements.what || elements.when || elements.where || elements.why || elements.how) {
      lines.push('【新闻六要素】')
      lines.push(`人物/主体：${elements.who || '无'}`)
      lines.push(`事件：${elements.what || '无'}`)
      lines.push(`时间：${elements.when || '无'}`)
      lines.push(`地点：${elements.where || '无'}`)
      lines.push(`原因：${elements.why || '无'}`)
      lines.push(`方式：${elements.how || '无'}`)
      lines.push('')
    }

    if (result.has_consistency) {
      lines.push('【一致性检测】')
      lines.push(`评分：${result.consistency.score}`)
      lines.push(`风险等级：${formatRiskLabel(result.consistency.risk_level)}`)
      lines.push(`问题提示：${(result.consistency.issues || []).join('；') || '无'}`)
      lines.push(`修改建议：${(result.consistency.suggestions || []).join('；') || '无'}`)
      lines.push('')
    }

    lines.push('【风险与证据】')
    if (result.risk_details) {
      lines.push(`风险说明：${result.risk_details}`)
    }
    if (typeof result.evidence_coverage === 'number') {
      lines.push(`证据覆盖率：${(result.evidence_coverage * 100).toFixed(0)}%`)
    }

    lines.push('')
    lines.push('【来源信息】')
    lines.push(`生成来源：${getAIGenerateSourceLabel(result.generation_source, result.generation_source)}`)
    const modelText = formatProviderModel(result.provider, result.model)
    if (modelText) {
      lines.push(`模型信息：${modelText}`)
    }
    if (result.fallback_reason) {
      lines.push(`回退原因：${result.fallback_reason}`)
    }

    return lines.filter(line => line !== undefined && line !== null).join('\n').trim()
  }

  const openExportDialog = async (record: AIGenerateRecordItem) => {
    const detail = await loadRecordDetail(record.id)
    if (!detail) return
    exportingRecord.value = normalizeAIGenerateHistoryRecord(record)
    exportingDetail.value = detail
    selectedExportFormat.value = ''
    showExportDialog.value = true
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

    const fileName = `ai-record-${record.id}-${new Date().toISOString().slice(0, 10)}`

    try {
      if (selectedExportFormat.value === 'txt') {
        const content = [
          'AI 标题摘要生成记录',
          '',
          `生成时间：${record.created_at || '无'}`,
          `生成来源：${getAIGenerateSourceLabel(detail.standardResult.generation_source, detail.standardResult.generation_source)}`,
          `模型信息：${formatProviderModel(detail.standardResult.provider, detail.standardResult.model) || '无'}`,
          detail.standardResult.fallback_reason ? `回退原因：${detail.standardResult.fallback_reason}` : '',
          '',
          '【输入内容】',
          detail.input_text || '无',
          '',
          '【生成参数】',
          `标题数量：${detail.params?.title_count ?? '无'}`,
          `摘要类型：${detail.params?.summary_type === 'extract' ? '抽取式' : detail.params?.summary_type === 'generate' ? '生成式' : '无'}`,
          `标题风格：${detail.params?.title_style || '无'}`,
          `摘要风格：${detail.params?.summary_style || '无'}`,
          `摘要长度：${detail.params?.summary_length || '无'}`,
          '',
          formatSummaryForExport(detail),
        ].filter(Boolean).join('\n')

        const blob = new Blob([content], { type: 'text/plain;charset=utf-8' })
        const url = URL.createObjectURL(blob)
        const anchor = document.createElement('a')
        anchor.href = url
        anchor.download = `${fileName}.txt`
        document.body.appendChild(anchor)
        anchor.click()
        document.body.removeChild(anchor)
        URL.revokeObjectURL(url)
      } else if (selectedExportFormat.value === 'docx') {
        await exportRecordToWord(detail)
      } else if (selectedExportFormat.value === 'pdf') {
        const pdf = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' })
        const margin = 20
        const lineHeight = 7
        const maxWidth = pdf.internal.pageSize.getWidth() - margin * 2
        const pageHeight = pdf.internal.pageSize.getHeight()
        let y = margin

        const writeLine = (text: string, size = 10, color: [number, number, number] = [0, 0, 0]) => {
          pdf.setFontSize(size)
          pdf.setTextColor(color[0], color[1], color[2])
          const lines = pdf.splitTextToSize(text, maxWidth) as string[]
          for (const line of lines) {
            if (y > pageHeight - margin) {
              pdf.addPage()
              y = margin
            }
            pdf.text(line, margin, y)
            y += lineHeight
          }
        }

        writeLine('AI 标题摘要生成记录', 16)
        y += 4
        writeLine(`生成时间：${record.created_at || '无'} | 生成来源：${getAIGenerateSourceLabel(detail.standardResult.generation_source, detail.standardResult.generation_source)}`, 9, [100, 100, 100])
        const modelText = formatProviderModel(detail.standardResult.provider, detail.standardResult.model)
        if (modelText) {
          y += 2
          writeLine(`模型信息：${modelText}`, 9, [100, 100, 100])
        }
        if (detail.standardResult.fallback_reason) {
          y += 2
          writeLine(`回退原因：${detail.standardResult.fallback_reason}`, 9, [100, 100, 100])
        }
        y += 4

        const sections: Array<[string, string]> = [
          ['输入内容', detail.input_text || '无'],
          ['生成参数', [
            `标题数量：${detail.params?.title_count ?? '无'}`,
            `摘要类型：${detail.params?.summary_type === 'extract' ? '抽取式' : detail.params?.summary_type === 'generate' ? '生成式' : '无'}`,
            `标题风格：${detail.params?.title_style || '无'}`,
            `摘要风格：${detail.params?.summary_style || '无'}`,
            `摘要长度：${detail.params?.summary_length || '无'}`,
          ].join('\n')],
          ['生成结果', formatSummaryForExport(detail)],
        ]

        for (const [title, content] of sections) {
          writeLine(title, 12)
          y += 1
          writeLine(content || '无', 10, [60, 60, 60])
          y += 3
        }

        pdf.save(`${fileName}.pdf`)
      }

      ElMessage.success('导出成功')
      showExportDialog.value = false
      selectedExportFormat.value = ''
    } catch {
      ElMessage.error('导出失败')
    }
  }

  const getRiskLevelType = (level: string): 'success' | 'warning' | 'danger' | 'info' => {
    const map: Record<string, 'success' | 'warning' | 'danger' | 'info'> = {
      low: 'success',
      medium: 'warning',
      high: 'danger',
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

    if (diffMins < 60) return `${diffMins} 分钟前`
    if (diffHours < 24) return `${diffHours} 小时前`
    if (diffDays < 7) return `${diffDays} 天前`
    return date.toLocaleDateString('zh-CN')
  }

  return {
    historyRecords,
    loading,
    showExportDialog,
    selectedExportFormat,
    exportingRecord,
    exportingDetail,
    loadHistory,
    loadRecordDetail,
    deleteRecord,
    openExportDialog,
    confirmExport,
    generateExportContent: formatSummaryForExport,
    getRiskLevelType,
    formatDate,
  }
}
