<template>
  <div class="auth-page">
    <section class="auth-page__hero">
      <div class="auth-page__badge">个人健康饮食记录系统</div>
      <h1 class="auth-page__title">为桌面管理场景准备的绿色管理后台</h1>
      <p class="auth-page__description">
        已内置鉴权守卫、请求封装、布局骨架与模块路由，适合后续继续叠加用户、食物、分类、配置与 AI 功能页面。
      </p>

      <div class="auth-page__feature-list">
        <div class="auth-page__feature-item">
          <span class="auth-page__feature-title">统一接口封装</span>
          <span class="auth-page__feature-text">按 `{ code, message, data }` 解析响应，并默认使用 `/api/admin` 前缀。</span>
        </div>
        <div class="auth-page__feature-item">
          <span class="auth-page__feature-title">独立登录态存储</span>
          <span class="auth-page__feature-text">管理员令牌与用户信息使用 `admin_token`、`admin_user`，不会影响 uni-app 用户端。</span>
        </div>
        <div class="auth-page__feature-item">
          <span class="auth-page__feature-title">视觉连续性</span>
          <span class="auth-page__feature-text">沿用用户端的 #4caf50 绿色方向，让前后台保持统一气质。</span>
        </div>
      </div>
    </section>

    <section class="auth-page__panel">
      <div class="auth-card">
        <div class="auth-card__header">
          <div>
            <div class="page-eyebrow">管理员入口</div>
            <h2 class="auth-card__title">登录后台</h2>
            <p class="auth-card__subtitle">请输入管理员账号与密码。</p>
          </div>
          <el-tag type="success" effect="light">Desktop SPA</el-tag>
        </div>

        <el-form
          ref="formRef"
          :model="form"
          :rules="rules"
          label-position="top"
          class="auth-form"
          @keyup.enter="handleSubmit"
        >
          <el-form-item label="用户名" prop="username">
            <el-input v-model="form.username" placeholder="请输入管理员用户名">
              <template #prefix>
                <el-icon><User /></el-icon>
              </template>
            </el-input>
          </el-form-item>

          <el-form-item label="密码" prop="password">
            <el-input
              v-model="form.password"
              type="password"
              show-password
              placeholder="请输入管理员密码"
            >
              <template #prefix>
                <el-icon><Lock /></el-icon>
              </template>
            </el-input>
          </el-form-item>

          <el-button type="primary" class="auth-form__submit" :loading="submitting" @click="handleSubmit">
            登录管理后台
          </el-button>
        </el-form>

        <div class="auth-card__footer">
          <span>首次启动且尚未创建管理员？</span>
          <router-link class="auth-card__link" :to="{ name: 'init-admin' }">前往初始化超级管理员</router-link>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Lock, User } from '@element-plus/icons-vue'
import { adminLogin } from '@/api/auth'
import { useAuthStore } from '@/store/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const formRef = ref(null)
const submitting = ref(false)

const form = reactive({
  username: '',
  password: ''
})

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

async function handleSubmit() {
  if (!formRef.value) {
    return
  }

  const valid = await formRef.value.validate().catch(() => false)

  if (!valid) {
    return
  }

  submitting.value = true

  try {
    const data = await adminLogin(form)
    authStore.setAuth(data)
    ElMessage.success('登录成功')

    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '/dashboard'
    router.replace(redirect)
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  if (typeof route.query.username === 'string') {
    form.username = route.query.username
  }
})
</script>

<style scoped>
.auth-page {
  display: grid;
  grid-template-columns: minmax(0, 1.2fr) minmax(380px, 520px);
  min-height: 100vh;
  padding: var(--space-8);
  gap: var(--space-8);
}

.auth-page__hero,
.auth-page__panel {
  position: relative;
}

.auth-page__hero {
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: var(--space-6);
  padding: var(--space-10);
  border: 1px solid rgba(215, 228, 216, 0.92);
  border-radius: 32px;
  background:
    linear-gradient(140deg, rgba(255, 255, 255, 0.88), rgba(232, 245, 233, 0.72)),
    var(--admin-bg-panel);
  box-shadow: var(--shadow-soft);
}

.auth-page__badge {
  display: inline-flex;
  width: fit-content;
  padding: var(--space-2) var(--space-4);
  border-radius: 999px;
  background: var(--admin-primary-wash);
  color: var(--admin-primary-deep);
  font-size: var(--font-size-xs);
  font-weight: 700;
  letter-spacing: 0.08em;
}

.auth-page__title {
  max-width: 680px;
  margin: 0;
  font-size: 48px;
  line-height: 1.1;
}

.auth-page__description {
  max-width: 720px;
  margin: 0;
  color: var(--admin-text-secondary);
  font-size: var(--font-size-lg);
  line-height: 1.8;
}

.auth-page__feature-list {
  display: grid;
  grid-template-columns: repeat(1, minmax(0, 1fr));
  gap: var(--space-4);
}

.auth-page__feature-item {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  padding: var(--space-5);
  border: 1px solid rgba(215, 228, 216, 0.9);
  border-radius: var(--radius-md);
  background: rgba(255, 255, 255, 0.72);
}

.auth-page__feature-title {
  font-weight: 700;
}

.auth-page__feature-text {
  color: var(--admin-text-secondary);
  line-height: 1.7;
}

.auth-page__panel {
  display: flex;
  align-items: center;
  justify-content: center;
}

.auth-card {
  width: 100%;
  padding: var(--space-8);
  border: 1px solid rgba(215, 228, 216, 0.92);
  border-radius: 32px;
  background: rgba(255, 255, 255, 0.86);
  box-shadow: var(--shadow-soft);
  backdrop-filter: blur(18px);
}

.auth-card__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-4);
  margin-bottom: var(--space-6);
}

.auth-card__title {
  margin: var(--space-3) 0 var(--space-2);
  font-size: 32px;
}

.auth-card__subtitle {
  margin: 0;
  color: var(--admin-text-secondary);
}

.auth-form {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.auth-form__submit {
  width: 100%;
  min-height: 48px;
  margin-top: var(--space-2);
}

.auth-card__footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-4);
  margin-top: var(--space-6);
  color: var(--admin-text-secondary);
  font-size: var(--font-size-sm);
}

.auth-card__link {
  color: var(--admin-primary-deep);
  font-weight: 600;
}

@media (max-width: 1100px) {
  .auth-page {
    grid-template-columns: 1fr;
    padding: var(--space-5);
  }

  .auth-page__title {
    font-size: 36px;
  }
}
</style>
