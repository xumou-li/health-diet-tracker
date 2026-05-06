<template>
  <div class="status-page">
    <div class="status-card">
      <div class="status-card__icon">404</div>
      <h1 class="status-card__title">页面不存在或尚未规划到后台路由中</h1>
      <p class="status-card__description">
        当前地址没有对应页面。你可以返回管理首页，或回到登录页重新进入后台。
      </p>

      <div class="status-card__actions">
        <el-button @click="router.push({ name: 'login' })">返回登录</el-button>
        <el-button type="primary" @click="router.push({ name: 'dashboard' })">前往首页</el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()
</script>

<style scoped>
.status-page {
  display: flex;
  min-height: 100vh;
  align-items: center;
  justify-content: center;
  padding: var(--space-8);
}

.status-card {
  display: flex;
  width: 100%;
  max-width: 720px;
  flex-direction: column;
  align-items: center;
  gap: var(--space-5);
  padding: var(--space-10);
  border: 1px solid rgba(215, 228, 216, 0.92);
  border-radius: 32px;
  background: rgba(255, 255, 255, 0.84);
  box-shadow: var(--shadow-soft);
  text-align: center;
}

.status-card__icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 140px;
  height: 140px;
  border-radius: 999px;
  background: rgba(76, 175, 80, 0.12);
  color: var(--admin-primary-deep);
  font-size: 42px;
  font-weight: 800;
}

.status-card__title {
  margin: 0;
  font-size: 32px;
}

.status-card__description {
  max-width: 560px;
  margin: 0;
  color: var(--admin-text-secondary);
  line-height: 1.8;
}

.status-card__actions {
  display: flex;
  gap: var(--space-3);
}
</style>
