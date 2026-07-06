<template>
  <main class="home-page">
    <div class="home-content-layout">
      <section class="home-main">
        <!-- 顶部热搜榜 -->
        <section class="home-hot-section">
          <NewsHotList
            variant="top"
            :list="hotNewsList"
            :loading="loadingHot"
            :title="hotListTitle"
            :subtitle="hotListSubtitle"
          />
        </section>

        <!-- 新闻区：加载态 / 空态 / 内容态 -->
        <section class="news-section">
          <div class="section-header">
            <div>
              <h2 class="section-header__title">{{ sectionTitle }}</h2>
              <p class="section-header__desc">{{ sectionDescription }}</p>
            </div>
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

    </div>
  </main>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  getHotNews,
  getNewsCategories,
  getNewsList,
  getSubscribedNews,
  searchNews,
  type HotNewsItem,
  type NewsCategory,
  type NewsItem,
} from '@/api/news'
import { getRecommendations } from '@/api/profile'
import { useUserStore } from '@/stores/user'
import { useHomeFeedStore } from '@/stores/homeFeed'
import NewsList from '@/components/news/NewsList.vue'
import NewsHotList from '@/components/news/NewsHotList.vue'
import { displayCategoryName } from '@/utils/displayText'

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
const pageSize = ref(35)
const loadMoreSize = 34
const total = ref(0)

/** 分类列表缓存，用于热搜榜标题计算 */
const categories = ref<NewsCategory[]>([])

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

/** 当前分类名称，用于热搜榜标题 */
const currentCategoryName = computed(() => {
  if (!activeCategoryId.value || searchKeyword.value) return ''
  const cat = categories.value.find((c) => String(c.id) === activeCategoryId.value)
  return displayCategoryName(cat?.name)
})

/** 顶部热搜榜标题 */
const hotListTitle = computed(() => {
  if (currentCategoryName.value) return `${currentCategoryName.value}热搜`
  return '今日热搜'
})

/** 顶部热搜榜副标题 */
const hotListSubtitle = computed(() => {
  if (currentCategoryName.value) return `${currentCategoryName.value}分类 · 热门排行`
  return '实时热点 · 两列速览'
})

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

/** 延迟恢复滚动位置：等待页面内容渲染到足够高度后再滚动 */
function restoreScrollPosition(targetY: number): void {
  if (!targetY || targetY <= 0) return

  const maxAttempts = 8
  let attempts = 0

  const tryRestore = () => {
    attempts += 1
    const scrollHeight = Math.max(document.documentElement.scrollHeight, document.body.scrollHeight)
    const canScroll = scrollHeight - window.innerHeight >= targetY - 20

    if (canScroll || attempts >= maxAttempts) {
      window.scrollTo({ top: targetY, behavior: 'auto' })
      // 二次确认，防止图片加载把位置顶回去
      setTimeout(() => {
        if (Math.abs(window.scrollY - targetY) > 80) {
          window.scrollTo({ top: targetY, behavior: 'auto' })
        }
      }, 200)
      return
    }
    setTimeout(tryRestore, 80)
  }

  nextTick(() => {
    requestAnimationFrame(() => {
      setTimeout(tryRestore, 80)
    })
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

  restoreScrollPosition(cache.scrollTop)
  return true
}

/** 手动刷新：清除缓存 + 换一批内容 */
async function loadNews(
  { force = false, reset = false }: { force?: boolean; reset?: boolean } = {},
) {
  // 分类/搜索/tab 切换时重置到第一页
  if (reset) {
    page.value = 1
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
  const effectivePage = page.value

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
        const fallback =await searchNews({ keyword, page: 1, page_size: pageSize.value })
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
        const fallback =await getSubscribedNews({ page: 1, page_size: pageSize.value })
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
          // 推荐模式：请求 pageSize 条推荐新闻
          const result = await getRecommendations(pageSize.value)
          if (result.list.length) {
            newsList.value = result.list
            total.value = Math.max(result.total, result.list.length)
            page.value = 1
            isRecommendationFeed.value = true
            recommendationHasMore.value = result.list.length >= pageSize.value
          } else {
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
        const fallback =await getNewsList({ category_id: activeCategoryId.value || undefined, page: 1, page_size: pageSize.value })
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

/** 请求序列号，防止快速切换分类时旧请求覆盖新请求 */
let hotNewsRequestSeq = 0

async function loadHotNews(categoryId?: number | string) {
  const seq = ++hotNewsRequestSeq
  loadingHot.value = true

  try {
    const result = await getHotNews({
      limit: 10,
      category_id: categoryId || undefined,
    })
    // 忽略过期的请求结果
    if (seq !== hotNewsRequestSeq) return
    hotNewsList.value = result
  } catch (error) {
    if (seq !== hotNewsRequestSeq) return
    hotNewsList.value = []
    ElMessage.error(error instanceof Error ? error.message : '获取热榜失败')
  } finally {
    if (seq === hotNewsRequestSeq) {
      loadingHot.value = false
    }
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
      const nextLimit = Math.min(currentCount + loadMoreSize, 200)

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
        appendedList.length > 0 && result.list.length > currentCount && result.list.length < 100
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

  // 加载分类列表用于热搜榜标题
  getNewsCategories().then((data) => {
    categories.value = data
  }).catch(() => {
    // 分类加载失败不影响主流程
  })

  // 优先从 Pinia 缓存恢复新闻列表（从详情页返回首页时不重新请求）
  // 热榜和热点脉络每次都刷新（数据变化频繁，请求量小）
  await loadNews()
  await loadHotNews(activeCategoryId.value || undefined)
})

watch(
  () => route.query.category_id,
  () => {
    loadNews({ reset: true })
    loadHotNews(activeCategoryId.value || undefined)
  },
)

watch(
  () => route.query.keyword,
  () => {
    loadNews({ reset: true })

    const keyword = String(route.query.keyword ?? '').trim()
    if (keyword) {
      // 进入搜索模式 → 全站热搜
      loadHotNews(undefined)
    } else {
      // 清除搜索 → 如果 URL 仍有分类则恢复分类热搜
      loadHotNews(activeCategoryId.value || undefined)
    }
  },
)

watch(
  () => route.query.tab,
  () => {
    loadNews({ reset: true })
    loadHotNews(activeCategoryId.value || undefined)
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
  width: 100%;
}

.home-main {
  width: 100%;
  min-width: 0;
  display: grid;
  gap: 20px;
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
  display: inline-flex;
  align-items: center;
  width: fit-content;
  max-width: 100%;
  padding: 3px 8px;
  border: 1px solid rgba(185, 28, 28, 0.55);
  border-radius: 999px;
  background: transparent;
  color: #b91c1c;
  font-size: 12px;
  line-height: 1.4;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
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
  background: var(--color-bg-card);
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

/* ========================================
   暗色模式适配
   ======================================== */
:root.dark .featured-news:hover {
  box-shadow: 0 12px 28px rgba(0, 0, 0, .35);
}

:root.dark .featured-news__reason {
  border-color: rgba(252, 165, 165, 0.55);
  color: #fca5a5;
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
   顶部热搜区
   ======================================== */
.home-hot-section {
  margin-bottom: 24px;
}

/* ========================================
   响应式
   ======================================== */
@media (max-width: 1200px) {
  .featured-news {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .home-hot-section {
    margin-bottom: 18px;
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
