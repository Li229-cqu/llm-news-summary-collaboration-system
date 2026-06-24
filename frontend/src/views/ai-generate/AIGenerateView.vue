<script setup lang="ts">
import { onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import AIInputPanel from '@/components/ai/AIInputPanel.vue'
import AIParamPanel from '@/components/ai/AIParamPanel.vue'
import AIResultPanel from '@/components/ai/AIResultPanel.vue'
import AIGenerateHistory from '@/components/ai/AIGenerateHistory.vue'
import { useAIDraftStore } from '@/stores/aiDraft'
import { generateTitleSummary } from '@/api/ai'

const aiDraft = useAIDraftStore()
const route = useRoute()

function loadNewsDraftFromSession() {
  const rawDraft = sessionStorage.getItem('ai_draft_from_news')

  if (!rawDraft) {
    return
  }

  try {
    const draft = JSON.parse(rawDraft) as {
      source?: string
      news_id?: number | string
      title?: string
      summary?: string
      content?: string
    }

    if (draft.source !== 'news' || !draft.content?.trim()) {
      return
    }

    aiDraft.setFromNews({
      id: draft.news_id ?? '',
      title: draft.title ?? '',
      content: draft.content,
    })
  } catch {
    // 无效草稿数据直接忽略，保持页面可用
  }
}

function syncDraftFromNewsRoute() {
  if (String(route.query.source ?? '') !== 'news') {
    return
  }

  const routeNewsId = String(route.query.newsId ?? '').trim()
  const currentNewsId = String(aiDraft.sourceNewsId ?? '').trim()

  if (routeNewsId && currentNewsId === routeNewsId && aiDraft.inputText.trim()) {
    return
  }

  loadNewsDraftFromSession()
}

const handleGenerate = async () => {
  // 输入验证
  if (aiDraft.inputText.trim().length === 0) {
    aiDraft.setError('请输入新闻正文后再生成')
    ElMessage.warning('请输入新闻正文后再生成')
    return
  }

  // 清空旧结果和错误
  aiDraft.clearResult()
  aiDraft.setError('')

  // 开始生成
  aiDraft.setLoading(true)

  try {
    const result = await generateTitleSummary({
      input_text: aiDraft.inputText,
      title_count: aiDraft.params.title_count,
      summary_type: aiDraft.params.summary_type,
      summary_style: aiDraft.params.summary_style,
      title_style: aiDraft.params.title_style,
      summary_length: aiDraft.params.summary_length,
    })

    aiDraft.setResult(result)
    ElMessage.success('标题和摘要生成成功')
  } catch (error) {
    let errorMessage = 'AI 服务暂时不可用，请稍后重试'

    if (error instanceof Error) {
      const msg = error.message || ''
      // 特殊处理 timeout 错误
      if (msg.includes('timeout') || msg.includes('60000ms')) {
        errorMessage = 'AI 生成耗时较长，请稍后重试或缩短新闻正文'
      } else {
        errorMessage = msg
      }
    }

    aiDraft.setError(errorMessage)
    ElMessage.error(errorMessage)
  } finally {
    aiDraft.setLoading(false)
  }
}

onMounted(() => {
  syncDraftFromNewsRoute()
})

watch(
  () => [route.query.source, route.query.newsId],
  () => {
    syncDraftFromNewsRoute()
  },
)
</script>

<template>
  <main class="page-container">
    <!-- 页面标题 -->
    <el-card class="app-card page-header">
      <h1>AI 标题摘要生成</h1>
      <p>智能生成新闻标题和摘要，支持多种风格和参数配置。</p>
    </el-card>

    <!-- 主要内容区：左侧输入，右侧参数 -->
    <div class="content-layout">
      <div class="content-left">
        <!-- 输入区组件 -->
        <AIInputPanel />
      </div>

      <div class="content-right">
        <!-- 参数选择区组件 -->
        <AIParamPanel />

        <!-- 生成按钮 -->
        <el-card class="app-card generate-action">
          <el-button
            type="primary"
            size="large"
            class="generate-button"
            @click="handleGenerate"
            :loading="aiDraft.loading"
            :disabled="aiDraft.loading"
          >
            {{ aiDraft.loading ? '✨ 生成中...' : '✨ 生成标题和摘要' }}
          </el-button>
        </el-card>
      </div>
    </div>

    <!-- 生成结果区域 -->
    <AIResultPanel />

    <!-- 生成历史区域 -->
    <AIGenerateHistory />
  </main>
</template>

<style scoped>
.page-container {
  padding: 24px;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h1 {
  margin-top: 0;
  margin-bottom: 8px;
  font-size: 24px;
  color: var(--color-text-primary);
}

.page-header p {
  margin: 0;
  color: var(--color-text-secondary);
  font-size: 14px;
}

/* 内容布局：响应式两栏 */
.content-layout {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 24px;
}

@media (max-width: 1200px) {
  .content-layout {
    grid-template-columns: 1fr;
  }
}

.content-left {
  /* 左侧输入区 */
}

.content-right {
  /* 右侧参数区和生成按钮 */
  display: flex;
  flex-direction: column;
  gap: 0;
}

/* 生成操作卡片 */
.generate-action {
  border-top: none;
  border-radius: 0 0 var(--border-radius-card) var(--border-radius-card);
}

.generate-button {
  width: 100%;
  height: 48px;
  font-size: 16px;
  font-weight: 600;
}

/* 占位区域 */
.placeholder-section {
  margin-bottom: 16px;

  &:last-child {
    margin-bottom: 0;
  }
}

.section-header {
  display: flex;
  align-items: center;
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.placeholder-content {
  padding: 40px 20px;
  text-align: center;
  background-color: rgba(64, 158, 255, 0.05);
  border-radius: 4px;
}

.placeholder-text {
  margin: 0 0 8px;
  font-size: 16px;
  color: var(--color-text-primary);
  font-weight: 500;
}

.placeholder-description {
  margin: 0;
  font-size: 14px;
  color: var(--color-text-secondary);
}
</style>
