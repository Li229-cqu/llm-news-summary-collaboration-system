<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const newsId = computed(() => route.params.id)
</script>

<template>
  <main class="page-container">
    <el-card class="app-card" shadow="never">
      <h1>新闻详情</h1>
      <p>新闻详情模块，用于展示新闻内容、阅读信息与互动入口。</p>
      <p class="route-parameter">当前新闻 ID：{{ newsId }}</p>
      <el-alert title="当前为第 1 阶段占位页面，后续模块开发时补充真实功能" type="info" :closable="false" />
    </el-card>

    <section class="placeholder-grid">
      <el-card class="app-card" shadow="never">
        <h2 class="placeholder-card__title">新闻标题区</h2>
        <p class="placeholder-card__description">后续展示新闻标题、来源、发布时间等基础信息。</p>
      </el-card>
      <el-card class="app-card" shadow="never">
        <h2 class="placeholder-card__title">正文区</h2>
        <p class="placeholder-card__description">后续展示新闻正文、媒体内容与相关信息。</p>
      </el-card>
      <el-card class="app-card" shadow="never">
        <h2 class="placeholder-card__title">评论区</h2>
        <p class="placeholder-card__description">后续展示评论列表与互动操作入口。</p>
      </el-card>
    </section>
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
  color: var(--color-text-secondary);
}

.route-parameter {
  margin-bottom: 16px;
  color: var(--color-text-primary);
}
</style>
