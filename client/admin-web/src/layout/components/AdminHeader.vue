<template>
  <header class="header">
    <div class="header__left">
      <el-button class="header__toggle" circle @click="appStore.toggleSidebar()">
        <el-icon><Operation /></el-icon>
      </el-button>

      <div class="header__title-wrap">
        <h2 class="header__title">{{ route.meta?.title || '健康饮食管理后台' }}</h2>
      </div>
    </div>

    <div class="header__right">
      <div class="header__status desktop-only">
        <span class="header__status-dot"></span>
        <span>{{ nowText }}</span>
      </div>

      <el-dropdown @command="handleCommand">
        <div class="header__user">
          <div class="header__avatar">{{ userInitial }}</div>
          <div class="header__user-meta desktop-only">
            <span class="header__user-name">{{ authStore.adminName }}</span>
            <span class="header__user-role">{{ authStore.adminRoleText }}</span>
          </div>
          <el-icon class="header__caret"><ArrowDown /></el-icon>
        </div>

        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="profile">当前身份：{{ authStore.adminRoleText }}</el-dropdown-item>
            <el-dropdown-item divided command="logout">退出登录</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </header>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowDown, Operation } from '@element-plus/icons-vue'
import { useAppStore } from '@/store/app'
import { useAuthStore } from '@/store/auth'

const route = useRoute()
const router = useRouter()
const appStore = useAppStore()
const authStore = useAuthStore()
const nowText = ref('')

let timerId = null

const userInitial = computed(() => authStore.adminName.slice(0, 1).toUpperCase())

function updateTime() {
  nowText.value = new Date().toLocaleString('zh-CN', {
    hour12: false,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function handleCommand(command) {
  if (command === 'logout') {
    authStore.logout()
    router.push({ name: 'login' })
  }
}

onMounted(() => {
  updateTime()
  timerId = window.setInterval(updateTime, 60000)
})

onBeforeUnmount(() => {
  if (timerId) {
    window.clearInterval(timerId)
  }
})
</script>

<style scoped>
.header {
  position: sticky;
  top: 0;
  z-index: 20;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-5);
  height: var(--header-height);
  padding: var(--space-4) var(--space-6);
  border-bottom: 1px solid rgba(215, 228, 216, 0.9);
  background: var(--admin-bg-header);
  backdrop-filter: blur(18px);
}

.header__left,
.header__right {
  display: flex;
  align-items: center;
  gap: var(--space-4);
}

.header__title-wrap {
  display: flex;
  align-items: center;
}

.header__toggle {
  border-color: var(--admin-border);
  background: rgba(255, 255, 255, 0.88);
}

.header__title {
  margin: 0;
  font-size: var(--font-size-xl);
}

.header__status {
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-3) var(--space-4);
  border: 1px solid rgba(215, 228, 216, 0.92);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.78);
  color: var(--admin-text-secondary);
  font-size: var(--font-size-sm);
}

.header__status-dot {
  width: var(--space-2);
  height: var(--space-2);
  border-radius: 999px;
  background: var(--admin-primary);
  box-shadow: 0 0 0 var(--space-1) rgba(76, 175, 80, 0.18);
}

.header__user {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-2) var(--space-3);
  border: 1px solid rgba(215, 228, 216, 0.92);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.82);
  cursor: pointer;
}

.header__avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  width: var(--space-10);
  height: var(--space-10);
  border-radius: 999px;
  background: linear-gradient(135deg, var(--admin-primary), var(--admin-accent));
  color: #fff;
  font-weight: 700;
}

.header__user-meta {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.header__user-name {
  font-size: var(--font-size-sm);
  font-weight: 600;
}

.header__user-role {
  color: var(--admin-text-tertiary);
  font-size: var(--font-size-xs);
}

.header__caret {
  color: var(--admin-text-tertiary);
}

@media (max-width: 1080px) {
  .header {
    height: auto;
    flex-direction: column;
    align-items: stretch;
  }

  .header__left,
  .header__right {
    justify-content: space-between;
  }
}
</style>
