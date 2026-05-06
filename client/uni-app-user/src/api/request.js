/**
 * 统一请求封装
 * 后端响应格式: { code: 200, message: "success", data: {...} }
 */
// #ifdef H5
export const BASE_URL = ''
// #endif
// #ifndef H5
export const BASE_URL = 'http://127.0.0.1:5000'
// #endif

/**
 * 封装uni.request为Promise
 * @param {Object} options - 请求配置
 * @param {string} options.url - 请求路径
 * @param {string} options.method - 请求方法
 * @param {Object} options.data - 请求数据
 * @param {boolean} options.showLoading - 是否显示loading
 * @param {boolean} options.showError - 是否显示错误提示
 */
export const request = (options) => {
  const {
    url,
    method = 'GET',
    data,
    showLoading = false,
    showError = true
  } = options

  return new Promise((resolve, reject) => {
    if (showLoading) {
      uni.showLoading({ title: '加载中...' })
    }

    const token = uni.getStorageSync('token')

    // 微信小程序需要显式序列化JSON，否则data可能不会被正确转为JSON字符串
    let requestData = data
    if (method === 'POST' || method === 'PUT' || method === 'PATCH' || method === 'DELETE') {
      if (data && typeof data === 'object') {
        requestData = JSON.stringify(data)
      }
    }

    uni.request({
      url: BASE_URL + url,
      method,
      data: requestData,
      timeout: 15000,
      header: {
        'Authorization': token ? `Bearer ${token}` : '',
        'Content-Type': 'application/json'
      },
      success: (res) => {
        if (showLoading) {
          uni.hideLoading()
        }

        const { statusCode, data: responseData } = res

        // HTTP 401 未授权，跳转登录
        if (statusCode === 401) {
          // 只有在确实有token的情况下才清除并跳转（避免首页加载时误触发）
          const currentToken = uni.getStorageSync('token')
          if (currentToken) {
            uni.removeStorageSync('token')
            uni.removeStorageSync('userInfo')
            uni.showToast({
              title: '登录已过期，请重新登录',
              icon: 'none'
            })
            setTimeout(() => {
              uni.reLaunch({ url: '/pages/login/login' })
            }, 1500)
          }
          reject(new Error('Unauthorized'))
          return
        }

        // HTTP请求成功，检查业务code
        if (statusCode >= 200 && statusCode < 300) {
          // 业务成功 code=200
          if (responseData.code === 200) {
            resolve(responseData.data)
          } else {
            // 业务失败
            if (showError) {
              uni.showToast({
                title: responseData.message || '操作失败',
                icon: 'none'
              })
            }
            reject(responseData)
          }
        } else {
          // HTTP错误
          if (showError) {
            uni.showToast({
              title: responseData?.message || '请求失败',
              icon: 'none'
            })
          }
          reject(responseData)
        }
      },
      fail: (err) => {
        if (showLoading) {
          uni.hideLoading()
        }
        if (showError) {
          uni.showToast({
            title: '网络错误，请检查网络连接',
            icon: 'none'
          })
        }
        reject(err)
      }
    })
  })
}

// 便捷方法
export const get = (url, data, options = {}) => {
  return request({ url, method: 'GET', data, ...options })
}

export const post = (url, data, options = {}) => {
  return request({ url, method: 'POST', data, ...options })
}

export const put = (url, data, options = {}) => {
  return request({ url, method: 'PUT', data, ...options })
}

export const del = (url, data, options = {}) => {
  return request({ url, method: 'DELETE', data, ...options })
}

export default {
  request,
  get,
  post,
  put,
  del,
  BASE_URL
}
