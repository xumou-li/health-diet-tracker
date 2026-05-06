import { del, get, post, put } from '@/utils/request'

export function getFoods(params) {
  return get('/foods', params)
}

export function createFood(data) {
  return post('/foods', data)
}

export function updateFood(food_id, data) {
  return put(`/foods/${food_id}`, data)
}

export function deleteFood(food_id) {
  return del(`/foods/${food_id}`)
}

export function approveFood(food_id) {
  return put(`/foods/${food_id}/approve`)
}
