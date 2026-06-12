<template>
  <view class="stats-container">
    <scroll-view scroll-y class="stats-scroll">
    <!-- 周期切换 -->
    <view class="period-tabs">
      <view 
        class="tab-item"
        :class="{ active: currentPeriod === 'analysis' }"
        @click="switchPeriod('analysis')"
      >
        今日分析
      </view>
      <view 
        v-for="tab in periodTabs" 
        :key="tab.key"
        class="tab-item"
        :class="{ active: currentPeriod === tab.key }"
        @click="switchPeriod(tab.key)"
      >
        {{ tab.name }}
      </view>
    </view>

    <!-- 今日热量分析 -->
    <view v-if="currentPeriod === 'analysis'" class="analysis-section">
      <!-- 热量摄入对比 -->
      <view class="analysis-card" v-if="analysis">
        <view class="card-title">热量摄入分析</view>
        <view class="calorie-compare">
          <view class="compare-item">
            <text class="label">已摄入</text>
            <text class="value" :class="{ excess: analysis.summary?.is_calorie_excess }">
              {{ analysis.summary?.actual?.calorie || 0 }}
            </text>
            <text class="unit">kcal</text>
          </view>
          <view class="compare-divider">
            <view class="progress-ring" :class="{ warning: analysis.summary?.is_calorie_excess }">
              <text class="percent">{{ caloriePercent }}%</text>
            </view>
          </view>
          <view class="compare-item">
            <text class="label">目标</text>
            <text class="value">{{ calibratedDailyGoal || 0 }}</text>
            <text class="unit">kcal</text>
          </view>
        </view>
        
        <!-- 超标警告 -->
        <view v-if="analysis.summary?.is_calorie_excess" class="excess-warning">
          <text class="warning-icon">⚠️</text>
          <text class="warning-text">热量超标 {{ analysis.excess_analysis?.excess_percent?.calorie || 0 }}%</text>
        </view>
        
        <!-- BMI状态 -->
        <view class="bmi-info">
          <text class="bmi-label">BMI</text>
          <text class="bmi-value" :class="getBMIClass(analysis.summary?.bmi)">
            {{ analysis.summary?.bmi || '--' }}
          </text>
          <text class="bmi-status" :class="getBMIClass(analysis.summary?.bmi)">
            {{ analysis.summary?.bmi_status || '--' }}
          </text>
        </view>
      </view>

      <!-- 营养素超标分析 -->
      <view class="analysis-card" v-if="analysis?.excess_analysis?.excess_nutrients?.length">
        <view class="card-title">营养素超标详情</view>
        <view class="excess-list">
          <view 
            v-for="nutrient in analysis.excess_analysis.excess_nutrients" 
            :key="nutrient"
            class="excess-item"
          >
            <text class="nutrient-name">{{ nutrientNameMap[nutrient] }}</text>
            <view class="excess-bar">
              <view 
                class="excess-fill" 
                :style="{ width: Math.min(analysis.excess_analysis.excess_percent[nutrient], 100) + '%' }"
              ></view>
            </view>
            <text class="excess-percent">+{{ analysis.excess_analysis.excess_percent[nutrient] }}%</text>
          </view>
        </view>
      </view>

      <!-- 超标食物来源 -->
      <view class="analysis-card" v-if="hasFoodSources">
        <view class="card-title">超标食物来源</view>
        <!-- 蛋白质超标 -->
        <view class="food-source-section" v-if="excessNutrients.includes('protein') && analysis.food_sources?.top_protein?.length">
          <view class="source-title">蛋白质贡献TOP</view>
          <view class="source-list">
            <view 
              v-for="(food, index) in analysis.food_sources.top_protein" 
              :key="index"
              class="source-item"
            >
              <text class="food-name">{{ food.name }}</text>
              <text class="food-value">{{ food.value }} g</text>
              <text class="meal-tag" :class="'meal-' + food.meal_type">{{ mealTypeMap[food.meal_type] }}</text>
            </view>
          </view>
        </view>
        <!-- 脂肪超标 -->
        <view class="food-source-section" v-if="excessNutrients.includes('fat') && analysis.food_sources?.top_fat?.length">
          <view class="source-title">脂肪贡献TOP</view>
          <view class="source-list">
            <view 
              v-for="(food, index) in analysis.food_sources.top_fat" 
              :key="index"
              class="source-item"
            >
              <text class="food-name">{{ food.name }}</text>
              <text class="food-value">{{ food.value }} g</text>
              <text class="meal-tag" :class="'meal-' + food.meal_type">{{ mealTypeMap[food.meal_type] }}</text>
            </view>
          </view>
        </view>
        <!-- 碳水超标 -->
        <view class="food-source-section" v-if="excessNutrients.includes('carb') && analysis.food_sources?.top_carb?.length">
          <view class="source-title">碳水贡献TOP</view>
          <view class="source-list">
            <view 
              v-for="(food, index) in analysis.food_sources.top_carb" 
              :key="index"
              class="source-item"
            >
              <text class="food-name">{{ food.name }}</text>
              <text class="food-value">{{ food.value }} g</text>
              <text class="meal-tag" :class="'meal-' + food.meal_type">{{ mealTypeMap[food.meal_type] }}</text>
            </view>
          </view>
        </view>
      </view>

      <!-- 个性化建议 -->
      <view class="analysis-card suggestions-card" v-if="analysis?.suggestions?.length">
        <view class="card-title">💡 饮食调整建议</view>
        <view class="suggestion-list">
          <view 
            v-for="(suggestion, index) in analysis.suggestions" 
            :key="index"
            class="suggestion-item"
          >
            <text class="suggestion-num">{{ index + 1 }}</text>
            <text class="suggestion-text">{{ suggestion }}</text>
          </view>
        </view>
      </view>

      <!-- 推荐食物 -->
      <view class="analysis-card" v-if="analysis?.recommended_foods?.length">
        <view class="card-title">🥗 推荐食物</view>
        <view class="recommended-list">
          <view 
            v-for="(food, index) in analysis.recommended_foods" 
            :key="index"
            class="recommended-item"
          >
            <text class="food-icon">🍽️</text>
            <view class="food-info">
              <text class="food-name">{{ food.name }}</text>
              <text class="food-reason">{{ food.reason }}</text>
            </view>
          </view>
        </view>
      </view>
    </view>

    <!-- 统计概览 -->
    <view class="overview-card" v-if="currentPeriod !== 'analysis' && stats">
      <view class="overview-item">
        <text class="value">{{ stats.summary?.avg_calorie || 0 }}</text>
        <text class="label">平均热量(kcal)</text>
      </view>
      <view class="overview-item">
        <text class="value">{{ stats.summary?.target_met_days || 0 }}</text>
        <text class="label">达标天数</text>
      </view>
      <view class="overview-item">
        <text class="value">{{ stats.summary?.avg_score || 0 }}</text>
        <text class="label">平均评分</text>
      </view>
    </view>

    <!-- 周/月统计内容 -->
    <view v-if="currentPeriod !== 'analysis'">
      <!-- 热量趋势图 -->
      <view class="chart-card">
        <view class="card-title">热量趋势</view>
        <view class="chart-container">
          <scroll-view class="bar-chart-scroll" scroll-x v-if="chartData.length">
            <view class="bar-chart">
              <view class="bar-item" v-for="(item, index) in chartData" :key="index">
                <view class="bar" :style="{ height: getBarHeight(item.calorie) + '%' }">
                  <text class="bar-value">{{ item.calorie }}</text>
                </view>
                <text class="bar-label">{{ item.label }}</text>
              </view>
            </view>
          </scroll-view>
          <view class="chart-empty" v-else>
            暂无数据
          </view>
        </view>
      </view>

      <!-- 营养素占比 -->
      <view class="chart-card">
        <view class="card-title">营养素摄入</view>
        <view class="nutrient-bars">
          <view class="nutrient-row">
            <text class="nutrient-name">蛋白质</text>
            <view class="nutrient-bar">
              <view class="bar-fill protein" :style="{ width: getNutrientPercent('protein') + '%' }"></view>
            </view>
            <text class="nutrient-value">{{ formatNutrient(avgNutrients.protein) }}g</text>
          </view>
          <view class="nutrient-row">
            <text class="nutrient-name">碳水</text>
            <view class="nutrient-bar">
              <view class="bar-fill carb" :style="{ width: getNutrientPercent('carb') + '%' }"></view>
            </view>
            <text class="nutrient-value">{{ formatNutrient(avgNutrients.carb) }}g</text>
          </view>
          <view class="nutrient-row">
            <text class="nutrient-name">脂肪</text>
            <view class="nutrient-bar">
              <view class="bar-fill fat" :style="{ width: getNutrientPercent('fat') + '%' }"></view>
            </view>
            <text class="nutrient-value">{{ formatNutrient(avgNutrients.fat) }}g</text>
          </view>
        </view>
      </view>

      <!-- 每日详情 -->
      <view class="daily-list" v-if="reversedDailyStats.length">
        <view class="list-title">每日详情</view>
        <view class="daily-item" v-for="day in reversedDailyStats" :key="day.date">
          <view class="day-date">{{ formatDate(day.date) }}</view>
          <view class="day-calorie">{{ day.calorie }} kcal</view>
          <view class="day-score" :class="getScoreClass(day.score)">{{ day.score }}分</view>
          <view class="day-status">
            <text :class="{ met: day.is_target_met }">{{ day.is_target_met ? '达标' : '未达标' }}</text>
          </view>
        </view>
      </view>
    </view>
    </scroll-view>
  </view>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { getWeekStats, getMonthStats, getTodayStats, getAnalysis } from '@/api/stats'
import { useUserStore } from '@/store/user'
import { calculateBMR, calculateAgeFromBirthday, calculateDailyCalorie } from '@/utils/nutrition'
import dayjs from 'dayjs'

const currentPeriod = ref('analysis')
const stats = ref(null)
const analysis = ref(null)
const loading = ref(false)

const userStore = useUserStore()
const profile = computed(() => userStore.profile)

const formulaDailyGoal = computed(() => {
  if (!profile.value) return 0
  const age = calculateAgeFromBirthday(profile.value.birthday)
  if (!age) return 0
  const bmr = calculateBMR(profile.value.weight_kg, profile.value.height_cm, age, profile.value.gender)
  return calculateDailyCalorie(bmr, profile.value.activity_level, profile.value.health_goal, profile.value.calorie_coefficient)
})

const calibratedDailyGoal = computed(() => {
  if (!formulaDailyGoal.value) return 0
  const mc = profile.value?.metabolic_coefficient
  if (!mc || mc === 1) return formulaDailyGoal.value
  return Math.round(formulaDailyGoal.value * mc)
})

const periodTabs = [
  { key: 'week', name: '最近7天' },
  { key: 'month', name: '最近30天' }
]

const nutrientNameMap = {
  calorie: '热量',
  protein: '蛋白质',
  carb: '碳水',
  fat: '脂肪'
}

const mealTypeMap = {
  1: '早餐',
  2: '午餐',
  3: '晚餐',
  4: '加餐'
}

// 计算属性
const chartData = computed(() => {
  if (!stats.value?.daily) return []
  return [...stats.value.daily]
    .reverse()
    .map(d => ({
      date: d.date,
      label: dayjs(d.date).format('MM/DD'),
      calorie: d.calorie || 0
    }))
})

const reversedDailyStats = computed(() => {
  if (!stats.value?.daily?.length) return []
  return [...stats.value.daily].reverse()
})

const avgNutrients = computed(() => {
  if (!stats.value?.daily?.length) {
    return { protein: 0, carb: 0, fat: 0 }
  }
  return {
    protein: stats.value.summary?.avg_protein ?? 0,
    carb: stats.value.summary?.avg_carb ?? 0,
    fat: stats.value.summary?.avg_fat ?? 0
  }
})

const targetNutrients = computed(() => {
  return stats.value?.target || { protein: 80, carb: 300, fat: 60 }
})

const caloriePercent = computed(() => {
  if (!analysis.value?.summary) return 0
  const actual = analysis.value.summary.actual?.calorie || 0
  const target = calibratedDailyGoal.value || analysis.value.summary.target?.calorie || 1
  return Math.round((actual / target) * 100)
})

const excessNutrients = computed(() => {
  return analysis.value?.excess_analysis?.excess_nutrients || []
})

const hasFoodSources = computed(() => {
  const nutrients = excessNutrients.value
  const sources = analysis.value?.food_sources
  if (!sources || !nutrients.length) return false
  return (nutrients.includes('protein') && sources.top_protein?.length) ||
         (nutrients.includes('fat') && sources.top_fat?.length) ||
         (nutrients.includes('carb') && sources.top_carb?.length)
})

// 方法
const switchPeriod = (period) => {
  currentPeriod.value = period
  if (period === 'analysis') {
    fetchAnalysis()
  } else {
    fetchStats()
  }
}

const fetchStats = async () => {
  loading.value = true
  try {
    if (currentPeriod.value === 'week') {
      stats.value = await getWeekStats()
    } else {
      stats.value = await getMonthStats()
    }
  } catch (error) {
    console.error('获取统计数据失败:', error)
  } finally {
    loading.value = false
  }
}

const fetchAnalysis = async () => {
  loading.value = true
  try {
    analysis.value = await getAnalysis()
  } catch (error) {
    console.error('获取分析数据失败:', error)
  } finally {
    loading.value = false
  }
}

const getBMIClass = (bmi) => {
  if (!bmi) return ''
  if (bmi < 18.5) return 'underweight'
  if (bmi < 24) return 'normal'
  if (bmi < 28) return 'overweight'
  return 'obese'
}

const getBarHeight = (calorie) => {
  if (!stats.value?.daily?.length) return 0
  const max = Math.max(...stats.value.daily.map(d => d.calorie || 0))
  if (max === 0) return 0
  return Math.round((calorie / max) * 100)
}

const getNutrientPercent = (type) => {
  const actual = avgNutrients.value[type] || 0
  const target = targetNutrients.value[type] || 1
  return Math.min(100, Math.round((actual / target) * 100))
}

const formatNutrient = (value) => {
  return value ? value.toFixed(1) : '0.0'
}

const formatDate = (date) => {
  return dayjs(date).format('M月D日')
}

const getScoreClass = (score) => {
  if (score >= 80) return 'high'
  if (score >= 60) return 'medium'
  return 'low'
}

onMounted(() => {
  fetchAnalysis()
})

// 页面显示时刷新数据（解决tabBar切换不刷新问题）
onShow(() => {
  if (currentPeriod.value === 'analysis') {
    fetchAnalysis()
  } else {
    fetchStats()
  }
})
</script>

<style lang="scss" scoped>
.stats-container {
  height: 100vh;
  overflow: hidden;
  background: #f5f5f5;
}

.stats-scroll {
  height: 100%;
  padding-bottom: 40rpx;
}

.period-tabs {
  display: flex;
  background: #fff;
  padding: 20rpx 30rpx;
  
  .tab-item {
    flex: 1;
    text-align: center;
    padding: 20rpx 0;
    font-size: 28rpx;
    color: #666;
    border-radius: 8rpx;
    
    &.active {
      background: #e8f5e9;
      color: #4caf50;
      font-weight: bold;
    }
  }
}

.overview-card {
  display: flex;
  margin: 20rpx 30rpx;
  background: linear-gradient(135deg, #4caf50 0%, #81c784 100%);
  border-radius: 20rpx;
  padding: 30rpx;
  
  .overview-item {
    flex: 1;
    text-align: center;
    
    .value {
      display: block;
      font-size: 44rpx;
      font-weight: bold;
      color: #fff;
    }
    
    .label {
      display: block;
      font-size: 24rpx;
      color: rgba(255,255,255,0.8);
      margin-top: 8rpx;
    }
  }
}

.chart-card {
  margin: 20rpx 30rpx;
  background: #fff;
  border-radius: 20rpx;
  padding: 30rpx;
  
  .card-title {
    font-size: 30rpx;
    font-weight: bold;
    color: #333;
    margin-bottom: 24rpx;
  }
  
  .chart-container {
    min-height: 260rpx;

    .bar-chart-scroll {
      width: 100%;
      height: 260rpx;
      overflow: visible;
      
      .bar-chart {
        display: flex;
        align-items: flex-end;
        height: 100%;
        padding: 40rpx 20rpx 24rpx;
        min-width: fit-content;
        box-sizing: border-box;
        overflow: visible;
        
        .bar-item {
          flex-shrink: 0;
          width: 60rpx;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: flex-end;
          height: 100%;
          margin-right: 16rpx;
          overflow: visible;
          
          &:last-child {
            margin-right: 20rpx;
          }
          
          .bar {
            width: 40rpx;
            background: linear-gradient(180deg, #4caf50, #81c784);
            border-radius: 8rpx 8rpx 0 0;
            position: relative;
            min-height: 10rpx;
            
            .bar-value {
              position: absolute;
              top: -32rpx;
              left: 50%;
              transform: translateX(-50%);
              font-size: 20rpx;
              color: #666;
              white-space: nowrap;
              line-height: 1;
            }
          }
           
          .bar-label {
            font-size: 20rpx;
            color: #999;
            margin-top: 12rpx;
            line-height: 1;
            white-space: nowrap;
          }
        }
      }
    }
    
    .chart-empty {
      height: 260rpx;
      display: flex;
      align-items: center;
      justify-content: center;
      color: #999;
      font-size: 28rpx;
    }
  }
  
  .nutrient-bars {
    .nutrient-row {
      display: flex;
      align-items: center;
      margin-bottom: 24rpx;
      
      &:last-child {
        margin-bottom: 0;
      }
      
      .nutrient-name {
        width: 100rpx;
        font-size: 26rpx;
        color: #666;
      }
      
      .nutrient-bar {
        flex: 1;
        height: 24rpx;
        background: #f0f0f0;
        border-radius: 12rpx;
        overflow: hidden;
        margin: 0 20rpx;
        
        .bar-fill {
          height: 100%;
          border-radius: 12rpx;
          transition: width 0.3s;
          
          &.protein { background: #e91e63; }
          &.carb { background: #ff9800; }
          &.fat { background: #9c27b0; }
        }
      }
      
      .nutrient-value {
        width: 100rpx;
        text-align: right;
        font-size: 26rpx;
        color: #333;
        font-weight: 500;
      }
    }
  }
}

.daily-list {
  margin: 20rpx 30rpx;
  background: #fff;
  border-radius: 20rpx;
  padding: 30rpx;
  
  .list-title {
    font-size: 30rpx;
    font-weight: bold;
    color: #333;
    margin-bottom: 24rpx;
  }
  
  .daily-item {
    display: flex;
    align-items: center;
    padding: 20rpx 0;
    border-bottom: 1rpx solid #f0f0f0;
    
    &:last-child {
      border-bottom: none;
    }
    
    .day-date {
      width: 140rpx;
      font-size: 26rpx;
      color: #333;
    }
    
    .day-calorie {
      flex: 1;
      font-size: 26rpx;
      color: #666;
    }
    
    .day-score {
      width: 100rpx;
      text-align: center;
      font-size: 26rpx;
      font-weight: 500;
      
      &.high { color: #4caf50; }
      &.medium { color: #ff9800; }
      &.low { color: #f44336; }
    }
    
    .day-status {
      width: 100rpx;
      text-align: right;
      font-size: 24rpx;
      
      text {
        padding: 6rpx 12rpx;
        border-radius: 8rpx;
        background: #ffebee;
        color: #f44336;
        
        &.met {
          background: #e8f5e9;
          color: #4caf50;
        }
      }
    }
  }
}

// 热量分析样式
.analysis-section {
  padding: 0 30rpx;
  
  .analysis-card {
    background: #fff;
    border-radius: 20rpx;
    padding: 30rpx;
    margin-bottom: 20rpx;
    
    .card-title {
      font-size: 30rpx;
      font-weight: bold;
      color: #333;
      margin-bottom: 24rpx;
    }
    
    .calorie-compare {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 30rpx;
      
      .compare-item {
        text-align: center;
        flex: 1;
        
        .label {
          display: block;
          font-size: 24rpx;
          color: #999;
          margin-bottom: 8rpx;
        }
        
        .value {
          display: block;
          font-size: 44rpx;
          font-weight: bold;
          color: #333;
          
          &.excess {
            color: #f44336;
          }
        }
        
        .unit {
          display: block;
          font-size: 22rpx;
          color: #999;
          margin-top: 4rpx;
        }
      }
      
      .compare-divider {
        .progress-ring {
          width: 120rpx;
          height: 120rpx;
          border-radius: 50%;
          background: conic-gradient(#4caf50 var(--percent), #e8e8e8 var(--percent));
          display: flex;
          align-items: center;
          justify-content: center;
          position: relative;
          
          &::before {
            content: '';
            position: absolute;
            width: 90rpx;
            height: 90rpx;
            background: #fff;
            border-radius: 50%;
          }
          
          &.warning {
            background: conic-gradient(#f44336 var(--percent), #ffebee var(--percent));
          }
          
          .percent {
            position: relative;
            font-size: 28rpx;
            font-weight: bold;
            color: #333;
          }
        }
      }
    }
    
    .excess-warning {
      display: flex;
      align-items: center;
      justify-content: center;
      background: #fff3e0;
      border-radius: 12rpx;
      padding: 20rpx;
      margin-bottom: 20rpx;
      
      .warning-icon {
        font-size: 36rpx;
        margin-right: 12rpx;
      }
      
      .warning-text {
        font-size: 28rpx;
        color: #ff6f00;
        font-weight: 500;
      }
    }
    
    .bmi-info {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 20rpx;
      padding-top: 20rpx;
      border-top: 1rpx solid #f0f0f0;
      
      .bmi-label {
        font-size: 26rpx;
        color: #999;
      }
      
      .bmi-value {
        font-size: 36rpx;
        font-weight: bold;
        color: #333;
        
        &.underweight { color: #2196f3; }
        &.normal { color: #4caf50; }
        &.overweight { color: #ff9800; }
        &.obese { color: #f44336; }
      }
      
      .bmi-status {
        font-size: 24rpx;
        padding: 6rpx 16rpx;
        border-radius: 20rpx;
        background: #f5f5f5;
        color: #666;
        
        &.underweight { background: #e3f2fd; color: #2196f3; }
        &.normal { background: #e8f5e9; color: #4caf50; }
        &.overweight { background: #fff3e0; color: #ff9800; }
        &.obese { background: #ffebee; color: #f44336; }
      }
    }
    
    .excess-list {
      .excess-item {
        display: flex;
        align-items: center;
        margin-bottom: 20rpx;
        
        &:last-child {
          margin-bottom: 0;
        }
        
        .nutrient-name {
          width: 100rpx;
          font-size: 26rpx;
          color: #666;
        }
        
        .excess-bar {
          flex: 1;
          height: 20rpx;
          background: #f0f0f0;
          border-radius: 10rpx;
          overflow: hidden;
          margin: 0 20rpx;
          
          .excess-fill {
            height: 100%;
            background: linear-gradient(90deg, #ff9800, #f44336);
            border-radius: 10rpx;
          }
        }
        
        .excess-percent {
          width: 80rpx;
          text-align: right;
          font-size: 26rpx;
          color: #f44336;
          font-weight: 500;
        }
      }
    }
    
    .food-source-section {
      .source-title {
        font-size: 26rpx;
        color: #666;
        margin-bottom: 16rpx;
      }
      
      .source-list {
        .source-item {
          display: flex;
          align-items: center;
          padding: 16rpx 0;
          border-bottom: 1rpx solid #f5f5f5;
          
          &:last-child {
            border-bottom: none;
          }
          
          .food-name {
            flex: 1;
            font-size: 28rpx;
            color: #333;
          }
          
          .food-value {
            font-size: 26rpx;
            color: #f44336;
            margin-right: 16rpx;
          }
          
          .meal-tag {
            font-size: 22rpx;
            padding: 4rpx 12rpx;
            border-radius: 8rpx;
            background: #f5f5f5;
            color: #666;
            
            &.meal-1 { background: #fff3e0; color: #ff9800; }
            &.meal-2 { background: #e3f2fd; color: #2196f3; }
            &.meal-3 { background: #f3e5f5; color: #9c27b0; }
            &.meal-4 { background: #e8f5e9; color: #4caf50; }
          }
        }
      }
    }
    
    .suggestion-list {
      .suggestion-item {
        display: flex;
        align-items: flex-start;
        margin-bottom: 20rpx;
        
        &:last-child {
          margin-bottom: 0;
        }
        
        .suggestion-num {
          width: 40rpx;
          height: 40rpx;
          background: #4caf50;
          color: #fff;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 24rpx;
          margin-right: 16rpx;
          flex-shrink: 0;
        }
        
        .suggestion-text {
          flex: 1;
          font-size: 28rpx;
          color: #333;
          line-height: 1.6;
        }
      }
    }
    
    .recommended-list {
      .recommended-item {
        display: flex;
        align-items: center;
        padding: 20rpx 0;
        border-bottom: 1rpx solid #f5f5f5;
        
        &:last-child {
          border-bottom: none;
        }
        
        .food-icon {
          font-size: 40rpx;
          margin-right: 20rpx;
        }
        
        .food-info {
          flex: 1;
          
          .food-name {
            display: block;
            font-size: 30rpx;
            color: #333;
            font-weight: 500;
          }
          
          .food-reason {
            display: block;
            font-size: 24rpx;
            color: #4caf50;
            margin-top: 4rpx;
          }
        }
      }
    }
    
    &.suggestions-card {
      background: linear-gradient(135deg, #e8f5e9 0%, #fff 100%);
    }
  }
}
</style>
