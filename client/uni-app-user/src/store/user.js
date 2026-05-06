/**
 * 用户状态管理
 */
import { defineStore } from 'pinia'
import { getProfile, updateProfile } from '@/api/user'

export const useUserStore = defineStore('user', {
  state: () => ({
    // 用户信息
    userInfo: null,
    // 登录Token
    token: uni.getStorageSync('token') || '',
    // 身体档案
    profile: null
  }),

  getters: {
    // 是否已登录
    isLoggedIn: (state) => !!state.token,
    
    // BMI状态文字
    bmiStatus: (state) => {
      if (!state.profile) return ''
      const bmi = state.profile.bmi
      if (bmi < 18.5) return '偏瘦'
      if (bmi < 24) return '正常'
      if (bmi < 28) return '超重'
      return '肥胖'
    },

    // 健康目标文字
    healthGoalText: (state) => {
      if (!state.profile) return ''
      const goals = { 1: '维持体重', 2: '减脂', 3: '增肌' }
      return goals[state.profile.health_goal] || ''
    },

    // 活动水平文字
    activityLevelText: (state) => {
      if (!state.profile) return ''
      const levels = { 1: '久坐', 2: '轻度活动', 3: '中度活动', 4: '高强度活动' }
      return levels[state.profile.activity_level] || ''
    }
  },

  actions: {
    // 设置Token
    setToken(token) {
      this.token = token
      uni.setStorageSync('token', token)
    },

    // 清除Token
    clearToken() {
      this.token = ''
      this.userInfo = null
      this.profile = null
      uni.removeStorageSync('token')
      uni.removeStorageSync('userInfo')
    },

    // 设置用户信息
    setUserInfo(userInfo) {
      this.userInfo = userInfo
      uni.setStorageSync('userInfo', JSON.stringify(userInfo))
    },

    // 获取用户档案
    async fetchProfile() {
      try {
        const data = await getProfile()
        this.profile = data
        this.userInfo = data
        return data
      } catch (error) {
        console.error('获取用户档案失败:', error)
        throw error
      }
    },

    // 更新用户档案
    async updateUserProfile(data) {
      try {
        const result = await updateProfile(data)
        // 更新本地数据
        this.profile = { ...this.profile, ...result }
        return result
      } catch (error) {
        console.error('更新用户档案失败:', error)
        throw error
      }
    },

    // 退出登录
    logout() {
      this.clearToken()
      uni.reLaunch({ url: '/pages/login/login' })
    },

    // 初始化用户状态（从本地存储恢复）
    initFromStorage() {
      const token = uni.getStorageSync('token')
      const userInfo = uni.getStorageSync('userInfo')
      
      if (token) {
        this.token = token
      } else {
        this.token = ''
        this.userInfo = null
        this.profile = null
      }
      if (userInfo) {
        try {
          this.userInfo = JSON.parse(userInfo)
        } catch (e) {
          console.error('解析用户信息失败:', e)
        }
      }
    }
  }
})
