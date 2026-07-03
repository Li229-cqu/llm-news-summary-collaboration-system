<script setup lang="ts">
defineProps<{
  visible?: boolean
}>()

defineEmits<{
  (e: 'refresh'): void
}>()
</script>

<template>
  <div class="history-panel-placeholder">
    <div class="placeholder-content">
      <span class="placeholder-icon">📚</span>
      <span class="placeholder-text">历史记录组件占位</span>
    </div>
  </div>
</template>

<style scoped>
.history-panel-placeholder {
  padding: 40px 20px;
  text-align: center;
  background-color: var(--color-bg-hover);
  border-radius: 6px;
  border: 1px dashed #e5e7eb;
}

.placeholder-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.placeholder-icon {
  font-size: 24px;
}

.placeholder-text {
  font-size: 14px;
  color: var(--color-text-secondary);
}
</style>