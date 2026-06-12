<template>
  <view class="body-profile-container">
    <!-- #ifdef H5 -->
    <view class="body-profile-scroll">
    <!-- #endif -->
    <!-- #ifndef H5 -->
    <scroll-view scroll-y class="body-profile-scroll">
    <!-- #endif -->
      <view class="body-profile-content">
        <!-- 身体数据卡片 -->
        <view class="body-card">
          <view class="card-title">身体数据</view>
          <view class="body-grid">
            <view class="body-item">
              <text class="value">{{ profile?.height_cm || '--' }}</text>
              <text class="label">身高(cm)</text>
            </view>
            <view class="body-item">
              <text class="value">{{ profile?.weight_kg || '--' }}</text>
              <text class="label">体重(kg)</text>
            </view>
            <view class="body-item">
              <text class="value" :style="{ color: bmiColor }">{{ profile?.bmi || '--' }}</text>
              <text class="label">BMI</text>
            </view>
            <view class="body-item">
              <text class="value">{{ profile?.bmr || '--' }}</text>
              <text class="label">BMR(kcal)</text>
            </view>
          </view>
          <view class="calorie-goal">
            <text class="goal-label">每日目标热量</text>
            <text class="goal-value">{{ calibratedDailyGoal }} kcal</text>
          </view>

          <view class="profile-meta-row">
            <view class="meta-item">
              <text class="meta-label">健康目标</text>
              <text class="meta-value">{{ healthGoalText }}</text>
            </view>
            <view class="meta-item">
              <text class="meta-label">活动水平</text>
              <text class="meta-value">{{ profile ? userStore.activityLevelText : '--' }}</text>
            </view>
            <view class="meta-item">
              <text class="meta-label">热量系数</text>
              <text class="meta-value">{{ profile?.calorie_coefficient?.toFixed ? profile.calorie_coefficient.toFixed(2) : Number(profile?.calorie_coefficient || 0).toFixed(2) }}x</text>
            </view>
          </view>
          
          <!-- 营养素比例 -->
          <view class="nutrient-ratio" v-if="profile?.protein_ratio !== undefined">
            <view class="ratio-title">营养素比例</view>
            <view class="ratio-bars">
              <view class="ratio-bar-item">
                <view class="bar-label">蛋白质</view>
                <view class="bar-track">
                  <view class="bar-fill protein" :style="{ width: profile.protein_ratio * 100 + '%' }"></view>
                </view>
                <view class="bar-value">{{ Math.round(profile.protein_ratio * 100) }}%</view>
              </view>
              <view class="ratio-bar-item">
                <view class="bar-label">脂肪</view>
                <view class="bar-track">
                  <view class="bar-fill fat" :style="{ width: profile.fat_ratio * 100 + '%' }"></view>
                </view>
                <view class="bar-value">{{ Math.round(profile.fat_ratio * 100) }}%</view>
              </view>
              <view class="ratio-bar-item">
                <view class="bar-label">碳水</view>
                <view class="bar-track">
                  <view class="bar-fill carb" :style="{ width: profile.carb_ratio * 100 + '%' }"></view>
                </view>
                <view class="bar-value">{{ Math.round(profile.carb_ratio * 100) }}%</view>
              </view>
            </view>
            <view class="nutrient-targets" v-if="profile?.nutrient_targets">
              <text class="target-item">蛋白目标: {{ profile.nutrient_targets.protein?.toFixed(1) }}g</text>
              <text class="target-item">脂肪目标: {{ profile.nutrient_targets.fat?.toFixed(1) }}g</text>
              <text class="target-item">碳水目标: {{ profile.nutrient_targets.carb?.toFixed(1) }}g</text>
            </view>
          </view>
        </view>

        <!-- 个人代谢分析卡片 -->
        <view class="metabolism-card" v-if="metabolismData?.is_calibrated">
          <view class="card-title">
            <text>个人代谢分析</text>
            <text class="coeff-badge">代谢系数 {{ metabolismData.coefficient?.toFixed(3) }}</text>
          </view>

          <view class="metabolism-compare">
            <view class="compare-item formula">
              <text class="compare-label">修正前每日推荐</text>
              <text class="compare-value">{{ formulaDailyGoal }} kcal/天</text>
              <text class="compare-desc">基于通用公式</text>
            </view>
            <text class="compare-arrow">→</text>
            <view class="compare-item actual">
              <text class="compare-label">修正后每日推荐</text>
              <text class="compare-value">{{ calibratedDailyGoal }} kcal/天</text>
              <text class="compare-desc">结合您的实际代谢</text>
            </view>
          </view>

          <view class="metabolism-footer">
            <text class="footer-text">
              基于 {{ metabolismData.sample_pairs }} 组身体快照数据 · 最近校准 {{ metabolismData.latest_calibrated_at?.slice(0, 10) }}
            </text>
          </view>
        </view>

        <!-- 未校准时的提示 -->
        <view class="no-calibration" v-else-if="profile">
          <text class="no-cal-text">代谢分析</text>
          <text class="no-cal-hint">记录多天体重数据后，系统将自动分析您的个人代谢系数</text>
        </view>

        <view class="tabbar-safe-space"></view>
      </view>
    <!-- #ifdef H5 -->
    </view>
    <!-- #endif -->
    <!-- #ifndef H5 -->
    </scroll-view>
    <!-- #endif -->
  </view>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useUserStore } from '@/store/user'
import { BASE_URL, request } from '@/api/request'
import { getBMIStatus, calculateBMR, calculateAgeFromBirthday, calculateDailyCalorie } from '@/utils/nutrition'

const userStore = useUserStore()
const metabolismData = ref(null)

const profile = computed(() => userStore.profile)

const bmiStatus = computed(() => {
  if (!profile.value?.bmi) return null
  return getBMIStatus(profile.value.bmi)
})

const bmiColor = computed(() => {
  return bmiStatus.value?.color || '#333'
})

const healthGoalText = computed(() => {
  const goals = { 1: '维持体重', 2: '减脂中', 3: '增肌中' }
  return goals[profile.value?.health_goal] || '--'
})

const formulaDailyGoal = computed(() => {
  if (!profile.value) return '--'
  const age = calculateAgeFromBirthday(profile.value.birthday)
  if (!age) return '--'
  const bmr = calculateBMR(profile.value.weight_kg, profile.value.height_cm, age, profile.value.gender)
  return calculateDailyCalorie(bmr, profile.value.activity_level, profile.value.health_goal, profile.value.calorie_coefficient)
})

const calibratedDailyGoal = computed(() => {
  if (!formulaDailyGoal.value || formulaDailyGoal.value === '--') return '--'
  const mc = profile.value?.metabolic_coefficient
  if (!mc || mc === 1) return formulaDailyGoal.value
  return Math.round(formulaDailyGoal.value * mc)
})

const fetchMetabolismInsight = async () => {
  try {
    const data = await request({
      url: BASE_URL + '/api/stats/metabolism-insight',
      method: 'GET',
      showError: false
    })
    if (data) {
      metabolismData.value = data
    }
  } catch (e) {
    // 静默失败
  }
}

const syncProfile = async () => {
  userStore.initFromStorage()
  if (userStore.isLoggedIn && !profile.value) {
    await userStore.fetchProfile()
  }
}

onMounted(async () => {
  try {
    await syncProfile()
    fetchMetabolismInsight()
  } catch (e) {
    // 静默失败
  }
})
</script>

<style lang="scss" scoped>
.body-profile-container {
  height: 100vh;
  overflow: hidden;
  background: #f5f5f5;
}

.body-profile-scroll {
  height: 100%;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
  box-sizing: border-box;
  /* #ifdef H5 */
  padding-bottom: 100rpx;
  /* #endif */
}

.body-profile-content {
  min-height: 100%;
  box-sizing: border-box;
  padding-top: 30rpx;
}

.tabbar-safe-space {
  /* #ifdef H5 */
  height: 120rpx;
  /* #endif */
  /* #ifndef H5 */
  height: 70rpx;
  /* #endif */
}

/* ===== 身体数据卡片 ===== */
.body-card {
  margin: 0 30rpx 20rpx;
  background: #fff;
  border-radius: 20rpx;
  padding: 30rpx;
  
  .card-title {
    font-size: 30rpx;
    font-weight: bold;
    color: #333;
    margin-bottom: 24rpx;
  }
  
  .body-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 20rpx;
    margin-bottom: 24rpx;
    
    .body-item {
      text-align: center;
      
      .value {
        display: block;
        font-size: 36rpx;
        font-weight: bold;
        color: #333;
      }
      
      .label {
        display: block;
        font-size: 22rpx;
        color: #999;
        margin-top: 8rpx;
      }
    }
  }
  
  .calorie-goal {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 20rpx;
    background: #e8f5e9;
    border-radius: 12rpx;
    
    .goal-label {
      font-size: 28rpx;
      color: #666;
    }
    
    .goal-value {
      font-size: 32rpx;
      font-weight: bold;
      color: #4caf50;
    }
  }

  .profile-meta-row {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 16rpx;
    margin-top: 20rpx;

    .meta-item {
      padding: 18rpx 16rpx;
      background: #f8fbf8;
      border-radius: 12rpx;
      text-align: center;
    }

    .meta-label {
      display: block;
      font-size: 22rpx;
      color: #999;
      margin-bottom: 8rpx;
    }

    .meta-value {
      display: block;
      font-size: 24rpx;
      color: #333;
      font-weight: 600;
      line-height: 1.4;
      word-break: break-all;
    }
  }
  
  .nutrient-ratio {
    margin-top: 24rpx;
    padding-top: 24rpx;
    border-top: 1rpx solid #f0f0f0;
    
    .ratio-title {
      font-size: 28rpx;
      color: #333;
      margin-bottom: 16rpx;
    }
    
    .ratio-bars {
      margin-bottom: 16rpx;
      
      .ratio-bar-item {
        display: flex;
        align-items: center;
        margin-bottom: 12rpx;
        
        &:last-child {
          margin-bottom: 0;
        }
        
        .bar-label {
          width: 80rpx;
          font-size: 24rpx;
          color: #666;
        }
        
        .bar-track {
          flex: 1;
          height: 16rpx;
          background: #f0f0f0;
          border-radius: 8rpx;
          overflow: hidden;
          margin: 0 16rpx;
          
          .bar-fill {
            height: 100%;
            border-radius: 8rpx;
            
            &.protein { background: #e91e63; }
            &.fat { background: #9c27b0; }
            &.carb { background: #ff9800; }
          }
        }
        
        .bar-value {
          width: 60rpx;
          text-align: right;
          font-size: 24rpx;
          color: #333;
        }
      }
    }
    
    .nutrient-targets {
      display: flex;
      flex-wrap: wrap;
      gap: 16rpx;
      padding-top: 16rpx;
      border-top: 1rpx solid #f0f0f0;
      
      .target-item {
        font-size: 24rpx;
        color: #666;
        background: #f5f5f5;
        padding: 8rpx 16rpx;
        border-radius: 8rpx;
      }
    }
  }
}

/* ===== 个人代谢分析卡片 ===== */
.metabolism-card {
  margin: 0 30rpx 20rpx;
  background: #fff;
  border-radius: 20rpx;
  padding: 30rpx;

  .card-title {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 24rpx;
    font-size: 30rpx;
    font-weight: bold;
    color: #333;

    .coeff-badge {
      font-size: 20rpx;
      padding: 4rpx 16rpx;
      border-radius: 20rpx;
      font-weight: normal;
      color: #fff;
      background: #66bb6a;
    }
  }

  .metabolism-compare {
    display: flex;
    align-items: center;
    gap: 16rpx;
    margin-bottom: 20rpx;

    .compare-item {
      flex: 1;
      text-align: center;
      padding: 24rpx 16rpx;
      border-radius: 12rpx;

      &.formula {
        background: #f5f5f5;
      }
      &.actual {
        background: #e8f5e9;
      }

      .compare-label {
        display: block;
        font-size: 22rpx;
        color: #999;
        margin-bottom: 8rpx;
      }
      .compare-value {
        display: block;
        font-size: 30rpx;
        font-weight: bold;
      }
      &.formula .compare-value { color: #666; }
      &.actual .compare-value { color: #2e7d32; }
      .compare-desc {
        display: block;
        font-size: 18rpx;
        color: #bbb;
        margin-top: 6rpx;
      }
    }

    .compare-arrow {
      font-size: 28rpx;
      color: #ccc;
      flex-shrink: 0;
    }
  }

  .metabolism-footer {
    text-align: center;

    .footer-text {
      font-size: 20rpx;
      color: #ccc;
    }
  }
}

/* ===== 未校准提示 ===== */
.no-calibration {
  margin: 0 30rpx 20rpx;
  background: #fff;
  border-radius: 20rpx;
  padding: 60rpx 30rpx;
  text-align: center;
  
  .no-cal-text {
    display: block;
    font-size: 30rpx;
    font-weight: bold;
    color: #333;
    margin-bottom: 16rpx;
  }
  
  .no-cal-hint {
    display: block;
    font-size: 24rpx;
    color: #999;
    line-height: 1.6;
  }
}
</style>
