/**
 * 首页新闻流状态缓存 Store。
 *
 * 解决问题：用户从详情页返回首页时，推荐列表因重新请求接口而变化。
 * 通过 Pinia 运行时缓存首页状态（newsList、分页、模式等），
 * 以 cacheKey 区分不同模式（推荐/分类/搜索/订阅），避免串数据。
 */
import { ref } from 'vue'
import { defineStore } from 'pinia'
import type { NewsItem } from '@/api/news'

export interface HomeFeedCache {
  newsList: NewsItem[]
  page: number
  pageSize: number
  total: number
  isRecommendationFeed: boolean
  recommendationHasMore: boolean
  scrollTop: number
  lastLoadedAt: number
}

export const useHomeFeedStore = defineStore('homeFeed', () => {
  /** 以 cacheKey 为键，每个模式独立缓存 */
  const caches = ref<Record<string, HomeFeedCache>>({})

  function getCache(key: string): HomeFeedCache | null {
    return caches.value[key] ?? null
  }

  function setCache(key: string, cache: HomeFeedCache): void {
    caches.value[key] = { ...cache }
  }

  function removeCache(key: string): void {
    delete caches.value[key]
  }

  /** 用户登出、切换账号或登录状态变化时清空所有缓存，避免串数据 */
  function clearAll(): void {
    caches.value = {}
  }

  return { caches, getCache, setCache, removeCache, clearAll }
})
