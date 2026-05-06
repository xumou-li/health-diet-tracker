<template>
  <div class="page-shell">
    <section class="page-header">
      <div class="page-header__content">
        <div class="page-eyebrow">系统配置</div>
        <h1 class="page-title">AI 与系统参数配置</h1>
        <p class="page-description">
          页面直接对接 <code>GET /api/admin/config</code> 与 <code>PUT /api/admin/config</code>。
          超级管理员可编辑保存，普通管理员保持只读模式，并按后端规则隐藏敏感密钥字段。
        </p>
      </div>

      <div class="config-header-actions">
        <el-tag :type="isSuperAdmin ? 'success' : 'info'" effect="dark" round>
          {{ isSuperAdmin ? '超级管理员：可编辑' : '普通管理员：只读查看' }}
        </el-tag>
        <el-button :loading="loading" @click="loadConfig">刷新配置</el-button>
        <el-button
          v-if="isSuperAdmin"
          :disabled="!hasChanges || loading || saving"
          :loading="saving"
          type="primary"
          @click="saveConfig"
        >
          保存配置
        </el-button>
      </div>
    </section>

    <section class="metric-grid">
      <article class="metric-card">
        <span class="metric-card__label">AI 功能状态</span>
        <span class="metric-card__value">{{ form.ai_enabled ? '已启用' : '已关闭' }}</span>
        <span class="metric-card__hint">直接映射 ai_enabled，便于后台快速确认服务开关。</span>
      </article>
      <article class="metric-card">
        <span class="metric-card__label">每日调用限额</span>
        <span class="metric-card__value">{{ formatNumber(form.ai_daily_limit) }}</span>
        <span class="metric-card__hint">后端最小值为 1，保存时保持与服务端规则一致。</span>
      </article>
      <article class="metric-card">
        <span class="metric-card__label">默认模型</span>
        <span class="metric-card__value metric-card__value--compact">{{ form.ai_model || '未设置' }}</span>
        <span class="metric-card__hint">用于标识当前系统默认调用的 AI 模型。</span>
      </article>
      <article class="metric-card">
        <span class="metric-card__label">API Base URL</span>
        <span class="metric-card__value metric-card__value--compact">{{ form.ai_api_base_url || siliconFlowBaseUrl }}</span>
        <span class="metric-card__hint">优先使用数据库配置，留空时回退到环境变量或 SiliconFlow 默认地址。</span>
      </article>
      <article class="metric-card">
        <span class="metric-card__label">最近更新时间</span>
        <span class="metric-card__value metric-card__value--compact">{{ updatedAtText }}</span>
        <span class="metric-card__hint">字段来自 updated_at，保存成功后会以最新值回填。</span>
      </article>
    </section>

    <section class="panel-grid">
      <el-card class="panel-card section-card config-main-card" shadow="never">
        <template #header>
          <div class="section-headline">
            <div>
              <h2 class="section-title">配置详情</h2>
              <p class="section-description">
                表单字段保持 snake_case 直连后端，避免演示阶段出现命名转换误差。
              </p>
            </div>
            <el-button v-if="isSuperAdmin" :disabled="!hasChanges || saving" @click="resetForm">重置修改</el-button>
          </div>
        </template>

        <el-alert
          :closable="false"
          :title="isSuperAdmin ? '当前账号拥有配置编辑权限' : '当前账号仅可查看配置内容'"
          :type="isSuperAdmin ? 'success' : 'info'"
          show-icon
        >
          <template #default>
            <span>
              {{
                isSuperAdmin
                  ? '保存时会调用 PUT /api/admin/config，密钥字段会按当前输入值提交。'
                  : '普通管理员调用 GET /api/admin/config 时不会收到 ai_api_key，本页也不会伪造显示。'
              }}
            </span>
          </template>
        </el-alert>

        <el-form
          class="config-form"
          label-position="top"
          :model="form"
          :disabled="!isSuperAdmin || loading"
        >
          <div class="config-form__grid">
            <el-form-item label="AI 功能开关">
              <el-switch
                v-model="form.ai_enabled"
                inline-prompt
                active-text="开"
                inactive-text="关"
              />
            </el-form-item>

            <el-form-item label="每用户每日调用限额">
              <el-input-number
                v-model="form.ai_daily_limit"
                :min="1"
                :step="1"
                controls-position="right"
              />
            </el-form-item>
          </div>

          <el-form-item label="默认模型">
            <el-input v-model="form.ai_model" placeholder="例如 deepseek-chat" maxlength="50" show-word-limit />
          </el-form-item>

          <el-form-item label="AI API Base URL">
            <el-input
              v-model="form.ai_api_base_url"
              placeholder="https://api.siliconflow.cn/v1"
            />
            <div class="field-helper-text">
              建议填写完整基础地址。留空后将按后端规则回退到环境变量 <code>AI_API_BASE_URL</code>，若仍未配置则使用
              <code>{{ siliconFlowBaseUrl }}</code>。
            </div>
          </el-form-item>

          <el-form-item v-if="isSuperAdmin" label="AI API Key">
            <el-input
              v-model="form.ai_api_key"
              type="password"
              show-password
              placeholder="为空表示未配置，清空后保存会覆盖为留空"
            />
          </el-form-item>

          <div v-else class="sensitive-panel">
            <span class="sensitive-panel__label">AI API Key</span>
            <div class="sensitive-panel__body">
              <el-icon class="sensitive-panel__icon"><Lock /></el-icon>
              <div class="sensitive-panel__content">
                <strong>敏感字段已按后端权限规则隐藏</strong>
                <p>
                  当前接口响应未包含 <code>ai_api_key</code>，只有超级管理员读取配置时才能看到并编辑该字段。
                </p>
              </div>
            </div>
          </div>

          <el-form-item label="AI 提示词模板">
            <el-input
              v-model="form.ai_prompt_template"
              :autosize="{ minRows: 7, maxRows: 12 }"
              type="textarea"
              :placeholder="defaultPromptTemplate"
            />
            <div class="field-helper-text">
              留空时使用系统默认模板（如上占位符所示）。修改后优先使用自定义模板。
            </div>
          </el-form-item>

          <el-form-item label="系统公告">
            <el-input
              v-model="form.announcement"
              :autosize="{ minRows: 5, maxRows: 10 }"
              type="textarea"
              placeholder="输入 announcement 内容"
            />
          </el-form-item>
        </el-form>
      </el-card>

      <div class="config-side-stack">
        <el-card class="panel-card section-card" shadow="never">
          <template #header>
            <div>
              <h2 class="section-title">当前状态</h2>
              <p class="section-description">用更适合演示的方式整理真实配置，便于快速讲解系统开关与权限边界。</p>
            </div>
          </template>

          <div class="info-list config-status-list">
            <div class="info-list__item">
              <span class="info-list__bullet">01</span>
              <div class="info-list__content">
                <span class="info-list__title">权限模式</span>
                <span class="info-list__text">{{ isSuperAdmin ? '超级管理员可直接修改并保存配置。' : '普通管理员仅查看，不能提交更新请求。' }}</span>
              </div>
            </div>
            <div class="info-list__item">
              <span class="info-list__bullet">02</span>
              <div class="info-list__content">
                <span class="info-list__title">密钥展示</span>
                <span class="info-list__text">{{ isSuperAdmin ? '接口已返回 ai_api_key 字段，可按当前值编辑。' : '接口未返回 ai_api_key，本页明确展示为隐藏状态。' }}</span>
              </div>
            </div>
            <div class="info-list__item">
              <span class="info-list__bullet">03</span>
              <div class="info-list__content">
                <span class="info-list__title">请求地址</span>
                <span class="info-list__text">AI 调用优先读取数据库中的 <code>ai_api_base_url</code>，未填写时自动回退，兼容 SiliconFlow 默认地址。</span>
              </div>
            </div>
            <div class="info-list__item">
              <span class="info-list__bullet">04</span>
              <div class="info-list__content">
                <span class="info-list__title">配置内容</span>
                <span class="info-list__text">提示模板与公告均保留多行输入，适合课程演示中的真实维护场景。</span>
              </div>
            </div>
          </div>
        </el-card>

        <el-card class="panel-card section-card" shadow="never">
          <template #header>
            <div>
              <h2 class="section-title">保存预览</h2>
              <p class="section-description">仅展示本页实际会提交的字段，帮助避免误操作。</p>
            </div>
          </template>

          <div class="payload-preview">
            <pre>{{ payloadPreview }}</pre>
          </div>
        </el-card>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Lock } from '@element-plus/icons-vue'
import { getSystemConfig, updateSystemConfig } from '@/api/system'
import { useAuthStore } from '@/store/auth'
import { canEditSystemConfig } from '@/utils/admin'
import { formatDateTime, formatNumber, formatJson } from '@/utils/format'

const authStore = useAuthStore()
const siliconFlowBaseUrl = 'https://api.siliconflow.cn/v1'

const defaultPromptTemplate = `你是一个专业的营养师助手，名叫"小营"。
用户信息：性别{gender}，年龄{age}岁，BMI={bmi}({bmi_status})，健康目标={goal}
今日摄入：热量{calorie}kcal（目标{target_calorie}kcal），蛋白质{protein}g，脂肪{fat}g，碳水{carb}g

请根据用户的问题提供专业的饮食建议和解答。简洁友好，150字以内。非饮食话题礼貌引导回饮食。`

const loading = ref(false)
const saving = ref(false)
const baselinePayload = ref('')

const form = reactive(createDefaultConfig())

const isSuperAdmin = computed(() => canEditSystemConfig(authStore.user))
const updatedAtText = computed(() => formatDateTime(form.updated_at))
const payloadPreview = computed(() => {
  const payload = { ...buildPayload(form, isSuperAdmin.value) }
  if (payload.ai_api_key && payload.ai_api_key.length > 4) {
    payload.ai_api_key = '***' + payload.ai_api_key.slice(-4)
  }
  return formatJson(payload)
})
const hasChanges = computed(() => formatJson(buildPayload(form, isSuperAdmin.value)) !== baselinePayload.value)

function createDefaultConfig() {
  return {
    id: null,
    ai_enabled: true,
    ai_daily_limit: 10,
    ai_model: 'deepseek-chat',
    ai_api_key: '',
    ai_api_base_url: siliconFlowBaseUrl,
    ai_prompt_template: '',
    announcement: '',
    updated_at: ''
  }
}

function normalizeText(value) {
  return typeof value === 'string' ? value : value || ''
}

function buildPayload(config, includeApiKey) {
  const payload = {
    ai_enabled: Boolean(config.ai_enabled),
    ai_daily_limit: Math.max(1, Number(config.ai_daily_limit) || 1),
    ai_model: normalizeText(config.ai_model),
    ai_api_base_url: normalizeText(config.ai_api_base_url),
    ai_prompt_template: normalizeText(config.ai_prompt_template),
    announcement: normalizeText(config.announcement)
  }

  if (includeApiKey) {
    payload.ai_api_key = normalizeText(config.ai_api_key)
  }

  return payload
}

function applyConfig(data) {
  const nextState = createDefaultConfig()

  Object.assign(nextState, {
    id: data?.id ?? nextState.id,
    ai_enabled: typeof data?.ai_enabled === 'boolean' ? data.ai_enabled : nextState.ai_enabled,
    ai_daily_limit: Number(data?.ai_daily_limit) || nextState.ai_daily_limit,
    ai_model: normalizeText(data?.ai_model),
    ai_api_base_url: normalizeText(data?.ai_api_base_url) || nextState.ai_api_base_url,
    ai_prompt_template: normalizeText(data?.ai_prompt_template),
    announcement: normalizeText(data?.announcement),
    updated_at: normalizeText(data?.updated_at)
  })

  if (Object.prototype.hasOwnProperty.call(data || {}, 'ai_api_key')) {
    nextState.ai_api_key = normalizeText(data?.ai_api_key)
  }

  Object.assign(form, nextState)
  baselinePayload.value = formatJson(buildPayload(form, isSuperAdmin.value))
}

async function loadConfig() {
  loading.value = true

  try {
    const data = await getSystemConfig()
    applyConfig(data)
  } finally {
    loading.value = false
  }
}

function resetForm() {
  const data = JSON.parse(baselinePayload.value)
  Object.assign(form, createDefaultConfig(), {
    ...form,
    ...data,
    updated_at: form.updated_at,
    id: form.id
  })
}

async function saveConfig() {
  if (!isSuperAdmin.value) {
    return
  }

  saving.value = true

  try {
    const updatedConfig = await updateSystemConfig(buildPayload(form, true))
    applyConfig(updatedConfig)
    ElMessage.success('系统配置已更新')
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  loadConfig()
})
</script>

<style scoped>
.config-header-actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: flex-end;
  gap: var(--space-3);
}

.config-main-card {
  grid-column: span 8;
}

.config-side-stack {
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
  grid-column: span 4;
}

.section-headline {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-4);
}

.config-form {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  margin-top: var(--space-6);
}

.config-form__grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--space-4);
}

.sensitive-panel {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  margin-bottom: var(--space-6);
}

.field-helper-text {
  margin-top: var(--space-2);
  color: var(--admin-text-secondary);
  font-size: var(--font-size-sm);
  line-height: 1.7;
}

.sensitive-panel__label {
  font-size: var(--font-size-md);
  font-weight: 600;
}

.sensitive-panel__body {
  display: flex;
  gap: var(--space-4);
  padding: var(--space-5);
  border: 1px solid var(--admin-border);
  border-radius: var(--radius-md);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.88), rgba(232, 245, 233, 0.72));
}

.sensitive-panel__icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: var(--space-10);
  height: var(--space-10);
  border-radius: 999px;
  background: var(--admin-primary-wash);
  color: var(--admin-primary-deep);
  flex-shrink: 0;
}

.sensitive-panel__content {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.sensitive-panel__content p {
  margin: 0;
  color: var(--admin-text-secondary);
  line-height: 1.7;
}

.config-status-list {
  margin-top: 0;
}

.payload-preview {
  padding: var(--space-4);
  border-radius: var(--radius-md);
  background: rgba(17, 33, 23, 0.94);
  box-shadow: var(--shadow-card);
  overflow: auto;
}

.payload-preview pre {
  margin: 0;
  color: var(--admin-text-light);
  font-size: var(--font-size-sm);
  line-height: 1.7;
  white-space: pre-wrap;
  word-break: break-word;
}

.metric-card__value--compact {
  font-size: var(--font-size-xl);
  line-height: 1.4;
}

code {
  padding: 0 var(--space-2);
  border-radius: var(--radius-sm);
  background: var(--admin-primary-soft);
  color: var(--admin-primary-deep);
}

@media (max-width: 1080px) {
  .config-main-card,
  .config-side-stack {
    grid-column: span 12;
  }
}

@media (max-width: 768px) {
  .section-headline,
  .config-form__grid {
    grid-template-columns: repeat(1, minmax(0, 1fr));
    display: grid;
  }

  .section-headline {
    gap: var(--space-3);
  }

  .config-header-actions {
    justify-content: flex-start;
  }
}
</style>
