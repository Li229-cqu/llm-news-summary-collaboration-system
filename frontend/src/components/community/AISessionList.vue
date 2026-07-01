<template>
  <div class="ai-session-list" :class="{ collapsed }">
    <div class="session-list-header">
      <div class="header-title-area">
        <el-button
          class="collapse-btn"
          :icon="collapsed ? 'Expand' : 'Fold'"
          text
          @click="$emit('toggleCollapse')"
        />
        <span v-show="!collapsed" class="header-title">我的会话</span>
      </div>
      <el-button
        v-show="!collapsed"
        type="primary"
        size="small"
        :icon="Plus"
        @click="$emit('create')"
      >
        新建会话
      </el-button>
    </div>

    <div v-if="!collapsed" class="session-list-body">
      <div v-if="loading" class="loading-area">
        <el-spinner />
      </div>
      <div v-else-if="sessions.length === 0" class="empty-area">
        <span>暂无会话</span>
        <el-button text type="primary" @click="$emit('create')">开始新会话</el-button>
      </div>
      <div v-else class="session-items">
        <div
          v-for="session in sessions"
          :key="session.id"
          :class="['session-item', { active: session.id === activeSessionId }]"
          @click="$emit('select', session.id)"
        >
          <div class="session-item-top">
            <span class="session-title">{{ session.title }}</span>
            <el-button
              text
              size="small"
              type="danger"
              class="delete-btn"
              @click.stop="handleDelete(session)"
            >
              <el-icon><Delete /></el-icon>
            </el-button>
          </div>
          <div class="session-item-preview">
            {{ session.last_message_preview || '暂无消息' }}
          </div>
          <div class="session-item-meta">
            {{ formatTime(session.last_message_at || session.created_at) }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Delete, Plus } from '@element-plus/icons-vue'
import { ElMessageBox } from 'element-plus'
import type { CommunityAiSession } from '@/api/community'

defineProps<{
  sessions: CommunityAiSession[]
  activeSessionId: number | null
  collapsed: boolean
  loading: boolean
}>()

const emit = defineEmits<{
  (e: 'select', sessionId: number): void
  (e: 'create'): void
  (e: 'delete', sessionId: number): void
  (e: 'toggleCollapse'): void
}>()

function handleDelete(session: CommunityAiSession) {
  ElMessageBox.confirm(`确定删除会话「${session.title}」吗？`, '删除会话', {
    confirmButtonText: '删除',
    cancelButtonText: '取消',
    type: 'warning',
  }).then(() => {
    emit('delete', session.id)
  }).catch(() => {})
}

function formatTime(timeStr: string | null | undefined) {
  if (!timeStr) return ''
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
.ai-session-list {
  display: flex;
  flex-direction: column;
  border-right: 1px solid #e3edf9;
  background: #fafcff;
  transition: width 0.25s ease;
  width: 280px;
  flex-shrink: 0;
}
.ai-session-list.collapsed {
  width: 48px;
}

.session-list-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px;
  border-bottom: 1px solid #e3edf9;
  gap: 8px;
}

.header-title-area {
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
}

.collapse-btn {
  flex-shrink: 0;
}

.header-title {
  font-size: 15px;
  font-weight: 700;
  color: #1f2937;
  white-space: nowrap;
}

.session-list-body {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.loading-area, .empty-area {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 32px 8px;
  color: #9ca3af;
  font-size: 13px;
}

.session-items {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.session-item {
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.15s;
}
.session-item:hover {
  background: #fef2f2;
}
.session-item.active {
  background: #fee2e2;
}

.session-item-top {
  display: flex;
  align-items: center;
  gap: 6px;
}

.session-title {
  flex: 1;
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.delete-btn {
  flex-shrink: 0;
  opacity: 0;
  transition: opacity 0.15s;
}
.session-item:hover .delete-btn {
  opacity: 1;
}

.session-item-preview {
  font-size: 12px;
  color: #6b7280;
  margin-top: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.session-item-meta {
  font-size: 11px;
  color: #9ca3af;
  margin-top: 2px;
}
</style>
