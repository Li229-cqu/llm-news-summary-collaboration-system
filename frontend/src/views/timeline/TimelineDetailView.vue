<template>
  <div class="timeline-detail-page">
    <div class="timeline-detail-page__layout">
      <main class="timeline-detail-page__main">
        <!-- 面包屑返回 -->
        <div class="timeline-detail-page__breadcrumb">
          <button class="breadcrumb-back-btn" @click="goBackToList">
            <span class="breadcrumb-arrow">←</span>
            <span>返回事件脉络中心</span>
          </button>
          <el-tag v-if="isAutoTopic" type="success" size="small" style="margin-left:12px">自动生成</el-tag>
          <span v-if="isAutoTopic" style="font-size:12px;color: var(--color-text-muted);margin-left:8px">该事件脉络由系统根据近期新闻自动聚合生成</span>
        </div>

        <!-- 复用 TimelineBriefPanel -->
        <TimelineBriefPanel
          v-if="topicId !== null"
          :key="topicId"
          :topic-id="topicId"
          :topic-name="displayTopicName"
          close-text="返回列表"
          @close="goBackToList"
        />

        <!-- topicId 无效 -->
        <div v-else class="timeline-detail-page__error">
          <div class="error-icon">⚠️</div>
          <p class="error-text">无效的话题 ID</p>
          <el-button size="small" @click="goBackToList">返回事件脉络中心</el-button>
        </div>
      </main>

    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getTimelineTopics, type TimelineTopic } from '@/api/timeline'
import TimelineBriefPanel from '@/components/timeline/TimelineBriefPanel.vue'

const route = useRoute()
const router = useRouter()

// ── topicId ──
const topicId = computed<number | null>(() => {
  const id = Number(route.params.topicId)
  return Number.isFinite(id) && id > 0 ? id : null
})

// ── topicName & sourceType ──
const queryTopicName = computed(() => String(route.query.topicName || ''))
const querySourceType = computed(() => String(route.query.sourceType || 'manual'))
const isAutoTopic = computed(() => querySourceType.value === 'auto')
const fallbackName = ref('')

async function resolveTopicName() {
  if (queryTopicName.value) {
    fallbackName.value = ''
    return
  }
  try {
    const topics: TimelineTopic[] = await getTimelineTopics()
    const found = topics.find((t) => t.topic_id === topicId.value)
    fallbackName.value = found?.topic_name || ''
  } catch {
    fallbackName.value = ''
  }
}

const displayTopicName = computed(() => {
  return queryTopicName.value || fallbackName.value || '事件脉络'
})

// ── 返回 ──
function goBackToList() {
  router.back()
}

onMounted(() => {
  void resolveTopicName()
})
</script>

<style scoped>
/* ========================================
   页面容器
   ======================================== */
.timeline-detail-page {
  width: 100%;
  padding: 24px 0 40px;
}

.timeline-detail-page__layout {
  width: 100%;
}

.timeline-detail-page__main {
  min-width: 0;
  display: grid;
  gap: 16px;
}

/* ========================================
   面包屑
   ======================================== */
.timeline-detail-page__breadcrumb {
  margin-bottom: 0;
}

.breadcrumb-back-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border: 1px solid var(--color-border);
  border-radius: 999px;
  background: var(--color-bg-card);
  color: var(--color-text-secondary);
  font-size: 13px;
  cursor: pointer;
  transition:
    color 0.18s ease,
    border-color 0.18s ease,
    background 0.18s ease;
}

.breadcrumb-back-btn:hover {
  color: var(--color-primary);
  border-color: var(--color-primary);
  background: color-mix(in srgb, var(--color-primary) 5%, var(--color-bg-card));
}

.breadcrumb-arrow {
  font-size: 14px;
  transition: transform 0.2s ease;
}

.breadcrumb-back-btn:hover .breadcrumb-arrow {
  transform: translateX(-2px);
}

/* ========================================
   错误态
   ======================================== */
.timeline-detail-page__error {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 64px 16px;
  text-align: center;
  border: 1px solid var(--color-border);
  border-radius: 14px;
  background: var(--color-bg-card);
}

.error-icon {
  font-size: 36px;
}

.error-text {
  margin: 0;
  color: var(--color-text-secondary);
  font-size: 14px;
}

/* ========================================
   暗色模式
   ======================================== */
:root.dark .breadcrumb-back-btn,
:root.dark .timeline-detail-page__error {
  background: #1f2933;
  border-color: #3b2020;
}

:root.dark .breadcrumb-back-btn {
  border-color: #334150;
  color: #aeb8c4;
}

:root.dark .breadcrumb-back-btn:hover {
  color: #f87171;
  border-color: #f87171;
}

:root.dark .error-text {
  color: var(--color-text-muted);
}

/* ========================================
   响应式
   ======================================== */
@media (max-width: 768px) {
  .timeline-detail-page {
    padding: 12px 0 24px;
  }

  .breadcrumb-back-btn {
    font-size: 12px;
    padding: 5px 12px;
  }
}
</style>
