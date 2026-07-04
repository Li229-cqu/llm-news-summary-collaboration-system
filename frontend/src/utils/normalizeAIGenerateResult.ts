import type {
  AIGenerateRecordDetail,
  AIGenerateRecordItem,
  AIGenerateResponse,
  ConsistencyCheck,
  EvidenceChain,
  NewsElement,
} from '@/api/ai'

export interface AgentStepSnapshot {
  name?: string
  step?: string
  provider?: string
  model?: string
  output?: Record<string, any> | null
}

export interface NormalizeAIGenerateResultOptions {
  steps?: AgentStepSnapshot[]
}

export interface NormalizedAIGenerateHistoryRecord extends AIGenerateRecordItem {
  standardResult: AIGenerateResponse
  displayTitle: string
  displaySummary: string
  displaySource: string
  displaySourceTagType: 'success' | 'warning' | 'info'
}

export interface NormalizedAIGenerateHistoryDetail extends AIGenerateRecordDetail {
  standardResult: AIGenerateResponse
}

type ResultSource = 'llm' | 'mock' | 'fallback' | 'demo'
type GenerationSource = 'llm' | 'mock' | 'fallback'

function isRecord(value: unknown): value is Record<string, any> {
  return !!value && typeof value === 'object' && !Array.isArray(value)
}

function toStringValue(value: unknown, fallback = ''): string {
  if (typeof value === 'string') return value
  if (value === null || value === undefined) return fallback
  return String(value)
}

function toStringArray(value: unknown): string[] {
  if (!Array.isArray(value)) return []
  return value.map(item => toStringValue(item).trim()).filter(Boolean)
}

function pickResultSource(value: unknown): ResultSource | undefined {
  if (value === 'llm' || value === 'mock' || value === 'fallback' || value === 'demo') {
    return value
  }
  return undefined
}

function pickGenerationSource(value: unknown): GenerationSource | undefined {
  if (value === 'llm' || value === 'mock' || value === 'fallback') {
    return value
  }
  return undefined
}

function buildEmptyElements(): NewsElement {
  return { who: '', what: '', when: '', where: '', why: '', how: '' }
}

function buildEmptyConsistency(): ConsistencyCheck {
  return { score: 0, risk_level: 'low', issues: [], suggestions: [] }
}

function hasConsistencyData(value: unknown): boolean {
  return isRecord(value) && Object.keys(value).length > 0
}

function safeNumber(value: unknown, fallback: number | undefined = 0): number | undefined {
  if (typeof value === 'number' && Number.isFinite(value)) return value
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : fallback
}

function extractNestedResult(source: unknown): unknown {
  if (!isRecord(source)) return source
  return source.standardResult
    ?? source.result
    ?? source.result_json
    ?? source.response
    ?? source.output
    ?? source.generated_result
    ?? source.data
}

function collectStepOutputs(source: unknown, steps: AgentStepSnapshot[] = []): Record<string, any>[] {
  const results: Record<string, any>[] = []

  if (Array.isArray(source)) {
    for (const item of source) {
      if (isRecord(item)) results.push(item)
    }
  } else if (isRecord(source)) {
    const maybeResults = source.result_json ?? source.result ?? source.steps
    if (Array.isArray(maybeResults)) {
      for (const item of maybeResults) {
        if (isRecord(item)) results.push(item)
      }
    }
  }

  for (const step of steps) {
    if (step?.output && isRecord(step.output)) {
      results.push({
        step: step.step || step.name,
        provider: step.provider,
        model: step.model,
        output: step.output,
      })
    }
  }

  return results
}

function pickStepOutput(stepResults: Record<string, any>[], stepName: string): Record<string, any> | null {
  for (let i = stepResults.length - 1; i >= 0; i -= 1) {
    const item = stepResults[i]
    const name = toStringValue(item.step || item.name)
    if (name === stepName) {
      if (isRecord(item.output)) return item.output
      return item
    }
  }
  return null
}

function normalizeElements(value: unknown): NewsElement {
  if (isRecord(value)) {
    return {
      who: toStringValue(value.who),
      what: toStringValue(value.what),
      when: toStringValue(value.when),
      where: toStringValue(value.where),
      why: toStringValue(value.why),
      how: toStringValue(value.how),
    }
  }
  return buildEmptyElements()
}

function normalizeConsistency(value: unknown): ConsistencyCheck {
  if (isRecord(value)) {
    return {
      score: safeNumber(value.score, 0) ?? 0,
      risk_level: value.risk_level === 'high' || value.risk_level === 'medium' ? value.risk_level : 'low',
      issues: toStringArray(value.issues),
      suggestions: toStringArray(value.suggestions),
    }
  }
  return buildEmptyConsistency()
}

function normalizeEvidenceChain(value: unknown): EvidenceChain | undefined {
  if (!isRecord(value)) return undefined
  const sentences = Array.isArray(value.sentences) ? value.sentences.filter(item => isRecord(item)) : []
  const coverage = safeNumber(value.evidence_coverage, 0) ?? 0
  if (!sentences.length && !Number.isFinite(coverage)) return undefined
  return {
    sentences: sentences as EvidenceChain['sentences'],
    evidence_coverage: coverage,
  }
}

function hasRealStepSignal(steps: AgentStepSnapshot[] = []): boolean {
  return steps.some(step => {
    const provider = toStringValue(step.provider).toLowerCase()
    return provider && provider !== 'mock' && provider !== 'local'
  })
}

function normalizeFromDirectResult(result: Record<string, any>): AIGenerateResponse {
  const source = pickResultSource(result.source) ?? 'mock'
  const generationSource = pickGenerationSource(result.generation_source)
    ?? (source === 'fallback' ? 'fallback' : source === 'llm' ? 'llm' : 'mock')

  return {
    candidate_titles: toStringArray(result.candidate_titles),
    summary_short: toStringValue(result.summary_short),
    summary_long: toStringValue(result.summary_long),
    summary_points: toStringArray(result.summary_points),
    keywords: toStringArray(result.keywords),
    elements: normalizeElements(result.elements),
    consistency: normalizeConsistency(result.consistency),
    source,
    generation_source: generationSource,
    has_consistency: hasConsistencyData(result.consistency),
    provider: toStringValue(result.provider) || undefined,
    model: toStringValue(result.model) || undefined,
    fallback_reason: toStringValue(result.fallback_reason) || undefined,
    evidence_chain: normalizeEvidenceChain(result.evidence_chain),
    evidence_chain_short: normalizeEvidenceChain(result.evidence_chain_short),
    evidence_chain_long: normalizeEvidenceChain(result.evidence_chain_long),
    risk_level: result.risk_level === 'high' || result.risk_level === 'medium' ? result.risk_level : undefined,
    risk_details: toStringValue(result.risk_details) || undefined,
    evidence_coverage: safeNumber(result.evidence_coverage, undefined),
  }
}

function normalizeFromAgentResult(source: unknown, steps: AgentStepSnapshot[]): AIGenerateResponse {
  const stepResults = collectStepOutputs(source, steps)
  const summaryStep = pickStepOutput(stepResults, 'generate_title_summary')
  const consistencyStep = pickStepOutput(stepResults, 'check_consistency')
  const evidenceStep = pickStepOutput(stepResults, 'judge_timeline')

  const candidateTitles = toStringArray(
    summaryStep?.candidate_titles
      ?? summaryStep?.output?.candidate_titles
      ?? (isRecord(source) ? source.candidate_titles : undefined),
  )

  const summaryShort = toStringValue(
    summaryStep?.summary_short
      ?? summaryStep?.output?.summary_short
      ?? (isRecord(source) ? source.summary_short : undefined)
      ?? (isRecord(source) && typeof source.summary === 'string' ? source.summary : ''),
  )

  const summaryLong = toStringValue(
    summaryStep?.summary_long
      ?? summaryStep?.output?.summary_long
      ?? (isRecord(source) ? source.summary_long : undefined),
  )

  const summaryPoints = toStringArray(
    summaryStep?.summary_points
      ?? summaryStep?.output?.summary_points
      ?? (isRecord(source) ? source.summary_points : undefined),
  )

  const keywords = toStringArray(
    summaryStep?.keywords
      ?? summaryStep?.output?.keywords
      ?? (isRecord(source) ? source.keywords : undefined),
  )

  const elements = normalizeElements(
    summaryStep?.elements
      ?? summaryStep?.output?.elements
      ?? (isRecord(source) ? source.elements : undefined),
  )

  const consistency = normalizeConsistency(
    consistencyStep?.consistency
      ?? consistencyStep?.output?.consistency
      ?? (isRecord(source) ? source.consistency : undefined),
  )

  const riskLevel = (
    isRecord(source) && (source.risk_level === 'low' || source.risk_level === 'medium' || source.risk_level === 'high')
      ? source.risk_level
      : consistency.risk_level
  ) as AIGenerateResponse['risk_level']

  const riskDetails = toStringValue(isRecord(source) ? source.risk_details : undefined) || undefined

  const evidenceCoverage = safeNumber(
    isRecord(source) ? source.evidence_coverage : evidenceStep?.evidence_coverage,
    undefined,
  )

  const provider = toStringValue(
    isRecord(source) ? source.provider : summaryStep?.provider ?? summaryStep?.output?.provider,
  ) || steps.find(step => step.provider)?.provider || undefined

  const model = toStringValue(
    isRecord(source) ? source.model : summaryStep?.model ?? summaryStep?.output?.model,
  ) || steps.find(step => step.model)?.model || undefined

  const fallbackReason = toStringValue(isRecord(source) ? source.fallback_reason : undefined) || undefined
  const rawConsistency = isRecord(source) ? source.consistency : undefined

  const sourceTag = pickResultSource(isRecord(source) ? source.source : undefined)
    ?? (provider && provider !== 'mock' && provider !== 'local'
      ? 'llm'
      : hasRealStepSignal(steps)
        ? 'llm'
        : fallbackReason
          ? 'fallback'
          : 'mock')

  const generationSource = pickGenerationSource(isRecord(source) ? source.generation_source : undefined)
    ?? (sourceTag === 'fallback' ? 'fallback' : sourceTag === 'llm' ? 'llm' : 'mock')

  return {
    candidate_titles: candidateTitles,
    summary_short: summaryShort,
    summary_long: summaryLong,
    summary_points: summaryPoints,
    keywords,
    elements,
    consistency,
    source: sourceTag,
    generation_source: generationSource,
    has_consistency: hasConsistencyData(rawConsistency)
      || hasConsistencyData(consistencyStep?.consistency)
      || hasConsistencyData(consistencyStep?.output?.consistency)
      || hasConsistencyData(consistencyStep?.output),
    provider,
    model,
    fallback_reason: fallbackReason,
    risk_level: riskLevel,
    risk_details: riskDetails,
    evidence_coverage: evidenceCoverage,
    evidence_chain_short: normalizeEvidenceChain(isRecord(source) ? source.evidence_chain_short : undefined),
    evidence_chain_long: normalizeEvidenceChain(isRecord(source) ? source.evidence_chain_long : undefined),
    evidence_chain: normalizeEvidenceChain(isRecord(source) ? source.evidence_chain : undefined),
  }
}

export function normalizeAIGenerateResult(source: unknown, options: NormalizeAIGenerateResultOptions = {}): AIGenerateResponse {
  const nestedResult = extractNestedResult(source)

  if (isRecord(source)) {
    const directKeys = ['candidate_titles', 'summary_short', 'summary_long', 'summary_points', 'keywords', 'elements', 'consistency']
    if (directKeys.some(key => key in source)) {
      return normalizeFromDirectResult(source)
    }
  }

  if (isRecord(nestedResult)) {
    const directKeys = ['candidate_titles', 'summary_short', 'summary_long', 'summary_points', 'keywords', 'elements', 'consistency']
    if (directKeys.some(key => key in nestedResult)) {
      return normalizeFromDirectResult(nestedResult)
    }
  }

  return normalizeFromAgentResult(nestedResult ?? source, options.steps ?? [])
}

function getHistoryDisplayTitle(result: AIGenerateResponse, sourceTitle: string): string {
  if (result.candidate_titles.length > 0 && result.candidate_titles[0]) return result.candidate_titles[0]
  if (result.summary_short) return result.summary_short.slice(0, 42)
  if (result.summary_long) return result.summary_long.slice(0, 42)
  return sourceTitle || '暂无标题'
}

function getHistoryDisplaySummary(result: AIGenerateResponse): string {
  return result.summary_short || result.summary_long || '暂无摘要'
}

function resolveSource(result: AIGenerateResponse, fallbackSource?: string): string {
  return result.generation_source || result.source || fallbackSource || ''
}

export function normalizeAIGenerateHistoryRecord(
  record: AIGenerateRecordItem | (Partial<AIGenerateRecordItem> & Record<string, unknown>),
): NormalizedAIGenerateHistoryRecord {
  const standardResult = normalizeAIGenerateResult(record)
  const displaySource = resolveSource(standardResult, record.ai_source)

  return {
    id: record.id ?? '',
    source: record.source ?? 'manual',
    source_news_id: record.source_news_id ?? null,
    source_title: record.source_title ?? '',
    title_count: typeof record.title_count === 'number' ? record.title_count : 0,
    risk_level: record.risk_level ?? standardResult.consistency?.risk_level ?? 'low',
    ai_source: record.ai_source,
    created_at: record.created_at ?? '',
    candidate_titles: Array.isArray(record.candidate_titles) ? record.candidate_titles : standardResult.candidate_titles,
    summary_short: typeof record.summary_short === 'string' ? record.summary_short : standardResult.summary_short,
    displayTitle: getHistoryDisplayTitle(standardResult, record.source_title ?? ''),
    displaySummary: getHistoryDisplaySummary(standardResult),
    displaySource,
    displaySourceTagType: getAIGenerateSourceTagType(displaySource),
    standardResult,
  }
}

export function normalizeAIGenerateHistoryDetail(
  detail: AIGenerateRecordDetail | (Partial<AIGenerateRecordDetail> & Record<string, unknown>),
): NormalizedAIGenerateHistoryDetail {
  const standardResult = normalizeAIGenerateResult(detail.result ?? detail)

  return {
    id: detail.id ?? '',
    source: detail.source ?? 'manual',
    source_news_id: detail.source_news_id ?? null,
    source_title: detail.source_title ?? '',
    input_text: detail.input_text ?? '',
    params: detail.params ?? {},
    result: standardResult,
    created_at: detail.created_at ?? '',
    standardResult,
  }
}

export function formatProviderModel(provider?: string, model?: string): string {
  const p = provider?.trim()
  const m = model?.trim()
  if (p && m) return `${p} / ${m}`
  if (p) return p
  if (m) return m
  return ''
}

export function getAIGenerateSourceLabel(source?: string, generationSource?: string): string {
  const resolved = generationSource || source || ''
  // "NLP 规则生成" 指系统在未调用真实大模型时，基于分句、关键词抽取、规则模板和文本特征完成的本地生成方式。
  switch (resolved) {
    case 'llm':
      return '真实 AI'
    case 'fallback':
      return 'AI 回退至 NLP 规则生成'
    case 'mock':
      return 'NLP 规则生成'
    default:
      return '未知来源'
  }
}

export function getAIGenerateSourceTagType(source?: string, generationSource?: string): 'success' | 'warning' | 'info' {
  const resolved = generationSource || source || 'mock'
  switch (resolved) {
    case 'llm':
      return 'success'
    case 'fallback':
      return 'warning'
    default:
      return 'info'
  }
}
