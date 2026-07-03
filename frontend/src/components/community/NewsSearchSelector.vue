<template>
  <div class="news-search-selector">
    <!-- 已选择状态 -->
    <div v-if="selectedNews" class="selected-news-card">
      <div class="selected-news-header">
        <el-icon><Link /></el-icon>
        <span class="selected-label">已关联新闻</span>
        <el-button
          text
          size="small"
          type="danger"
          class="clear-btn"
          @click="handleClear"
        >
          清除关联
        </el-button>
      </div>
      <div class="selected-news-body">
        <span class="selected-news-title">{{ selectedNews.title }}</span>
        <span class="selected-news-source">{{ selectedNews.source }} · {{ formatTime(selectedNews.publish_time) }}</span>
      </div>
    </div>

    <!-- 搜索状态 -->
    <div v-else-if="isSearching" class="search-state">
      <div class="search-inline">
        <el-input
          v-model="keyword"
          placeholder="输入新闻关键词搜索..."
          clearable
          @keyup.enter="doSearch"
        />
        <el-button type="primary" :loading="loading" @click="doSearch">搜索</el-button>
        <el-button @click="handleCancelSearch">取消</el-button>
      </div>

      <div v-if="loading" class="search-loading">
        <el-spinner />
      </div>

      <div v-else-if="keyword && results.length === 0 && hasSearched" class="search-empty">
        <el-empty description="未找到相关新闻" :image-size="60" />
      </div>

      <div v-else-if="results.length > 0" class="search-results">
        <div
          v-for="item in results"
          :key="item.id"
          class="search-result-item"
          @click="handleSelect(item)"
        >
          <div class="result-text">
            <span class="result-title">{{ item.title }}</span>
            <span class="result-summary">{{ item.summary }}</span>
            <span class="result-meta">{{ item.source }} · {{ formatTime(item.publish_time) }}</span>
          </div>
          <div v-if="item.cover_image" class="result-cover">
            <el-image :src="item.cover_image" fit="cover" />
          </div>
        </div>
      </div>

      <div v-else class="search-hint">
        <el-icon><Search /></el-icon>
        <span>输入关键词搜索新闻并关联到帖子</span>
      </div>
    </div>

    <!-- 默认状态 -->
    <div v-else class="search-trigger" @click="isSearching = true">
      <el-icon><Link /></el-icon>
      <span>搜索并关联新闻</span>
      <span class="trigger-desc">关联新闻后，帖子会显示对应新闻来源，方便读者跳转查看原文</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Link, Search } from '@element-plus/icons-vue'
import { searchNews, getNewsList, type NewsItem } from '@/api/news'

const emit = defineEmits<{
  (e: 'select', news: NewsItem): void
  (e: 'clear'): void
}>()

const selectedNews = ref<NewsItem | null>(null)
const isSearching = ref(false)
const keyword = ref('')
const results = ref<NewsItem[]>([])
const loading = ref(false)
const hasSearched = ref(false)

async function doSearch() {
  const kw = keyword.value.trim()
  if (!kw) {
    ElMessage.warning('请输入搜索关键词')
    return
  }
  loading.value = true
  hasSearched.value = true
  try {
    // 同时走关键词搜索 + 按分类名搜索，合并去重
    const [keywordRes, categoryRes] = await Promise.all([
      searchNews({ keyword: kw, page: 1, page_size: 10 }).catch(() => ({ list: [] as NewsItem[] })),
      getNewsList({ category: kw, page: 1, page_size: 10 }).catch(() => ({ list: [] as NewsItem[] })),
    ])
    const map = new Map<number, NewsItem>()
    for (const item of [...(keywordRes.list || []), ...(categoryRes.list || [])]) {
      if (!map.has(item.id)) map.set(item.id, item)
    }
    results.value = Array.from(map.values())
  } catch {
    results.value = []
    ElMessage.error('新闻搜索失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

function handleSelect(item: NewsItem) {
  selectedNews.value = item
  isSearching.value = false
  keyword.value = ''
  results.value = []
  hasSearched.value = false
  emit('select', item)
}

function handleClear() {
  selectedNews.value = null
  emit('clear')
}

function handleCancelSearch() {
  isSearching.value = false
  keyword.value = ''
  results.value = []
  hasSearched.value = false
}

function reset() {
  selectedNews.value = null
  isSearching.value = false
  keyword.value = ''
  results.value = []
  hasSearched.value = false
}

function formatTime(timeStr: string) {
  if (!timeStr) return ''
  const date = new Date(timeStr)
  return date.toLocaleString('zh-CN', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function activate() {
  if (!selectedNews.value) {
    isSearching.value = true
  }
}

defineExpose({ reset, activate })
</script>

<style scoped>
.news-search-selector {
  margin-bottom: 16px;
}

/* ── 默认状态 ── */
.search-trigger {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  border: 1px dashed #c0d4e8;
  border-radius: 8px;
  background: #fef2f2;
  cursor: pointer;
  transition: all 0.2s;
  color: #dc2626;
  font-size: 14px;
  flex-wrap: wrap;
}
.search-trigger:hover {
  border-color: #dc2626;
  background: #fee2e2;
}
.trigger-desc {
  color: var(--color-text-muted);
  font-size: 12px;
  margin-left: auto;
}

/* ── 搜索状态 ── */
.search-state {
  border: 1px solid #f5dfdf;
  border-radius: 8px;
  padding: 12px;
  background: var(--color-bg-hover);
}

.search-inline {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.search-loading {
  display: flex;
  justify-content: center;
  padding: 24px;
}

.search-empty {
  padding: 16px;
}

.search-hint {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 24px;
  color: var(--color-text-muted);
  font-size: 14px;
}

.search-results {
  display: flex;
  flex-direction: column;
  gap: 6px;
  max-height: 240px;
  overflow-y: auto;
}

.search-result-item {
  display: flex;
  gap: 12px;
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.15s;
}
.search-result-item:hover {
  background: #fee2e2;
}

.result-text {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.result-title {
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.result-summary {
  font-size: 12px;
  color: var(--color-text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.result-meta {
  font-size: 11px;
  color: var(--color-text-muted);
}

.result-cover {
  width: 56px;
  height: 42px;
  flex-shrink: 0;
  border-radius: 4px;
  overflow: hidden;
}
.result-cover .el-image {
  width: 100%;
  height: 100%;
}

/* ── 已选择状态 ── */
.selected-news-card {
  border: 1px solid #f5bfbf;
  border-radius: 8px;
  background: #fef2f2;
  padding: 10px 14px;
}

.selected-news-header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 6px;
  color: #dc2626;
  font-size: 13px;
}

.selected-label {
  font-weight: 600;
  flex: 1;
}

.clear-btn {
  font-size: 12px;
}

.selected-news-body {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding-left: 22px;
}

.selected-news-title {
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
}

.selected-news-source {
  font-size: 12px;
  color: var(--color-text-secondary);
}
</style>
