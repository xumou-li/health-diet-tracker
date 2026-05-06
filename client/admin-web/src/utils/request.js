import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'
import { clearAdminAuth, getAdminToken } from '@/utils/storage'

const service = axios.create({
  baseURL: '/api/admin',
  timeout: 15000
})

function redirectToLogin() {
  const currentRoute = router.currentRoute.value
  const currentName = currentRoute?.name

  if (currentName === 'login' || currentName === 'init-admin') {
    return
  }

  router.push({
    name: 'login',
    query: {
      redirect: currentRoute?.fullPath || '/dashboard'
    }
  })
}

service.interceptors.request.use(
  (config) => {
    const token = getAdminToken()

    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }

    return config
  },
  (error) => Promise.reject(error)
)

service.interceptors.response.use(
  (response) => {
    const payload = response.data

    if (payload && typeof payload.code !== 'undefined') {
      if (payload.code === 200) {
        return payload.data
      }

      ElMessage.error(payload.message || '请求失败')
      return Promise.reject(payload)
    }

    return payload
  },
  (error) => {
    const status = error.response?.status
    const payload = error.response?.data
    const message = payload?.message || error.message || '请求失败'

    if (status === 401) {
      clearAdminAuth()
      ElMessage.error('登录状态已失效，请重新登录')
      redirectToLogin()
      return Promise.reject(payload || error)
    }

    ElMessage.error(message)
    return Promise.reject(payload || error)
  }
)

export function request(config) {
  return service(config)
}

export function get(url, params, config = {}) {
  return service({
    url,
    method: 'get',
    params,
    ...config
  })
}

export function post(url, data, config = {}) {
  return service({
    url,
    method: 'post',
    data,
    ...config
  })
}

export function put(url, data, config = {}) {
  return service({
    url,
    method: 'put',
    data,
    ...config
  })
}

export function del(url, data, config = {}) {
  return service({
    url,
    method: 'delete',
    data,
    ...config
  })
}

export default service
