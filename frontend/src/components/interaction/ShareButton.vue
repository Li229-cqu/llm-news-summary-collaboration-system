<template>
  <el-button
    class="interaction-button"
    plain
    :loading="loading"
    @click="handleScreenshot"
  >
    {{ loading ? '生成截图中...' : '截图分享' }}
  </el-button>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import html2canvas from 'html2canvas'

const props = defineProps<{
  targetSelector?: string
  title?: string
}>()

const loading = ref(false)

function sanitizeFilename(name: string): string {
  if (!name) return `news-share-${Date.now()}`
  const safe = name.replace(/[\\/:*?"<>|]/g, '_').trim()
  return safe.slice(0, 40) || `news-share-${Date.now()}`
}

function sanitizeClonedStyles(root: HTMLElement, clonedWindow: Window) {
  const elements: HTMLElement[] = [root, ...Array.from(root.querySelectorAll('*')) as HTMLElement[]]
  elements.forEach((el) => {
    const style = clonedWindow.getComputedStyle(el)
    const bgImage = style.backgroundImage || ''
    const bg = style.background || ''
    const boxShadow = style.boxShadow || ''
    const borderColor = style.borderColor || ''
    const color = style.color || ''

    const hasUnsupportedColor =
      bgImage.includes('color(') || bgImage.includes('color-mix(') ||
      bg.includes('color(') || bg.includes('color-mix(') ||
      boxShadow.includes('color(') || boxShadow.includes('color-mix(') ||
      borderColor.includes('color(') || borderColor.includes('color-mix(') ||
      color.includes('color(') || color.includes('color-mix(')

    const hasGradient =
      bgImage.includes('linear-gradient') || bgImage.includes('radial-gradient') ||
      bgImage.includes('conic-gradient')

    const hasVar = bgImage.includes('var(') || bg.includes('var(') ||
      boxShadow.includes('var(') || borderColor.includes('var(')

    if (hasUnsupportedColor || hasVar) {
      el.style.backgroundImage = 'none'
      if (!el.style.backgroundColor || el.style.backgroundColor === 'transparent') {
        el.style.backgroundColor = 'var(--color-bg-card)'
      }
      el.style.boxShadow = 'none'
      el.style.borderColor = 'var(--color-border)'
      el.style.color = 'var(--color-text-primary)'
    } else if (hasGradient) {
      el.style.backgroundImage = 'none'
      if (!el.style.backgroundColor || el.style.backgroundColor === 'transparent') {
        el.style.backgroundColor = 'var(--color-bg-hover)'
      }
    }
  })
}

function triggerDownload(url: string, filename: string) {
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

async function handleScreenshot() {
  const selector = props.targetSelector || '.news-detail-main'
  const target = document.querySelector(selector) as HTMLElement | null

  if (!target) {
    ElMessage.warning('未找到可截图的内容区域')
    return
  }

  loading.value = true
  try {
    const canvas = await html2canvas(target, {
      backgroundColor: 'var(--color-bg-card)',
      useCORS: true,
      scale: window.devicePixelRatio || 2,
      logging: false,
      onclone: (clonedDoc) => {
        const clonedTarget = clonedDoc.querySelector(selector) as HTMLElement | null
        if (clonedTarget && clonedDoc.defaultView) {
          sanitizeClonedStyles(clonedTarget, clonedDoc.defaultView)
        }
      },
    })

    const filename = sanitizeFilename(props.title || '') + '.png'

    canvas.toBlob((blob) => {
      if (!blob) {
        ElMessage.error('截图生成失败，请稍后重试')
        return
      }
      const url = URL.createObjectURL(blob)
      triggerDownload(url, filename)
      URL.revokeObjectURL(url)
      ElMessage.success('截图已下载')
    }, 'image/png')
  } catch (error) {
    console.error('截图失败:', error)
    ElMessage.error('截图生成失败，请稍后重试')
  } finally {
    loading.value = false
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
