/**
 * 食物库API
 */
import { get, post, del } from './request'

/**
 * 搜索食物
 * @param {Object} params - 搜索参数
 * @param {string} params.keyword - 关键词
 * @param {string} params.category_code - 分类编码
 * @param {number} params.page - 页码
 * @param {number} params.limit - 每页数量
 */
export const searchFoods = (params) => {
  return get('/api/foods', params)
}

/**
 * 获取食物详情
 * @param {number} id - 食物ID
 */
export const getFoodDetail = (id) => {
  return get(`/api/foods/${id}`)
}

/**
 * 获取相似低热量食物
 * @param {number} id - 食物ID
 */
export const getFoodAlternatives = (id) => {
  return get(`/api/foods/${id}/alternatives`)
}

/**
 * 获取热门食物排行
 * @param {number} limit - 数量限制
 */
export const getPopularFoods = (limit = 10) => {
  return get('/api/foods/popular', { limit })
}

/**
 * 获取分类树
 */
export const getCategories = () => {
  return get('/api/food-categories')
}

/**
 * 收藏食物
 * @param {number} foodId - 食物ID
 */
export const addFavorite = (foodId) => {
  return post('/api/favorites', { food_id: foodId })
}

/**
 * 取消收藏
 * @param {number} foodId - 食物ID
 */
export const removeFavorite = (foodId) => {
  return del(`/api/favorites/${foodId}`)
}

/**
 * 获取收藏列表
 * @param {Object} params - 查询参数
 * @param {number} params.page - 页码
 * @param {number} params.limit - 每页数量
 */
export const getFavorites = (params) => {
  return get('/api/favorites', params)
}

export default {
  searchFoods,
  getFoodDetail,
  getFoodAlternatives,
  getPopularFoods,
  getCategories,
  addFavorite,
  removeFavorite,
  getFavorites
}
