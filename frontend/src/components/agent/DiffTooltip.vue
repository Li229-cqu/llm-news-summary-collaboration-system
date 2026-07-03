<script setup lang="ts">
/** DiffTooltip — 悬浮差异对比浮层。
 *
 * 用途：鼠标 hover 在文本差异标记上时，显示原文 ↔ 清洗后对比。
 * 输入：originalText（原文片段）、cleanedText（清洗后片段）、deletedText（被删内容）、
 *       type（变更类型）、x/y（鼠标坐标）
 * 输出：纯视觉展示，无事件
 * 依赖：无外部依赖，纯 CSS 定位
 */

const props = defineProps<{
  originalText?: string
  cleanedText?: string
  deletedText?: string
  type: 'delete' | 'modify' | 'add'
  x: number
  y: number
}>()

function typeLabel(t: string): string {
  switch (t) {
    case 'delete': return '删除'
    case 'modify': return '修改'
    case 'add': return '新增'
    default: return t
  }
}

/** 防止浮层溢出屏幕 */
function safeX(): string {
  const w = 370
  if (props.x + w + 16 > window.innerWidth) return (props.x - w - 8) + 'px'
  return (props.x + 12) + 'px'
}
function safeY(): string {
  const h = 180
  if (props.y + h + 16 > window.innerHeight) return (props.y - h - 8) + 'px'
  return (props.y + 8) + 'px'
}
</script>

<template>
  <Teleport to="body">
    <div
      class="dt"
      :style="{ left: safeX(), top: safeY() }"
    >
      <div class="dt__head">
        <span class="dt__badge" :class="'dt__badge--' + type">{{ typeLabel(type) }}</span>
      </div>
      <div class="dt__body">
        <!-- 删除：显示原文被删片段 -->
        <div v-if="type === 'delete' && deletedText" class="dt__row">
          <span class="dt__label">已删除</span>
          <span class="dt__del-text">{{ deletedText }}</span>
        </div>
        <!-- 修改：显示原文 vs 清洗后 -->
        <div v-if="type === 'modify'" class="dt__row">
          <span class="dt__label">原文</span>
          <span class="dt__orig-text">{{ originalText }}</span>
        </div>
        <div v-if="type === 'modify'" class="dt__row">
          <span class="dt__label">清洗后</span>
          <span class="dt__clean-text">{{ cleanedText }}</span>
        </div>
        <!-- 新增：显示新增内容 -->
        <div v-if="type === 'add'" class="dt__row">
          <span class="dt__label">新增</span>
          <span class="dt__add-text">{{ cleanedText }}</span>
        </div>
        <!-- 上下文预览（删除类型显示清洗后的上下文） -->
        <div v-if="type === 'delete' && cleanedText" class="dt__row">
          <span class="dt__label">清洗后上下文</span>
          <span class="dt__ctx-text">{{ cleanedText }}</span>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.dt {
  position: fixed;
  z-index: 9999;
  width: 370px;
  max-width: calc(100vw - 24px);
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: 10px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, .14);
  pointer-events: none;
  font-size: 12px;
  line-height: 1.6;
}

.dt__head {
  padding: 10px 14px;
  border-bottom: 1px solid #f3f4f6;
}

.dt__badge {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
  color: #fff;
}
.dt__badge--delete { background: #ef4444; }
.dt__badge--modify { background: #f59e0b; }
.dt__badge--add { background: #16a34a; }

.dt__body {
  padding: 10px 14px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.dt__row {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.dt__label {
  font-size: 10px;
  font-weight: 600;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: .04em;
}

.dt__del-text {
  color: #dc2626;
  text-decoration: line-through;
  background: #fef2f2;
  padding: 4px 8px;
  border-radius: 4px;
  word-break: break-all;
}

.dt__orig-text {
  color: #b45309;
  background: #fffbeb;
  padding: 4px 8px;
  border-radius: 4px;
  word-break: break-all;
  text-decoration: line-through;
}

.dt__clean-text {
  color: #16a34a;
  background: #f0fdf4;
  padding: 4px 8px;
  border-radius: 4px;
  word-break: break-all;
}

.dt__add-text {
  color: #16a34a;
  background: #f0fdf4;
  padding: 4px 8px;
  border-radius: 4px;
  word-break: break-all;
}

.dt__ctx-text {
  color: var(--color-text-secondary);
  background: var(--color-bg-hover);
  padding: 4px 8px;
  border-radius: 4px;
  font-style: italic;
  word-break: break-all;
}
</style>
