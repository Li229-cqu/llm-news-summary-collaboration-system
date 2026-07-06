<template>
  <el-button
    class="interaction-button"
    :class="{ 'is-active': liked }"
    :type="liked ? 'primary' : 'default'"
    :plain="!liked"
    :disabled="disabled"
    :loading="loading"
    @click="handleToggle"
  >
    <span class="interaction-button__icon">{{ liked ? '👍' : '👍' }}</span>
    <span>{{ liked ? '已点赞' : '点赞' }}</span>
    <span class="interaction-button__count">{{ count }}</span>
  </el-button>
</template>

<script setup lang="ts">
const props = withDefaults(
  defineProps<{
    newsId: number | string
    liked: boolean
    count: number
    disabled?: boolean
    loading?: boolean
  }>(),
  {
    disabled: false,
    loading: false,
  },
)

const emit = defineEmits<{
  (event: 'toggle', newsId: number | string): void
}>()

function handleToggle() {
  if (props.disabled || props.loading) {
    return
  }

  emit('toggle', props.newsId)
}
</script>

<style scoped>
.interaction-button {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-width: 116px;
}

.interaction-button__count {
  color: inherit;
  font-size: 12px;
  font-weight: 600;
  opacity: 0.88;
}

.interaction-button.is-active {
  box-shadow: 0 6px 14px color-mix(in srgb, var(--color-primary) 30%, transparent);
}

:global(:root.dark) .interaction-button {
  --el-button-bg-color: var(--control-bg);
  --el-button-border-color: var(--color-border);
  --el-button-text-color: var(--color-text-secondary);
  --el-button-hover-bg-color: var(--control-hover-bg);
  --el-button-hover-border-color: color-mix(in srgb, var(--color-primary) 35%, var(--color-border));
  --el-button-hover-text-color: var(--color-primary);
  --el-button-active-bg-color: var(--color-primary-soft);
  --el-button-active-border-color: var(--color-primary);
  --el-button-active-text-color: var(--color-primary);
}

:global(:root.dark) .interaction-button.is-active {
  --el-button-bg-color: var(--color-primary);
  --el-button-border-color: var(--color-primary);
  --el-button-text-color: #fff;
  --el-button-hover-bg-color: var(--color-primary);
  --el-button-hover-border-color: var(--color-primary);
  --el-button-hover-text-color: #fff;
}

@media (max-width: 640px) {
  .interaction-button {
    width: 100%;
  }
}
</style>
