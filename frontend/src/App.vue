<template>
  <RouterView v-slot="{ Component }">
    <component :is="Component" />
  </RouterView>
  <!-- 全局浮动 AI 助手 -->
  <FloatingAIAssistant
    logoSrc=""
    title="AI 助手"
  />
</template>

<script setup lang="ts">
import FloatingAIAssistant from '@/components/ai/FloatingAIAssistant.vue'
</script>
