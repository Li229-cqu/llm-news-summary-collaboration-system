<template>
  <el-form class="news-search-bar" inline @submit.prevent>
    <el-form-item class="news-search-bar__field" label="关键词">
      <el-input
        v-model="keyword"
        clearable
        placeholder="搜索新闻、话题或关键词"
        @keyup.enter="handleSearch"
      />
    </el-form-item>
    <el-form-item>
      <el-button type="primary" @click="handleSearch">搜索</el-button>
      <el-button @click="handleReset">重置</el-button>
    </el-form-item>
  </el-form>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const keyword = ref('')

const emit = defineEmits<{
  (event: 'search', keyword: string): void
  (event: 'reset'): void
}>()

function handleSearch() {
  emit('search', keyword.value.trim())
}

function handleReset() {
  keyword.value = ''
  emit('reset')
}
</script>

<style scoped>
.news-search-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 12px 16px;
  align-items: center;
  padding: 16px;
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-card);
  background: var(--color-bg-card);
}

.news-search-bar__field {
  flex: 1 1 320px;
  min-width: 240px;
  margin-bottom: 0;
}

:deep(.el-form-item) {
  margin-bottom: 0;
}

:deep(.el-form-item__label) {
  color: var(--color-text-secondary);
}
</style>
