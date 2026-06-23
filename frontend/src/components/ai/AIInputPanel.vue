<script setup lang="ts">
import { computed } from 'vue'
import { useAIDraftStore } from '@/stores/aiDraft'
import { ElMessage } from 'element-plus'

const aiDraft = useAIDraftStore()

const charCount = computed(() => aiDraft.inputText.length)
const isInputEmpty = computed(() => aiDraft.inputText.trim().length === 0)

const handleInputChange = (text: string) => {
  aiDraft.setInputText(text)
}

const handleClearInput = () => {
  aiDraft.setInputText('')
  ElMessage.success('已清空正文')
}

const handleFileUpload = () => {
  ElMessage.info('上传文件功能暂未开放，敬请期待')
}
</script>

<template>
  <el-card class="app-card input-panel">
    <template #header>
      <div class="card-header">
        <span class="title">📝 新闻正文输入</span>
      </div>
    </template>

    <!-- 来源新闻提示 -->
    <div v-if="aiDraft.sourceTitle" class="source-news-info">
      <el-alert
        :title="`已从新闻详情导入：${aiDraft.sourceTitle}`"
        type="success"
        :closable="false"
        show-icon
      />
    </div>

    <!-- 输入区 -->
    <div class="input-area">
      <textarea
        :value="aiDraft.inputText"
        @input="(e) => handleInputChange((e.target as HTMLTextAreaElement).value)"
        placeholder="请粘贴或输入新闻正文..."
        class="text-input"
      />

      <!-- 字数统计 -->
      <div class="char-count">
        已输入 <span class="count-number">{{ charCount }}</span> 字
      </div>
    </div>

    <!-- 提示信息 -->
    <div v-if="isInputEmpty" class="empty-tip">
      💡 请输入新闻正文后再生成
    </div>

    <!-- 操作按钮 -->
    <div class="action-buttons">
      <el-button type="default" @click="handleClearInput" :disabled="isInputEmpty">
        清空正文
      </el-button>
      <el-button type="default" @click="handleFileUpload">
        📎 上传文件（后续支持）
      </el-button>
    </div>
  </el-card>
</template>

<style scoped>
.input-panel {
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

.source-news-info {
  margin-bottom: 16px;
}

.input-area {
  position: relative;
  margin-bottom: 12px;
}

.text-input {
  width: 100%;
  min-height: 200px;
  padding: 12px;
  border: 1px solid var(--color-border);
  border-radius: 4px;
  font-family: inherit;
  font-size: 14px;
  line-height: 1.6;
  color: var(--color-text-primary);
  background-color: var(--color-bg-card);
  resize: vertical;
  transition: border-color 0.3s;
}

.text-input:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.2);
}

.char-count {
  margin-top: 8px;
  text-align: right;
  font-size: 12px;
  color: var(--color-text-secondary);
}

.count-number {
  font-weight: 600;
  color: var(--color-primary);
}

.empty-tip {
  padding: 12px;
  margin-bottom: 12px;
  background-color: var(--color-primary-soft);
  border-radius: 4px;
  font-size: 14px;
  color: var(--color-text-primary);
  border-left: 3px solid var(--color-primary);
}

.action-buttons {
  display: flex;
  gap: 8px;
}

.action-buttons :deep(.el-button) {
  flex: 1;
}
</style>
