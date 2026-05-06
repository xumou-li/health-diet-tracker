/**
 * AI助手API
 */
import { get, del } from './request'

/**
 * AI问答（流式）
 * 返回原生 Response 对象，由调用方通过 ReadableStream 读取
 * @param {Object} data - 问答数据
 * @param {string} data.question - 用户问题
 */
export const chatStream = async (data) => {
  const token = uni.getStorageSync('token')
  // H5 环境用空字符串 base URL（走 vite proxy）
  // #ifdef H5
  const baseUrl = ''
  // #endif
  // #ifndef H5
  const baseUrl = 'http://127.0.0.1:5000'
  // #endif

  const response = await fetch(baseUrl + '/api/ai/chat/stream', {
    method: 'POST',
    headers: {
      'Authorization': token ? `Bearer ${token}` : '',
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(data)
  })

  if (!response.ok) {
    const errData = await response.json().catch(() => ({}))
    throw new Error(errData.message || `请求失败 (${response.status})`)
  }

  return response
}

/**
 * 获取AI功能状态（开关、剩余次数）
 */
export const getStatus = () => {
  return get('/api/ai/status')
}

/**
 * 获取AI建议历史记录
 * @param {Object} params - 查询参数
 * @param {number} params.page - 页码
 * @param {number} params.limit - 每页数量
 */
export const getHistory = (params) => {
  return get('/api/ai/history', params)
}

/**
 * 清空AI历史记录
 * @param {Object} params - 查询参数
 * @param {string} params.type - 类型筛选
 */
export const clearHistory = (params) => {
  return del('/api/ai/history', params)
}

export default {
  chatStream,
  getStatus,
  getHistory,
  clearHistory
}
