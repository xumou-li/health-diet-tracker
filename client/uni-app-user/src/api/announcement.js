/**
 * 系统公告 API
 */
import { get } from './request'

/**
 * 获取系统公告（无需登录）
 */
export function getAnnouncement() {
  return get('/api/auth/announcement').then(res => res.announcement || '')
}
