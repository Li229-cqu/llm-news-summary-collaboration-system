<template>
  <main class="page-container">
    <el-card class="app-card" shadow="never">
      <h1>个人中心</h1>
      <p>个人中心模块，用于聚合展示用户资料、互动记录和 AI 使用记录。</p>
      <el-alert title="当前为第 1 阶段占位页面，后续模块开发时补充真实功能" type="info" :closable="false" />
    </el-card>

    <section class="placeholder-grid">
      <el-card class="app-card" shadow="never">
        <h2 class="placeholder-card__title">用户信息卡片</h2>
        <p class="placeholder-card__description">后续展示用户基本资料与账号状态。</p>
      </el-card>
      <el-card class="app-card" shadow="never">
        <h2 class="placeholder-card__title">浏览历史</h2>
        <p class="placeholder-card__description">后续展示用户新闻浏览记录。</p>
      </el-card>
      <el-card class="app-card" shadow="never">
        <h2 class="placeholder-card__title">收藏</h2>
        <p class="placeholder-card__description">后续展示用户收藏的内容。</p>
      </el-card>
      <el-card class="app-card" shadow="never">
        <h2 class="placeholder-card__title">AI 生成历史</h2>
        <p class="placeholder-card__description">后续展示用户的 AI 生成记录。</p>
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
