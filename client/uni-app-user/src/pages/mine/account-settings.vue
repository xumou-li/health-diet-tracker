<template>
  <view class="account-settings">
    <!-- H5 用普通 view 滚动 -->
    <!-- #ifdef H5 -->
    <view class="settings-scroll">
    <!-- #endif -->
    <!-- #ifndef H5 -->
    <scroll-view scroll-y class="settings-scroll">
    <!-- #endif -->
      <view class="settings-content">
        <!-- 头像区域 -->
        <view class="section-card">
          <view class="card-title">头像</view>
          <view class="avatar-row" @click="chooseAvatar">
            <image
              v-if="avatarUrl"
              class="avatar-img"
              :src="avatarUrl"
              mode="aspectFill"
            />
            <view v-else class="avatar-placeholder">
              <text class="avatar-text">{{ userInitial }}</text>
            </view>
            <view class="avatar-action">
              <text class="action-text">点击更换头像</text>
              <text class="action-arrow">›</text>
            </view>
          </view>
        </view>

        <!-- 昵称区域 -->
        <view class="section-card">
          <view class="card-title">昵称</view>
          <view class="nickname-row">
            <input
              class="nickname-input"
              v-model="nickname"
              placeholder="设置昵称（最多50字）"
              maxlength="50"
            />
            <view class="save-btn" @click="saveNickname">保存</view>
          </view>
        </view>

        <!-- 修改密码区域 -->
        <view class="section-card">
          <view class="card-title">修改密码</view>
          <view class="password-section">
            <!-- 未绑定邮箱提示 -->
            <view v-if="!profile?.email" class="no-email-tip">
              <text>您的账号未绑定邮箱，无法修改密码</text>
            </view>
            <template v-else>
              <!-- 发送验证码 -->
              <view class="form-item">
                <text class="form-label">邮箱</text>
                <view class="email-display">
                  <text>{{ maskedEmail }}</text>
                </view>
              </view>
              <view class="form-item">
                <text class="form-label">验证码</text>
                <view class="code-row">
                  <input
                    class="code-input"
                    v-model="verifyCode"
                    placeholder="请输入验证码"
                    maxlength="6"
                    type="number"
                  />
                  <view
                    class="send-code-btn"
                    :class="{ disabled: codeCountdown > 0 }"
                    @click="sendCode"
                  >
                    <text v-if="codeCountdown > 0">{{ codeCountdown }}s</text>
                    <text v-else>获取验证码</text>
                  </view>
                </view>
              </view>
              <view class="form-item">
                <text class="form-label">新密码</text>
                <input
                  class="password-input"
                  v-model="newPassword"
                  placeholder="至少6位"
                  :password="!showPassword"
                />
                <text class="toggle-pwd" @click="showPassword = !showPassword">
                  {{ showPassword ? '隐藏' : '显示' }}
                </text>
              </view>
              <view class="confirm-btn" @click="changePassword">确认修改</view>
            </template>
          </view>
        </view>
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
import { uploadAvatar, updateProfile, sendChangePasswordCode, changePassword as doChangePassword } from '@/api/user'
import { BASE_URL } from '@/api/request'

const userStore = useUserStore()

const profile = computed(() => userStore.profile)

// 头像
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

const userInitial = computed(() => {
  const nick = profile.value?.nickname
  if (nick) return nick.charAt(0).toUpperCase()
  if (profile.value?.phone) return profile.value.phone.slice(-2)
  if (profile.value?.email) return profile.value.email.charAt(0).toUpperCase()
  return 'U'
})

// 昵称
const nickname = ref('')

// 修改密码
const maskedEmail = computed(() => {
  const email = profile.value?.email
  if (!email) return ''
  const [name, domain] = email.split('@')
  if (name.length <= 2) return email
  return name.charAt(0) + '***' + name.charAt(name.length - 1) + '@' + domain
})

const verifyCode = ref('')
const newPassword = ref('')
const showPassword = ref(false)
const codeCountdown = ref(0)
let countdownTimer = null

// 选择头像
const chooseAvatar = () => {
  uni.chooseImage({
    count: 1,
    sizeType: ['compressed'],
    sourceType: ['album', 'camera'],
    success: async (res) => {
      const filePath = res.tempFilePaths[0]
      try {
        await uploadAvatar(filePath)
        uni.showToast({ title: '头像更新成功', icon: 'success' })
        await userStore.fetchProfile()
      } catch (e) {
        // 错误已由 API 层处理
      }
    }
  })
}

// 保存昵称
const saveNickname = async () => {
  const val = nickname.value.trim()
  if (!val) {
    return uni.showToast({ title: '请输入昵称', icon: 'none' })
  }
  try {
    await updateProfile({ nickname: val })
    uni.showToast({ title: '昵称保存成功', icon: 'success' })
    await userStore.fetchProfile()
  } catch (e) {
    // 错误已由 API 层处理
  }
}

// 发送验证码
const sendCode = async () => {
  if (codeCountdown.value > 0) return
  try {
    await sendChangePasswordCode()
    uni.showToast({ title: '验证码已发送', icon: 'success' })
    // 倒计时
    codeCountdown.value = 60
    countdownTimer = setInterval(() => {
      codeCountdown.value--
      if (codeCountdown.value <= 0) {
        clearInterval(countdownTimer)
      }
    }, 1000)
  } catch (e) {
    // 错误已由 API 层处理
  }
}

// 修改密码
const changePassword = async () => {
  const code = verifyCode.value.trim()
  const pwd = newPassword.value

  if (!code) {
    return uni.showToast({ title: '请输入验证码', icon: 'none' })
  }
  if (!pwd || pwd.length < 6) {
    return uni.showToast({ title: '新密码至少6位', icon: 'none' })
  }

  uni.showModal({
    title: '确认修改',
    content: '确定要修改密码吗？',
    success: async (res) => {
      if (res.confirm) {
        try {
          await doChangePassword({ code, new_password: pwd })
          uni.showToast({ title: '密码修改成功', icon: 'success' })
          verifyCode.value = ''
          newPassword.value = ''
        } catch (e) {
          // 错误已由 API 层处理
        }
      }
    }
  })
}

onMounted(() => {
  nickname.value = profile.value?.nickname || ''
})
</script>

<style lang="scss" scoped>
.account-settings {
  height: 100vh;
  overflow: hidden;
  background: #f5f5f5;
}

.settings-scroll {
  height: 100vh;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
  box-sizing: border-box;
  padding: 20rpx 30rpx 40rpx;
}

.settings-content {
  min-height: 100%;
}

.section-card {
  background: #fff;
  border-radius: 20rpx;
  padding: 30rpx;
  margin-bottom: 20rpx;
  box-sizing: border-box;

  .card-title {
    font-size: 30rpx;
    font-weight: bold;
    color: #333;
    margin-bottom: 24rpx;
  }
}

// 头像
.avatar-row {
  display: flex;
  align-items: center;

  .avatar-img {
    width: 120rpx;
    height: 120rpx;
    border-radius: 50%;
    flex-shrink: 0;
  }

  .avatar-placeholder {
    width: 120rpx;
    height: 120rpx;
    border-radius: 50%;
    background: linear-gradient(135deg, #4caf50 0%, #81c784 100%);
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;

    .avatar-text {
      color: #fff;
      font-size: 40rpx;
      font-weight: bold;
    }
  }

  .avatar-action {
    margin-left: 30rpx;
    display: flex;
    align-items: center;

    .action-text {
      font-size: 28rpx;
      color: #4caf50;
    }

    .action-arrow {
      font-size: 36rpx;
      color: #ccc;
      margin-left: 8rpx;
    }
  }
}

// 昵称
.nickname-row {
  display: flex;
  align-items: center;
  gap: 20rpx;

  .nickname-input {
    flex: 1;
    height: 72rpx;
    line-height: 72rpx;
    font-size: 28rpx;
    padding: 0 20rpx;
    background: #f5f5f5;
    border-radius: 12rpx;
    box-sizing: border-box;
  }

  .save-btn {
    flex-shrink: 0;
    padding: 0 32rpx;
    height: 72rpx;
    line-height: 72rpx;
    background: #4caf50;
    color: #fff;
    font-size: 28rpx;
    border-radius: 36rpx;
    text-align: center;
  }
}

// 密码修改
.password-section {
  .no-email-tip {
    padding: 40rpx 0;
    text-align: center;
    font-size: 28rpx;
    color: #999;
  }

  .form-item {
    margin-bottom: 24rpx;

    .form-label {
      display: block;
      font-size: 26rpx;
      color: #666;
      margin-bottom: 12rpx;
    }

    .email-display {
      height: 72rpx;
      line-height: 72rpx;
      padding: 0 20rpx;
      background: #f5f5f5;
      border-radius: 12rpx;
      font-size: 28rpx;
      color: #333;
    }

    .code-row {
      display: flex;
      align-items: center;
      gap: 20rpx;

      .code-input {
        flex: 1;
        height: 72rpx;
        line-height: 72rpx;
        font-size: 28rpx;
        padding: 0 20rpx;
        background: #f5f5f5;
        border-radius: 12rpx;
        box-sizing: border-box;
      }

      .send-code-btn {
        flex-shrink: 0;
        padding: 0 24rpx;
        height: 72rpx;
        line-height: 72rpx;
        background: #4caf50;
        color: #fff;
        font-size: 26rpx;
        border-radius: 36rpx;
        text-align: center;

        &.disabled {
          background: #ccc;
          color: #999;
        }
      }
    }

    .password-input {
      height: 72rpx;
      line-height: 72rpx;
      font-size: 28rpx;
      padding: 0 20rpx;
      background: #f5f5f5;
      border-radius: 12rpx;
      width: 100%;
      box-sizing: border-box;
    }

    .toggle-pwd {
      display: inline-block;
      margin-top: 10rpx;
      font-size: 24rpx;
      color: #4caf50;
    }
  }

  .confirm-btn {
    margin-top: 10rpx;
    width: 100%;
    height: 80rpx;
    line-height: 80rpx;
    background: #4caf50;
    color: #fff;
    font-size: 30rpx;
    border-radius: 40rpx;
    text-align: center;
  }
}
</style>
