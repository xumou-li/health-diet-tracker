<template>
  <div class="page-shell dashboard-page" v-loading="loading">
    <section class="page-header">
      <div class="page-header__content">
        <div class="page-eyebrow">后台首页</div>
        <h1 class="page-title">管理数据概览</h1>
        <p class="page-description">
          面板直接接入 <code>/api/admin/dashboard</code> 与 <code>/api/admin/stats/ai</code>，用于查看用户增长、记录活跃度、BMI 分布以及 AI 调用运行状态。
        </p>

        <div class="tag-row">
          <el-tag type="success" effect="light">GET /api/admin/dashboard</el-tag>
          <el-tag effect="plain">GET /api/admin/stats/ai</el-tag>
          <el-tag effect="plain">snake_case 字段直连后端</el-tag>
        </div>
      </div>

      <el-card class="panel-card dashboard-page__callout" shadow="never">
        <template #header>
          <span>运行状态</span>
        </template>

        <div class="dashboard-page__callout-content">
          <div class="dashboard-page__status">
            <span class="dashboard-page__status-dot"></span>
            <span>{{ sync_status_text }}</span>
          </div>

          <div class="dashboard-page__timestamp">
            <span class="dashboard-page__timestamp-label">最近刷新</span>
            <strong>{{ last_updated_at || '尚未同步' }}</strong>
          </div>

          <el-button type="primary" :loading="refreshing" @click="fetch_dashboard_data">
            刷新概览
          </el-button>
        </div>
      </el-card>
    </section>

    <section class="metric-grid">
      <article v-for="item in overview_metrics" :key="item.label" class="metric-card">
        <span class="metric-card__label">{{ item.label }}</span>
        <span class="metric-card__value">{{ item.value }}</span>
        <span class="metric-card__hint">{{ item.hint }}</span>
      </article>
    </section>

    <section class="panel-grid">
      <el-card class="panel-card section-card" shadow="never" style="grid-column: span 7;">
        <template #header>
          <div>
            <h2 class="section-title">BMI 分布</h2>
            <p class="section-description">
              数据来自 <code>bmi_distribution</code>，帮助管理员快速判断当前用户群体的体重结构分布。
            </p>
          </div>
        </template>

        <div v-if="bmi_total > 0" class="bmi-list">
          <div v-for="item in bmi_distribution_items" :key="item.key" class="bmi-item">
            <div class="bmi-item__meta">
              <div class="bmi-item__label-wrap">
                <span class="bmi-item__dot" :class="`is-${item.key}`"></span>
                <span class="bmi-item__label">{{ item.label }}</span>
              </div>
              <span class="bmi-item__count">{{ format_number(item.count) }} 人 · {{ item.percent_text }}</span>
            </div>

            <div class="bmi-item__track">
              <div class="bmi-item__bar" :class="`is-${item.key}`" :style="{ width: item.bar_width }"></div>
            </div>

            <p class="bmi-item__description">{{ item.description }}</p>
          </div>
        </div>

        <el-empty v-else description="暂无用户 BMI 数据" />
      </el-card>

      <el-card class="panel-card section-card" shadow="never" style="grid-column: span 5;">
        <template #header>
          <div>
            <h2 class="section-title">AI 调用摘要</h2>
            <p class="section-description">
              汇总今日与累计 AI 使用量、Token 消耗和响应时间，便于后台观察当前服务热度与性能状态。
            </p>
          </div>
        </template>

        <div class="ai-summary-grid">
          <div v-for="item in ai_summary_metrics" :key="item.label" class="ai-summary-card">
            <span class="ai-summary-card__label">{{ item.label }}</span>
            <strong class="ai-summary-card__value">{{ item.value }}</strong>
            <span class="ai-summary-card__hint">{{ item.hint }}</span>
          </div>
        </div>

        <div class="soft-divider"></div>

        <div class="type-list">
          <div class="type-list__item">
            <div class="type-list__meta">
              <span class="type-list__label">今日调用人数</span>
              <strong class="type-list__value">{{ format_number(ai_stats.today.today_users) }}</strong>
            </div>
            <div class="type-list__track">
              <div class="type-list__bar" :style="{ width: ai_stats.today.today_users > 0 ? '100%' : '12%' }"></div>
            </div>
          </div>
        </div>
      </el-card>

      <el-card class="panel-card section-card" shadow="never" style="grid-column: span 12;">
        <template #header>
          <div>
            <h2 class="section-title">运营提示</h2>
            <p class="section-description">
              基于当前接口数据生成的快捷解读，帮助管理端演示时快速说明平台现状。
            </p>
          </div>
        </template>

        <div class="info-list dashboard-insights">
          <div v-for="(item, index) in dashboard_insights" :key="item" class="info-list__item">
            <span class="info-list__bullet">{{ index + 1 }}</span>
            <div class="info-list__content">
              <span class="info-list__title">概览提示</span>
              <span class="info-list__text">{{ item }}</span>
            </div>
          </div>
        </div>
      </el-card>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { getAIStats } from '@/api/ai'
import { getDashboard } from '@/api/dashboard'

const loading = ref(true)
const refreshing = ref(false)
const last_updated_at = ref('')

const dashboard_data = reactive({
  users: {
    total: 0,
    today_new: 0,
    today_active: 0
  },
  records: {
    today: 0
  },
  bmi_distribution: {
    underweight: 0,
    normal: 0,
    overweight: 0,
    obese: 0
  }
})

const ai_stats = reactive({
  today: {
    total_calls: 0,
    today_users: 0,
    tokens_used: 0,
    avg_response_ms: 0
  },
  all_time: {
    total_calls: 0,
    total_tokens: 0
  }
})

const sync_status_text = computed(() => {
  if (loading.value) {
    return '正在同步后台数据...'
  }

  return last_updated_at.value ? '实时接口已接通' : '等待首次同步'
})

const overview_metrics = computed(() => [
  {
    label: '总用户数',
    value: format_number(dashboard_data.users.total),
    hint: `今日新增 ${format_number(dashboard_data.users.today_new)} 人`
  },
  {
    label: '今日活跃用户',
    value: format_number(dashboard_data.users.today_active),
    hint: '按今日产生饮食记录的去重用户统计'
  },
  {
    label: '今日记录数',
    value: format_number(dashboard_data.records.today),
    hint: '反映当天录入活跃度与留存温度'
  },
  {
    label: '今日 AI 调用',
    value: format_number(ai_stats.today.total_calls),
    hint: `平均响应 ${format_number(ai_stats.today.avg_response_ms)} ms`
  }
])

const bmi_total = computed(() => Object.values(dashboard_data.bmi_distribution).reduce((sum, count) => sum + Number(count || 0), 0))

const bmi_distribution_items = computed(() => {
  const total = bmi_total.value
  const distribution = dashboard_data.bmi_distribution

  return [
    {
      key: 'underweight',
      label: '偏瘦',
      description: 'BMI < 18.5，需要关注营养摄入与体重恢复。',
      count: distribution.underweight || 0
    },
    {
      key: 'normal',
      label: '正常',
      description: '18.5 ≤ BMI < 24，是当前最理想的体重结构区间。',
      count: distribution.normal || 0
    },
    {
      key: 'overweight',
      label: '超重',
      description: '24 ≤ BMI < 28，适合重点关注饮食干预与活动建议。',
      count: distribution.overweight || 0
    },
    {
      key: 'obese',
      label: '肥胖',
      description: 'BMI ≥ 28，可作为后台干预优先级更高的人群。',
      count: distribution.obese || 0
    }
  ].map((item) => {
    const percent = total > 0 ? Number(((item.count / total) * 100).toFixed(1)) : 0

    return {
      ...item,
      bar_width: `${percent}%`,
      percent_text: `${percent}%`
    }
  })
})

const ai_summary_metrics = computed(() => [
  {
    label: '今日 AI 调用',
    value: format_number(ai_stats.today.total_calls),
    hint: `今日 ${format_number(ai_stats.today.today_users)} 人使用`
  },
  {
    label: '今日平均响应',
    value: `${format_number(ai_stats.today.avg_response_ms)} ms`,
    hint: '按 response_time_ms 平均值展示'
  },
  {
    label: '累计调用量',
    value: format_number(ai_stats.all_time.total_calls),
    hint: '全周期 AI 请求总数'
  },
  {
    label: '累计 Token',
    value: format_number(ai_stats.all_time.total_tokens),
    hint: '便于观察模型消耗规模'
  }
])

const dashboard_insights = computed(() => {
  const total_users = dashboard_data.users.total || 0
  const today_new = dashboard_data.users.today_new || 0
  const today_active = dashboard_data.users.today_active || 0
  const today_records = dashboard_data.records.today || 0
  const top_bmi_item = bmi_distribution_items.value.slice().sort((current, next) => next.count - current.count)[0]
  const today_ai_users = Number(ai_stats.today.today_users) || 0
  const today_ai_calls = Number(ai_stats.today.total_calls) || 0

  return [
    `当前共有 ${format_number(total_users)} 位有效用户，今日新增 ${format_number(today_new)} 位，管理端可以直接用这组数据说明平台增长节奏。`,
    `今日活跃用户 ${format_number(today_active)} 位，对应 ${format_number(today_records)} 条饮食记录，能够快速反映当天记录热度。`,
    top_bmi_item
      ? `BMI 分布中"${top_bmi_item.label}"占比最高，为 ${top_bmi_item.percent_text}，适合作为后台首页的重点观察维度。`
      : 'BMI 分布数据暂未返回。',
    today_ai_users > 0
      ? `今日 ${format_number(today_ai_users)} 人使用 AI 功能，共发起 ${format_number(today_ai_calls)} 次调用，人均 ${(today_ai_calls / today_ai_users).toFixed(1)} 次。`
      : '今日暂无 AI 调用数据。'
  ]
})

function apply_dashboard_payload(payload) {
  dashboard_data.users.total = Number(payload?.users?.total || 0)
  dashboard_data.users.today_new = Number(payload?.users?.today_new || 0)
  dashboard_data.users.today_active = Number(payload?.users?.today_active || 0)
  dashboard_data.records.today = Number(payload?.records?.today || 0)
  dashboard_data.bmi_distribution.underweight = Number(payload?.bmi_distribution?.underweight || 0)
  dashboard_data.bmi_distribution.normal = Number(payload?.bmi_distribution?.normal || 0)
  dashboard_data.bmi_distribution.overweight = Number(payload?.bmi_distribution?.overweight || 0)
  dashboard_data.bmi_distribution.obese = Number(payload?.bmi_distribution?.obese || 0)
}

function apply_ai_stats_payload(payload) {
  ai_stats.today.total_calls = Number(payload?.today?.total_calls || 0)
  ai_stats.today.today_users = Number(payload?.today?.today_users || 0)
  ai_stats.today.tokens_used = Number(payload?.today?.tokens_used || 0)
  ai_stats.today.avg_response_ms = Number(payload?.today?.avg_response_ms || 0)
  ai_stats.all_time.total_calls = Number(payload?.all_time?.total_calls || 0)
  ai_stats.all_time.total_tokens = Number(payload?.all_time?.total_tokens || 0)
}

function format_number(value) {
  return Number(value || 0).toLocaleString('zh-CN')
}

async function fetch_dashboard_data() {
  const is_initial_loading = !last_updated_at.value

  if (is_initial_loading) {
    loading.value = true
  } else {
    refreshing.value = true
  }

  try {
    const [dashboard_result, ai_stats_result] = await Promise.allSettled([
      getDashboard(),
      getAIStats()
    ])

    let has_success = false

    if (dashboard_result.status === 'fulfilled') {
      apply_dashboard_payload(dashboard_result.value)
      has_success = true
    }

    if (ai_stats_result.status === 'fulfilled') {
      apply_ai_stats_payload(ai_stats_result.value)
      has_success = true
    }

    if (has_success) {
      last_updated_at.value = new Date().toLocaleString('zh-CN', {
        hour12: false,
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      })
    }
  } finally {
    loading.value = false
    refreshing.value = false
  }
}

onMounted(() => {
  fetch_dashboard_data()
})
</script>

<style scoped>
.dashboard-page code {
  padding: var(--space-1) var(--space-2);
  border-radius: var(--radius-sm);
  background: var(--admin-primary-soft);
  color: var(--admin-primary-deep);
  font-size: var(--font-size-sm);
}

.dashboard-page__callout {
  min-width: 0;
}

.dashboard-page__callout-content {
  display: flex;
  min-width: 320px;
  flex-direction: column;
  gap: var(--space-4);
}

.dashboard-page__status {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  color: var(--admin-text-secondary);
  font-size: var(--font-size-sm);
  font-weight: 600;
}

.dashboard-page__status-dot {
  width: var(--space-3);
  height: var(--space-3);
  border-radius: 999px;
  background: var(--admin-primary);
  box-shadow: 0 0 0 var(--space-1) rgba(76, 175, 80, 0.16);
}

.dashboard-page__timestamp {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.dashboard-page__timestamp-label {
  color: var(--admin-text-tertiary);
  font-size: var(--font-size-xs);
}

.bmi-list,
.type-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
}

.bmi-item,
.type-list__item {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.bmi-item__meta,
.type-list__meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-4);
}

.bmi-item__label-wrap {
  display: inline-flex;
  align-items: center;
  gap: var(--space-3);
}

.bmi-item__dot {
  width: var(--space-3);
  height: var(--space-3);
  border-radius: 999px;
}

.bmi-item__dot.is-underweight,
.bmi-item__bar.is-underweight {
  background: var(--admin-info);
}

.bmi-item__dot.is-normal,
.bmi-item__bar.is-normal {
  background: var(--admin-success);
}

.bmi-item__dot.is-overweight,
.bmi-item__bar.is-overweight {
  background: var(--admin-warning);
}

.bmi-item__dot.is-obese,
.bmi-item__bar.is-obese {
  background: var(--admin-danger);
}

.bmi-item__label,
.type-list__label {
  font-weight: 600;
}

.bmi-item__count,
.type-list__value {
  color: var(--admin-text-secondary);
  font-size: var(--font-size-sm);
}

.bmi-item__track,
.type-list__track {
  overflow: hidden;
  height: var(--space-3);
  border-radius: 999px;
  background: var(--admin-primary-soft);
}

.bmi-item__bar,
.type-list__bar {
  height: 100%;
  border-radius: 999px;
  transition: width 0.28s ease;
}

.bmi-item__description {
  margin: 0;
  color: var(--admin-text-secondary);
  line-height: 1.7;
}

.ai-summary-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--space-4);
}

.ai-summary-card {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  padding: var(--space-4);
  border: 1px solid rgba(215, 228, 216, 0.92);
  border-radius: var(--radius-md);
  background: rgba(255, 255, 255, 0.72);
}

.ai-summary-card__label {
  color: var(--admin-text-secondary);
  font-size: var(--font-size-sm);
}

.ai-summary-card__value {
  font-size: var(--font-size-xl);
}

.ai-summary-card__hint {
  color: var(--admin-text-tertiary);
  font-size: var(--font-size-xs);
  line-height: 1.6;
}

.type-list__bar {
  background: linear-gradient(90deg, var(--admin-primary), var(--admin-accent));
}

.dashboard-insights {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

@media (max-width: 960px) {
  .panel-grid :deep(.el-card) {
    grid-column: span 12 !important;
  }

  .dashboard-page__callout-content {
    min-width: auto;
  }

  .ai-summary-grid,
  .dashboard-insights {
    grid-template-columns: repeat(1, minmax(0, 1fr));
  }

  .bmi-item__meta,
  .type-list__meta {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
