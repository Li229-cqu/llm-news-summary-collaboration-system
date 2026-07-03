<script setup lang="ts">
import { computed, ref } from 'vue'
import { ElMessage, ElDialog } from 'element-plus'
import { useAIDraftStore } from '@/stores/aiDraft'
import type { AIGenerateResponse, EvidenceChain, SentenceEvidence } from '@/api/ai'
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

const resultSource = computed(() => {
  return displayResult.value?.source || 'mock'
})

const evidenceChainShort = computed<EvidenceChain | undefined>(() => {
  return displayResult.value?.evidence_chain_short
})

const evidenceChainLong = computed<EvidenceChain | undefined>(() => {
  return displayResult.value?.evidence_chain_long
})

const riskLevel = computed(() => {
  return displayResult.value?.risk_level || displayResult.value?.consistency?.risk_level
})

const riskDetails = computed(() => {
  return displayResult.value?.risk_details
})

const evidenceCoverage = computed(() => {
  return displayResult.value?.evidence_coverage
})

const showEvidenceDialog = ref(false)
const currentSentenceEvidence = ref<SentenceEvidence | null>(null)

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

const getRiskLevelColor = (level: string) => {
  switch (level) {
    case 'high': return 'danger'
    case 'medium': return 'warning'
    case 'low': return 'success'
    default: return 'info'
  }
}

const getRiskLevelText = (level: string) => {
  switch (level) {
    case 'high': return '高风险'
    case 'medium': return '中风险'
    case 'low': return '低风险'
    default: return '未知'
  }
}

const getSentenceRiskColor = (riskLevel: number) => {
  switch (riskLevel) {
    case 2: return 'background-color: rgba(255, 73, 73, 0.1); border-color: #ff4949;'
    case 1: return 'background-color: rgba(255, 149, 0, 0.1); border-color: #ff9500;'
    case 0: return 'background-color: rgba(52, 199, 89, 0.1); border-color: #34c759;'
    default: return 'background-color: rgba(142, 142, 147, 0.1); border-color: #8e8e93;'
  }
}

const openEvidenceDialog = (sentence: SentenceEvidence) => {
  currentSentenceEvidence.value = sentence
  showEvidenceDialog.value = true
}

const closeEvidenceDialog = () => {
  showEvidenceDialog.value = false
  currentSentenceEvidence.value = null
}

const renderSummaryWithEvidence = (summary: string, chain?: EvidenceChain) => {
  if (!chain?.sentences?.length) {
    return summary
  }
  
  const chainSentences = chain.sentences
  
  let result = ''
  
  for (let i = 0; i < chainSentences.length; i++) {
    const sent = chainSentences[i]
    if (sent.text && sent.text.trim()) {
      result += `<span 
        class="sentence-clickable" 
        style="${getSentenceRiskColor(sent.risk_level)}"
        data-index="${i}"
      >${sent.text}。</span>`
    }
  }
  
  return result || summary
}

const handleShortSummaryClick = (event: Event) => {
  handleSummaryClick(event, evidenceChainShort.value)
}

const handleLongSummaryClick = (event: Event) => {
  handleSummaryClick(event, evidenceChainLong.value)
}

const handleSummaryClick = (event: Event, chain?: EvidenceChain) => {
  if (!chain?.sentences?.length) return
  const target = event.target as HTMLElement
  const sentenceSpan = target.closest('.sentence-clickable') as HTMLElement
  if (sentenceSpan) {
    const index = parseInt(sentenceSpan.getAttribute('data-index') || '0')
    const sentence = chain.sentences[index]
    if (sentence) {
      openEvidenceDialog(sentence)
    }
  }
}
</script>

<template>
  <el-card class="app-card result-panel">
    <template #header>
      <div class="card-header">
        <span class="title">生成结果</span>
        <div class="header-tags">
          <el-tag
            v-if="hasResult()"
            :type="resultSource === 'llm' ? 'success' : 'info'"
            size="small"
          >
            {{ resultSource === 'llm' ? '真实AI' : 'Mock演示' }}
          </el-tag>
          <el-tag
            v-if="riskLevel"
            :type="getRiskLevelColor(riskLevel)"
            size="small"
          >
            {{ getRiskLevelText(riskLevel) }}
          </el-tag>
        </div>
      </div>
    </template>

    <div v-if="!hasResult()" class="empty-state">
      <p class="empty-text">生成结果将在这里展示</p>
      <p class="empty-description">输入新闻正文、调整参数后点击"生成"按钮开始处理</p>
    </div>

    <div v-else class="result-content">
      <div v-if="riskLevel || evidenceCoverage || riskDetails" class="result-section">
        <h4 class="section-title">风险评估</h4>
        <div class="risk-panel">
          <div class="risk-item">
            <span class="risk-label">风险等级</span>
            <el-tag :type="getRiskLevelColor(riskLevel || '')" size="medium">
              {{ getRiskLevelText(riskLevel || '') }}
            </el-tag>
          </div>
          <div v-if="evidenceCoverage !== undefined" class="risk-item">
            <span class="risk-label">证据覆盖率</span>
            <div class="coverage-bar-container">
              <div 
                class="coverage-bar" 
                :style="{ width: `${(evidenceCoverage * 100)}%` }"
                :class="{
                  'coverage-high': evidenceCoverage >= 0.9,
                  'coverage-medium': evidenceCoverage >= 0.7 && evidenceCoverage < 0.9,
                  'coverage-low': evidenceCoverage < 0.7
                }"
              ></div>
              <span class="coverage-text">{{ (evidenceCoverage * 100).toFixed(0) }}%</span>
            </div>
          </div>
          <div v-if="riskDetails" class="risk-item">
            <span class="risk-label">风险详情</span>
            <span class="risk-detail-text">{{ riskDetails }}</span>
          </div>
        </div>
      </div>

      <div v-if="(displayResult?.candidate_titles?.length ?? 0) > 0" class="result-section">
        <h4 class="section-title">候选标题</h4>
        <div class="title-list">
          <div v-for="(title, index) in (displayResult?.candidate_titles ?? [])" :key="index" class="title-item">
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
              复制
            </el-button>
          </div>
        </div>
      </div>

      <div v-if="displayResult?.summary_short" class="result-section">
        <h4 class="section-title">短摘要</h4>
        <div class="summary-item">
          <p 
            class="summary-text"
            v-html="renderSummaryWithEvidence(displayResult.summary_short, evidenceChainShort)"
            @click="handleShortSummaryClick"
          ></p>
          <el-button
            type="text"
            size="small"
            @click="copyToClipboard(displayResult.summary_short)"
            class="copy-button-summary"
          >
            复制
          </el-button>
        </div>
      </div>

      <div v-if="displayResult?.summary_long" class="result-section">
        <h4 class="section-title">长摘要</h4>
        <div class="summary-item">
          <p 
            class="summary-text"
            v-html="renderSummaryWithEvidence(displayResult.summary_long, evidenceChainLong)"
            @click="handleLongSummaryClick"
          ></p>
          <el-button
            type="text"
            size="small"
            @click="copyToClipboard(displayResult.summary_long)"
            class="copy-button-summary"
          >
            复制
          </el-button>
        </div>
      </div>

      <div v-if="(displayResult?.summary_points?.length ?? 0) > 0" class="result-section">
        <h4 class="section-title">摘要要点</h4>
        <ul class="points-list">
          <li v-for="(point, index) in (displayResult?.summary_points ?? [])" :key="index" class="point-item">
            {{ point }}
          </li>
        </ul>
      </div>

      <KeywordTags
        v-if="displayResult?.keywords"
        :keywords="displayResult.keywords"
        class="result-section"
      />

      <NewsElements
        v-if="displayResult?.elements"
        :elements="displayResult.elements"
        class="result-section"
      />

      <ConsistencyCheckPanel
        v-if="displayResult?.consistency"
        :consistency="displayResult.consistency"
        class="result-section"
      />
    </div>
  </el-card>

  <ElDialog
    v-model="showEvidenceDialog"
    title="证据详情"
    width="600px"
    @close="closeEvidenceDialog"
  >
    <div v-if="currentSentenceEvidence" class="evidence-dialog">
      <div class="evidence-sentence">
        <span class="evidence-label">摘要句子</span>
        <p class="evidence-sentence-text">{{ currentSentenceEvidence.text }}</p>
      </div>
      
      <div class="evidence-status">
        <span class="evidence-label">证据状态</span>
        <el-tag :type="currentSentenceEvidence.has_evidence ? 'success' : 'danger'">
          {{ currentSentenceEvidence.has_evidence ? '有证据支持' : '无证据支持' }}
        </el-tag>
      </div>

      <div v-if="currentSentenceEvidence.risk_level !== undefined" class="evidence-risk">
        <span class="evidence-label">风险等级</span>
        <el-tag :type="getRiskLevelColor(['low', 'medium', 'high'][currentSentenceEvidence.risk_level] || '')">
          {{ getRiskLevelText(['low', 'medium', 'high'][currentSentenceEvidence.risk_level] || '') }}
        </el-tag>
      </div>

      <div class="evidence-list">
        <span class="evidence-label">证据来源</span>
        <div v-if="currentSentenceEvidence.evidence?.length > 0" class="evidence-items">
          <div 
            v-for="(evidence, index) in currentSentenceEvidence.evidence" 
            :key="index" 
            class="evidence-item"
          >
            <div class="evidence-header">
              <span class="evidence-source">{{ evidence.source_name || '未知来源' }}</span>
              <span class="evidence-confidence">置信度: {{ evidence.confidence }}%</span>
            </div>
            <div class="evidence-position">{{ evidence.position }}</div>
            <p class="evidence-text">{{ evidence.text }}</p>
            <div v-if="evidence.similarity !== undefined" class="evidence-similarity">
              语义相似度: {{ (evidence.similarity * 100).toFixed(0) }}%
            </div>
          </div>
        </div>
        <p v-else class="no-evidence">暂无证据数据</p>
      </div>
    </div>
  </ElDialog>
</template>

<style scoped>
.result-panel {
  margin-bottom: 0;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.header-tags {
  display: flex;
  gap: 8px;
}

.title {
  font-size: 15px;
  font-weight: 600;
  color: #374151;
}

.empty-state {
  padding: 40px 20px;
  text-align: center;
  background-color: #f9fafb;
  border-radius: 6px;
  border: 1px dashed #e5e7eb;
}

.empty-text {
  margin: 0 0 8px;
  font-size: 15px;
  color: #374151;
  font-weight: 500;
}

.empty-description {
  margin: 0;
  font-size: 14px;
  color: #6b7280;
}

.result-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.result-section {
  padding-bottom: 16px;
  border-bottom: 1px solid #f3f4f6;

  &:last-child {
    padding-bottom: 0;
    border-bottom: none;
  }
}

.section-title {
  margin: 0 0 12px;
  font-size: 14px;
  font-weight: 600;
  color: #374151;
}

.risk-panel {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  padding: 12px 14px;
  background-color: #f9fafb;
  border-radius: 6px;
}

.risk-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.risk-label {
  font-size: 13px;
  color: #6b7280;
  font-weight: 500;
}

.risk-detail-text {
  font-size: 13px;
  color: #374151;
}

.coverage-bar-container {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 150px;
}

.coverage-bar {
  height: 6px;
  border-radius: 3px;
  transition: width 0.3s ease;
}

.coverage-high {
  background-color: #38a169;
}

.coverage-medium {
  background-color: #d69e2e;
}

.coverage-low {
  background-color: #e53e3e;
}

.coverage-text {
  font-size: 12px;
  color: #6b7280;
  min-width: 35px;
}

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
  background-color: #f9fafb;
  border-radius: 6px;
  border: 1px solid #f3f4f6;
  transition: border-color 0.2s ease;

  &:hover {
    border-color: #e5e7eb;
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
  color: #6b7280;
  font-size: 14px;
}

.title-content {
  flex: 1;
  color: #374151;
  font-size: 14px;
  line-height: 1.5;
  word-break: break-word;
}

.copy-button {
  flex-shrink: 0;
  margin-left: 8px;
  color: #6b7280;
  padding: 4px 8px;
  font-size: 12px;

  &:hover {
    color: #ff4d4f;
  }
}

.summary-item {
  position: relative;
  padding: 14px;
  background-color: #f9fafb;
  border-radius: 6px;
}

.summary-text {
  margin: 0;
  font-size: 14px;
  line-height: 1.7;
  color: #374151;
  word-break: break-word;
  white-space: pre-wrap;
}

.sentence-clickable {
  display: inline-block;
  padding: 2px 4px;
  margin: 2px;
  border-radius: 3px;
  border-bottom: 1px dashed currentColor;
  cursor: pointer;
  transition: opacity 0.2s;

  &:hover {
    opacity: 0.7;
  }
}

.copy-button-summary {
  display: block;
  margin-top: 10px;
  color: #6b7280;
  padding: 4px 8px;
  font-size: 12px;

  &:hover {
    color: #ff4d4f;
  }
}

.points-list {
  margin: 0;
  padding-left: 0;
  list-style: none;
}

.point-item {
  margin-bottom: 8px;
  padding-left: 18px;
  position: relative;
  font-size: 14px;
  line-height: 1.6;
  color: #374151;

  &::before {
    content: '';
    position: absolute;
    left: 0;
    top: 50%;
    transform: translateY(-50%);
    width: 6px;
    height: 6px;
    background-color: #d1d5db;
    border-radius: 50%;
  }

  &:last-child {
    margin-bottom: 0;
  }
}

.evidence-dialog {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.evidence-label {
  font-size: 13px;
  color: #6b7280;
  font-weight: 500;
  margin-bottom: 4px;
  display: block;
}

.evidence-sentence-text {
  font-size: 14px;
  line-height: 1.6;
  color: #374151;
  padding: 12px;
  background-color: #f9fafb;
  border-radius: 6px;
  margin: 0;
}

.evidence-status,
.evidence-risk {
  display: flex;
  align-items: center;
  gap: 8px;
}

.evidence-list {
  display: flex;
  flex-direction: column;
}

.evidence-items {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.evidence-item {
  padding: 12px;
  background-color: #f9fafb;
  border-radius: 6px;
}

.evidence-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.evidence-source {
  font-size: 13px;
  font-weight: 600;
  color: #374151;
}

.evidence-confidence {
  font-size: 12px;
  color: #6b7280;
}

.evidence-position {
  font-size: 12px;
  color: #6b7280;
  margin-bottom: 6px;
}

.evidence-text {
  font-size: 13px;
  line-height: 1.6;
  color: #374151;
  margin: 0;
}

.evidence-similarity {
  font-size: 12px;
  color: #6b7280;
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid #f3f4f6;
}

.no-evidence {
  font-size: 14px;
  color: #6b7280;
  text-align: center;
  padding: 24px;
  background-color: #f9fafb;
  border-radius: 6px;
}
</style>
