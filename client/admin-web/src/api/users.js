import { get, put } from '@/utils/request'

export function getUsers(params) {
  return get('/users', params)
}

export function getUserDetail(user_id) {
  return get(`/users/${user_id}`)
}

export function toggleFreezeUser(user_id) {
  return put(`/users/${user_id}/freeze`)
}
