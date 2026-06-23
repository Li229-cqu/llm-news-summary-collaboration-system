<script setup lang="ts">
import { ref } from 'vue'

const categories = ['推荐', '时政', '社会', '财经', '科技', '体育', '娱乐']
const activeCategory = ref('推荐')

function selectCategory(category: string) {
  activeCategory.value = category
}
</script>

<template>
  <aside class="app-sidebar">
    <div class="app-sidebar__title">新闻分类</div>
    <el-menu class="app-sidebar__menu" :default-active="activeCategory" @select="selectCategory">
      <el-menu-item v-for="category in categories" :key="category" :index="category">
        <span class="app-sidebar__dot" aria-hidden="true"></span>
        <span>{{ category }}</span>
      </el-menu-item>
    </el-menu>

    <div class="app-sidebar__quick-links">
      <el-card class="app-sidebar__quick-card" shadow="never">
        <span class="app-sidebar__quick-title">生成历史</span>
        <span class="app-sidebar__quick-description">功能入口占位</span>
      </el-card>
      <el-card class="app-sidebar__quick-card" shadow="never">
        <span class="app-sidebar__quick-title">订阅管理</span>
        <span class="app-sidebar__quick-description">功能入口占位</span>
      </el-card>
    </div>
  </aside>
</template>

<style scoped>
.app-sidebar {
  padding: 20px 0;
}

.app-sidebar__title {
  padding: 0 20px 12px;
  color: var(--color-text-secondary);
  font-size: 13px;
}

.app-sidebar__menu {
  border-right: 0;
}

.app-sidebar__menu :deep(.el-menu-item) {
  gap: 10px;
  height: 44px;
  line-height: 44px;
}

.app-sidebar__menu :deep(.el-menu-item.is-active) {
  color: var(--color-primary);
  background: var(--color-primary-soft);
}

.app-sidebar__dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--color-text-secondary);
}

.app-sidebar__menu :deep(.el-menu-item.is-active) .app-sidebar__dot {
  background: var(--color-primary);
}

.app-sidebar__quick-links {
  display: grid;
  gap: 10px;
  margin-top: 16px;
  padding: 16px;
}

.app-sidebar__quick-card {
  cursor: default;
  border-color: var(--color-border);
}

.app-sidebar__quick-card :deep(.el-card__body) {
  display: grid;
  gap: 4px;
  padding: 12px;
}

.app-sidebar__quick-title {
  color: var(--color-text-primary);
  font-size: 14px;
  font-weight: 600;
}

.app-sidebar__quick-description {
  color: var(--color-text-secondary);
  font-size: 12px;
}
</style>
