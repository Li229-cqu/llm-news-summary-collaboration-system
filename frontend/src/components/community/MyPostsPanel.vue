<template>
  <div class="my-posts-panel">
    <div v-if="loading" class="loading-area">
      <el-spinner />
    </div>

    <div v-else-if="posts.length === 0" class="empty-area">
      <el-empty description="你还没有发布过帖子" :image-size="80">
        <el-button type="primary" @click="$emit('publish')">去发布第一篇帖子</el-button>
      </el-empty>
    </div>

    <div v-else class="posts-list">
      <PostCard
        v-for="post in mappedCards"
        :key="post.id"
        :post="post"
        @view="handleView"
        @like="handleLike"
        @favorite="handleFavorite"
        @comment="handleView"
        @open-related-news="handleOpenRelatedNews"
      />
      <el-pagination
        v-if="total > pageSize"
        :current-page="currentPage"
        :page-size="pageSize"
        :total="total"
        layout="prev, pager, next"
        @current-change="loadPosts"
        class="pagination"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  getMyCommunityPosts,
  toggleLike,
  toggleFavorite,
  unfavoritePost,
  type MyCommunityPost,
  type CommunityPost,
} from '@/api/community'
import PostCard from '@/components/community/PostCard.vue'

const emit = defineEmits<{
  (e: 'publish'): void
  (e: 'viewPost', postId: number): void
}>()

const posts = ref<MyCommunityPost[]>([])
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)

const mappedCards = computed<CommunityPost[]>(() => {
  return posts.value.map((p) => ({
    id: p.id,
    title: p.title,
    content: p.content,
    author: p.author,
    author_id: p.author_id,
    avatar: p.avatar,
    created_at: p.created_at,
    updated_at: p.updated_at || p.created_at,
    likes: p.like_count ?? p.likes ?? 0,
    comments: p.comment_count ?? p.comments ?? 0,
    views: p.view_count ?? p.views ?? 0,
    tags: p.tags || [],
    liked: p.liked ?? false,
    is_favorited: p.favorited ?? false,
    favorite_count: p.favorite_count ?? 0,
    related_news_id: p.related_news_id,
    related_news_title: p.related_news_title || '',
  }))
})

async function loadPosts(page = 1) {
  currentPage.value = page
  loading.value = true
  try {
    const res = await getMyCommunityPosts({ page, page_size: pageSize.value })
    posts.value = res.list || []
    total.value = res.total
  } catch {
    ElMessage.error('获取我的帖子失败')
  } finally {
    loading.value = false
  }
}

function handleView(post: CommunityPost) {
  emit('viewPost', post.id)
}

async function handleLike(post: CommunityPost) {
  try {
    const result = await toggleLike(post.id)
    post.likes = result.count
    post.liked = result.liked
  } catch {
    console.error('点赞失败')
  }
}

async function handleFavorite(post: CommunityPost, event: Event) {
  event.stopPropagation()
  try {
    if (post.is_favorited) {
      const result = await unfavoritePost(post.id)
      post.is_favorited = false
      post.favorite_count = result.favorite_count
    } else {
      const result = await toggleFavorite(post.id)
      post.is_favorited = result.is_favorited
      post.favorite_count = result.favorite_count
    }
  } catch {
    console.error('收藏操作失败')
  }
}

function handleOpenRelatedNews(post: CommunityPost) {
  emit('viewPost', post.id)
}

onMounted(() => {
  loadPosts(1)
})
</script>

<style scoped>
.my-posts-panel {
  min-height: 300px;
}

.loading-area {
  display: flex;
  justify-content: center;
  padding: 48px;
}

.empty-area {
  padding: 48px;
}

.posts-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.pagination {
  margin-top: 24px;
  display: flex;
  justify-content: center;
}
</style>
