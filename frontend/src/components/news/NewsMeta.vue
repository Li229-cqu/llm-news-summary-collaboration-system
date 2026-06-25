<template>
  <div class="news-meta">
    <div class="news-meta__row news-meta__row--primary">
      <el-tag v-if="news.category_name" effect="plain" type="primary">{{ news.category_name }}</el-tag>
      <span class="news-meta__item">来源：{{ news.source }}</span>
      <span class="news-meta__item">编辑：{{ news.editor }}</span>
      <span class="news-meta__item">发布时间：{{ news.publish_time }}</span>
    </div>

    <div class="news-meta__row news-meta__row--stats">
      <span class="news-meta__item">阅读 {{ news.view_count }}</span>
      <span class="news-meta__item">评论 {{ news.comment_count }}</span>
      <span class="news-meta__item">点赞 {{ news.like_count }}</span>
      <span class="news-meta__item">收藏 {{ news.favorite_count }}</span>
    </div>

    <div v-if="news.tags?.length" class="news-meta__tags">
      <el-tag v-for="tag in news.tags" :key="tag" size="small" effect="light">
        {{ tag }}
      </el-tag>
    </div>
  </div>
</template>

<script setup lang="ts">
export interface NewsMetaItem {
  category_name: string
  source: string
  editor: string
  publish_time: string
  view_count: number
  like_count: number
  comment_count: number
  favorite_count: number
  tags?: string[]
}

defineProps<{
  news: NewsMetaItem
}>()
</script>

<style scoped>
.news-meta {
  display: grid;
  gap: 14px;
}

.news-meta__row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px 14px;
  align-items: center;
}

.news-meta__row--primary {
  padding-bottom: 8px;
  border-bottom: 1px solid var(--color-border);
}

.news-meta__row--stats {
  color: var(--color-text-secondary);
  font-size: 13px;
}

.news-meta__item {
  color: var(--color-text-secondary);
  font-size: 13px;
}

.news-meta__tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
</style>
