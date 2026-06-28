<template>
  <div class="reading-timeline">
    <div class="timeline-header">
      <div class="header-info">
        <h3 class="header-title">阅读时间线</h3>
        <p class="header-subtitle">按日期查看你的阅读记录分布</p>
      </div>
      <div class="header-controls">
        <el-radio-group v-model="timeRange" size="small" @change="handleReload">
          <el-radio-button value="7">7天</el-radio-button>
          <el-radio-button value="30">30天</el-radio-button>
        </el-radio-group>
        <el-button size="small" :loading="loading" @click="handleReload">刷新</el-button>
      </div>
    </div>

    <!-- Summary Cards -->
    <div v-if="data" class="summary-row">
      <div class="summary-item">
        <span class="summary-value">{{ data.summary.total_days }}</span>
        <span class="summary-label">活跃天数</span>
      </div>
      <div class="summary-item">
        <span class="summary-value">{{ data.summary.total_reads }}</span>
        <span class="summary-label">总阅读数</span>
      </div>
      <div class="summary-item">
        <span class="summary-value">{{ data.summary.most_active_date }}</span>
        <span class="summary-label">最活跃日期</span>
      </div>
      <div class="summary-item">
        <span class="summary-value">{{ data.summary.most_active_category }}</span>
        <span class="summary-label">最常读分类</span>
      </div>
    </div>

    <el-skeleton v-if="loading" :rows="5" animated />

    <el-empty v-else-if="!data || data.items.length === 0" description="暂无阅读时间线数据" :image-size="60" />

    <!-- Timeline List -->
    <div v-else class="timeline-list">
      <div v-for="item in data.items" :key="item.date" class="timeline-day">
        <div class="day-header">
          <div class="day-date">
            <span class="date-text">{{ item.date }}</span>
            <el-tag size="small" type="primary">{{ item.total_reads }} 篇</el-tag>
          </div>
        </div>

        <div class="day-body">
          <!-- Categories -->
          <div v-if="item.categories.length" class="day-section">
            <span class="section-label">分类</span>
            <div class="tag-row">
              <el-tag v-for="cat in item.categories.slice(0, 5)" :key="cat.category_name" size="small" effect="plain">
                {{ cat.category_name }} ({{ cat.read_count }})
              </el-tag>
            </div>
          </div>

          <!-- Topics -->
          <div v-if="item.topics.length" class="day-section">
            <span class="section-label">话题</span>
            <div class="tag-row">
              <el-tag v-for="topic in item.topics.slice(0, 5)" :key="topic.topic_name" size="small" effect="plain" type="success">
                {{ topic.topic_name }} ({{ topic.read_count }})
              </el-tag>
            </div>
          </div>

          <!-- News List -->
          <div v-if="item.news.length" class="day-section">
            <span class="section-label">阅读新闻 ({{ item.news.length }})</span>
            <div class="news-list">
              <div
                v-for="news in item.news.slice(0, 5)"
                :key="news.news_id"
                class="news-row"
                @click="handleNewsClick(news.news_id)"
              >
                <span class="news-title">{{ news.title }}</span>
                <span class="news-meta">
                  <el-tag size="small" type="info">{{ news.category_name }}</el-tag>
                  <span class="news-time">{{ news.browse_time }}</span>
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getReadingTimeline, type ReadingTimelineResponse } from '@/api/profile'

const router = useRouter()

const loading = ref(false)
const data = ref<ReadingTimelineResponse | null>(null)
const timeRange = ref<7 | 30>(30)

async function loadData() {
  loading.value = true
  try {
    data.value = await getReadingTimeline({ days: timeRange.value })
  } catch (err) {
    ElMessage.error('加载阅读时间线失败')
  } finally {
    loading.value = false
  }
}

function handleReload() {
  loadData()
}

function handleNewsClick(newsId: number) {
  router.push(`/news/${newsId}`)
}

onMounted(() => {
  loadData()
})
</script>

<style scoped lang="scss">
.reading-timeline {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.timeline-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;

  .header-title {
    margin: 0 0 2px;
    font-size: 18px;
    font-weight: 600;
    color: var(--el-text-color-primary);
  }

  .header-subtitle {
    margin: 0;
    font-size: 13px;
    color: var(--el-text-color-secondary);
  }

  .header-controls {
    display: flex;
    align-items: center;
    gap: 8px;
  }
}

.summary-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 12px;

  .summary-item {
    display: flex;
    flex-direction: column;
    gap: 4px;
    padding: 14px 16px;
    border: 1px solid var(--el-border-color-light);
    border-radius: 8px;
    background: var(--el-fill-color-lighter);
    text-align: center;

    .summary-value {
      font-size: 20px;
      font-weight: 700;
      color: var(--el-color-primary);
    }

    .summary-label {
      font-size: 12px;
      color: var(--el-text-color-secondary);
    }
  }
}

.timeline-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.timeline-day {
  border: 1px solid var(--el-border-color-light);
  border-radius: 8px;
  overflow: hidden;

  .day-header {
    padding: 12px 16px;
    background: var(--el-fill-color-lighter);
    border-bottom: 1px solid var(--el-border-color-light);

    .day-date {
      display: flex;
      align-items: center;
      gap: 10px;

      .date-text {
        font-size: 15px;
        font-weight: 600;
        color: var(--el-text-color-primary);
      }
    }
  }

  .day-body {
    padding: 14px 16px;
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .day-section {
    display: flex;
    flex-direction: column;
    gap: 6px;

    .section-label {
      font-size: 12px;
      font-weight: 500;
      color: var(--el-text-color-secondary);
    }
  }

  .tag-row {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
  }

  .news-list {
    display: flex;
    flex-direction: column;
    gap: 6px;

    .news-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      padding: 8px 10px;
      border-radius: 6px;
      cursor: pointer;
      transition: all 0.2s;

      &:hover {
        background: var(--el-color-primary-light-9);
      }

      .news-title {
        flex: 1;
        min-width: 0;
        font-size: 13px;
        color: var(--el-text-color-primary);
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }

      .news-meta {
        display: flex;
        align-items: center;
        gap: 6px;
        flex-shrink: 0;

        .news-time {
          font-size: 11px;
          color: var(--el-text-color-secondary);
        }
      }
    }
  }
}
</style>
