<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import AIInputPanel from './AIInputPanel.vue'
import AIResultPanel from './AIResultPanel.vue'
import { aiApi, type AIGenerateRecordItem } from '@/api/ai'

const props = defineProps<{
  loading: boolean
  uiMode: 'input' | 'history' | 'detail'
  historyDetailResult?: any
}>()

const emit = defineEmits<{
  (e: 'generate'): void
  (e: 'clear'): void
  (e: 'loadSample'): void
  (e: 'load-history-item', record: AIGenerateRecordItem): void
  (e: 'view-history-item', record: AIGenerateRecordItem): void
  (e: 'set-ui-mode', mode: 'input' | 'history' | 'detail'): void
}>()

const historyRecords = ref<AIGenerateRecordItem[]>([])
const historyLoading = ref(false)

const loadHistory = async () => {
  historyLoading.value = true
  try {
    const response = await aiApi.getRecords()
    historyRecords.value = response.records
  } catch (error) {
    ElMessage.error('加载历史记录失败')
  } finally {
    historyLoading.value = false
  }
}

const handleGenerate = () => {
  emit('generate')
}

const handleClear = () => {
  emit('clear')
}

const handleLoadSample = () => {
  emit('loadSample')
}

const handleLoadHistoryItem = (record: AIGenerateRecordItem) => {
  emit('load-history-item', record)
}

const refreshHistory = () => {
  loadHistory()
}

onMounted(() => {
  if (props.uiMode === 'history') {
    loadHistory()
  }
})

watch(
  () => props.uiMode,
  (newMode) => {
    if (newMode === 'history') {
      loadHistory()
    }
  }
)

defineExpose({ refreshHistory })
</script>

<template>
  <div class="main-area">
    <template v-if="uiMode === 'input'">
      <AIInputPanel />
      
      <div class="action-wrapper">
        <div class="tips-section">
          <div class="tip-item">
            <span class="tip-dot"></span>
            <span>支持粘贴新闻正文，自动提取关键信息</span>
          </div>
          <div class="tip-item">
            <span class="tip-dot"></span>
            <span>可生成1-5个候选标题供选择</span>
          </div>
          <div class="tip-item">
            <span class="tip-dot"></span>
            <span>短摘要150字以内，长摘要300-800字</span>
          </div>
        </div>
        
        <div class="shortcuts-section">
          <button class="shortcut-btn" @click="handleClear">清空内容</button>
          <button class="shortcut-btn" @click="handleLoadSample">加载示例</button>
        </div>
        
        <el-button
          type="primary"
          size="large"
          class="generate-button"
          @click="handleGenerate"
          :loading="loading"
          :disabled="loading"
        >
          {{ loading ? '生成中...' : '生成标题和摘要' }}
        </el-button>
      </div>

      <AIResultPanel />
    </template>

    <template v-else-if="uiMode === 'history'">
      <div class="history-mode-header">
        <h3>生成记录</h3>
        <div class="header-actions">
          <el-button type="text" @click="loadHistory" :loading="historyLoading">刷新</el-button>
          <el-button type="text" @click="$emit('set-ui-mode', 'input')">返回输入模式</el-button>
        </div>
      </div>
      
      <div class="history-list-container">
        <div v-if="historyLoading" class="loading-state">
          <el-spinner />
          <span>加载中...</span>
        </div>
        
        <div v-else-if="historyRecords.length === 0" class="empty-state">
          <p class="empty-text">暂无生成记录</p>
          <p class="empty-description">生成标题和摘要后，记录将显示在这里</p>
        </div>
        
        <div v-else class="history-list">
          <div v-for="record in historyRecords" :key="record.id" class="history-item">
            <div class="item-content">
              <div class="item-title">
                {{ record.candidate_titles?.[0] || record.source_title }}
              </div>
              <div class="item-summary">{{ record.summary_short || '暂无摘要' }}</div>
              <div class="item-time">{{ record.created_at }}</div>
            </div>
            <div class="item-actions">
              <el-button type="text" size="small" @click="emit('view-history-item', record)">查看</el-button>
              <el-button type="text" size="small" @click="handleLoadHistoryItem(record)">复用</el-button>
            </div>
          </div>
        </div>
      </div>
    </template>

    <template v-else-if="uiMode === 'detail'">
      <div class="detail-mode-header">
        <h3>历史详情</h3>
        <div class="header-actions">
          <el-button type="text" @click="$emit('set-ui-mode', 'history')">返回历史列表</el-button>
          <el-button type="text" @click="$emit('set-ui-mode', 'input')">返回输入模式</el-button>
        </div>
      </div>
      
      <AIResultPanel :has-result="true" :override-result="historyDetailResult" />
    </template>
  </div>
</template>

<style scoped>
.main-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.action-wrapper {
  padding: 20px;
  background-color: #ffffff;
  border-radius: 10px;
  border: 1px solid #f0f0f0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.tips-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
  
  .tip-item {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 13px;
    color: #666666;
    
    .tip-dot {
      width: 4px;
      height: 4px;
      background-color: #ff4d4f;
      border-radius: 50%;
      flex-shrink: 0;
    }
  }
}

.shortcuts-section {
  display: flex;
  gap: 10px;
  
  .shortcut-btn {
    flex: 1;
    padding: 10px 16px;
    font-size: 13px;
    color: #666666;
    background-color: #f8f8f8;
    border: 1px solid #e8e8e8;
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.2s ease;
    
    &:hover {
      background-color: #fff5f5;
      border-color: #ffccc7;
      color: #ff4d4f;
    }
  }
}

.generate-button {
  width: 100%;
  height: 46px;
  font-size: 16px;
  font-weight: 600;
  border-radius: 8px;
  background: linear-gradient(135deg, #ff4d4f 0%, #ff7875 100%);
  border: none;
  transition: all 0.25s ease;
  
  &:hover:not(:disabled) {
    background: linear-gradient(135deg, #ff7875 0%, #ff4d4f 100%);
    transform: translateY(-1px);
    box-shadow: 0 6px 20px rgba(255, 77, 79, 0.4);
  }
  
  &:active:not(:disabled) {
    transform: translateY(0);
    box-shadow: 0 3px 10px rgba(255, 77, 79, 0.3);
  }
}

.history-mode-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  background-color: #ffffff;
  border-radius: 10px;
  border: 1px solid #f0f0f0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  position: sticky;
  top: 0;
  z-index: 10;
  
  h3 {
    margin: 0;
    font-size: 16px;
    font-weight: 600;
    color: #374151;
  }
}

.header-actions {
  display: flex;
  gap: 16px;
}

.history-list-container {
  background-color: #ffffff;
  border-radius: 10px;
  border: 1px solid #f0f0f0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  padding: 16px;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 40px 20px;
  color: #6b7280;
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

.history-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.history-item {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 16px;
  background-color: #f9fafb;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
  
  &:hover {
    border-color: #d1d5db;
  }
}

.item-content {
  flex: 1;
  min-width: 0;
}

.item-title {
  font-size: 15px;
  font-weight: 600;
  color: #374151;
  margin-bottom: 8px;
}

.item-summary {
  font-size: 13px;
  color: #6b7280;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
  margin-bottom: 8px;
}

.item-time {
  font-size: 12px;
  color: #9ca3af;
}

.item-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-left: 16px;
  flex-shrink: 0;
  
  :deep(.el-button) {
    padding: 6px 12px;
    font-size: 12px;
  }
}

.detail-mode-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  background-color: #ffffff;
  border-radius: 10px;
  border: 1px solid #f0f0f0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  position: sticky;
  top: 0;
  z-index: 10;
  
  h3 {
    margin: 0;
    font-size: 16px;
    font-weight: 600;
    color: #374151;
  }
}
</style>