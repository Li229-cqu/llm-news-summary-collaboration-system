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

function resolveVar(value: string): string {
  // Read the actual computed value from the live document, where CSS variables are defined
  const testEl = document.createElement('div')
  testEl.style.setProperty('background', value)
  document.body.appendChild(testEl)
  const computed = getComputedStyle(testEl).backgroundImage || getComputedStyle(testEl).background
  document.body.removeChild(testEl)
  // If the computed value still contains var(), return a safe fallback
  if (!computed || computed === 'none' || computed.includes('var(')) return ''
  return computed
}

function sanitizeClonedStyles(root: HTMLElement, clonedWindow: Window) {
  // Read resolved values from the live document once
  const liveStyle = getComputedStyle(document.documentElement)
  const cardBg = liveStyle.getPropertyValue('--color-bg-card').trim() || '#ffffff'
  const hoverBg = liveStyle.getPropertyValue('--color-bg-hover').trim() || '#f8fafc'
  const borderColor = liveStyle.getPropertyValue('--color-border').trim() || '#e2e8f0'
  const textColor = liveStyle.getPropertyValue('--color-text-primary').trim() || '#334155'

  const elements: HTMLElement[] = [root, ...Array.from(root.querySelectorAll('*')) as HTMLElement[]]
  elements.forEach((el) => {
    const style = clonedWindow.getComputedStyle(el)
    const bgImage = style.backgroundImage || ''
    const bg = style.background || ''
    const boxShadow = style.boxShadow || ''
    const brdColor = style.borderColor || ''
    const color = style.color || ''

    const hasUnsupportedColor =
      bgImage.includes('color(') || bgImage.includes('color-mix(') ||
      bg.includes('color(') || bg.includes('color-mix(') ||
      boxShadow.includes('color(') || boxShadow.includes('color-mix(') ||
      brdColor.includes('color(') || brdColor.includes('color-mix(') ||
      color.includes('color(') || color.includes('color-mix(')

    const hasGradient =
      bgImage.includes('linear-gradient') || bgImage.includes('radial-gradient') ||
      bgImage.includes('conic-gradient')

    const hasVar = bgImage.includes('var(') || bg.includes('var(') ||
      boxShadow.includes('var(') || brdColor.includes('var(') || color.includes('var(')

    if (hasUnsupportedColor || hasVar) {
      el.style.backgroundImage = 'none'
      const currentBg = style.backgroundColor
      if (!currentBg || currentBg === 'transparent' || currentBg === 'rgba(0, 0, 0, 0)') {
        el.style.backgroundColor = cardBg
      }
      el.style.boxShadow = 'none'
      el.style.borderColor = borderColor
      el.style.color = textColor
    } else if (hasGradient) {
      el.style.backgroundImage = 'none'
      const currentBg = style.backgroundColor
      if (!currentBg || currentBg === 'transparent' || currentBg === 'rgba(0, 0, 0, 0)') {
        el.style.backgroundColor = hoverBg
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
    const liveStyle = getComputedStyle(document.documentElement)
    const resolvedBg = liveStyle.getPropertyValue('--color-bg-card').trim() || '#ffffff'

    const canvas = await html2canvas(target, {
      backgroundColor: resolvedBg,
      useCORS: true,
      allowTaint: true,
      scale: Math.min(window.devicePixelRatio || 2, 2),
      logging: false,
      onclone: (clonedDoc) => {
        try {
          // html2canvas 不支持 CSS Color Level 4 的 color()/color-mix()，
          // 必须从样式表和内联样式中移除，否则解析时直接抛错
          clonedDoc.querySelectorAll('style').forEach((el) => {
            if (el.textContent) {
              el.textContent = el.textContent
                .replace(/color-mix\(/gi, 'x-cm(')
                .replace(/color\(/gi, 'x-c(')
            }
          })
          clonedDoc.querySelectorAll('[style]').forEach((el) => {
            const s = el.getAttribute('style') || ''
            if (s.includes('color(') || s.includes('color-mix(')) {
              el.setAttribute('style',
                s.replace(/color-mix\(/gi, 'x-cm(').replace(/color\(/gi, 'x-c('),
              )
            }
          })
          const clonedTarget = clonedDoc.querySelector(selector) as HTMLElement | null
          if (clonedTarget && clonedDoc.defaultView) {
            sanitizeClonedStyles(clonedTarget, clonedDoc.defaultView)
          }
        } catch {
          // 样式清洗失败不阻塞截图
        }
      },
    })

    const filename = sanitizeFilename(props.title || '') + '.png'

    // 优先 toBlob（更小的文件），失败时回退到 toDataURL
    if (typeof canvas.toBlob === 'function') {
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
    } else {
      const dataUrl = canvas.toDataURL('image/png')
      triggerDownload(dataUrl, filename)
      ElMessage.success('截图已下载')
    }
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
