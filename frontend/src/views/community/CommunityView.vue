<template>
  <main class="page-container">
    <div class="community-layout">
      <div class="community-main">
        <el-card class="app-card post-form-card" shadow="never">
          <h2 class="card-title">发帖</h2>
          <el-form :model="postForm" label-width="0">
            <el-input
              v-model="postForm.title"
              placeholder="输入帖子标题"
              class="post-title-input"
            />
            <el-textarea
              v-model="postForm.content"
              placeholder="分享你的想法..."
              :rows="4"
              class="post-content-input"
            />
            <div class="post-tags">
              <el-tag
                v-for="tag in postForm.tags"
                :key="tag"
                closable
                @close="removeTag(tag)"
              >
                {{ tag }}
              </el-tag>
              <el-input
                v-model="newTag"
                placeholder="添加标签"
                class="tag-input"
                @keyup.enter="addTag"
              />
            </div>
            <div class="post-actions">
              <el-button type="primary" @click="submitPost" :loading="submitting">
                发布帖子
              </el-button>
            </div>
          </el-form>
        </el-card>

        <el-card class="app-card" shadow="never">
          <h2 class="card-title">帖子流</h2>
          <div v-if="loadingPosts" class="loading-container">
            <el-spinner />
          </div>
          <div v-else-if="posts.length === 0" class="empty-state">
            <el-empty description="暂无帖子" />
          </div>
          <div v-else class="posts-list">
            <el-card
              v-for="post in posts"
              :key="post.id"
              class="post-card"
              hover
              @click="showPostDetail(post)"
            >
              <div class="post-header">
                <el-avatar :text="post.author.slice(0, 1)" />
                <div class="post-meta">
                  <span class="post-author">{{ post.author }}</span>
                  <span class="post-time">{{ formatTime(post.created_at) }}</span>
                </div>
              </div>
              <h3 class="post-title">{{ post.title }}</h3>
              <p class="post-content">{{ truncateContent(post.content, 100) }}</p>
              <div class="post-tags">
                <el-tag
                  v-for="tag in post.tags"
                  :key="tag"
                  size="small"
                  type="info"
                >
                  {{ tag }}
                </el-tag>
              </div>
              <div class="post-stats">
                <span class="stat-item">
                  <el-icon class="stat-icon"><Search /></el-icon>
                  {{ post.views }}
                </span>
                <span class="stat-item" @click.stop="handleLike(post)">
                  <el-icon :class="['stat-icon', post.liked ? 'liked' : '']"><StarFilled /></el-icon>
                  {{ post.likes }}
                </span>
                <span class="stat-item">
                  <el-icon class="stat-icon"><Message /></el-icon>
                  {{ post.comments }}
                </span>
              </div>
            </el-card>
          </div>
          <el-pagination
            v-if="postTotal > pageSize"
            :current-page="currentPage"
            :page-size="pageSize"
            :total="postTotal"
            layout="prev, pager, next"
            @current-change="loadPosts"
            class="pagination"
          />
        </el-card>
      </div>

      <div class="community-sidebar">
        <el-card class="app-card" shadow="never">
          <h2 class="card-title">
            <el-icon><BarChart3 /></el-icon>
            热搜 Top10
          </h2>
          <div v-if="loadingHotSearch" class="loading-container">
            <el-spinner />
          </div>
          <div v-else class="hot-search-list">
            <div
              v-for="item in hotSearchList"
              :key="item.id"
              class="hot-search-item"
              @click="handleSearch(item.keyword)"
            >
              <span :class="['rank', getRankClass(item.rank)]">{{ item.rank }}</span>
              <span class="keyword">{{ item.keyword }}</span>
              <el-icon :class="['trend', item.trend]">
                <ArrowUp v-if="item.trend === 'up'" />
                <ArrowDown v-else-if="item.trend === 'down'" />
                <Minus v-else />
              </el-icon>
            </div>
          </div>
        </el-card>

        <el-card class="app-card ai-helper-card" shadow="never">
          <h2 class="card-title">
            <el-icon><User /></el-icon>
            AI 新闻助手
          </h2>
          <div class="ai-chat-container">
            <div v-if="aiMessages.length === 0" class="ai-welcome">
              <el-icon class="ai-icon"><StarFilled /></el-icon>
              <p>有什么可以帮助您的？</p>
            </div>
            <div v-else class="ai-messages">
              <div
                v-for="(msg, index) in aiMessages"
                :key="index"
                :class="['ai-message', msg.type]"
              >
                <el-avatar v-if="msg.type === 'user'" :text="'我'" />
                <el-avatar v-else icon="robot" />
                <div class="message-content">{{ msg.content }}</div>
              </div>
            </div>
            <div class="ai-input-area">
              <el-input
                v-model="aiQuestion"
                placeholder="输入您的问题..."
                @keyup.enter="sendAIQuestion"
              />
              <el-button type="primary" @click="sendAIQuestion" :loading="aiLoading">
                <el-icon><Share /></el-icon>
              </el-button>
            </div>
          </div>
        </el-card>
      </div>
    </div>

    <el-dialog v-model="showPostModal" title="帖子详情" width="600px">
      <div v-if="selectedPost" class="post-detail">
        <div class="post-detail-header">
          <el-avatar :text="selectedPost.author.slice(0, 1)" />
          <div class="post-detail-meta">
            <span class="post-detail-author">{{ selectedPost.author }}</span>
            <span class="post-detail-time">{{ formatTime(selectedPost.created_at) }}</span>
          </div>
        </div>
        <h3 class="post-detail-title">{{ selectedPost.title }}</h3>
        <div class="post-detail-content">{{ selectedPost.content }}</div>
        <div class="post-detail-tags">
          <el-tag
            v-for="tag in selectedPost.tags"
            :key="tag"
            size="small"
            type="info"
          >
            {{ tag }}
          </el-tag>
        </div>
        <div class="post-detail-stats">
          <span>{{ selectedPost.views }} 阅读</span>
          <span>{{ selectedPost.likes }} 点赞</span>
          <span>{{ selectedPost.comments }} 评论</span>
        </div>
        <div class="post-detail-actions">
          <el-button @click="handleLike(selectedPost)">
            <el-icon><StarFilled /></el-icon>
            {{ selectedPost.liked ? '取消点赞' : '点赞' }}
          </el-button>
        </div>
      </div>
      <div class="comments-section">
        <h4>评论 ({{ comments.length }})</h4>
        <div v-if="loadingComments" class="loading-container">
          <el-spinner />
        </div>
        <div v-else class="comments-list">
          <div
            v-for="comment in comments"
            :key="comment.id"
            class="comment-item"
          >
            <el-avatar :text="comment.author.slice(0, 1)" />
            <div class="comment-content">
              <span class="comment-author">{{ comment.author }}</span>
              <p>{{ comment.content }}</p>
              <span class="comment-time">{{ formatTime(comment.created_at) }}</span>
            </div>
          </div>
        </div>
        <el-input
          v-model="newComment"
          placeholder="写下你的评论..."
          @keyup.enter="submitComment"
          class="comment-input"
        />
        <div class="comment-actions">
          <el-button type="primary" @click="submitComment">发表评论</el-button>
        </div>
      </div>
    </el-dialog>
  </main>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import {
  Star,
  StarFilled,
  Message,
  Search,
  TrendCharts,
  ArrowUp,
  ArrowDown,
  Minus,
  User,
  Share,
} from '@element-plus/icons-vue'
import {
  getPostList,
  createPost,
  getPostDetail,
  getComments,
  createComment,
  toggleLike,
  getHotSearch,
  aiNewsHelper,
  type CommunityPost,
  type HotSearchItem,
} from '@/api/community'

const postForm = ref({
  title: '',
  content: '',
  tags: [] as string[],
})
const newTag = ref('')
const submitting = ref(false)

const posts = ref<CommunityPost[]>([])
const loadingPosts = ref(false)
const currentPage = ref(1)
const pageSize = ref(10)
const postTotal = ref(0)

const hotSearchList = ref<HotSearchItem[]>([])
const loadingHotSearch = ref(false)

const aiQuestion = ref('')
const aiMessages = ref<{ type: 'user' | 'ai'; content: string }[]>([])
const aiLoading = ref(false)

const showPostModal = ref(false)
const selectedPost = ref<CommunityPost | null>(null)
const comments = ref<any[]>([])
const loadingComments = ref(false)
const newComment = ref('')

function addTag() {
  if (newTag.value && !postForm.value.tags.includes(newTag.value)) {
    postForm.value.tags.push(newTag.value)
    newTag.value = ''
  }
}

function removeTag(tag: string) {
  const index = postForm.value.tags.indexOf(tag)
  if (index > -1) {
    postForm.value.tags.splice(index, 1)
  }
}

async function submitPost() {
  if (!postForm.value.title || !postForm.value.content) {
    return
  }
  submitting.value = true
  try {
    await createPost({
      title: postForm.value.title,
      content: postForm.value.content,
      tags: postForm.value.tags,
    })
    postForm.value = { title: '', content: '', tags: [] }
    await loadPosts(1)
  } finally {
    submitting.value = false
  }
}

async function loadPosts(page = 1) {
  currentPage.value = page
  loadingPosts.value = true
  try {
    const result = await getPostList({ page, page_size: pageSize.value })
    posts.value = result.list.map((p) => ({ ...p, liked: false }))
    postTotal.value = result.total
  } finally {
    loadingPosts.value = false
  }
}

async function handleLike(post: CommunityPost) {
  try {
    const result = await toggleLike(post.id)
    post.likes = result.count
    post.liked = result.liked
  } catch (e) {
    console.error('点赞失败', e)
  }
}

async function loadHotSearch() {
  loadingHotSearch.value = true
  try {
    hotSearchList.value = await getHotSearch({ limit: 10 })
  } finally {
    loadingHotSearch.value = false
  }
}

function handleSearch(keyword: string) {
  console.log('搜索:', keyword)
}

function getRankClass(rank: number) {
  if (rank <= 3) return 'top-three'
  return ''
}

async function sendAIQuestion() {
  if (!aiQuestion.value) return
  aiMessages.value.push({ type: 'user', content: aiQuestion.value })
  const question = aiQuestion.value
  aiQuestion.value = ''
  aiLoading.value = true
  try {
    const result = await aiNewsHelper(question)
    aiMessages.value.push({ type: 'ai', content: result.answer || '暂无回答' })
  } finally {
    aiLoading.value = false
  }
}

async function showPostDetail(post: CommunityPost) {
  selectedPost.value = post
  showPostModal.value = true
  await loadComments(post.id)
}

async function loadComments(postId: number) {
  loadingComments.value = true
  try {
    const result = await getComments(postId)
    comments.value = result.list
  } finally {
    loadingComments.value = false
  }
}

async function submitComment() {
  if (!newComment.value || !selectedPost.value) return
  try {
    await createComment(selectedPost.value.id, { content: newComment.value })
    newComment.value = ''
    await loadComments(selectedPost.value.id)
  } catch (e) {
    console.error('评论失败', e)
  }
}

function formatTime(timeStr: string) {
  const date = new Date(timeStr)
  return date.toLocaleString('zh-CN', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function truncateContent(content: string, maxLength: number) {
  if (content.length <= maxLength) return content
  return content.slice(0, maxLength) + '...'
}

onMounted(() => {
  loadPosts()
  loadHotSearch()
})
</script>

<style scoped>
.page-container {
  padding: 24px;
}

.community-layout {
  display: flex;
  gap: 24px;
}

.community-main {
  flex: 1;
}

.community-sidebar {
  width: 360px;
  flex-shrink: 0;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.post-form-card {
  margin-bottom: 24px;
}

.post-title-input {
  margin-bottom: 12px;
}

.post-content-input {
  margin-bottom: 12px;
}

.post-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 16px;
}

.tag-input {
  width: 120px;
}

.post-actions {
  display: flex;
  justify-content: flex-end;
}

.loading-container {
  display: flex;
  justify-content: center;
  padding: 40px;
}

.empty-state {
  padding: 40px;
}

.posts-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.post-card {
  cursor: pointer;
  transition: all 0.3s;
}

.post-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.post-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.post-meta {
  display: flex;
  flex-direction: column;
}

.post-author {
  font-weight: 500;
}

.post-time {
  font-size: 12px;
  color: #999;
}

.post-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 8px;
}

.post-content {
  color: #666;
  margin-bottom: 12px;
  line-height: 1.6;
}

.post-stats {
  display: flex;
  gap: 24px;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #eee;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 4px;
  cursor: pointer;
  color: #999;
  transition: color 0.3s;
}

.stat-item:hover {
  color: #409eff;
}

.stat-icon.liked {
  color: #f56c6c;
}

.pagination {
  margin-top: 24px;
  display: flex;
  justify-content: center;
}

.hot-search-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.hot-search-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px;
  cursor: pointer;
  border-radius: 4px;
  transition: background-color 0.3s;
}

.hot-search-item:hover {
  background-color: #f5f7fa;
}

.rank {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
  color: #999;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.rank.top-three {
  background-color: #fff2e8;
  color: #ff9800;
}

.rank:nth-child(1) {
  background-color: #fff2e8;
  color: #f56c6c;
}

.keyword {
  flex: 1;
  font-size: 14px;
}

.trend {
  font-size: 12px;
}

.trend.up {
  color: #67c23a;
}

.trend.down {
  color: #f56c6c;
}

.trend.stable {
  color: #999;
}

.ai-helper-card {
  margin-top: 24px;
}

.ai-chat-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.ai-welcome {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 32px;
  color: #999;
}

.ai-icon {
  font-size: 48px;
  margin-bottom: 12px;
  color: #409eff;
}

.ai-messages {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-height: 200px;
  overflow-y: auto;
}

.ai-message {
  display: flex;
  gap: 8px;
}

.ai-message.user {
  flex-direction: row-reverse;
}

.ai-message.user .message-content {
  background-color: #409eff;
  color: #fff;
}

.message-content {
  max-width: 70%;
  padding: 8px 12px;
  border-radius: 8px;
  font-size: 14px;
  line-height: 1.5;
}

.ai-input-area {
  display: flex;
  gap: 8px;
}

.post-detail {
  padding-bottom: 24px;
  border-bottom: 1px solid #eee;
  margin-bottom: 24px;
}

.post-detail-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.post-detail-meta {
  display: flex;
  flex-direction: column;
}

.post-detail-author {
  font-weight: 600;
}

.post-detail-time {
  font-size: 12px;
  color: #999;
}

.post-detail-title {
  font-size: 20px;
  font-weight: 600;
  margin-bottom: 16px;
}

.post-detail-content {
  color: #333;
  line-height: 1.8;
  margin-bottom: 16px;
}

.post-detail-tags {
  margin-bottom: 16px;
}

.post-detail-stats {
  display: flex;
  gap: 24px;
  margin-bottom: 16px;
  color: #999;
}

.post-detail-actions {
  margin-bottom: 16px;
}

.comments-section {
  padding-bottom: 16px;
}

.comments-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-bottom: 16px;
}

.comment-item {
  display: flex;
  gap: 12px;
}

.comment-content {
  flex: 1;
}

.comment-author {
  font-weight: 500;
  margin-right: 8px;
}

.comment-time {
  font-size: 12px;
  color: #999;
}

.comment-input {
  margin-bottom: 12px;
}

.comment-actions {
  display: flex;
  justify-content: flex-end;
}

@media (max-width: 768px) {
  .community-layout {
    flex-direction: column;
  }

  .community-sidebar {
    width: 100%;
  }
}
</style>