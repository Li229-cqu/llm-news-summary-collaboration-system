<template>
  <main class="home-page">
    <div class="home-content-layout">
      <section class="home-main">
        <el-card class="hero-card" shadow="never">
          <div class="hero-card__inner">
            <div class="hero-card__copy">
              <p class="hero-card__eyebrow">今日推荐</p>
              <h1>基于大语言模型的智能新闻摘要与协同互动系统</h1>
              <p class="hero-card__description">
                聚合优质新闻，为你精选今日要闻，快速浏览重点内容，并进入后续摘要生成流程。
              </p>
              <el-button type="primary" size="large" @click="goToAiGenerate">了解更多</el-button>
            </div>

            <div class="hero-card__visual" aria-hidden="true">
              <div class="hero-card__orb hero-card__orb--large"></div>
              <div class="hero-card__orb hero-card__orb--small"></div>
              <div class="hero-card__panel">
                <span>新闻聚合</span>
                <strong>{{ total }}</strong>
              </div>
            </div>
          </div>
        </el-card>

        <el-card class="featured-section" shadow="never">
          <div class="section-header">
            <div>
              <h2>{{ searchKeyword ? `搜索结果: ${searchKeyword}` : activeCategoryId ? '精选新闻' : '为你推荐' }}</h2>
              <p>{{ searchKeyword ? '找到 ' + total + ' 条相关新闻' : activeCategoryId ? '实时更新的精选内容，点击即可查看详情' : '基于你的浏览、收藏、点赞推荐' }}</p>
            </div>
            <el-button text type="primary" :disabled="!hasMoreNews" @click="handleLoadMore">
              查看更多
            </el-button>
          </div>

          <NewsList
            :list="newsList"
            :loading="loadingNews"
            :empty-text="searchKeyword ? '未找到相关新闻，请尝试其他关键词' : '暂无新闻数据'"
          />

          <div class="load-more">
            <el-button plain type="primary" :loading="loadingNews" :disabled="!hasMoreNews" @click="handleLoadMore">
              查看更多新闻
            </el-button>
          </div>
        </el-card>
      </section>

      <aside class="home-aside">
        <el-card class="aside-card" shadow="never">
          <NewsHotList :list="hotNewsList" :loading="loadingHot" @refresh="loadHotNews" />
        </el-card>

        <el-card class="aside-card" shadow="never">
          <div class="timeline-entry">
            <div class="timeline-entry__header">
              <h3>热点事件脉络</h3>
              <span>从热门话题中查看事件发展过程</span>
            </div>

            <el-skeleton v-if="loadingTimelineTopics" animated :rows="4" />
            <el-empty v-else-if="!timelineTopics.length" description="暂无事件脉络话题" />
            <div v-else class="timeline-entry__list">
              <div v-for="topic in timelineTopics" :key="topic.topic_id" class="timeline-entry__item">
                <div class="timeline-entry__item-main">
                  <div class="timeline-entry__item-title">{{ topic.topic_name }}</div>
                  <div class="timeline-entry__item-meta">
                    <span>热度 {{ topic.heat_score }}</span>
                    <span>{{ topic.news_count }} 篇新闻</span>
                  </div>
                </div>
                <el-button type="primary" link @click="openTimeline(topic)">查看脉络</el-button>
              </div>
            </div>
          </div>
        </el-card>

        <NewsRecommendPanel :recent-items="recentNews" />
      </aside>
    </div>

    <TimelineDrawer
      v-model="timelineDrawerVisible"
      :topic-id="selectedTopicId"
      :topic-name="selectedTopicName"
    />
  </main>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  getHotNews,
  getNewsList,
  type HotNewsItem,
  type NewsItem,
} from '@/api/news'
import { getRecommendations } from '@/api/profile'
import { getTimelineTopics, type TimelineTopic } from '@/api/timeline'
import { useUserStore } from '@/stores/user'
import NewsList from '@/components/news/NewsList.vue'
import NewsHotList from '@/components/news/NewsHotList.vue'
import NewsRecommendPanel from '@/components/news/NewsRecommendPanel.vue'
import TimelineDrawer from '@/components/timeline/TimelineDrawer.vue'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const newsList = ref<NewsItem[]>([])
const hotNewsList = ref<HotNewsItem[]>([])
const timelineTopics = ref<TimelineTopic[]>([])
const loadingNews = ref(false)
const loadingHot = ref(false)
const loadingTimelineTopics = ref(false)
const page = ref(1)
const pageSize = ref(6)
const total = ref(0)

const recentNews = computed(() => newsList.value.slice(0, 3))
const hasMoreNews = computed(() => total.value === 0 || newsList.value.length < total.value)
const activeCategoryId = computed(() => String(route.query.category_id ?? '').trim())
const searchKeyword = computed(() => String(route.query.keyword ?? '').trim())

const timelineDrawerVisible = ref(false)
const selectedTopicId = ref<number | string | null>(null)
const selectedTopicName = ref('')

async function loadNews() {
  loadingNews.value = true

  try {
    const keyword = searchKeyword.value || undefined

    if (!activeCategoryId.value && !keyword) {
      if (!userStore.isLoggedIn) {
        const result = await getNewsList({
          page: page.value,
          page_size: pageSize.value,
        })
        newsList.value = result.list
        total.value = result.total
        page.value = result.page
        pageSize.value = result.page_size
      } else {
        try {
          const result = await getRecommendations(pageSize.value)
          newsList.value = result.list
          total.value = result.total
          page.value = 1
        } catch (recommendError) {
          console.error('推荐接口失败，已切换为最新新闻:', recommendError)
          ElMessage.info('个性化推荐暂时不可用，已为你展示最新新闻')
          const result = await getNewsList({
            page: page.value,
            page_size: pageSize.value,
          })
          newsList.value = result.list
          total.value = result.total
          page.value = result.page
          pageSize.value = result.page_size
        }
      }
    } else {
      const result = await getNewsList({
        category_id: activeCategoryId.value || undefined,
        keyword,
        page: page.value,
        page_size: pageSize.value,
      })

      newsList.value = result.list
      total.value = result.total
      page.value = result.page
      pageSize.value = result.page_size
    }
  } catch (error) {
    newsList.value = []
    total.value = 0
    ElMessage.error(error instanceof Error ? error.message : '获取新闻列表失败')
  } finally {
    loadingNews.value = false
  }
}

async function loadHotNews() {
  loadingHot.value = true

  try {
    hotNewsList.value = await getHotNews({ limit: 10 })
  } catch (error) {
    hotNewsList.value = []
    ElMessage.error(error instanceof Error ? error.message : '获取热榜失败')
  } finally {
    loadingHot.value = false
  }
}

async function loadTimelineTopics() {
  loadingTimelineTopics.value = true

  try {
    const result = await getTimelineTopics()
    timelineTopics.value = result.slice(0, 5)
  } catch (error) {
    timelineTopics.value = []
    ElMessage.error(error instanceof Error ? error.message : '获取事件脉络话题失败')
  } finally {
    loadingTimelineTopics.value = false
  }
}

async function handleLoadMore() {
  if (!hasMoreNews.value) {
    return
  }

  page.value += 1
  loadingNews.value = true

  try {
    const result = await getNewsList({
      category_id: activeCategoryId.value || undefined,
      keyword: searchKeyword.value || undefined,
      page: page.value,
      page_size: pageSize.value,
    })

    newsList.value = [...newsList.value, ...result.list]
    total.value = result.total
    page.value = result.page
    pageSize.value = result.page_size
  } catch (error) {
    page.value = Math.max(1, page.value - 1)
    ElMessage.error(error instanceof Error ? error.message : '获取更多新闻失败')
  } finally {
    loadingNews.value = false
  }
}

function goToAiGenerate() {
  router.push('/ai/title-summary')
}

function openTimeline(topic: TimelineTopic) {
  if (!userStore.isLoggedIn) {
    ElMessage.warning('请先登录后查看事件脉络')
    router.push({
      path: '/login',
      query: { redirect: route.fullPath },
    })
    return
  }

  selectedTopicId.value = topic.topic_id
  selectedTopicName.value = topic.topic_name
  timelineDrawerVisible.value = true
}

onMounted(async () => {
  if (!userStore.userInfo) {
    userStore.loadFromStorage()
  }

  await Promise.all([loadNews(), loadHotNews(), loadTimelineTopics()])
})

watch(
  () => route.query.category_id,
  () => {
    page.value = 1
    loadNews()
  },
)

watch(
  () => route.query.keyword,
  () => {
    page.value = 1
    loadNews()
  },
)
</script>

<style scoped>
.home-page {
  width: 100%;
  box-sizing: border-box;
}

.home-content-layout {
  display: flex;
  align-items: flex-start;
  gap: 20px;
  width: 100%;
}

.home-main {
  flex: 1;
  min-width: 0;
  display: grid;
  gap: 20px;
}

.home-aside {
  width: 320px;
  flex: 0 0 320px;
  display: grid;
  gap: 20px;
  min-width: 0;
}

.hero-card,
.featured-section,
.aside-card {
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-card);
  background: var(--color-bg-card);
}

.hero-card :deep(.el-card__body),
.featured-section :deep(.el-card__body),
.aside-card :deep(.el-card__body) {
  padding: 20px;
}

.hero-card__inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
}

.hero-card__copy {
  min-width: 0;
  max-width: 640px;
}

.hero-card__eyebrow {
  margin: 0 0 8px;
  color: var(--color-primary);
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.hero-card h1 {
  margin: 0;
  color: var(--color-text-primary);
  font-size: 28px;
  line-height: 1.3;
}

.hero-card__description {
  margin: 12px 0 20px;
  color: var(--color-text-secondary);
  font-size: 14px;
  line-height: 1.8;
}

.hero-card__visual {
  position: relative;
  width: 260px;
  height: 180px;
  flex: 0 0 260px;
  overflow: hidden;
  border-radius: 22px;
  background: linear-gradient(
    135deg,
    color-mix(in srgb, var(--color-primary) 10%, var(--color-bg-card)),
    var(--color-primary-soft)
  );
}

.hero-card__orb {
  position: absolute;
  border-radius: 50%;
  background: color-mix(in srgb, var(--color-primary) 22%, white);
}

.hero-card__orb--large {
  top: 20px;
  right: 24px;
  width: 120px;
  height: 120px;
}

.hero-card__orb--small {
  bottom: 18px;
  left: 24px;
  width: 72px;
  height: 72px;
}

.hero-card__panel {
  position: absolute;
  right: 22px;
  bottom: 22px;
  display: grid;
  gap: 6px;
  padding: 14px 16px;
  border: 1px solid color-mix(in srgb, var(--color-primary) 16%, white);
  border-radius: 18px;
  background: rgb(255 255 255 / 78%);
  backdrop-filter: blur(10px);
}

.hero-card__panel span {
  color: var(--color-text-secondary);
  font-size: 12px;
}

.hero-card__panel strong {
  color: var(--color-primary);
  font-size: 28px;
  line-height: 1;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;
}

.section-header h2,
.timeline-entry__header h3,
.home-aside :deep(.news-hot-list__header h3),
.home-aside :deep(.news-recommend-panel__title),
.home-aside :deep(.news-recommend-panel__section-title) {
  margin: 0;
  color: var(--color-text-primary);
}

.section-header h2 {
  font-size: 20px;
}

.section-header p,
.timeline-entry__header span {
  margin: 6px 0 0;
  color: var(--color-text-secondary);
  font-size: 13px;
}

.load-more {
  display: flex;
  justify-content: center;
  margin-top: 16px;
}

.timeline-entry {
  display: grid;
  gap: 14px;
}

.timeline-entry__list {
  display: grid;
  gap: 10px;
}

.timeline-entry__item {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 14px;
  border: 1px solid var(--color-border);
  border-radius: 14px;
  background: var(--color-bg);
}

.timeline-entry__item-main {
  display: grid;
  gap: 6px;
  min-width: 0;
}

.timeline-entry__item-title {
  overflow: hidden;
  color: var(--color-text-primary);
  font-size: 14px;
  font-weight: 600;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.timeline-entry__item-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 6px 10px;
  color: var(--color-text-secondary);
  font-size: 12px;
}

.home-aside :deep(.el-card__body) {
  padding: 18px;
}

@media (max-width: 1200px) {
  .home-content-layout {
    flex-direction: column;
  }

  .home-aside {
    width: 100%;
    flex: none;
  }
}

@media (max-width: 768px) {
  .hero-card__inner {
    flex-direction: column;
    align-items: flex-start;
  }

  .hero-card__visual {
    width: 100%;
    flex: none;
  }

  .timeline-entry__item {
    flex-direction: column;
  }
}
</style>
