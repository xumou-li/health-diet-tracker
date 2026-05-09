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

        <!-- 功能菜单 -->
        <view class="menu-section">
          <view class="menu-item" @click="goToBodyProfile">
            <text class="menu-icon">🧬</text>
            <text class="menu-text">身体档案</text>
            <text class="menu-arrow">›</text>
          </view>
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

const healthGoalText = computed(() => {
  const goals = { 1: '维持体重', 2: '减脂中', 3: '增肌中' }
  return goals[profile.value?.health_goal] || '--'
})

// 方法
const goToBodyProfile = () => {
  uni.navigateTo({ url: '/pages/mine/body-profile' })
}

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
  height: 100%;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
  box-sizing: border-box;
  /* #ifdef H5 */
  padding-bottom: 100rpx;
  /* #endif */
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

.menu-section {
  margin: 20rpx 30rpx 0;
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
