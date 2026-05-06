/**
 * 用户食谱（收藏）API
 */
import { get, post, put, del } from './request'

/**
 * 获取收藏列表
 */
export const getRecipes = () => {
  return get('/api/recipes')
}

/**
 * 创建收藏
 * @param {string} name - 收藏名称
 * @param {Array} items - 条目列表
 *   food:   { type: 'food', food_id, weight_g }
 *   custom: { type: 'custom', name, protein, fat, carb, calorie? }
 */
export const createRecipe = (data) => {
  return post('/api/recipes', data)
}

/**
 * 更新收藏
 * @param {number} id - 收藏ID
 * @param {Object} data - { name?, items? }
 */
export const updateRecipe = (id, data) => {
  return put(`/api/recipes/${id}`, data)
}

/**
 * 删除收藏
 * @param {number} id - 收藏ID
 */
export const deleteRecipe = (id) => {
  return del(`/api/recipes/${id}`)
}

export default {
  getRecipes,
  createRecipe,
  updateRecipe,
  deleteRecipe
}
