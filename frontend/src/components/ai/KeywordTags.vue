<script setup lang="ts">
interface Props {
  keywords: string[]
}

defineProps<Props>()
</script>

<template>
  <div class="keywords-section">
    <h4 class="section-title">关键词</h4>
    <div v-if="keywords.length > 0" class="keywords-container">
      <el-tag
        v-for="(keyword, index) in keywords"
        :key="index"
        type="info"
        class="keyword-tag"
      >
        {{ keyword }}
      </el-tag>
    </div>
    <div v-else class="empty-tip">
      暂无关键词
    </div>
  </div>
</template>

<style scoped>
.keywords-section {
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

.keywords-container {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.keyword-tag {
  cursor: pointer;
  transition: all 0.3s;

  &:hover {
    transform: translateY(-2px);
  }
}

.empty-tip {
  font-size: 14px;
  color: var(--color-text-secondary);
  padding: 12px;
  background-color: var(--color-bg);
  border-radius: 4px;
  text-align: center;
}
</style>
