/**
 * 用户与身体档案API
 */
import { get, put, post, BASE_URL } from './request'

/**
 * 获取用户信息+当前身体档案
 */
export const getProfile = () => {
  return get('/api/user/profile')
}

/**
 * 更新身体档案（触发BMI/BMR重算）
 * @param {Object} data - 身体档案信息
 * @param {number} data.height_cm - 身高(cm)
 * @param {number} data.weight_kg - 体重(kg)
 * @param {number} data.activity_level - 活动水平 1=久坐,2=轻度,3=中度,4=高强度
 * @param {number} data.gender - 性别 0=男,1=女,2=其他
 * @param {string} data.birthday - 出生日期 YYYY-MM-DD
 * @param {string} data.nickname - 昵称（可选）
 */
export const updateProfile = (data) => {
  return put('/api/user/profile', data, { showLoading: true })
}

/**
 * 更新健康目标
 * @param {Object} data - 健康目标
 * @param {number} data.health_goal - 1=维持,2=减脂,3=增肌
 */
export const updateHealthGoal = (data) => {
  return put('/api/user/health-goal', data)
}

/**
 * 更新饮食偏好
 * @param {Object} data - 饮食偏好
 * @param {string} data.diet_preference - 饮食偏好标签,逗号分隔
 */
export const updateDietPreference = (data) => {
  return put('/api/user/diet-preference', data)
}

/**
 * 获取身体记录历史
 * @param {Object} params - 查询参数
 * @param {number} params.page - 页码
 * @param {number} params.limit - 每页数量
 */
export const getBodyHistory = (params) => {
  return get('/api/user/body-history', params)
}

/**
 * 上传头像
 * @param {string} filePath - 本地文件路径（uni.chooseImage 返回的 tempFilePath）
 */
export const uploadAvatar = (filePath) => {
  return new Promise((resolve, reject) => {
    const token = uni.getStorageSync('token')
    uni.showLoading({ title: '上传中...' })

    uni.uploadFile({
      url: BASE_URL + '/api/user/avatar',
      filePath,
      name: 'file',
      header: {
        'Authorization': token ? `Bearer ${token}` : ''
      },
      success: (res) => {
        uni.hideLoading()
        try {
          const data = JSON.parse(res.data)
          if (data.code === 200) {
            resolve(data.data)
          } else {
            uni.showToast({ title: data.message || '上传失败', icon: 'none' })
            reject(data)
          }
        } catch (e) {
          uni.showToast({ title: '服务器响应异常', icon: 'none' })
          reject(e)
        }
      },
      fail: (err) => {
        uni.hideLoading()
        uni.showToast({ title: '网络错误，请检查网络连接', icon: 'none' })
        reject(err)
      }
    })
  })
}

/**
 * 发送修改密码验证码（到当前用户邮箱）
 */
export const sendChangePasswordCode = () => {
  return post('/api/user/send-change-password-code')
}

/**
 * 通过邮箱验证码修改密码
 * @param {Object} data
 * @param {string} data.code - 邮箱验证码
 * @param {string} data.new_password - 新密码
 */
export const changePassword = (data) => {
  return put('/api/user/change-password', data, { showLoading: true })
}

export default {
  getProfile,
  updateProfile,
  updateHealthGoal,
  updateDietPreference,
  getBodyHistory,
  uploadAvatar,
  sendChangePasswordCode,
  changePassword
}
