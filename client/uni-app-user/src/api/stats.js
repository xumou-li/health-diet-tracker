/**
 * 营养统计API
 */
import { get } from './request'

/**
 * 今日汇总（热量、营养素、评分）
 */
export const getTodayStats = () => {
  return get('/api/stats/today')
}

/**
 * 最近7天统计
 */
export const getWeekStats = () => {
  return get('/api/stats/week')
}

/**
 * 最近30天统计
 */
export const getMonthStats = () => {
  return get('/api/stats/month')
}

/**
 * 营养素雷达图数据
 */
export const getNutrientsRadar = () => {
  return get('/api/stats/nutrients-radar')
}

/**
 * 体重变化趋势
 * @param {Object} params - 查询参数
 * @param {number} params.days - 天数
 */
export const getWeightTrend = (params) => {
  return get('/api/stats/weight-trend', params)
}

/**
 * 热量分析与反馈
 * @param {string} date - 日期，格式 YYYY-MM-DD，默认今天
 */
export const getAnalysis = (date) => {
  return get('/api/stats/analysis', date ? { date } : {})
}

export default {
  getTodayStats,
  getWeekStats,
  getMonthStats,
  getNutrientsRadar,
  getWeightTrend,
  getAnalysis
}
