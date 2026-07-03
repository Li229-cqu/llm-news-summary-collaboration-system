<template>
  <main class="timeline-page">
    <div class="timeline-page__layout">
      <!-- 中间主区：事件脉络主题列表 -->
      <section class="timeline-page__main">
        <!-- 顶部 Hero 卡片 -->
        <section class="timeline-hero">
          <div class="timeline-hero__bg">
            <div class="timeline-hero__orb timeline-hero__orb--1"></div>
            <div class="timeline-hero__orb timeline-hero__orb--2"></div>
            <div class="timeline-hero__grid"></div>
          </div>
          <div class="timeline-hero__deco" aria-hidden="true">
            <div class="timeline-hero__deco-card timeline-hero__deco-card--1"></div>
            <div class="timeline-hero__deco-card timeline-hero__deco-card--2"></div>
            <div class="timeline-hero__deco-card timeline-hero__deco-card--3"></div>
          </div>
          <div class="timeline-hero__inner">
            <div class="timeline-hero__body">
              <p class="timeline-hero__kicker">EVENT TIMELINE · 智能事件追踪</p>
              <h1 class="timeline-hero__title">事件脉络</h1>
              <p class="timeline-hero__subtitle">AI 聚合同一话题下的多篇新闻，提炼事件关键进展</p>
              <div v-if="!loadingTopics && !topicError && topics.length" class="timeline-hero__stats">
                <span>共 <strong>{{ topics.length }}</strong> 个事件话题</span>
                <span class="timeline-hero__stats-sep">·</span>
                <span>可生成脉络 <strong>{{ availableCount }}</strong> 个</span>
              </div>
            </div>
          </div>
        </section>

        <!-- 加载态 -->
        <div v-if="loadingTopics" class="timeline-page__skeleton">
          <div v-for="n in 3" :key="n" class="skeleton-topic">
            <div class="skeleton-line skeleton-line--title"></div>
            <div class="skeleton-line skeleton-line--desc"></div>
            <div class="skeleton-line skeleton-line--meta"></div>
          </div>
        </div>

        <!-- 错误态 -->
        <div v-else-if="topicError" class="timeline-page__error">
          <div class="error-icon">⚠️</div>
          <p class="error-text">{{ topicError }}</p>
          <el-button size="small" @click="loadTopics">重试</el-button>
        </div>

        <!-- 空态 -->
        <div v-else-if="!topics.length" class="timeline-page__empty">
          <el-empty description="暂无事件脉络话题" :image-size="56" />
        </div>

        <!-- 来源筛选 -->
        <div v-if="!loadingTopics && !topicError && topics.length" class="timeline-source-filter">
          <el-radio-group v-model="topicSourceFilter" size="small">
            <el-radio-button value="all">全部 ({{ topics.length }})</el-radio-button>
            <el-radio-button value="auto">自动生成 ({{ topics.filter(t=>(t.source_type||'manual')==='auto').length }})</el-radio-button>
            <el-radio-button value="manual">人工维护 ({{ topics.filter(t=>(t.source_type||'manual')==='manual').length }})</el-radio-button>
          </el-radio-group>
        </div>

        <!-- 主题列表 -->
        <div v-if="!loadingTopics && filteredTopics.length" class="timeline-topics">
          <article
            v-for="topic in filteredTopics"
            :key="topic.topic_id"
            class="timeline-topic-card"
            :class="{ 'timeline-topic-card--disabled': topic.news_count < 2 }"
          >
            <div class="timeline-topic-card__body">
              <h3 class="timeline-topic-card__title">
                {{ topic.topic_name }}
                <el-tag v-if="(topic.source_type||'manual')==='auto'" type="success" size="small" style="margin-left:8px">自动生成</el-tag>
                <el-tag v-else type="info" size="small" style="margin-left:8px">人工维护</el-tag>
              </h3>
              <p v-if="topic.summary" class="timeline-topic-card__summary">{{ topic.summary }}</p>
              <p v-if="(topic.source_type||'manual')==='auto' && topic.auto_generated_at" class="timeline-topic-card__auto-time">
                自动生成于 {{ formatAutoTime(topic.auto_generated_at) }}
              </p>

              <div class="timeline-topic-card__meta">
                <span class="timeline-topic-card__meta-pill">{{ topic.news_count }} 篇新闻</span>
                <span class="timeline-topic-card__meta-pill">热度 {{ topic.heat_score }}</span>
              </div>

              <div v-if="topic.keyword_list?.length" class="timeline-topic-card__keywords">
                <span
                  v-for="(kw, kIdx) in topic.keyword_list.slice(0, 3)"
                  :key="kIdx"
                  class="timeline-topic-card__keyword"
                >#{{ kw }}</span>
              </div>
            </div>

            <div class="timeline-topic-card__action">
              <button
                v-if="topic.news_count >= 2"
                class="timeline-topic-card__action-btn"
                @click="handleViewTopic(topic)"
              >
                <span>查看脉络</span>
                <span class="action-arrow">→</span>
              </button>
              <span v-else class="timeline-topic-card__action-hint">
                相关新闻不足，暂不可生成完整脉络
              </span>
            </div>
          </article>
        </div>

        <!-- 筛选空态 -->
        <div v-else-if="!loadingTopics && !filteredTopics.length" class="timeline-page__empty">
          <el-empty description="该筛选条件下暂无话题" :image-size="48" />
        </div>
      </section>

      <!-- 右侧：热搜榜 -->
    </div>
  </main>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { getTimelineTopics, type TimelineTopic } from '@/api/timeline'

const router = useRouter()

const SCROLL_KEY = 'timeline:list-scroll'

// ── 事件话题 ──
const topics = ref<TimelineTopic[]>([])
const loadingTopics = ref(false)
const topicError = ref('')

const topicSourceFilter = ref<'all' | 'manual' | 'auto'>('all')

const filteredTopics = computed(() => {
  if (topicSourceFilter.value === 'all') return topics.value
  return topics.value.filter((t) => (t.source_type || 'manual') === topicSourceFilter.value)
})

const availableCount = computed(() => topics.value.filter((t) => t.news_count >= 2).length)

/** 格式化时间显示 */
function formatAutoTime(dateStr?: string | null): string {
  if (!dateStr) return ''
  try {
    const d = new Date(dateStr)
    if (isNaN(d.getTime())) return ''
    return d.toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
  } catch { return '' }
}

async function loadTopics() {
  loadingTopics.value = true
  topicError.value = ''
  try {
    const result = await getTimelineTopics()
    topics.value = result
  } catch (error) {
    topics.value = []
    topicError.value = error instanceof Error ? error.message : '事件脉络话题加载失败'
  } finally {
    loadingTopics.value = false
  }
}

function getScrollY(): number {
  return window.scrollY || document.documentElement.scrollTop || document.body.scrollTop || 0
}

function handleViewTopic(topic: TimelineTopic) {
  // 保存滚动位置
  try {
    sessionStorage.setItem(SCROLL_KEY, String(getScrollY()))
  } catch { /* ignore */ }
  router.push({
    name: 'timeline-detail',
    params: { topicId: topic.topic_id },
    query: { topicName: topic.topic_name, sourceType: topic.source_type || 'manual' },
  })
}

/** 恢复滚动位置（重试最多 5 次直到页面高度足够） */
function restoreScroll() {
  try {
    const saved = sessionStorage.getItem(SCROLL_KEY)
    if (!saved) return
    const y = parseInt(saved, 10)
    if (y <= 0) return
    sessionStorage.removeItem(SCROLL_KEY)

    let attempts = 0
    const maxAttempts = 5
    function tryScroll() {
      attempts++
      const maxY = Math.max(
        document.documentElement.scrollHeight - window.innerHeight,
        document.body.scrollHeight - window.innerHeight,
        0,
      )
      if (attempts >= maxAttempts || maxY >= y) {
        // 页面已足够高，或已达最大重试次数
        window.scrollTo({ top: y, behavior: 'auto' })
        document.documentElement.scrollTop = y
      } else {
        // 页面还不够高，等一等再试
        setTimeout(tryScroll, 200)
      }
    }
    nextTick(() => {
      requestAnimationFrame(() => {
        setTimeout(tryScroll, 100)
      })
    })
  } catch { /* ignore */ }
}

onMounted(async () => {
  await loadTopics()
  // 数据加载 + DOM 更新后再恢复滚动
  await nextTick()
  restoreScroll()
})
</script>

<style scoped>
/* ========================================
   页面容器
   ======================================== */
.timeline-page {
  width: 100%;
  padding: 24px 0 40px;
}

.timeline-page__layout {
  width: 100%;
}

.timeline-page__main {
  min-width: 0;
  display: grid;
  gap: 20px;
}

/* ========================================
   顶部 Hero 卡片（仿首页"今日头版"风格）
   ======================================== */
.timeline-hero {
  position: relative;
  height: 175px;
  margin-bottom: 4px;
  border-radius: 22px;
  overflow: hidden;
  background: var(--color-bg-card);
  border: 1px solid #f1d4d4;
  box-shadow: 0 4px 24px rgba(217, 45, 32, 0.06);
}

.timeline-hero__bg {
  position: absolute;
  inset: 0;
  pointer-events: none;
  overflow: hidden;
}

.timeline-hero__grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(217, 45, 32, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(217, 45, 32, 0.03) 1px, transparent 1px);
  background-size: 32px 32px;
  mask-image: linear-gradient(to bottom, rgba(0,0,0,0.08), transparent);
}

.timeline-hero__orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(60px);
}

.timeline-hero__orb--1 {
  top: -30px;
  right: 18%;
  width: 160px;
  height: 160px;
  background: rgba(217, 45, 32, 0.06);
}

.timeline-hero__orb--2 {
  bottom: -30px;
  left: 55%;
  width: 100px;
  height: 100px;
  background: rgba(217, 45, 32, 0.04);
}

/* 右侧抽象装饰卡片 */
.timeline-hero__deco {
  position: absolute;
  right: 36px;
  top: 50%;
  transform: translateY(-50%);
  width: 180px;
  height: 115px;
  pointer-events: none;
}

.timeline-hero__deco-card {
  position: absolute;
  border-radius: 10px;
  border: 1px solid rgba(217, 45, 32, 0.12);
  background: var(--color-bg-card);
}

.timeline-hero__deco-card--1 {
  top: 0;
  right: 0;
  width: 125px;
  height: 78px;
  box-shadow: 0 4px 14px rgba(0,0,0,0.05);
  z-index: 3;
}

.timeline-hero__deco-card--1::after {
  content: '';
  position: absolute;
  top: 12px;
  left: 12px;
  right: 12px;
  height: 4px;
  border-radius: 2px;
  background: rgba(217, 45, 32, 0.3);
}

.timeline-hero__deco-card--2 {
  top: 10px;
  right: 16px;
  width: 108px;
  height: 70px;
  box-shadow: 0 3px 10px rgba(0,0,0,0.04);
  transform: rotate(-3deg);
  z-index: 2;
}

.timeline-hero__deco-card--3 {
  top: 24px;
  right: 32px;
  width: 90px;
  height: 60px;
  box-shadow: 0 2px 6px rgba(0,0,0,0.03);
  transform: rotate(-6deg);
  z-index: 1;
}

.timeline-hero__inner {
  position: relative;
  z-index: 10;
  display: flex;
  align-items: center;
  height: 100%;
  padding: 0 32px;
}

.timeline-hero__body {
  min-width: 0;
  max-width: 520px;
}

.timeline-hero__kicker {
  margin: 0;
  color: var(--color-primary);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

.timeline-hero__title {
  margin: 6px 0 0;
  color: #1f2937;
  font-size: 32px;
  font-weight: 800;
  letter-spacing: 0.01em;
  line-height: 1.15;
}

.timeline-hero__subtitle {
  margin: 8px 0 0;
  color: var(--color-text-secondary);
  font-size: 14px;
  line-height: 1.6;
}

.timeline-hero__stats {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 12px;
  color: var(--color-text-secondary);
  font-size: 13px;
}

.timeline-hero__stats strong {
  color: var(--color-primary);
  font-weight: 700;
}

.timeline-hero__stats-sep {
  color: rgba(217, 45, 32, 0.2);
}

/* ========================================
   骨架屏
   ======================================== */
.timeline-page__skeleton {
  display: grid;
  gap: 12px;
}

.skeleton-topic {
  padding: 20px 24px;
  border: 1px solid var(--color-border);
  border-radius: 14px;
  background: var(--color-bg-card);
}

.skeleton-line {
  height: 14px;
  border-radius: 7px;
  background: var(--el-fill-color);
  margin-bottom: 8px;
}

.skeleton-line--title { width: 45%; height: 18px; }
.skeleton-line--desc  { width: 75%; }
.skeleton-line--meta  { width: 35%; height: 12px; margin-bottom: 0; }

/* ========================================
   错误 / 空态
   ======================================== */
.timeline-page__error,
.timeline-page__empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 48px 16px;
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
   主题列表卡片
   ======================================== */
.timeline-topics {
  display: grid;
  gap: 12px;
}

.timeline-topic-card {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding: 20px 22px;
  border: 1px solid var(--color-border);
  border-radius: 14px;
  background: var(--color-bg-card);
  transition:
    transform 0.2s ease,
    border-color 0.2s ease,
    box-shadow 0.2s ease;
}

.timeline-topic-card:hover:not(.timeline-topic-card--disabled) {
  transform: translateY(-1px);
  border-color: color-mix(in srgb, var(--color-primary) 35%, var(--color-border));
  box-shadow: 0 6px 18px rgba(217, 45, 32, 0.06);
}

.timeline-topic-card--disabled {
  opacity: 0.6;
}

.timeline-topic-card__body {
  display: grid;
  gap: 8px;
  min-width: 0;
  flex: 1;
}

.timeline-topic-card__title {
  margin: 0;
  color: var(--color-text-primary);
  font-size: 16px;
  font-weight: 700;
  line-height: 1.4;
}

.timeline-topic-card:hover:not(.timeline-topic-card--disabled) .timeline-topic-card__title {
  color: var(--color-primary);
}

.timeline-topic-card__summary {
  margin: 0;
  color: var(--color-text-secondary);
  font-size: 13px;
  line-height: 1.65;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.timeline-topic-card__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.timeline-topic-card__meta-pill {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 999px;
  border: 1px solid color-mix(in srgb, var(--color-primary) 18%, var(--color-border));
  background: color-mix(in srgb, var(--color-primary) 5%, var(--color-bg-card));
  color: var(--color-text-secondary);
  font-size: 12px;
  font-weight: 500;
  white-space: nowrap;
}

.timeline-topic-card__keywords {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.timeline-topic-card__keyword {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--color-primary) 6%, transparent);
  border: 1px solid color-mix(in srgb, var(--color-primary) 20%, transparent);
  color: #b91c1c;
  font-size: 11px;
  font-weight: 500;
  white-space: nowrap;
}

/* ── 操作区 ── */
.timeline-topic-card__action {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  padding-top: 2px;
}

.timeline-topic-card__action-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 18px;
  border: 1px solid var(--color-primary);
  border-radius: 999px;
  background: transparent;
  color: var(--color-primary);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
  transition:
    background 0.18s ease,
    color 0.18s ease;
}

.timeline-topic-card__action-btn:hover {
  background: var(--color-primary);
  color: #fff;
}

.action-arrow {
  display: inline-block;
  transition: transform 0.2s ease;
}

.timeline-topic-card__action-btn:hover .action-arrow {
  transform: translateX(3px);
}

.timeline-topic-card__action-hint {
  color: var(--color-text-secondary);
  font-size: 12px;
  font-style: italic;
  white-space: nowrap;
}

/* ========================================
   暗色模式
   ======================================== */
:root.dark .timeline-hero {
  background: #1f2933;
  border-color: #3b2020;
}

:root.dark .timeline-hero__deco-card {
  background: #2a3542;
  border-color: rgba(248, 113, 113, 0.1);
}

:root.dark .timeline-hero__title {
  color: #e5e7eb;
}

:root.dark .timeline-hero__subtitle,
:root.dark .timeline-hero__stats {
  color: #aeb8c4;
}

:root.dark .skeleton-topic,
:root.dark .timeline-topic-card,
:root.dark .timeline-page__error,
:root.dark .timeline-page__empty {
  background: #1f2933;
  border-color: #3b2020;
}

:root.dark .timeline-topic-card {
  border-color: #334150;
}

:root.dark .timeline-topic-card:hover:not(.timeline-topic-card--disabled) {
  border-color: rgba(248, 113, 113, 0.3);
  box-shadow: 0 6px 18px rgba(0, 0, 0, 0.2);
}

:root.dark .timeline-topic-card__title {
  color: #e5e7eb;
}

:root.dark .timeline-topic-card__summary {
  color: var(--color-text-muted);
}

:root.dark .timeline-topic-card__keyword {
  background: rgba(248, 113, 113, 0.1);
  border-color: rgba(248, 113, 113, 0.22);
  color: #fca5a5;
}

:root.dark .timeline-topic-card__meta-pill {
  background: rgba(248, 113, 113, 0.06);
  border-color: rgba(248, 113, 113, 0.18);
  color: #aeb8c4;
}

:root.dark .skeleton-line {
  background: rgba(255, 255, 255, 0.06);
}

:root.dark .timeline-topic-card__action-hint {
  color: #8a94a3;
}

:root.dark .timeline-topic-card--disabled {
  opacity: 0.45;
}

/* ========================================
   响应式
   ======================================== */
@media (max-width: 768px) {
  .timeline-page {
    padding: 12px 0 24px;
  }

  .timeline-hero {
    height: auto;
    min-height: 120px;
    padding: 20px 0;
    border-radius: 18px;
  }

  .timeline-hero__inner {
    padding: 0 18px;
  }

  .timeline-hero__deco {
    display: none;
  }

  .timeline-hero__title {
    font-size: 22px;
  }

  .timeline-hero__stats {
    flex-wrap: wrap;
    font-size: 12px;
  }

  .timeline-topic-card {
    flex-direction: column;
    gap: 12px;
    padding: 16px;
  }

  .timeline-topic-card__action {
    align-self: flex-start;
  }

  .timeline-topic-card__title {
    font-size: 15px;
  }
}
.timeline-source-filter { margin-bottom:16px; display:flex; align-items:center }
.timeline-topic-card__auto-time { margin:0; font-size:12px; color:#94a3b8 }
</style>
