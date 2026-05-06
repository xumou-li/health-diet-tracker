<template>
  <div class="admin-layout" :class="{ 'is-collapsed': appStore.sidebarCollapsed }">
    <AdminSidebar />

    <div class="admin-layout__main">
      <AdminHeader />

      <main class="admin-layout__content">
        <div class="admin-layout__content-inner">
          <router-view />
        </div>
      </main>
    </div>
  </div>
</template>

<script setup>
import { useAppStore } from '@/store/app'
import AdminHeader from './components/AdminHeader.vue'
import AdminSidebar from './components/AdminSidebar.vue'

const appStore = useAppStore()
</script>

<style scoped>
.admin-layout {
  display: grid;
  grid-template-columns: var(--sidebar-width) minmax(0, 1fr);
  min-height: 100vh;
  transition: grid-template-columns 0.28s ease;
}

.admin-layout.is-collapsed {
  grid-template-columns: var(--sidebar-collapsed-width) minmax(0, 1fr);
}

.admin-layout__main {
  display: flex;
  min-width: 0;
  flex-direction: column;
}

.admin-layout__content {
  flex: 1;
  padding: var(--space-6);
}

.admin-layout__content-inner {
  width: 100%;
  max-width: var(--page-max-width);
  margin: 0 auto;
}

@media (max-width: 1080px) {
  .admin-layout,
  .admin-layout.is-collapsed {
    grid-template-columns: 1fr;
  }
}
</style>
