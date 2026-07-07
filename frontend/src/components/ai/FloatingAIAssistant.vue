<template>
  <Teleport to="body">
    <!-- ========== 悬浮按钮 ========== -->
    <button
      ref="btnRef"
      class="floating-btn"
      :class="{ 'is-open': dialogOpen, 'is-dragging': dragging }"
      :style="btnStyle"
      :title="dialogOpen ? '关闭 AI 助手' : '打开 AI 助手'"
      @pointerdown.prevent="onPointerDown"
    >
      <img v-if="logoSrc" :src="logoSrc" alt="AI 助手" class="logo-img" />
      <el-icon v-else class="logo-icon"><ChatDotRound /></el-icon>
    </button>

    <!-- ========== 对话弹窗 ========== -->
    <Transition name="dialog-slide">
      <div v-if="dialogOpen" class="chat-dialog" :style="dialogStyle">
        <!-- 头部 -->
        <div class="dialog-header">
          <div class="header-left">
            <el-icon v-if="showHistory" class="header-back" @click="showHistory = false"><ArrowLeft /></el-icon>
            <span class="header-title">{{ showHistory ? '历史记录' : title }}</span>
            <el-tag v-if="!showHistory" size="small" type="info" class="mock-tag">智闻ai</el-tag>
          </div>
          <div class="header-actions">
            <button v-if="!showHistory" class="header-icon-btn" title="历史记录" @click="openHistory">
              <el-icon><Clock /></el-icon>
            </button>
            <button v-if="!showHistory && messages.length > 0" class="header-icon-btn" title="新建对话" @click="newChat">
              <el-icon><Plus /></el-icon>
            </button>
            <button v-if="!showHistory && messages.length > 0" class="header-icon-btn" title="清空当前对话" @click="clearCurrent">
              <el-icon><Delete /></el-icon>
            </button>
            <button class="header-close" @click="dialogOpen = false">
              <el-icon><Close /></el-icon>
            </button>
          </div>
        </div>

        <!-- ====== 历史记录面板 ====== -->
        <div v-if="showHistory" class="dialog-messages">
          <div v-if="sessions.length === 0" class="empty-chat">
            <el-icon class="empty-icon"><Clock /></el-icon>
            <p class="empty-title">暂无历史记录</p>
            <p class="empty-desc">开始一段对话后，它会自动保存在这里。</p>
            <el-button type="primary" size="small" @click="showHistory = false">开始新对话</el-button>
          </div>
          <div v-else class="history-list">
            <div
              v-for="s in sessions"
              :key="s.id"
              class="history-item"
              @click="loadSession(s.id)"
            >
              <div class="history-item-main">
                <span class="history-title">{{ s.title }}</span>
                <span class="history-preview">{{ s.preview }}</span>
              </div>
              <div class="history-item-tail">
                <span class="history-date">{{ s.dateLabel }}</span>
                <button class="history-del" title="删除" @click.stop="deleteSession(s.id)">
                  <el-icon><Close /></el-icon>
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- ====== 聊天面板 ====== -->
        <template v-else>
          <div ref="msgAreaRef" class="dialog-messages">
            <div v-if="messages.length === 0 && !loading" class="empty-chat">
              <el-icon class="empty-icon"><ChatDotRound /></el-icon>
              <p class="empty-title">AI 新闻助手</p>
              <p class="empty-desc">可以问我新闻内容、热点话题、社区讨论等任何问题。</p>
              <div class="quick-questions">
                <button v-for="q in quickQuestions" :key="q" class="quick-item" @click="send(q)">{{ q }}</button>
              </div>
            </div>
            <template v-else>
              <div v-for="msg in messages" :key="msg.id" :class="['msg-row', msg.role]">
                <div class="msg-bubble">
                  <div class="msg-content">{{ msg.content }}</div>
                  <!-- 来源标签（仅 AI 回复） -->
                  <div v-if="msg.role === 'assistant' && msgSources[msg.id]?.length" class="msg-sources">
                    <span class="sources-label">📎 参考来源</span>
                    <router-link
                      v-for="s in msgSources[msg.id]"
                      :key="s.id"
                      :to="sourceLink(s)"
                      :class="['source-tag', s.relevance]"
                    >
                      {{ sourceLabel(s) }}
                    </router-link>
                  </div>
                  <div class="msg-time">{{ formatTime(msg.timestamp) }}</div>
                </div>
              </div>
              <div v-if="loading" class="msg-row assistant">
                <div class="msg-bubble loading-bubble">
                  <span>AI 思考中...</span>
                  <el-icon class="spin-icon"><Loading /></el-icon>
                </div>
              </div>
            </template>
          </div>

          <!-- 输入区 -->
          <div class="dialog-input-area">
            <div class="input-row">
              <el-input
                v-model="inputText"
                type="textarea"
                :rows="2"
                placeholder="输入你的问题..."
                :disabled="loading"
                @keyup.enter.exact.prevent="handleSend"
              />
              <el-button
                type="primary"
                :loading="loading"
                :disabled="loading || !inputText.trim() || charCount > 1000"
                class="send-btn"
                @click="handleSend"
              >
                <span v-if="!loading">发送</span>
              </el-button>
            </div>
            <div class="input-footer">
              <span :class="['char-count', { 'is-over': charCount > 1000 }]">
                {{ charCount }} / 1000
              </span>
            </div>
          </div>
        </template>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, reactive, computed, nextTick, watch, onBeforeUnmount } from 'vue'
import { useRoute } from 'vue-router'
import { ChatDotRound, Loading, Close, Delete, Clock, Plus, ArrowLeft } from '@element-plus/icons-vue'
import { sendAssistantMessage, type AssistantMessage, type RAGContext, type RAGArticle } from '@/api/aiAssistant'

// ── Types ────────────────────────────────────────────
interface ChatSession {
  id: string
  title: string
  preview: string
  dateLabel: string
  messages: AssistantMessage[]
  createdAt: string
}

/** 消息来源映射: message.id → RAGArticle[] */
const msgSources = ref<Record<string, RAGArticle[]>>({})

// ── Props ──────────────────────────────────────────
withDefaults(defineProps<{ logoSrc?: string; title?: string }>(), { title: 'AI 助手' })

// ── State ─────────────────────────────────────────
const dialogOpen = ref(false)
const inputText = ref('')
const messages = ref<AssistantMessage[]>([])
const loading = ref(false)
const msgAreaRef = ref<HTMLElement>()
const btnRef = ref<HTMLElement>()
const showHistory = ref(false)

// ── localStorage keys ─────────────────────────────
const SESSIONS_KEY = 'llm-news-ai-assistant-sessions'
const POS_KEY = 'llm-news-ai-assistant-position'
const MAX_MSG_COUNT = 200

// ── Session management ─────────────────────────────
const sessions = ref<ChatSession[]>([])

function loadSessions() {
  try {
    const raw = localStorage.getItem(SESSIONS_KEY)
    if (raw) sessions.value = JSON.parse(raw)
  } catch { sessions.value = [] }
}

function saveSessions() {
  try { localStorage.setItem(SESSIONS_KEY, JSON.stringify(sessions.value)) } catch { /* ignore */ }
}

/** 把当前消息存为一个 session */
function saveCurrentAsSession() {
  if (messages.value.length === 0) return
  const firstUser = messages.value.find((m) => m.role === 'user')
  const lastAssistant = [...messages.value].reverse().find((m) => m.role === 'assistant')
  const title = firstUser ? firstUser.content.slice(0, 30) + (firstUser.content.length > 30 ? '…' : '') : '空对话'
  const preview = lastAssistant ? lastAssistant.content.slice(0, 40) + (lastAssistant.content.length > 40 ? '…' : '') : ''
  const d = new Date()
  const dateLabel = `${d.getMonth() + 1}/${d.getDate()} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`

  // 用当前第一条消息的时间作为 createdAt 以保持排序稳定
  const createdAt = messages.value[0]?.timestamp || d.toISOString()

  const session: ChatSession = {
    id: `s_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`,
    title,
    preview,
    dateLabel,
    messages: [...messages.value],
    createdAt,
  }

  // 放到最前面
  sessions.value.unshift(session)
  // 最多保留 50 个 session
  if (sessions.value.length > 50) sessions.value = sessions.value.slice(0, 50)
  saveSessions()
}

function openHistory() {
  // 进入历史前先保存当前对话
  saveCurrentAsSession()
  messages.value = []
  loadSessions()
  showHistory.value = true
}

function loadSession(id: string) {
  const s = sessions.value.find((x) => x.id === id)
  if (!s) return
  messages.value = s.messages
  showHistory.value = false
  scrollBottom()
}

function deleteSession(id: string) {
  sessions.value = sessions.value.filter((x) => x.id !== id)
  saveSessions()
}

function newChat() {
  saveCurrentAsSession()
  messages.value = []
  scrollBottom()
}

function clearCurrent() {
  messages.value = []
}

function loadPosition() {
  try {
    const raw = localStorage.getItem(POS_KEY)
    if (raw) {
      const p = JSON.parse(raw)
      if (typeof p.right === 'number' && typeof p.bottom === 'number') { pos.right = p.right; pos.bottom = p.bottom }
    }
  } catch { /* ignore */ }
}

function savePosition() {
  try { localStorage.setItem(POS_KEY, JSON.stringify({ right: pos.right, bottom: pos.bottom })) } catch { /* ignore */ }
}

// 初始化
loadSessions()
loadPosition()

// ── 拖拽状态 ──────────────────────────────────────
const dragging = ref(false)
const pos = reactive({ right: 70, bottom: 110 })
const btnSize = ref(56)

const charCount = computed(() => inputText.value.replace(/\s/g, '').length)

const btnStyle = computed(() => ({ right: `${pos.right}px`, bottom: `${pos.bottom}px` }))

const dialogStyle = computed(() => {
  const gap = 16
  const btnCenter = window.innerWidth - pos.right - btnSize.value / 2
  const dialogW = 400
  const margin = 24
  let left = btnCenter - dialogW / 2
  left = Math.max(margin, Math.min(left, window.innerWidth - dialogW - margin))
  return { right: 'auto', left: `${left}px`, bottom: `${pos.bottom + btnSize.value + gap}px` }
})

const quickQuestions = [
  '今天有哪些热门新闻？',
  '帮我总结最近的科技动态',
  '这个社区有什么有趣讨论？',
]

// ── 上下文采集 ──────────────────────────────────────
const route = useRoute()

function buildContext(): RAGContext {
  const p = route.path

  if (p.startsWith('/news/') && route.params.id) {
    return { page: 'news-detail', newsId: Number(route.params.id) }
  }
  if (p.startsWith('/community/posts/') && route.params.id) {
    return { page: 'community', postId: Number(route.params.id) }
  }
  if (p.startsWith('/timeline/') && route.params.topicId) {
    return { page: 'timeline', topicId: Number(route.params.topicId) }
  }
  if (p === '/home') {
    return {
      page: 'home',
      categoryId: Number(route.query.category_id) || null,
      searchKeyword: (route.query.keyword as string) || null,
    }
  }
  return { page: 'other' }
}

/** 构建来源跳转链接 */
function sourceLink(a: RAGArticle): string {
  switch (a.type) {
    case 'news': return `/news/${a.id}`
    case 'community_post': return `/community/posts/${a.id}`
    case 'news_comment': return `/news/${a.newsId || 0}`
    case 'post_comment': return `/community/posts/${a.postId || 0}`
    case 'news_topic': return `/timeline/${a.id}`
    default: return '#'
  }
}

function sourceLabel(a: RAGArticle): string {
  const typeMap: Record<string, string> = {
    news: '新闻', community_post: '帖子', news_comment: '新闻评论',
    post_comment: '帖子评论', news_topic: '话题',
  }
  const relMap: Record<string, string> = {
    current: '当前', topic_match: '关联', keyword_match: '搜索',
  }
  return `${typeMap[a.type] || a.type}·${relMap[a.relevance] || a.relevance}`
}

// ── 拖拽逻辑 ──────────────────────────────────────
let dragStart = { x: 0, y: 0, right: 0, bottom: 0 }
let totalMoved = 0

function clamp(v: number, min: number, max: number) { return Math.min(Math.max(v, min), max) }

function onPointerDown(e: PointerEvent) {
  dragStart = { x: e.clientX, y: e.clientY, right: pos.right, bottom: pos.bottom }
  totalMoved = 0
  ;(e.target as HTMLElement).setPointerCapture(e.pointerId)
  document.addEventListener('pointermove', onPointerMove)
  document.addEventListener('pointerup', onPointerUp)
}

function onPointerMove(e: PointerEvent) {
  const dx = dragStart.x - e.clientX
  const dy = dragStart.y - e.clientY
  totalMoved = Math.abs(dx) + Math.abs(dy)
  if (totalMoved > 4) dragging.value = true
  const margin = 8
  pos.right = clamp(dragStart.right + dx, margin, window.innerWidth - btnSize.value - margin)
  pos.bottom = clamp(dragStart.bottom + dy, margin, window.innerHeight - btnSize.value - margin)
}

function onPointerUp(_e: PointerEvent) {
  document.removeEventListener('pointermove', onPointerMove)
  document.removeEventListener('pointerup', onPointerUp)
  dragging.value = false
  if (totalMoved < 5) dialogOpen.value = !dialogOpen.value
}

onBeforeUnmount(() => {
  document.removeEventListener('pointermove', onPointerMove)
  document.removeEventListener('pointerup', onPointerUp)
})

// ── 消息逻辑 ──────────────────────────────────────
function formatTime(ts: string) {
  const d = new Date(ts)
  return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

function makeMsg(role: 'user' | 'assistant', content: string): AssistantMessage {
  return { id: `m_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`, role, content, timestamp: new Date().toISOString() }
}

function scrollBottom() {
  nextTick(() => { const el = msgAreaRef.value; if (el) el.scrollTop = el.scrollHeight })
}

async function handleSend() {
  const text = inputText.value.trim()
  if (!text || loading.value) return
  messages.value.push(makeMsg('user', text))
  inputText.value = ''
  scrollBottom()
  loading.value = true
  try {
    const reply = await sendAssistantMessage({
      messages: messages.value.map((m) => ({ role: m.role, content: m.content })),
      context: buildContext(),
    })
    const replyMsg = makeMsg('assistant', reply.content)
    messages.value.push(replyMsg)
    // 存储来源引用
    if (reply.sources && reply.sources.length > 0) {
      msgSources.value[replyMsg.id] = reply.sources
    }
  } catch (err: any) {
    const reason = err?.message || String(err)
    messages.value.push(makeMsg('assistant', `请求失败：${reason}。请稍后重试。`))
  } finally {
    loading.value = false
    scrollBottom()
  }
}

function send(text: string) { inputText.value = text; handleSend() }

watch(() => messages.value.length, () => scrollBottom())
watch(dragging, (val) => { if (!val) savePosition() })
</script>

<style scoped>
.floating-btn {
  position: fixed; z-index: 9998; width: 56px; height: 56px; border-radius: 50%;
  border: none; background: var(--color-bg-card);
  box-shadow: 0 4px 16px rgba(0,0,0,.12), 0 2px 6px rgba(0,0,0,.06);
  cursor: grab; display: flex; align-items: center; justify-content: center;
  transition: transform .2s, box-shadow .2s; overflow: hidden; padding: 0;
  touch-action: none; user-select: none; -webkit-user-select: none;
}
.floating-btn:hover { transform: scale(1.08); box-shadow: 0 6px 24px rgba(0,0,0,.16), 0 2px 8px rgba(0,0,0,.08); }
.floating-btn:active { transform: scale(.96); }
.floating-btn.is-dragging { cursor: grabbing; transform: scale(1.12) !important; box-shadow: 0 8px 32px rgba(0,0,0,.22), 0 4px 12px rgba(0,0,0,.1) !important; opacity: .9; }
.floating-btn.is-open { background: var(--color-primary); color: #fff; }
.logo-img { width: 100%; height: 100%; object-fit: cover; border-radius: 50%; pointer-events: none; }
.logo-icon { font-size: 24px; color: var(--color-primary); pointer-events: none; }
.floating-btn.is-open .logo-icon { color: #fff; }

.chat-dialog {
  position: fixed; z-index: 9999; width: 400px; max-width: calc(100vw - 48px);
  height: 540px; max-height: calc(100vh - 140px);
  background: var(--color-bg-card); border: 1px solid var(--color-border);
  border-radius: 12px; box-shadow: 0 12px 40px rgba(0,0,0,.14), 0 4px 12px rgba(0,0,0,.08);
  display: flex; flex-direction: column; overflow: hidden;
}

.dialog-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 14px 16px; border-bottom: 1px solid var(--color-border-light); flex-shrink: 0;
}
.header-left { display: flex; align-items: center; gap: 8px; }
.header-title { font-size: 15px; font-weight: 600; color: var(--color-text-primary); }
.header-back { font-size: 18px; color: var(--color-text-secondary); cursor: pointer; padding: 2px; border-radius: 4px; }
.header-back:hover { color: var(--color-primary); background: var(--color-primary-soft); }
.mock-tag { font-size: 11px; opacity: .6; }
.header-actions { display: flex; align-items: center; gap: 2px; }
.header-icon-btn,
.header-close {
  border: none; background: none; cursor: pointer; color: var(--color-text-muted);
  font-size: 16px; padding: 4px; border-radius: 4px;
  display: flex; align-items: center; justify-content: center;
  transition: color .15s, background .15s;
}
.header-icon-btn:hover,
.header-close:hover { color: var(--color-text-primary); background: var(--color-bg-hover); }

.dialog-messages { flex: 1; overflow-y: auto; padding: 14px 16px; display: flex; flex-direction: column; gap: 12px; }

/* ── 历史记录列表 ─────────────────────────────── */
.history-list { display: flex; flex-direction: column; gap: 2px; }
.history-item {
  display: flex; align-items: center; justify-content: space-between;
  padding: 12px 14px; border-radius: 8px; cursor: pointer; transition: background .15s;
}
.history-item:hover { background: var(--color-bg-hover); }
.history-item-main { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 4px; }
.history-title { font-size: 14px; font-weight: 500; color: var(--color-text-primary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.history-preview { font-size: 12px; color: var(--color-text-muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.history-item-tail { display: flex; align-items: center; gap: 8px; flex-shrink: 0; margin-left: 8px; }
.history-date { font-size: 11px; color: var(--color-text-muted); white-space: nowrap; }
.history-del { border: none; background: none; cursor: pointer; color: var(--color-text-muted); font-size: 14px; padding: 2px; border-radius: 4px; display: flex; opacity: 0; transition: opacity .15s, color .15s; }
.history-item:hover .history-del { opacity: 1; }
.history-del:hover { color: var(--color-primary); }

/* ── 空状态 ──────────────────────────────────── */
.empty-chat {
  flex: 1; display: flex; flex-direction: column; align-items: center;
  justify-content: center; text-align: center; padding: 24px;
}
.empty-icon { font-size: 42px; color: var(--color-primary); margin-bottom: 10px; }
.empty-title { margin: 0 0 6px; font-size: 17px; font-weight: 600; color: var(--color-text-primary); }
.empty-desc { margin: 0 0 18px; font-size: 13px; color: var(--color-text-secondary); line-height: 1.6; }
.quick-questions { display: flex; flex-wrap: wrap; gap: 8px; justify-content: center; }
.quick-item {
  padding: 6px 14px; border-radius: 20px; border: 1px solid var(--color-border);
  background: var(--color-bg); color: var(--color-text-secondary); font-size: 13px;
  cursor: pointer; transition: all .15s;
}
.quick-item:hover { border-color: var(--color-primary); color: var(--color-primary); background: var(--color-primary-soft); }

/* ── 消息气泡 ────────────────────────────────── */
.msg-row { display: flex; max-width: 86%; }
.msg-row.user { align-self: flex-end; }
.msg-row.assistant { align-self: flex-start; }
.msg-bubble { display: flex; flex-direction: column; gap: 3px; }
.msg-content {
  padding: 10px 14px; border-radius: 12px; font-size: 14px; line-height: 1.6;
  white-space: pre-wrap; word-break: break-word;
}
.msg-row.user .msg-content { background: var(--color-primary); color: #fff; border-bottom-right-radius: 4px; }
.msg-row.assistant .msg-content { background: var(--color-bg); color: var(--color-text-primary); border-bottom-left-radius: 4px; }
.msg-time { font-size: 11px; color: var(--color-text-muted); padding: 0 4px; }
.msg-row.user .msg-time { text-align: right; }

/* 来源标签 */
.msg-sources {
  display: flex; flex-wrap: wrap; align-items: center; gap: 5px;
  margin-top: 4px; padding-top: 4px;
  border-top: 1px solid var(--color-border-light);
}
.sources-label {
  font-size: 11px; color: var(--color-text-muted); margin-right: 2px;
}
.source-tag {
  display: inline-block; padding: 2px 8px; border-radius: 10px;
  font-size: 11px; text-decoration: none; cursor: pointer;
  white-space: nowrap; max-width: 120px; overflow: hidden; text-overflow: ellipsis;
  transition: opacity .15s;
  border: 1px solid;
}
.source-tag.current {
  background: var(--color-primary-soft); color: var(--color-primary); border-color: var(--color-primary-light);
}
.source-tag.topic_match {
  background: #eff6ff; color: #2563eb; border-color: #bfdbfe;
}
.source-tag.keyword_match {
  background: #f5f3ff; color: #7c3aed; border-color: #ddd6fe;
}
.source-tag:hover { opacity: .75; }

.loading-bubble {
  flex-direction: row !important; align-items: center; gap: 8px;
  padding: 10px 14px; background: var(--color-bg); border-radius: 12px;
  border-bottom-left-radius: 4px; font-size: 14px; color: var(--color-text-secondary);
}
.spin-icon { animation: asst-spin 1s linear infinite; }
@keyframes asst-spin { to { transform: rotate(360deg); } }

/* ── 输入区 ──────────────────────────────────── */
.dialog-input-area { padding: 10px 14px 14px; border-top: 1px solid var(--color-border-light); flex-shrink: 0; }
.input-row { display: flex; gap: 8px; align-items: flex-end; }
.input-row :deep(.el-textarea) { flex: 1; }
.input-footer { display: flex; justify-content: flex-end; margin-top: 4px; }
.char-count { font-size: 12px; color: var(--color-text-muted); transition: color .15s; }
.char-count.is-over { color: var(--color-primary); font-weight: 600; }
.send-btn { height: 40px; min-width: 64px; }

/* ── 动画 ────────────────────────────────────── */
.dialog-slide-enter-active { transition: all .25s cubic-bezier(.4,0,.2,1); }
.dialog-slide-leave-active { transition: all .2s cubic-bezier(.4,0,1,1); }
.dialog-slide-enter-from { opacity: 0; transform: translateY(12px) scale(.95); }
.dialog-slide-leave-to { opacity: 0; transform: translateY(8px) scale(.97); }
</style>
