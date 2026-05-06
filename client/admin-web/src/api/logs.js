import { get } from '@/utils/request'

export function getAdminLogs(params) {
  return get('/logs', params)
}
