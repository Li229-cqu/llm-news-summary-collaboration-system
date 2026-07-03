<script setup lang="ts">
/** AgentExplainPanel — AI 决策可解释性面板（Phase 4）。
 *
 * 展示分类推理、时间线推理、一致性推理三方面的决策路径，
 * 附带可信度评分和证据数据。
 */

import { ref, watch } from 'vue'
import { getTaskExplain, type ExplainResult } from '@/api/agentAnalysis'

const props = defineProps<{ taskId: number | null }>()

const data = ref<ExplainResult | null>(null)
const loading = ref(false)
const error = ref('')

async function load() {
  if (!props.taskId) return
  loading.value = true
  error.value = ''
  try {
    data.value = await getTaskExplain(props.taskId)
  } catch (e) {
    error.value = e instanceof Error ? e.message : '加载可解释性数据失败'
  } finally {
    loading.value = false
  }
}

watch(() => props.taskId, () => { if (props.taskId) load() }, { immediate: true })

function categoryIcon(cat: string): string {
  switch (cat) {
    case 'classification': return '🏷'
    case 'timeline':       return '📅'
    case 'consistency':    return '🔍'
    default:               return '📋'
  }
}

function confidenceColor(c: number): string {
  if (c >= 0.8) return '#16a34a'
  if (c >= 0.5) return '#f59e0b'
  return '#dc2626'
}

function confidenceLabel(c: number): string {
  if (c >= 0.8) return '高'
  if (c >= 0.5) return '中'
  return '低'
}
</script>

<template>
  <div class="explain-panel">
    <el-skeleton v-if="loading" animated :rows="4" />

    <el-empty
      v-else-if="!data && !error"
      description="提交并完成任务后，可查看 AI 决策解释"
      :image-size="60"
    />

    <el-alert v-else-if="error" :title="error" type="error" show-icon :closable="false" />

    <template v-else-if="data">
      <!-- 综合信息 -->
      <div class="explain-summary">
        <div class="summary-text">{{ data.summary }}</div>
        <div class="summary-conf">
          <span class="conf-badge" :style="{ color: confidenceColor(data.confidence) }">
            {{ confidenceLabel(data.confidence) }}可信度
          </span>
          <el-progress
            :percentage="Math.round(data.confidence * 100)"
            :stroke-width="8"
            :color="confidenceColor(data.confidence)"
            :show-text="false"
            style="width: 120px;"
          />
          <span class="conf-num">{{ (data.confidence * 100).toFixed(0) }}%</span>
        </div>
      </div>

      <!-- 推理链 -->
      <div class="reasoning-list">
        <div
          v-for="(item, i) in data.reasoning"
          :key="i"
          class="reasoning-item"
        >
          <div class="reasoning-header">
            <span class="reasoning-icon">{{ categoryIcon(item.category) }}</span>
            <span class="reasoning-label">{{ item.label }}</span>
            <el-tag
              :color="confidenceColor(item.confidence)"
              size="small"
              effect="dark"
              style="border: none; color: #fff;"
            >
              {{ confidenceLabel(item.confidence) }} {{ (item.confidence * 100).toFixed(0) }}%
            </el-tag>
          </div>
          <p class="reasoning-detail">{{ item.detail }}</p>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.explain-panel { padding: 4px 0; }

/* 综合摘要 */
.explain-summary {
  padding: 16px;
  margin-bottom: 16px;
  background: color-mix(in srgb, var(--color-primary) 4%, var(--color-bg-card));
  border: 1px solid color-mix(in srgb, var(--color-primary) 15%, var(--color-border));
  border-radius: 12px;
}

.summary-text {
  font-size: 14px;
  line-height: 1.65;
  color: var(--color-text-primary);
  margin-bottom: 12px;
}

.summary-conf {
  display: flex;
  align-items: center;
  gap: 10px;
}

.conf-badge {
  font-size: 12px;
  font-weight: 600;
}

.conf-num {
  font-size: 13px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  color: var(--color-text-secondary);
}

/* 推理链 */
.reasoning-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.reasoning-item {
  padding: 12px 14px;
  border: 1px solid var(--color-border);
  border-radius: 10px;
  transition: border-color 0.2s;
}
.reasoning-item:hover {
  border-color: color-mix(in srgb, var(--color-primary) 30%, var(--color-border));
}

.reasoning-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.reasoning-icon { font-size: 16px; }
.reasoning-label {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-primary);
  flex: 1;
}

.reasoning-detail {
  margin: 0;
  font-size: 12px;
  line-height: 1.6;
  color: var(--color-text-secondary);
  white-space: pre-line;
}
</style>
