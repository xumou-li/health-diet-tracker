<template>
  <div class="page-shell">
    <section class="page-header">
      <div class="page-header__content">
        <div class="page-eyebrow">AI 统计</div>
        <h1 class="page-title">AI 调用汇总看板</h1>
        <p class="page-description">
          页面直接展示 <code>GET /api/admin/stats/ai</code> 返回的 today / all_time 汇总数据，
          关注调用量、人数、Token 消耗与响应时间。
        </p>
      </div>

      <div class="stats-header-actions">
        <el-tag type="success" round>汇总数据模式</el-tag>
        <el-button :loading="loading" @click="loadStats">刷新统计</el-button>
      </div>
    </section>

    <section class="metric-grid">
      <article v-for="item in summaryCards" :key="item.label" class="metric-card">
        <span class="metric-card__label">{{ item.label }}</span>
        <span class="metric-card__value">{{ item.value }}</span>
        <span class="metric-card__hint">{{ item.hint }}</span>
      </article>
    </section>

    <section class="panel-grid">
      <el-card class="panel-card section-card stats-main-card" shadow="never">
        <template #header>
          <div>
            <h2 class="section-title">今日概览</h2>
            <p class="section-description">AI 服务今日运行状态一览，聚焦调用量与用户体验指标。</p>
          </div>
        </template>

        <div class="type-stat-list">
          <div class="type-stat-card">
            <div class="type-stat-card__top">
              <div>
                <div class="type-stat-card__label">今日调用次数</div>
                <div class="type-stat-card__value">{{ formatNumber(stats.today.total_calls) }}</div>
              </div>
              <el-tag type="primary" round>调用量</el-tag>
            </div>
            <el-progress
              :percentage="Math.min(100, Math.round((stats.today.total_calls / Math.max(stats.all_time.total_calls, 1)) * 100))"
              :show-text="false"
              :stroke-width="10"
            />
            <div class="type-stat-card__hint">占累计调用 {{ allTimeCallShare }}%</div>
          </div>

          <div class="type-stat-card">
            <div class="type-stat-card__top">
              <div>
                <div class="type-stat-card__label">今日调用人数</div>
                <div class="type-stat-card__value">{{ formatNumber(stats.today.today_users) }}</div>
              </div>
              <el-tag type="success" round>活跃用户</el-tag>
            </div>
            <el-progress
              :percentage="stats.today.today_users > 0 ? 100 : 0"
              :show-text="false"
              :stroke-width="10"
            />
            <div class="type-stat-card__hint">去重用户数，反映AI功能覆盖面</div>
          </div>

          <div class="type-stat-card">
            <div class="type-stat-card__top">
              <div>
                <div class="type-stat-card__label">今日 Token 消耗</div>
                <div class="type-stat-card__value">{{ formatNumber(stats.today.tokens_used) }}</div>
              </div>
              <el-tag type="warning" round>成本</el-tag>
            </div>
            <el-progress
              :percentage="allTimeTokens > 0 ? Math.min(100, Math.round((stats.today.tokens_used / allTimeTokens) * 100)) : 0"
              :show-text="false"
              :stroke-width="10"
            />
            <div class="type-stat-card__hint">累计 Token {{ formatNumber(stats.all_time.total_tokens) }}</div>
          </div>

          <div class="type-stat-card">
            <div class="type-stat-card__top">
              <div>
                <div class="type-stat-card__label">平均响应时间</div>
                <div class="type-stat-card__value">{{ formatMilliseconds(stats.today.avg_response_ms) }}</div>
              </div>
              <el-tag type="info" round>性能</el-tag>
            </div>
            <el-progress
              :percentage="avgResponseLevel"
              :show-text="false"
              :stroke-width="10"
            />
            <div class="type-stat-card__hint">{{ avgResponseHint }}</div>
          </div>
        </div>
      </el-card>

      <div class="stats-side-stack">
        <el-card class="panel-card section-card" shadow="never">
          <template #header>
            <div>
              <h2 class="section-title">关键信号</h2>
              <p class="section-description">从现有汇总数据提炼的观察点。</p>
            </div>
          </template>

          <div class="info-list stats-insights-list">
            <div v-for="(item, index) in insights" :key="item.title" class="info-list__item">
              <span class="info-list__bullet">{{ String(index + 1).padStart(2, '0') }}</span>
              <div class="info-list__content">
                <span class="info-list__title">{{ item.title }}</span>
                <span class="info-list__text">{{ item.text }}</span>
              </div>
            </div>
          </div>
        </el-card>

        <el-card class="panel-card section-card" shadow="never">
          <template #header>
            <div>
              <h2 class="section-title">原始汇总预览</h2>
              <p class="section-description">便于核对演示页面与接口返回的一致性。</p>
            </div>
          </template>

          <div class="stats-payload-preview">
            <pre>{{ payloadPreview }}</pre>
          </div>
        </el-card>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { getAIStats } from '@/api/ai'
import { formatJson, formatMilliseconds, formatNumber } from '@/utils/format'

const loading = ref(false)
const stats = ref(createEmptyStats())

const summaryCards = computed(() => [
  {
    label: '今日调用次数',
    value: formatNumber(stats.value.today.total_calls),
    hint: '今日 AI 请求总量。'
  },
  {
    label: '今日调用人数',
    value: formatNumber(stats.value.today.today_users),
    hint: '去重用户数，反映日活覆盖。'
  },
  {
    label: '今日 Token 消耗',
    value: formatNumber(stats.value.today.tokens_used),
    hint: '今日调用成本参考。'
  },
  {
    label: '累计调用次数',
    value: formatNumber(stats.value.all_time.total_calls),
    hint: 'AI 功能的长期使用规模。'
  }
])

const allTimeCallShare = computed(() => {
  const all = Number(stats.value.all_time.total_calls) || 0
  const today = Number(stats.value.today.total_calls) || 0
  return all > 0 ? `${Math.round((today / all) * 100)}` : '0'
})

const allTimeTokens = computed(() => Number(stats.value.all_time.total_tokens) || 0)

const avgResponseLevel = computed(() => {
  const ms = Number(stats.value.today.avg_response_ms) || 0
  if (ms === 0) return 0
  if (ms < 1000) return 80
  if (ms < 2000) return 60
  if (ms < 3000) return 40
  return 20
})

const avgResponseHint = computed(() => {
  const ms = Number(stats.value.today.avg_response_ms) || 0
  if (ms === 0) return '暂无数据'
  if (ms < 1000) return '响应迅速，体验良好'
  if (ms < 2000) return '响应正常'
  if (ms < 3000) return '响应偏慢，需关注'
  return '响应较慢，建议排查'
})

const insights = computed(() => {
  const todayCalls = Number(stats.value.today.total_calls) || 0
  const todayUsers = Number(stats.value.today.today_users) || 0
  const avgPerUser = todayUsers > 0 ? (todayCalls / todayUsers).toFixed(1) : '0'
  const allTimeCalls = Number(stats.value.all_time.total_calls) || 0
  const callShare = allTimeCalls > 0 ? Math.round((todayCalls / allTimeCalls) * 100) : 0

  return [
    {
      title: '人均调用次数',
      text: `今日 ${formatNumber(todayUsers)} 人共发起 ${formatNumber(todayCalls)} 次调用，人均约 ${avgPerUser} 次，反映用户粘性。`
    },
    {
      title: '今日对累计规模的贡献',
      text: `今日调用占累计调用的 ${callShare}%，累计 Token 已达 ${formatNumber(stats.value.all_time.total_tokens)}。`
    },
    {
      title: '响应时间评估',
      text: `今日平均响应时间 ${formatMilliseconds(stats.value.today.avg_response_ms)}。${avgResponseHint.value}。`
    }
  ]
})

const payloadPreview = computed(() => formatJson(stats.value))

function createEmptyStats() {
  return {
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
  }
}

async function loadStats() {
  loading.value = true

  try {
    const data = await getAIStats()
    stats.value = {
      ...createEmptyStats(),
      ...data,
      today: {
        ...createEmptyStats().today,
        ...(data?.today || {})
      },
      all_time: {
        ...createEmptyStats().all_time,
        ...(data?.all_time || {})
      }
    }
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadStats()
})
</script>

<style scoped>
.stats-header-actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: flex-end;
  gap: var(--space-3);
}

.stats-main-card {
  grid-column: span 8;
}

.stats-side-stack {
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
  grid-column: span 4;
}

.type-stat-list {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--space-4);
}

.type-stat-card {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  padding: var(--space-5);
  border: 1px solid rgba(215, 228, 216, 0.9);
  border-radius: var(--radius-md);
  background: rgba(255, 255, 255, 0.78);
}

.type-stat-card__top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-3);
}

.type-stat-card__label {
  color: var(--admin-text-secondary);
  font-size: var(--font-size-sm);
}

.type-stat-card__value {
  margin-top: var(--space-2);
  font-size: var(--font-size-xl);
  font-weight: 700;
}

.type-stat-card__hint {
  color: var(--admin-text-secondary);
  font-size: var(--font-size-sm);
  line-height: 1.7;
}

.stats-insights-list {
  margin-top: 0;
}

.stats-payload-preview {
  padding: var(--space-4);
  border-radius: var(--radius-md);
  background: rgba(17, 33, 23, 0.94);
  box-shadow: var(--shadow-card);
  overflow: auto;
}

.stats-payload-preview pre {
  margin: 0;
  color: var(--admin-text-light);
  font-size: var(--font-size-sm);
  line-height: 1.8;
  white-space: pre-wrap;
  word-break: break-word;
}

code {
  padding: 0 var(--space-2);
  border-radius: var(--radius-sm);
  background: var(--admin-primary-soft);
  color: var(--admin-primary-deep);
}

@media (max-width: 1080px) {
  .stats-main-card,
  .stats-side-stack {
    grid-column: span 12;
  }
}

@media (max-width: 768px) {
  .stats-header-actions {
    justify-content: flex-start;
  }

  .type-stat-list {
    grid-template-columns: repeat(1, minmax(0, 1fr));
  }
}
</style>
