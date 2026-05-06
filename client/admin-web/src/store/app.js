import { defineStore } from 'pinia'

const SIDEBAR_COLLAPSED_KEY = 'admin_sidebar_collapsed'

function getStoredSidebarState() {
  return window.localStorage.getItem(SIDEBAR_COLLAPSED_KEY) === '1'
}

export const useAppStore = defineStore('admin-app', {
  state: () => ({
    sidebarCollapsed: getStoredSidebarState()
  }),
  actions: {
    setSidebarCollapsed(value) {
      this.sidebarCollapsed = Boolean(value)
      window.localStorage.setItem(SIDEBAR_COLLAPSED_KEY, this.sidebarCollapsed ? '1' : '0')
    },
    toggleSidebar() {
      this.setSidebarCollapsed(!this.sidebarCollapsed)
    }
  }
})
