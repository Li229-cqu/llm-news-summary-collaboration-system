<template>
  <main class="page-container">
    <!-- 顶部一行：社区广场 + 搜索框 + 标签筛选 + 发布按钮 -->
    <div class="top-bar">
      <h2 class="top-bar-title">
        社区广场
        <el-icon class="title-icon"><Message /></el-icon>
      </h2>
      <div class="top-bar-search">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索帖子、话题、新闻事件"
          class="search-input"
          clearable
          @keyup.enter="handleSearch"
        />
        <el-button type="primary" @click="handleSearch">搜索</el-button>
        <el-button @click="handleSearchClear">清空</el-button>
      </div>
      <div class="top-bar-tags">
        <el-tag :type="!selectedTag ? 'primary' : 'info'" effect="light" class="filter-tag" @click="selectedTag = ''; currentPage = 1; loadPosts(1)">全部</el-tag>
        <el-tag v-for="tag in availableTags" :key="tag.name" :type="selectedTag === tag.name ? 'primary' : 'info'" effect="light" class="filter-tag" @click="toggleTag(tag.name)">{{ tag.name }}</el-tag>
      </div>
      <el-button type="primary" class="top-bar-btn" @click="router.push('/community/create')">发布帖子</el-button>
    </div>

    <div class="community-layout">
      <div class="community-sidebar">
        <HotTopicsSidebar :list="hotSearchList" :loading="loadingHotSearch" @open-hot-topic="handleHotSearchClick" />
      </div>
      <div class="community-main">
        <el-card class="app-card main-card" shadow="never">
          <div class="feed-tabs">
            <button v-for="tab in feedTabs" :key="tab.name" :class="['feed-tab', { active: activeFeedTab === tab.name }]" @click="switchTab(tab.name)">{{ tab.label }}</button>
          </div>
          <div ref="scrollAreaRef" class="scroll-area">
            <template v-if="activeFeedTab === 'recommend' && contentMode === 'list'">
              <div v-if="loadingPosts" class="loading-container"><el-spinner /></div>
              <div v-else-if="posts.length === 0" class="empty-state"><el-empty :description="searchKeyword ? '未找到相关帖子' : '暂无帖子，快来发布第一条吧'" /></div>
              <div v-else class="posts-list">
                <PostCard v-for="post in posts" :key="post.id" :post="post" @view="openPostDetail" @like="handleLike" @favorite="handleFavorite" @comment="openPostDetail" @open-related-news="handleOpenRelatedNews" />
              </div>
              <el-pagination v-if="postTotal > pageSize" :current-page="currentPage" :page-size="pageSize" :total="postTotal" layout="prev, pager, next" @current-change="loadPosts" class="pagination" />
            </template>
            <PostDetailPanel
              v-else-if="activeFeedTab === 'recommend' && contentMode === 'detail' && selectedPostId"
              :post-id="selectedPostId"
              @back="backToPostList"
              @updated="handlePostDetailUpdated"
              @open-related-news="handleOpenRelatedNewsId"
            />
            <div v-else-if="activeFeedTab === 'ai'" class="ai-tab-container">
              <AISessionList :sessions="aiSessions" :active-session-id="aiActiveSessionId" :collapsed="aiSessionCollapsed" :loading="aiLoadingSessions" @select="handleAiSelectSession" @create="handleAiCreateSession" @delete="handleAiDeleteSession" @toggle-collapse="aiSessionCollapsed = !aiSessionCollapsed" />
              <AIChatPanel :active-session="aiActiveSession" :messages="aiCurrentMessages" :loading-messages="aiLoadingMessages" :sending="aiSending" :user-avatar="userAvatar" @send="handleAiSend" @first-question="handleAiCreateSession" />
            </div>
            <MyInteractionsPanel v-else-if="activeFeedTab === 'interactions'" @open-post-detail="handleOpenMyPostDetail" />
            <MyPostsPanel v-else-if="activeFeedTab === 'posts'" @publish="router.push('/community/create')" @view-post="handleOpenMyPostDetail" />
          </div>
        </el-card>
      </div>
    </div>
  </main>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, watch, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getPostList, getPostDetail, toggleLike, toggleFavorite, unfavoritePost, getHotSearch, getAvailableTags, createCommunityAiSession, getCommunityAiSessions, getCommunityAiSessionDetail, sendCommunityAiMessage, deleteCommunityAiSession, type CommunityPost, type PostListParams, type HotSearchItem, type TagCount, type CommunityAiSession, type CommunityAiMessage } from '@/api/community'
import { useUserStore } from '@/stores/user'
import PostCard from '@/components/community/PostCard.vue'
import HotTopicsSidebar from '@/components/community/HotTopicsSidebar.vue'
import AISessionList from '@/components/community/AISessionList.vue'
import AIChatPanel from '@/components/community/AIChatPanel.vue'
import MyInteractionsPanel from '@/components/community/MyInteractionsPanel.vue'
import MyPostsPanel from '@/components/community/MyPostsPanel.vue'
import PostDetailPanel from '@/components/community/PostDetailPanel.vue'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

// ─── Post List ──
const posts = ref<CommunityPost[]>([])
const loadingPosts = ref(false)
const currentPage = ref(1)
const pageSize = ref(10)
const postTotal = ref(0)
const searchKeyword = ref('')
const selectedTag = ref('')

function toggleTag(name: string) {
  selectedTag.value = selectedTag.value === name ? '' : name
  currentPage.value = 1
  loadPosts(1)
}

async function loadPosts(page = 1) {
  currentPage.value = page; loadingPosts.value = true
  try {
    const params: PostListParams = { page, page_size: pageSize.value, sort: 'hot' }
    const kw = searchKeyword.value.trim()
    if (kw) params.keyword = kw
    if (selectedTag.value) params.tag = selectedTag.value
    const result = await getPostList(params)
    posts.value = result.list.map(p => ({ ...p, liked: Boolean(p.liked ?? (p as any).is_liked ?? false) }))
    postTotal.value = result.total
    // 如果当前页为空但 total > 0，回退到最后一页
    if (posts.value.length === 0 && postTotal.value > 0 && currentPage.value > 1) {
      const lastPage = Math.ceil(postTotal.value / pageSize.value)
      loadPosts(lastPage)
    }
  } catch { posts.value = []; postTotal.value = 0; ElMessage.error('获取帖子列表失败') } finally { loadingPosts.value = false }
}
function handleSearch() { currentPage.value = 1; loadPosts(1) }
function handleSearchClear() { searchKeyword.value = ''; selectedTag.value = ''; currentPage.value = 1; loadPosts(1) }
let searchTimer: ReturnType<typeof setTimeout> | null = null
watch(searchKeyword, () => { if (searchTimer) clearTimeout(searchTimer); searchTimer = setTimeout(() => { currentPage.value = 1; loadPosts(1) }, 500) })
watch(selectedTag, () => { /* 已在 toggleTag 中处理 */ })

// ─── Tags ──
const availableTags = ref<TagCount[]>([])
async function loadAvailableTags() {
  try { availableTags.value = await getAvailableTags() } catch { availableTags.value = [{ name: '时政', count: 0 }, { name: '经济', count: 0 }, { name: '科技', count: 0 }, { name: '教育', count: 0 }, { name: '军事', count: 0 }, { name: '社会', count: 0 }, { name: '国际', count: 0 }, { name: '体育', count: 0 }, { name: '娱乐', count: 0 }, { name: '健康', count: 0 }] }
}

// ─── Tabs & Content Mode ──
const activeFeedTab = ref<'recommend' | 'ai' | 'interactions' | 'posts'>('recommend')
const feedTabs = [ { name: 'recommend', label: '推荐讨论' }, { name: 'ai', label: 'AI 问答' }, { name: 'interactions', label: '我的互动' }, { name: 'posts', label: '我的帖子' } ] as const

const contentMode = ref<'list' | 'detail'>('list')
const selectedPostId = ref<number | string | null>(null)

// 滚动恢复
const scrollAreaRef = ref<HTMLElement | null>(null)
const listScrollTop = ref(0)

function switchTab(name: string) {
  // 切 Tab 时退出详情模式
  contentMode.value = 'list'
  selectedPostId.value = null
  activeFeedTab.value = name as typeof activeFeedTab.value
  if (name === 'recommend') {
    currentPage.value = 1
    loadPosts(1)
  }
}

function openPostDetail(post: CommunityPost) {
  const postId = post.id
  if (!postId) return
  // 保存当前列表滚动位置，再切换到详情模式
  if (scrollAreaRef.value) {
    listScrollTop.value = scrollAreaRef.value.scrollTop
  }
  selectedPostId.value = postId
  contentMode.value = 'detail'
}

function backToPostList() {
  contentMode.value = 'list'
  selectedPostId.value = null
  // 恢复滚动位置
  nextTick(() => {
    if (scrollAreaRef.value) {
      scrollAreaRef.value.scrollTop = listScrollTop.value
    }
  })
}

function handlePostDetailUpdated() {
  // 详情中有点赞/收藏/评论更新时，刷新列表数据（但不退出详情）
  if (currentPage.value) {
    loadPosts(currentPage.value)
  }
}

// ─── AI ──
const aiSessions = ref<CommunityAiSession[]>([]); const aiActiveSessionId = ref<number | null>(null); const aiActiveSession = ref<CommunityAiSession | null>(null); const aiCurrentMessages = ref<CommunityAiMessage[]>([]); const aiLoadingSessions = ref(false); const aiLoadingMessages = ref(false); const aiSending = ref(false); const aiSessionCollapsed = ref(false)
const userAvatar = computed(() => normalizeAvatarUrl(userStore.userInfo?.avatar))
function normalizeAvatarUrl(url?: string): string {
  if (!url) return ''
  if (url.startsWith('http://') || url.startsWith('https://') || url.startsWith('data:image/')) return url
  const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'
  return `${baseURL.replace(/\/$/, '')}/${url.replace(/^\//, '')}`
}
function makeTempMsg(role: 'user' | 'assistant', content: string, loading = false): CommunityAiMessage {
  return { id: `temp-${role}-${Date.now()}`, role, content, loading, created_at: new Date().toISOString() } as unknown as CommunityAiMessage
}
watch(activeFeedTab, (tab) => { if (tab === 'ai') loadAiSessions() })
async function loadAiSessions() { aiLoadingSessions.value = true; try { const res = await getCommunityAiSessions({ page: 1, page_size: 50 }); aiSessions.value = res.list || []; if (aiSessions.value.length > 0) { if (!aiActiveSessionId.value || !aiSessions.value.some(s => s.id === aiActiveSessionId.value)) aiActiveSessionId.value = aiSessions.value[0].id; await loadAiSessionDetail(aiActiveSessionId.value) } else { aiActiveSessionId.value = null; aiActiveSession.value = null; aiCurrentMessages.value = [] } } catch { aiSessions.value = [] } finally { aiLoadingSessions.value = false } }
async function loadAiSessionDetail(sessionId: number) { if (!sessionId) return; aiLoadingMessages.value = true; try { const res = await getCommunityAiSessionDetail(sessionId); aiActiveSession.value = res.session; aiCurrentMessages.value = res.messages || [] } catch { ElMessage.error('获取会话详情失败') } finally { aiLoadingMessages.value = false } }
async function handleAiCreateSession() { try { const res = await createCommunityAiSession({}); aiSessions.value.unshift(res.session); aiActiveSessionId.value = res.session.id; aiActiveSession.value = res.session; aiCurrentMessages.value = res.messages || [] } catch { ElMessage.error('创建会话失败') } }
async function handleAiSelectSession(sessionId: number) { aiActiveSessionId.value = sessionId; await loadAiSessionDetail(sessionId) }
async function handleAiSend(question: string) {
  // 乐观更新：先立即显示用户消息 + AI loading
  const userMsg = makeTempMsg('user', question)
  const loadingMsg = makeTempMsg('assistant', '', true)
  aiCurrentMessages.value.push(userMsg)
  aiCurrentMessages.value.push(loadingMsg)
  aiSending.value = true
  try {
    if (aiActiveSessionId.value) {
      const res = await sendCommunityAiMessage(aiActiveSessionId.value, { question })
      // 替换临时消息为真实消息
      const userIdx = aiCurrentMessages.value.findIndex(m => m.id === userMsg.id)
      if (userIdx !== -1) aiCurrentMessages.value[userIdx] = res.user_message
      const aiIdx = aiCurrentMessages.value.findIndex(m => m.id === loadingMsg.id)
      if (aiIdx !== -1) aiCurrentMessages.value[aiIdx] = res.assistant_message
      aiActiveSession.value = res.session
      const idx = aiSessions.value.findIndex(s => s.id === res.session.id)
      if (idx !== -1) aiSessions.value[idx] = res.session
    } else {
      const res = await createCommunityAiSession({ question })
      aiSessions.value.unshift(res.session)
      aiActiveSessionId.value = res.session.id
      aiActiveSession.value = res.session
      // 合并后端返回的消息，去重
      const serverMessages = res.messages || []
      if (serverMessages.length > 0) {
        const currentIds = new Set(aiCurrentMessages.value.filter(m => !String(m.id).startsWith('temp-')).map(m => m.id))
        const newMsgs = serverMessages.filter(m => !currentIds.has(m.id))
        // 移除临时 loading，追加新消息
        const filtered = aiCurrentMessages.value.filter(m => !String(m.id).startsWith('temp-'))
        aiCurrentMessages.value = [...filtered, ...newMsgs]
      }
    }
  } catch {
    // 失败时保留用户消息，loading 改为失败提示
    const aiIdx = aiCurrentMessages.value.findIndex(m => m.id === loadingMsg.id)
    if (aiIdx !== -1) aiCurrentMessages.value[aiIdx] = makeTempMsg('assistant', 'AI 助手暂时无法回复，请稍后再试。')
    ElMessage.error('消息发送失败')
  } finally { aiSending.value = false }
}
async function handleAiDeleteSession(sessionId: number) { try { await deleteCommunityAiSession(sessionId); aiSessions.value = aiSessions.value.filter(s => s.id !== sessionId); if (aiActiveSessionId.value === sessionId) { if (aiSessions.value.length > 0) { aiActiveSessionId.value = aiSessions.value[0].id; await loadAiSessionDetail(aiActiveSessionId.value) } else { aiActiveSessionId.value = null; aiActiveSession.value = null; aiCurrentMessages.value = [] } } } catch { ElMessage.error('删除会话失败') } }

// ─── Hot Search ──
const hotSearchList = ref<HotSearchItem[]>([]); const loadingHotSearch = ref(false)
async function loadHotSearch() { loadingHotSearch.value = true; try { hotSearchList.value = await getHotSearch({ limit: 10 }) } finally { loadingHotSearch.value = false } }
function handleHotSearchClick(item: HotSearchItem) {
  if (item.target_type === 'post' || item.target_type === 'community_post') {
    // 进入内嵌详情
    selectedPostId.value = item.target_id
    contentMode.value = 'detail'
    activeFeedTab.value = 'recommend'
  } else {
    searchKeyword.value = item.keyword; currentPage.value = 1; loadPosts(1)
  }
}

// ─── Like / Favorite ──
async function handleLike(post: CommunityPost) { try { const r = await toggleLike(post.id); post.likes = r.count; post.liked = r.liked } catch { console.error('点赞失败') } }
async function handleFavorite(post: CommunityPost, event: Event) { event.stopPropagation(); try { if (post.is_favorited) { const r = await unfavoritePost(post.id); post.is_favorited = false; post.favorite_count = r.favorite_count } else { const r = await toggleFavorite(post.id); post.is_favorited = r.is_favorited; post.favorite_count = r.favorite_count } } catch { console.error('收藏操作失败') } }

// ─── Nav ──
function handleViewPost(post: CommunityPost) { openPostDetail(post) }
function handleOpenMyPostDetail(postId: number) {
  // 从我的帖子/互动进入内嵌详情
  selectedPostId.value = postId
  contentMode.value = 'detail'
  activeFeedTab.value = 'recommend'
}
function handleOpenRelatedNews(post: CommunityPost) { if (post.related_news_id) router.push(`/news/${post.related_news_id}`) }
function handleOpenRelatedNewsId(newsId: number | string) { router.push(`/news/${newsId}`) }

onMounted(() => {
  if (!userStore.userInfo) userStore.loadFromStorage()
  loadPosts()
  loadHotSearch()
  loadAvailableTags()
  // 发帖成功后置顶新帖子
  const pendingId = route.query.newPostId || sessionStorage.getItem('community_pending_new_post_id')
  if (pendingId) {
    sessionStorage.removeItem('community_pending_new_post_id')
    currentPage.value = 1
    loadPosts(1).then(() => {
      if (pendingId) pinNewPostToTop(String(pendingId))
    })
    router.replace({ path: '/community', query: {} })
  }
})

async function pinNewPostToTop(postId: string | number) {
  try {
    const detail = await getPostDetail(postId)
    if (!detail || !detail.id) return
    // 去重后插入第一位
    posts.value = [detail, ...posts.value.filter(p => String(p.id) !== String(detail.id))]
    if (posts.value.length > postTotal.value) {
      postTotal.value = posts.value.length
    }
  } catch {
    // 静默失败，不影响社区页正常显示
  }
}</script>

<style scoped>
.page-container { height: 100%; min-height: 0; display: flex; flex-direction: column; overflow: hidden; background: radial-gradient(circle at 18% 10%, rgba(220, 38, 38, 0.08), transparent 28%), linear-gradient(180deg, #fef2f2 0%, #fef7f7 100%); }

/* ── 顶部一行 ── */
.top-bar { display: flex; align-items: center; gap: 12px; padding: 12px 32px; flex-shrink: 0; flex-wrap: wrap; }
.top-bar-title { margin: 0; color: #111827; font-size: 20px; font-weight: 800; white-space: nowrap; display: flex; align-items: center; gap: 6px; flex-shrink: 0; }
.title-icon { color: #dc2626; font-size: 16px; }
.top-bar-search { display: flex; align-items: center; gap: 6px; flex: 1; min-width: 200px; max-width: 420px; }
.top-bar-search .search-input { flex: 1; }
.top-bar-search :deep(.el-input__wrapper) { height: 34px; border-radius: 8px; }
.top-bar-tags { display: flex; align-items: center; gap: 4px; flex: 1; min-width: 300px; flex-wrap: wrap; }
.filter-tag { height: 26px; min-width: 44px; justify-content: center; border-radius: 999px; background: #fff; cursor: pointer; font-size: 12px; box-shadow: 0 2px 8px rgba(31, 76, 130, 0.06); }
.top-bar-btn { height: 36px; border-radius: 6px; font-size: 14px; font-weight: 600; flex-shrink: 0; }

/* ── 主体 ── */
.community-layout { display: flex; align-items: stretch; gap: 16px; flex: 1; min-height: 0; width: 100%; padding: 0 32px 16px; }
.community-sidebar { width: 320px; flex: 0 0 320px; display: flex; flex-direction: column; min-height: 0; overflow: hidden; }
.community-main { flex: 1; min-width: 0; display: flex; flex-direction: column; min-height: 0; overflow: hidden; }
.main-card { flex: 1; min-height: 0; display: flex; flex-direction: column; overflow: hidden; }
.main-card :deep(.el-card__body) { padding: 16px 24px; flex: 1; display: flex; flex-direction: column; min-height: 0; overflow: hidden; }
.scroll-area { flex: 1; min-height: 0; overflow-y: auto; overscroll-behavior: contain; padding-right: 4px; }
.app-card { border: 1px solid rgba(238, 210, 210, 0.86); border-radius: 12px; box-shadow: 0 8px 24px rgba(130, 34, 34, 0.08); background: rgba(255, 255, 255, 0.94); }
.feed-tabs { display: flex; align-items: center; gap: 36px; margin: 0 0 12px; padding: 0; height: 40px; border-bottom: 1px solid #f5dfdf; flex-shrink: 0; }
.feed-tab { position: relative; border: 0; background: transparent; color: #7c5c5c; font-size: 15px; font-weight: 600; cursor: pointer; padding: 0; height: 40px; transition: color 0.2s; }
.feed-tab.active { color: #dc2626; }
.feed-tab.active::after { content: ''; position: absolute; left: 0; right: 0; bottom: 0; height: 2px; border-radius: 999px; background: #dc2626; }
.feed-tab:hover { color: #dc2626; }
.posts-list { display: flex; flex-direction: column; gap: 10px; padding-bottom: 16px; }
.ai-tab-container { display: flex; height: 100%; min-height: 0; border: 1px solid #f0dada; border-radius: 8px; overflow: hidden; }
.loading-container { display: flex; justify-content: center; padding: 40px; }
.empty-state { padding: 40px; }
.pagination { margin-top: 16px; display: flex; justify-content: center; flex-shrink: 0; }
@media (max-width: 1100px) { .community-layout { flex-direction: column; } .community-sidebar { width: 100%; flex-basis: auto; max-height: 260px; } .top-bar-tags { min-width: 0; } }
@media (max-width: 768px) { .community-layout { padding: 0 12px 12px; } .feed-tabs { gap: 24px; overflow-x: auto; } .top-bar { padding: 8px 12px; } }
</style>
