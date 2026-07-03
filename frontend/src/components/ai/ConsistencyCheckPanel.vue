<script setup lang="ts">
import { computed } from 'vue'
import type { ConsistencyCheck } from '@/api/ai'

interface Props {
  consistency: ConsistencyCheck
}

const props = defineProps<Props>()

const riskLevelText = computed(() => {
  const map: Record<string, string> = {
    low: '低风险',
    medium: '中风险',
    high: '高风险',
  }
  return map[props.consistency.risk_level] || '未知'
})

const riskLevelType = computed(() => {
  const map: Record<string, string> = {
    low: 'success',
    medium: 'warning',
    high: 'danger',
  }
  return map[props.consistency.risk_level] || 'info'
})

const scoreStatus = computed(() => {
  const score = props.consistency.score
  if (score >= 90) return 'success'
  if (score >= 70) return 'warning'
  return 'danger'
})
</script>

<template>
  <div class="consistency-section">
    <h4 class="section-title">一致性检测</h4>

    <div class="score-card">
      <div class="score-display">
        <div class="score-value" :class="`score-status-${scoreStatus}`">{{ consistency.score }}</div>
        <div class="score-label">评分</div>
      </div>
      <div class="score-bar">
        <div
          class="score-bar-fill"
          :style="{ width: `${consistency.score}%` }"
          :class="`score-status-${scoreStatus}`"
        />
      </div>
    </div>

    <div class="risk-section">
      <span class="risk-label">风险等级：</span>
      <el-tag :type="riskLevelType" size="large">
        {{ riskLevelText }}
      </el-tag>
    </div>

    <div v-if="consistency.issues.length > 0" class="issues-section">
      <h5 class="subsection-title">问题提示</h5>
      <ul class="issues-list">
        <li v-for="(issue, index) in consistency.issues" :key="index" class="issue-item">
          {{ issue }}
        </li>
      </ul>
    </div>

    <div v-if="consistency.suggestions.length > 0" class="suggestions-section">
      <h5 class="subsection-title">修改建议</h5>
      <ul class="suggestions-list">
        <li v-for="(suggestion, index) in consistency.suggestions" :key="index" class="suggestion-item">
          {{ suggestion }}
        </li>
      </ul>
    </div>
  </div>
</template>

<style scoped>
.consistency-section {
  padding-bottom: 20px;
  border-bottom: 1px solid var(--color-border);

  &:last-child {
    padding-bottom: 0;
    border-bottom: none;
  }
}

.section-title {
  margin: 0 0 12px;
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.score-card {
  padding: 16px;
  background: linear-gradient(135deg, var(--color-primary-soft) 0%, rgba(64, 158, 255, 0.08) 100%);
  border-radius: 4px;
  margin-bottom: 12px;
}

.score-display {
  text-align: center;
  margin-bottom: 12px;
}

.score-value {
  font-size: 32px;
  font-weight: bold;

  &.score-status-success {
    color: #67c23a;
  }

  &.score-status-warning {
    color: #e6a23c;
  }

  &.score-status-danger {
    color: #f56c6c;
  }
}

.score-label {
  font-size: 12px;
  color: var(--color-text-secondary);
  margin-top: 4px;
}

.score-bar {
  height: 8px;
  background-color: rgba(64, 158, 255, 0.1);
  border-radius: 4px;
  overflow: hidden;
}

.score-bar-fill {
  height: 100%;
  transition: width 0.3s, background-color 0.3s;

  &.score-status-success {
    background-color: #67c23a;
  }

  &.score-status-warning {
    background-color: #e6a23c;
  }

  &.score-status-danger {
    background-color: #f56c6c;
  }
}

.risk-section {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.risk-label {
  font-size: 14px;
  color: var(--color-text-primary);
  font-weight: 500;
}

.issues-section,
.suggestions-section {
  margin-top: 12px;
}

.subsection-title {
  margin: 0 0 8px;
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.issues-list,
.suggestions-list {
  margin: 0;
  padding-left: 20px;
  list-style: none;
}

.issue-item,
.suggestion-item {
  margin-bottom: 6px;
  padding-left: 16px;
  position: relative;
  font-size: 13px;
  line-height: 1.6;
  color: var(--color-text-primary);

  &::before {
    content: '•';
    position: absolute;
    left: 0;
    color: var(--color-primary);
    font-weight: bold;
  }

  &:last-child {
    margin-bottom: 0;
  }
}

.issues-list .issue-item::before {
  color: #f56c6c;
}

.suggestions-list .suggestion-item::before {
  color: #67c23a;
}
</style>
