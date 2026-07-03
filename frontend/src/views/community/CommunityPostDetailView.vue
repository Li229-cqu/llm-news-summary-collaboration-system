<template>
  <main class="post-detail-page">
    <div class="detail-header">
      <el-button text @click="goBack">
        <el-icon><ArrowLeft /></el-icon>
        返回社区
      </el-button>
      <el-breadcrumb separator="/">
        <el-breadcrumb-item :to="{ path: '/community' }">社区广场</el-breadcrumb-item>
        <el-breadcrumb-item>帖子详情</el-breadcrumb-item>
      </el-breadcrumb>
    </div>

    <PostDetailPanel
      :post-id="postId"
      @back="goBack"
      @open-related-news="handleRelatedNews"
    />
  </main>
</template>

<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router'
import PostDetailPanel from '@/components/community/PostDetailPanel.vue'

const route = useRoute()
const router = useRouter()
const { id } = route.params
const postId = id as string

function goBack() { router.push('/community') }
function handleRelatedNews(newsId: number | string) { router.push(`/news/${newsId}`) }
</script>

<style scoped>
.post-detail-page {
  max-width: 800px;
  margin: 0 auto;
  padding: 24px 32px 56px;
  min-height: 100vh;
  background:
    radial-gradient(circle at 18% 10%, rgba(220, 38, 38, 0.08), transparent 28%),
    linear-gradient(180deg, #fef2f2 0%, #fef7f7 100%);
}
.detail-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
}

:root.dark .post-detail-page { background: var(--color-bg); }
</style>
