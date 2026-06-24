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
      <template v-if="loading">
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
import { computed, ref, watch } from 'vue'
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
const errorMessage = ref('')
const timelineData = ref<TimelineResponse | null>(null)
const sourceNewsList = ref<TimelineNewsItem[]>([])

const drawerSize = computed(() => '720px')
const drawerTitle = computed(() => {
  const topicName = props.topicName || timelineData.value?.topic_name || ''
  return topicName ? `事件脉络：${topicName}` : '事件脉络'
})

function handleVisibleUpdate(value: boolean) {
  emit('update:modelValue', value)

  if (!value) {
    emit('close')
  }
}

function resetState() {
  loading.value = false
  errorMessage.value = ''
  timelineData.value = null
  sourceNewsList.value = []
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

  try {
    const [topicNewsResult, initialTimelineResult] = await Promise.all([
      getTimelineTopicNews(props.topicId).catch(() => null),
      getTimeline(props.topicId).catch(() => null),
    ])

    let finalTimelineResult = initialTimelineResult

    if (!finalTimelineResult || !finalTimelineResult.timeline?.length) {
      await generateTimeline(props.topicId)
      finalTimelineResult = await getTimeline(props.topicId).catch(() => null)
    }

    if (!finalTimelineResult || !finalTimelineResult.timeline?.length) {
      throw new Error('暂无可展示的事件脉络')
    }

    timelineData.value = {
      ...finalTimelineResult,
      topic_id: Number(props.topicId),
      topic_name:
        finalTimelineResult.topic_name || props.topicName || topicNewsResult?.topic_name || '事件脉络',
    }
    sourceNewsList.value = topicNewsResult?.news_items ?? []
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '事件脉络加载失败，请稍后重试'
    timelineData.value = null
    sourceNewsList.value = []
  } finally {
    loading.value = false
  }
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

@media (max-width: 768px) {
  .timeline-drawer {
    --el-drawer-width: 100% !important;
  }
}
</style>
