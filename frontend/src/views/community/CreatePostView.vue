<template>
  <main class="create-post-page">
    <div class="page-header">
      <el-button text @click="goBack">
        <el-icon><ArrowLeft /></el-icon>
        &#36820;&#22238;&#31038;&#21306;
      </el-button>
      <el-breadcrumb separator="/">
        <el-breadcrumb-item :to="{ path: '/community' }">&#31038;&#21306;&#24191;&#22330;</el-breadcrumb-item>
        <el-breadcrumb-item>&#21457;&#24067;&#24086;&#23376;</el-breadcrumb-item>
      </el-breadcrumb>
    </div>

    <div class="create-layout">
      <div class="create-main">
        <el-card class="sidebar-card" shadow="never">
          <h4 class="sidebar-title">&#21457;&#24086;&#25552;&#31034;</h4>
          <ul class="tip-list">
            <li>&#26631;&#39064;&#26368;&#22810; 80 &#23383;&#65292;&#35831;&#31616;&#26126;&#25212;&#35201;</li>
            <li>&#27491;&#25991;&#26368;&#22810; 2000 &#23383;</li>
            <li>&#26368;&#22810;&#36873;&#25321; 5 &#20010;&#26631;&#31614;&#20998;&#31867;</li>
            <li>&#20851;&#32852;&#26032;&#38395;&#21518;&#65292;&#20320;&#30340;&#24086;&#23376;&#20250;&#26174;&#31034;&#26032;&#38395;&#26469;&#28304;</li>
            <li>&#35831;&#21451;&#21892;&#21457;&#35328;&#65292;&#29702;&#24615;&#35752;&#35770;</li>
          </ul>
        </el-card>

        <el-card class="create-card" shadow="never">
          <h2 class="create-title">&#21457;&#24067;&#26032;&#24086;&#23376;</h2>

          <el-form label-width="0" @submit.prevent="submitPost">
            <div class="form-section">
              <div class="section-label">&#26631;&#39064;</div>
              <el-input
                v-model="form.title"
                placeholder="&#35831;&#36755;&#20837;&#24086;&#23376;&#26631;&#39064;"
                maxlength="80"
                show-word-limit
                class="input-title"
              />
            </div>

            <div class="form-section">
              <div class="section-label">&#27491;&#25991;</div>
              <el-input
                v-model="form.content"
                type="textarea"
                placeholder="&#20998;&#20139;&#20320;&#30340;&#35266;&#28857;&#12289;&#38382;&#39064;&#25110;&#21457;&#29616;..."
                :rows="8"
                maxlength="2000"
                show-word-limit
                class="input-content"
              />
            </div>

            <div class="form-section">
              <div class="section-label">&#36873;&#25321;&#26631;&#31614;&#65288;&#26368;&#22810;5&#20010;&#65289;</div>
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
              <div class="section-label">&#20851;&#32852;&#26032;&#38395;</div>
              <NewsSearchSelector
                ref="newsSearchRef"
                @select="handleNewsSelect"
                @clear="handleNewsClear"
              />
            </div>

            <div class="form-actions">
              <el-button @click="goBack">&#21462;&#28040;</el-button>
              <el-button type="primary" :loading="submitting" :disabled="submitting" @click="submitPost">
                &#21457;&#24067;
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
import { ArrowLeft } from '@element-plus/icons-vue'
import { createPost, getAvailableTags, type TagCount } from '@/api/community'
import { type NewsItem } from '@/api/news'
import NewsSearchSelector from '@/components/community/NewsSearchSelector.vue'

const router = useRouter()
const route = useRoute()

const form = ref({ title: '', content: '', tags: [] as string[], related_news_id: null as number | null })
const submitting = ref(false)
const newsSearchRef = ref<InstanceType<typeof NewsSearchSelector>>()
const availableTags = ref<TagCount[]>([])

function goBack() { router.push('/community') }

function handleNewsSelect(news: NewsItem) { form.value.related_news_id = news.id }
function handleNewsClear() { form.value.related_news_id = null }
function resetForm() {
  form.value = { title: '', content: '', tags: [], related_news_id: null }
  newsSearchRef.value?.reset()
}

async function submitPost() {
  const title = form.value.title.trim()
  const content = form.value.content.trim()
  if (!title || !content) {
    ElMessage.warning(!title ? '\u8bf7\u8f93\u5165\u5e16\u5b50\u6807\u9898' : '\u8bf7\u8f93\u5165\u5e16\u5b50\u5185\u5bb9')
    return
  }
  submitting.value = true
  try {
    const payload: { title: string; content: string; tags: string[]; related_news_id?: number | null } = { title, content, tags: form.value.tags }
    if (form.value.related_news_id) payload.related_news_id = form.value.related_news_id
    await createPost(payload)
    ElMessage.success('鍙戝竷鎴愬姛')
    router.push('/community')
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '鍙戝笘澶辫触')
  } finally { submitting.value = false }
}

onMounted(async () => {
  try { availableTags.value = await getAvailableTags() } catch {
    availableTags.value = [
      { name: '鏃舵斂', count: 0 }, { name: '缁忔祹', count: 0 }, { name: '绉戞妧', count: 0 },
      { name: '鏁欒偛', count: 0 }, { name: '鍐涗簨', count: 0 }, { name: '绀句細', count: 0 },
      { name: '鍥介檯', count: 0 }, { name: '浣撹偛', count: 0 }, { name: '濞变箰', count: 0 },
      { name: '鍋ュ悍', count: 0 },
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
  box-shadow: 0 8px 24px rgba(34, 78, 130, 0.08); background: rgba(255, 255, 255, 0.94);
  width: 100%;
  flex-shrink: 0;
}
.create-card :deep(.el-card__body) { padding: 28px 32px; }
.create-title { font-size: 22px; font-weight: 700; color: #111827; margin: 0 0 24px; }
.form-section { margin-bottom: 24px; }
.section-label { font-size: 14px; font-weight: 600; color: #374151; margin-bottom: 10px; }
.input-title :deep(.el-input__wrapper) { height: 48px; border-radius: 8px; }
.input-content :deep(.el-textarea__inner) { min-height: 200px; border-radius: 8px; }
.tags-group { display: flex; flex-wrap: wrap; gap: 12px; }
.form-actions { display: flex; justify-content: flex-end; gap: 12px; padding-top: 16px; border-top: 1px solid #e5e7eb; }
.sidebar-card {
  border: 1px solid rgba(210, 222, 238, 0.86); border-radius: 12px;
  box-shadow: 0 8px 24px rgba(34, 78, 130, 0.08); background: rgba(255, 255, 255, 0.94);
  width: 100%;
  flex-shrink: 0;
}
.sidebar-card :deep(.el-card__body) {
  padding: 18px 32px;
}
.sidebar-title { font-size: 16px; font-weight: 700; color: #111827; margin: 0 0 12px; }
.tip-list { margin: 0; padding-left: 18px; display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 8px 24px; }
.tip-list li { font-size: 13px; color: #6b7280; line-height: 1.6; }
@media (max-width: 1100px) { .tip-list { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
@media (max-width: 768px) { .create-post-page { padding: 12px; } .create-main { padding-right: 0; } .create-card :deep(.el-card__body), .sidebar-card :deep(.el-card__body) { padding: 18px; } .tip-list { grid-template-columns: 1fr; } }
</style>
