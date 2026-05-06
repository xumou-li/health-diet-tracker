/**
 * 饮食记录API
 */
import { get, post, put, del } from './request'

/**
 * 新增饮食记录
 * @param {Object} data - 饮食记录
 * @param {number} data.food_id - 食物ID
 * @param {string} data.date - 日期 YYYY-MM-DD
 * @param {number} data.meal_type - 餐次 1=早餐,2=午餐,3=晚餐,4=加餐
 * @param {number} data.weight_g - 重量(克)
 */
export const addMeal = (data) => {
  return post('/api/meals', data)
}

/**
 * 批量新增饮食记录（食谱一键添加）
 * @param {Object} data - 批量记录
 * @param {string} data.date - 日期 YYYY-MM-DD
 * @param {number} data.meal_type - 餐次
 * @param {Array} data.items - 食物列表 [{food_id, weight_g}]
 */
export const batchAddMeals = (data) => {
  return post('/api/meals/batch', data)
}

/**
 * 获取指定日期的饮食记录
 * @param {string} date - 日期 YYYY-MM-DD
 */
export const getMealsByDate = (date) => {
  return get('/api/meals', { date })
}

/**
 * 修改饮食记录
 * @param {number} id - 记录ID
 * @param {Object} data - 修改数据
 * @param {number} data.weight_g - 重量(克)
 * @param {number} data.meal_type - 餐次
 */
export const updateMeal = (id, data) => {
  return put(`/api/meals/${id}`, data)
}

/**
 * 删除饮食记录
 * @param {number} id - 记录ID
 */
export const deleteMeal = (id) => {
  return del(`/api/meals/${id}`)
}

/**
 * 复制某天某餐到今天
 * @param {Object} data - 复制信息
 * @param {string} data.source_date - 源日期
 * @param {number} data.source_meal_type - 源餐次
 * @param {string} data.target_date - 目标日期
 * @param {number} data.target_meal_type - 目标餐次
 */
export const copyMeal = (data) => {
  return post('/api/meals/copy', data)
}

export default {
  addMeal,
  batchAddMeals,
  getMealsByDate,
  updateMeal,
  deleteMeal,
  copyMeal
}
