import { get } from '@/utils/request'

export function getDashboard() {
  return get('/dashboard')
}
