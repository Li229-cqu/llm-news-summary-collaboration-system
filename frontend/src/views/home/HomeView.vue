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
                聚合优质新闻，为你精选今日要闻，帮助快速浏览重点内容，并进入后续摘要生成流程。
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
              <h2>精选新闻</h2>
              <p>实时更新的精选内容，点击即可查看详情</p>
            </div>
            <el-button text type="primary" :disabled="!hasMoreNews" @click="handleLoadMore">查看更多</el-button>
          </div>

          <NewsList :list="newsList" :loading="loadingNews" empty-text="暂无新闻数据" />

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

        <NewsRecommendPanel :recent-items="recentNews" />
      </aside>
    </div>
  </main>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getHotNews, getNewsList, type HotNewsItem, type NewsItem } from '@/api/news'
import NewsList from '@/components/news/NewsList.vue'
import NewsHotList from '@/components/news/NewsHotList.vue'
import NewsRecommendPanel from '@/components/news/NewsRecommendPanel.vue'

const router = useRouter()

const newsList = ref<NewsItem[]>([])
const hotNewsList = ref<HotNewsItem[]>([])
const loadingNews = ref(false)
const loadingHot = ref(false)
const page = ref(1)
const pageSize = ref(6)
const total = ref(0)

const recentNews = computed(() => newsList.value.slice(0, 3))
const hasMoreNews = computed(() => total.value === 0 || newsList.value.length < total.value)

async function loadNews() {
  loadingNews.value = true

  try {
    const result = await getNewsList({
      page: page.value,
      page_size: pageSize.value,
    })

    newsList.value = result.list
    total.value = result.total
    page.value = result.page
    pageSize.value = result.page_size
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

async function handleLoadMore() {
  if (!hasMoreNews.value) {
    return
  }

  page.value += 1
  loadingNews.value = true

  try {
    const result = await getNewsList({
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

onMounted(async () => {
  await Promise.all([loadNews(), loadHotNews()])
})
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
  border-color: var(--color-border);
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
  background: linear-gradient(135deg, color-mix(in srgb, var(--color-primary) 10%, var(--color-bg-card)), var(--color-primary-soft));
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
.home-aside :deep(.news-hot-list__header h3),
.home-aside :deep(.news-recommend-panel__title),
.home-aside :deep(.news-recommend-panel__section-title) {
  margin: 0;
  color: var(--color-text-primary);
}

.section-header h2 {
  font-size: 20px;
}

.section-header p {
  margin: 6px 0 0;
  color: var(--color-text-secondary);
  font-size: 13px;
}

.load-more {
  display: flex;
  justify-content: center;
  margin-top: 16px;
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
}
</style>
