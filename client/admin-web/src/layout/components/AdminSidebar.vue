<template>
  <aside class="sidebar" :class="{ 'is-collapsed': appStore.sidebarCollapsed }">
    <div class="sidebar__brand">
      <div class="sidebar__logo">HD</div>
      <div v-if="!appStore.sidebarCollapsed" class="sidebar__brand-text">
        <span class="sidebar__title">健康饮食后台</span>
        <span class="sidebar__subtitle">Admin Console</span>
      </div>
    </div>

    <el-scrollbar class="sidebar__scrollbar">
      <el-menu
        class="sidebar__menu"
        :default-active="activeMenu"
        :collapse="appStore.sidebarCollapsed"
        :collapse-transition="false"
        background-color="transparent"
        text-color="var(--admin-text-light)"
        active-text-color="var(--admin-text-light)"
        router
      >
        <el-menu-item
          v-for="item in menuItems"
          :key="item.name"
          :index="item.fullPath"
        >
          <el-icon>
            <component :is="iconMap[item.meta.icon]" />
          </el-icon>
          <template #title>
            <span>{{ item.meta.title }}</span>
          </template>
        </el-menu-item>
      </el-menu>
    </el-scrollbar>

    <div v-if="!appStore.sidebarCollapsed" class="sidebar__footer">
      <div class="sidebar__footer-chip">课程项目管理端基础骨架</div>
      <p class="sidebar__footer-text">
        基于 Vue 3、Element Plus、Pinia 与 Vue Router，已预留管理路由和接口层。
      </p>
    </div>
  </aside>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import {
  Dish,
  Document,
  Grid,
  House,
  Setting,
  TrendCharts,
  User
} from '@element-plus/icons-vue'
import { adminChildrenRoutes } from '@/router/routes'
import { useAppStore } from '@/store/app'

const route = useRoute()
const appStore = useAppStore()

const iconMap = {
  House,
  User,
  Dish,
  Grid,
  Setting,
  Document,
  TrendCharts
}

const menuItems = adminChildrenRoutes
  .filter((item) => item.meta?.menu)
  .map((item) => ({
    ...item,
    fullPath: `/${item.path}`
  }))

const activeMenu = computed(() => route.path)
</script>

<style scoped>
.sidebar {
  position: sticky;
  top: 0;
  display: flex;
  height: 100vh;
  flex-direction: column;
  padding: var(--space-5);
  border-right: 1px solid rgba(255, 255, 255, 0.06);
  background:
    linear-gradient(180deg, rgba(17, 33, 23, 0.98), rgba(26, 45, 32, 0.98)),
    var(--admin-bg-sidebar);
  color: var(--admin-text-light);
}

.sidebar__brand {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  padding: var(--space-4);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: var(--radius-md);
  background: rgba(255, 255, 255, 0.04);
}

.sidebar__logo {
  display: flex;
  align-items: center;
  justify-content: center;
  width: var(--space-12);
  height: var(--space-12);
  border-radius: var(--radius-md);
  background: linear-gradient(135deg, var(--admin-primary), var(--admin-accent));
  color: var(--admin-bg-sidebar);
  font-weight: 800;
  letter-spacing: 0.08em;
  box-shadow: 0 14px 32px rgba(76, 175, 80, 0.3);
}

.sidebar__brand-text {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.sidebar__title {
  font-size: var(--font-size-lg);
  font-weight: 700;
}

.sidebar__subtitle {
  color: rgba(237, 247, 238, 0.72);
  font-size: var(--font-size-xs);
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.sidebar__scrollbar {
  flex: 1;
  margin-top: var(--space-5);
}

.sidebar__menu {
  border-right: 0;
}

:deep(.el-menu-item) {
  height: 48px;
  margin-bottom: var(--space-2);
  border-radius: var(--radius-sm);
}

:deep(.el-menu-item.is-active) {
  background: linear-gradient(135deg, rgba(76, 175, 80, 0.26), rgba(135, 201, 139, 0.18));
}

:deep(.el-menu-item:hover) {
  background: rgba(255, 255, 255, 0.07);
}

.sidebar__footer {
  margin-top: var(--space-5);
  padding: var(--space-4);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: var(--radius-md);
  background: rgba(255, 255, 255, 0.04);
}

.sidebar__footer-chip {
  display: inline-flex;
  padding: var(--space-2) var(--space-3);
  border-radius: 999px;
  background: rgba(76, 175, 80, 0.18);
  color: #cceacd;
  font-size: var(--font-size-xs);
  font-weight: 700;
}

.sidebar__footer-text {
  margin: var(--space-3) 0 0;
  color: rgba(237, 247, 238, 0.72);
  font-size: var(--font-size-xs);
  line-height: 1.7;
}

.sidebar.is-collapsed {
  padding: var(--space-5) var(--space-3);
}

.sidebar.is-collapsed .sidebar__brand {
  justify-content: center;
}

@media (max-width: 1080px) {
  .sidebar {
    position: static;
    height: auto;
  }
}
</style>
