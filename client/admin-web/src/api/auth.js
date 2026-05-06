import { post } from '@/utils/request'

export function adminLogin(data) {
  return post('/auth/login', data)
}

export function initAdmin(data) {
  return post('/auth/init', data)
}
