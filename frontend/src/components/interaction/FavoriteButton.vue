<template>
  <el-button
    class="interaction-button"
    :class="{ 'is-active': favorited }"
    :type="favorited ? 'primary' : 'default'"
    :plain="!favorited"
    :disabled="disabled"
    :loading="loading"
    @click="handleToggle"
  >
    <span>{{ favorited ? '已收藏' : '收藏' }}</span>
    <span class="interaction-button__count">{{ count }}</span>
  </el-button>
</template>

<script setup lang="ts">
const props = withDefaults(
  defineProps<{
    newsId: number | string
    favorited: boolean
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
  box-shadow: 0 6px 14px rgb(37 99 235 / 14%);
}

@media (max-width: 640px) {
  .interaction-button {
    width: 100%;
  }
}
</style>
