<script setup lang="ts">
/** Step7AuditPanel — 完整审计模式一致性检查面板（历史详情页）。
 *
 * 用途：在历史记录详情页中展示完整的一致性检查结果，包含：
 *   - 风险等级 + 检查项 + 原文覆盖热力图 + 全量逐句对齐 + hover 对照预览 + 改进建议
 *
 * 输入：consistencyData — Step 7 完整输出对象
 * 输出：纯展示 + hover 交互
 * 依赖：无外部依赖
 */

import { ref } from 'vue'

const props = defineProps<{
  consistencyData: Record<string, any> | null | undefined
}>()

const hoveredSimItem = ref<any>(null)
const hoverX = ref(0)
const hoverY = ref(0)

// ── 评分颜色映射 ──
function scoreColor(score: number): string {
  if (score >= 0.9) return '#16a34a'
  if (score >= 0.7) return '#22c55e'
  if (score >= 0.5) return '#f59e0b'
  if (score >= 0.3) return '#f97316'
  return '#ef4444'
}

function heatmapColor(score: number): string {
  if (score >= 0.9) return '#22c55e'
  if (score >= 0.7) return '#86efac'
  if (score >= 0.5) return '#fde047'
  if (score >= 0.3) return '#fdba74'
  return '#fca5a5'
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
    case 'low': return '低风险'
    case 'medium': return '中风险'
    case 'high': return '高风险'
    default: return level || '未知'
  }
}

function onSimEnter(item: any, ev: MouseEvent) {
  hoveredSimItem.value = item
  hoverX.value = ev.clientX + 12
  hoverY.value = ev.clientY - 10
}

function onSimMove(ev: MouseEvent) {
  hoverX.value = ev.clientX + 12
  hoverY.value = ev.clientY - 10
}

function onSimLeave() {
  hoveredSimItem.value = null
}

// ── 统计 ──
function simStats(simMap: any[]) {
  if (!simMap?.length) return null
  const total = simMap.length
  const hallucinations = simMap.filter((s: any) => s.type === 'hallucination').length
  const drifts = simMap.filter((s: any) => s.type === 'drift').length
  const matches = simMap.filter((s: any) => s.type === 'match').length
  const avgScore = simMap.reduce((sum: number, s: any) => sum + (s.score || 0), 0) / total
  return { total, hallucinations, drifts, matches, avgScore }
}
</script>

<template>
  <div class="s7a" v-if="consistencyData">
    <!-- ═══ 风险等级 ═══ -->
    <div class="s7a__risk-row">
      <span class="s7a__risk-label">风险等级</span>
      <el-tag :type="riskTag(consistencyData.risk_level)" effect="dark" size="small">
        {{ riskText(consistencyData.risk_level) }}
      </el-tag>
      <span v-if="simStats(consistencyData.similarity_map)" class="s7a__stats">
        {{ simStats(consistencyData.similarity_map)!.total }} 句对齐 ·
        均分 {{ (simStats(consistencyData.similarity_map)!.avgScore * 100).toFixed(0) }}%
        <template v-if="simStats(consistencyData.similarity_map)!.hallucinations > 0">
          · {{ simStats(consistencyData.similarity_map)!.hallucinations }} 幻觉
        </template>
        <template v-if="simStats(consistencyData.similarity_map)!.drifts > 0">
          · {{ simStats(consistencyData.similarity_map)!.drifts }} 偏离
        </template>
      </span>
    </div>

    <!-- ═══ 检查项（SSE 格式：check_items） ═══ -->
    <div v-if="(consistencyData.check_items || []).length" class="s7a__checks">
      <span class="s7a__section-title">检查项</span>
      <div v-for="(item, i) in consistencyData.check_items" :key="i" class="s7a__check-item">
        <span class="s7a__check-icon">{{ item.status === 'pass' ? '✓' : item.status === 'warn' ? '!' : '✕' }}</span>
        <span class="s7a__check-status" :class="'is-' + item.status">{{ item.status === 'pass' ? '通过' : item.status === 'warn' ? '警告' : '异常' }}</span>
        <strong>{{ item.name }}</strong>
        <span class="s7a__check-msg">{{ item.message }}</span>
      </div>
    </div>

    <!-- ═══ 问题列表（DB 格式：issues 字符串数组） ═══ -->
    <div v-if="!(consistencyData.check_items || []).length && (consistencyData.issues || []).length" class="s7a__section">
      <span class="s7a__section-title">发现的问题</span>
      <div class="s7a__issue-list">
        <div v-for="(iss, i) in consistencyData.issues" :key="i" class="s7a__issue-row">
          <span class="s7a__issue-dot"></span>
          {{ iss }}
        </div>
      </div>
    </div>

    <!-- ═══ 匹配度分数（DB 格式） ═══ -->
    <div v-if="consistencyData.score !== undefined && consistencyData.score !== null" class="s7a__section">
      <span class="s7a__section-title">综合匹配度</span>
      <div class="s7a__score-bar-wrap">
        <div class="s7a__score-bar">
          <div
            class="s7a__score-bar-fill"
            :style="{ width: (consistencyData.score * 100).toFixed(0) + '%', backgroundColor: scoreColor(consistencyData.score) }"
          ></div>
        </div>
        <span class="s7a__score-val" :style="{ color: scoreColor(consistencyData.score) }">
          {{ (consistencyData.score * 100).toFixed(0) }}%
        </span>
      </div>
    </div>

    <!-- ═══ 原文覆盖度热力图 ═══ -->
    <div v-if="(consistencyData.highlight_segments || []).length" class="s7a__section">
      <span class="s7a__section-title">原文覆盖度</span>
      <div class="s7a__heatmap-bar">
        <div
          v-for="(seg, i) in consistencyData.highlight_segments"
          :key="i"
          class="s7a__heatmap-seg"
          :style="{ backgroundColor: heatmapColor(seg.score), flex: '1' }"
          :title="`${(seg.text_range || '').slice(0, 60)}…\n覆盖度: ${(seg.score * 100).toFixed(0)}%\n${seg.covered ? '已覆盖' : '未覆盖'}`"
        ></div>
      </div>
      <div class="s7a__heatmap-legend">
        <span class="s7a__legend-item"><span class="s7a__legend-dot" style="background:#22c55e"></span> 已覆盖(绿)</span>
        <span class="s7a__legend-item"><span class="s7a__legend-dot" style="background:#ef4444"></span> 未覆盖(红)</span>
        <span class="s7a__legend-item"><span class="s7a__legend-dot" style="background:#f59e0b"></span> 低匹配(黄)</span>
      </div>
    </div>

    <!-- ═══ 全量逐句对齐 ═══ -->
    <div v-if="(consistencyData.similarity_map || []).length" class="s7a__section">
      <span class="s7a__section-title">
        逐句对齐审计
        <span class="s7a__section-count">{{ consistencyData.similarity_map.length }} 句</span>
      </span>
      <div class="s7a__sim-list">
        <div
          v-for="(item, i) in consistencyData.similarity_map"
          :key="i"
          class="s7a__sim-item"
          @mouseenter="(e: MouseEvent) => onSimEnter(item, e)"
          @mousemove="onSimMove"
          @mouseleave="onSimLeave"
        >
          <!-- 头部：类型 + 分数 + 原因 -->
          <div class="s7a__sim-head">
            <span class="s7a__sim-type" :style="{ backgroundColor: scoreColor(item.score) }">
              {{ typeLabel(item.type) }}
            </span>
            <span class="s7a__sim-score" :style="{ color: scoreColor(item.score) }">
              {{ (item.score * 100).toFixed(0) }}%
            </span>
            <span class="s7a__sim-reason">{{ item.reason }}</span>
          </div>
          <!-- 分数条 -->
          <div class="s7a__sim-bar">
            <div
              class="s7a__sim-bar-fill"
              :style="{ width: (item.score * 100) + '%', backgroundColor: scoreColor(item.score) }"
            ></div>
          </div>
          <!-- AI 输出句 -->
          <p class="s7a__sim-ai-text">{{ item.summary_sentence }}</p>
          <!-- 原文对应句 -->
          <p v-if="item.source_sentence && item.source_sentence !== '无对应'" class="s7a__sim-src-text">
            {{ item.source_sentence }}
          </p>
          <p v-else class="s7a__sim-no-src">（原文中无对应内容）</p>
        </div>
      </div>
    </div>

    <!-- ═══ Hover 预览浮层 ═══ -->
    <Teleport to="body">
      <div
        v-if="hoveredSimItem"
        class="s7a__hover"
        :style="{ left: hoverX + 'px', top: hoverY + 'px' }"
      >
        <div class="s7a__hover-score" :style="{ color: scoreColor(hoveredSimItem.score) }">
          {{ (hoveredSimItem.score * 100).toFixed(0) }}%
        </div>
        <div class="s7a__hover-type">
          <el-tag
            :type="hoveredSimItem.type === 'match' ? 'success' : hoveredSimItem.type === 'drift' ? 'warning' : 'danger'"
            size="small"
          >{{ typeLabel(hoveredSimItem.type) }}</el-tag>
        </div>
        <p class="s7a__hover-text"><strong>AI 输出:</strong> {{ hoveredSimItem.summary_sentence }}</p>
        <p class="s7a__hover-text"><strong>原文:</strong> {{ hoveredSimItem.source_sentence || '无对应原文 — 可能为 AI 幻觉' }}</p>
        <p class="s7a__hover-text s7a__hover-text--dim"><strong>判断:</strong> {{ hoveredSimItem.reason }}</p>
      </div>
    </Teleport>

    <!-- ═══ 改进建议 ═══ -->
    <div v-if="(consistencyData.suggestions || []).length" class="s7a__section">
      <span class="s7a__section-title">改进建议</span>
      <ul class="s7a__suggestions">
        <li v-for="(s, i) in consistencyData.suggestions" :key="i">{{ s }}</li>
      </ul>
    </div>
  </div>
</template>

<style scoped>
.s7a {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.s7a__section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.s7a__section-title {
  font-size: 12px;
  font-weight: 600;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: .03em;
}

.s7a__section-count {
  font-weight: 400;
  color: #9ca3af;
  margin-left: 6px;
  font-size: 11px;
}

/* ── 风险等级行 ── */
.s7a__risk-row {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}
.s7a__risk-label {
  font-size: 13px;
  color: #6b7280;
}
.s7a__stats {
  font-size: 12px;
  color: #9ca3af;
}

/* ── 检查项 ── */
.s7a__checks {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.s7a__check-item {
  display: flex;
  align-items: baseline;
  gap: 6px;
  font-size: 13px;
  color: #555;
  padding: 6px 10px;
  background: #f9fafb;
  border-radius: 6px;
}
.s7a__check-icon {
  width: 18px;
  height: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  font-size: 10px;
  font-weight: 700;
  flex-shrink: 0;
  color: #fff;
}
.is-pass { color: #16a34a; }
.is-warn { color: #f59e0b; }
.is-fail { color: #ef4444; }
.s7a__check-item:has(.is-pass) .s7a__check-icon { background: #22c55e; }
.s7a__check-item:has(.is-warn) .s7a__check-icon { background: #f59e0b; }
.s7a__check-item:has(.is-fail) .s7a__check-icon { background: #ef4444; }
.s7a__check-status {
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  flex-shrink: 0;
}
.s7a__check-msg {
  color: #9ca3af;
  margin-left: 4px;
}

/* ── 热力图 ── */
.s7a__heatmap-bar {
  display: flex;
  height: 14px;
  border-radius: 7px;
  overflow: hidden;
  gap: 2px;
}
.s7a__heatmap-seg {
  min-width: 4px;
  border-radius: 2px;
  cursor: pointer;
  transition: opacity .15s;
}
.s7a__heatmap-seg:hover {
  opacity: .65;
}
.s7a__heatmap-legend {
  display: flex;
  gap: 14px;
  font-size: 11px;
  color: #9ca3af;
  align-items: center;
}
.s7a__legend-item {
  display: flex;
  align-items: center;
  gap: 4px;
}
.s7a__legend-dot {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 3px;
}

/* ── 逐句对齐列表 ── */
.s7a__sim-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.s7a__sim-item {
  padding: 10px 12px;
  background: #fafafa;
  border-radius: 8px;
  border-left: 3px solid #e5e7eb;
  transition: all .15s;
  cursor: default;
}
.s7a__sim-item:hover {
  border-left-color: #6366f1;
  background: #f5f3ff;
}

.s7a__sim-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
  flex-wrap: wrap;
}

.s7a__sim-type {
  padding: 2px 8px;
  border-radius: 4px;
  color: #fff;
  font-size: 11px;
  font-weight: 600;
}

.s7a__sim-score {
  font-size: 14px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}

.s7a__sim-reason {
  font-size: 11px;
  color: #9ca3af;
  flex: 1;
}

.s7a__sim-bar {
  height: 4px;
  background: #e5e7eb;
  border-radius: 2px;
  margin-bottom: 6px;
  overflow: hidden;
}
.s7a__sim-bar-fill {
  height: 100%;
  border-radius: 2px;
  transition: width .3s ease;
}

.s7a__sim-ai-text {
  margin: 0;
  font-size: 13px;
  color: #444;
  line-height: 1.5;
}

.s7a__sim-src-text {
  margin: 4px 0 0;
  font-size: 12px;
  color: #9ca3af;
  font-style: italic;
  line-height: 1.45;
  padding-left: 12px;
  border-left: 2px solid #e5e7eb;
}

.s7a__sim-no-src {
  margin: 4px 0 0;
  font-size: 11px;
  color: #ef4444;
  padding-left: 12px;
  border-left: 2px solid #fca5a5;
}

/* ── Hover 浮层 ── */
.s7a__hover {
  position: fixed;
  z-index: 9999;
  max-width: 380px;
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  padding: 14px 16px;
  box-shadow: 0 8px 32px rgba(0,0,0,.14);
  pointer-events: none;
  font-size: 12px;
  line-height: 1.6;
}

.s7a__hover-score {
  font-size: 26px;
  font-weight: 700;
  margin-bottom: 4px;
}

.s7a__hover-type {
  margin-bottom: 8px;
}

.s7a__hover-text {
  margin: 4px 0;
  color: #444;
}

.s7a__hover-text--dim {
  color: #9ca3af;
  font-size: 11px;
}

/* ── 改进建议 ── */
.s7a__suggestions {
  margin: 0;
  padding-left: 18px;
  font-size: 13px;
  color: #555;
  line-height: 1.7;
}

/* ── DB 格式：问题列表 ── */
.s7a__issue-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.s7a__issue-row {
  font-size: 13px;
  color: #555;
  display: flex;
  gap: 8px;
  align-items: baseline;
  padding: 6px 10px;
  background: #f9fafb;
  border-radius: 6px;
}
.s7a__issue-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #f59e0b;
  flex-shrink: 0;
  margin-top: 7px;
}

/* ── DB 格式：匹配度分数条 ── */
.s7a__score-bar-wrap {
  display: flex;
  align-items: center;
  gap: 10px;
}
.s7a__score-bar {
  flex: 1;
  height: 10px;
  background: #e5e7eb;
  border-radius: 5px;
  overflow: hidden;
}
.s7a__score-bar-fill {
  height: 100%;
  border-radius: 5px;
  transition: width .4s ease;
}
.s7a__score-val {
  font-size: 16px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}
</style>
