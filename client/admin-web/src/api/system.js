import { get, put } from '@/utils/request'

export function getSystemConfig() {
  return get('/config')
}

export function updateSystemConfig(data) {
  return put('/config', data)
}
