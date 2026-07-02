<template>
  <main class="home-page">
    <!-- 首页版头：现代新闻门户风格 -->
    <section class="home-hero">
      <div class="home-hero__bg">
        <div class="home-hero__orb home-hero__orb--1"></div>
        <div class="home-hero__orb home-hero__orb--2"></div>
        <div class="home-hero__grid"></div>
      </div>
      <!-- 右侧抽象装饰：层叠新闻卡片 -->
      <div class="home-hero__deco" aria-hidden="true">
        <div class="home-hero__deco-card home-hero__deco-card--1"></div>
        <div class="home-hero__deco-card home-hero__deco-card--2"></div>
        <div class="home-hero__deco-card home-hero__deco-card--3"></div>
      </div>
      <div class="home-hero__inner">
        <div class="home-hero__body">
          <p class="home-hero__kicker">NEWS TODAY · 智能新闻聚合</p>
          <h1 class="home-hero__title">今日头版</h1>
          <p class="home-hero__subtitle">智能聚合最新资讯，洞察热点背后的新闻脉络</p>
          <div class="home-hero__tags">
            <span class="home-hero__tag">智能推荐</span>
            <span class="home-hero__tag">实时热点</span>
            <span class="home-hero__tag">深度追踪</span>
            <span class="home-hero__tag">新闻速览</span>
          </div>
        </div>
      </div>
    </section>

    <div class="home-content-layout">
      <section class="home-main">
        <!-- 新闻区：加载态 / 空态 / 内容态 -->
        <section class="news-section">
          <div class="section-header">
            <div>
              <h2 class="section-header__title">{{ sectionTitle }}</h2>
              <p class="section-header__desc">{{ sectionDescription }}</p>
            </div>
            <button
              class="refresh-btn"
              :class="{ 'refresh-btn--spin': loadingNews }"
              :disabled="loadingNews"
              @click="handleRefresh"
            >
              <span class="refresh-btn__icon">↻</span>
              <span>{{ isRecommendationFeed && !activeCategoryId && !searchKeyword && !isSubscriptionTab ? '刷新推荐' : '刷新内容' }}</span>
            </button>
          </div>

          <!-- 骨架屏（首次加载中） -->
          <el-skeleton v-if="loadingNews && !newsList.length" animated :rows="6" />

          <!-- 空态 -->
          <el-empty v-else-if="!loadingNews && !newsList.length" :description="emptyNewsText" />

          <!-- 新闻内容区：焦点 + 次级 + 普通流 -->
          <template v-else>
            <!-- 焦点新闻（有图）：大图 + 信息 -->
            <article
              v-if="featuredNews && featuredHasCover"
              class="featured-news featured-news--with-image"
              @click="goToNews(featuredNews.id)"
            >
              <div class="featured-news__image">
                <img
                  :src="featuredNews.cover_image"
                  :alt="featuredNews.title"
                  @error="($event.target as HTMLImageElement).style.display='none'"
                />
              </div>
              <div class="featured-news__body">
                <h3 class="featured-news__title">{{ featuredNews.title }}</h3>
                <p class="featured-news__summary">{{ featuredNews.summary }}</p>
                <div v-if="featuredNews.recommendation_reason" class="featured-news__reason">
                  {{ featuredNews.recommendation_reason }}
                </div>
                <div class="featured-news__meta">
                  <span v-if="featuredNews.source" class="featured-news__meta-source">{{ featuredNews.source }}</span>
                  <span>{{ featuredNews.publish_time }}</span>
                  <span>阅读 {{ featuredNews.view_count }}</span>
                  <span>评论 {{ featuredNews.comment_count }}</span>
                  <span>点赞 {{ featuredNews.like_count }}</span>
                </div>
              </div>
            </article>

            <!-- 焦点新闻（无图兜底）：纯文字头条卡片 -->
            <article
              v-else-if="featuredNews"
              class="featured-news featured-news--text-only"
              @click="goToNews(featuredNews.id)"
            >
              <div class="featured-news__text-card">
                <span class="featured-news__headline-badge">今日头条</span>
                <h3 class="featured-news__title">{{ featuredNews.title }}</h3>
                <p class="featured-news__summary">{{ featuredNews.summary }}</p>
                <div v-if="featuredNews.recommendation_reason" class="featured-news__reason">
                  {{ featuredNews.recommendation_reason }}
                </div>
                <div class="featured-news__meta">
                  <span v-if="featuredNews.source" class="featured-news__meta-source">{{ featuredNews.source }}</span>
                  <span>{{ featuredNews.publish_time }}</span>
                  <span>阅读 {{ featuredNews.view_count }}</span>
                  <span>评论 {{ featuredNews.comment_count }}</span>
                  <span>点赞 {{ featuredNews.like_count }}</span>
                </div>
              </div>
            </article>

            <!-- 次级新闻（剩余列表前 2 条）：不显示顶部分类标签 -->
            <div v-if="secondaryNews.length" class="secondary-news">
              <article
                v-for="item in secondaryNews"
                :key="item.id"
                class="secondary-news__card"
                :class="{ 'secondary-news__card--text-only': !hasCoverImage(item) }"
                @click="goToNews(item.id)"
              >
                <div v-if="hasCoverImage(item)" class="secondary-news__image">
                  <img
                    :src="item.cover_image"
                    :alt="item.title"
                    @error="($event.target as HTMLImageElement).style.display='none'"
                  />
                </div>
                <div class="secondary-news__body">
                  <h3 class="secondary-news__title">{{ item.title }}</h3>
                  <div class="secondary-news__meta">
                    <span v-if="item.source" class="secondary-news__meta-source">{{ item.source }}</span>
                    <span>{{ item.publish_time }}</span>
                    <span>{{ item.view_count }} 阅读</span>
                  </div>
                </div>
              </article>
            </div>

            <!-- 普通新闻流（剩余列表第 3 条起），首页精简模式 -->
            <NewsList
              v-if="normalNews.length"
              :list="normalNews"
              :loading="false"
              empty-text=""
              compact-home
            />

            <!-- 加载更多 -->
            <div v-if="hasMoreNews" class="load-more">
              <button
                class="load-more-btn"
                :disabled="loadingNews || !hasMoreNews"
                @click="handleLoadMore"
              >
                <span v-if="loadingNews" class="load-more-btn__spinner"></span>
                {{ loadingNews ? '加载中...' : loadMoreText }}
              </button>
            </div>
          </template>
        </section>
      </section>

      <aside class="home-aside">
        <el-card class="aside-card" shadow="never">
          <NewsHotList :list="hotNewsList" :loading="loadingHot" />
        </el-card>
      </aside>
    </div>
  </main>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  getHotNews,
  getNewsList,
  getSubscribedNews,
  searchNews,
  type HotNewsItem,
  type NewsItem,
} from '@/api/news'
import { getRecommendations } from '@/api/profile'
import { useUserStore } from '@/stores/user'
import { useHomeFeedStore } from '@/stores/homeFeed'
import NewsList from '@/components/news/NewsList.vue'
import NewsHotList from '@/components/news/NewsHotList.vue'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const feedStore = useHomeFeedStore()

const newsList = ref<NewsItem[]>([])
const hotNewsList = ref<HotNewsItem[]>([])
const loadingNews = ref(false)
const loadingHot = ref(false)
const isRecommendationFeed = ref(false)
const recommendationHasMore = ref(false)
const page = ref(1)
const pageSize = ref(6)
const total = ref(0)

const activeCategoryId = computed(() => String(route.query.category_id ?? '').trim())
const activeTab = computed(() => String(route.query.tab ?? '').trim())
const isSubscriptionTab = computed(() => activeTab.value === 'subscription')
const searchKeyword = computed(() => String(route.query.keyword ?? '').trim())

/** 根据当前模式生成缓存键，区分推荐/分类/搜索/订阅/默认，防止不同模式数据互相覆盖 */
const feedCacheKey = computed(() => {
  const userId = userStore.userInfo?.id ?? 'anon'
  if (searchKeyword.value) return `search:${searchKeyword.value}`
  if (isSubscriptionTab.value) return `sub:${userId}`
  if (activeCategoryId.value) return `cat:${activeCategoryId.value}`
  return userStore.isLoggedIn ? `recommend:${userId}` : 'default'
})

const hasMoreNews = computed(() => {
  if (isRecommendationFeed.value && !activeCategoryId.value && !searchKeyword.value && !isSubscriptionTab.value) {
    return recommendationHasMore.value
  }

  return newsList.value.length < total.value
})
const sectionTitle = computed(() => {
  if (searchKeyword.value) {
    return `全站搜索结果：${searchKeyword.value}`
  }

  if (isSubscriptionTab.value) {
    return '我的订阅'
  }

  return activeCategoryId.value ? '精选新闻' : '为你推荐'
})
const sectionDescription = computed(() => {
  if (searchKeyword.value) {
    return `找到 ${total.value} 条相关新闻`
  }

  if (isSubscriptionTab.value) {
    return total.value > 0
      ? `找到 ${total.value} 条订阅相关新闻`
      : '根据你订阅的新闻分类，为你展示相关内容'
  }

  return activeCategoryId.value ? '实时更新的精选内容，点击即可查看详情' : '基于你的浏览、收藏、点赞推荐'
})
const emptyNewsText = computed(() => {
  if (searchKeyword.value) {
    return '未找到全站相关新闻，请尝试其他关键词'
  }

  if (isSubscriptionTab.value) {
    return userStore.isLoggedIn
      ? '你还没有订阅新闻分类，或订阅分类下暂无新闻'
      : '登录后可查看你的订阅内容'
  }

  return '暂无新闻数据'
})

/** 版头副标题：根据当前模式动态展示一句话说明 */
const heroSubtitle = computed(() => {
  if (searchKeyword.value) return `正在查看与「${searchKeyword.value}」相关的内容`
  if (isSubscriptionTab.value) return '来自你关注分类的最新内容'
  if (activeCategoryId.value) return '当前分类下的精选新闻内容'
  if (userStore.isLoggedIn) return '为你整理最新推荐内容'
  return '聚合全网热点，发现值得关注的新闻脉络'
})

/** 判断新闻是否有可用封面图：排除 null/undefined/空字符串 */
function hasCoverImage(item?: NewsItem | null): boolean {
  if (!item) return false
  return typeof item.cover_image === 'string' && item.cover_image.trim().length > 0
}

/** 焦点新闻：优先选取第一条有封面图的新闻，若全无图则退回到 newsList[0] */
const featuredNews = computed(() => {
  return newsList.value.find((item) => hasCoverImage(item)) || newsList.value[0] || null
})

/** 焦点新闻是否有封面图 */
const featuredHasCover = computed(() => hasCoverImage(featuredNews.value))

/** 剩余新闻：排除焦点新闻后的列表，避免焦点新闻重复出现 */
const remainingNews = computed(() => {
  if (!featuredNews.value) return newsList.value
  return newsList.value.filter((item) => item.id !== featuredNews.value!.id)
})

/** 次级新闻（取剩余列表前 2 条） */
const secondaryNews = computed(() => remainingNews.value.slice(0, 2))
/** 普通新闻流（剩余列表第 3 条起） */
const normalNews = computed(() => remainingNews.value.slice(2))

const loadMoreText = computed(() => {
  if (isRecommendationFeed.value && !activeCategoryId.value && !searchKeyword.value && !isSubscriptionTab.value) {
    return '加载更多推荐'
  }

  if (searchKeyword.value) {
    return '加载更多搜索结果'
  }

  if (isSubscriptionTab.value) {
    return '加载更多订阅新闻'
  }

  return '加载更多新闻'
})

/** 保存当前首页新闻流状态到 Pinia 缓存 */
function saveFeedState(): void {
  feedStore.setCache(feedCacheKey.value, {
    newsList: newsList.value,
    page: page.value,
    pageSize: pageSize.value,
    total: total.value,
    isRecommendationFeed: isRecommendationFeed.value,
    recommendationHasMore: recommendationHasMore.value,
    scrollTop: window.scrollY || document.documentElement.scrollTop,
    lastLoadedAt: Date.now(),
  })
}

/** 尝试从 Pinia 缓存恢复首页新闻流状态，成功返回 true */
function restoreFeedState(): boolean {
  const cache = feedStore.getCache(feedCacheKey.value)
  if (!cache) return false

  newsList.value = cache.newsList
  page.value = cache.page
  pageSize.value = cache.pageSize
  total.value = cache.total
  isRecommendationFeed.value = cache.isRecommendationFeed
  recommendationHasMore.value = cache.recommendationHasMore

  // DOM 渲染完成后恢复滚动位置
  nextTick(() => {
    requestAnimationFrame(() => {
      window.scrollTo(0, cache.scrollTop)
    })
  })

  return true
}

/** 刷新页号：每次手动刷新 +1，用于请求不同页的内容实现换一批效果 */
const refreshOffset = ref(0)

/** 手动刷新：清除缓存 + 换一批内容 */
async function handleRefresh(): Promise<void> {
  refreshOffset.value += 1
  await loadNews({ force: true, reset: true })
}

async function loadNews(
  { force = false, reset = false }: { force?: boolean; reset?: boolean } = {},
) {
  // 分类/搜索/tab 切换时重置页号（不是手动刷新，清零 refreshOffset）
  if (reset && !force) {
    refreshOffset.value = 0
    page.value = 1
  }

  // 手动刷新时重置到第一页并清缓存
  if (force) {
    page.value = 1
    feedStore.removeCache(feedCacheKey.value)
  }

  // 非强制且非重置时，优先从缓存恢复（从详情页返回首页的场景）
  if (!force && !reset) {
    const restored = restoreFeedState()
    if (restored) return
  }

  loadingNews.value = true
  isRecommendationFeed.value = false
  recommendationHasMore.value = false

  // 计算有效页码：手动刷新时翻页获取不同内容
  const effectivePage = page.value + (force ? refreshOffset.value : 0)

  try {
    const keyword = searchKeyword.value || undefined

    if (keyword) {
      const result = await searchNews({
        keyword,
        page: effectivePage,
        page_size: pageSize.value,
      })
      // 如果翻页无数据则回退到第 1 页
      if (force && !result.list.length && effectivePage > 1) {
        refreshOffset.value = 0
        const fallback = await searchNews({ keyword, page: 1, page_size: pageSize.value })
        newsList.value = fallback.list
        total.value = fallback.total
        page.value = fallback.page
        pageSize.value = fallback.page_size
      } else {
        newsList.value = result.list
        total.value = result.total
        page.value = result.page
        pageSize.value = result.page_size
      }
    } else if (isSubscriptionTab.value) {
      if (!userStore.isLoggedIn) {
        newsList.value = []
        total.value = 0
        page.value = 1
        ElMessage.warning('请先登录后查看订阅新闻')
        return
      }

      const result = await getSubscribedNews({
        page: effectivePage,
        page_size: pageSize.value,
      })
      // 翻页无数据回退
      if (force && !result.list.length && effectivePage > 1) {
        refreshOffset.value = 0
        const fallback = await getSubscribedNews({ page: 1, page_size: pageSize.value })
        newsList.value = fallback.list
        total.value = fallback.total
        page.value = fallback.page
        pageSize.value = fallback.page_size
      } else {
        newsList.value = result.list
        total.value = result.total
        page.value = result.page
        pageSize.value = result.page_size
      }
    } else if (!activeCategoryId.value) {
      if (!userStore.isLoggedIn) {
        const result = await getNewsList({
          page: effectivePage,
          page_size: pageSize.value,
        })
        if (force && !result.list.length && effectivePage > 1) {
          refreshOffset.value = 0
          const fallback = await getNewsList({ page: 1, page_size: pageSize.value })
          newsList.value = fallback.list
          total.value = fallback.total
          page.value = fallback.page
          pageSize.value = fallback.page_size
        } else {
          newsList.value = result.list
          total.value = result.total
          page.value = result.page
          pageSize.value = result.page_size
        }
      } else {
        try {
          // 推荐模式刷新：请求更多数据再取不同切片实现换一批
          const maxLimit = 50
          const offset = force ? refreshOffset.value : 0
          const startIdx = offset * pageSize.value
          const endIdx = startIdx + pageSize.value
          const requestLimit = Math.min(endIdx, maxLimit)

          const result = await getRecommendations(requestLimit)
          if (result.list.length) {
            let sliced = result.list.slice(startIdx, endIdx)

            // 仅在目标切片确实为空时才重置（不再基于 total 提前重置）
            if (force && sliced.length === 0 && offset > 0) {
              refreshOffset.value = 0
              const fallback = await getRecommendations(pageSize.value)
              sliced = fallback.list.slice(0, pageSize.value)
            }

            newsList.value = sliced
            total.value = Math.max(result.total, result.list.length)
            page.value = 1
            isRecommendationFeed.value = true
            // 刷新后也保持 hasMore：只要当前切片满一页且未达上限，就还有更多
            recommendationHasMore.value = sliced.length >= pageSize.value && endIdx < maxLimit
          } else {
            refreshOffset.value = 0
            const fallback = await getNewsList({
              page: effectivePage,
              page_size: pageSize.value,
            })
            newsList.value = fallback.list
            total.value = fallback.total
            page.value = fallback.page
            pageSize.value = fallback.page_size
          }
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
        page: effectivePage,
        page_size: pageSize.value,
      })

      if (force && !result.list.length && effectivePage > 1) {
        refreshOffset.value = 0
        const fallback = await getNewsList({ category_id: activeCategoryId.value || undefined, page: 1, page_size: pageSize.value })
        newsList.value = fallback.list
        total.value = fallback.total
        page.value = fallback.page
        pageSize.value = fallback.page_size
      } else {
        newsList.value = result.list
        total.value = result.total
        page.value = result.page
        pageSize.value = result.page_size
      }
    }

    // 请求成功后缓存首页状态，避免从详情页返回时重新请求
    saveFeedState()
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

  const previousPage = page.value
  loadingNews.value = true

  try {
    if (isRecommendationFeed.value && !activeCategoryId.value && !searchKeyword.value && !isSubscriptionTab.value) {
      const currentCount = newsList.value.length
      const nextLimit = Math.min(currentCount + pageSize.value, 50)

      if (nextLimit <= currentCount) {
        recommendationHasMore.value = false
        return
      }

      const result = await getRecommendations(nextLimit)
      const existingIds = new Set(newsList.value.map((item) => item.id))
      const appendedList = result.list.filter((item) => !existingIds.has(item.id))

      newsList.value = [...newsList.value, ...appendedList]
      total.value = Math.max(result.total, newsList.value.length)
      page.value = 1
      recommendationHasMore.value =
        appendedList.length > 0 && result.list.length > currentCount && result.list.length < 50
    } else {
      const nextPage = page.value + 1
      const result = searchKeyword.value
        ? await searchNews({
            keyword: searchKeyword.value,
            page: nextPage,
            page_size: pageSize.value,
          })
        : isSubscriptionTab.value
          ? await getSubscribedNews({
              page: nextPage,
              page_size: pageSize.value,
            })
          : await getNewsList({
              category_id: activeCategoryId.value || undefined,
              page: nextPage,
              page_size: pageSize.value,
            })
      const existingIds = new Set(newsList.value.map((item) => item.id))
      const appendedList = result.list.filter((item) => !existingIds.has(item.id))

      newsList.value = [...newsList.value, ...appendedList]
      total.value = result.total
      page.value = result.page
      pageSize.value = result.page_size
    }

    // 加载更多后同步更新缓存
    saveFeedState()
  } catch (error) {
    page.value = previousPage
    ElMessage.error(error instanceof Error ? error.message : '获取更多新闻失败')
  } finally {
    loadingNews.value = false
  }
}

/** 跳转新闻详情 */
function goToNews(id: number | string): void {
  router.push(`/news/${id}`)
}

onMounted(async () => {
  if (!userStore.userInfo) {
    userStore.loadFromStorage()
  }

  // 优先从 Pinia 缓存恢复新闻列表（从详情页返回首页时不重新请求）
  // 热榜和热点脉络每次都刷新（数据变化频繁，请求量小）
  await loadNews()
  await loadHotNews()
})

watch(
  () => route.query.category_id,
  () => {
    loadNews({ reset: true })
  },
)

watch(
  () => route.query.keyword,
  () => {
    loadNews({ reset: true })
  },
)

watch(
  () => route.query.tab,
  () => {
    loadNews({ reset: true })
  },
)

watch(
  () => route.query.subscription_updated,
  () => {
    loadNews({ reset: true })
  },
)

// 离开首页前保存滚动位置，返回时在 restoreFeedState 中恢复
onBeforeUnmount(() => {
  const scrollTop = window.scrollY || document.documentElement.scrollTop
  const cache = feedStore.getCache(feedCacheKey.value)
  if (cache) {
    cache.scrollTop = scrollTop
    feedStore.setCache(feedCacheKey.value, cache)
  }
})
</script>

<style scoped>
/* ========================================
   首页容器
   ======================================== */
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

/* ========================================
   首页版头 —— 现代新闻门户
   ======================================== */
.home-hero {
  position: relative;
  height: 185px;
  margin-bottom: 24px;
  border-radius: 22px;
  overflow: hidden;
  background: #fff;
  border: 1px solid #f1d4d4;
  box-shadow: 0 4px 24px rgba(217, 45, 32, .06);
}

.home-hero__bg {
  position: absolute;
  inset: 0;
  pointer-events: none;
  overflow: hidden;
}

/* 网格纹理 */
.home-hero__grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(217, 45, 32, .03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(217, 45, 32, .03) 1px, transparent 1px);
  background-size: 32px 32px;
  mask-image: linear-gradient(to bottom, rgba(0,0,0,.08), transparent);
}

.home-hero__orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(72px);
}

.home-hero__orb--1 {
  top: -50px;
  right: 15%;
  width: 200px;
  height: 200px;
  background: rgba(217, 45, 32, .06);
}

.home-hero__orb--2 {
  bottom: -40px;
  left: 50%;
  width: 120px;
  height: 120px;
  background: rgba(217, 45, 32, .04);
}

/* 右侧抽象装饰：层叠新闻卡片 */
.home-hero__deco {
  position: absolute;
  right: 40px;
  top: 50%;
  transform: translateY(-50%);
  width: 200px;
  height: 130px;
  pointer-events: none;
}

.home-hero__deco-card {
  position: absolute;
  border-radius: 12px;
  border: 1px solid rgba(217, 45, 32, .12);
  background: #fff;
}

.home-hero__deco-card--1 {
  top: 0;
  right: 0;
  width: 140px;
  height: 90px;
  box-shadow: 0 4px 16px rgba(0,0,0,.06);
  z-index: 3;
}

.home-hero__deco-card--1::after {
  content: '';
  position: absolute;
  top: 14px;
  left: 14px;
  right: 14px;
  height: 4px;
  border-radius: 2px;
  background: rgba(217, 45, 32, .3);
}

.home-hero__deco-card--2 {
  top: 12px;
  right: 18px;
  width: 120px;
  height: 80px;
  box-shadow: 0 3px 12px rgba(0,0,0,.04);
  transform: rotate(-3deg);
  z-index: 2;
}

.home-hero__deco-card--3 {
  top: 28px;
  right: 36px;
  width: 100px;
  height: 70px;
  box-shadow: 0 2px 8px rgba(0,0,0,.03);
  transform: rotate(-6deg);
  z-index: 1;
}

.home-hero__inner {
  position: relative;
  z-index: 10;
  display: flex;
  align-items: center;
  height: 100%;
  padding: 0 36px;
}

.home-hero__body {
  min-width: 0;
  max-width: 580px;
}

.home-hero__kicker {
  margin: 0;
  color: var(--color-primary);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: .1em;
  text-transform: uppercase;
}

.home-hero__title {
  margin: 6px 0 0;
  color: #1f2937;
  font-size: 34px;
  font-weight: 800;
  letter-spacing: .01em;
  line-height: 1.15;
}

.home-hero__subtitle {
  margin: 10px 0 16px;
  color: #64748b;
  font-size: 14px;
  line-height: 1.6;
}

.home-hero__tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.home-hero__tag {
  padding: 5px 14px;
  border-radius: 999px;
  border: 1px solid rgba(217, 45, 32, .22);
  background: rgba(217, 45, 32, .04);
  color: #b91c1c;
  font-size: 12px;
  font-weight: 500;
  white-space: nowrap;
  transition: background .18s ease, border-color .18s ease;
}

.home-hero__tag:hover {
  background: rgba(217, 45, 32, .1);
  border-color: rgba(217, 45, 32, .35);
}

/* ========================================
   新闻区容器
   ======================================== */
.news-section {
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-card);
  background: var(--color-bg-card);
  padding: 20px;
}

/* ========================================
   标题行 + 胶囊刷新按钮
   ======================================== */
.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 20px;
}

.section-header__title {
  margin: 0;
  color: var(--color-text-primary);
  font-size: 20px;
  font-weight: 700;
}

.section-header__desc {
  margin: 6px 0 0;
  color: var(--color-text-secondary);
  font-size: 13px;
}

/* 胶囊刷新按钮 */
.refresh-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
  padding: 8px 20px;
  border: 1px solid color-mix(in srgb, var(--color-primary) 30%, var(--color-border));
  border-radius: 999px;
  background: color-mix(in srgb, var(--color-primary) 6%, var(--color-bg-card));
  color: var(--color-primary);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition:
    background .2s ease,
    border-color .2s ease,
    box-shadow .2s ease;
  white-space: nowrap;
}

.refresh-btn:hover:not(:disabled) {
  background: color-mix(in srgb, var(--color-primary) 14%, var(--color-bg-card));
  border-color: color-mix(in srgb, var(--color-primary) 55%, var(--color-border));
  box-shadow: 0 2px 10px color-mix(in srgb, var(--color-primary) 18%, transparent);
}

.refresh-btn:disabled {
  opacity: .6;
  cursor: not-allowed;
}

.refresh-btn__icon {
  display: inline-block;
  font-size: 16px;
  line-height: 1;
  transition: transform .6s ease;
}

.refresh-btn--spin .refresh-btn__icon {
  animation: refresh-spin 1s linear infinite;
}

@keyframes refresh-spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* ========================================
   焦点新闻卡片（第 1 条）
   ======================================== */
.featured-news {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-bottom: 20px;
  padding: 16px;
  border: 1px solid var(--color-border);
  border-radius: 18px;
  background: var(--color-bg-card);
  cursor: pointer;
  transition:
    transform .2s ease,
    box-shadow .2s ease,
    border-color .2s ease;
}

.featured-news:hover {
  transform: translateY(-2px);
  border-color: color-mix(in srgb, var(--color-primary) 35%, var(--color-border));
  box-shadow: 0 12px 28px rgba(15, 23, 42, .1);
}

.featured-news__image {
  overflow: hidden;
  border-radius: 12px;
  background: linear-gradient(135deg, color-mix(in srgb, var(--color-primary) 14%, var(--color-bg-card)), var(--color-bg));
  aspect-ratio: 16 / 10;
}

.featured-news__image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform .35s ease;
}

.featured-news:hover .featured-news__image img {
  transform: scale(1.04);
}

.featured-news__image-placeholder {
  width: 100%;
  height: 100%;
  background: linear-gradient(
    135deg,
    color-mix(in srgb, var(--color-primary) 10%, var(--color-bg-card)),
    color-mix(in srgb, var(--color-primary) 3%, var(--color-bg))
  );
}

.featured-news__body {
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-width: 0;
}

.featured-news__topline {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
}

.featured-news__source {
  color: var(--color-text-secondary);
  font-size: 12px;
}

.featured-news__title {
  margin: 0;
  color: var(--color-text-primary);
  font-size: 22px;
  font-weight: 700;
  line-height: 1.4;
}

.featured-news__summary {
  display: -webkit-box;
  overflow: hidden;
  margin: 0;
  color: var(--color-text-secondary);
  font-size: 14px;
  line-height: 1.72;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 3;
}

.featured-news__reason {
  display: flex;
  align-items: center;
  min-height: 28px;
  padding: 4px 10px;
  border-radius: 6px;
  background: color-mix(in srgb, var(--color-primary) 8%, var(--color-bg));
  color: var(--color-primary);
  font-size: 12px;
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.featured-news__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 14px;
  margin-top: auto;
  color: var(--color-text-secondary);
  font-size: 12px;
}

/* 底部来源轻强调 */
.featured-news__meta-source {
  color: var(--color-text-primary);
  font-weight: 500;
}

.featured-news__meta-source::after {
  content: '·';
  margin-left: 6px;
  color: var(--color-text-secondary);
  font-weight: 400;
}

/* --- 无图文字头条卡片 --- */
.featured-news--text-only {
  grid-template-columns: 1fr;
  border-left: 4px solid var(--color-primary);
  background: var(--color-bg-card);
}

.featured-news--text-only:hover {
  border-left-color: #991b1b;
}

.featured-news__text-card {
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-width: 0;
}

/* "今日头条" 角标 */
.featured-news__headline-badge {
  display: inline-block;
  align-self: flex-start;
  padding: 3px 12px;
  border-radius: 999px;
  border: 1px solid color-mix(in srgb, var(--color-primary) 30%, var(--color-border));
  background: color-mix(in srgb, var(--color-primary) 8%, var(--color-bg-card));
  color: var(--color-primary);
  font-size: 12px;
  font-weight: 600;
  letter-spacing: .04em;
}

/* 暗色模式 */
:root.dark .featured-news--text-only {
  background: var(--color-bg-card);
}

:root.dark .featured-news--text-only:hover {
  border-left-color: #f87171;
}

/* ========================================
   次级新闻卡片（第 2-3 条）
   ======================================== */
.secondary-news {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
  margin-bottom: 20px;
}

.secondary-news__card {
  display: grid;
  grid-template-columns: 140px 1fr;
  gap: 12px;
  padding: 12px;
  border: 1px solid var(--color-border);
  border-radius: 14px;
  background: var(--color-bg-card);
  cursor: pointer;
  transition:
    transform .18s ease,
    border-color .18s ease,
    box-shadow .18s ease;
}

.secondary-news__card:hover {
  transform: translateY(-1px);
  border-color: color-mix(in srgb, var(--color-primary) 30%, var(--color-border));
  box-shadow: 0 8px 20px rgba(15, 23, 42, .07);
}

/* 无图次级新闻：单栏文字卡片 */
.secondary-news__card--text-only {
  grid-template-columns: 1fr;
}

.secondary-news__image {
  overflow: hidden;
  border-radius: 10px;
  background: linear-gradient(135deg, color-mix(in srgb, var(--color-primary) 12%, var(--color-bg-card)), var(--color-bg));
  aspect-ratio: 4 / 3;
}

.secondary-news__image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform .3s ease;
}

.secondary-news__card:hover .secondary-news__image img {
  transform: scale(1.05);
}

.secondary-news__image-placeholder {
  width: 100%;
  height: 100%;
  background: linear-gradient(
    135deg,
    color-mix(in srgb, var(--color-primary) 8%, var(--color-bg-card)),
    color-mix(in srgb, var(--color-primary) 2%, var(--color-bg))
  );
}

.secondary-news__body {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-width: 0;
}

.secondary-news__topline {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.secondary-news__title {
  display: -webkit-box;
  overflow: hidden;
  margin: 0;
  color: var(--color-text-primary);
  font-size: 16px;
  font-weight: 600;
  line-height: 1.45;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.secondary-news__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 6px 10px;
  margin-top: auto;
  color: var(--color-text-secondary);
  font-size: 12px;
}

.secondary-news__meta-source {
  color: var(--color-text-primary);
  font-weight: 500;
}

.secondary-news__meta-source::after {
  content: '·';
  margin-left: 4px;
  color: var(--color-text-secondary);
  font-weight: 400;
}

/* ========================================
   加载更多红白按钮
   ======================================== */
.load-more {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}

.load-more-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 28px;
  border: 1px solid color-mix(in srgb, var(--color-primary) 35%, var(--color-border));
  border-radius: 999px;
  background: #fff;
  color: var(--color-primary);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition:
    background .2s ease,
    border-color .2s ease,
    color .2s ease,
    box-shadow .2s ease;
}

.load-more-btn:hover:not(:disabled) {
  background: var(--color-primary);
  color: #fff;
  border-color: var(--color-primary);
  box-shadow: 0 4px 14px color-mix(in srgb, var(--color-primary) 28%, transparent);
}

.load-more-btn:disabled {
  opacity: .55;
  cursor: not-allowed;
}

.load-more-btn__spinner {
  display: inline-block;
  width: 14px;
  height: 14px;
  border: 2px solid color-mix(in srgb, var(--color-primary) 25%, transparent);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: load-more-spin .7s linear infinite;
}

@keyframes load-more-spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* 暗色模式 */
:root.dark .load-more-btn {
  background: transparent;
  border-color: color-mix(in srgb, var(--color-primary) 30%, rgba(255,255,255,.12));
  color: var(--color-primary);
}

:root.dark .load-more-btn:hover:not(:disabled) {
  background: var(--color-primary);
  color: #fff;
}

:root.dark .load-more-btn__spinner {
  border-color: color-mix(in srgb, var(--color-primary) 25%, transparent);
  border-top-color: var(--color-primary);
}

.aside-card {
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-card);
  background: var(--color-bg-card);
}

.aside-card :deep(.el-card__body) {
  padding: 18px;
}

/* ========================================
   暗色模式适配
   ======================================== */
:root.dark .home-hero {
  background: #1f2933;
  border-color: #3b2020;
}

:root.dark .home-hero__title {
  color: #e5e7eb;
}

:root.dark .home-hero__subtitle {
  color: #aeb8c4;
}

:root.dark .home-hero__deco-card {
  background: #2a3542;
  border-color: rgba(248, 113, 113, .1);
}

:root.dark .home-hero__tag {
  border-color: rgba(248, 113, 113, .25);
  background: rgba(248, 113, 113, .08);
  color: #fca5a5;
}

:root.dark .home-hero__tag:hover {
  background: rgba(248, 113, 113, .15);
}

:root.dark .featured-news:hover {
  box-shadow: 0 12px 28px rgba(0, 0, 0, .35);
}

:root.dark .secondary-news__card:hover {
  box-shadow: 0 8px 20px rgba(0, 0, 0, .3);
}

:root.dark .refresh-btn {
  border-color: color-mix(in srgb, var(--color-primary) 25%, rgba(255,255,255,.12));
  background: color-mix(in srgb, var(--color-primary) 10%, rgba(255,255,255,.04));
}

:root.dark .refresh-btn:hover:not(:disabled) {
  background: color-mix(in srgb, var(--color-primary) 20%, rgba(255,255,255,.06));
}

/* ========================================
   响应式
   ======================================== */
@media (max-width: 1200px) {
  .home-content-layout {
    flex-direction: column;
  }

  .home-aside {
    width: 100%;
    flex: none;
  }

  .featured-news {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .home-hero {
    height: auto;
    min-height: 130px;
    padding: 24px 0;
  }

  .home-hero__inner {
    padding: 0 20px;
  }

  .home-hero__deco {
    display: none;
  }

  .home-hero__title {
    font-size: 24px;
  }

  .home-hero__orb {
    display: none;
  }

  .featured-news {
    grid-template-columns: 1fr;
  }

  .secondary-news {
    grid-template-columns: 1fr;
  }

  .secondary-news__card {
    grid-template-columns: 120px 1fr;
  }

  .section-header {
    flex-wrap: wrap;
  }
}
</style>
