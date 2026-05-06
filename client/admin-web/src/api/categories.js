import { get, post, put } from '@/utils/request'

export function getCategories() {
  return get('/categories')
}

export function createCategory(data) {
  return post('/categories', data)
}

export function updateCategory(category_id, data) {
  return put(`/categories/${category_id}`, data)
}
