<template>
  <main class="community-page">
    <div class="page-header">
      <div class="header-content">
        <h1 class="page-title">
          <span class="title-icon">💬</span>
          社区交流
        </h1>
        <p class="page-subtitle">分享观点，讨论热点，连接思想</p>
      </div>
      <div class="header-stats">
        <div class="stat-box">
          <div class="stat-number">{{ postTotal }}</div>
          <div class="stat-label">帖子总数</div>
        </div>
        <div class="stat-box">
          <div class="stat-number">{{ activeUsers }}</div>
          <div class="stat-label">活跃用户</div>
        </div>
        <div class="stat-box">
          <div class="stat-number">{{ todayPosts }}</div>
          <div class="stat-label">今日新帖</div>
        </div>
      </div>
    </div>

    <div class="community-container">
      <!-- 左侧主内容区 -->
      <div class="main-content">
        <!-- 发帖卡片 -->
        <div class="create-post-card">
          <div class="card-header">
            <div class="header-icon">✍️</div>
            <h2>发布新帖</h2>
          </div>
          <div class="card-body">
            <el-form :model="postForm" class="post-form">
              <div class="form-group">
                <el-input
                  v-model="postForm.title"
                  placeholder="帖子标题"
                  class="title-input"
                  maxlength="100"
                  show-word-limit
                >
                  <template #prefix>
                    <span class="input-icon">📌</span>
                  </template>
                </el-input>
              </div>
              
              <div class="form-group">
                <el-textarea
                  v-model="postForm.content"
                  placeholder="分享你的观点、经验或见解..."
                  :rows="4"
                  class="content-input"
                  maxlength="500"
                  show-word-limit
                />
              </div>

              <div class="tags-section">
                <div class="tags-label">
                  <span class="label-icon">🏷️</span>
                  标签
                </div>
                <div class="tags-container">
                  <el-tag
                    v-for="tag in postForm.tags"
                    :key="tag"
                    closable
                    @close="removeTag(tag)"
                    class="custom-tag"
                  >
                    {{ tag }}
                  </el-tag>
                  <el-input
                    v-model="newTag"
                    placeholder="添加标签"
                    class="tag-input"
                    @keyup.enter="addTag"
                  >
                    <template #suffix>
                      <el-icon class="add-tag-icon" @click="addTag"><Plus /></el-icon>
                    </template>
                  </el-input>
                </div>
              </div>

              <div class="form-actions">
                <el-button 
                  type="primary" 
                  size="large"
                  @click="submitPost" 
                  :loading="submitting"
                  class="publish-btn"
                >
                  <el-icon><Position /></el-icon>
                  发布帖子
                </el-button>
              </div>
            </el-form>
          </div>
        </div>

        <!-- 帖子流 -->
        <div class="posts-section">
          <div class="section-header">
            <div class="header-left">
              <h2 class="section-title">
                <span class="title-icon">🔥</span>
                热门帖子
              </h2>
              <div class="filter-tabs">
                <el-radio-group v-model="filterType" size="small">
                  <el-radio-button label="latest">最新</el-radio-button>
                  <el-radio-button label="hot">热门</el-radio-button>
                  <el-radio-button label="discussed">热议</el-radio-button>
                </el-radio-group>
              </div>
            </div>
          </div>

          <div v-if="loadingPosts" class="loading-state">
            <div class="loading-spinner"></div>
            <p>加载中...</p>
          </div>

          <div v-else-if="posts.length === 0" class="empty-state">
            <div class="empty-icon">📭</div>
            <p>暂无帖子，快来发布第一篇吧！</p>
          </div>

          <div v-else class="posts-grid">
            <div
              v-for="post in posts"
              :key="post.id"
              class="post-item"
              @click="showPostDetail(post)"
            >
              <div class="post-item-header">
                <div class="author-info">
                  <el-avatar 
                    :size="40"
                    :text="post.author.slice(0, 1)"
                    class="author-avatar"
                  />
                  <div class="author-details">
                    <span class="author-name">{{ post.author }}</span>
                    <span class="post-time">{{ formatTime(post.created_at) }}</span>
                  </div>
                </div>
                <div class="post-badges">
                  <el-tag v-if="post.hot" type="danger" effect="dark" size="small">🔥热门</el-tag>
                  <el-tag v-if="post.official" type="success" effect="dark" size="small">官方</el-tag>
                </div>
              </div>

              <div class="post-item-body">
                <h3 class="post-title">{{ post.title }}</h3>
                <p class="post-preview">{{ truncateContent(post.content, 120) }}</p>
                <div class="post-tags">
                  <el-tag
                    v-for="tag in post.tags.slice(0, 3)"
                    :key="tag"
                    size="small"
                    effect="plain"
                    class="topic-tag"
                  >
                    {{ tag }}
                  </el-tag>
                </div>
              </div>

              <div class="post-item-footer">
                <div class="interaction-stats">
                  <div class="stat">
                    <el-icon class="stat-icon"><View /></el-icon>
                    <span class="stat-value">{{ post.views || 0 }}</span>
                  </div>
                  <div class="stat clickable" @click.stop="handleLike(post)">
                    <el-icon :class="['stat-icon', post.liked ? 'active' : '']">
                      <StarFilled v-if="post.liked" />
                      <Star v-else />
                    </el-icon>
                    <span class="stat-value">{{ post.likes || 0 }}</span>
                  </div>
                  <div class="stat">
                    <el-icon class="stat-icon"><ChatDotRound /></el-icon>
                    <span class="stat-value">{{ post.comments || 0 }}</span>
                  </div>
                </div>
              </div>
            </div>
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
        </div>
      </div>

      <!-- 右侧侧边栏 -->
      <div class="sidebar">
        <!-- 热搜榜 -->
        <div class="hot-search-card">
          <div class="card-header">
            <div class="header-icon gradient-icon">📊</div>
            <h2>热搜榜</h2>
            <span class="update-time">实时更新</span>
          </div>
          <div v-if="loadingHotSearch" class="loading-mini">
            <el-spinner />
          </div>
          <div v-else class="hot-search-list">
            <div
              v-for="item in hotSearchList"
              :key="item.id"
              class="hot-item"
              @click="handleSearch(item.keyword)"
            >
              <div :class="['hot-rank', `rank-${item.rank}`]">
                <span class="rank-number">{{ item.rank }}</span>
                <div v-if="item.rank <= 3" class="rank-badge">
                  <span v-if="item.rank === 1">🥇</span>
                  <span v-else-if="item.rank === 2">🥈</span>
                  <span v-else-if="item.rank === 3">🥉</span>
                </div>
              </div>
              <div class="hot-content">
                <span class="hot-keyword">{{ item.keyword }}</span>
                <div class="hot-meta">
                  <el-icon :class="['trend-icon', item.trend]">
                    <ArrowUp v-if="item.trend === 'up'" />
                    <ArrowDown v-else-if="item.trend === 'down'" />
                    <Minus v-else />
                  </el-icon>
                  <el-button 
                    type="primary" 
                    link 
                    size="small"
                    @click.stop="openTimelineForHotSearch(item)"
                    class="timeline-btn"
                  >
                    查看脉络
                  </el-button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- AI助手 -->
        <div class="ai-helper-card">
          <div class="card-header">
            <div class="header-icon gradient-icon purple">🤖</div>
            <h2>AI 新闻助手</h2>
          </div>
          <div class="ai-chat-box">
            <div v-if="aiMessages.length === 0" class="ai-welcome">
              <div class="welcome-icon">✨</div>
              <div class="welcome-text">
                <p class="welcome-title">有什么可以帮助您的？</p>
                <div class="quick-actions">
                  <el-button size="small" round @click="aiQuestion='帮我总结今天的科技新闻'">
                    📰 今日新闻摘要
                  </el-button>
                  <el-button size="small" round @click="aiQuestion='推荐一些热门话题'">
                    🔥 热门话题
                  </el-button>
                </div>
              </div>
            </div>
            <div v-else class="ai-messages">
              <div
                v-for="(msg, index) in aiMessages"
                :key="index"
                :class="['message', msg.type]"
              >
                <el-avatar 
                  v-if="msg.type === 'user'" 
                  :size="32"
                  :text="'我'"
                  class="msg-avatar"
                />
                <div v-else class="ai-avatar-box">
                  <span class="ai-avatar-icon">🤖</span>
                </div>
                <div class="msg-content">{{ msg.content }}</div>
              </div>
            </div>
            <div class="ai-input-box">
              <el-input
                v-model="aiQuestion"
                placeholder="输入问题..."
                @keyup.enter="sendAIQuestion"
                class="ai-input"
              >
                <template #suffix>
                  <el-icon 
                    class="send-icon" 
                    @click="sendAIQuestion"
                    :class="{ active: aiQuestion }"
                  >
                    <Promotion />
                  </el-icon>
                </template>
              </el-input>
            </div>
          </div>
        </div>

        <!-- 活跃用户 -->
        <div class="active-users-card">
          <div class="card-header">
            <div class="header-icon">👥</div>
            <h2>活跃作者</h2>
          </div>
          <div class="users-grid">
            <div v-for="user in activeUsersList" :key="user.id" class="user-item">
              <el-avatar :size="36" :text="user.name.slice(0, 1)" />
              <div class="user-info">
                <span class="user-name">{{ user.name }}</span>
                <span class="user-posts">{{ user.posts }} 帖子</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 帖子详情对话框 -->
    <el-dialog 
      v-model="showPostModal" 
      title=""
      width="700px"
      class="post-detail-dialog"
    >
      <div v-if="selectedPost" class="post-detail-content">
        <div class="detail-header">
          <div class="detail-author">
            <el-avatar :size="48" :text="selectedPost.author.slice(0, 1)" />
            <div class="author-meta">
              <span class="detail-author-name">{{ selectedPost.author }}</span>
              <span class="detail-time">{{ formatTime(selectedPost.created_at) }}</span>
            </div>
          </div>
          <div class="detail-actions-top">
            <el-button 
              :type="selectedPost.liked ? 'danger' : 'default'"
              @click="handleLike(selectedPost)"
              class="like-btn"
            >
              <el-icon><StarFilled v-if="selectedPost.liked" /><Star v-else /></el-icon>
              {{ selectedPost.liked ? '已点赞' : '点赞' }}
            </el-button>
          </div>
        </div>

        <h1 class="detail-title">{{ selectedPost.title }}</h1>
        <div class="detail-body">{{ selectedPost.content }}</div>
        
        <div class="detail-tags">
          <el-tag
            v-for="tag in selectedPost.tags"
            :key="tag"
            effect="plain"
            class="detail-tag"
          >
            {{ tag }}
          </el-tag>
        </div>

        <div class="detail-stats">
          <div class="stat-box">
            <el-icon><View /></el-icon>
            <span>{{ selectedPost.views || 0 }} 阅读</span>
          </div>
          <div class="stat-box">
            <el-icon><StarFilled /></el-icon>
            <span>{{ selectedPost.likes || 0 }} 点赞</span>
          </div>
          <div class="stat-box">
            <el-icon><ChatDotRound /></el-icon>
            <span>{{ selectedPost.comments || 0 }} 评论</span>
          </div>
        </div>

        <!-- 评论区 -->
        <div class="comments-section">
          <h3 class="comments-title">
            <span class="title-icon">💬</span>
            评论 ({{ comments.length }})
          </h3>
          
          <div v-if="loadingComments" class="loading-mini">
            <el-spinner />
          </div>
          
          <div v-else class="comments-list">
            <div
              v-for="comment in comments"
              :key="comment.id"
              class="comment-item"
            >
              <el-avatar :size="32" :text="comment.author.slice(0, 1)" />
              <div class="comment-body">
                <div class="comment-header">
                  <span class="comment-author">{{ comment.author }}</span>
                  <span class="comment-time">{{ formatTime(comment.created_at) }}</span>
                </div>
                <p class="comment-text">{{ comment.content }}</p>
              </div>
            </div>
          </div>

          <div class="comment-input-box">
            <el-input
              v-model="newComment"
              placeholder="发表你的看法..."
              @keyup.enter="submitComment"
              class="comment-input"
            >
              <template #suffix>
                <el-button 
                  type="primary" 
                  size="small"
                  @click="submitComment"
                  class="submit-comment-btn"
                >
                  发送
                </el-button>
              </template>
            </el-input>
          </div>
        </div>
      </div>
    </el-dialog>

    <TimelineDrawer
      v-model="timelineDrawerVisible"
      :topic-id="selectedTopicId"
      :topic-name="selectedTopicName"
    />
  </main>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Star,
  StarFilled,
  ChatDotRound,
  View,
  ArrowUp,
  ArrowDown,
  Minus,
  Plus,
  Position,
  Promotion,
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
import { getTimelineTopics, type TimelineTopic } from '@/api/timeline'
import { useUserStore } from '@/stores/user'
import TimelineDrawer from '@/components/timeline/TimelineDrawer.vue'

const postForm = ref({
  title: '',
  content: '',
  tags: [] as string[],
})
const newTag = ref('')
const submitting = ref(false)
const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const posts = ref<CommunityPost[]>([])
const loadingPosts = ref(false)
const currentPage = ref(1)
const pageSize = ref(10)
const postTotal = ref(0)
const filterType = ref('latest')

const activeUsers = ref(156)
const todayPosts = ref(23)

const activeUsersList = ref([
  { id: 1, name: '科技达人', posts: 45 },
  { id: 2, name: '新闻观察者', posts: 32 },
  { id: 3, name: '数据分析', posts: 28 },
  { id: 4, name: 'AI爱好者', posts: 21 },
])

const hotSearchList = ref<HotSearchItem[]>([])
const loadingHotSearch = ref(false)
const timelineTopics = ref<TimelineTopic[]>([])
const loadingTimelineTopics = ref(false)
const timelineDrawerVisible = ref(false)
const selectedTopicId = ref<number | string | null>(null)
const selectedTopicName = ref('')

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
    ElMessage.warning('请填写标题和内容')
    return
  }
  submitting.value = true
  try {
    await createPost({
      title: postForm.value.title,
      content: postForm.value.content,
      tags: postForm.value.tags,
    })
    ElMessage.success('帖子发布成功！')
    postForm.value = { title: '', content: '', tags: [] }
    await loadPosts(1)
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '发布失败')
  } finally {
    submitting.value = false
  }
}

async function loadPosts(page = 1) {
  currentPage.value = page
  loadingPosts.value = true
  try {
    const result = await getPostList({ page, page_size: pageSize.value })
    posts.value = result.list.map((p) => ({
      ...p,
      liked: Boolean(p.liked ?? (p as { is_liked?: boolean }).is_liked ?? false),
    }))
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
    if (result.liked) {
      ElMessage.success('点赞成功！')
    } else {
      ElMessage.info('取消点赞')
    }
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

async function loadTimelineTopics() {
  loadingTimelineTopics.value = true
  try {
    timelineTopics.value = await getTimelineTopics()
  } catch (error) {
    timelineTopics.value = []
    ElMessage.error(error instanceof Error ? error.message : '获取事件脉络话题失败')
  } finally {
    loadingTimelineTopics.value = false
  }
}

function handleSearch(keyword: string) {
  console.log('搜索:', keyword)
}

function findTimelineTopic(keyword: string) {
  const lowerKeyword = keyword.trim().toLowerCase()

  return (
    timelineTopics.value.find((topic) => {
      const topicName = topic.topic_name.toLowerCase()
      return (
        topicName.includes(lowerKeyword) ||
        topic.keyword_list.some((item) => item.toLowerCase().includes(lowerKeyword))
      )
    }) ?? timelineTopics.value[0] ?? null
  )
}

function openTimelineForHotSearch(item: HotSearchItem) {
  if (!userStore.isLoggedIn) {
    ElMessage.warning('请先登录后查看事件脉络')
    router.push({
      path: '/login',
      query: { redirect: route.fullPath },
    })
    return
  }

  const topic = findTimelineTopic(item.keyword)

  if (!topic) {
    ElMessage.warning('当前暂无可查看的事件脉络')
    return
  }

  selectedTopicId.value = topic.topic_id
  selectedTopicName.value = topic.topic_name
  timelineDrawerVisible.value = true
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
    ElMessage.success('评论发布成功！')
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
  if (!content) return ''
  if (content.length <= maxLength) return content
  return content.slice(0, maxLength) + '...'
}

onMounted(() => {
  if (!userStore.userInfo) {
    userStore.loadFromStorage()
  }

  loadPosts()
  loadHotSearch()
  loadTimelineTopics()
})
</script>

<style scoped>
/* 页面整体布局 */
.community-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #f5f7fa 0%, #e8eef5 100%);
  padding: 0;
}

/* 页面头部 */
.page-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 48px 32px;
  color: white;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 4px 20px rgba(102, 126, 234, 0.3);
}

.header-content {
  flex: 1;
}

.page-title {
  font-size: 32px;
  font-weight: 700;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  gap: 12px;
}

.title-icon {
  font-size: 36px;
}

.page-subtitle {
  font-size: 16px;
  opacity: 0.9;
  font-weight: 300;
}

.header-stats {
  display: flex;
  gap: 32px;
}

.header-stats .stat-box {
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(10px);
  border-radius: 12px;
  padding: 16px 24px;
  text-align: center;
  min-width: 120px;
}

.stat-number {
  font-size: 28px;
  font-weight: 700;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 12px;
  opacity: 0.8;
}

/* 主容器 */
.community-container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 32px;
  display: grid;
  grid-template-columns: 1fr 380px;
  gap: 32px;
}

/* 主内容区 */
.main-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* 侧边栏 */
.sidebar {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* 通用卡片样式 */
.create-post-card,
.posts-section,
.hot-search-card,
.ai-helper-card,
.active-users-card {
  background: white;
  border-radius: 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
}

.card-header {
  padding: 24px 24px 0;
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-icon {
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
}

.gradient-icon.purple {
  background: linear-gradient(135deg, #a855f7 0%, #6366f1 100%);
}

.card-header h2 {
  font-size: 20px;
  font-weight: 600;
  color: #2d3748;
  flex: 1;
}

.update-time {
  font-size: 12px;
  color: #a0aec0;
  background: #f7fafc;
  padding: 4px 8px;
  border-radius: 6px;
}

.card-body {
  padding: 24px;
}

/* 发帖卡片 */
.create-post-card {
  background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
}

.post-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-group {
  width: 100%;
}

.title-input,
.content-input {
  width: 100%;
}

.title-input :deep(.el-input__wrapper) {
  padding: 12px 16px;
  border-radius: 10px;
  border: 2px solid #e2e8f0;
  transition: all 0.3s;
}

.title-input :deep(.el-input__wrapper:focus-within) {
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.input-icon {
  font-size: 16px;
  opacity: 0.6;
}

.content-input :deep(.el-textarea__inner) {
  padding: 16px;
  border-radius: 10px;
  border: 2px solid #e2e8f0;
  font-size: 14px;
  line-height: 1.6;
  transition: all 0.3s;
}

.content-input :deep(.el-textarea__inner:focus) {
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.tags-section {
  background: #f7fafc;
  border-radius: 10px;
  padding: 16px;
}

.tags-label {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  font-size: 14px;
  font-weight: 600;
  color: #4a5568;
}

.label-icon {
  font-size: 18px;
}

.tags-container {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.custom-tag {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  padding: 6px 12px;
}

.tag-input {
  width: 120px;
}

.add-tag-icon {
  cursor: pointer;
  color: #667eea;
  transition: all 0.3s;
}

.add-tag-icon:hover {
  color: #764ba2;
  transform: scale(1.1);
}

.form-actions {
  display: flex;
  justify-content: flex-end;
}

.publish-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  border-radius: 10px;
  padding: 12px 32px;
  font-size: 16px;
  font-weight: 600;
  transition: all 0.3s;
}

.publish-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
}

/* 帖子区域 */
.posts-section {
  padding: 24px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 24px;
}

.section-title {
  font-size: 22px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 10px;
  color: #2d3748;
}

.filter-tabs :deep(.el-radio-button__inner) {
  border-radius: 8px;
  padding: 8px 16px;
}

/* 加载和空状态 */
.loading-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
  color: #718096;
}

.loading-spinner {
  width: 48px;
  height: 48px;
  border: 4px solid #e2e8f0;
  border-top-color: #667eea;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.empty-icon {
  font-size: 64px;
  margin-bottom: 16px;
}

.empty-state p {
  font-size: 16px;
}

/* 帖子网格 */
.posts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 24px;
}

.post-item {
  background: white;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  padding: 20px;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.post-item::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 4px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  opacity: 0;
  transition: opacity 0.3s;
}

.post-item:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
  border-color: transparent;
}

.post-item:hover::before {
  opacity: 1;
}

.post-item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.author-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.author-avatar {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.author-details {
  display: flex;
  flex-direction: column;
}

.author-name {
  font-size: 14px;
  font-weight: 600;
  color: #2d3748;
}

.post-time {
  font-size: 12px;
  color: #a0aec0;
}

.post-badges {
  display: flex;
  gap: 6px;
}

.post-item-body {
  margin-bottom: 16px;
}

.post-title {
  font-size: 18px;
  font-weight: 600;
  color: #2d3748;
  margin-bottom: 12px;
  line-height: 1.4;
}

.post-preview {
  font-size: 14px;
  color: #718096;
  line-height: 1.6;
  margin-bottom: 12px;
}

.post-tags {
  display: flex;
  gap: 6px;
}

.topic-tag {
  border-radius: 6px;
  background: #f7fafc;
  color: #4a5568;
  border: 1px solid #e2e8f0;
}

.post-item-footer {
  border-top: 1px solid #e2e8f0;
  padding-top: 16px;
}

.interaction-stats {
  display: flex;
  gap: 24px;
}

.stat {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #a0aec0;
  font-size: 14px;
  transition: all 0.3s;
}

.stat.clickable {
  cursor: pointer;
}

.stat.clickable:hover {
  color: #667eea;
}

.stat-icon {
  font-size: 16px;
}

.stat-icon.active {
  color: #f56565;
}

.stat-value {
  font-weight: 500;
}

/* 分页 */
.pagination {
  margin-top: 32px;
  display: flex;
  justify-content: center;
}

/* 热搜榜 */
.hot-search-card {
  background: linear-gradient(135deg, #ffffff 0%, #fafbfc 100%);
}

.loading-mini {
  display: flex;
  justify-content: center;
  padding: 24px;
}

.hot-search-list {
  padding: 0 24px 24px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.hot-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: white;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.3s;
  border: 1px solid #f0f0f0;
}

.hot-item:hover {
  background: linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%);
  transform: translateX(4px);
}

.hot-rank {
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f7fafc;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 700;
  color: #718096;
  position: relative;
}

.rank-1 {
  background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
  color: white;
}

.rank-2 {
  background: linear-gradient(135deg, #ffa502 0%, #ff7f50 100%);
  color: white;
}

.rank-3 {
  background: linear-gradient(135deg, #ffd93d 0%, #f9ca24 100%);
  color: white;
}

.rank-badge {
  position: absolute;
  top: -4px;
  right: -4px;
  font-size: 14px;
}

.hot-content {
  flex: 1;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.hot-keyword {
  font-size: 14px;
  font-weight: 500;
  color: #2d3748;
}

.hot-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}

.trend-icon {
  font-size: 14px;
}

.trend-icon.up {
  color: #48bb78;
}

.trend-icon.down {
  color: #f56565;
}

.timeline-btn {
  font-size: 12px;
}

/* AI助手 */
.ai-helper-card {
  background: linear-gradient(135deg, #ffffff 0%, #f8f9ff 100%);
  border: 1px solid rgba(102, 126, 234, 0.1);
}

.ai-chat-box {
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.ai-welcome {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 32px 16px;
  text-align: center;
}

.welcome-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.welcome-title {
  font-size: 16px;
  color: #718096;
  margin-bottom: 16px;
}

.quick-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.quick-actions :deep(.el-button) {
  background: #f7fafc;
  border: 1px solid #e2e8f0;
  color: #4a5568;
  font-size: 12px;
}

.quick-actions :deep(.el-button:hover) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-color: transparent;
}

.ai-messages {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-height: 240px;
  overflow-y: auto;
}

.message {
  display: flex;
  gap: 10px;
  align-items: flex-end;
}

.message.user {
  flex-direction: row-reverse;
}

.msg-avatar {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.ai-avatar-box {
  width: 32px;
  height: 32px;
  background: linear-gradient(135deg, #a855f7 0%, #6366f1 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.ai-avatar-icon {
  font-size: 16px;
}

.msg-content {
  max-width: 70%;
  padding: 10px 14px;
  border-radius: 12px;
  font-size: 14px;
  line-height: 1.5;
  background: #f7fafc;
  color: #2d3748;
}

.message.user .msg-content {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.ai-input-box {
  position: relative;
}

.ai-input :deep(.el-input__wrapper) {
  border-radius: 10px;
  padding: 10px 16px;
  border: 2px solid #e2e8f0;
}

.ai-input :deep(.el-input__wrapper:focus-within) {
  border-color: #667eea;
}

.send-icon {
  font-size: 18px;
  color: #a0aec0;
  cursor: pointer;
  transition: all 0.3s;
}

.send-icon.active {
  color: #667eea;
}

.send-icon:hover {
  color: #764ba2;
  transform: scale(1.1);
}

/* 活跃用户 */
.active-users-card {
  background: white;
}

.users-grid {
  padding: 0 24px 24px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.user-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: #f7fafc;
  border-radius: 10px;
  transition: all 0.3s;
}

.user-item:hover {
  background: #edf2f7;
  transform: translateX(4px);
}

.user-info {
  flex: 1;
}

.user-name {
  font-size: 14px;
  font-weight: 600;
  color: #2d3748;
}

.user-posts {
  font-size: 12px;
  color: #a0aec0;
}

/* 帖子详情对话框 */
.post-detail-dialog :deep(.el-dialog__header) {
  display: none;
}

.post-detail-dialog :deep(.el-dialog__body) {
  padding: 0;
}

.post-detail-content {
  padding: 32px;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding-bottom: 24px;
  border-bottom: 1px solid #e2e8f0;
}

.detail-author {
  display: flex;
  align-items: center;
  gap: 16px;
}

.author-meta {
  display: flex;
  flex-direction: column;
}

.detail-author-name {
  font-size: 18px;
  font-weight: 600;
  color: #2d3748;
}

.detail-time {
  font-size: 14px;
  color: #a0aec0;
}

.like-btn {
  border-radius: 8px;
}

.detail-title {
  font-size: 28px;
  font-weight: 700;
  color: #2d3748;
  line-height: 1.3;
  margin-bottom: 24px;
}

.detail-body {
  font-size: 16px;
  line-height: 1.8;
  color: #4a5568;
  margin-bottom: 24px;
}

.detail-tags {
  display: flex;
  gap: 8px;
  margin-bottom: 24px;
}

.detail-tag {
  background: #f7fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 6px 12px;
  color: #4a5568;
}

.detail-stats {
  display: flex;
  gap: 24px;
  margin-bottom: 24px;
}

.detail-stats .stat-box {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  background: #f7fafc;
  border-radius: 10px;
  color: #718096;
}

/* 评论区 */
.comments-section {
  background: #f7fafc;
  border-radius: 12px;
  padding: 24px;
  margin-top: 24px;
}

.comments-title {
  font-size: 18px;
  font-weight: 600;
  color: #2d3748;
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.comments-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-bottom: 24px;
}

.comment-item {
  display: flex;
  gap: 12px;
}

.comment-body {
  flex: 1;
  background: white;
  border-radius: 10px;
  padding: 16px;
}

.comment-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.comment-author {
  font-size: 14px;
  font-weight: 600;
  color: #2d3748;
}

.comment-time {
  font-size: 12px;
  color: #a0aec0;
}

.comment-text {
  font-size: 14px;
  color: #4a5568;
  line-height: 1.6;
}

.comment-input-box {
  position: relative;
}

.comment-input :deep(.el-input__wrapper) {
  border-radius: 10px;
  border: 2px solid #e2e8f0;
}

.submit-comment-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .community-container {
    grid-template-columns: 1fr;
    gap: 24px;
  }
  
  .sidebar {
    order: -1;
  }
}

@media (max-width: 768px) {
  .page-header {
    padding: 32px 24px;
    flex-direction: column;
    gap: 24px;
  }
  
  .header-stats {
    gap: 16px;
  }
  
  .header-stats .stat-box {
    padding: 12px 16px;
    min-width: 100px;
  }
  
  .stat-number {
    font-size: 24px;
  }
  
  .community-container {
    padding: 24px 16px;
  }
  
  .posts-grid {
    grid-template-columns: 1fr;
  }
}
</style>