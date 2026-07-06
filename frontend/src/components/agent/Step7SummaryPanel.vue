<script setup lang="ts">
/** Step7SummaryPanel — 简洁模式一致性检查面板（AI 生成页）。
 *
 * 用途：在 AI 编辑页面中展示 Top-K 关键一致性问题，避免全量输出淹没重点。
 * 规则：
 *   - 优先展示 hallucination（幻觉）类型，其次 drift（偏离），最后 score 最低的 match
 *   - 最多展示 5 条（3 条最严重 + 2 条最低分）
 *   - 显示整体风险摘要 + 风险等级标签
 *
 * 输入：consistencyData — Step 7 完整输出对象 { risk_level, risk_label, similarity_map[], check_items[], suggestions[] }
 * 输出：纯展示，无事件
 * 依赖：无外部依赖
 */

import { computed } from 'vue'

const props = defineProps<{
  consistencyData: Record<string, any> | null | undefined
}>()

// ── 评分颜色映射 ──
function scoreColor(score: number): string {
  if (score >= 0.9) return '#16a34a'
  if (score >= 0.7) return '#22c55e'
  if (score >= 0.5) return '#f59e0b'
  if (score >= 0.3) return '#f97316'
  return '#ef4444'
}

function typeLabel(type: string): string {
  switch (type) {
    case 'match': return '匹配'
    case 'drift': return '偏离'
    case 'hallucination': return '幻觉'
    default: return type || '未知'
  }
}

function riskTag(level: string): 'success' | 'warning' | 'danger' | 'info' {
  switch (level) {
    case 'low': return 'success'
    case 'medium': return 'warning'
    case 'high': return 'danger'
    default: return 'info'
  }
}

function riskText(level: string): string {
  switch (level) {
    case 'low': return '高质量'
    case 'medium': return '中质量'
    case 'high': return '低质量'
    default: return level || '未知'
  }
}

// ── 提取最严重问题 ──
const topIssues = computed(() => {
  const simMap = props.consistencyData?.similarity_map || []
  if (!simMap.length) return []

  // 深拷贝避免修改原数据
  const items = [...simMap] as Array<{
    summary_sentence: string
    source_sentence: string
    score: number
    type: string
    reason: string
  }>

  // 严重度排序：hallucination > drift > match（同类型按 score 升序）
  const typeOrder: Record<string, number> = { hallucination: 0, drift: 1, match: 2 }
  items.sort((a, b) => {
    const ta = typeOrder[a.type] ?? 3
    const tb = typeOrder[b.type] ?? 3
    if (ta !== tb) return ta - tb
    return a.score - b.score // 低分优先
  })

  // 最多取 5 条：优先不同类型各取一条 + 补充低分
  const result: typeof items = []
  const typeCount: Record<string, number> = {}
  for (const item of items) {
    if (result.length >= 5) break
    const t = item.type
    const cur = typeCount[t] || 0
    // 每种类型最多 2 条
    if (cur < 2) {
      result.push(item)
      typeCount[t] = cur + 1
    }
  }
  return result
})

// ── 严重程度标签 ──
function severityLabel(item: { type: string; score: number }): string {
  if (item.type === 'hallucination') return '严重'
  if (item.type === 'drift') return '偏离'
  if (item.score < 0.7) return '注意'
  return '轻微'
}

function severityColor(item: { type: string; score: number }): string {
  if (item.type === 'hallucination') return '#ef4444'
  if (item.type === 'drift') return '#f59e0b'
  if (item.score < 0.7) return '#f97316'
  return '#6b7280'
}

// ── 整体摘要 ──
const riskSummary = computed(() => {
  const data = props.consistencyData
  if (!data) return ''
  const simMap = data.similarity_map || []
  if (!simMap.length) return riskText(data.risk_level || '')

  const total = simMap.length
  const hallucinations = simMap.filter((s: any) => s.type === 'hallucination').length
  const drifts = simMap.filter((s: any) => s.type === 'drift').length
  const matches = simMap.filter((s: any) => s.type === 'match').length
  const avgScore = simMap.reduce((sum: number, s: any) => sum + (s.score || 0), 0) / total

  const parts: string[] = []
  if (hallucinations > 0) parts.push(`${hallucinations} 处幻觉`)
  if (drifts > 0) parts.push(`${drifts} 处偏离`)
  parts.push(`${matches} 处匹配`)
  parts.push(`均分 ${(avgScore * 100).toFixed(0)}%`)
  return parts.join(' · ')
})
</script>

<template>
  <div class="s7s" v-if="consistencyData">
    <!-- ═══ 风险总览 ═══ -->
    <div class="s7s__summary">
      <div class="s7s__risk-row">
        <span class="s7s__risk-label">综合质量</span>
        <el-tag :type="riskTag(consistencyData.risk_level)" effect="dark" size="small">
          {{ riskText(consistencyData.risk_level) }}
        </el-tag>
        <span class="s7s__risk-desc">{{ riskSummary }}</span>
      </div>
    </div>

    <!-- ═══ Top-K 关键问题 ═══ -->
    <div v-if="topIssues.length" class="s7s__issues">
      <span class="s7s__section-title">关键问题</span>
      <div
        v-for="(item, i) in topIssues"
        :key="i"
        class="s7s__issue-card"
        :class="'s7s__issue--' + item.type"
      >
        <!-- 严重度 + 类型 -->
        <div class="s7s__issue-head">
          <span class="s7s__severity-tag" :style="{ backgroundColor: severityColor(item) }">
            {{ severityLabel(item) }}
          </span>
          <span class="s7s__type-tag" :style="{ backgroundColor: scoreColor(item.score), color: '#fff' }">
            {{ typeLabel(item.type) }}
          </span>
          <span class="s7s__issue-score" :style="{ color: scoreColor(item.score) }">
            {{ (item.score * 100).toFixed(0) }}%
          </span>
        </div>
        <!-- 摘要句内容 -->
        <p class="s7s__issue-text">{{ item.summary_sentence }}</p>
        <!-- 原因简述 -->
        <p class="s7s__issue-reason">{{ item.reason }}</p>
      </div>
    </div>

    <!-- ═══ 检查项摘要（仅 warn/fail） ═══ -->
    <div v-if="(consistencyData.check_items || []).filter((c: any) => c.status !== 'pass').length" class="s7s__checks">
      <span class="s7s__section-title">待关注项</span>
      <div
        v-for="(item, i) in consistencyData.check_items.filter((c: any) => c.status !== 'pass')"
        :key="i"
        class="s7s__check-row"
      >
        <span class="s7s__check-dot" :class="item.status === 'fail' ? 'is-fail' : 'is-warn'"></span>
        <strong>{{ item.name }}</strong>
        <span class="s7s__check-msg">{{ item.message }}</span>
      </div>
    </div>

    <!-- ═══ 空状态 ═══ -->
    <div v-if="!topIssues.length && !(consistencyData.check_items || []).filter((c: any) => c.status !== 'pass').length" class="s7s__empty">
      未检测到明显问题
    </div>
  </div>
</template>

<style scoped>
.s7s {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* ── 风险总览 ── */
.s7s__summary {
  padding: 10px 14px;
  background: var(--color-bg-hover);
  border-radius: 8px;
}
.s7s__risk-row {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}
.s7s__risk-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text-secondary);
}
.s7s__risk-desc {
  font-size: 12px;
  color: var(--color-text-muted);
}

/* ── 分区标题 ── */
.s7s__section-title {
  display: block;
  font-size: 11px;
  font-weight: 600;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: .03em;
  margin-bottom: 6px;
}

/* ── 关键问题卡片 ── */
.s7s__issues {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.s7s__issue-card {
  padding: 10px 12px;
  background: var(--color-bg-hover);
  border-radius: 8px;
  border-left: 3px solid var(--color-border);
  transition: all .15s;
}
.s7s__issue-card:hover {
  background: var(--color-bg-card);
  box-shadow: 0 1px 4px rgba(0,0,0,.06);
}
.s7s__issue--hallucination {
  border-left-color: #ef4444;
  background: var(--color-primary-soft);
}
.s7s__issue--drift {
  border-left-color: #f59e0b;
  background: var(--color-warning-soft);
}

.s7s__issue-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.s7s__severity-tag {
  padding: 1px 8px;
  border-radius: 3px;
  color: #fff;
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
}

.s7s__type-tag {
  padding: 1px 8px;
  border-radius: 3px;
  font-size: 10px;
  font-weight: 600;
}

.s7s__issue-score {
  margin-left: auto;
  font-size: 14px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}

.s7s__issue-text {
  margin: 0 0 4px;
  font-size: 12px;
  line-height: 1.5;
  color: var(--color-text-primary);
}

.s7s__issue-reason {
  margin: 0;
  font-size: 11px;
  color: var(--color-text-muted);
  font-style: italic;
}

/* ── 待关注检查项 ── */
.s7s__checks {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.s7s__check-row {
  display: flex;
  align-items: baseline;
  gap: 6px;
  font-size: 12px;
  color: var(--color-text-secondary);
}
.s7s__check-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  flex-shrink: 0;
  margin-top: 6px;
}
.s7s__check-dot.is-fail { background: #ef4444; }
.s7s__check-dot.is-warn { background: #f59e0b; }
.s7s__check-msg {
  color: var(--color-text-muted);
  margin-left: 4px;
}

/* ── 空状态 ── */
.s7s__empty {
  padding: 16px;
  text-align: center;
  font-size: 12px;
  color: var(--color-text-muted);
  background: var(--color-bg-hover);
  border-radius: 8px;
}
</style>
