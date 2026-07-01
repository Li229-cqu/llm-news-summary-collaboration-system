<script setup lang="ts">
import { computed, ref } from 'vue'
import { useAIDraftStore } from '@/stores/aiDraft'
import { ElMessage } from 'element-plus'
import { uploadFile } from '@/api/ai'

const aiDraft = useAIDraftStore()
const fileInputRef = ref<HTMLInputElement | null>(null)
const isUploading = ref(false)

const charCount = computed(() => aiDraft.inputText.length)
const isInputEmpty = computed(() => aiDraft.inputText.trim().length === 0)

const handleInputChange = (text: string) => {
  aiDraft.setInputText(text)
}

const handleClearInput = () => {
  aiDraft.setInputText('')
  aiDraft.clearSourceNews()
  ElMessage.success('已清空正文')
}

const handleFileUpload = () => {
  fileInputRef.value?.click()
}

const handleFileChange = async (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return

  const validExtensions = ['.txt', '.md', '.docx', '.pdf']
  const extension = file.name.toLowerCase().substring(file.name.lastIndexOf('.'))
  
  if (!validExtensions.includes(extension)) {
    ElMessage.error('仅支持上传 .txt、.md、.docx、.pdf 格式的文件')
    return
  }

  isUploading.value = true
  try {
    const formData = new FormData()
    formData.append('file', file)
    
    const response = await uploadFile(formData)
    
    if (response.content) {
      aiDraft.setFromUpload(file.name, response.content)
      ElMessage.success(`文件 "${response.filename}" 上传成功，已提取文本内容`)
    } else {
      ElMessage.warning(response.message || '文件内容为空')
    }
  } catch (error) {
    ElMessage.error('文件上传失败，请重试')
  } finally {
    isUploading.value = false
    target.value = ''
  }
}
</script>

<template>
  <el-card class="app-card input-panel">
    <template #header>
      <div class="card-header">
        <span class="title">新闻正文输入</span>
      </div>
    </template>

    <div v-if="aiDraft.sourceTitle" class="source-news-info">
      <el-alert
        :title="`已从新闻详情导入：${aiDraft.sourceTitle}`"
        type="success"
        :closable="false"
        show-icon
      />
    </div>

    <div class="input-area">
      <textarea
        :value="aiDraft.inputText"
        @input="(e) => handleInputChange((e.target as HTMLTextAreaElement).value)"
        placeholder="请粘贴或输入新闻正文..."
        class="text-input"
      />

      <div class="char-count">
        已输入 <span class="count-number">{{ charCount }}</span> 字
      </div>
    </div>

    <div v-if="isInputEmpty" class="empty-tip">
      请输入新闻正文后再生成
    </div>

    <div class="action-buttons">
      <el-button type="default" @click="handleClearInput" :disabled="isInputEmpty">
        清空正文
      </el-button>
      <el-button type="default" @click="handleFileUpload" :loading="isUploading">
        📎 上传文件
      </el-button>
    </div>
  </el-card>

  <input
    ref="fileInputRef"
    type="file"
    accept=".txt,.md,.docx,.pdf"
    class="hidden-file-input"
    @change="handleFileChange"
  />
</template>

<style scoped>
.input-panel {
  margin-bottom: 0;
  display: flex;
  flex-direction: column;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.title {
  font-size: 15px;
  font-weight: 600;
  color: #374151;
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
  height: 280px;
  padding: 14px;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  font-family: inherit;
  font-size: 14px;
  line-height: 1.6;
  color: #374151;
  background-color: #ffffff;
  resize: vertical;
  transition: border-color 0.2s ease;
  box-sizing: border-box;
}

.text-input:focus {
  outline: none;
  border-color: #ff4d4f;
}

.text-input::placeholder {
  color: #9ca3af;
}

.char-count {
  margin-top: 8px;
  text-align: right;
  font-size: 12px;
  color: #6b7280;
}

.count-number {
  font-weight: 600;
  color: #ff4d4f;
}

.empty-tip {
  padding: 12px 14px;
  margin-bottom: 12px;
  background-color: #f9fafb;
  border-radius: 6px;
  font-size: 14px;
  color: #6b7280;
  border-left: 3px solid #d1d5db;
}

.action-buttons {
  display: flex;
  gap: 8px;
}

.action-buttons :deep(.el-button) {
  flex: 1;
  height: 40px;
  font-size: 14px;
}

.hidden-file-input {
  display: none;
}
</style>
