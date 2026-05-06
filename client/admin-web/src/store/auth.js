import { defineStore } from 'pinia'
import {
  clearAdminAuth,
  getAdminToken,
  getAdminUser,
  setAdminToken,
  setAdminUser
} from '@/utils/storage'

export const useAuthStore = defineStore('admin-auth', {
  state: () => ({
    token: getAdminToken(),
    user: getAdminUser()
  }),
  getters: {
    isAuthenticated: (state) => Boolean(state.token),
    adminName: (state) => state.user?.username || '管理员',
    adminRoleText: (state) => (state.user?.role === 2 ? '超级管理员' : '管理员')
  },
  actions: {
    hydrate() {
      this.token = getAdminToken()
      this.user = getAdminUser()
    },
    setAuth(payload) {
      this.token = payload?.token || ''
      this.user = payload?.admin || null
      setAdminToken(this.token)
      setAdminUser(this.user)
    },
    setUser(user) {
      this.user = user || null
      setAdminUser(this.user)
    },
    logout() {
      this.token = ''
      this.user = null
      clearAdminAuth()
    }
  }
})
