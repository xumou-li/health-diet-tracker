<template>
  <view class="login-container">
    <!-- Logo区域 -->
    <view class="logo-section">
      <image class="logo" src="/static/logo.png" mode="aspectFit"></image>
      <text class="app-name">健康饮食记录</text>
      <text class="app-desc">科学饮食，健康生活</text>
    </view>

    <!-- 登录表单 -->
    <view class="form-section" v-if="!isRegister">
      <view class="input-group">
        <uni-easyinput
          v-model="loginForm.account"
          placeholder="请输入手机号/邮箱"
          prefixIcon="person"
        />
      </view>
      <view class="input-group">
        <uni-easyinput
          v-model="loginForm.password"
          type="password"
          placeholder="请输入密码"
          prefixIcon="locked"
        />
      </view>
      <button class="btn-primary" @click="handleLogin" :loading="loading">
        登录
      </button>
      <view class="switch-tip">
        <text>还没有账号？</text>
        <text class="link" @click="isRegister = true">立即注册</text>
      </view>
    </view>

    <!-- 注册表单 -->
    <view class="form-section" v-else>
      <!-- 第一步：账号信息 -->
      <view v-if="registerStep === 1">
        <view class="step-title">第1步：账号信息</view>
        <view class="input-group">
          <uni-easyinput
            v-model="registerForm.email"
            placeholder="请输入邮箱"
            prefixIcon="email"
          />
        </view>
        <view class="input-group code-row">
          <view class="code-input">
            <uni-easyinput
              v-model="registerForm.code"
              placeholder="请输入验证码"
              prefixIcon="locked"
              type="number"
              :maxlength="6"
            />
          </view>
          <button
            class="btn-code"
            :disabled="codeCooldown > 0 || !registerForm.email"
            @click="handleSendCode"
          >
            {{ codeCooldown > 0 ? codeCooldown + 's' : '获取验证码' }}
          </button>
        </view>
        <view class="input-group">
          <uni-easyinput
            v-model="registerForm.password"
            type="password"
            placeholder="请输入密码（至少6位）"
            prefixIcon="locked"
          />
        </view>
        <view class="input-group">
          <uni-easyinput
            v-model="registerForm.confirmPassword"
            type="password"
            placeholder="请确认密码"
            prefixIcon="locked"
          />
        </view>
        <button class="btn-primary" @click="nextStep">下一步</button>
      </view>

      <!-- 第二步：身体档案 -->
      <view v-if="registerStep === 2">
        <view class="step-title">第2步：身体档案</view>
        
        <view class="input-group">
          <view class="label">性别</view>
          <radio-group @change="onGenderChange" class="radio-group">
            <label class="radio-item" v-for="item in genderOptions" :key="item.value">
              <radio :value="String(item.value)" :checked="registerForm.gender === item.value" />
              <text>{{ item.label }}</text>
            </label>
          </radio-group>
        </view>

        <view class="input-group">
          <view class="label">出生日期</view>
          <picker mode="date" :value="registerForm.birthday" @change="onBirthdayChange" :end="maxBirthday">
            <view class="picker-value">
              {{ registerForm.birthday || '请选择出生日期' }}
            </view>
          </picker>
        </view>

        <view class="input-group row">
          <view class="half">
            <view class="label">身高(cm)</view>
            <uni-easyinput v-model="registerForm.height_cm" type="number" placeholder="身高" />
          </view>
          <view class="half">
            <view class="label">体重(kg)</view>
            <uni-easyinput v-model="registerForm.weight_kg" type="digit" placeholder="体重" />
          </view>
        </view>

        <view class="input-group">
          <view class="label">活动水平</view>
          <radio-group @change="onActivityChange" class="radio-group vertical">
            <label class="radio-item" v-for="item in activityOptions" :key="item.value">
              <radio :value="String(item.value)" :checked="registerForm.activity_level === item.value" />
              <text>{{ item.label }}</text>
            </label>
          </radio-group>
        </view>

        <view class="input-group">
          <view class="label">健康目标</view>
          <radio-group @change="onGoalChange" class="radio-group">
            <label class="radio-item" v-for="item in goalOptions" :key="item.value">
              <radio :value="String(item.value)" :checked="registerForm.health_goal === item.value" />
              <text>{{ item.label }}</text>
            </label>
          </radio-group>
        </view>

        <view class="input-group">
          <view class="label">热量系数</view>
          <view class="coefficient-section">
            <view class="coefficient-input-row">
              <uni-easyinput
                v-model="registerForm.calorie_coefficient"
                type="digit"
                placeholder="请输入热量系数"
              />
              <text class="coefficient-default">默认 {{ defaultCalorieCoefficientText }}</text>
            </view>
            <text class="coefficient-tip">维持 1.00 / 减脂 0.85 / 增肌 1.15，可手动调整</text>
          </view>
        </view>

        <view class="input-group">
          <view class="label">预计每日热量</view>
          <view class="calorie-preview-card" :class="{ muted: !dailyCaloriePreview }">
            <text class="preview-value">{{ dailyCaloriePreviewText }}</text>
            <text class="preview-unit" v-if="dailyCaloriePreview">kcal/天</text>
            <text class="preview-hint">{{ dailyCaloriePreviewHint }}</text>
          </view>
        </view>

        <!-- 营养素比例 -->
        <view class="input-group">
          <view class="label">营养素比例（可选）</view>
          <view class="nutrient-ratio-section">
            <view class="ratio-item">
              <text class="ratio-label">蛋白质</text>
              <slider 
                :value="registerForm.protein_ratio * 100" 
                @changing="onProteinChange"
                @change="onProteinChange"
                min="5" 
                max="50" 
                block-size="20"
              />
              <text class="ratio-value">{{ formatRatioValue(registerForm.protein_ratio) }}%</text>
            </view>
            <view class="ratio-item">
              <text class="ratio-label">脂肪</text>
              <slider 
                :value="registerForm.fat_ratio * 100" 
                @changing="onFatChange"
                @change="onFatChange"
                min="10" 
                max="45" 
                block-size="20"
              />
              <text class="ratio-value">{{ formatRatioValue(registerForm.fat_ratio) }}%</text>
            </view>
            <view class="ratio-item">
              <text class="ratio-label">碳水</text>
              <slider 
                :value="registerForm.carb_ratio * 100" 
                @changing="onCarbChange"
                @change="onCarbChange"
                min="20" 
                max="70" 
                block-size="20"
              />
              <text class="ratio-value">{{ formatRatioValue(registerForm.carb_ratio) }}%</text>
            </view>
            <view class="ratio-total" :class="{ warning: !isRatioValid }">
              总计: {{ Math.round((registerForm.protein_ratio + registerForm.fat_ratio + registerForm.carb_ratio) * 100) }}%
              <text v-if="!isRatioValid">（应为100%）</text>
            </view>
          </view>
        </view>

        <view class="btn-row">
          <button class="btn-secondary" @click="registerStep = 1">上一步</button>
          <button class="btn-primary" @click="handleRegister" :loading="loading">完成注册</button>
        </view>
      </view>

      <view class="switch-tip">
        <text>已有账号？</text>
        <text class="link" @click="isRegister = false; registerStep = 1">立即登录</text>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, computed } from 'vue'
import { login, register, sendCode } from '@/api/auth'
import { useUserStore } from '@/store/user'
import {
  calculateAgeFromBirthday,
  calculateBMR,
  calculateDailyCalorie,
  getDefaultCalorieCoefficient
} from '@/utils/nutrition'

const userStore = useUserStore()
const loading = ref(false)
const isRegister = ref(false)
const registerStep = ref(1)
const codeCooldown = ref(0)  // 验证码发送冷却倒计时（秒）

// 登录表单
const loginForm = ref({
  account: '',
  password: ''
})

// 注册表单
const registerForm = ref({
  email: '',
  code: '',
  password: '',
  confirmPassword: '',
  gender: 0,
  birthday: '',
  height_cm: '',
  weight_kg: '',
  activity_level: 2,
  health_goal: 1,
  calorie_coefficient: '1.00',
  protein_ratio: 0.20,
  fat_ratio: 0.25,
  carb_ratio: 0.55
})

// 默认营养素比例
const defaultNutrientRatios = {
  1: { protein: 0.20, fat: 0.25, carb: 0.55 }, // 维持
  2: { protein: 0.30, fat: 0.25, carb: 0.45 }, // 减脂
  3: { protein: 0.25, fat: 0.20, carb: 0.55 }  // 增肌
}

// 选项配置
const genderOptions = [
  { value: 0, label: '男' },
  { value: 1, label: '女' }
]

const activityOptions = [
  { value: 1, label: '久坐（几乎不运动）' },
  { value: 2, label: '轻度活动（每周1-3次）' },
  { value: 3, label: '中度活动（每周3-5次）' },
  { value: 4, label: '高强度（每周6-7次）' }
]

const goalOptions = [
  { value: 1, label: '维持体重' },
  { value: 2, label: '减脂' },
  { value: 3, label: '增肌' }
]

const coefficientLimits = {
  min: 0.5,
  max: 2
}

// 出生日期最大值（年满12岁）
const maxBirthday = computed(() => {
  const d = new Date()
  d.setFullYear(d.getFullYear() - 12)
  return d.toISOString().split('T')[0]
})

// 营养素比例是否有效
const isRatioValid = computed(() => {
  const total = registerForm.value.protein_ratio + registerForm.value.fat_ratio + registerForm.value.carb_ratio
  return Math.abs(total - 1) < 0.01 // 允许0.01的误差
})

const defaultCalorieCoefficient = computed(() => {
  return getDefaultCalorieCoefficient(registerForm.value.health_goal)
})

const defaultCalorieCoefficientText = computed(() => {
  return defaultCalorieCoefficient.value.toFixed(2)
})

const calorieCoefficientNumber = computed(() => {
  const coefficient = Number(registerForm.value.calorie_coefficient)
  return Number.isFinite(coefficient) ? coefficient : NaN
})

const dailyCaloriePreview = computed(() => {
  const age = calculateAgeFromBirthday(registerForm.value.birthday)
  const heightCm = Number(registerForm.value.height_cm)
  const weightKg = Number(registerForm.value.weight_kg)
  const coefficient = calorieCoefficientNumber.value

  if (!age || age < 12) return 0
  if (!Number.isFinite(heightCm) || heightCm < 100 || heightCm > 250) return 0
  if (!Number.isFinite(weightKg) || weightKg < 30 || weightKg > 300) return 0
  if (!Number.isFinite(coefficient) || coefficient <= 0) return 0

  const bmr = calculateBMR(weightKg, heightCm, age, registerForm.value.gender)
  return calculateDailyCalorie(
    bmr,
    registerForm.value.activity_level,
    registerForm.value.health_goal,
    coefficient
  )
})

const dailyCaloriePreviewText = computed(() => {
  return dailyCaloriePreview.value ? String(dailyCaloriePreview.value) : '待完善身体信息后自动预估'
})

const dailyCaloriePreviewHint = computed(() => {
  if (!registerForm.value.birthday) return '请选择出生日期以计算年龄'

  const coefficient = calorieCoefficientNumber.value
  if (!Number.isFinite(coefficient) || coefficient <= 0) {
    return '请输入大于 0 的热量系数'
  }

  if (!dailyCaloriePreview.value) {
    return '补全身高、体重、活动水平后可查看预估结果'
  }

  return `按当前身体信息、活动水平与系数 ${coefficient.toFixed(2)} 实时计算`
})

// 事件处理
const onGenderChange = (e) => {
  registerForm.value.gender = parseInt(e.detail.value)
}

const onBirthdayChange = (e) => {
  registerForm.value.birthday = e.detail.value
}

const onActivityChange = (e) => {
  registerForm.value.activity_level = parseInt(e.detail.value)
}

const onProteinChange = (e) => {
  registerForm.value.protein_ratio = Math.round(e.detail.value) / 100
}

const onFatChange = (e) => {
  registerForm.value.fat_ratio = Math.round(e.detail.value) / 100
}

const onCarbChange = (e) => {
  registerForm.value.carb_ratio = Math.round(e.detail.value) / 100
}

const formatRatioValue = (ratio) => {
  return Math.round(ratio * 100)
}

const onGoalChange = (e) => {
  const goal = parseInt(e.detail.value)
  registerForm.value.health_goal = goal
  registerForm.value.calorie_coefficient = getDefaultCalorieCoefficient(goal).toFixed(2)
  // 自动更新为对应的营养素比例
  const ratios = defaultNutrientRatios[goal]
  registerForm.value.protein_ratio = ratios.protein
  registerForm.value.fat_ratio = ratios.fat
  registerForm.value.carb_ratio = ratios.carb
}

// 下一步
const nextStep = () => {
  const { email, code, password, confirmPassword } = registerForm.value
  
  if (!email) {
    return uni.showToast({ title: '请输入邮箱', icon: 'none' })
  }
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    return uni.showToast({ title: '邮箱格式不正确', icon: 'none' })
  }
  if (!code) {
    return uni.showToast({ title: '请输入验证码', icon: 'none' })
  }
  if (!password || password.length < 6) {
    return uni.showToast({ title: '密码至少6位', icon: 'none' })
  }
  if (password !== confirmPassword) {
    return uni.showToast({ title: '两次密码不一致', icon: 'none' })
  }
  
  registerStep.value = 2
}

// 发送验证码
const handleSendCode = async () => {
  const email = registerForm.value.email.trim()
  if (!email) {
    return uni.showToast({ title: '请先输入邮箱', icon: 'none' })
  }
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    return uni.showToast({ title: '邮箱格式不正确', icon: 'none' })
  }

  try {
    await sendCode({ email })
    uni.showToast({ title: '验证码已发送', icon: 'success' })
    // 启动60秒冷却
    codeCooldown.value = 60
    const timer = setInterval(() => {
      codeCooldown.value--
      if (codeCooldown.value <= 0) {
        clearInterval(timer)
      }
    }, 1000)
  } catch (error) {
    console.error('发送验证码失败:', error)
  }
}

// 登录
const handleLogin = async () => {
  const { account, password } = loginForm.value
  
  if (!account) {
    return uni.showToast({ title: '请输入手机号/邮箱', icon: 'none' })
  }
  if (!password) {
    return uni.showToast({ title: '请输入密码', icon: 'none' })
  }
  
  loading.value = true
  try {
    const data = await login({ account, password })
    
    // 保存Token和用户信息
    userStore.setToken(data.token)
    userStore.setUserInfo(data.user)
    
    uni.showToast({ title: '登录成功', icon: 'success' })
    setTimeout(() => {
      uni.switchTab({ url: '/pages/index/index' })
    }, 1500)
  } catch (error) {
    console.error('登录失败:', error)
  } finally {
    loading.value = false
  }
}

// 注册
const handleRegister = async () => {
  const form = registerForm.value
  
  if (!form.birthday) {
    return uni.showToast({ title: '请选择出生日期', icon: 'none' })
  }
  if (!form.height_cm || form.height_cm < 100 || form.height_cm > 250) {
    return uni.showToast({ title: '请输入正确的身高(100-250cm)', icon: 'none' })
  }
  if (!form.weight_kg || form.weight_kg < 30 || form.weight_kg > 300) {
    return uni.showToast({ title: '请输入正确的体重(30-300kg)', icon: 'none' })
  }
  const calorieCoefficient = Number(form.calorie_coefficient)
  if (!Number.isFinite(calorieCoefficient) || calorieCoefficient <= 0) {
    return uni.showToast({ title: '请输入正确的热量系数', icon: 'none' })
  }
  if (calorieCoefficient < coefficientLimits.min || calorieCoefficient > coefficientLimits.max) {
    return uni.showToast({ title: '热量系数需在0.50-2.00之间', icon: 'none' })
  }
  if (!isRatioValid.value) {
    return uni.showToast({ title: '营养素比例总计应为100%', icon: 'none' })
  }
  
  loading.value = true
  try {
    const data = await register({
      email: form.email,
      code: form.code,
      password: form.password,
      gender: form.gender,
      birthday: form.birthday,
      height_cm: parseInt(form.height_cm),
      weight_kg: parseFloat(form.weight_kg),
      activity_level: form.activity_level,
      health_goal: form.health_goal,
      calorie_coefficient: parseFloat(calorieCoefficient.toFixed(2)),
      protein_ratio: form.protein_ratio,
      fat_ratio: form.fat_ratio,
      carb_ratio: form.carb_ratio
    })
    
    // 保存Token和用户信息
    userStore.setToken(data.token)
    userStore.setUserInfo(data.user)
    
    uni.showToast({ title: '注册成功', icon: 'success' })
    setTimeout(() => {
      uni.switchTab({ url: '/pages/index/index' })
    }, 1500)
  } catch (error) {
    console.error('注册失败:', error)
  } finally {
    loading.value = false
  }
}
</script>

<style lang="scss" scoped>
.login-container {
  height: 100vh;
  overflow-y: auto;
  padding: 60rpx 40rpx;
  background: linear-gradient(180deg, #e8f5e9 0%, #fff 100%);
}

.logo-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40rpx 0 60rpx;
  
  .logo {
    width: 160rpx;
    height: 160rpx;
    margin-bottom: 20rpx;
  }
  
  .app-name {
    font-size: 44rpx;
    font-weight: bold;
    color: #2e7d32;
    margin-bottom: 10rpx;
  }
  
  .app-desc {
    font-size: 28rpx;
    color: #666;
  }
}

.form-section {
  background: #fff;
  border-radius: 24rpx;
  padding: 40rpx;
  box-shadow: 0 4rpx 20rpx rgba(0,0,0,0.05);
}

.step-title {
  font-size: 32rpx;
  font-weight: bold;
  color: #333;
  margin-bottom: 30rpx;
  text-align: center;
}

.input-group {
  margin-bottom: 30rpx;
  
  &.row {
    display: flex;
    gap: 20rpx;
    
    .half {
      flex: 1;
    }
  }
  
  .label {
    font-size: 28rpx;
    color: #333;
    margin-bottom: 12rpx;
  }
}

.radio-group {
  display: flex;
  flex-wrap: wrap;
  gap: 20rpx;
  
  &.vertical {
    flex-direction: column;
  }
  
  .radio-item {
    display: flex;
    align-items: center;
    font-size: 28rpx;
    color: #333;
    
    radio {
      transform: scale(0.8);
    }
  }
}

.picker-value {
  padding: 20rpx;
  background: #f5f5f5;
  border-radius: 8rpx;
  font-size: 28rpx;
  color: #333;
}

.coefficient-section {
  background: #f9f9f9;
  border-radius: 12rpx;
  padding: 20rpx;

  .coefficient-input-row {
    display: flex;
    align-items: center;
    gap: 16rpx;
  }

  .coefficient-default {
    flex-shrink: 0;
    font-size: 24rpx;
    color: #4caf50;
    font-weight: 500;
  }

  .coefficient-tip {
    display: block;
    margin-top: 12rpx;
    font-size: 24rpx;
    line-height: 1.6;
    color: #666;
  }
}

.calorie-preview-card {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  padding: 24rpx;
  background: #e8f5e9;
  border-radius: 12rpx;

  &.muted {
    background: #f5f5f5;

    .preview-value,
    .preview-unit {
      color: #999;
    }
  }

  .preview-value {
    font-size: 38rpx;
    line-height: 1.1;
    color: #2e7d32;
    font-weight: bold;
  }

  .preview-unit {
    margin-top: 8rpx;
    font-size: 24rpx;
    color: #4caf50;
  }

  .preview-hint {
    margin-top: 12rpx;
    font-size: 24rpx;
    line-height: 1.6;
    color: #666;
  }
}

.btn-primary {
  width: 100%;
  height: 88rpx;
  line-height: 88rpx;
  background: #4caf50;
  color: #fff;
  font-size: 32rpx;
  border-radius: 44rpx;
  border: none;
  margin-top: 20rpx;
  
  &:active {
    background: #388e3c;
  }
}

.btn-secondary {
  flex: 1;
  height: 88rpx;
  line-height: 88rpx;
  background: #f5f5f5;
  color: #666;
  font-size: 32rpx;
  border-radius: 44rpx;
  border: none;
}

.btn-row {
  display: flex;
  gap: 20rpx;
  margin-top: 20rpx;
  
  .btn-primary {
    flex: 1;
    margin-top: 0;
  }
}

.code-row {
  display: flex;
  gap: 16rpx;
  align-items: flex-start;

  .code-input {
    flex: 1;
  }

  .btn-code {
    height: 74rpx;
    padding: 0 28rpx;
    font-size: 26rpx;
    color: #fff;
    background: #4caf50;
    border: none;
    border-radius: 12rpx;
    white-space: nowrap;
    line-height: 74rpx;
  }
}

.switch-tip {
  text-align: center;
  margin-top: 30rpx;
  font-size: 28rpx;
  color: #666;
  
  .link {
    color: #4caf50;
    margin-left: 10rpx;
  }
}

// 营养素比例样式
.nutrient-ratio-section {
  background: #f9f9f9;
  border-radius: 12rpx;
  padding: 20rpx;
  
  .ratio-item {
    display: flex;
    align-items: center;
    margin-bottom: 16rpx;
    
    &:last-child {
      margin-bottom: 0;
    }
    
    .ratio-label {
      width: 100rpx;
      font-size: 26rpx;
      color: #666;
    }
    
    slider {
      flex: 1;
    }
    
    .ratio-value {
      width: 80rpx;
      text-align: right;
      font-size: 26rpx;
      color: #333;
      font-weight: 500;
    }
  }
  
  .ratio-total {
    text-align: center;
    font-size: 26rpx;
    color: #4caf50;
    margin-top: 16rpx;
    padding-top: 16rpx;
    border-top: 1rpx solid #e0e0e0;
    
    &.warning {
      color: #f44336;
    }
    
    text {
      margin-left: 10rpx;
      font-size: 24rpx;
    }
  }
}
</style>
