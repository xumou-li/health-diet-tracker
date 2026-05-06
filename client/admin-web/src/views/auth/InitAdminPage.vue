<template>
  <div class="auth-page">
    <section class="auth-page__hero">
      <div class="auth-page__badge">初始化向导</div>
      <h1 class="auth-page__title">创建首个超级管理员账号</h1>
      <p class="auth-page__description">
        该页面只用于系统首次部署时创建管理员。若后端已经存在管理员，接口会直接拒绝重复初始化。
      </p>

      <div class="auth-page__notice">
        <div class="auth-page__notice-title">注意事项</div>
        <ul class="auth-page__notice-list">
          <li>默认建议使用易记但不弱的用户名。</li>
          <li>初始化完成后请立即回到登录页验证账号。</li>
          <li>后续的配置更新能力将根据管理员角色进行限制。</li>
        </ul>
      </div>
    </section>

    <section class="auth-page__panel">
      <div class="auth-card">
        <div class="auth-card__header">
          <div>
            <div class="page-eyebrow">首次部署</div>
            <h2 class="auth-card__title">初始化超级管理员</h2>
            <p class="auth-card__subtitle">将调用 POST /api/admin/auth/init。</p>
          </div>
          <el-tag type="warning" effect="light">仅首次可用</el-tag>
        </div>

        <el-form ref="formRef" :model="form" :rules="rules" label-position="top" class="auth-form">
          <el-form-item label="管理员用户名" prop="username">
            <el-input v-model="form.username" placeholder="例如：admin" />
          </el-form-item>

          <el-form-item label="管理员密码" prop="password">
            <el-input v-model="form.password" type="password" show-password placeholder="请输入密码" />
          </el-form-item>

          <el-form-item label="确认密码" prop="confirm_password">
            <el-input v-model="form.confirm_password" type="password" show-password placeholder="请再次输入密码" />
          </el-form-item>

          <div class="auth-card__actions">
            <el-button @click="router.push({ name: 'login' })">返回登录</el-button>
            <el-button type="primary" :loading="submitting" @click="handleSubmit">创建管理员</el-button>
          </div>
        </el-form>
      </div>
    </section>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { initAdmin } from '@/api/auth'

const router = useRouter()
const formRef = ref(null)
const submitting = ref(false)

const form = reactive({
  username: 'admin',
  password: 'admin123',
  confirm_password: 'admin123'
})

const validateConfirmPassword = (rule, value, callback) => {
  if (!value) {
    callback(new Error('请再次输入密码'))
    return
  }

  if (value !== form.password) {
    callback(new Error('两次输入的密码不一致'))
    return
  }

  callback()
}

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少 6 位', trigger: 'blur' }
  ],
  confirm_password: [{ validator: validateConfirmPassword, trigger: 'blur' }]
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
    await initAdmin({
      username: form.username,
      password: form.password
    })

    ElMessage.success('超级管理员创建成功，请使用新账号登录')
    router.replace({
      name: 'login',
      query: {
        username: form.username
      }
    })
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.auth-page {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(400px, 520px);
  min-height: 100vh;
  padding: var(--space-8);
  gap: var(--space-8);
}

.auth-page__hero,
.auth-page__panel {
  display: flex;
}

.auth-page__hero {
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
  background: rgba(196, 136, 19, 0.12);
  color: var(--admin-warning);
  font-size: var(--font-size-xs);
  font-weight: 700;
}

.auth-page__title {
  margin: 0;
  font-size: 44px;
  line-height: 1.15;
}

.auth-page__description {
  margin: 0;
  color: var(--admin-text-secondary);
  font-size: var(--font-size-lg);
  line-height: 1.8;
}

.auth-page__notice {
  padding: var(--space-6);
  border: 1px solid rgba(196, 136, 19, 0.18);
  border-radius: var(--radius-md);
  background: rgba(255, 248, 235, 0.82);
}

.auth-page__notice-title {
  font-weight: 700;
  margin-bottom: var(--space-3);
}

.auth-page__notice-list {
  margin: 0;
  padding-left: var(--space-5);
  color: var(--admin-text-secondary);
  line-height: 1.8;
}

.auth-page__panel {
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
}

.auth-card__actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-3);
  margin-top: var(--space-3);
}

@media (max-width: 1100px) {
  .auth-page {
    grid-template-columns: 1fr;
    padding: var(--space-5);
  }

  .auth-page__title {
    font-size: 34px;
  }
}
</style>
