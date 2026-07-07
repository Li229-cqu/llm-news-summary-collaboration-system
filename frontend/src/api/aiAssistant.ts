/**
 * AI 浮动助手 API — 前端调 LLM + 后端做多资源检索（RAG）
 */

import request from './request'

// ── 类型 ──────────────────────────────────────────

export interface AssistantMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: string
}

/** 用户当前浏览页面上下文 */
export interface RAGContext {
  page: string
  newsId?: number | null
  categoryId?: number | null
  topicId?: number | null
  searchKeyword?: string | null
  postId?: number | null
}

export interface AssistantChatRequest {
  messages: Array<{ role: 'user' | 'assistant'; content: string }>
  stream?: boolean
  context?: RAGContext
}

export interface RAGArticle {
  type: 'news' | 'community_post' | 'news_comment' | 'post_comment' | 'news_topic'
  id: number
  title: string | null
  content: string
  summary: string | null
  source: string | null
  publishTime: string | null
  relevance: 'current' | 'topic_match' | 'keyword_match'
  newsId?: number | null
  postId?: number | null
  topicId?: number | null
  categoryId?: number | null
}

export interface AssistantChatResponse {
  id: string
  content: string
  sources?: RAGArticle[]
}

// ── 常量 ──────────────────────────────────────────

// 走 Vite 代理避免跨域问题
const LLM_URL = '/llm-api/v1/chat/completions'
const MODEL = 'qwen-lora'

/** 资源类型 → 中文标签 */
const TYPE_LABELS: Record<string, string> = {
  news: '新闻',
  community_post: '社区帖子',
  news_comment: '新闻评论',
  post_comment: '帖子评论',
  news_topic: '话题',
}

/** 关联程度 → 中文标签 */
const REL_LABELS: Record<string, string> = {
  current: '当前浏览',
  topic_match: '话题关联',
  keyword_match: '关键词匹配',
}

// ── 检索 API（调后端） ────────────────────────────

/**
 * 请求后端检索与问题相关的多资源内容
 */
export async function searchArticles(
  question: string,
  context: RAGContext,
): Promise<{ current: RAGArticle | null; articles: RAGArticle[] }> {
  try {
    const result: any = await request.post('/api/assistant/search', {
      question,
      context,
    })
    return {
      current: result?.current || null,
      articles: result?.articles || [],
    }
  } catch {
    // 检索失败不阻断对话，返回空结果
    return { current: null, articles: [] }
  }
}

// ── Prompt 构建 ───────────────────────────────────

/**
 * 将检索结果拼接为发送给 LLM 的 messages
 */
function buildRAGMessages(
  question: string,
  data: { current: RAGArticle | null; articles: RAGArticle[] },
): Array<{ role: string; content: string }> {
  // 组装所有文章（current 排第一，最多取 5 篇）
  const allArticles: RAGArticle[] = []
  if (data.current) allArticles.push(data.current)
  allArticles.push(...data.articles.slice(0, 5))

  let contextBlock = ''
  if (allArticles.length > 0) {
    contextBlock = '\n\n【以下是从数据库中检索到的相关内容】\n\n'
    allArticles.forEach((a, i) => {
      const typeLabel = TYPE_LABELS[a.type] || a.type
      const relLabel = REL_LABELS[a.relevance] || a.relevance
      const heading = a.title || (a.content || '').slice(0, 30)
      contextBlock += `### ${i + 1}. [${typeLabel}] ${heading}（${relLabel}）\n`
      if (a.source) contextBlock += `来源/作者：${a.source}\n`
      if (a.publishTime) contextBlock += `时间：${a.publishTime}\n`
      contextBlock += `内容：${(a.content || a.summary || '').slice(0, 300)}\n\n`
    })
  }

  // Qwen-Lora 模型不支持 system 角色，将指令合并到 user 消息中
  const instruction = '【指令】你是智闻平台的 AI 新闻助手。请严格基于以下检索到的内容回答用户问题，不要编造。如果内容与问题不相关，如实告知。回复简洁。注意：不要使用markdown格式（如#、**等标记），用纯文本回复。用户的指令在最后一行。\n\n'

  return [
    { role: 'user', content: instruction + contextBlock + question },
  ]
}

// ── 主对话 API ────────────────────────────────────

export async function sendAssistantMessage(
  payload: AssistantChatRequest,
): Promise<AssistantChatResponse> {
  const t0 = Date.now()
  const lastUserMsg = [...payload.messages].reverse().find((m) => m.role === 'user')
  const question = lastUserMsg?.content || ''

  // ── ① 调后端检索 ──
  console.group('%c[RAG 步骤1] 前端 → 后端检索', 'color:#2563eb;font-weight:bold')
  console.log('📤 请求: POST /api/assistant/search')
  console.log('📝 问题:', question)
  console.log('📍 上下文:', JSON.stringify(payload.context, null, 2))
  let ragData: { current: RAGArticle | null; articles: RAGArticle[] } = {
    current: null,
    articles: [],
  }
  if (payload.context) {
    ragData = await searchArticles(question, payload.context)
  }
  if (ragData.current) {
    console.log('📥 当前资源:', ragData.current.type, `"${ragData.current.title}"`)
  } else {
    console.log('📥 当前资源: 无')
  }
  console.log('📥 检索结果 (%d 条):', ragData.articles.length)
  ragData.articles.forEach((a, i) => {
    console.log(`  ${i + 1}. [${a.type}][${a.relevance}] ${a.title || (a.content || '').slice(0, 50)}`)
  })
  console.groupEnd()

  // ── ② 拼接 RAG Prompt ──
  const ragMessages = buildRAGMessages(question, ragData)

  console.group('%c[RAG 步骤2] 前端 → LLM', 'color:#7c3aed;font-weight:bold')
  console.log('LLM URL:', LLM_URL)
  console.log('模型:', MODEL)
  console.log('发送的 messages (%d 条):', ragMessages.length)
  ragMessages.forEach((m, i) => {
    console.log(`─── 消息 #${i + 1} [${m.role}] ───`)
    console.log(m.content)
  })
  console.groupEnd()

  // ══════ 写入调试日志 (localStorage) ══════
  const debugEntry: any = {
    timestamp: new Date().toLocaleTimeString('zh-CN'),
    question,
    context: payload.context || null,
    currentArticle: ragData.current,
    retrievedArticles: ragData.articles,
    llmRequest: {
      url: LLM_URL,
      model: MODEL,
      messages: ragMessages.map(m => ({ role: m.role, content: m.content })),
    },
    llmResponse: null,
    llmError: null,
    llmResponseTimeMs: null,
  }

  // ── ③ 调 LLM API ──
  let response: Response
  try {
    response = await fetch(LLM_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ model: MODEL, messages: ragMessages }),
    })
  } catch (err: any) {
    console.error('[RAG 步骤3] LLM 网络错误:', err.message)
    debugEntry.llmError = `网络错误: ${err.message}`
    debugEntry.llmResponseTimeMs = Date.now() - t0
    _appendDebugLog(debugEntry)
    throw err
  }

  if (!response.ok) {
    console.error('[RAG 步骤3] LLM HTTP 错误:', response.status, response.statusText)
    debugEntry.llmError = `HTTP ${response.status} ${response.statusText}`
    debugEntry.llmResponseTimeMs = Date.now() - t0
    _appendDebugLog(debugEntry)
    throw new Error(`LLM 请求失败: ${response.status} ${response.statusText}`)
  }

  const data = await response.json()
  const content = data?.choices?.[0]?.message?.content || '（无回复内容）'

  console.group('%c[RAG 步骤3] LLM 响应 ✅', 'color:#16a34a;font-weight:bold')
  console.log('耗时:', Date.now() - t0, 'ms')
  console.log('回复内容:', content)
  console.groupEnd()

  debugEntry.llmResponse = content
  debugEntry.llmResponseTimeMs = Date.now() - t0
  _appendDebugLog(debugEntry)

  return {
    id: `msg_${Date.now()}`,
    content,
    sources: ragData.articles,
  }
}

/** 追加调试日志到 sessionStorage */
function _appendDebugLog(entry: any) {
  try {
    const key = 'llm-rag-debug-log'
    const raw = localStorage.getItem(key)
    const logs: any[] = raw ? JSON.parse(raw) : []
    logs.push(entry)
    if (logs.length > 10) logs.shift()
    localStorage.setItem(key, JSON.stringify(logs))
    console.log('[RAG Debug] 日志已写入 localStorage · 共', logs.length, '条', entry)
  } catch (e) { console.warn('[RAG Debug] 写入失败:', e) }
}
