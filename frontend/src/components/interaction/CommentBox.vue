<template>
  <div class="comment-box">
    <div class="comment-box__header">
      <div class="comment-box__title">{{ titleText }}</div>
      <div class="comment-box__hint">{{ hintText }}</div>
    </div>
    <el-input
      ref="textareaRef"
      v-model="content"
      type="textarea"
      :rows="4"
      :placeholder="placeholder"
      :disabled="loading"
      resize="none"
    />

    <!-- 已选图片预览 -->
    <div v-if="uploadedImage" class="comment-box__preview">
      <img :src="uploadedImage" alt="评论图片预览" />
      <el-button
        class="comment-box__preview-remove"
        :icon="Close"
        circle
        size="small"
        @click="removeImage"
      />
    </div>

    <div class="comment-box__actions">
      <div class="comment-box__tools">
        <!-- 表情按钮 -->
        <el-popover
          placement="top-start"
          :width="360"
          trigger="click"
          :show-arrow="false"
        >
          <template #reference>
            <el-button text :disabled="loading" title="插入表情">
              😀 表情
            </el-button>
          </template>
          <div class="emoji-picker-wrapper" @emoji-click="onEmojiClick">
            <emoji-picker locale="zh"></emoji-picker>
          </div>
        </el-popover>

        <!-- 上传图片按钮 -->
        <el-button text :disabled="loading || uploadingImage" @click="triggerFileInput" title="上传图片">
          <el-icon v-if="uploadingImage" class="is-loading"><Loading /></el-icon>
          <span v-else>🖼 图片</span>
        </el-button>
        <input
          ref="fileInputRef"
          type="file"
          accept="image/jpeg,image/png,image/gif,image/webp"
          style="display: none"
          @change="onFileChange"
        />
      </div>

      <el-button type="primary" class="comment-box__submit" :loading="loading" @click="handleSubmit">
        {{ buttonText }}
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, ref } from 'vue'
import { Close, Loading } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import 'emoji-picker-element'
import { uploadCommentMedia } from '@/api/interaction'

const props = withDefaults(
  defineProps<{
    placeholder?: string
    loading?: boolean
    buttonText?: string
    title?: string
    hint?: string
  }>(),
  {
    placeholder: '写下你的评论',
    loading: false,
    buttonText: '提交评论',
    title: '发表评论',
    hint: '支持图片和表情，写下你的想法',
  },
)

const emit = defineEmits<{
  (event: 'submit', content: string, mediaJson: Record<string, unknown> | null): void
}>()

const content = ref('')
const textareaRef = ref<InstanceType<typeof import('element-plus').ElInput> | null>(null)
const fileInputRef = ref<HTMLInputElement | null>(null)
const titleText = computed(() => props.title || '发表评论')
const hintText = computed(() => props.hint || '')

// 图片上传状态
const uploadingImage = ref(false)
const uploadedImage = ref<string | null>(null)
const uploadedImageUrl = ref<string | null>(null)

// emoji 收集
const insertedEmojis = ref<string[]>([])

function triggerFileInput() {
  fileInputRef.value?.click()
}

async function onFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return

  // 前端初步大小校验
  if (file.size > 5 * 1024 * 1024) {
    ElMessage.warning('图片大小不能超过 5MB')
    input.value = ''
    return
  }

  // 本地预览
  const previewUrl = URL.createObjectURL(file)
  uploadedImage.value = previewUrl

  uploadingImage.value = true
  try {
    const result = await uploadCommentMedia(file)
    uploadedImageUrl.value = result.url
    ElMessage.success('图片上传成功')
  } catch (err) {
    uploadedImage.value = null
    uploadedImageUrl.value = null
    ElMessage.error(err instanceof Error ? err.message : '图片上传失败')
  } finally {
    uploadingImage.value = false
    input.value = ''
  }
}

function removeImage() {
  uploadedImage.value = null
  uploadedImageUrl.value = null
}

async function onEmojiClick(event: Event) {
  const detail = (event as CustomEvent).detail
  if (detail?.unicode) {
    insertedEmojis.value.push(detail.unicode)
    // 插入 emoji 到 textarea 光标位置
    const textarea = textareaRef.value?.$el?.querySelector('textarea') as HTMLTextAreaElement | null
    if (textarea) {
      const start = textarea.selectionStart ?? content.value.length
      const end = textarea.selectionEnd ?? start
      const before = content.value.slice(0, start)
      const after = content.value.slice(end)
      const newContent = before + detail.unicode + after
      content.value = newContent
      // 恢复光标位置
      await nextTick()
      const pos = start + (detail.unicode as string).length
      textarea.setSelectionRange(pos, pos)
      textarea.focus()
    }
  }
}

function handleSubmit() {
  const value = content.value.trim()

  if (!value && !uploadedImageUrl.value) {
    ElMessage.warning('评论内容不能为空')
    return
  }

  // 构建 media_json
  const mediaJson: Record<string, unknown> = {}
  const images: string[] = []
  if (uploadedImageUrl.value) {
    images.push(uploadedImageUrl.value)
  }
  if (images.length > 0) {
    mediaJson.images = images
  }
  if (insertedEmojis.value.length > 0) {
    mediaJson.emojis = [...insertedEmojis.value]
  }

  const finalMediaJson = Object.keys(mediaJson).length > 0 ? mediaJson : null

  emit('submit', value || ' ', finalMediaJson)
  content.value = ''
  uploadedImage.value = null
  uploadedImageUrl.value = null
  insertedEmojis.value = []
}
</script>

<style scoped>
.comment-box {
  display: grid;
  gap: 12px;
  padding: 16px;
  border: 1px solid color-mix(in srgb, var(--color-primary) 8%, var(--color-border));
  border-radius: 18px;
  background: linear-gradient(180deg, color-mix(in srgb, var(--color-primary) 4%, var(--color-bg-card)), var(--color-bg-card));
  box-shadow: 0 1px 0 rgb(15 23 42 / 3%);
}

.comment-box__header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
}

.comment-box__title {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.comment-box__hint {
  font-size: 12px;
  color: var(--color-text-secondary);
}

.comment-box__preview {
  position: relative;
  display: inline-block;
  max-width: 200px;
}

.comment-box__preview img {
  width: 100%;
  height: auto;
  border-radius: 8px;
  border: 1px solid var(--color-border);
}

.comment-box__preview-remove {
  position: absolute;
  top: -8px;
  right: -8px;
}

.comment-box__actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.comment-box__tools {
  display: flex;
  align-items: center;
  gap: 6px;
}

.emoji-picker-wrapper {
  margin: -12px;
}

.comment-box__submit {
  min-width: 110px;
}

@media (max-width: 640px) {
  .comment-box {
    padding: 12px;
  }

  .comment-box__header {
    flex-direction: column;
    align-items: flex-start;
  }

  .comment-box__actions {
    flex-wrap: wrap;
    gap: 8px;
    justify-content: flex-end;
  }

  .comment-box__actions :deep(.el-button--primary) {
    width: 100%;
  }
}
</style>
