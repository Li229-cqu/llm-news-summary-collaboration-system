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
        <el-tag :type="selectedTags.length === 0 ? 'primary' : 'info'" effect="light" class="filter-tag" @click="selectedTags = []">全部</el-tag>
        <el-tag v-for="tag in availableTags" :key="tag.name" :type="selectedTags.includes(tag.name) ? 'primary' : 'info'" effect="light" class="filter-tag" @click="toggleTag(tag.name)">{{ tag.name }}</el-tag>
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
            <button v-for="tab in feedTabs" :key="tab.name" :class="['feed-tab', { active: activeFeedTab === tab.name }]" @click="activeFeedTab = tab.name">{{ tab.label }}</button>
          </div>
          <div class="scroll-area">
            <template v-if="activeFeedTab === 'recommend'">
              <div v-if="loadingPosts" class="loading-container"><el-spinner /></div>
              <div v-else-if="filteredPosts.length === 0" class="empty-state"><el-empty :description="searchKeyword ? '未找到相关帖子' : '暂无帖子，快来发布第一条吧'" /></div>
              <div v-else class="posts-list">
                <PostCard v-for="post in filteredPosts" :key="post.id" :post="post" @view="handleViewPost" @like="handleLike" @favorite="handleFavorite" @comment="handleViewPost" @open-related-news="handleOpenRelatedNews" />
              </div>
              <el-pagination v-if="postTotal > pageSize" :current-page="currentPage" :page-size="pageSize" :total="postTotal" layout="prev, pager, next" @current-change="loadPosts" class="pagination" />
            </template>
            <div v-else-if="activeFeedTab === 'ai'" class="ai-tab-container">
              <AISessionList :sessions="aiSessions" :active-session-id="aiActiveSessionId" :collapsed="aiSessionCollapsed" :loading="aiLoadingSessions" @select="handleAiSelectSession" @create="handleAiCreateSession" @delete="handleAiDeleteSession" @toggle-collapse="aiSessionCollapsed = !aiSessionCollapsed" />
              <AIChatPanel :active-session="aiActiveSession" :messages="aiCurrentMessages" :loading-messages="aiLoadingMessages" :sending="aiSending" @send="handleAiSend" @first-question="handleAiCreateSession" />
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
import { computed, ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getPostList, toggleLike, toggleFavorite, unfavoritePost, getHotSearch, getAvailableTags, createCommunityAiSession, getCommunityAiSessions, getCommunityAiSessionDetail, sendCommunityAiMessage, deleteCommunityAiSession, type CommunityPost, type HotSearchItem, type TagCount, type CommunityAiSession, type CommunityAiMessage } from '@/api/community'
import { useUserStore } from '@/stores/user'
import PostCard from '@/components/community/PostCard.vue'
import HotTopicsSidebar from '@/components/community/HotTopicsSidebar.vue'
import AISessionList from '@/components/community/AISessionList.vue'
import AIChatPanel from '@/components/community/AIChatPanel.vue'
import MyInteractionsPanel from '@/components/community/MyInteractionsPanel.vue'
import MyPostsPanel from '@/components/community/MyPostsPanel.vue'

const router = useRouter()
const userStore = useUserStore()

// ─── Post List ──
const posts = ref<CommunityPost[]>([])
const loadingPosts = ref(false)
const currentPage = ref(1)
const pageSize = ref(10)
const postTotal = ref(0)
const searchKeyword = ref('')
const selectedTags = ref<string[]>([])

const filteredPosts = computed(() => {
  if (selectedTags.value.length === 0) return posts.value
  return posts.value.filter(p => selectedTags.value.some(t => (p.tags || []).includes(t)))
})

function toggleTag(name: string) {
  const i = selectedTags.value.indexOf(name)
  if (i >= 0) selectedTags.value.splice(i, 1)
  else selectedTags.value.push(name)
}

async function loadPosts(page = 1) {
  currentPage.value = page; loadingPosts.value = true
  try {
    const result = await getPostList({ page, page_size: pageSize.value, keyword: searchKeyword.value.trim() || undefined })
    posts.value = result.list.map(p => ({ ...p, liked: Boolean(p.liked ?? (p as any).is_liked ?? false) }))
    postTotal.value = result.total
  } catch { posts.value = []; postTotal.value = 0; ElMessage.error('获取帖子列表失败') } finally { loadingPosts.value = false }
}
function handleSearch() { currentPage.value = 1; loadPosts(1) }
function handleSearchClear() { searchKeyword.value = ''; currentPage.value = 1; loadPosts(1) }
let searchTimer: ReturnType<typeof setTimeout> | null = null
watch(searchKeyword, () => { if (searchTimer) clearTimeout(searchTimer); searchTimer = setTimeout(() => { currentPage.value = 1; loadPosts(1) }, 500) })

// ─── Tags ──
const availableTags = ref<TagCount[]>([])
async function loadAvailableTags() {
  try { availableTags.value = await getAvailableTags() } catch { availableTags.value = [{ name: '时政', count: 0 }, { name: '经济', count: 0 }, { name: '科技', count: 0 }, { name: '教育', count: 0 }, { name: '军事', count: 0 }, { name: '社会', count: 0 }, { name: '国际', count: 0 }, { name: '体育', count: 0 }, { name: '娱乐', count: 0 }, { name: '健康', count: 0 }] }
}

// ─── Tabs ──
const activeFeedTab = ref<'recommend' | 'ai' | 'interactions' | 'posts'>('recommend')
const feedTabs = [ { name: 'recommend', label: '推荐讨论' }, { name: 'ai', label: 'AI 问答' }, { name: 'interactions', label: '我的互动' }, { name: 'posts', label: '我的帖子' } ] as const

// ─── AI ──
const aiSessions = ref<CommunityAiSession[]>([]); const aiActiveSessionId = ref<number | null>(null); const aiActiveSession = ref<CommunityAiSession | null>(null); const aiCurrentMessages = ref<CommunityAiMessage[]>([]); const aiLoadingSessions = ref(false); const aiLoadingMessages = ref(false); const aiSending = ref(false); const aiSessionCollapsed = ref(false)
watch(activeFeedTab, (tab) => { if (tab === 'ai') loadAiSessions() })
async function loadAiSessions() { aiLoadingSessions.value = true; try { const res = await getCommunityAiSessions({ page: 1, page_size: 50 }); aiSessions.value = res.list || []; if (aiSessions.value.length > 0) { if (!aiActiveSessionId.value || !aiSessions.value.some(s => s.id === aiActiveSessionId.value)) aiActiveSessionId.value = aiSessions.value[0].id; await loadAiSessionDetail(aiActiveSessionId.value) } else { aiActiveSessionId.value = null; aiActiveSession.value = null; aiCurrentMessages.value = [] } } catch { aiSessions.value = [] } finally { aiLoadingSessions.value = false } }
async function loadAiSessionDetail(sessionId: number) { if (!sessionId) return; aiLoadingMessages.value = true; try { const res = await getCommunityAiSessionDetail(sessionId); aiActiveSession.value = res.session; aiCurrentMessages.value = res.messages || [] } catch { ElMessage.error('获取会话详情失败') } finally { aiLoadingMessages.value = false } }
async function handleAiCreateSession() { try { const res = await createCommunityAiSession({}); aiSessions.value.unshift(res.session); aiActiveSessionId.value = res.session.id; aiActiveSession.value = res.session; aiCurrentMessages.value = res.messages || [] } catch { ElMessage.error('创建会话失败') } }
async function handleAiSelectSession(sessionId: number) { aiActiveSessionId.value = sessionId; await loadAiSessionDetail(sessionId) }
async function handleAiSend(question: string) {
  if (aiActiveSessionId.value) { aiSending.value = true; try { const res = await sendCommunityAiMessage(aiActiveSessionId.value, { question }); aiCurrentMessages.value.push(res.user_message); aiCurrentMessages.value.push(res.assistant_message); aiActiveSession.value = res.session; const idx = aiSessions.value.findIndex(s => s.id === res.session.id); if (idx !== -1) aiSessions.value[idx] = res.session } catch { ElMessage.error('消息发送失败') } finally { aiSending.value = false } }
  else { aiSending.value = true; try { const res = await createCommunityAiSession({ question }); aiSessions.value.unshift(res.session); aiActiveSessionId.value = res.session.id; aiActiveSession.value = res.session; aiCurrentMessages.value = res.messages || [] } catch { ElMessage.error('发送失败') } finally { aiSending.value = false } }
}
async function handleAiDeleteSession(sessionId: number) { try { await deleteCommunityAiSession(sessionId); aiSessions.value = aiSessions.value.filter(s => s.id !== sessionId); if (aiActiveSessionId.value === sessionId) { if (aiSessions.value.length > 0) { aiActiveSessionId.value = aiSessions.value[0].id; await loadAiSessionDetail(aiActiveSessionId.value) } else { aiActiveSessionId.value = null; aiActiveSession.value = null; aiCurrentMessages.value = [] } } } catch { ElMessage.error('删除会话失败') } }

// ─── Hot Search ──
const hotSearchList = ref<HotSearchItem[]>([]); const loadingHotSearch = ref(false)
async function loadHotSearch() { loadingHotSearch.value = true; try { hotSearchList.value = await getHotSearch({ limit: 10 }) } finally { loadingHotSearch.value = false } }
function handleHotSearchClick(item: HotSearchItem) { if (item.target_type === 'post' || item.target_type === 'community_post') router.push(`/community/posts/${item.target_id}`); else { searchKeyword.value = item.keyword; currentPage.value = 1; loadPosts(1) } }

// ─── Like / Favorite ──
async function handleLike(post: CommunityPost) { try { const r = await toggleLike(post.id); post.likes = r.count; post.liked = r.liked } catch { console.error('点赞失败') } }
async function handleFavorite(post: CommunityPost, event: Event) { event.stopPropagation(); try { if (post.is_favorited) { const r = await unfavoritePost(post.id); post.is_favorited = false; post.favorite_count = r.favorite_count } else { const r = await toggleFavorite(post.id); post.is_favorited = r.is_favorited; post.favorite_count = r.favorite_count } } catch { console.error('收藏操作失败') } }

// ─── Nav ──
function handleViewPost(post: CommunityPost) { router.push(`/community/posts/${post.id}`) }
function handleOpenMyPostDetail(postId: number) { router.push(`/community/posts/${postId}`) }
function handleOpenRelatedNews(post: CommunityPost) { if (post.related_news_id) router.push(`/news/${post.related_news_id}`) }

onMounted(() => { if (!userStore.userInfo) userStore.loadFromStorage(); loadPosts(); loadHotSearch(); loadAvailableTags() })
</script>

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
