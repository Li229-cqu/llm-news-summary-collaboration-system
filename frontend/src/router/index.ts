import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { ElMessage } from 'element-plus'
import MainLayout from '@/layouts/MainLayout.vue'
import pinia from '@/stores'
import { useUserStore } from '@/stores/user'
import HomeView from '@/views/home/HomeView.vue'

const projectName = '基于大语言模型的智能新闻摘要与协同互动系统'

declare module 'vue-router' {
  interface RouteMeta {
    title?: string
    requiresAuth?: boolean
    roles?: string[]
  }
}

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    component: MainLayout,
    redirect: '/home',
    children: [
      {
        path: 'home',
        name: 'home',
        component: HomeView,
        meta: { title: '首页', requiresAuth: false },
      },
      {
        path: 'news/:id',
        name: 'news-detail',
        component: () => import('@/views/news-detail/NewsDetailView.vue'),
        meta: { title: '新闻详情', requiresAuth: false },
      },
      {
        path: 'ai/title-summary',
        redirect: '/ai-generate',
      },
      {
        path: 'ai-generate',
        name: 'ai-generate',
        component: () => import('@/views/ai-generate/AIGenerateView.vue'),
        meta: { title: 'AI 标题摘要生成', requiresAuth: true },
      },
      {
        path: 'ai-generate/history',
        name: 'ai-generate-history',
        component: () => import('@/views/ai-generate/AIGenerateHistoryListView.vue'),
        meta: { title: 'AI 生成历史', requiresAuth: true },
      },
      {
        path: 'ai-generate/history/:id',
        name: 'ai-generate-history-detail',
        component: () => import('@/views/ai-generate/AIGenerateHistoryDetailView.vue'),
        meta: { title: 'AI 生成历史详情', requiresAuth: true },
      },
      {
        path: 'community',
        name: 'community',
        component: () => import('@/views/community/CommunityView.vue'),
        meta: { title: '社区互动', requiresAuth: true },
      },
      {
        path: 'community/posts/:id',
        name: 'community-post-detail',
        component: () => import('@/views/community/CommunityPostDetailView.vue'),
        meta: { title: '帖子详情', requiresAuth: true },
      },
      {
        path: 'community/create',
        name: 'community-create-post',
        component: () => import('@/views/community/CreatePostView.vue'),
        meta: { title: '发布帖子', requiresAuth: true },
      },
      {
        path: 'timeline',
        name: 'timeline-list',
        component: () => import('@/views/timeline/TimelineListView.vue'),
        meta: { title: '事件脉络', requiresAuth: false },
      },
      {
        path: 'timeline/:topicId',
        name: 'timeline-detail',
        component: () => import('@/views/timeline/TimelineDetailView.vue'),
        meta: { title: '事件脉络详情', requiresAuth: false },
      },
      {
        path: 'profile',
        name: 'profile',
        component: () => import('@/views/profile/ProfileView.vue'),
        meta: { title: '个人中心', requiresAuth: true },
      },
      {
        path: 'admin',
        name: 'admin',
        component: () => import('@/views/admin/AdminView.vue'),
        meta: { title: '管理后台', requiresAuth: true, roles: ['editor', 'admin'] },
      },
    ],
  },
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/login/LoginView.vue'),
    meta: { title: '登录', requiresAuth: false },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to) => {
  const userStore = useUserStore(pinia)

  if (to.path === '/login' && userStore.isLoggedIn) {
    return '/home'
  }

  if (to.meta.requiresAuth && !userStore.isLoggedIn) {
    return {
      path: '/login',
      query: { redirect: to.fullPath },
    }
  }

  if (to.meta.roles && !to.meta.roles.includes(userStore.role)) {
    ElMessage.warning('当前账号无权限访问该页面')
    return '/home'
  }

  return true
})

router.afterEach((to) => {
  const pageTitle = typeof to.meta.title === 'string' ? to.meta.title : projectName
  document.title = `${pageTitle} - ${projectName}`
})

export default router
