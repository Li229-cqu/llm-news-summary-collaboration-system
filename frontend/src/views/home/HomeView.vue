<template>
  <main class="page-container">
    <el-card class="app-card" shadow="never">
      <h1>首页新闻</h1>
      <p>系统首页模块，用于承载新闻浏览、内容推荐和热点信息。</p>
      <el-alert title="当前为第 1 阶段占位页面，后续模块开发时补充真实功能" type="info" :closable="false" />
    </el-card>

    <section class="placeholder-grid">
      <el-card class="app-card" shadow="never">
        <h2 class="placeholder-card__title">新闻推荐区</h2>
        <p class="placeholder-card__description">后续展示面向用户的推荐新闻内容。</p>
      </el-card>
      <el-card class="app-card" shadow="never">
        <h2 class="placeholder-card__title">新闻列表区</h2>
        <p class="placeholder-card__description">后续展示分类浏览与新闻列表内容。</p>
      </el-card>
      <el-card class="app-card" shadow="never">
        <h2 class="placeholder-card__title">热榜区</h2>
        <p class="placeholder-card__description">后续展示热点新闻与趋势信息。</p>
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
