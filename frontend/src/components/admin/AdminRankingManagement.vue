<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import PaginationBar from '@/components/common/PaginationBar.vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Check, Link, Refresh, View, Hide } from '@element-plus/icons-vue'
import {
  getAdminCommunityHotRanking,
  getAdminNewsHotRanking,
  reviewAdminNews,
  reviewAdminPost,
  type AdminCommunityHotRankingResponse,
  type AdminNewsHotRankingResponse,
} from '@/api/admin'

const emit = defineEmits<{
  changed: []
  navigate: [tab: string]
}>()

const router = useRouter()
const activeTab = ref<'news' | 'community'>('news')
const loadingNews = ref(false)
const loadingCommunity = ref(false)
const newsData = ref<AdminNewsHotRankingResponse | null>(null)
const communityData = ref<AdminCommunityHotRankingResponse | null>(null)
const newsQuery = reactive({ keyword: '', page: 1, page_size: 10 })
const communityQuery = reactive({ keyword: '', page: 1, page_size: 10 })

const summaryCards = computed(() => {
  const summary = newsData.value?.summary || communityData.value?.summary
  return [
    { key: 'newsHot', label: '首页热搜数量', value: newsData.value?.total ?? summary?.news_hot_count ?? 0 },
    { key: 'communityHot', label: '社区热议数量', value: communityData.value?.total ?? summary?.community_hot_count ?? 0 },
    { key: 'todayNews', label: '今日新增新闻', value: summary?.today_news_count ?? 0 },
    { key: 'todayPosts', label: '今日新增帖子', value: summary?.today_post_count ?? 0 },
  ]
})

async function loadNewsRanking() {
  loadingNews.value = true
  try {
    newsData.value = await getAdminNewsHotRanking({ ...newsQuery })
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '首页热搜榜加载失败')
  } finally {
    loadingNews.value = false
  }
}

async function loadCommunityRanking() {
  loadingCommunity.value = true
  try {
    communityData.value = await getAdminCommunityHotRanking({ ...communityQuery })
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '社区热议榜加载失败')
  } finally {
    loadingCommunity.value = false
  }
}

function searchNewsRanking() {
  newsQuery.page = 1
  void loadNewsRanking()
}

function searchCommunityRanking() {
  communityQuery.page = 1
  void loadCommunityRanking()
}

function openNews(id: number) {
  void router.push(`/news/${id}`)
}

function openPost(id: number) {
  void router.push(`/community/posts/${id}`)
}

function goNewsManagement() {
  emit('navigate', 'news')
}

function goPostManagement() {
  emit('navigate', 'posts')
}

async function changeNewsStatus(id: number, action: 'reject' | 'restore') {
  const label = action === 'reject' ? '下架' : '恢复显示'
  await ElMessageBox.confirm(`确认${label}这条新闻？`, '操作确认', { type: 'warning' })
  await reviewAdminNews(id, { action, reason: '榜单运营操作' })
  ElMessage.success('操作完成')
  await loadNewsRanking()
  emit('changed')
}

async function changePostStatus(id: number, action: 'fold' | 'restore') {
  const label = action === 'fold' ? '隐藏' : '恢复显示'
  await ElMessageBox.confirm(`确认${label}这个帖子？`, '操作确认', { type: 'warning' })
  await reviewAdminPost(id, { action, reason: '榜单运营操作' })
  ElMessage.success('操作完成')
  await loadCommunityRanking()
  emit('changed')
}

onMounted(async () => {
  await Promise.allSettled([loadNewsRanking(), loadCommunityRanking()])
})
</script>

<template>
  <section class="admin-ranking-management">
    <el-card shadow="never" class="module-card">
      <div class="panel-header">
        <div>
          <h3>榜单运营</h3>
          <p>管理首页热搜榜与社区热议榜，查看真实前台榜单数据与热度排序。</p>
        </div>
        <el-button :icon="Refresh" type="primary" @click="activeTab === 'news' ? loadNewsRanking() : loadCommunityRanking()">刷新榜单</el-button>
      </div>

      <div class="summary-grid">
        <article v-for="card in summaryCards" :key="card.key" class="summary-card">
          <span>{{ card.label }}</span>
          <strong>{{ card.value }}</strong>
        </article>
      </div>

      <el-tabs v-model="activeTab" class="ranking-tabs">
        <el-tab-pane label="首页热搜榜" name="news">
          <div class="ranking-note">
            根据新闻浏览、点赞、收藏、评论等互动数据综合计算，排序结果与首页展示保持一致。
            <el-tooltip content="热度 = 浏览量 + 点赞数 * 5 + 收藏数 * 4 + 评论数 * 6" placement="top">
              <el-tag size="small" effect="plain">公式</el-tag>
            </el-tooltip>
          </div>
          <div class="filter-row">
            <el-input v-model="newsQuery.keyword" placeholder="搜索新闻标题" clearable @keyup.enter="searchNewsRanking" />
            <el-button type="primary" @click="searchNewsRanking">搜索</el-button>
            <el-button :icon="Refresh" @click="loadNewsRanking">刷新</el-button>
          </div>
          <el-table v-loading="loadingNews" :data="newsData?.items || []" border empty-text="暂无首页热搜榜数据">
            <el-table-column prop="rank" label="排名" width="80" />
            <el-table-column prop="title" label="新闻标题" min-width="260" show-overflow-tooltip />
            <el-table-column prop="category_name" label="分类" width="120" />
            <el-table-column prop="source" label="来源" width="130" show-overflow-tooltip />
            <el-table-column prop="view_count" label="浏览量" width="90" />
            <el-table-column prop="like_count" label="点赞数" width="90" />
            <el-table-column prop="favorite_count" label="收藏数" width="90" />
            <el-table-column prop="comment_count" label="评论数" width="90" />
            <el-table-column prop="heat_score" label="热度值" width="100" />
            <el-table-column prop="publish_time" label="发布时间" width="170" />
            <el-table-column label="状态" width="100">
              <template #default="scope"><el-tag :type="scope.row.status === 1 ? 'success' : 'info'" size="small">{{ scope.row.status_label }}</el-tag></template>
            </el-table-column>
            <el-table-column label="操作" width="320" fixed="right">
              <template #default="scope">
                <el-button :icon="View" size="small" text type="primary" @click="openNews(scope.row.id)">查看新闻</el-button>
                <el-button :icon="Link" size="small" text type="primary" @click="goNewsManagement">新闻管理</el-button>
                <el-button :icon="Hide" size="small" text type="danger" @click="changeNewsStatus(scope.row.id, 'reject')">下架</el-button>
                <el-button v-if="scope.row.status !== 1" :icon="Check" size="small" text type="success" @click="changeNewsStatus(scope.row.id, 'restore')">恢复</el-button>
              </template>
            </el-table-column>
          </el-table>
          <PaginationBar :current-page="newsQuery.page" :total-pages="Math.ceil((newsData?.total || 0) / newsQuery.page_size)" @change="(p: number) => { newsQuery.page = p; loadNewsRanking(); }" />
        </el-tab-pane>

        <el-tab-pane label="社区热议榜" name="community">
          <div class="ranking-note">
            根据帖子浏览、点赞、收藏、评论等互动数据综合计算，排序结果与社区热议榜保持一致。
            <el-tooltip content="热度 = 点赞数 * 4 + 收藏数 * 5 + 评论数 * 6 + 浏览量 * 3" placement="top">
              <el-tag size="small" effect="plain">公式</el-tag>
            </el-tooltip>
          </div>
          <div class="filter-row">
            <el-input v-model="communityQuery.keyword" placeholder="搜索帖子标题" clearable @keyup.enter="searchCommunityRanking" />
            <el-button type="primary" @click="searchCommunityRanking">搜索</el-button>
            <el-button :icon="Refresh" @click="loadCommunityRanking">刷新</el-button>
          </div>
          <el-table v-loading="loadingCommunity" :data="communityData?.items || []" border empty-text="暂无社区热议榜数据">
            <el-table-column prop="rank" label="排名" width="80" />
            <el-table-column prop="title" label="帖子标题" min-width="260" show-overflow-tooltip />
            <el-table-column prop="author_name" label="作者" width="130" show-overflow-tooltip />
            <el-table-column prop="view_count" label="浏览量" width="90" />
            <el-table-column prop="like_count" label="点赞数" width="90" />
            <el-table-column prop="favorite_count" label="收藏数" width="90" />
            <el-table-column prop="comment_count" label="评论数" width="90" />
            <el-table-column prop="heat_score" label="热度值" width="100" />
            <el-table-column prop="created_at" label="发布时间" width="170" />
            <el-table-column label="状态" width="100">
              <template #default="scope"><el-tag :type="scope.row.status === 1 ? 'success' : 'info'" size="small">{{ scope.row.status_label }}</el-tag></template>
            </el-table-column>
            <el-table-column label="操作" width="320" fixed="right">
              <template #default="scope">
                <el-button :icon="View" size="small" text type="primary" @click="openPost(scope.row.id)">查看帖子</el-button>
                <el-button :icon="Link" size="small" text type="primary" @click="goPostManagement">帖子管理</el-button>
                <el-button :icon="Hide" size="small" text type="danger" @click="changePostStatus(scope.row.id, 'fold')">隐藏</el-button>
                <el-button v-if="scope.row.status !== 1" :icon="Check" size="small" text type="success" @click="changePostStatus(scope.row.id, 'restore')">恢复</el-button>
              </template>
            </el-table-column>
          </el-table>
          <PaginationBar :current-page="communityQuery.page" :total-pages="Math.ceil((communityData?.total || 0) / communityQuery.page_size)" @change="(p: number) => { communityQuery.page = p; loadCommunityRanking(); }" />
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </section>
</template>

<style scoped>
.admin-ranking-management { width: 100%; }
.module-card { border-radius: 18px; }
.panel-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; margin-bottom: 16px; }
.panel-header h3 { margin: 0 0 6px; color: var(--color-text-primary); }
.panel-header p { margin: 0; color: var(--color-text-secondary); }
.summary-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; margin: 12px 0 16px; }
.summary-card { padding: 14px; border: 1px solid var(--color-border-light); border-radius: 8px; background: var(--color-bg-page); }
.summary-card span { display: block; color: var(--color-text-secondary); font-size: 13px; }
.summary-card strong { display: block; margin-top: 8px; font-size: 24px; color: var(--color-text-primary); }
.ranking-tabs { margin-top: 8px; }
.ranking-note { display: flex; align-items: center; gap: 8px; margin: 4px 0 14px; color: var(--color-text-secondary); font-size: 13px; }
.filter-row { display: flex; flex-wrap: wrap; gap: 10px; margin: 12px 0 16px; }
.filter-row .el-input { width: 280px; }
.pager { margin-top: 16px; justify-content: flex-end; }
@media (max-width: 1200px) { .summary-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
@media (max-width: 720px) {
  .summary-grid { grid-template-columns: 1fr; }
  .filter-row .el-input { width: 100%; }
  .panel-header { display: grid; }
}
</style>
