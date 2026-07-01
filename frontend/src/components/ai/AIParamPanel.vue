<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { useAIDraftStore } from '@/stores/aiDraft'

const aiDraft = useAIDraftStore()

const titleCountOptions = [
  { label: '1 个标题', value: 1 },
  { label: '3 个标题', value: 3 },
  { label: '5 个标题', value: 5 },
]

const summaryTypeOptions = [
  { label: '生成式摘要', value: 'generate' },
  { label: '抽取式摘要', value: 'extract' },
]

const titleStyleOptions = [
  { label: '客观新闻型', value: '客观新闻型' },
  { label: '吸引点击型', value: '吸引点击型' },
  { label: '简洁概括型', value: '简洁概括型' },
]

const summaryStyleOptions = [
  { label: '简明扼要', value: '简明扼要' },
  { label: '客观正式', value: '客观正式' },
  { label: '通俗易懂', value: '通俗易懂' },
]

const summaryLengthOptions = [
  { label: '短摘要', value: 'short' },
  { label: '长摘要', value: 'long' },
  { label: '短摘要 + 长摘要', value: 'both' },
]

const handleParamChange = (key: keyof typeof aiDraft.params, value: any) => {
  if (key === 'title_count') {
    aiDraft.setParams({ [key]: Number(value) })
  } else {
    aiDraft.setParams({ [key]: value })
  }
}

const handleResetParams = () => {
  aiDraft.resetParams()
  ElMessage.success('已恢复默认参数')
}
</script>

<template>
  <div class="param-sidebar">
    <div class="sidebar-header">
      <div class="sidebar-title">参数选择</div>
    </div>
    <div class="sidebar-section">
      <div class="section-header">
        <div class="section-title">标题数量</div>
        <div class="section-desc">选择生成的标题数量</div>
      </div>
      <div class="option-list">
        <button
          v-for="option in titleCountOptions"
          :key="option.value"
          :class="{ active: aiDraft.params.title_count === option.value }"
          @click="handleParamChange('title_count', option.value)"
          class="option-item"
        >
          <span class="option-dot"></span>
          <span class="option-text">{{ option.label }}</span>
        </button>
      </div>
    </div>

    <div class="sidebar-section">
      <div class="section-header">
        <div class="section-title">摘要类型</div>
        <div class="section-desc">选择摘要生成方式</div>
      </div>
      <div class="option-list">
        <button
          v-for="option in summaryTypeOptions"
          :key="option.value"
          :class="{ active: aiDraft.params.summary_type === option.value }"
          @click="handleParamChange('summary_type', option.value)"
          class="option-item"
        >
          <span class="option-dot"></span>
          <span class="option-text">{{ option.label }}</span>
        </button>
      </div>
    </div>

    <div class="sidebar-section">
      <div class="section-header">
        <div class="section-title">标题风格</div>
        <div class="section-desc">选择标题写作风格</div>
      </div>
      <div class="option-list">
        <button
          v-for="option in titleStyleOptions"
          :key="option.value"
          :class="{ active: aiDraft.params.title_style === option.value }"
          @click="handleParamChange('title_style', option.value)"
          class="option-item"
        >
          <span class="option-dot"></span>
          <span class="option-text">{{ option.label }}</span>
        </button>
      </div>
    </div>

    <div class="sidebar-section">
      <div class="section-header">
        <div class="section-title">摘要风格</div>
        <div class="section-desc">选择摘要写作风格</div>
      </div>
      <div class="option-list">
        <button
          v-for="option in summaryStyleOptions"
          :key="option.value"
          :class="{ active: aiDraft.params.summary_style === option.value }"
          @click="handleParamChange('summary_style', option.value)"
          class="option-item"
        >
          <span class="option-dot"></span>
          <span class="option-text">{{ option.label }}</span>
        </button>
      </div>
    </div>

    <div class="sidebar-section">
      <div class="section-header">
        <div class="section-title">摘要长度</div>
        <div class="section-desc">选择摘要输出长度</div>
      </div>
      <div class="option-list">
        <button
          v-for="option in summaryLengthOptions"
          :key="option.value"
          :class="{ active: aiDraft.params.summary_length === option.value }"
          @click="handleParamChange('summary_length', option.value)"
          class="option-item"
        >
          <span class="option-dot"></span>
          <span class="option-text">{{ option.label }}</span>
        </button>
      </div>
    </div>

    <div class="sidebar-footer">
      <button class="reset-btn" @click="handleResetParams">
        恢复默认参数
      </button>
    </div>
  </div>
</template>

<style scoped>
.param-sidebar {
  display: flex;
  flex-direction: column;
  background-color: var(--color-bg-card);
  border-radius: 12px;
  border: 1px solid var(--color-border);
  padding: 20px 0;
}

.sidebar-header {
  padding: 0 20px 20px;
  border-bottom: 2px solid #ff4d4f;
  margin-bottom: 20px;
}

.sidebar-title {
  font-size: 18px;
  font-weight: 700;
  color: #1e293b;
}

.sidebar-section {
  padding: 0 20px;
  margin-bottom: 24px;
  
  &:not(:last-of-type):not(.sidebar-footer) {
    border-bottom: 1px dashed var(--color-border);
    padding-bottom: 20px;
  }
  
  &:last-of-type {
    margin-bottom: 0;
  }
}

.section-header {
  margin-bottom: 12px;
}

.section-title {
  font-size: 16px;
  font-weight: 700;
  color: #1e293b;
  margin-bottom: 4px;
  padding-left: 10px;
  position: relative;
  
  &::before {
    content: '';
    position: absolute;
    left: 0;
    top: 50%;
    transform: translateY(-50%);
    width: 4px;
    height: 18px;
    background-color: #ff4d4f;
    border-radius: 2px;
  }
}

.section-desc {
  font-size: 12px;
  color: #94a3b8;
  padding-left: 14px;
}

.option-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.option-item {
  width: 100%;
  padding: 10px 14px 10px 28px;
  text-align: left;
  font-size: 14px;
  color: #475569;
  background: transparent;
  border: none;
  border-radius: 0;
  cursor: pointer;
  transition: all 0.25s ease;
  display: flex;
  align-items: center;
  gap: 10px;
  position: relative;
  
  &:hover {
    background-color: #fef2f2;
    color: #dc2626;
  }
  
  &:hover .option-dot {
    background-color: #fca5a5;
  }
}

.option-dot {
  width: 10px;
  height: 10px;
  background-color: #cbd5e1;
  border-radius: 50%;
  flex-shrink: 0;
  transition: all 0.25s ease;
}

.option-text {
  flex: 1;
}

.option-item.active {
  background-color: #fff1f0;
  color: #dc2626;
  font-weight: 600;
  border-radius: 8px;
  
  .option-dot {
    background-color: #dc2626;
  }
}

.sidebar-footer {
  padding: 16px 20px;
  margin-top: auto;
  border-top: 1px solid var(--color-border);
}

.reset-btn {
  width: 100%;
  padding: 11px 16px;
  font-size: 13px;
  color: var(--color-text-secondary);
  background-color: var(--color-bg-hover);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.25s ease;
  
  &:hover {
    background-color: var(--color-primary-soft);
    border-color: var(--color-primary-light);
    color: var(--color-primary-dark);
  }
}
</style>
