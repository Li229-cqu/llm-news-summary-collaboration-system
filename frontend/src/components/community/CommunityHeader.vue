<template>
  <div class="community-header">
    <div class="header-top">
      <h2 class="community-title">
        社区广场
        <el-icon class="title-icon"><Message /></el-icon>
      </h2>
      <div class="header-search-bar">
        <el-input
          v-model="localKeyword"
          placeholder="搜索帖子、话题、新闻事件"
          class="search-input"
          clearable
          @keyup.enter="$emit('search')"
        />
        <el-button type="primary" @click="$emit('search')">搜索</el-button>
        <el-button @click="handleClear">清空</el-button>
      </div>
      <el-button type="primary" class="action-btn" @click="$emit('publish')">
        发布帖子
      </el-button>
    </div>

    <div class="tag-filter-bar">
      <el-tag
        :type="activeTag.length === 0 ? 'primary' : 'info'"
        effect="light"
        class="filter-tag"
        @click="$emit('update:activeTag', [])"
      >
        全部
      </el-tag>
      <el-tag
        v-for="tag in tagOptions"
        :key="tag.name"
        :type="activeTag.includes(tag.name) ? 'primary' : 'info'"
        effect="light"
        class="filter-tag"
        @click="toggleTag(tag.name)"
      >
        {{ tag.name }}
      </el-tag>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Message } from '@element-plus/icons-vue'
import type { TagCount } from '@/api/community'

const props = defineProps<{
  keyword: string
  activeTag: string[]
  tagOptions: TagCount[]
}>()

const emit = defineEmits<{
  (e: 'update:keyword', val: string): void
  (e: 'update:activeTag', val: string[]): void
  (e: 'search'): void
  (e: 'publish'): void
  (e: 'refreshTags'): void
}>()

function toggleTag(tagName: string) {
  const current = [...props.activeTag]
  const idx = current.indexOf(tagName)
  if (idx >= 0) current.splice(idx, 1)
  else current.push(tagName)
  emit('update:activeTag', current)
}

const localKeyword = computed({
  get: () => props.keyword,
  set: (val: string) => emit('update:keyword', val),
})

function handleClear() {
  emit('update:keyword', '')
  emit('search')
}
</script>

<style scoped>
.community-header { margin-bottom: 0; flex-shrink: 0; padding: 12px 32px 0; }
.header-top { display: flex; align-items: center; justify-content: space-between; gap: 16px; }
.community-title { margin: 0; color: #111827; font-size: 20px; font-weight: 800; line-height: 1.3; display: flex; align-items: center; gap: 6px; white-space: nowrap; flex-shrink: 0; }
.title-icon { color: #dc2626; font-size: 16px; }
.community-desc { display: none; }
.action-btn { height: 36px; border-radius: 6px; font-size: 14px; font-weight: 600; flex-shrink: 0; }
.related-btn { display: none; }
.topic-refresh { display: none; }
.header-search-bar { display: flex; align-items: center; gap: 8px; flex: 1; max-width: 520px; margin: 0 auto; justify-content: center; }
.search-input { flex: 1; }
.search-input :deep(.el-input__wrapper) { height: 36px; border-radius: 8px; box-shadow: 0 4px 12px rgba(25, 64, 120, 0.06); }
.tag-filter-bar { display: flex; align-items: center; flex-wrap: wrap; gap: 6px; padding-top: 8px; }
.filter-tag { min-width: 56px; height: 28px; justify-content: center; border-radius: 999px; background: #fff; box-shadow: 0 4px 10px rgba(31, 76, 130, 0.06); cursor: pointer; user-select: none; font-size: 12px; }
@media (max-width: 768px) { .header-top { flex-direction: column; } .header-search-bar { max-width: 100%; } }
</style>
