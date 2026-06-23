<script setup lang="ts">
import type { NewsElement } from '@/api/ai'

interface Props {
  elements: NewsElement
}

defineProps<Props>()

const elementLabels = {
  who: '谁(Who)',
  what: '什么(What)',
  when: '何时(When)',
  where: '何地(Where)',
  why: '为什么(Why)',
  how: '怎样(How)',
}
</script>

<template>
  <div class="elements-section">
    <h4 class="section-title">📋 新闻六要素</h4>
    <div class="elements-grid">
      <div
        v-for="(label, key) in elementLabels"
        :key="key"
        class="element-item"
      >
        <div class="element-label">{{ label }}</div>
        <div class="element-value">
          {{ elements[key as keyof typeof elements] || '暂无信息' }}
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.elements-section {
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

.elements-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 12px;
}

.element-item {
  padding: 12px;
  background-color: var(--color-bg);
  border-radius: 4px;
  border-left: 3px solid var(--color-primary);
}

.element-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-primary);
  margin-bottom: 6px;
}

.element-value {
  font-size: 14px;
  color: var(--color-text-primary);
  line-height: 1.6;
  word-break: break-word;
}
</style>
