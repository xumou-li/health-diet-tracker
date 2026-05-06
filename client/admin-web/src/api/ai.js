import { get } from '@/utils/request'

export function getAIStats() {
  return get('/stats/ai')
}
