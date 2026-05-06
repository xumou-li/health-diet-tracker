<template>
  <view class="index-container">
    <scroll-view scroll-y class="index-scroll">
      <view class="scroll-inner">
    <!-- 顶部用户信息（可滚动） -->
    <view class="header">
      <view class="user-info" @click="goToMine">
        <view class="avatar">
          <image
            v-if="avatarUrl"
            class="avatar-img"
            :src="avatarUrl"
            mode="aspectFill"
          />
          <text v-else class="avatar-text">{{ userInitial }}</text>
        </view>
        <view class="info">
          <text class="greeting">{{ greeting }}</text>
          <text class="goal-text" v-if="profile">{{ healthGoalText }} · BMI {{ profile.bmi }}</text>
        </view>
      </view>
      <view class="date">{{ todayStr }}</view>
    </view>

    <!-- 热量进度卡片 -->
    <view class="calorie-card">
      <view class="calorie-summary">
        <view class="calorie-ring">
          <view class="ring-progress" :style="ringStyle"></view>
          <view class="ring-center">
            <text class="calorie-value">{{ calorieActual }}</text>
            <text class="calorie-unit">千卡</text>
            <text class="calorie-percent">{{ caloriePercentText }}</text>
          </view>
        </view>
        <view class="calorie-info">
          <view class="info-item">
            <text class="label">目标</text>
            <text class="value">{{ displayMetric(todayStats.target?.calorie) }} kcal</text>
          </view>
          <view class="info-item">
            <text class="label">剩余</text>
            <text class="value" :class="{ warning: calorieRemaining < 0 }">
              {{ displayMetric(todayStats.remaining?.calorie) }} kcal
            </text>
          </view>
          <view class="info-item">
            <text class="label">完成</text>
            <text class="value progress">{{ caloriePercentText }}</text>
          </view>
          <view class="info-item">
            <text class="label">评分</text>
            <text class="value score">{{ displayMetric(todayStats.score) }}分</text>
          </view>

          <view class="meal-ring-legend" v-if="mealRingLegend.length">
            <view class="legend-item" v-for="meal in mealRingLegend" :key="meal.type">
              <view class="legend-dot" :style="{ background: meal.color }"></view>
              <text class="legend-name">{{ meal.name }}</text>
              <text class="legend-value">{{ meal.calorie }} kcal · {{ meal.percentText }}</text>
            </view>
          </view>
        </view>
      </view>
    </view>

    <!-- 营养素卡片 -->
    <view class="nutrient-section">
      <view class="section-title">营养素摄入</view>
      <view class="nutrient-cards">
        <view class="nutrient-card protein">
          <view class="nutrient-icon">P</view>
          <view class="nutrient-info">
            <text class="name">蛋白质</text>
            <text class="value">{{ formatNutrient(todayStats.actual?.protein) }}g</text>
            <text class="remaining" :class="getNutrientStatus(todayStats.actual?.protein, todayStats.target?.protein)">
              {{ getNutrientRemainingText(todayStats.actual?.protein, todayStats.target?.protein) }}
            </text>
            <view class="progress-bar">
              <view class="progress" :style="{ width: getPercent(todayStats.actual?.protein, todayStats.target?.protein) + '%' }"></view>
            </view>
          </view>
        </view>
        <view class="nutrient-card carb">
          <view class="nutrient-icon">C</view>
          <view class="nutrient-info">
            <text class="name">碳水</text>
            <text class="value">{{ formatNutrient(todayStats.actual?.carb) }}g</text>
            <text class="remaining" :class="getNutrientStatus(todayStats.actual?.carb, todayStats.target?.carb)">
              {{ getNutrientRemainingText(todayStats.actual?.carb, todayStats.target?.carb) }}
            </text>
            <view class="progress-bar">
              <view class="progress" :style="{ width: getPercent(todayStats.actual?.carb, todayStats.target?.carb) + '%' }"></view>
            </view>
          </view>
        </view>
        <view class="nutrient-card fat">
          <view class="nutrient-icon">F</view>
          <view class="nutrient-info">
            <text class="name">脂肪</text>
            <text class="value">{{ formatNutrient(todayStats.actual?.fat) }}g</text>
            <text class="remaining" :class="getNutrientStatus(todayStats.actual?.fat, todayStats.target?.fat)">
              {{ getNutrientRemainingText(todayStats.actual?.fat, todayStats.target?.fat) }}
            </text>
            <view class="progress-bar">
              <view class="progress" :style="{ width: getPercent(todayStats.actual?.fat, todayStats.target?.fat) + '%' }"></view>
            </view>
          </view>
        </view>
      </view>
    </view>

    <!-- 餐次记录 -->
    <view class="meal-section">
      <view class="section-title">今日饮食</view>
      <view class="meal-list">
        <view 
          class="meal-item" 
          v-for="meal in mealTypes" 
          :key="meal.type"
          @click="goToRecord(meal.type)"
        >
          <view class="meal-icon" :class="meal.class">{{ meal.icon }}</view>
          <view class="meal-info">
            <text class="meal-name">{{ meal.name }}</text>
            <text class="meal-calorie">{{ getMealCalorie(meal.type) }} kcal</text>
          </view>
          <view class="meal-count">{{ getMealCount(meal.type) }}项</view>
          <text class="arrow">›</text>
        </view>
      </view>
    </view>

      </view>
    </scroll-view>

    <!-- 公告弹窗 -->
    <view class="announcement-overlay" v-if="showAnnouncementModal" @click.stop>
      <view class="announcement-modal">
        <view class="announcement-modal__header">
          <text class="announcement-modal__icon">📢</text>
          <text class="announcement-modal__title">系统公告</text>
        </view>
        <scroll-view scroll-y class="announcement-modal__body">
          <text class="announcement-modal__text">{{ announcement }}</text>
        </scroll-view>
        <view class="announcement-modal__footer">
          <view class="announcement-modal__checkbox" @click="dontShowToday = !dontShowToday">
            <view class="checkbox-box" :class="{ 'checkbox-box--checked': dontShowToday }">
              <text v-if="dontShowToday">✓</text>
            </view>
            <text class="checkbox-label">今日不再显示</text>
          </view>
          <view class="announcement-modal__btn" @click="closeAnnouncement">我知道了</view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { onShow, onUnload } from '@dcloudio/uni-app'
import { useUserStore } from '@/store/user'
import { getTodayStats } from '@/api/stats'
import { getMealsByDate } from '@/api/meal'
import { getAnnouncement } from '@/api/announcement'
import { BASE_URL } from '@/api/request'
import dayjs from 'dayjs'

const userStore = useUserStore()
const todayStats = ref({})
const todayMeals = ref({})
const loading = ref(false)
const announcement = ref('')
const showAnnouncementModal = ref(false)
const dontShowToday = ref(false)

// 餐次配置
const mealTypes = [
  { type: 1, name: '早餐', icon: '🌅', class: 'breakfast' },
  { type: 2, name: '午餐', icon: '☀️', class: 'lunch' },
  { type: 3, name: '晚餐', icon: '🌙', class: 'dinner' },
  { type: 4, name: '加餐', icon: '🍎', class: 'snack' }
]

const mealTypeKeyMap = {
  1: 'breakfast',
  2: 'lunch',
  3: 'dinner',
  4: 'snack'
}

// 计算属性
const profile = computed(() => userStore.profile)

const userInitial = computed(() => {
  if (profile.value?.nickname) {
    return profile.value.nickname.charAt(0).toUpperCase()
  }
  if (profile.value?.phone) {
    return profile.value.phone.slice(-2)
  }
  return 'U'
})

const avatarUrl = computed(() => {
  const avatar = profile.value?.avatar
  if (!avatar) return ''
  // #ifdef H5
  return avatar
  // #endif
  // #ifndef H5
  return BASE_URL + avatar
  // #endif
})

const greeting = computed(() => {
  const hour = new Date().getHours()
  if (hour < 6) return '夜深了'
  if (hour < 9) return '早上好'
  if (hour < 12) return '上午好'
  if (hour < 14) return '中午好'
  if (hour < 18) return '下午好'
  if (hour < 22) return '晚上好'
  return '夜深了'
})

const healthGoalText = computed(() => {
  const goals = { 1: '维持体重', 2: '减脂中', 3: '增肌中' }
  return goals[profile.value?.health_goal] || ''
})

const todayStr = computed(() => dayjs().format('M月D日 dddd'))

const toNumber = (value) => {
  const num = Number(value)
  return Number.isFinite(num) ? num : 0
}

const displayMetric = (value, fallback = '--') => {
  if (value === null || value === undefined || value === '') {
    return fallback
  }
  return value
}

const calorieActual = computed(() => toNumber(todayStats.value.actual?.calorie))
const calorieTarget = computed(() => toNumber(todayStats.value.target?.calorie))
const calorieRemaining = computed(() => toNumber(todayStats.value.remaining?.calorie))

const calorieProgressRatio = computed(() => {
  if (!calorieTarget.value) return 0
  return calorieActual.value / calorieTarget.value
})

const caloriePercent = computed(() => {
  return Math.max(0, Math.min(Math.round(calorieProgressRatio.value * 100), 100))
})

const caloriePercentText = computed(() => {
  if (!calorieTarget.value) return '--'
  return `${Math.round(calorieProgressRatio.value * 100)}%`
})

const ringStyle = computed(() => {
  const totalTarget = calorieTarget.value

  if (!totalTarget) {
    return {
      background: 'conic-gradient(#e8e8e8 0deg 360deg)'
    }
  }

  let currentDegree = 0
  const segments = []

  mealBreakdown.value.forEach((meal) => {
    const degree = Math.max(0, Math.min((meal.calorie / totalTarget) * 360, 360 - currentDegree))

    if (degree <= 0) return

    const start = currentDegree
    const end = currentDegree + degree
    segments.push(`${meal.color} ${start}deg ${end}deg`)
    currentDegree = end
  })

  if (currentDegree < 360) {
    segments.push(`#e8e8e8 ${currentDegree}deg 360deg`)
  }

  return {
    background: `conic-gradient(${segments.join(', ')})`
  }
})

const extractMealCalorie = (mealStat) => {
  if (mealStat === null || mealStat === undefined) return null
  if (typeof mealStat === 'number') return toNumber(mealStat)
  if (typeof mealStat !== 'object') return null

  const calorie = mealStat.actual?.calorie
    ?? mealStat.calorie
    ?? mealStat.total_calorie
    ?? mealStat.totalCalorie
    ?? mealStat.value

  return calorie === null || calorie === undefined ? null : toNumber(calorie)
}

const getMealStatCalorie = (type) => {
  const byMealType = todayStats.value.by_meal_type
  if (!byMealType) return null

  if (Array.isArray(byMealType)) {
    const mealStat = byMealType.find(item => {
      const mealType = item?.meal_type ?? item?.type
      return Number(mealType) === Number(type)
    })
    return extractMealCalorie(mealStat)
  }

  if (typeof byMealType === 'object') {
    const mealKey = mealTypeKeyMap[type]
    const mealStat = byMealType[type]
      ?? byMealType[String(type)]
      ?? byMealType[mealKey]
    return extractMealCalorie(mealStat)
  }

  return null
}

const mealBreakdown = computed(() => {
  const meals = mealTypes.map(meal => {
    const statCalorie = getMealStatCalorie(meal.type)
    const calorie = statCalorie !== null ? statCalorie : getMealCalorie(meal.type)

    return {
      ...meal,
      calorie: Math.round(calorie),
      count: getMealCount(meal.type),
      color: {
        breakfast: '#ffb74d',
        lunch: '#4caf50',
        dinner: '#5c6bc0',
        snack: '#ec407a'
      }[meal.class]
    }
  })

  const total = meals.reduce((sum, meal) => sum + meal.calorie, 0)

  return meals.map(meal => {
    const percent = total ? Number(((meal.calorie / total) * 100).toFixed(1)) : 0
    let percentText = '0%'

    if (percent > 0 && percent < 1) {
      percentText = '<1%'
    } else if (percent >= 1) {
      percentText = `${Math.round(percent)}%`
    }

    return {
      ...meal,
      percent,
      percentText
    }
  })
})

const mealRingLegend = computed(() => mealBreakdown.value.filter(meal => meal.calorie > 0))

// 方法
const formatNutrient = (value) => {
  return value ? value.toFixed(1) : '0.0'
}

const getPercent = (actual, target) => {
  if (!target) return 0
  return Math.min(100, Math.round(((actual || 0) / target) * 100))
}

const getNutrientStatus = (actual, target) => {
  if (!target) return ''
  const ratio = (actual || 0) / target
  if (ratio < 0.8) return 'insufficient'
  if (ratio > 1.2) return 'excess'
  return 'normal'
}

const getNutrientRemainingText = (actual, target) => {
  if (!target) return ''
  const diff = target - (actual || 0)
  if (diff > 0) {
    return `还需 ${diff.toFixed(1)}g`
  } else if (diff < 0) {
    return `超出 ${Math.abs(diff).toFixed(1)}g`
  }
  return '已达标'
}

const getMealCalorie = (type) => {
  const meals = todayMeals.value[type] || []
  return meals.reduce((sum, m) => sum + (m.calorie || 0), 0)
}

const getMealCount = (type) => {
  return (todayMeals.value[type] || []).length
}

const goToMine = () => {
  uni.switchTab({ url: '/pages/mine/mine' })
}

const goToRecord = (mealType) => {
  const url = mealType 
    ? `/pages/record/record?mealType=${mealType}` 
    : '/pages/record/record'
  uni.navigateTo({ url })
}

// 获取数据
const fetchData = async () => {
  loading.value = true
  try {
    // 并行获取今日统计和饮食记录
    const [statsData, mealsData] = await Promise.all([
      getTodayStats(),
      getMealsByDate(dayjs().format('YYYY-MM-DD'))
    ])
    
    todayStats.value = statsData || {}
    todayMeals.value = mealsData?.meals || {}
  } catch (error) {
    console.error('获取数据失败:', error)
  } finally {
    loading.value = false
  }
}

// 检查登录状态
const checkLogin = () => {
  if (!userStore.isLoggedIn) {
    uni.reLaunch({ url: '/pages/login/login' })
    return false
  }
  return true
}

const refreshIndexData = async () => {
  if (!checkLogin()) return

  if (!profile.value) {
    try {
      await userStore.fetchProfile()
    } catch (e) {
      console.error('获取用户档案失败:', e)
    }
  }

  try {
    await Promise.all([
      fetchData(),
      fetchAnnouncement()
    ])
  } catch (e) {
    console.error('获取首页数据失败:', e)
  }
}

const fetchAnnouncement = async () => {
  try {
    const text = await getAnnouncement()
    if (!text) return

    announcement.value = text

    // 检查今日是否已关闭
    const today = dayjs().format('YYYY-MM-DD')
    const dismissed = uni.getStorageSync('announcement_dismissed')
    if (dismissed === today) return

    showAnnouncementModal.value = true
  } catch (e) {
    console.error('获取公告失败:', e)
  }
}

const closeAnnouncement = () => {
  showAnnouncementModal.value = false
  if (dontShowToday.value) {
    const today = dayjs().format('YYYY-MM-DD')
    uni.setStorageSync('announcement_dismissed', today)
  }
}

onMounted(async () => {
  await refreshIndexData()
})

// 页面显示时刷新数据
uni.$on('refreshIndex', fetchData)

onShow(async () => {
  // 切回首页时刷新数据，但不重复弹公告
  if (!checkLogin()) return
  try {
    await fetchData()
  } catch (e) {
    console.error('获取首页数据失败:', e)
  }
})

onUnload(() => {
  uni.$off('refreshIndex', fetchData)
})
</script>

<style lang="scss" scoped>
.index-container {
  height: 100vh;
  overflow: hidden;
  background: #f5f5f5;
}

.index-scroll {
  height: 100%;
  width: 100%;
  box-sizing: border-box;
}

.scroll-inner {
  padding-bottom: 120rpx;
  box-sizing: border-box;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 40rpx 30rpx;
  background: linear-gradient(135deg, #4caf50 0%, #81c784 100%);
  
  .user-info {
    display: flex;
    align-items: center;
    
    .avatar {
      width: 80rpx;
      height: 80rpx;
      border-radius: 50%;
      background: rgba(255,255,255,0.3);
      display: flex;
      align-items: center;
      justify-content: center;
      margin-right: 20rpx;
      
      .avatar-text {
        color: #fff;
        font-size: 28rpx;
        font-weight: bold;
      }

      .avatar-img {
        width: 80rpx;
        height: 80rpx;
        border-radius: 50%;
      }
    }
    
    .info {
      display: flex;
      flex-direction: column;
      
      .greeting {
        color: #fff;
        font-size: 32rpx;
        font-weight: bold;
      }
      
      .goal-text {
        color: rgba(255,255,255,0.8);
        font-size: 24rpx;
        margin-top: 4rpx;
      }
    }
  }
  
  .date {
    color: rgba(255,255,255,0.9);
    font-size: 26rpx;
  }
}

.announcement-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 999;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 60rpx;
}

.announcement-modal {
  width: 100%;
  max-width: 600rpx;
  background: #fff;
  border-radius: 24rpx;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.announcement-modal__header {
  display: flex;
  align-items: center;
  gap: 16rpx;
  padding: 40rpx 40rpx 20rpx;
  border-bottom: 1rpx solid #f0f0f0;

  .announcement-modal__icon {
    font-size: 40rpx;
  }

  .announcement-modal__title {
    font-size: 34rpx;
    font-weight: bold;
    color: #333;
  }
}

.announcement-modal__body {
  padding: 30rpx 40rpx;
  max-height: 400rpx;
}

.announcement-modal__text {
  font-size: 28rpx;
  color: #555;
  line-height: 1.8;
}

.announcement-modal__footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24rpx 40rpx 40rpx;
}

.announcement-modal__checkbox {
  display: flex;
  align-items: center;
  gap: 12rpx;

  .checkbox-box {
    width: 36rpx;
    height: 36rpx;
    border: 2rpx solid #ccc;
    border-radius: 6rpx;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 24rpx;
    color: #fff;
    transition: all 0.2s;

    &--checked {
      background: #4caf50;
      border-color: #4caf50;
    }
  }

  .checkbox-label {
    font-size: 26rpx;
    color: #999;
  }
}

.announcement-modal__btn {
  background: linear-gradient(135deg, #4caf50, #81c784);
  color: #fff;
  font-size: 28rpx;
  font-weight: 500;
  padding: 16rpx 40rpx;
  border-radius: 40rpx;
}

.calorie-card {
  margin: -40rpx 30rpx 30rpx;
  background: #fff;
  border-radius: 24rpx;
  padding: 40rpx;
  box-shadow: 0 4rpx 20rpx rgba(0,0,0,0.08);

  .calorie-summary {
    display: flex;
    align-items: center;
  }
   
  .calorie-ring {
    width: 180rpx;
    height: 180rpx;
    position: relative;
    margin-right: 40rpx;
    flex-shrink: 0;

    .ring-progress {
      position: absolute;
      width: 100%;
      height: 100%;
      border-radius: 50%;
      transform: rotate(-90deg);
      transition: background 0.3s ease;
      box-shadow: inset 0 0 0 2rpx rgba(76, 175, 80, 0.06);
    }
     
    .ring-center {
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      width: 132rpx;
      height: 132rpx;
      border-radius: 50%;
      background: #fff;
      text-align: center;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      box-shadow: 0 2rpx 12rpx rgba(76, 175, 80, 0.08);
      
      .calorie-value {
        display: block;
        font-size: 38rpx;
        font-weight: bold;
        color: #333;
        line-height: 1.1;
      }
      
      .calorie-unit {
        font-size: 22rpx;
        color: #999;
      }

      .calorie-percent {
        margin-top: 6rpx;
        font-size: 22rpx;
        color: #4caf50;
        font-weight: 600;
      }
    }
  }
  
  .calorie-info {
    flex: 1;
    
    .info-item {
      display: flex;
      justify-content: space-between;
      margin-bottom: 16rpx;
      
      &:last-child {
        margin-bottom: 0;
      }
      
      .label {
        font-size: 26rpx;
        color: #999;
      }
      
      .value {
        font-size: 26rpx;
        color: #333;
        font-weight: 500;
        
        &.warning {
          color: #f44336;
        }
        
        &.progress,
        &.score {
          color: #4caf50;
          font-weight: bold;
        }
      }
    }

    .meal-ring-legend {
      margin-top: 22rpx;
      display: flex;
      flex-direction: column;
      gap: 12rpx;

      .legend-item {
        display: flex;
        align-items: center;
        gap: 12rpx;
        font-size: 22rpx;
        color: #666;
      }

      .legend-dot {
        width: 14rpx;
        height: 14rpx;
        border-radius: 50%;
        flex-shrink: 0;
      }

      .legend-name {
        width: 72rpx;
        color: #333;
      }

      .legend-value {
        color: #999;
      }
    }
  }
}

.section-title {
  font-size: 32rpx;
  font-weight: bold;
  color: #333;
  margin-bottom: 20rpx;
  padding: 0 30rpx;
}

.nutrient-section {
  margin-bottom: 30rpx;
  
  .nutrient-cards {
    display: flex;
    padding: 0 30rpx;
    gap: 20rpx;
    
    .nutrient-card {
      flex: 1;
      background: #fff;
      border-radius: 16rpx;
      padding: 24rpx;
      display: flex;
      flex-direction: column;
      align-items: center;
      
      .nutrient-icon {
        width: 60rpx;
        height: 60rpx;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 28rpx;
        font-weight: bold;
        color: #fff;
        margin-bottom: 12rpx;
      }
      
      &.protein .nutrient-icon { background: #e91e63; }
      &.carb .nutrient-icon { background: #ff9800; }
      &.fat .nutrient-icon { background: #9c27b0; }
      
      .nutrient-info {
        width: 100%;
        text-align: center;
        
        .name {
          font-size: 24rpx;
          color: #999;
          display: block;
        }
        
        .value {
          font-size: 32rpx;
          font-weight: bold;
          color: #333;
          display: block;
          margin: 4rpx 0;
        }
        
        .remaining {
          font-size: 22rpx;
          display: block;
          margin-bottom: 8rpx;
          
          &.insufficient {
            color: #ff9800;
          }
          
          &.excess {
            color: #f44336;
          }
          
          &.normal {
            color: #4caf50;
          }
        }
        
        .progress-bar {
          height: 8rpx;
          background: #e8e8e8;
          border-radius: 4rpx;
          overflow: hidden;
          
          .progress {
            height: 100%;
            background: #4caf50;
            border-radius: 4rpx;
            transition: width 0.3s;
          }
        }
      }
    }
  }
}

.meal-section {
  .meal-list {
    background: #fff;
    margin: 0 30rpx;
    border-radius: 16rpx;
    overflow: hidden;
    
    .meal-item {
      display: flex;
      align-items: center;
      padding: 30rpx;
      border-bottom: 1rpx solid #f0f0f0;
      
      &:last-child {
        border-bottom: none;
      }
      
      .meal-icon {
        width: 80rpx;
        height: 80rpx;
        border-radius: 16rpx;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 40rpx;
        margin-right: 24rpx;
        
        &.breakfast { background: #fff3e0; }
        &.lunch { background: #e3f2fd; }
        &.dinner { background: #f3e5f5; }
        &.snack { background: #e8f5e9; }
      }
      
      .meal-info {
        flex: 1;
        
        .meal-name {
          font-size: 30rpx;
          color: #333;
          font-weight: 500;
          display: block;
        }
        
        .meal-calorie {
          font-size: 26rpx;
          color: #999;
          margin-top: 4rpx;
        }
      }
      
      .meal-count {
        font-size: 26rpx;
        color: #999;
        margin-right: 16rpx;
      }
      
      .arrow {
        font-size: 36rpx;
        color: #ccc;
      }
    }
  }
}

</style>
