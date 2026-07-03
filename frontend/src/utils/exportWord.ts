/**
 * Word 文档导出工具 — 将 AI 生成记录导出为 .docx 文件。
 *
 * 依赖：docx v9+ (npm:docx)
 * 输出：触发浏览器下载 .docx 文件
 */

import {
  Document,
  Packer,
  Paragraph,
  TextRun,
  HeadingLevel,
  Table,
  TableRow,
  TableCell,
  BorderStyle,
  AlignmentType,
  ShadingType,
  WidthType,
  type IRunOptions,
  type ITableCellOptions,
  type ITableOptions,
} from 'docx'
import type { AIGenerateRecordDetail } from '@/api/ai'

// ── 排版常量 ──────────────────────────────────────────

const FONT = 'Microsoft YaHei'
const FONT_SIZE = 22
const FONT_SIZE_SM = 20
const FONT_SIZE_H1 = 36
const FONT_SIZE_H2 = 28
const COLOR_PRIMARY = '1E293B'
const COLOR_SECONDARY = '64748B'
const COLOR_MUTED = '94A3B8'
const COLOR_BRAND = 'DC2626'
const COLOR_GREEN = '16A34A'
const COLOR_WARN = 'D97706'
const COLOR_BG = 'F8FAFC'
const COLOR_BORDER = 'E2E8F0'

type DocChild = Paragraph | Table

// ── 辅助函数 ──────────────────────────────────────────

function txt(text: string, opts: Partial<IRunOptions> = {}): TextRun {
  return new TextRun({ text, font: FONT, size: FONT_SIZE, color: COLOR_PRIMARY, ...opts })
}

type HeadingLevelValue = (typeof HeadingLevel)[keyof typeof HeadingLevel]

function headingBlock(text: string, level: HeadingLevelValue): Paragraph {
  return new Paragraph({
    heading: level,
    children: [txt(text, { bold: true, size: level === HeadingLevel.HEADING_1 ? FONT_SIZE_H1 : FONT_SIZE_H2 })],
    spacing: { before: level === HeadingLevel.HEADING_1 ? 0 : 280, after: 120 },
  })
}

function para(text: string, opts: Partial<IRunOptions> = {}): Paragraph {
  return new Paragraph({
    children: [txt(text, opts)],
    spacing: { after: 60 },
  })
}

function mutedPara(text: string): Paragraph {
  return new Paragraph({
    children: [txt(text, { size: FONT_SIZE_SM, color: COLOR_SECONDARY, italics: true })],
    spacing: { after: 40 },
  })
}

function emptyLine(): Paragraph {
  return new Paragraph({ spacing: { after: 60 }, children: [] })
}

function chipRow(labels: string[]): Paragraph {
  if (!labels.length) return emptyLine()
  return new Paragraph({
    children: labels.map((l, i) =>
      txt(i < labels.length - 1 ? `${l}  ·  ` : l, { size: FONT_SIZE_SM, color: COLOR_MUTED }),
    ),
    spacing: { after: 60 },
  })
}

/** 简易两列表格 */
function keyValueTable(rows: [string, string][]): Table {
  const border = { style: BorderStyle.SINGLE, size: 1, color: COLOR_BORDER }
  return new Table({
    width: { size: 100, type: WidthType.PERCENTAGE },
    rows: rows.map(([k, v]) =>
      new TableRow({
        children: [
          new TableCell({
            width: { size: 22, type: WidthType.PERCENTAGE },
            shading: { type: ShadingType.SOLID, color: COLOR_BG },
            borders: { top: border, bottom: border, left: border, right: border },
            children: [new Paragraph({
              children: [txt(k, { bold: true, size: FONT_SIZE_SM, color: COLOR_PRIMARY })],
            })],
          }),
          new TableCell({
            width: { size: 78, type: WidthType.PERCENTAGE },
            borders: { top: border, bottom: border, left: border, right: border },
            children: [new Paragraph({
              children: [txt(v || '—', { size: FONT_SIZE_SM, color: v ? COLOR_PRIMARY : COLOR_MUTED })],
            })],
          }),
        ],
      })
    ),
  })
}

// ── 主导出函数 ──────────────────────────────────────────

export async function exportRecordToWord(record: AIGenerateRecordDetail): Promise<void> {
  const title = record.source_title || 'AI 智能编辑结果'
  const result = record.result
  const params = record.params as Record<string, any> | undefined

  const children: DocChild[] = []

  // ═══ 标题 ═══
  children.push(
    new Paragraph({
      heading: HeadingLevel.HEADING_1,
      alignment: AlignmentType.CENTER,
      children: [txt(title, { bold: true, size: FONT_SIZE_H1, color: COLOR_BRAND })],
      spacing: { after: 80 },
    }),
    mutedPara(`生成时间：${record.created_at || '—'}`),
    emptyLine(),
  )

  // ═══ 输入原文 ═══
  children.push(headingBlock('输入原文', HeadingLevel.HEADING_2))
  children.push(para(record.input_text || ''))

  // ═══ 生成参数 ═══
  if (params) {
    children.push(headingBlock('生成参数', HeadingLevel.HEADING_2))
    children.push(chipRow([
      `标题 ${params.title_count || 1} 个`,
      params.summary_type === 'extract' ? '抽取式' : '生成式',
      params.title_style || '',
      params.summary_style || '',
      params.summary_length === 'short' ? '短摘要' : params.summary_length === 'long' ? '长摘要' : '短摘要+长摘要',
    ].filter(Boolean)))
  }

  if (!result) {
    children.push(mutedPara('（无生成结果数据）'))
    await downloadDocx(children, title)
    return
  }

  // ═══ 候选标题 ═══
  if ((result.candidate_titles || []).length) {
    children.push(headingBlock('候选标题', HeadingLevel.HEADING_2))
    for (const t of result.candidate_titles!) {
      children.push(para(`• ${t}`))
    }
  }

  // ═══ 短摘要 ═══
  if (result.summary_short) {
    children.push(headingBlock('短摘要', HeadingLevel.HEADING_2))
    children.push(para(result.summary_short))
  }

  // ═══ 长摘要 ═══
  if (result.summary_long) {
    children.push(headingBlock('长摘要', HeadingLevel.HEADING_2))
    children.push(para(result.summary_long))
  }

  // ═══ 关键词 ═══
  if ((result.keywords || []).length) {
    children.push(headingBlock('关键词', HeadingLevel.HEADING_2))
    const kw = result.keywords!.map(k => (typeof k === 'string' ? k : (k as any).word || String(k)))
    children.push(chipRow(kw))
  }

  // ═══ 六要素 ═══
  if (result.elements && result.elements.what) {
    children.push(headingBlock('新闻六要素', HeadingLevel.HEADING_2))
    const el = result.elements
    children.push(keyValueTable([
      ['人物/主体', el.who || ''],
      ['事件', el.what || ''],
      ['时间', el.when || ''],
      ['地点', el.where || ''],
      ['原因', el.why || ''],
      ['方式', el.how || ''],
    ]))
  }

  // ═══ 一致性检查 ═══
  if (result.has_consistency) {
    children.push(headingBlock('一致性检查', HeadingLevel.HEADING_2))
    const c = result.consistency as Record<string, any>

    const riskLabel: Record<string, string> = { low: '低风险', medium: '中风险', high: '高风险' }
    const riskColor: Record<string, string> = { low: COLOR_GREEN, medium: COLOR_WARN, high: COLOR_BRAND }

    children.push(para(
      `风险等级：${riskLabel[c.risk_level] || c.risk_level}`,
      { bold: true, color: riskColor[c.risk_level] || COLOR_PRIMARY },
    ))

    if (c.score !== undefined) {
      children.push(para(`综合匹配度：${(c.score * 100).toFixed(0)}%`, { color: COLOR_SECONDARY }))
    }

    if ((c.issues || []).length) {
      children.push(para('发现的问题：', { bold: true, size: FONT_SIZE_SM }))
      for (const iss of c.issues!) {
        children.push(para(`• ${iss}`, { size: FONT_SIZE_SM, color: COLOR_SECONDARY }))
      }
    }

    if ((c.check_items || []).length) {
      children.push(para('检查项：', { bold: true, size: FONT_SIZE_SM }))
      for (const item of c.check_items!) {
        const statusIcon = item.status === 'pass' ? '✓' : item.status === 'warn' ? '⚠' : '✗'
        children.push(para(`${statusIcon} ${item.name}: ${item.message}`, { size: FONT_SIZE_SM, color: COLOR_SECONDARY }))
      }
    }

    if ((c.suggestions || []).length) {
      children.push(para('改进建议：', { bold: true, size: FONT_SIZE_SM }))
      for (const s of c.suggestions!) {
        children.push(para(`• ${s}`, { size: FONT_SIZE_SM, color: COLOR_SECONDARY }))
      }
    }
  }

  await downloadDocx(children, title)
}

// ── 生成并下载 ──────────────────────────────────────────

async function downloadDocx(children: DocChild[], title: string): Promise<void> {
  const doc = new Document({
    sections: [{
      properties: {},
      children: children as any[], // docx v9 接受 Paragraph | Table
    }],
  })

  const blob = await Packer.toBlob(doc)

  const safeTitle = title
    .replace(/[\\/:*?"<>|]/g, '')
    .slice(0, 40)
    .trim() || 'AI生成结果'

  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${safeTitle}.docx`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}
