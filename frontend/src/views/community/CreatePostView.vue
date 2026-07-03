<template>
  <main class="create-post-page">
    <div class="page-header">
      <el-button text @click="goBack">
        <el-icon><ArrowLeft /></el-icon>
        返回社区
      </el-button>
      <el-breadcrumb separator="/">
        <el-breadcrumb-item :to="{ path: '/community' }">社区广场</el-breadcrumb-item>
        <el-breadcrumb-item>发布帖子</el-breadcrumb-item>
      </el-breadcrumb>
    </div>

    <div class="create-layout">
      <div class="create-main">
        <el-card class="sidebar-card" shadow="never">
          <h4 class="sidebar-title">发帖提示</h4>
          <ul class="tip-list">
            <li>标题最多 80 字，请简明扼要</li>
            <li>正文最多 2000 字</li>
            <li>最多选择 5 个标签分类</li>
            <li>关联新闻后，你的帖子会显示新闻来源</li>
            <li>最多上传 9 张图片，支持 JPG/PNG/GIF/WebP</li>
            <li>请友善发言，理性讨论</li>
          </ul>
        </el-card>

        <el-card class="create-card" shadow="never">
          <h2 class="create-title">发布新帖子</h2>

          <el-form label-width="0" @submit.prevent="submitPost">
            <div class="form-section">
              <div class="section-label">标题</div>
              <el-input
                v-model="form.title"
                placeholder="请输入帖子标题"
                maxlength="80"
                show-word-limit
                class="input-title"
              />
            </div>

            <div class="form-section">
              <div class="section-label">正文</div>
              <el-input
                v-model="form.content"
                type="textarea"
                placeholder="分享你的观点、问题或发现..."
                :rows="8"
                maxlength="2000"
                show-word-limit
                class="input-content"
              />
            </div>

            <div class="form-section">
              <div class="section-label">图片</div>
              <div class="image-upload-area">
                <div class="image-preview-list">
                  <div v-for="(img, idx) in uploadedImages" :key="idx" class="image-preview-item">
                    <el-image
                      :src="resolveImageUrl(img.serverUrl || img.previewUrl)"
                      fit="cover"
                      class="preview-img"
                      :preview-src-list="uploadedImages.filter(i => i.serverUrl).map(i => resolveImageUrl(i.serverUrl))"
                      preview-teleported
                    />
                    <el-button
                      class="preview-remove"
                      :icon="Close"
                      circle
                      size="small"
                      @click="removeImage(idx)"
                    />
                  </div>
                  <div
                    v-if="uploadedImages.length < 9"
                    class="image-upload-trigger"
                    @click="triggerFileInput"
                  >
                    <el-icon v-if="uploadingImage" class="is-loading"><Loading /></el-icon>
                    <el-icon v-else><Plus /></el-icon>
                    <span>{{ uploadingImage ? '上传中...' : '添加图片' }}</span>
                  </div>
                </div>
                <input
                  ref="fileInputRef"
                  type="file"
                  accept="image/jpeg,image/png,image/gif,image/webp"
                  multiple
                  style="display: none"
                  @change="onFileChange"
                />
                <p class="image-upload-hint">最多上传 9 张图片，支持 JPG、PNG、GIF、WEBP，单张不超过 5MB</p>
              </div>
            </div>

            <div class="form-section">
              <div class="section-label">选择标签（最多5个）</div>
              <el-checkbox-group v-model="form.tags" class="tags-group">
                <el-checkbox
                  v-for="tag in availableTags"
                  :key="tag.name"
                  :label="tag.name"
                  :disabled="form.tags.length >= 5 && !form.tags.includes(tag.name)"
                >
                  {{ tag.name }}
                </el-checkbox>
              </el-checkbox-group>
            </div>

            <div class="form-section">
              <div class="section-label">关联新闻</div>
              <NewsSearchSelector
                ref="newsSearchRef"
                @select="handleNewsSelect"
                @clear="handleNewsClear"
              />
            </div>

            <div class="form-actions">
              <el-button @click="goBack">取消</el-button>
              <el-button type="primary" :loading="submitting" :disabled="submitting" @click="submitPost">
                发布
              </el-button>
            </div>
          </el-form>
        </el-card>
      </div>

    </div>
  </main>
</template>

<script setup lang="ts">
import { ref, nextTick, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, Plus, Close, Loading } from '@element-plus/icons-vue'
import { createPost, getAvailableTags, uploadPostMedia, type TagCount } from '@/api/community'
import { type NewsItem } from '@/api/news'
import { resolveImageUrl } from '@/utils/media'
import NewsSearchSelector from '@/components/community/NewsSearchSelector.vue'

const router = useRouter()
const route = useRoute()

const form = ref({ title: '', content: '', tags: [] as string[], related_news_id: null as number | null })
const submitting = ref(false)
const newsSearchRef = ref<InstanceType<typeof NewsSearchSelector>>()
const availableTags = ref<TagCount[]>([])

// 图片上传状态
const fileInputRef = ref<HTMLInputElement | null>(null)
const uploadingImage = ref(false)
const uploadedImages = ref<{ previewUrl: string; serverUrl: string }[]>([])

function triggerFileInput() {
  fileInputRef.value?.click()
}

async function onFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  const files = input.files
  if (!files || files.length === 0) return

  const remaining = 9 - uploadedImages.value.length
  if (remaining <= 0) {
    ElMessage.warning('最多只能上传 9 张图片')
    input.value = ''
    return
  }

  const toUpload = Array.from(files).slice(0, remaining)

  uploadingImage.value = true
  try {
    for (const file of toUpload) {
      if (!['image/jpeg', 'image/png', 'image/gif', 'image/webp'].includes(file.type)) {
        ElMessage.warning(`仅支持 JPG、PNG、GIF、WEBP 图片，已跳过：${file.name}`)
        continue
      }
      if (file.size > 5 * 1024 * 1024) {
        ElMessage.warning(`单张图片不能超过 5MB，已跳过：${file.name}`)
        continue
      }

      const previewUrl = URL.createObjectURL(file)
      const tempIdx = uploadedImages.value.length
      uploadedImages.value.push({ previewUrl, serverUrl: '' })

      try {
        const result = await uploadPostMedia(file)
        uploadedImages.value[tempIdx].serverUrl = result.url
      } catch {
        uploadedImages.value.splice(tempIdx, 1)
        ElMessage.error(`图片上传失败：${file.name}`)
      }
    }
  } finally {
    uploadingImage.value = false
    input.value = ''
  }
}

function removeImage(idx: number) {
  URL.revokeObjectURL(uploadedImages.value[idx].previewUrl)
  uploadedImages.value.splice(idx, 1)
}

function goBack() { router.push('/community') }

function handleNewsSelect(news: NewsItem) { form.value.related_news_id = news.id }
function handleNewsClear() { form.value.related_news_id = null }
function resetForm() {
  form.value = { title: '', content: '', tags: [], related_news_id: null }
  for (const img of uploadedImages.value) {
    URL.revokeObjectURL(img.previewUrl)
  }
  uploadedImages.value = []
  newsSearchRef.value?.reset()
}

async function submitPost() {
  const title = form.value.title.trim()
  const content = form.value.content.trim()
  if (!title || !content) {
    ElMessage.warning(!title ? '请输入帖子标题' : '请输入帖子内容')
    return
  }
  if (uploadingImage.value) {
    ElMessage.warning('图片仍在上传，请稍后再发布')
    return
  }
  const incomplete = uploadedImages.value.filter(img => !img.serverUrl)
  if (incomplete.length > 0) {
    ElMessage.warning('有图片上传未完成，请移除后重试')
    return
  }
  submitting.value = true
  try {
    const payload: { title: string; content: string; tags: string[]; related_news_id?: number | null; images?: string[] } = { title, content, tags: form.value.tags }
    if (form.value.related_news_id) payload.related_news_id = form.value.related_news_id
    const imageUrls = uploadedImages.value.map(img => img.serverUrl)
    if (imageUrls.length > 0) payload.images = imageUrls
    const newPost = await createPost(payload)
    ElMessage.success('发布成功')
    const newPostId = newPost?.id
    if (newPostId) {
      sessionStorage.setItem('community_pending_new_post_id', String(newPostId))
      router.push({ path: '/community', query: { newPostId: String(newPostId), pinNew: '1' } })
    } else {
      router.push('/community')
    }
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '发帖失败')
  } finally { submitting.value = false }
}

onMounted(async () => {
  try { availableTags.value = await getAvailableTags() } catch {
    availableTags.value = [
      { name: '时政', count: 0 }, { name: '经济', count: 0 }, { name: '科技', count: 0 },
      { name: '教育', count: 0 }, { name: '军事', count: 0 }, { name: '社会', count: 0 },
      { name: '国际', count: 0 }, { name: '体育', count: 0 }, { name: '娱乐', count: 0 },
      { name: '健康', count: 0 },
    ]
  }
  if (route.query.related === '1') {
    nextTick(() => newsSearchRef.value?.activate())
  }
})
</script>

<style scoped>
.create-post-page {
  width: 100%; height: 100%; min-height: 0; padding: 24px 32px; overflow: hidden; display: flex; flex-direction: column;
  background: radial-gradient(circle at 18% 10%, rgba(220, 38, 38, 0.08), transparent 28%),
              linear-gradient(180deg, #fef2f2 0%, #fef7f7 100%);
}
.page-header { display: flex; align-items: center; gap: 16px; margin-bottom: 16px; flex-shrink: 0; }
.create-layout { flex: 1; min-height: 0; width: 100%; display: flex; }
.create-main { min-width: 0; width: 100%; min-height: 0; display: flex; flex-direction: column; gap: 16px; overflow-y: auto; overscroll-behavior: contain; padding-right: 4px; }
.create-card {
  border: 1px solid rgba(210, 222, 238, 0.86); border-radius: 12px;
  box-shadow: 0 8px 24px rgba(34, 78, 130, 0.08); background: var(--color-bg-card);
  width: 100%;
  flex-shrink: 0;
}
.create-card :deep(.el-card__body) { padding: 28px 32px; }
.create-title { font-size: 22px; font-weight: 700; color: var(--color-text-primary); margin: 0 0 24px; }
.form-section { margin-bottom: 24px; }
.section-label { font-size: 14px; font-weight: 600; color: #374151; margin-bottom: 10px; }
.input-title :deep(.el-input__wrapper) { height: 48px; border-radius: 8px; }
.input-content :deep(.el-textarea__inner) { min-height: 200px; border-radius: 8px; }
.tags-group { display: flex; flex-wrap: wrap; gap: 12px; }
.form-actions { display: flex; justify-content: flex-end; gap: 12px; padding-top: 16px; border-top: 1px solid #e5e7eb; }
.sidebar-card {
  border: 1px solid rgba(210, 222, 238, 0.86); border-radius: 12px;
  box-shadow: 0 8px 24px rgba(34, 78, 130, 0.08); background: var(--color-bg-card);
  width: 100%;
  flex-shrink: 0;
}
.sidebar-card :deep(.el-card__body) { padding: 18px 32px; }
.sidebar-title { font-size: 16px; font-weight: 700; color: var(--color-text-primary); margin: 0 0 12px; }
.tip-list { margin: 0; padding-left: 18px; display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 8px 24px; }
.tip-list li { font-size: 13px; color: var(--color-text-secondary); line-height: 1.6; }

/* 图片上传 */
.image-upload-area { width: 100%; }
.image-preview-list { display: flex; flex-wrap: wrap; gap: 12px; }
.image-preview-item { position: relative; width: 100px; height: 100px; border-radius: 8px; overflow: hidden; border: 1px solid var(--color-border); flex-shrink: 0; }
.preview-img { width: 100%; height: 100%; }
.preview-remove { position: absolute; top: -6px; right: -6px; }
.image-upload-trigger { display: flex; flex-direction: column; align-items: center; justify-content: center; width: 100px; height: 100px; border: 1px dashed #c0d4e8; border-radius: 8px; cursor: pointer; color: var(--color-text-muted); font-size: 12px; gap: 4px; transition: all 0.2s; background: var(--color-bg-hover); flex-shrink: 0; }
.image-upload-trigger:hover { border-color: #dc2626; color: #dc2626; }
.image-upload-hint { font-size: 12px; color: var(--color-text-muted); margin-top: 8px; }

@media (max-width: 1100px) { .tip-list { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
@media (max-width: 768px) { .create-post-page { padding: 12px; } .create-main { padding-right: 0; } .create-card :deep(.el-card__body), .sidebar-card :deep(.el-card__body) { padding: 18px; } .tip-list { grid-template-columns: 1fr; } }

:root.dark .create-post-page { background: var(--color-bg); }
</style>
