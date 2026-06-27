<template>
  <el-drawer
    class="timeline-drawer"
    :model-value="props.modelValue"
    :title="drawerTitle"
    :size="drawerSize"
    append-to-body
    destroy-on-close
    @update:model-value="handleVisibleUpdate"
  >
    <div class="timeline-drawer__content">
      <template v-if="isGenerating">
        <div class="generating-status">
          <div class="generating-spinner">
            <el-icon class="is-loading" :size="40">
              <LoadingIcon />
            </el-icon>
          </div>
          <div class="generating-text">
            <p class="generating-title">正在生成事件脉络</p>
            <p class="generating-desc">AI 正在分析新闻数据，构建时间线...</p>
            <p class="generating-count">已等待 {{ pollCount }} 秒</p>
          </div>
          <div class="generating-progress">
            <el-progress :percentage="progressPercentage" :stroke-width="8" status="success" />
          </div>
          <div class="generating-actions">
            <el-button size="small" @click="handleCancelGenerate">取消</el-button>
          </div>
        </div>
      </template>

      <template v-else-if="loading">
        <el-skeleton :rows="8" animated />
      </template>

      <template v-else-if="errorMessage">
        <el-empty :description="errorMessage">
          <el-button type="primary" @click="handleRetry">重试</el-button>
        </el-empty>
      </template>

      <template v-else-if="timelineData">
        <TimelinePanel :timeline-data="timelineData" :source-news-list="sourceNewsList" />
      </template>

      <template v-else>
        <el-empty description="暂无事件脉络数据" />
      </template>
    </div>
  </el-drawer>
</template>

<script setup lang="ts">
import { computed, ref, watch, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Loading as LoadingIcon } from '@element-plus/icons-vue'
import {
  generateTimeline,
  getTimeline,
  getTimelineTopicNews,
  type TimelineNewsItem,
  type TimelineResponse,
} from '@/api/timeline'
import TimelinePanel from './TimelinePanel.vue'

const props = withDefaults(
  defineProps<{
    modelValue: boolean
    topicId: number | string | null
    topicName?: string
  }>(),
  {
    topicName: '',
  },
)

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
  (e: 'close'): void
}>()

const loading = ref(false)
const isGenerating = ref(false)
const pollCount = ref(0)
const errorMessage = ref('')
const timelineData = ref<TimelineResponse | null>(null)
const sourceNewsList = ref<TimelineNewsItem[]>([])

let pollTimer: ReturnType<typeof setInterval> | null = null
let timeoutTimer: ReturnType<typeof setTimeout> | null = null

const POLL_INTERVAL = 2000
const TIMEOUT_SECONDS = 60

const drawerSize = computed(() => '720px')
const drawerTitle = computed(() => {
  const topicName = props.topicName || timelineData.value?.topic_name || ''
  return topicName ? `事件脉络：${topicName}` : '事件脉络'
})

const progressPercentage = computed(() => {
  const maxSeconds = TIMEOUT_SECONDS
  const current = pollCount.value
  return Math.min(Math.round((current / maxSeconds) * 100), 95)
})

function handleVisibleUpdate(value: boolean) {
  emit('update:modelValue', value)

  if (!value) {
    emit('close')
  }
}

function resetState() {
  loading.value = false
  isGenerating.value = false
  pollCount.value = 0
  errorMessage.value = ''
  timelineData.value = null
  sourceNewsList.value = []
  stopPolling()
}

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
  if (timeoutTimer) {
    clearTimeout(timeoutTimer)
    timeoutTimer = null
  }
}

async function checkGenerationStatus() {
  try {
    const result = await getTimeline(props.topicId!)
    if (result.generate_status !== 'generating') {
      stopPolling()
      isGenerating.value = false
      loading.value = false
      
      if (result.timeline?.length) {
        timelineData.value = {
          ...result,
          topic_id: Number(props.topicId),
          topic_name: result.topic_name || props.topicName || '事件脉络',
        }
      } else {
        errorMessage.value = '事件脉络生成失败，请重试'
      }
    }
  } catch (error) {
    console.error('轮询失败:', error)
  }
}

async function loadTimelineData() {
  if (props.topicId === null || props.topicId === undefined || props.topicId === '') {
    errorMessage.value = '请选择话题后查看事件脉络'
    timelineData.value = null
    sourceNewsList.value = []
    return
  }

  loading.value = true
  errorMessage.value = ''
  isGenerating.value = false
  pollCount.value = 0
  stopPolling()

  try {
    const [topicNewsResult, initialTimelineResult] = await Promise.all([
      getTimelineTopicNews(props.topicId).catch(() => null),
      getTimeline(props.topicId).catch(() => null),
    ])

    sourceNewsList.value = topicNewsResult?.news_items ?? []

    if (initialTimelineResult?.generate_status === 'generating') {
      isGenerating.value = true
      loading.value = false
      startPolling()
      return
    }

    if (initialTimelineResult?.timeline?.length) {
      timelineData.value = {
        ...initialTimelineResult,
        topic_id: Number(props.topicId),
        topic_name:
          initialTimelineResult.topic_name || props.topicName || topicNewsResult?.topic_name || '事件脉络',
      }
      loading.value = false
      return
    }

    try {
      const generateResult = await generateTimeline(props.topicId)
      if (generateResult.generate_status === 'generating') {
        isGenerating.value = true
        loading.value = false
        startPolling()
        return
      }
      if (generateResult.timeline?.length) {
        timelineData.value = {
          ...generateResult,
          topic_id: Number(props.topicId),
          topic_name:
            generateResult.topic_name || props.topicName || topicNewsResult?.topic_name || '事件脉络',
        }
      } else {
        throw new Error('生成结果为空')
      }
    } catch (generateError) {
      console.warn('生成请求失败:', generateError)
      throw new Error('事件脉络生成失败，请稍后重试')
    }
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '事件脉络加载失败，请稍后重试'
    timelineData.value = null
    sourceNewsList.value = []
    loading.value = false
  }
}

function startPolling() {
  stopPolling()
  
  pollTimer = setInterval(() => {
    pollCount.value += POLL_INTERVAL / 1000
    void checkGenerationStatus()
  }, POLL_INTERVAL)
  
  timeoutTimer = setTimeout(() => {
    stopPolling()
    isGenerating.value = false
    loading.value = false
    errorMessage.value = '事件脉络生成超时，请稍后重试'
    ElMessage.error('事件脉络生成超时')
  }, TIMEOUT_SECONDS * 1000)
}

function handleCancelGenerate() {
  stopPolling()
  isGenerating.value = false
  loading.value = false
  errorMessage.value = '已取消事件脉络生成'
}

function handleRetry() {
  void loadTimelineData()
}

watch(
  () => [props.modelValue, props.topicId],
  ([visible]) => {
    if (visible) {
      void loadTimelineData()
      return
    }

    resetState()
  },
  {
    immediate: true,
  },
)

onUnmounted(() => {
  stopPolling()
})
</script>

<style scoped>
.timeline-drawer__content {
  min-height: 100%;
  background: var(--color-bg);
}

.timeline-drawer :deep(.el-drawer__body) {
  background: var(--color-bg);
}

.timeline-drawer :deep(.el-drawer__header) {
  margin-bottom: 0;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--color-border);
}

.generating-status {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  min-height: 400px;
}

.generating-spinner {
  margin-bottom: 24px;
}

.generating-text {
  text-align: center;
  margin-bottom: 24px;
}

.generating-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  margin-bottom: 8px;
}

.generating-desc {
  font-size: 14px;
  color: var(--el-text-color-secondary);
  margin-bottom: 8px;
}

.generating-count {
  font-size: 12px;
  color: var(--el-text-color-placeholder);
}

.generating-progress {
  width: 100%;
  max-width: 300px;
  margin-bottom: 20px;
}

.generating-actions {
  margin-top: 10px;
}

@media (max-width: 768px) {
  .timeline-drawer {
    --el-drawer-width: 100% !important;
  }
}
</style>
