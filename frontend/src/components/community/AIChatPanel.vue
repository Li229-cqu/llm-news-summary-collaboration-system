<template>
  <div class="ai-chat-panel">
    <!-- 空状态 -->
    <div v-if="!activeSession && !loadingMessages" class="empty-state">
      <div class="empty-content">
        <el-icon class="empty-icon"><ChatLineSquare /></el-icon>
        <h3 class="empty-title">AI 问答</h3>
        <p class="empty-desc">
          AI 新闻助手可以帮你了解新闻内容、热点话题和社区讨论。
        </p>
        <el-button type="primary" @click="handleFirstQuestion">
          开始提问
        </el-button>
      </div>
    </div>

    <!-- 聊天区域 -->
    <template v-else>
      <div ref="messageContainerRef" class="message-area">
        <div v-if="loadingMessages" class="loading-area">
          <el-spinner />
        </div>
        <template v-else>
          <div
            v-for="msg in messages"
            :key="msg.id"
            :class="['message-row', msg.role]"
          >
            <div v-if="msg.role === 'assistant'" class="avatar-col">
              <el-avatar :size="32">
                <el-icon><ChatLineSquare /></el-icon>
              </el-avatar>
            </div>
            <div v-else class="avatar-col user-avatar-col">
              <el-avatar :size="32" :src="userAvatar" />
            </div>
            <!-- loading 消息：带旋转图标 -->
            <div v-if="(msg as any).loading" class="message-bubble thinking-bubble">
              <span class="thinking-text">AI 正在思考...</span>
              <el-icon class="thinking-icon"><Loading /></el-icon>
            </div>
            <!-- 普通消息 -->
            <div v-else class="message-bubble">
              <div class="message-content">{{ msg.content }}</div>
              <div class="message-time">{{ formatTime(msg.created_at) }}</div>
            </div>
          </div>
        </template>
      </div>

      <!-- 输入区域 -->
      <div class="input-area">
        <el-input
          v-model="inputText"
          type="textarea"
          :rows="2"
          placeholder="输入你的问题..."
          maxlength="500"
          show-word-limit
          :disabled="sending"
          @keyup.enter.prevent="handleSend"
        />
        <el-button
          type="primary"
          :loading="sending"
          :disabled="sending || !inputText.trim()"
          @click="handleSend"
          class="send-btn"
        >
          发送
        </el-button>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, watch } from 'vue'
import { ChatLineSquare, Loading } from '@element-plus/icons-vue'
import type { CommunityAiSession, CommunityAiMessage } from '@/api/community'

const props = defineProps<{
  activeSession: CommunityAiSession | null
  messages: CommunityAiMessage[]
  loadingMessages: boolean
  sending: boolean
  userAvatar?: string
}>()

const emit = defineEmits<{
  (e: 'send', question: string): void
  (e: 'firstQuestion'): void
}>()

const inputText = ref('')
const messageContainerRef = ref<HTMLElement>()

function handleSend() {
  const text = inputText.value.trim()
  if (!text) return
  inputText.value = ''
  emit('send', text)
}

function handleFirstQuestion() {
  emit('firstQuestion')
}

function scrollToBottom() {
  nextTick(() => {
    if (messageContainerRef.value) {
      messageContainerRef.value.scrollTop = messageContainerRef.value.scrollHeight
    }
  })
}

// 自动滚动到最新消息
watch(
  () => props.messages.length,
  () => scrollToBottom(),
)
watch(
  () => props.sending,
  (val) => {
    if (val) scrollToBottom()
  },
)

function formatTime(timeStr: string) {
  const date = new Date(timeStr)
  return date.toLocaleString('zh-CN', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}
</script>

<style scoped>
.ai-chat-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 480px;
}

/* ── Empty State ── */
.empty-state {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.empty-content {
  text-align: center;
  padding: 48px 32px;
  max-width: 420px;
}

.empty-icon {
  font-size: 56px;
  color: #dc2626;
  margin-bottom: 16px;
}

.empty-title {
  font-size: 22px;
  font-weight: 700;
  color: #1f2937;
  margin: 0 0 12px;
}

.empty-desc {
  font-size: 15px;
  color: #6b7280;
  line-height: 1.7;
  margin: 0 0 24px;
}

/* ── Message Area ── */
.ai-chat-panel { flex: 1; min-width: 0; }
.message-area {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.loading-area {
  display: flex;
  justify-content: center;
  padding: 48px;
}

.message-row {
  display: flex;
  gap: 10px;
  max-width: 85%;
}
.message-row.user {
  align-self: flex-end;
  flex-direction: row-reverse;
}
.message-row.assistant {
  align-self: flex-start;
}

.avatar-col {
  flex-shrink: 0;
}

.message-bubble {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.message-row.user .message-bubble {
  align-items: flex-end;
}

.message-content {
  padding: 10px 14px;
  border-radius: 12px;
  font-size: 14px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
  max-width: 100%;
  overflow-wrap: break-word;
}
.message-row.user .message-content {
  background: #dc2626;
  color: #fff;
  border-bottom-right-radius: 4px;
}
.message-row.assistant .message-content {
  background: #f0f4f9;
  color: #1f2937;
  border-bottom-left-radius: 4px;
}

.message-time {
  font-size: 11px;
  color: #9ca3af;
  padding: 0 4px;
}

.thinking-bubble {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  background: #f0f4f9;
  border-radius: 12px;
  border-bottom-left-radius: 4px;
}

.thinking-text {
  font-size: 14px;
  color: #6b7280;
}

.thinking-icon {
  font-size: 16px;
  color: #6b7280;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* ── Input Area ── */
.input-area {
  display: flex;
  gap: 10px;
  padding: 12px 16px;
  border-top: 1px solid #e3edf9;
  align-items: flex-end;
}

.input-area :deep(.el-textarea) {
  flex: 1;
}

.send-btn {
  height: 44px;
  min-width: 80px;
}
</style>
