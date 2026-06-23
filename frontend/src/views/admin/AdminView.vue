<script setup lang="ts">
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()

const editorFeatures = [
  { title: '内容审核', description: '后续提供新闻与内容审核入口。' },
  { title: '评论筛选', description: '后续提供评论筛选与处理入口。' },
  { title: '社区帖子管理', description: '后续提供社区帖子管理入口。' },
  { title: '热搜话题维护', description: '后续提供热门话题维护入口。' },
]

const adminFeatures = [
  { title: '账号管理', description: '后续提供用户账号管理入口。' },
  { title: '角色权限管理', description: '后续提供角色与权限配置入口。' },
  { title: '内容总管理', description: '后续提供全站内容管理入口。' },
  { title: 'AI 模型配置', description: '后续提供 AI 服务配置入口。' },
  { title: '提示词模板', description: '后续提供提示词模板管理入口。' },
  { title: '系统日志', description: '后续展示系统运行与操作日志。' },
  { title: '数据备份与恢复', description: '后续提供数据维护入口。' },
]
</script>

<template>
  <main class="page-container">
    <template v-if="userStore.isEditorOrAdmin">
      <el-card class="app-card" shadow="never">
        <h1>管理后台</h1>
        <p>后台功能入口会根据当前用户角色展示，当前仅提供第 4 阶段权限 Mock UI。</p>
        <el-alert title="当前为权限 Mock 占位页面，后续模块开发时补充真实管理功能" type="info" :closable="false" />
      </el-card>

      <section class="admin-section">
        <h2>审核/编辑功能</h2>
        <div class="placeholder-grid">
          <el-card v-for="feature in editorFeatures" :key="feature.title" class="app-card" shadow="never">
            <h3 class="placeholder-card__title">{{ feature.title }}</h3>
            <p class="placeholder-card__description">{{ feature.description }}</p>
          </el-card>
        </div>
      </section>

      <section v-if="userStore.isAdmin" class="admin-section">
        <h2>管理员专属功能</h2>
        <div class="placeholder-grid">
          <el-card v-for="feature in adminFeatures" :key="feature.title" class="app-card" shadow="never">
            <h3 class="placeholder-card__title">{{ feature.title }}</h3>
            <p class="placeholder-card__description">{{ feature.description }}</p>
          </el-card>
        </div>
      </section>
    </template>

    <el-card v-else class="app-card unauthorized-card" shadow="never">
      <el-result icon="warning" title="当前账号无权限访问" sub-title="该页面仅允许审核/编辑或管理员访问。" />
    </el-card>
  </main>
</template>

<style scoped>
.page-container {
  padding: 24px;
}

h1 {
  margin-top: 0;
}

p {
  margin: 0 0 16px;
  color: var(--color-text-secondary);
}

.admin-section {
  margin-top: 24px;
}

.admin-section h2 {
  margin: 0;
  color: var(--color-text-primary);
  font-size: 18px;
}

.unauthorized-card {
  max-width: 560px;
  margin: 48px auto;
}
</style>
