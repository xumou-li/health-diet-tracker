<template>
  <div class="status-page">
    <div class="status-card">
      <div class="status-card__icon">403</div>
      <h1 class="status-card__title">当前账号没有访问此页面的权限</h1>
      <p class="status-card__description">
        如果这是课程演示环境，请使用具备权限的管理员账号登录，或联系超级管理员确认角色配置。
      </p>

      <div class="status-card__actions">
        <el-button @click="router.push({ name: 'login' })">返回登录</el-button>
        <el-button type="primary" @click="router.push({ name: 'dashboard' })">回到首页</el-button>
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
  background: rgba(217, 72, 65, 0.1);
  color: var(--admin-danger);
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
