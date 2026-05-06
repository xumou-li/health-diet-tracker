/**
 * 认证相关API
 */
import { post } from './request'

/**
 * 用户注册
 * @param {Object} data - 注册信息
 * @param {string} data.email - 邮箱（与phone二选一，邮箱需验证码）
 * @param {string} data.code - 邮箱验证码（使用邮箱时必填）
 * @param {string} data.phone - 手机号
 * @param {string} data.password - 密码
 * @param {number} data.gender - 性别 0=男,1=女,2=其他
 * @param {string} data.birthday - 出生日期 YYYY-MM-DD
 * @param {number} data.height_cm - 身高(cm)
 * @param {number} data.weight_kg - 体重(kg)
 * @param {number} data.activity_level - 活动水平 1=久坐,2=轻度,3=中度,4=高强度
 * @param {number} data.health_goal - 健康目标 1=维持,2=减脂,3=增肌
 */
export const register = (data) => {
  return post('/api/auth/register', data, { showLoading: true })
}

/**
 * 用户登录
 * @param {Object} data - 登录信息
 * @param {string} data.phone - 手机号(与email二选一)
 * @param {string} data.email - 邮箱(与phone二选一)
 * @param {string} data.password - 密码
 */
export const login = (data) => {
  return post('/api/auth/login', data, { showLoading: true })
}

/**
 * 微信一键登录
 * @param {Object} data - 微信登录信息
 * @param {string} data.code - 微信授权code
 */
export const wechatLogin = (data) => {
  return post('/api/auth/wechat-login', data, { showLoading: true })
}

/**
 * 重置密码
 * @param {Object} data - 重置密码信息
 * @param {string} data.phone - 手机号
 * @param {string} data.code - 验证码
 * @param {string} data.new_password - 新密码
 */
export const resetPassword = (data) => {
  return post('/api/auth/reset-password', data, { showLoading: true })
}

/**
 * 发送邮箱验证码
 * @param {Object} data
 * @param {string} data.email - 邮箱
 */
export const sendCode = (data) => {
  return post('/api/auth/send-code', data, { showLoading: false })
}

export default {
  register,
  login,
  wechatLogin,
  resetPassword,
  sendCode
}
