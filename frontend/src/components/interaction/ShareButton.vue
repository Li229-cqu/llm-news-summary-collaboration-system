<template>
  <div class="share-button-wrapper">
    <el-button
      class="interaction-button"
      plain
      :loading="loading"
      @click="handleScreenshot"
    >
      {{ loading ? '生成截图中...' : '截图分享' }}
    </el-button>
    <el-button
      class="interaction-button"
      plain
      @click="handleCopyLink"
    >
      复制链接
    </el-button>
  </div>
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
        el.style.backgroundColor = '#ffffff'
      }
      el.style.boxShadow = 'none'
      el.style.borderColor = '#e5e5e5'
      el.style.color = '#333333'
    } else if (hasGradient) {
      el.style.backgroundImage = 'none'
      if (!el.style.backgroundColor || el.style.backgroundColor === 'transparent') {
        el.style.backgroundColor = '#f5f5f5'
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
      backgroundColor: '#ffffff',
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
        ElMessage.error('截图生成失败，已保留复制链接分享方式')
        return
      }
      const url = URL.createObjectURL(blob)
      triggerDownload(url, filename)
      URL.revokeObjectURL(url)
      ElMessage.success('截图已下载')
    }, 'image/png')
  } catch (error) {
    console.error('截图失败:', error)
    ElMessage.error('截图生成失败，已保留复制链接分享方式')
  } finally {
    loading.value = false
  }
}

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

async function handleCopyLink() {
  try {
    await copyText(window.location.href)
    ElMessage.success('链接已复制')
  } catch {
    ElMessage.warning('复制失败，请手动复制地址')
  }
}
</script>

<style scoped>
.share-button-wrapper {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.interaction-button {
  display: inline-flex;
  align-items: center;
}

@media (max-width: 640px) {
  .share-button-wrapper {
    flex-direction: column;
    width: 100%;
  }

  .interaction-button {
    width: 100%;
  }
}
</style>
