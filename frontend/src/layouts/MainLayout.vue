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
  height: 100%;
  overflow: hidden;
  background: var(--color-bg);
}

.layout-body {
  display: flex;
  flex-direction: row;
  width: 100%;
  height: calc(100vh - var(--header-height));
  min-height: 0;
}

.layout-sidebar {
  flex: 0 0 var(--sidebar-width);
  width: var(--sidebar-width);
  min-width: var(--sidebar-width);
  overflow-y: auto;
  background: var(--color-bg-card);
  border-right: 1px solid var(--color-border);
}

.layout-main {
  flex: 1;
  min-width: 0;
  padding: var(--layout-main-padding);
  overflow-y: auto;
  background: var(--color-bg);
}
</style>
