<template>
  <view class="body-history-container">
  <scroll-view class="page-scroll" scroll-y>
  <view class="body-history-page">
    <view v-if="loading" class="state-card">
      <text class="state-icon">⏳</text>
      <text class="state-title">正在加载体重记录</text>
      <text class="state-desc">正在同步最近30天趋势和身体档案历史</text>
    </view>

    <view v-else-if="errorMessage" class="state-card">
      <text class="state-icon">⚠️</text>
      <text class="state-title">体重历史加载失败</text>
      <text class="state-desc">{{ errorMessage }}</text>
      <button class="state-button" @click="fetchData">重新加载</button>
    </view>

    <block v-else>
      <view class="summary-card">
        <view class="section-head">
          <view>
            <text class="section-title">{{ trendTitle }}</text>
            <text class="section-subtitle">{{ trendPeriodText }}</text>
          </view>
          <view class="change-badge" :class="trendChangeClass">
            {{ trendChangeLabel }}
          </view>
        </view>

        <view class="trend-tabs" role="tablist" aria-label="体重趋势周期切换">
          <view
            v-for="option in trendOptions"
            :key="option.days"
            class="trend-tab"
            :class="{ 'trend-tab--active': trendTabDays === option.days, 'trend-tab--disabled': trendLoading }"
            @click="switchTrendDays(option.days)"
          >
            {{ option.label }}
          </view>
        </view>

        <view class="summary-grid">
          <view class="summary-item summary-item--highlight">
            <text class="summary-label">当前体重</text>
            <text class="summary-value">{{ formatWeight(trendSummary.current_weight) }}</text>
          </view>
          <view class="summary-item">
            <text class="summary-label">{{ trendSummaryLabel }}</text>
            <text class="summary-value" :class="trendChangeClass">{{ formatSignedWeight(trendSummary.weight_change) }}</text>
          </view>
          <view class="summary-item">
            <text class="summary-label">记录次数</text>
            <text class="summary-value">{{ trendRecordsCount }}</text>
          </view>
        </view>

        <view v-if="trendLoading" class="trend-inline-state">
          <text class="trend-inline-state__icon">⏳</text>
          <text class="trend-inline-state__text">正在加载{{ trendTabLabel }}趋势…</text>
        </view>

          <view v-if="weightChartData.length" class="trend-panel">
            <view class="trend-chart-card">
              <view class="trend-chart-title-row">
                <text class="trend-chart-title">体重趋势</text>
              </view>
              <view class="chart-container">
                <body-trend-chart
                  canvas-id="weightTrendChart"
                  :categories="weightChartCategories"
                  :series="weightChartSeries"
                  :visible-count="trendVisibleCount"
                  :label-step="trendLabelStep"
                  color="#4CAF50"
                  background-color="#F8FAF8"
                  y-axis-title="kg"
                  unit-suffix="kg"
                />
              </view>
            </view>

            <view class="trend-chart-card trend-chart-card--secondary">
              <view class="trend-chart-title-row">
                <text class="trend-chart-title">BMI趋势</text>
              </view>
              <view class="chart-container">
                <body-trend-chart
                  canvas-id="bmiTrendChart"
                  :categories="bmiChartCategories"
                  :series="bmiChartSeries"
                  :visible-count="trendVisibleCount"
                  :label-step="trendLabelStep"
                  color="#42A5F5"
                  background-color="#F7F9FF"
                  y-axis-title="BMI"
                />
              </view>
            </view>

        </view>

        <view v-else class="inline-empty">
          <text class="inline-empty-title">{{ trendEmptyTitle }}</text>
          <text class="inline-empty-desc">更新身体档案后，这里会自动展示趋势变化。</text>
        </view>
      </view>

      <view class="history-card">
        <view class="section-head section-head--history">
          <view>
            <text class="section-title">身体记录历史</text>
            <text class="section-subtitle">近{{ trendDays }}天的记录</text>
          </view>
          <text class="history-total">共 {{ historyTotal }} 条</text>
        </view>

        <view v-if="historyRecords.length" class="history-list">
          <view v-for="record in historyRecords" :key="record.id" class="history-item">
            <view class="history-top">
              <view class="history-main">
                <text class="history-weight">{{ formatWeight(record.weight_kg) }}</text>
                <text class="history-time">{{ formatDateTime(record.recorded_at) }}</text>
              </view>
              <text v-if="record.weight_change !== null" class="history-change" :class="getChangeClass(record.weight_change)">
                较上次 {{ formatSignedWeight(record.weight_change) }}
              </text>
              <text v-else class="history-change history-change--muted">首条记录</text>
            </view>

            <view class="metric-grid">
              <view class="metric-chip">
                <text class="metric-label">BMI</text>
                <text class="metric-value">{{ formatValue(record.bmi, 1) }}</text>
              </view>
              <view class="metric-chip">
                <text class="metric-label">身高</text>
                <text class="metric-value">{{ formatInteger(record.height_cm) }} cm</text>
              </view>
              <view class="metric-chip">
                <text class="metric-label">BMR</text>
                <text class="metric-value">{{ formatInteger(record.bmr) }} kcal</text>
              </view>
              <view class="metric-chip">
                <text class="metric-label">热量目标</text>
                <text class="metric-value">{{ formatInteger(record.daily_calorie_goal) }} kcal</text>
              </view>
            </view>
          </view>
        </view>

        <view v-else class="inline-empty inline-empty--history">
          <text class="inline-empty-title">还没有身体记录历史</text>
          <text class="inline-empty-desc">首次保存身体档案后，这里会按时间倒序展示你的体重变化。</text>
        </view>
      </view>
    </block>
  </view>
  </scroll-view>
  </view>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import dayjs from 'dayjs'
import BodyTrendChart from '@/components/body-trend-chart.vue'
import { getBodyHistory } from '@/api/user'
import { getWeightTrend } from '@/api/stats'

const systemInfo = uni.getSystemInfoSync()
const isNarrowViewport = (systemInfo.windowWidth || 0) <= 375

const loading = ref(true)
const errorMessage = ref('')
const trendSummary = ref({
  start_weight: null,
  current_weight: null,
  weight_change: 0,
  bmi_change: 0
})
const trendOptions = [
  { days: 7, label: '7天' },
  { days: 30, label: '30天' }
]
const trendDays = ref(7)
const trendTabDays = ref(7)
const trendLoading = ref(false)
const trendPeriod = ref('')
const trendRecords = ref([])
const historyRecords = ref([])
const historyTotal = ref(0)

const trendTitle = computed(() => `近${trendDays.value}天体重趋势`)

const trendTabLabel = computed(() => {
  return trendOptions.find(option => option.days === trendTabDays.value)?.label || `${trendTabDays.value}天`
})

const trendPeriodText = computed(() => trendPeriod.value || `最近${trendDays.value}天`)

const trendSummaryLabel = computed(() => `${trendDays.value}天变化`)

const trendEmptyTitle = computed(() => `近${trendDays.value}天暂无新增体重记录`)

const trendRecordsCount = computed(() => {
  return `${trendRecords.value.length} 次`
})

const trendChangeClass = computed(() => {
  return getChangeClass(trendSummary.value.weight_change)
})

const trendChangeLabel = computed(() => {
  const change = Number(trendSummary.value.weight_change || 0)
  if (change > 0) return `近${trendDays.value}天上升`
  if (change < 0) return `近${trendDays.value}天下降`
  return `近${trendDays.value}天持平`
})

const filledTrendRecords = computed(() => {
  const recordMap = new Map()

  trendRecords.value.forEach((item) => {
    if (!item?.date) return
    recordMap.set(item.date, item)
  })

  // 短周期填充缺失值，长周期同样填充避免图表断线
  const shouldFill = true
  const records = []
  let lastKnownWeight = null
  let lastKnownBmi = null

  // 短周期先找今天或之前的最近记录作为初始值，避免开头全是 null
  if (shouldFill) {
    const initialRecord = [...trendRecords.value]
      .filter((r) => r?.date && !dayjs(r.date).isAfter(dayjs(), 'day'))
      .sort((a, b) => dayjs(b.date).valueOf() - dayjs(a.date).valueOf())[0]

    if (initialRecord) {
      lastKnownWeight = Number(initialRecord.weight)
      lastKnownBmi = Number(initialRecord.bmi)
    }
  }

  for (let i = trendDays.value - 1; i >= 0; i -= 1) {
    const currentDate = dayjs().subtract(i, 'day')
    const dateKey = currentDate.format('YYYY-MM-DD')
    const record = recordMap.get(dateKey)

    if (record) {
      lastKnownWeight = Number(record.weight)
      lastKnownBmi = Number(record.bmi)
    }

    records.push({
      date: dateKey,
      label: currentDate.format('MM/DD'),
      weight: record ? Number(record.weight) : (shouldFill ? lastKnownWeight : null),
      bmi: record ? Number(record.bmi) : (shouldFill ? lastKnownBmi : null),
      hasRecord: !!record
    })
  }

  // 反转回从近到远的展示顺序（与图表 x 轴从左到右一致）
  return records.reverse()
})

const weightChartData = computed(() => {
  return filledTrendRecords.value.map((item, index) => ({
    key: `${item.date || 'weight'}-${index}`,
    label: item.label,
    value: Number.isFinite(item.weight) ? item.weight : null,
    display: Number.isFinite(item.weight) ? formatValue(item.weight, 1) : ''
  }))
})

const bmiChartData = computed(() => {
  return filledTrendRecords.value.map((item, index) => ({
    key: `${item.date || 'bmi'}-${index}`,
    label: item.label,
    value: Number.isFinite(item.bmi) ? item.bmi : null,
    display: Number.isFinite(item.bmi) ? formatValue(item.bmi, 1) : ''
  }))
})

const weightChartCategories = computed(() => {
  return weightChartData.value.map(item => item.label)
})

const bmiChartCategories = computed(() => {
  return bmiChartData.value.map(item => item.label)
})

const weightChartSeries = computed(() => {
  const data = filledTrendRecords.value.map((item) =>
    Number.isFinite(item.weight) ? item.weight : null
  )

  return [
    {
      name: '体重',
      color: '#4CAF50',
      data,
      pointShape: 'none'
    }
  ]
})

const bmiChartSeries = computed(() => {
  const data = filledTrendRecords.value.map((item) =>
    Number.isFinite(item.bmi) ? item.bmi : null
  )

  return [
    {
      name: 'BMI',
      color: '#42A5F5',
      data,
      pointShape: 'none'
    }
  ]
})

const trendVisibleCount = computed(() => {
  if (!isNarrowViewport) return trendDays.value
  return trendDays.value <= 7 ? 5 : 6
})

const trendLabelStep = computed(() => {
  if (!isNarrowViewport) {
    return trendDays.value <= 7 ? 1 : 4
  }

  return trendDays.value <= 7 ? 2 : 6
})

const fetchTrend = async (days) => {
  const trendData = await getWeightTrend({ days })

  trendDays.value = days
  trendTabDays.value = days
  trendPeriod.value = trendData?.period || ''
  trendSummary.value = {
    start_weight: trendData?.summary?.start_weight ?? null,
    current_weight: trendData?.summary?.current_weight ?? null,
    weight_change: Number(trendData?.summary?.weight_change || 0),
    bmi_change: Number(trendData?.summary?.bmi_change || 0)
  }
  trendRecords.value = Array.isArray(trendData?.trend) ? trendData.trend : []
}

const fetchHistory = async (days = 7) => {
  const historyData = await getBodyHistory({ days })

  const items = Array.isArray(historyData?.items) ? historyData.items : []
  historyTotal.value = Number(historyData?.total || 0)
  historyRecords.value = items.map((item, index) => {
    // items 已按 recorded_at 降序排列（最新在前）
    const prevItem = items[index + 1]  // 更旧的一条
    const currentWeight = Number(item?.weight_kg)
    const previousWeight = prevItem ? Number(prevItem?.weight_kg) : null
    return {
      ...item,
      weight_change: Number.isFinite(previousWeight) ? roundValue(currentWeight - previousWeight, 1) : null
    }
  })
}

const fetchData = async () => {
  loading.value = true
  errorMessage.value = ''

  try {
    await Promise.all([
      fetchTrend(trendDays.value),
      fetchHistory(trendDays.value)
    ])
  } catch (error) {
    console.error('获取体重历史失败:', error)
    errorMessage.value = error?.message || '请稍后重试'
  } finally {
    loading.value = false
  }
}

const switchTrendDays = async (days) => {
  if (trendLoading.value || trendTabDays.value === days) return

  const previousTab = trendTabDays.value
  trendTabDays.value = days
  trendLoading.value = true

  try {
    await Promise.all([
      fetchTrend(days),
      fetchHistory(days)
    ])
  } catch (error) {
    console.error('切换体重趋势失败:', error)
    trendTabDays.value = previousTab
    uni.showToast({
      title: error?.message || '趋势加载失败',
      icon: 'none'
    })
  } finally {
    trendLoading.value = false
  }
}

const roundValue = (value, digits = 1) => {
  const numericValue = Number(value)
  if (!Number.isFinite(numericValue)) return null
  const factor = Math.pow(10, digits)
  return Math.round(numericValue * factor) / factor
}

const formatValue = (value, digits = 1) => {
  const numericValue = Number(value)
  if (!Number.isFinite(numericValue)) return '--'
  return numericValue.toFixed(digits)
}

const formatInteger = (value) => {
  const numericValue = Number(value)
  if (!Number.isFinite(numericValue)) return '--'
  return `${Math.round(numericValue)}`
}

const formatWeight = (value) => {
  const numericValue = Number(value)
  if (!Number.isFinite(numericValue)) return '--'
  return `${numericValue.toFixed(1)} kg`
}

const formatSignedValue = (value, digits = 1) => {
  const numericValue = Number(value)
  if (!Number.isFinite(numericValue)) return '--'
  if (numericValue === 0) return (0).toFixed(digits)
  return `${numericValue > 0 ? '+' : ''}${numericValue.toFixed(digits)}`
}

const formatSignedWeight = (value) => {
  const numericValue = Number(value)
  if (!Number.isFinite(numericValue)) return '--'
  if (numericValue === 0) return '0.0 kg'
  return `${numericValue > 0 ? '+' : ''}${numericValue.toFixed(1)} kg`
}

const formatDateTime = (value) => {
  if (!value) return '--'
  return dayjs(value).format('YYYY.MM.DD HH:mm')
}

const getChangeClass = (value) => {
  const numericValue = Number(value)
  if (!Number.isFinite(numericValue) || numericValue === 0) return 'is-flat'
  return numericValue > 0 ? 'is-up' : 'is-down'
}

onMounted(() => {
  fetchData()
})
</script>

<style lang="scss" scoped>
.body-history-container {
  height: 100vh;
  overflow: hidden;
  background: #f5f5f5;
}

.page-scroll {
  height: 100%;
}

.body-history-page {
  --page-bg: #f5f5f5;
  --card-bg: #ffffff;
  --primary: #4caf50;
  --primary-soft: #e8f5e9;
  --primary-deep: #2e7d32;
  --primary-gradient: linear-gradient(135deg, #4caf50 0%, #81c784 100%);
  --text-main: #333333;
  --text-secondary: #666666;
  --text-muted: #999999;
  --border-soft: #f0f0f0;
  --danger: #f44336;
  --danger-soft: #ffebee;
  --warning: #ff9800;
  --warning-soft: #fff3e0;
  --space-xs: 12rpx;
  --space-sm: 20rpx;
  --space-md: 24rpx;
  --space-lg: 30rpx;
  --radius-sm: 12rpx;
  --radius-md: 16rpx;
  --radius-lg: 20rpx;

  background: var(--page-bg);
  padding: var(--space-sm) var(--space-lg) 40rpx;
  box-sizing: border-box;
}

.summary-card,
.history-card,
.state-card {
  background: var(--card-bg);
  border-radius: var(--radius-lg);
  padding: var(--space-lg);
  box-shadow: 0 10rpx 24rpx rgba(76, 175, 80, 0.06);
}

.history-card {
  margin-top: var(--space-sm);
}

.state-card {
  min-height: 420rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
}

.state-icon {
  font-size: 72rpx;
}

.state-title,
.section-title {
  display: block;
  font-size: 32rpx;
  font-weight: 700;
  color: var(--text-main);
}

.state-title {
  margin-top: var(--space-sm);
}

.state-desc,
.section-subtitle {
  display: block;
  margin-top: var(--space-xs);
  font-size: 24rpx;
  line-height: 1.6;
  color: var(--text-muted);
}

.state-button {
  margin-top: var(--space-lg);
  min-width: 220rpx;
  height: 80rpx;
  line-height: 80rpx;
  border-radius: 40rpx;
  background: var(--primary);
  color: #fff;
  font-size: 28rpx;
}

.state-button::after {
  border: none;
}

.section-head {
  display: flex;
  justify-content: space-between;
  gap: var(--space-sm);
}

.section-head--history {
  align-items: center;
}

.change-badge,
.history-total,
.history-change {
  align-self: flex-start;
  padding: 10rpx 18rpx;
  border-radius: 999rpx;
  font-size: 22rpx;
  font-weight: 600;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: var(--space-sm);
  margin-top: var(--space-md);
}

.trend-tabs {
  display: inline-flex;
  gap: 8rpx;
  margin-top: var(--space-md);
  padding: 8rpx;
  border-radius: 999rpx;
  background: var(--primary-soft);
}

.trend-tab {
  min-width: 116rpx;
  padding: 14rpx 24rpx;
  border-radius: 999rpx;
  text-align: center;
  font-size: 24rpx;
  font-weight: 600;
  color: var(--primary-deep);
}

.trend-tab--active {
  background: var(--card-bg);
  color: var(--primary-deep);
  box-shadow: 0 6rpx 14rpx rgba(76, 175, 80, 0.12);
}

.trend-tab--disabled {
  opacity: 0.72;
}

.summary-item {
  background: #f8faf8;
  border-radius: var(--radius-md);
  padding: var(--space-sm);
}

.summary-item--highlight {
  background: var(--primary-gradient);
}

.summary-label {
  display: block;
  font-size: 22rpx;
  color: var(--text-muted);
}

.summary-item--highlight .summary-label {
  color: rgba(255, 255, 255, 0.84);
}

.summary-value {
  display: block;
  margin-top: 12rpx;
  font-size: 34rpx;
  font-weight: 700;
  color: var(--text-main);
}

.summary-item--highlight .summary-value {
  color: #fff;
}

.trend-panel {
  margin-top: var(--space-lg);
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.trend-chart-card {
  padding: var(--space-md);
  border-radius: var(--radius-md);
  background: #f8faf8;
}

.trend-chart-card--secondary {
  background: #f7f9ff;
}

.trend-chart-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
  margin-bottom: 18rpx;
}

.trend-chart-title {
  font-size: 28rpx;
  font-weight: 700;
  color: var(--text-main);
}

.trend-inline-state {
  display: flex;
  align-items: center;
  gap: 12rpx;
  margin-top: var(--space-lg);
  padding: 28rpx 24rpx;
  border-radius: var(--radius-md);
  background: #f8faf8;
  color: var(--text-secondary);
}

.trend-inline-state__icon {
  font-size: 28rpx;
}

.trend-inline-state__text {
  font-size: 24rpx;
}

.chart-container {
  width: 100%;
  min-height: 320rpx;
}

.history-list {
  margin-top: var(--space-md);
}

.history-item {
  padding: var(--space-md) 0;
  border-bottom: 1rpx solid var(--border-soft);
}

.history-item:first-child {
  padding-top: 0;
}

.history-item:last-child {
  padding-bottom: 0;
  border-bottom: none;
}

.history-top {
  display: flex;
  justify-content: space-between;
  gap: var(--space-sm);
}

.history-main {
  flex: 1;
}

.history-weight {
  display: block;
  font-size: 36rpx;
  font-weight: 700;
  color: var(--text-main);
}

.history-time {
  display: block;
  margin-top: 10rpx;
  font-size: 22rpx;
  color: var(--text-muted);
}

.history-total {
  color: var(--primary-deep);
  background: var(--primary-soft);
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--space-sm);
  margin-top: var(--space-md);
}

.metric-chip {
  padding: 18rpx 20rpx;
  border-radius: var(--radius-sm);
  background: #f8faf8;
}

.metric-label {
  display: block;
  font-size: 20rpx;
  color: var(--text-muted);
}

.metric-value {
  display: block;
  margin-top: 8rpx;
  font-size: 26rpx;
  font-weight: 600;
  color: var(--text-main);
}

.inline-empty {
  margin-top: var(--space-lg);
  padding: 48rpx 24rpx;
  border-radius: var(--radius-md);
  background: #f8faf8;
  text-align: center;
}

.inline-empty--history {
  margin-top: var(--space-md);
}

.inline-empty-title {
  display: block;
  font-size: 28rpx;
  font-weight: 600;
  color: var(--text-main);
}

.inline-empty-desc {
  display: block;
  margin-top: 12rpx;
  font-size: 24rpx;
  line-height: 1.6;
  color: var(--text-muted);
}

.is-up {
  color: var(--danger);
  background: var(--danger-soft);
}

.is-down {
  color: var(--primary-deep);
  background: var(--primary-soft);
}

.is-flat {
  color: var(--warning);
  background: var(--warning-soft);
}

.history-change--muted {
  color: var(--text-muted);
  background: #f5f5f5;
}

@media screen and (max-width: 375px) {
  .body-history-page {
    padding-left: var(--space-sm);
    padding-right: var(--space-sm);
  }

  .summary-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .summary-item--highlight {
    grid-column: span 2;
  }

  .trend-tab {
    min-width: 108rpx;
    padding-left: 20rpx;
    padding-right: 20rpx;
  }

}
</style>
