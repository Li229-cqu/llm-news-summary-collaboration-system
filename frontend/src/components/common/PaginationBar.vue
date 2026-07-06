<script setup lang="ts">
defineProps<{
  currentPage: number
  totalPages: number
}>()

const emit = defineEmits<{ (e: 'change', page: number): void }>()

function getVisiblePages(current: number, total: number): (number | string)[] {
  if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1)
  const pages: (number | string)[] = []
  pages.push(1)
  if (current > 3) pages.push('...')
  const start = Math.max(2, current - 1)
  const end = Math.min(total - 1, current + 1)
  for (let i = start; i <= end; i++) pages.push(i)
  if (current < total - 2) pages.push('...')
  pages.push(total)
  return pages
}
</script>

<template>
  <div class="pagination-bar">
    <button class="page-btn" :disabled="currentPage <= 1" @click="emit('change', 1)" title="首页">&lt;&lt;</button>
    <button class="page-btn" :disabled="currentPage <= 1" @click="emit('change', currentPage - 1)" title="上一页">&lt;</button>
    <template v-for="item in getVisiblePages(currentPage, totalPages)" :key="item">
      <span v-if="item === '...'" class="page-ellipsis">...</span>
      <button v-else class="page-btn" :class="{ active: item === currentPage }" @click="emit('change', Number(item))">{{ item }}</button>
    </template>
    <button class="page-btn" :disabled="currentPage >= totalPages" @click="emit('change', currentPage + 1)" title="下一页">&gt;</button>
    <button class="page-btn" :disabled="currentPage >= totalPages" @click="emit('change', totalPages)" title="尾页">&gt;&gt;</button>
  </div>
</template>

<style scoped>
.pagination-bar {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 4px;
  margin-top: 24px;
  padding-bottom: 8px;
  flex-wrap: wrap;
}
.page-btn {
  min-width: 36px;
  height: 36px;
  padding: 0 8px;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  background: var(--color-bg-card);
  color: var(--color-text-primary);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  user-select: none;
}
.page-btn:hover:not(:disabled):not(.active) {
  background: var(--color-bg-hover);
  border-color: var(--color-primary);
  color: var(--color-primary);
}
.page-btn.active {
  background: #d92d20;
  border-color: var(--color-primary);
  color: #fff;
  font-weight: 600;
  box-shadow: 0 2px 8px rgba(217, 45, 32, 0.25);
}
.page-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
  background: var(--color-bg);
}
.page-ellipsis {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  color: var(--color-text-muted);
  font-size: 14px;
  user-select: none;
}
</style>
