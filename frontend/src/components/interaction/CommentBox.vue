<template>
  <div class="comment-box">
    <el-input
      v-model="content"
      type="textarea"
      :rows="4"
      :placeholder="placeholder"
      :disabled="loading"
      resize="none"
    />
    <div class="comment-box__actions">
      <el-button type="primary" :loading="loading" @click="handleSubmit">
        {{ buttonText }}
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'

const props = withDefaults(
  defineProps<{
    placeholder?: string
    loading?: boolean
    buttonText?: string
  }>(),
  {
    placeholder: '写下你的评论',
    loading: false,
    buttonText: '提交评论',
  },
)

const emit = defineEmits<{
  (event: 'submit', content: string): void
}>()

const content = ref('')

function handleSubmit() {
  const value = content.value.trim()

  if (!value) {
    ElMessage.warning('评论内容不能为空')
    return
  }

  emit('submit', value)
  content.value = ''
}
</script>

<style scoped>
.comment-box {
  display: grid;
  gap: 12px;
  padding: 14px;
  border: 1px solid var(--color-border);
  border-radius: 16px;
  background: var(--color-bg-card);
}

.comment-box__actions {
  display: flex;
  justify-content: flex-end;
}

@media (max-width: 640px) {
  .comment-box {
    padding: 12px;
  }

  .comment-box__actions {
    justify-content: stretch;
  }

  .comment-box__actions :deep(.el-button) {
    width: 100%;
  }
}
</style>
