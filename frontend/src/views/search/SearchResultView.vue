<template>
  <div class="search-page">
    <!-- 搜索栏 -->
    <div class="search-header">
      <div class="search-input-wrap">
        <el-input
          v-model="keyword"
          size="large"
          placeholder="搜索新闻、社区帖子…"
          clearable
          @keyup.enter="doSearch"
          @clear="doSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-button type="primary" size="large" @click="doSearch">搜索</el-button>
      </div>
    </div>

    <!-- 结果 -->
    <div v-if="searched" class="search-body">
      <div class="result-summary">
        找到 <strong>{{ totalResults }}</strong> 条结果
        <span v-if="results.news.length">（新闻 {{ results.totalNews }} 条）</span>
        <span v-if="results.posts.length">（帖子 {{ results.totalPosts }} 条）</span>
      </div>

      <!-- 空结果 -->
      <el-empty v-if="totalResults === 0 && !loading" description="未找到相关内容" />

      <!-- 新闻结果 -->
      <div v-if="results.news.length" class="result-section">
        <h3 class="section-title">📰 新闻 ({{ results.news.length }})</h3>
        <div
          v-for="item in results.news" :key="'n' + item.id"
          class="result-card"
          @click="openNews(item.id)"
        >
          <h4 class="result-title">{{ item.title }}</h4>
          <p class="result-content">{{ (item.summary || item.content || '').slice(0, 200) }}</p>
          <div class="result-meta">
            <span>{{ item.source }}</span>
            <span>{{ formatDate(item.publishTime) }}</span>
          </div>
        </div>
      </div>

      <!-- 帖子结果 -->
      <div v-if="results.posts.length" class="result-section">
        <h3 class="section-title">💬 社区帖子 ({{ results.posts.length }})</h3>
        <div
          v-for="item in results.posts" :key="'p' + item.id"
          class="result-card"
          @click="openPost(item.id)"
        >
          <h4 class="result-title">{{ item.title }}</h4>
          <p class="result-content">{{ (item.content || '').slice(0, 200) }}</p>
          <div class="result-meta">
            <span>{{ item.source }}</span>
            <span>{{ formatDate(item.publishTime) }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 初始状态 -->
    <div v-else class="search-body">
      <el-empty description="输入关键词开始搜索" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Search } from '@element-plus/icons-vue'
import { searchAll, type SearchResults } from '@/api/search'

const route = useRoute()
const router = useRouter()

const keyword = ref((route.query.q as string) || '')
const results = ref<SearchResults>({ news: [], posts: [], totalNews: 0, totalPosts: 0 })
const loading = ref(false)
const searched = ref(false)

const totalResults = computed(() => results.value.totalNews + results.value.totalPosts)

function doSearch() {
  const q = keyword.value.trim()
  if (!q) return

  router.replace({ query: { q } })
  loading.value = true
  searched.value = true

  searchAll(q)
    .then((r) => { results.value = r })
    .catch(() => { results.value = { news: [], posts: [], totalNews: 0, totalPosts: 0 } })
    .finally(() => { loading.value = false })
}

function openNews(id: number) {
  router.push(`/news/${id}`)
}

function openPost(id: number) {
  router.push(`/community/posts/${id}`)
}

function formatDate(s: string | null) {
  if (!s) return ''
  return s.slice(0, 10)
}

// 如果 URL 带 q 参数，自动搜索
if (keyword.value) {
  doSearch()
}
</script>

<style scoped>
.search-page { max-width: 900px; margin: 0 auto; padding: 24px 0; }
.search-header { margin-bottom: 24px; }
.search-input-wrap { display: flex; gap: 12px; max-width: 640px; }
.search-input-wrap :deep(.el-input) { flex: 1; }

.search-body { min-height: 300px; }
.result-summary { font-size: 14px; color: var(--color-text-secondary); margin-bottom: 20px; }
.result-summary strong { color: var(--color-primary); }

.result-section { margin-bottom: 32px; }
.section-title { font-size: 17px; font-weight: 600; margin-bottom: 12px; color: var(--color-text-primary); }

.result-card {
  padding: 16px 20px; border: 1px solid var(--color-border); border-radius: 8px;
  margin-bottom: 10px; cursor: pointer; transition: box-shadow .15s, border-color .15s;
}
.result-card:hover { border-color: var(--color-primary); box-shadow: 0 2px 12px rgba(0,0,0,.06); }
.result-title { font-size: 16px; font-weight: 600; margin: 0 0 8px; color: var(--color-text-primary); }
.result-content { font-size: 14px; color: var(--color-text-secondary); line-height: 1.6; margin: 0 0 8px; }
.result-meta { display: flex; gap: 16px; font-size: 12px; color: var(--color-text-muted); }
</style>
