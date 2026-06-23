<template>
  <main class="page-container">
    <el-card class="app-card" shadow="never">
      <h1>AI 标题摘要生成</h1>
      <p>AI 生成模块，用于组织新闻文本输入、生成参数和结果展示流程。</p>
      <el-alert title="当前为第 1 阶段占位页面，后续模块开发时补充真实功能" type="info" :closable="false" />
    </el-card>

    <section class="placeholder-grid">
      <el-card class="app-card" shadow="never">
        <h2 class="placeholder-card__title">文本输入区</h2>
        <p class="placeholder-card__description">后续提供新闻文本或链接等输入方式。</p>
      </el-card>
      <el-card class="app-card" shadow="never">
        <h2 class="placeholder-card__title">参数选择区</h2>
        <p class="placeholder-card__description">后续提供标题、摘要和生成风格等参数选择。</p>
      </el-card>
      <el-card class="app-card" shadow="never">
        <h2 class="placeholder-card__title">结果展示区</h2>
        <p class="placeholder-card__description">后续展示 AI 生成结果与相关操作。</p>
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
