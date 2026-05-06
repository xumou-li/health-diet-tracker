/**
 * 本地存储工具封装
 */

/**
 * 设置缓存
 * @param {string} key - 键名
 * @param {any} value - 值
 * @param {number} expireTime - 过期时间(毫秒)，不传则永不过期
 */
export const setStorage = (key, value, expireTime) => {
  const data = {
    value,
    time: Date.now(),
    expire: expireTime
  }
  uni.setStorageSync(key, JSON.stringify(data))
}

/**
 * 获取缓存
 * @param {string} key - 键名
 * @returns {any} 值，过期或不存在返回null
 */
export const getStorage = (key) => {
  try {
    const dataStr = uni.getStorageSync(key)
    if (!dataStr) return null

    const data = JSON.parse(dataStr)
    
    // 检查是否过期
    if (data.expire && Date.now() - data.time > data.expire) {
      removeStorage(key)
      return null
    }
    
    return data.value
  } catch (e) {
    console.error('获取缓存失败:', e)
    return null
  }
}

/**
 * 移除缓存
 * @param {string} key - 键名
 */
export const removeStorage = (key) => {
  uni.removeStorageSync(key)
}

/**
 * 清空所有缓存
 */
export const clearStorage = () => {
  uni.clearStorageSync()
}

/**
 * 设置Token
 * @param {string} token - Token值
 */
export const setToken = (token) => {
  uni.setStorageSync('token', token)
}

/**
 * 获取Token
 * @returns {string} Token值
 */
export const getToken = () => {
  return uni.getStorageSync('token') || ''
}

/**
 * 移除Token
 */
export const removeToken = () => {
  uni.removeStorageSync('token')
}

/**
 * 检查是否已登录
 * @returns {boolean}
 */
export const isLoggedIn = () => {
  return !!getToken()
}

export default {
  setStorage,
  getStorage,
  removeStorage,
  clearStorage,
  setToken,
  getToken,
  removeToken,
  isLoggedIn
}
