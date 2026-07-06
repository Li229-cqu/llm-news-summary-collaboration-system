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

export type RiskLevel = 'low' | 'medium' | 'high'
export type QualityLevel = 'high' | 'medium' | 'low'
type ResultSource = 'llm' | 'deepseek' | 'zhipu' | 'glm' | 'mock' | 'fallback' | 'demo' | 'nlp_rule' | 'unknown'
type GenerationSource = ResultSource

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

export function normalizeRiskLevel(value: unknown, fallback: RiskLevel = 'medium'): RiskLevel {
  const raw = toStringValue(value).trim().toLowerCase()
  if (raw === 'low' || raw === 'medium' || raw === 'high') return raw
  if (raw === '低风险') return 'low'
  if (raw === '中风险' || raw === '中等风险') return 'medium'
  if (raw === '高风险') return 'high'
  return fallback
}

export function riskLevelToQualityLevel(riskLevel: unknown): QualityLevel {
  const normalized = normalizeRiskLevel(riskLevel)
  if (normalized === 'low') return 'high'
  if (normalized === 'high') return 'low'
  return 'medium'
}

export function getQualityLabel(qualityLevel: unknown): string {
  if (qualityLevel === 'high') return '高质量'
  if (qualityLevel === 'low') return '低质量'
  return '中质量'
}

export function getQualityTagType(qualityLevel: unknown): 'success' | 'warning' | 'danger' | 'info' {
  if (qualityLevel === 'high') return 'success'
  if (qualityLevel === 'low') return 'danger'
  if (qualityLevel === 'medium') return 'warning'
  return 'info'
}

export function getRiskLabel(riskLevel: unknown): string {
  const normalized = normalizeRiskLevel(riskLevel)
  if (normalized === 'low') return '低风险'
  if (normalized === 'high') return '高风险'
  return '中风险'
}

export function getQualityLabelFromRisk(riskLevel: unknown): string {
  return getQualityLabel(riskLevelToQualityLevel(riskLevel))
}

export function getQualityTagTypeFromRisk(riskLevel: unknown): 'success' | 'warning' | 'danger' | 'info' {
  return getQualityTagType(riskLevelToQualityLevel(riskLevel))
}

export function normalizeAISource(value: unknown, fallback: ResultSource = 'unknown'): ResultSource {
  const raw = toStringValue(value).trim().toLowerCase()
  if (!raw) return fallback
  if (['deepseek', 'llm_deepseek', 'summary_deepseek'].includes(raw)) return 'deepseek'
  if (['zhipu', 'glm', 'llm_zhipu', 'glm-4', 'glm4'].includes(raw)) return 'zhipu'
  if (['llm', 'openai', 'model', 'ai'].includes(raw)) return 'llm'
  if (raw === 'fallback' || raw === 'fallback_rule') return 'fallback'
  if (['nlp_rule', 'rule', 'nlp', 'local_rules', 'local', 'algorithm', 'extractive'].includes(raw)) return 'nlp_rule'
  if (raw === 'mock') return 'mock'
  if (raw === 'demo') return 'demo'
  return fallback
}

function pickResultSource(value: unknown): ResultSource | undefined {
  const normalized = normalizeAISource(value)
  return normalized === 'unknown' ? undefined : normalized
}

function pickGenerationSource(value: unknown): GenerationSource | undefined {
  const normalized = normalizeAISource(value)
  return normalized === 'unknown' ? undefined : normalized
}

function buildEmptyElements(): NewsElement {
  return { who: '', what: '', when: '', where: '', why: '', how: '' }
}

function buildEmptyConsistency(): ConsistencyCheck {
  return { score: 0, risk_level: 'medium', issues: [], suggestions: [] }
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
      risk_level: normalizeRiskLevel(value.risk_level),
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
    return provider && provider !== 'mock' && provider !== 'local' && provider !== 'nlp' && provider !== 'fallback_rule'
  })
}

function normalizeFromDirectResult(result: Record<string, any>): AIGenerateResponse {
  const source = pickResultSource(result.source) ?? 'unknown'
  const generationSource = pickGenerationSource(result.generation_source)
    ?? (source === 'unknown' ? 'unknown' : source)

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
    risk_level: result.risk_level ? normalizeRiskLevel(result.risk_level) : undefined,
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
    ?? (provider && provider !== 'mock' && provider !== 'local' && provider !== 'nlp' && provider !== 'fallback_rule'
      ? 'llm'
      : hasRealStepSignal(steps)
        ? 'llm'
        : fallbackReason
          ? 'fallback'
          : 'unknown')

  const generationSource = pickGenerationSource(isRecord(source) ? source.generation_source : undefined)
    ?? (sourceTag === 'unknown' ? 'unknown' : sourceTag)

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
    risk_level: normalizeRiskLevel(riskLevel),
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
  return normalizeAISource(fallbackSource || result.generation_source || result.source)
}

export function normalizeAIGenerateHistoryRecord(
  record: AIGenerateRecordItem | (Partial<AIGenerateRecordItem> & Record<string, unknown>),
): NormalizedAIGenerateHistoryRecord {
  const standardResult = normalizeAIGenerateResult(record)
  // 来源优先用后端标准化后的 ai_source，API 数据比客户端推算更可靠
  const displaySource = resolveSource(standardResult, record.ai_source)
  const riskLevel = normalizeRiskLevel(record.risk_level ?? standardResult.risk_level ?? standardResult.consistency?.risk_level)
  standardResult.risk_level = riskLevel
  standardResult.consistency.risk_level = riskLevel

  return {
    id: record.id ?? '',
    source: record.source ?? 'manual',
    source_news_id: record.source_news_id ?? null,
    source_title: record.source_title ?? '',
    title_count: typeof record.title_count === 'number' ? record.title_count : 0,
    risk_level: riskLevel,
    ai_source: displaySource,
    created_at: record.created_at ?? '',
    candidate_titles: Array.isArray(record.candidate_titles) ? record.candidate_titles : standardResult.candidate_titles,
    summary_short: typeof record.summary_short === 'string' ? record.summary_short : standardResult.summary_short,
    displayTitle: getHistoryDisplayTitle(standardResult, record.source_title ?? ''),
    displaySummary: getHistoryDisplaySummary(standardResult),
    displaySource,
    displaySourceTagType: getAISourceTagType(displaySource),
    standardResult,
  }
}

export function normalizeAIGenerateHistoryDetail(
  detail: AIGenerateRecordDetail | (Partial<AIGenerateRecordDetail> & Record<string, unknown>),
): NormalizedAIGenerateHistoryDetail {
  const standardResult = normalizeAIGenerateResult(detail.result ?? detail)
  const source = normalizeAISource(detail.ai_source || standardResult.generation_source || standardResult.source)
  const riskLevel = normalizeRiskLevel(detail.risk_level || standardResult.risk_level || standardResult.consistency?.risk_level)
  standardResult.source = source
  standardResult.generation_source = source
  standardResult.risk_level = riskLevel
  standardResult.consistency.risk_level = riskLevel

  return {
    id: detail.id ?? '',
    source: detail.source ?? 'manual',
    source_news_id: detail.source_news_id ?? null,
    source_title: detail.source_title ?? '',
    input_text: detail.input_text ?? '',
    params: detail.params ?? {},
    result: standardResult,
    created_at: detail.created_at ?? '',
    ai_source: source,
    risk_level: riskLevel,
    standardResult,
  }
}

export function formatProviderModel(provider?: string, model?: string): string {
  const p = formatProviderLabel(provider)
  const m = formatProviderLabel(model)
  if (p && m) return `${p} / ${m}`
  if (p) return p
  if (m) return m
  return ''
}

export function formatProviderLabel(provider?: string): string {
  const value = provider?.trim()
  if (!value) return ''
  const lower = value.toLowerCase()
  if (lower === 'deepseek') return 'DeepSeek'
  if (lower === 'zhipu' || lower === 'glm') return '智谱'
  if (lower === 'llm' || lower === 'ai' || lower === 'model') return 'AI'
  if (lower === 'mock') return '演示'
  if (lower === 'demo') return '演示'
  if (lower === 'local' || lower === 'nlp' || lower === 'fallback_rule') return 'NLP 规则'
  return value
}

export function getAIGenerateSourceLabel(source?: string, generationSource?: string): string {
  const resolved = normalizeAISource(source || generationSource) || 'unknown'
  switch (resolved) {
    case 'deepseek':
      return 'DeepSeek 生成'
    case 'zhipu':
    case 'glm':
      return 'AI 生成'
    case 'llm':
      return 'AI 生成'
    case 'fallback':
      return '降级生成'
    case 'nlp_rule':
      return 'NLP 规则生成'
    case 'mock':
    case 'demo':
      return '演示生成'
    default:
      return '未知来源'
  }
}

export function getAIGenerateSourceTagType(source?: string, generationSource?: string): 'success' | 'warning' | 'info' {
  const resolved = normalizeAISource(source || generationSource) || 'unknown'
  switch (resolved) {
    case 'deepseek':
    case 'zhipu':
    case 'glm':
    case 'llm':
      return 'success'
    case 'fallback':
      return 'warning'
    default:
      return 'info'
  }
}

export function getAISourceLabel(source?: string, generationSource?: string): string {
  const resolved = normalizeAISource(source || generationSource)
  switch (resolved) {
    case 'deepseek':
      return 'DeepSeek 生成'
    case 'zhipu':
    case 'glm':
      return 'AI 生成'
    case 'llm':
      return 'AI 生成'
    case 'nlp_rule':
      return 'NLP 规则生成'
    case 'fallback':
      return '降级生成'
    case 'mock':
    case 'demo':
      return '演示生成'
    default:
      return '未知来源'
  }
}

export function getAISourceTagType(source?: string, generationSource?: string): 'success' | 'warning' | 'info' {
  const resolved = normalizeAISource(source || generationSource)
  if (resolved === 'llm' || resolved === 'deepseek' || resolved === 'zhipu' || resolved === 'glm') return 'success'
  if (resolved === 'fallback') return 'warning'
  return 'info'
}
