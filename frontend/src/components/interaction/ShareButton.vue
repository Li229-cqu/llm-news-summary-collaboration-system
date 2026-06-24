<template>
  <el-button class="interaction-button" plain @click="handleShare">分享</el-button>
</template>

<script setup lang="ts">
import { ElMessage } from 'element-plus'

async function copyText(text: string) {
  if (navigator.clipboard?.writeText) {
    await navigator.clipboard.writeText(text)
    return
  }

  const textArea = document.createElement('textarea')
  textArea.value = text
  textArea.setAttribute('readonly', 'true')
  textArea.style.position = 'absolute'
  textArea.style.left = '-9999px'
  document.body.appendChild(textArea)
  textArea.select()
  const success = document.execCommand('copy')
  document.body.removeChild(textArea)

  if (!success) {
    throw new Error('copy failed')
  }
}

async function handleShare() {
  try {
    await copyText(window.location.href)
    ElMessage.success('链接已复制')
  } catch {
    ElMessage.warning('复制失败，请手动复制地址')
  }
}
</script>

<style scoped>
.interaction-button {
  display: inline-flex;
  align-items: center;
}

@media (max-width: 640px) {
  .interaction-button {
    width: 100%;
  }
}
</style>
