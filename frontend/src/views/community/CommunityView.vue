<template>
  <main class="page-container">
    <el-card class="app-card" shadow="never">
      <h1>社区互动</h1>
      <p>社区模块，用于承载话题讨论、用户发帖和 AI 辅助交流等功能。</p>
      <el-alert title="当前为第 1 阶段占位页面，后续模块开发时补充真实功能" type="info" :closable="false" />
    </el-card>

    <section class="placeholder-grid">
      <el-card class="app-card" shadow="never">
        <h2 class="placeholder-card__title">发帖区</h2>
        <p class="placeholder-card__description">后续提供社区内容发布入口。</p>
      </el-card>
      <el-card class="app-card" shadow="never">
        <h2 class="placeholder-card__title">帖子流</h2>
        <p class="placeholder-card__description">后续展示社区帖子与互动内容。</p>
      </el-card>
      <el-card class="app-card" shadow="never">
        <h2 class="placeholder-card__title">热搜 Top10</h2>
        <p class="placeholder-card__description">后续展示社区热门搜索与讨论趋势。</p>
      </el-card>
      <el-card class="app-card" shadow="never">
        <h2 class="placeholder-card__title">AI 新闻助手</h2>
        <p class="placeholder-card__description">后续提供社区场景下的 AI 问答入口。</p>
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
  margin: 0 0 16px;
  color: var(--color-text-secondary);
}
</style>
