<template>
  <main class="page-container">
    <div class="community-layout">
      <div class="community-main">
        <el-card class="app-card post-entry-card" shadow="never">
          <div class="post-entry">
            <div class="post-entry-text">
              <h2 class="card-title">社区交流</h2>
              <p class="post-entry-desc">分享观点、讨论新闻、参与互动</p>
            </div>
            <el-button type="primary" class="post-entry-button" @click="openPostDialog">
              发布帖子
            </el-button>
          </div>
        </el-card>

        <el-dialog
          v-model="postDialogVisible"
          title="发布新帖子"
          width="640px"
          class="post-dialog"
          :close-on-click-modal="false"
          @close="closePostDialog"
        >
          <el-form :model="postForm" label-width="0" @submit.prevent="submitPost">
            <el-form-item>
              <el-input
                v-model="postForm.title"
                placeholder="请输入帖子标题"
                maxlength="80"
                show-word-limit
                class="post-title-input"
              />
            </el-form-item>
            <el-form-item>
              <el-input
                v-model="postForm.content"
                type="textarea"
                placeholder="分享你的观点、问题或发现..."
                :rows="6"
                maxlength="2000"
                show-word-limit
                class="post-content-input"
              />
            </el-form-item>
            <el-form-item>
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
                  @keyup.enter.prevent="addTag"
                />
              </div>
              <div v-if="suggestedTags.length" class="suggested-tags-wrap">
                <div class="suggested-tags-title">推荐标签</div>
                <div class="suggested-tags">
                  <el-tag
                    v-for="tag in suggestedTags"
                    :key="tag"
                    class="suggested-tag"
                    effect="plain"
                    @click="addSuggestedTag(tag)"
                  >
                    + {{ tag }}
                  </el-tag>
                </div>
              </div>
            </el-form-item>
          </el-form>
          <template #footer>
            <div class="dialog-footer">
              <el-button @click="closePostDialog">取消</el-button>
              <el-button type="primary" :loading="submitting" :disabled="submitting" @click="submitPost">
                发布
              </el-button>
            </div>
          </template>
        </el-dialog>

        <el-card class="app-card" shadow="never">
          <div class="section-header">
            <h2 class="card-title">帖子流</h2>
            <div class="search-bar-wrapper">
              <el-input
                v-model="searchKeyword"
                placeholder="搜索帖子..."
                @keyup.enter="handleSearch"
                class="search-input"
              />
              <el-button type="primary" :loading="loadingPosts" @click="handleSearch">搜索</el-button>
              <el-button @click="handleSearchClear">清空</el-button>
            </div>
          </div>
          <div class="tag-filter-bar">
            <span class="tag-filter-title">热门标签：</span>
            <el-tag
              :type="!selectedTag ? 'primary' : 'info'"
              effect="light"
              class="filter-tag"
              @click="selectedTag = ''"
            >
              全部
            </el-tag>
            <el-tag
              v-for="tag in hotTags"
              :key="tag.name"
              :type="selectedTag === tag.name ? 'primary' : 'info'"
              effect="light"
              class="filter-tag"
              @click="selectedTag = tag.name"
            >
              {{ tag.name }} {{ tag.count }}
            </el-tag>
          </div>
          <div v-if="loadingPosts" class="loading-container">
            <el-spinner />
          </div>
          <div v-else-if="filteredPosts.length === 0" class="empty-state">
            <el-empty :description="selectedTag ? '暂无该标签下的帖子' : searchKeyword ? '未找到相关帖子' : '暂无帖子'" />
          </div>
          <div v-else class="posts-list">
            <el-card
              v-for="post in filteredPosts"
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
              @click="handleHotSearch(item.keyword)"
            >
              <div :class="['rank', getRankClass(item.rank)]">{{ item.rank }}</div>
              <div class="hot-search-content">
                <div class="keyword-row">
                  <span class="keyword">{{ item.keyword }}</span>
                  <el-icon :class="['trend', item.trend]">
                    <ArrowUp v-if="item.trend === 'up'" />
                    <ArrowDown v-else-if="item.trend === 'down'" />
                    <Minus v-else />
                  </el-icon>
                </div>
                <div class="hot-search-meta">
                  <span>热度 {{ item.search_count }}</span>
                  <span>排名 {{ item.rank }}</span>
                </div>
              </div>
              <el-button class="timeline-link" type="primary" link @click.stop="openTimelineForHotSearch(item)">
                查看脉络
              </el-button>
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

    <TimelineDrawer
      v-model="timelineDrawerVisible"
      :topic-id="selectedTopicId"
      :topic-name="selectedTopicName"
    />

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
        <div v-if="loadingCommentsSummary" class="loading-container">
          <el-spinner />
        </div>
        <div v-else-if="commentsSummary" class="comments-summary-card">
          <div class="summary-header">
            <el-icon><ChatDotRound /></el-icon>
            <span class="summary-title">AI 评论总结</span>
            <el-tag :type="commentsSummary.source === 'llm' ? 'success' : 'info'" size="small">
              {{ commentsSummary.source === 'llm' ? 'AI 生成' : '关键词匹配' }}
            </el-tag>
          </div>
          <div class="summary-content">
            <p>{{ commentsSummary.summary }}</p>
          </div>
          <div class="summary-tags">
            <el-tag :type="getSentimentType(commentsSummary.sentiment)" size="small">
              {{ getSentimentText(commentsSummary.sentiment) }}
            </el-tag>
            <el-tag type="info" size="small">
              关键词: {{ commentsSummary.keyword }}
            </el-tag>
          </div>
        </div>
        <div class="comments-header">
          <h4>评论 ({{ comments.length }})</h4>
          <span class="comments-hint">支持图片和表情</span>
        </div>

        <CommentBox
          placeholder="写下你的评论..."
          button-text="发表评论"
          :loading="submittingComment"
          class="community-comment-box"
          @submit="handleCreateComment"
        />

        <div v-if="loadingComments" class="loading-container">
          <el-spinner />
        </div>
        <div v-else-if="comments.length === 0" class="empty-state">
          <el-empty description="暂无评论，快来发第一条吧" />
        </div>
        <div v-else class="comments-list">
          <CommentItem
            v-for="comment in comments"
            :key="comment.id"
            :comment="comment"
            :replying-id="replyingCommentId"
            :loading-like="commentLikeLoadingId === comment.id"
            :loading-reply="commentReplyLoadingId === comment.id"
            :deleting-id="commentDeleteLoadingId"
            :current-user-id="userStore.userInfo?.id ?? null"
            :current-user-role="userStore.role"
            @like="handleCommentLike"
            @reply="handleCommentReply"
            @delete="handleCommentDelete"
          />
        </div>
      </div>
    </el-dialog>
  </main>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
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
  ChatDotRound,
} from '@element-plus/icons-vue'
import {
  getPostList,
  createPost,
  getPostDetail,
  getComments,
  createComment,
  replyComment,
  deleteComment,
  likeComment,
  toggleLike,
  getHotSearch,
  aiNewsHelper,
  getCommentsSummary,
  type CommunityPost,
  type CommentItem as CommunityCommentItem,
  type HotSearchItem,
  type CommentsSummaryResponse,
} from '@/api/community'
import { getTimelineTopics, type TimelineTopic } from '@/api/timeline'
import { useUserStore } from '@/stores/user'
import TimelineDrawer from '@/components/timeline/TimelineDrawer.vue'
import CommentBox from '@/components/interaction/CommentBox.vue'
import CommentItem, {
  type CommentItemData as RichCommentItemData,
  type CommentMediaJson,
} from '@/components/interaction/CommentItem.vue'

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
const searchKeyword = ref('')
const selectedTag = ref('')

const hotTags = computed(() => {
  const counter = new Map<string, number>()

  posts.value.forEach((post) => {
    ;(post.tags || []).forEach((tag) => {
      const normalizedTag = String(tag || '').trim()
      if (!normalizedTag) return
      counter.set(normalizedTag, (counter.get(normalizedTag) || 0) + 1)
    })
  })

  return Array.from(counter.entries())
    .map(([name, count]) => ({ name, count }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 10)
})

const filteredPosts = computed(() => {
  if (!selectedTag.value) {
    return posts.value
  }

  return posts.value.filter((post) => (post.tags || []).includes(selectedTag.value))
})

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

const postDialogVisible = ref(false)
const showPostModal = ref(false)
const selectedPost = ref<CommunityPost | null>(null)
const comments = ref<CommunityCommentItem[]>([])
const loadingComments = ref(false)
const submittingComment = ref(false)
const newComment = ref('')
const replyingCommentId = ref<number | null>(null)
const commentLikeLoadingId = ref<number | null>(null)
const commentReplyLoadingId = ref<number | null>(null)
const commentDeleteLoadingId = ref<number | null>(null)
const commentsSummary = ref<CommentsSummaryResponse | null>(null)
const loadingCommentsSummary = ref(false)

const tagRules = [
  {
    tag: 'AI生成',
    keywords: ['AI', '大模型', '生成', '标题生成', '摘要生成', '智能生成'],
  },
  {
    tag: '摘要',
    keywords: ['摘要', '总结', '概括', '长摘要', '短摘要'],
  },
  {
    tag: '新闻推荐',
    keywords: ['推荐', '个性化', '首页', '推送', '阅读偏好'],
  },
  {
    tag: '社区反馈',
    keywords: ['社区', '帖子', '发帖', '互动', '讨论'],
  },
  {
    tag: '评论审核',
    keywords: ['评论', '审核', '删除', '举报', '拉黑', '管理'],
  },
  {
    tag: '时间线',
    keywords: ['时间线', '脉络', '事件脉络', 'timeline', '发展过程'],
  },
  {
    tag: '爬虫数据',
    keywords: ['爬虫', '采集', 'RSS', '新闻源', '数据源'],
  },
  {
    tag: '系统问题',
    keywords: ['bug', '报错', '失败', '无法', '问题', '异常'],
  },
  {
    tag: '功能建议',
    keywords: ['建议', '优化', '希望', '能不能', '增加', '改进'],
  },
] as const

const suggestedTags = computed(() => {
  const text = `${postForm.value.title || ''} ${postForm.value.content || ''}`.toLowerCase()
  const currentTags = postForm.value.tags

  if (!text.trim()) {
    return [] as string[]
  }

  return tagRules
    .filter((rule) => rule.keywords.some((keyword) => text.includes(keyword.toLowerCase())))
    .map((rule) => rule.tag)
    .filter((tag) => !currentTags.includes(tag))
    .slice(0, 5)
})

function addTag() {
  addSuggestedTag(newTag.value)
  newTag.value = ''
}

function removeTag(tag: string) {
  const index = postForm.value.tags.indexOf(tag)
  if (index > -1) {
    postForm.value.tags.splice(index, 1)
  }
}

function addSuggestedTag(tag: string) {
  const normalizedTag = tag.trim()
  if (!normalizedTag) {
    return
  }

  if (postForm.value.tags.includes(normalizedTag)) {
    return
  }

  if (postForm.value.tags.length >= 5) {
    ElMessage.warning('最多添加 5 个标签')
    return
  }

  postForm.value.tags.push(normalizedTag)
}

function openPostDialog() {
  postDialogVisible.value = true
}

function closePostDialog() {
  if (submitting.value) {
    return
  }
  postDialogVisible.value = false
}

async function submitPost() {
  const title = postForm.value.title.trim()
  const content = postForm.value.content.trim()

  if (!title || !content) {
    if (!title) {
      ElMessage.warning('请输入帖子标题')
    } else {
      ElMessage.warning('请输入帖子内容')
    }
    return
  }

  submitting.value = true
  try {
    await createPost({
      title,
      content,
      tags: postForm.value.tags,
    })
    ElMessage.success('帖子已提交，正在审核中')
    postForm.value = { title: '', content: '', tags: [] }
    newTag.value = ''
    postDialogVisible.value = false
    await loadPosts(1)
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '发帖失败，请稍后重试')
  } finally {
    submitting.value = false
  }
}

async function loadPosts(page = 1) {
  currentPage.value = page
  loadingPosts.value = true
  try {
    const result = await getPostList({
      page,
      page_size: pageSize.value,
      keyword: searchKeyword.value.trim() || undefined,
    })
    posts.value = result.list.map((p) => ({
      ...p,
      liked: Boolean(p.liked ?? (p as { is_liked?: boolean }).is_liked ?? false),
    }))
    postTotal.value = result.total
  } catch (error) {
    posts.value = []
    postTotal.value = 0
    ElMessage.error(error instanceof Error ? error.message : '获取帖子列表失败')
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

function handleSearch() {
  currentPage.value = 1
  loadPosts(1)
}

function handleSearchClear() {
  searchKeyword.value = ''
  currentPage.value = 1
  loadPosts(1)
}

let searchTimer: ReturnType<typeof setTimeout> | null = null
watch(searchKeyword, () => {
  if (searchTimer) {
    clearTimeout(searchTimer)
  }
  searchTimer = setTimeout(() => {
    currentPage.value = 1
    loadPosts(1)
  }, 500)
})

function handleHotSearch(keyword: string) {
  searchKeyword.value = keyword
  currentPage.value = 1
  loadPosts(1)
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

function getRankClass(rank: number) {
  if (rank <= 3) return 'top-three'
  return ''
}

async function sendAIQuestion() {
  if (!aiQuestion.value.trim() || aiLoading.value) return
  aiMessages.value.push({ type: 'user', content: aiQuestion.value })
  const question = aiQuestion.value
  aiQuestion.value = ''
  aiLoading.value = true
  try {
    const result = await aiNewsHelper(question)
    aiMessages.value.push({ type: 'ai', content: result.answer || '暂无回答' })
  } catch (error) {
    aiMessages.value.push({ type: 'ai', content: '抱歉，AI服务暂时不可用，请稍后重试。' })
    ElMessage.warning('AI服务暂时不可用，已切换到本地回答模式')
  } finally {
    aiLoading.value = false
  }
}

async function showPostDetail(post: CommunityPost) {
  selectedPost.value = post
  replyingCommentId.value = null
  showPostModal.value = true
  await loadComments(post.id)
  await loadCommentsSummary(post.id)
}

async function loadCommentsSummary(postId: number) {
  loadingCommentsSummary.value = true
  try {
    commentsSummary.value = await getCommentsSummary(postId)
  } catch (e) {
    commentsSummary.value = null
    console.error('获取评论总结失败', e)
  } finally {
    loadingCommentsSummary.value = false
  }
}

async function loadComments(postId: number) {
  loadingComments.value = true
  try {
    const result = await getComments(postId)
    comments.value = result.list || []
  } finally {
    loadingComments.value = false
  }
}

async function handleCreateComment(content: string, mediaJson: CommentMediaJson | null) {
  if (!selectedPost.value) return

  const normalizedContent = content.trim()
  if (!normalizedContent && !mediaJson) return

  submittingComment.value = true
  try {
    await createComment(selectedPost.value.id, {
      content: normalizedContent || ' ',
      media_json: mediaJson,
    })
    await loadComments(selectedPost.value.id)
    selectedPost.value.comment_count = (selectedPost.value.comment_count || 0) + 1
    selectedPost.value.comments = (selectedPost.value.comments || 0) + 1
  } catch (e) {
    console.error('评论失败', e)
    ElMessage.error(e instanceof Error ? e.message : '评论失败，请稍后重试')
  } finally {
    submittingComment.value = false
  }
}

async function handleCommentLike(comment: RichCommentItemData) {
  if (!selectedPost.value) return

  commentLikeLoadingId.value = comment.id
  try {
    await likeComment(comment.id)
    await loadComments(selectedPost.value.id)
  } catch (e) {
    console.error('评论点赞失败', e)
    ElMessage.error(e instanceof Error ? e.message : '评论点赞失败，请稍后重试')
  } finally {
    commentLikeLoadingId.value = null
  }
}

async function handleCommentReply(comment: RichCommentItemData, content: string, mediaJson?: CommentMediaJson | null) {
  if (!selectedPost.value) return

  if (content === '__toggle__') {
    replyingCommentId.value = replyingCommentId.value === comment.id ? null : comment.id
    return
  }

  if (!content.trim()) {
    replyingCommentId.value = null
    return
  }

  commentReplyLoadingId.value = comment.id
  try {
    await replyComment(comment.id, {
      content,
      media_json: mediaJson,
    })
    replyingCommentId.value = null
    await loadComments(selectedPost.value.id)
    selectedPost.value.comment_count = (selectedPost.value.comment_count || 0) + 1
    selectedPost.value.comments = (selectedPost.value.comments || 0) + 1
  } catch (e) {
    console.error('回复评论失败', e)
    ElMessage.error(e instanceof Error ? e.message : '回复评论失败，请稍后重试')
  } finally {
    commentReplyLoadingId.value = null
  }
}

async function handleCommentDelete(comment: RichCommentItemData) {
  if (!selectedPost.value) return

  try {
    await ElMessageBox.confirm('确定删除这条评论吗？', '删除评论', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning',
    })
  } catch {
    return
  }

  commentDeleteLoadingId.value = comment.id
  try {
    const result = await deleteComment(comment.id)
    await loadComments(selectedPost.value.id)
    selectedPost.value.comment_count = result.comment_count ?? Math.max(0, (selectedPost.value.comment_count || 0) - 1)
    selectedPost.value.comments = selectedPost.value.comment_count || 0
    ElMessage.success('评论已删除')
  } catch (e) {
    console.error('删除评论失败', e)
    ElMessage.error(e instanceof Error ? e.message : '删除评论失败')
  } finally {
    commentDeleteLoadingId.value = null
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

function getSentimentType(sentiment: string) {
  switch (sentiment) {
    case 'positive': return 'success'
    case 'negative': return 'danger'
    default: return 'warning'
  }
}

function getSentimentText(sentiment: string) {
  switch (sentiment) {
    case 'positive': return '正面'
    case 'negative': return '负面'
    default: return '中立'
  }
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

.post-entry-card {
  margin-bottom: 24px;
}

.post-entry {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  min-height: 96px;
}

.post-entry-text {
  min-width: 0;
}

.post-entry-desc {
  margin: 8px 0 0;
  color: #909399;
  font-size: 14px;
}

.post-entry-button {
  flex-shrink: 0;
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
  width: 160px;
}

.tag-filter-bar {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 16px;
}

.tag-filter-title {
  font-weight: 600;
  color: #374151;
}

.filter-tag {
  cursor: pointer;
  user-select: none;
}

.suggested-tags-wrap {
  margin-top: 8px;
}

.suggested-tags-title {
  margin-bottom: 8px;
  font-size: 13px;
  color: #909399;
}

.suggested-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.suggested-tag {
  cursor: pointer;
  transition: all 0.2s ease;
  border-style: dashed;
}

.suggested-tag:hover {
  color: #409eff;
  border-color: #409eff;
  background: rgba(64, 158, 255, 0.08);
}

.post-actions {
  display: flex;
  justify-content: flex-end;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.post-dialog :deep(.el-dialog__body) {
  padding-top: 8px;
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
  display: grid;
  gap: 10px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.hot-search-item {
  display: grid;
  grid-template-columns: 34px minmax(0, 1fr) auto;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  border: 1px solid #e5e7eb;
  border-radius: 14px;
  background: var(--color-bg-card, #fff);
  cursor: pointer;
  transition:
    transform 0.16s ease,
    border-color 0.16s ease,
    box-shadow 0.16s ease,
    background-color 0.16s ease;
}

.hot-search-item:hover {
  border-color: color-mix(in srgb, var(--color-primary) 30%, #e5e7eb);
  box-shadow: 0 8px 16px rgb(15 23 42 / 8%);
  transform: translateY(-1px);
}

.rank {
  width: 34px;
  height: 34px;
  display: grid;
  place-items: center;
  border-radius: 999px;
  background: var(--color-primary-soft, #e8f1ff);
  color: var(--color-primary, #409eff);
  font-size: 13px;
  font-weight: 700;
}

.rank.top-three {
  background: color-mix(in srgb, var(--color-primary) 14%, white);
  color: #1d4ed8;
  box-shadow: inset 0 0 0 1px color-mix(in srgb, var(--color-primary) 14%, white);
}

.keyword {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-primary, #1f2937);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.hot-search-content {
  min-width: 0;
  display: grid;
  gap: 6px;
}

.keyword-row {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.keyword-row .keyword {
  flex: 1;
}

.hot-search-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 6px 12px;
  color: var(--color-text-secondary, #6b7280);
  font-size: 12px;
}

.hot-search-item .trend {
  margin-left: 2px;
}

.timeline-link {
  flex-shrink: 0;
  justify-self: end;
  padding: 0;
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

@media (max-width: 768px) {
  .hot-search-item {
    grid-template-columns: 34px minmax(0, 1fr);
    grid-template-areas:
      'rank content'
      'rank action';
  }

  .rank {
    grid-area: rank;
  }

  .hot-search-content {
    grid-area: content;
    min-width: 0;
  }

  .keyword-row {
    justify-content: space-between;
  }

  .hot-search-item .trend {
    justify-self: end;
  }

  .timeline-link {
    grid-area: action;
    justify-self: start;
  }
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

.comments-summary-card {
  background: linear-gradient(135deg, #f5f7fa 0%, #e4e8ec 100%);
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
}

.summary-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.summary-title {
  font-weight: 600;
  font-size: 14px;
}

.summary-content {
  margin-bottom: 12px;
}

.summary-content p {
  color: #333;
  line-height: 1.6;
  margin: 0;
}

.summary-tags {
  display: flex;
  gap: 8px;
}

.comments-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin: 20px 0 12px;
}

.comments-hint {
  font-size: 12px;
  color: #909399;
}

.community-comment-box {
  margin-bottom: 16px;
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

.search-input {
  width: 200px;
}

.search-bar-wrapper {
  display: flex;
  align-items: center;
  gap: 8px;
}

.search-bar-wrapper > :nth-child(3) {
  margin-left: -2px;
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
