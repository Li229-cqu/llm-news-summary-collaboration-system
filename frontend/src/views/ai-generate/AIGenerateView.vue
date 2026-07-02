<script setup lang="ts">
import { nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import LeftControlPanel from '@/components/ai/LeftControlPanel.vue'
import MainWorkspace from '@/components/ai/MainWorkspace.vue'
import { useAIDraftStore } from '@/stores/aiDraft'
import { aiApi, type AIGenerateRecordItem } from '@/api/ai'

const aiDraft = useAIDraftStore()
const route = useRoute()
const mainWorkspaceRef = ref<{ refreshHistory?: () => void } | null>(null)

type UiMode = 'input' | 'history' | 'detail'

const uiMode = ref<UiMode>('input')
const historyDetailResult = ref<any>(null)

interface Params {
  title_count: number
  summary_type: 'extract' | 'generate'
  title_style: string
  summary_style: string
  summary_length: 'short' | 'long' | 'both'
}

type HistoryRecord = AIGenerateRecordItem

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
  if (aiDraft.inputText.trim().length === 0) {
    aiDraft.setError('请输入新闻正文后再生成')
    ElMessage.warning('请输入新闻正文后再生成')
    return
  }

  aiDraft.clearResult()
  aiDraft.setError('')

  aiDraft.setLoading(true)

  try {
    const result = await aiApi.generate({
      input_text: aiDraft.inputText,
      title_count: aiDraft.params.title_count,
      summary_type: aiDraft.params.summary_type,
      summary_style: aiDraft.params.summary_style,
      title_style: aiDraft.params.title_style,
      summary_length: aiDraft.params.summary_length,
      source: aiDraft.sourceNewsId ? 'news' : 'manual',
      source_news_id: aiDraft.sourceNewsId,
      source_title: aiDraft.sourceTitle,
    })

    aiDraft.setResult(result)
    ElMessage.success('标题和摘要生成成功')
    await nextTick()
    mainWorkspaceRef.value?.refreshHistory?.()
  } catch (error) {
    let errorMessage = 'AI 服务暂时不可用，请稍后重试'

    if (error instanceof Error) {
      const msg = error.message || ''
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

const handleLoadSample = () => {
  const sampleText = `近日，我国新能源汽车产业发展再传捷报。据中国汽车工业协会最新数据显示，今年前五个月，全国新能源汽车销量达到224.7万辆，同比增长46.8%，市场占有率达到27.7%。

在技术创新方面，多家车企宣布在固态电池领域取得重大突破。某知名新能源车企发布公告称，其自主研发的固态电池能量密度已突破500Wh/kg，预计明年将率先搭载于旗下高端车型。该技术将使纯电动汽车续航里程轻松突破1000公里，大幅缓解消费者的续航焦虑。

与此同时，充电基础设施建设也在加速推进。国家能源局数据显示，截至目前，全国充电基础设施累计达630万台，同比增长56%。其中，公共充电桩180万台，私人充电桩450万台，形成了较为完善的充电网络体系。

业内专家表示，随着技术进步和政策支持，新能源汽车产业正处于快速发展的黄金期，预计全年销量有望突破500万辆，继续保持全球领先地位。`
  aiDraft.inputText = sampleText
  aiDraft.clearResult()
  aiDraft.setError('')
  ElMessage.success('已加载示例新闻')
}

const handleClear = () => {
  aiDraft.inputText = ''
  aiDraft.clearResult()
  aiDraft.setError('')
}

const handleParamUpdate = (key: keyof Params, value: any) => {
  if (key === 'title_count') {
    aiDraft.setParams({ [key]: Number(value) })
  } else {
    aiDraft.setParams({ [key]: value })
  }
}

const handleResetParams = () => {
  aiDraft.resetParams()
}

const handleSetUiMode = (mode: UiMode) => {
  uiMode.value = mode
}

const handleLoadHistoryItem = async (record: HistoryRecord) => {
  try {
    const detail = await aiApi.getRecordDetail(record.id)
    aiDraft.inputText = detail.input_text
    aiDraft.setParams(detail.params)
    ElMessage.success('已复用历史输入')
  } catch (error) {
    ElMessage.error('获取历史详情失败')
    return
  }
  uiMode.value = 'input'
}

const handleViewHistoryItem = async (record: HistoryRecord) => {
  try {
    const detail = await aiApi.getRecordDetail(record.id)
    historyDetailResult.value = detail.result
    uiMode.value = 'detail'
  } catch (error) {
    ElMessage.error('获取历史详情失败')
  }
}

onMounted(() => {
  syncDraftFromNewsRoute()
})

onUnmounted(() => {
  aiDraft.resetDraft()
  sessionStorage.removeItem('ai_draft_from_news')
})

watch(
  () => [route.query.source, route.query.newsId],
  () => {
    syncDraftFromNewsRoute()
  },
)
</script>

<template>
  <main class="ai-generate-container">
    <header class="page-header">
      <div class="header-content">
        <div class="header-text">
          <h1>新闻标题与摘要生成</h1>
          <p>输入新闻正文，自动生成多个候选标题和不同长度的摘要内容</p>
        </div>
      </div>
    </header>

    <div class="main-content">
      <aside class="sidebar">
        <LeftControlPanel
          :params="aiDraft.params"
          :ui-mode="uiMode"
          @update:params="handleParamUpdate"
          @reset="handleResetParams"
          @set-ui-mode="handleSetUiMode"
        />
      </aside>
      
      <MainWorkspace
        ref="mainWorkspaceRef"
        :loading="aiDraft.loading"
        :ui-mode="uiMode"
        :history-detail-result="historyDetailResult"
        @generate="handleGenerate"
        @clear="handleClear"
        @load-sample="handleLoadSample"
        @load-history-item="handleLoadHistoryItem"
        @view-history-item="handleViewHistoryItem"
        @set-ui-mode="handleSetUiMode"
      />
    </div>
  </main>
</template>

<style scoped>
.ai-generate-container {
  padding: 0;
  min-height: calc(100vh - 120px);
  display: flex;
  flex-direction: column;
}

.page-header {
  background: #fff;
  border: 1px solid #f1d4d4;
  border-radius: 22px;
  padding: 32px 40px;
  margin-bottom: 24px;
  box-shadow: 0 4px 24px rgba(217, 45, 32, .06);
  
  .header-content {
    display: flex;
    align-items: center;
    gap: 16px;
  }
  
  .header-text {
    h1 {
      margin: 0;
      font-size: 26px;
      font-weight: 700;
      color: #1e293b;
      letter-spacing: -0.5px;
    }
    
    p {
      margin: 6px 0 0;
      font-size: 14px;
      color: #666666;
    }
  }
}

.main-content {
  padding: 0 24px 24px;
  display: flex;
  gap: 24px;
  max-width: none;
}

.sidebar {
  width: 260px;
  flex-shrink: 0;
  position: sticky;
  top: 0;
  align-self: flex-start;
}

@media (max-width: 900px) {
  .main-content {
    flex-direction: column;
  }
  
  .sidebar {
    width: 100%;
    position: static;
  }
}

.ai-generate-container :deep(.input-panel) {
  border-radius: 10px;
  border: 1px solid #f0f0f0;
  background-color: #ffffff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  
  :deep(.el-card__header) {
    padding: 16px 20px;
    border-bottom: 1px solid #f5f5f5;
    background-color: #fafafa;
    border-radius: 10px 10px 0 0;
  }
  
  :deep(.el-card__body) {
    padding: 20px;
  }
}

.ai-generate-container :deep(.result-panel),
.ai-generate-container :deep(.history-panel) {
  border-radius: 10px;
  border: 1px solid #f0f0f0;
  background-color: #ffffff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  margin: 0;
  
  :deep(.el-card__header) {
    padding: 16px 20px;
    border-bottom: 1px solid #f5f5f5;
    background-color: #fafafa;
    border-radius: 10px 10px 0 0;
  }
  
  :deep(.el-card__body) {
    padding: 20px;
  }
}

.ai-generate-container :deep(.el-radio__inner) {
  border-color: #d9d9d9;
  width: 16px;
  height: 16px;
  
  &:checked {
    border-color: #ff4d4f;
    background-color: #ff4d4f;
  }
}

.ai-generate-container :deep(.el-radio__input.is-checked + .el-radio__label) {
  color: #ff4d4f;
}

.ai-generate-container :deep(.el-select .el-input__wrapper) {
  border-radius: 6px;
  border-color: #d9d9d9;
  
  &:hover {
    border-color: #bfbfbf;
  }
  
  &.is-focus {
    box-shadow: 0 0 0 2px rgba(255, 77, 79, 0.1);
    border-color: #ff4d4f;
  }
}

.ai-generate-container :deep(.el-button--primary) {
  --el-button-bg-color: #ff4d4f;
  --el-button-border-color: #ff4d4f;
  --el-button-hover-bg-color: #ff7875;
  --el-button-hover-border-color: #ff7875;
  --el-button-active-bg-color: #d9363e;
  --el-button-active-border-color: #d9363e;
  --el-button-text-color: #ffffff;
  border-radius: 6px;
}

.ai-generate-container :deep(.el-button--default) {
  border-radius: 6px;
  border-color: #f0f0f0;
  
  &:hover {
    border-color: #ff4d4f;
    color: #ff4d4f;
  }
}

.ai-generate-container :deep(.el-tag--primary) {
  --el-tag-bg-color: #fff5f5;
  --el-tag-border-color: #ffe4e4;
  --el-tag-text-color: #ff4d4f;
  border-radius: 4px;
}

.ai-generate-container :deep(.el-tag--success) {
  --el-tag-bg-color: #f0fff4;
  --el-tag-border-color: #c6f6d5;
  --el-tag-text-color: #38a169;
  border-radius: 4px;
}

.ai-generate-container :deep(.el-tag--warning) {
  --el-tag-bg-color: #fffaf0;
  --el-tag-border-color: #feebc8;
  --el-tag-text-color: #d69e2e;
  border-radius: 4px;
}

.ai-generate-container :deep(.el-tag--danger) {
  --el-tag-bg-color: #fff5f5;
  --el-tag-border-color: #ffe4e4;
  --el-tag-text-color: #ff4d4f;
  border-radius: 4px;
}

.ai-generate-container :deep(.el-alert--success) {
  --el-alert-bg-color: #f0fff4;
  --el-alert-border-color: #c6f6d5;
  border-radius: 8px;
}

.ai-generate-container :deep(.el-dialog) {
  border-radius: 10px;
}

.ai-generate-container :deep(.el-dialog__header) {
  padding: 18px 24px;
  border-bottom: 1px solid #f5f5f5;
}

.ai-generate-container :deep(.el-dialog__body) {
  padding: 24px;
}

.ai-generate-container :deep(.el-dialog__footer) {
  padding: 14px 24px;
  border-top: 1px solid #f5f5f5;
}
</style>