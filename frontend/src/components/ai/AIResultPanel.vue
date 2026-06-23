<script setup lang="ts">
import { computed } from 'vue'
import { ElMessage } from 'element-plus'
import { useAIDraftStore } from '@/stores/aiDraft'
import type { AIGenerateResponse } from '@/api/ai'
import KeywordTags from './KeywordTags.vue'
import NewsElements from './NewsElements.vue'
import ConsistencyCheckPanel from './ConsistencyCheckPanel.vue'

interface Props {
  hasResult?: boolean
  overrideResult?: AIGenerateResponse
}

const props = withDefaults(defineProps<Props>(), {
  hasResult: false,
})

const aiDraft = useAIDraftStore()

const displayResult = computed(() => {
  return props.overrideResult || aiDraft.result
})

const copyToClipboard = (text: string) => {
  navigator.clipboard.writeText(text).then(() => {
    ElMessage.success('已复制到剪贴板')
  }).catch(() => {
    ElMessage.error('复制失败，请重试')
  })
}

const hasResult = () => {
  return displayResult.value && (
    displayResult.value.candidate_titles?.length > 0 ||
    displayResult.value.summary_short ||
    displayResult.value.summary_long ||
    displayResult.value.summary_points?.length > 0
  )
}
</script>

<template>
  <el-card class="app-card result-panel">
    <template #header>
      <div class="card-header">
        <span class="title">📊 生成结果</span>
      </div>
    </template>

    <!-- 空状态 -->
    <div v-if="!hasResult()" class="empty-state">
      <p class="empty-text">生成结果将在这里展示</p>
      <p class="empty-description">输入新闻正文、调整参数后点击"生成"按钮开始处理</p>
    </div>

    <!-- 结果展示 -->
    <div v-else class="result-content">
      <!-- 候选标题 -->
      <div v-if="displayResult?.candidate_titles?.length > 0" class="result-section">
        <h4 class="section-title">📌 候选标题</h4>
        <div class="title-list">
          <div v-for="(title, index) in displayResult.candidate_titles" :key="index" class="title-item">
            <div class="title-text">
              <span class="title-number">{{ index + 1 }}.</span>
              <span class="title-content">{{ title }}</span>
            </div>
            <el-button
              type="text"
              size="small"
              @click="copyToClipboard(title)"
              class="copy-button"
            >
              📋 复制
            </el-button>
          </div>
        </div>
      </div>

      <!-- 短摘要 -->
      <div v-if="displayResult?.summary_short" class="result-section">
        <h4 class="section-title">📄 短摘要</h4>
        <div class="summary-item">
          <p class="summary-text">{{ displayResult.summary_short }}</p>
          <el-button
            type="text"
            size="small"
            @click="copyToClipboard(displayResult.summary_short)"
            class="copy-button-summary"
          >
            📋 复制
          </el-button>
        </div>
      </div>

      <!-- 长摘要 -->
      <div v-if="displayResult?.summary_long" class="result-section">
        <h4 class="section-title">📖 长摘要</h4>
        <div class="summary-item">
          <p class="summary-text">{{ displayResult.summary_long }}</p>
          <el-button
            type="text"
            size="small"
            @click="copyToClipboard(displayResult.summary_long)"
            class="copy-button-summary"
          >
            📋 复制
          </el-button>
        </div>
      </div>

      <!-- 摘要要点 -->
      <div v-if="displayResult?.summary_points?.length > 0" class="result-section">
        <h4 class="section-title">🎯 摘要要点</h4>
        <ul class="points-list">
          <li v-for="(point, index) in displayResult.summary_points" :key="index" class="point-item">
            {{ point }}
          </li>
        </ul>
      </div>

      <!-- 关键词 -->
      <KeywordTags
        v-if="displayResult?.keywords"
        :keywords="displayResult.keywords"
        class="result-section"
      />

      <!-- 新闻要素 -->
      <NewsElements
        v-if="displayResult?.elements"
        :elements="displayResult.elements"
        class="result-section"
      />

      <!-- 一致性校验 -->
      <ConsistencyCheckPanel
        v-if="displayResult?.consistency"
        :consistency="displayResult.consistency"
        class="result-section"
      />
    </div>
  </el-card>
</template>

<style scoped>
.result-panel {
  margin-bottom: 16px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.title {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-primary);
}

/* 空状态 */
.empty-state {
  padding: 40px 20px;
  text-align: center;
  background-color: rgba(64, 158, 255, 0.05);
  border-radius: 4px;
}

.empty-text {
  margin: 0 0 8px;
  font-size: 16px;
  color: var(--color-text-primary);
  font-weight: 500;
}

.empty-description {
  margin: 0;
  font-size: 14px;
  color: var(--color-text-secondary);
}

/* 结果内容 */
.result-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.result-section {
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

/* 标题列表 */
.title-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.title-item {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 10px 12px;
  background-color: var(--color-primary-soft);
  border-radius: 4px;
  transition: background-color 0.3s;

  &:hover {
    background-color: rgba(64, 158, 255, 0.15);
  }
}

.title-text {
  display: flex;
  gap: 8px;
  flex: 1;
  align-items: flex-start;
}

.title-number {
  flex-shrink: 0;
  font-weight: 600;
  color: var(--color-primary);
}

.title-content {
  flex: 1;
  color: var(--color-text-primary);
  font-size: 14px;
  line-height: 1.6;
  word-break: break-word;
}

.copy-button {
  flex-shrink: 0;
  margin-left: 8px;
  color: var(--color-primary);
  padding: 0;
}

/* 摘要 */
.summary-item {
  position: relative;
  padding: 12px;
  background-color: var(--color-bg);
  border-radius: 4px;
  border-left: 3px solid var(--color-primary);
}

.summary-text {
  margin: 0;
  font-size: 14px;
  line-height: 1.8;
  color: var(--color-text-primary);
  word-break: break-word;
  white-space: pre-wrap;
}

.copy-button-summary {
  display: block;
  margin-top: 8px;
  color: var(--color-primary);
  padding: 0;
}

/* 要点列表 */
.points-list {
  margin: 0;
  padding-left: 20px;
  list-style: none;
}

.point-item {
  margin-bottom: 8px;
  padding-left: 16px;
  position: relative;
  font-size: 14px;
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
</style>
