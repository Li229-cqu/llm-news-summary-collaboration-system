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
  <el-card class="app-card param-panel">
    <template #header>
      <div class="card-header">
        <span class="title">⚙️ 生成参数</span>
      </div>
    </template>

    <!-- 标题数量 -->
    <div class="param-group">
      <label class="param-label">标题数量</label>
      <el-radio-group
        :model-value="aiDraft.params.title_count"
        @update:model-value="(val: unknown) => handleParamChange('title_count', val)"
        class="radio-group"
      >
        <el-radio
          v-for="option in titleCountOptions"
          :key="option.value"
          :label="option.value"
          :value="option.value"
        >
          {{ option.label }}
        </el-radio>
      </el-radio-group>
    </div>

    <!-- 摘要类型 -->
    <div class="param-group">
      <label class="param-label">摘要类型</label>
      <el-radio-group
        :model-value="aiDraft.params.summary_type"
        @update:model-value="(val: unknown) => handleParamChange('summary_type', val)"
        class="radio-group"
      >
        <el-radio
          v-for="option in summaryTypeOptions"
          :key="option.value"
          :label="option.value"
          :value="option.value"
        >
          {{ option.label }}
        </el-radio>
      </el-radio-group>
    </div>

    <!-- 标题风格 -->
    <div class="param-group">
      <label class="param-label">标题风格</label>
      <el-select
        :model-value="aiDraft.params.title_style"
        @update:model-value="(val: unknown) => handleParamChange('title_style', val)"
        class="param-select"
      >
        <el-option
          v-for="option in titleStyleOptions"
          :key="option.value"
          :label="option.label"
          :value="option.value"
        />
      </el-select>
    </div>

    <!-- 摘要风格 -->
    <div class="param-group">
      <label class="param-label">摘要风格</label>
      <el-select
        :model-value="aiDraft.params.summary_style"
        @update:model-value="(val: unknown) => handleParamChange('summary_style', val)"
        class="param-select"
      >
        <el-option
          v-for="option in summaryStyleOptions"
          :key="option.value"
          :label="option.label"
          :value="option.value"
        />
      </el-select>
    </div>

    <!-- 摘要长度 -->
    <div class="param-group">
      <label class="param-label">摘要长度</label>
      <el-radio-group
        :model-value="aiDraft.params.summary_length"
        @update:model-value="(val: unknown) => handleParamChange('summary_length', val)"
        class="radio-group"
      >
        <el-radio
          v-for="option in summaryLengthOptions"
          :key="option.value"
          :label="option.value"
          :value="option.value"
        >
          {{ option.label }}
        </el-radio>
      </el-radio-group>
    </div>

    <!-- 恢复默认按钮 -->
    <div class="action-buttons">
      <el-button type="default" @click="handleResetParams" class="reset-button">
        🔄 恢复默认参数
      </el-button>
    </div>
  </el-card>
</template>

<style scoped>
.param-panel {
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

.param-group {
  margin-bottom: 20px;

  &:last-of-type {
    margin-bottom: 16px;
  }
}

.param-label {
  display: block;
  margin-bottom: 8px;
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-primary);
}

.radio-group {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.radio-group :deep(.el-radio) {
  flex-basis: auto;
}

.param-select {
  width: 100%;
}

.action-buttons {
  display: flex;
  gap: 8px;
}

.reset-button {
  width: 100%;
}
</style>
