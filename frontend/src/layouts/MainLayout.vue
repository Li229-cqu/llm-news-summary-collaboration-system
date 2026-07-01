<template>
  <div class="main-layout">
    <AppHeader />

    <div class="layout-body">
      <aside v-if="isHomeRoute" class="layout-sidebar">
        <AppSidebar />
      </aside>

      <main class="layout-main">
        <RouterView />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import AppHeader from '@/components/layout/AppHeader.vue'
import AppSidebar from '@/components/layout/AppSidebar.vue'

const route = useRoute()
const isHomeRoute = computed(() => route.name === 'home' || route.path === '/home')
</script>

<style scoped>
.main-layout {
  display: flex;
  flex-direction: column;
  width: 100%;
  min-width: 0;
  min-height: 100vh;
  background: var(--color-bg);
}

.layout-body {
  display: flex;
  flex-direction: row;
  width: 100%;
  flex: 1;
  min-height: 0;
}

.layout-sidebar {
  flex: 0 0 var(--sidebar-width);
  width: var(--sidebar-width);
  min-width: var(--sidebar-width);
  position: sticky;
  top: 12px;
  align-self: flex-start;
  height: calc(100vh - 24px);
}

.layout-main {
  flex: 1;
  min-width: 0;
  min-height: 0;
  padding: var(--layout-main-padding);
  background: var(--color-bg);
}

/* 窄屏下取消侧边栏 sticky，恢复普通布局 */
@media (max-width: 1200px) {
  .layout-sidebar {
    position: static;
    width: 100%;
    flex: none;
    height: auto;
  }
}
</style>
