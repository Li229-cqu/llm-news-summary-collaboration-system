<template>
  <div class="main-layout" :class="{ 'main-layout--community': isCommunityRoute, 'main-layout--admin': isAdminRoute }">
    <AppHeader />

    <div class="layout-body">
      <aside v-if="isHomeRoute" class="layout-sidebar">
        <AppSidebar />
      </aside>

      <main class="layout-main" :class="{ 'layout-main--community': isCommunityRoute, 'layout-main--admin': isAdminRoute }">
        <RouterView v-slot="{ Component, route: childRoute }">
          <KeepAlive :max="8">
            <component :is="Component" :key="childRoute.fullPath" />
          </KeepAlive>
        </RouterView>
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
const isHomeRoute = computed(() => route.name === 'home' || route.path === '/home' || route.path.startsWith('/timeline'))
const isCommunityRoute = computed(() => route.name === 'community' || route.name === 'community-create-post')
const isAdminRoute = computed(() => route.name === 'admin')
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

.main-layout--community,
.main-layout--admin {
  height: 100vh;
  min-height: 100vh;
  overflow: hidden;
}

.layout-main--community,
.layout-main--admin {
  padding: 0;
  overflow: hidden;
}

@media (max-width: 1200px) {
  .layout-sidebar {
    position: static;
    width: 100%;
    flex: none;
    height: auto;
  }
}
</style>
