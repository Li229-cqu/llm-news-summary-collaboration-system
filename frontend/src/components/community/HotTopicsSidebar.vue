<template>
  <div class="sidebar-wrapper">
    <!-- 热议榜 Top10 -->
    <el-card class="app-card" shadow="never">
      <h2 class="card-title">
        <el-icon><TrendCharts /></el-icon>
        热议榜 Top10
      </h2>
      <div v-if="loading" class="loading-container">
        <el-spinner />
      </div>
      <div v-else class="hot-search-list">
        <div
          v-for="item in list"
          :key="item.id"
          class="hot-search-item"
          @click="handleClick(item)"
        >
          <div :class="['rank', item.rank <= 3 ? 'top-three' : '']">{{ item.rank }}</div>
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
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import {
  TrendCharts,
  ArrowUp,
  ArrowDown,
  Minus,
  WarningFilled,
} from '@element-plus/icons-vue'
import type { HotSearchItem } from '@/api/community'

defineProps<{
  list: HotSearchItem[]
  loading: boolean
}>()

const emit = defineEmits<{
  (e: 'openHotTopic', item: HotSearchItem): void
}>()

function handleClick(item: HotSearchItem) {
  emit('openHotTopic', item)
}
</script>

<style scoped>
.sidebar-wrapper {
  display: flex;
  flex-direction: column;
  gap: 0;
  min-height: 0;
  height: 100%;
}
.app-card {
  border: 1px solid var(--color-border);
  border-radius: 12px;
  box-shadow: 0 8px 24px rgba(130, 34, 34, 0.08);
  background: var(--color-bg-card);
  margin: 0;
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

.app-card :deep(.el-card__body) {
  height: 100%;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.card-title {
  font-size: 18px;
  font-weight: 800;
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--color-text-primary);
}

.loading-container {
  display: flex;
  justify-content: center;
  padding: 40px;
}

.hot-search-list {
  display: grid;
  align-content: start;
  gap: 8px;
  margin: 0;
  padding: 0;
  list-style: none;
  min-height: 0;
  overflow: hidden;
}

.hot-search-item {
  display: grid;
  grid-template-columns: 28px minmax(0, 1fr);
  align-items: center;
  gap: 12px;
  padding: 8px 4px;
  border: 0;
  border-radius: 8px;
  background: transparent;
  cursor: pointer;
  transition: background 0.16s ease;
}
.hot-search-item:hover {
  background: var(--color-primary-soft);
}

.rank {
  width: 22px;
  height: 22px;
  display: grid;
  place-items: center;
  border-radius: 6px;
  background: var(--color-primary-soft);
  color: var(--color-primary);
  font-size: 12px;
  font-weight: 700;
}
.rank.top-three {
  background: linear-gradient(135deg, #ff7a45, #ffb020);
  color: #fff;
}

.hot-search-content {
  min-width: 0;
  display: grid;
  gap: 4px;
}

.keyword-row {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.keyword {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
}

.trend {
  font-size: 12px;
}
.trend.up { color: #67c23a; }
.trend.down { color: #f56c6c; }
.trend.stable { color: #999; }

.hot-search-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 6px 12px;
  color: var(--color-text-secondary);
  font-size: 12px;
  justify-content: flex-end;
}

.tip-card {
  margin-top: 0;
}

.tip-content {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.tip-icon {
  font-size: 24px;
  color: #f59e0b;
  flex-shrink: 0;
  margin-top: 2px;
}

.tip-title {
  margin: 0 0 4px;
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.tip-text {
  margin: 0;
  font-size: 13px;
  color: var(--color-text-secondary);
  line-height: 1.6;
}

:global(:root.dark) .hot-search-item:hover {
  background: var(--control-hover-bg);
}

:global(:root.dark) .rank {
  background: var(--color-primary-soft);
  color: var(--color-primary);
}
</style>
