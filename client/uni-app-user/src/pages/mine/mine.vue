<template>
  <view class="mine-container">
    <!-- #ifdef H5 -->
    <view class="mine-scroll">
    <!-- #endif -->
    <!-- #ifndef H5 -->
    <scroll-view scroll-y class="mine-scroll">
    <!-- #endif -->
      <view class="mine-content">
        <!-- 用户信息卡 -->
        <view class="user-card">
          <view class="avatar">
            <image
              v-if="avatarUrl"
              class="avatar-img"
              :src="avatarUrl"
              mode="aspectFill"
            />
            <text v-else class="avatar-text">{{ userInitial }}</text>
          </view>
          <view class="user-info">
            <text class="phone">{{ displayName }}</text>
            <view class="health-tags">
              <text class="tag">{{ bmiStatusText }}</text>
              <text class="tag">{{ healthGoalText }}</text>
            </view>
          </view>
        </view>

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
            <text class="goal-value">{{ profile?.daily_calorie_goal || '--' }} kcal</text>
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

        <!-- 功能菜单 -->
        <view class="menu-section">
          <view class="menu-item" @click="goToEditProfile">
            <text class="menu-icon">📝</text>
            <text class="menu-text">编辑身体档案</text>
            <text class="menu-arrow">›</text>
          </view>
          <view class="menu-item" @click="goToBodyHistory">
            <text class="menu-icon">📊</text>
            <text class="menu-text">体重记录历史</text>
            <text class="menu-arrow">›</text>
          </view>
          <view class="menu-item" @click="goToFavorites">
            <text class="menu-icon">⭐</text>
            <text class="menu-text">我的收藏</text>
            <text class="menu-arrow">›</text>
          </view>
          <view class="menu-item" @click="goToAccountSettings">
            <text class="menu-icon">⚙️</text>
            <text class="menu-text">账户设置</text>
            <text class="menu-arrow">›</text>
          </view>
          <view class="menu-item" @click="goToAbout">
            <text class="menu-icon">ℹ️</text>
            <text class="menu-text">关于我们</text>
            <text class="menu-arrow">›</text>
          </view>
        </view>

        <!-- 登录 / 退出登录 -->
        <view class="logout-section">
          <view v-if="isLoggedIn" class="logout-btn" @click="handleLogout">退出登录</view>
          <view v-else class="login-btn" @click="goToLogin">登录</view>
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
import { ref, computed, onMounted, watch } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { useUserStore } from '@/store/user'
import { BASE_URL } from '@/api/request'
import {
  getBMIStatus
} from '@/utils/nutrition'

const userStore = useUserStore()
const hasUserSession = ref(false)

const profile = computed(() => userStore.profile)
const isLoggedIn = computed(() => hasUserSession.value)

const userInitial = computed(() => {
  if (profile.value?.nickname) {
    return profile.value.nickname.charAt(0).toUpperCase()
  }
  if (profile.value?.phone) {
    return profile.value.phone.slice(-2)
  }
  if (profile.value?.email) {
    return profile.value.email.charAt(0).toUpperCase()
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

const displayName = computed(() => {
  if (profile.value?.nickname) return profile.value.nickname
  if (profile.value?.phone) return profile.value.phone
  if (profile.value?.email) return profile.value.email
  return '未登录'
})

const bmiStatus = computed(() => {
  if (!profile.value?.bmi) return null
  return getBMIStatus(profile.value.bmi)
})

const bmiStatusText = computed(() => {
  return bmiStatus.value?.status || '--'
})

const bmiColor = computed(() => {
  return bmiStatus.value?.color || '#333'
})

const healthGoalText = computed(() => {
  const goals = { 1: '维持体重', 2: '减脂中', 3: '增肌中' }
  return goals[profile.value?.health_goal] || '--'
})

// 方法
const goToEditProfile = () => {
  uni.navigateTo({ url: '/pages/mine/profile-edit' })
}

const goToBodyHistory = () => {
  uni.navigateTo({ url: '/pages/mine/body-history' })
}

const goToFavorites = () => {
  uni.navigateTo({ url: '/pages/mine/favorites' })
}

const goToAccountSettings = () => {
  uni.navigateTo({ url: '/pages/mine/account-settings' })
}

const goToAbout = () => {
  uni.showToast({ title: '功能开发中', icon: 'none' })
}

const handleLogout = () => {
  uni.showModal({
    title: '确认退出',
    content: '确定要退出登录吗？',
    success: (res) => {
      if (res.confirm) {
        userStore.logout()
      }
    }
  })
}

const goToLogin = () => {
  uni.navigateTo({ url: '/pages/login/login' })
}

const updateLoginState = () => {
  const token = userStore.token || uni.getStorageSync('token')
  const userInfo = userStore.userInfo || uni.getStorageSync('userInfo')
  hasUserSession.value = !!token || !!userInfo || !!profile.value
}

const syncUserState = async () => {
  userStore.initFromStorage()
  updateLoginState()
  if (userStore.isLoggedIn && !profile.value) {
    await userStore.fetchProfile()
    updateLoginState()
  }
}

watch(
  () => [userStore.token, userStore.userInfo, userStore.profile],
  updateLoginState,
  { immediate: true }
)

onMounted(async () => {
  try {
    await syncUserState()
  } catch (e) {
    // 静默失败，未登录或网络错误
  }
})

// H5 keep-alive 场景：切回 tab 时同步
onShow(() => {
  syncUserState().catch(() => {})
})
</script>

<style lang="scss" scoped>
.mine-container {
  height: 100vh;
  overflow: hidden;
  background: #f5f5f5;
}

.mine-scroll {
  height: 100vh;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
  box-sizing: border-box;
}

.mine-content {
  min-height: 100%;
  box-sizing: border-box;
}

.logout-section {
  margin: 40rpx 30rpx 0;

  .logout-btn {
    width: 100%;
    height: 88rpx;
    background: #fff;
    color: #f44336;
    font-size: 32rpx;
    border-radius: 44rpx;
    border: none;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .login-btn {
    width: 100%;
    height: 88rpx;
    background: #4caf50;
    color: #fff;
    font-size: 32rpx;
    border-radius: 44rpx;
    border: none;
    display: flex;
    align-items: center;
    justify-content: center;
  }
}

.tabbar-safe-space {
  /* #ifdef H5 */
  height: 120rpx;
  /* #endif */
  /* #ifndef H5 */
  height: 70rpx;
  /* #endif */
}


.user-card {
  display: flex;
  align-items: center;
  padding: 50rpx 40rpx;
  background: linear-gradient(135deg, #4caf50 0%, #81c784 100%);
  
  .avatar {
    width: 120rpx;
    height: 120rpx;
    border-radius: 50%;
    background: rgba(255,255,255,0.3);
    display: flex;
    align-items: center;
    justify-content: center;
    margin-right: 30rpx;
    
    .avatar-text {
      color: #fff;
      font-size: 40rpx;
      font-weight: bold;
    }

    .avatar-img {
      width: 120rpx;
      height: 120rpx;
      border-radius: 50%;
    }
  }
  
  .user-info {
    .phone {
      font-size: 36rpx;
      color: #fff;
      font-weight: bold;
      display: block;
      margin-bottom: 12rpx;
    }
    
    .health-tags {
      display: flex;
      gap: 16rpx;
      
      .tag {
        padding: 6rpx 16rpx;
        background: rgba(255,255,255,0.2);
        border-radius: 20rpx;
        font-size: 24rpx;
        color: #fff;
      }
    }
  }
}

.body-card {
  margin: 30rpx;
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

.menu-section {
  margin: 0 30rpx;
  background: #fff;
  border-radius: 20rpx;
  overflow: hidden;
  
  .menu-item {
    display: flex;
    align-items: center;
    padding: 30rpx;
    border-bottom: 1rpx solid #f0f0f0;
    
    &:last-child {
      border-bottom: none;
    }
    
    .menu-icon {
      font-size: 40rpx;
      margin-right: 20rpx;
    }
    
    .menu-text {
      flex: 1;
      font-size: 30rpx;
      color: #333;
    }
    
    .menu-arrow {
      font-size: 36rpx;
      color: #ccc;
    }
  }
}

</style>
