/**
 * 营养计算工具函数
 */

/**
 * 计算BMI
 * @param {number} weightKg - 体重(kg)
 * @param {number} heightCm - 身高(cm)
 * @returns {number} BMI值
 */
export const calculateBMI = (weightKg, heightCm) => {
  const heightM = heightCm / 100
  return parseFloat((weightKg / (heightM * heightM)).toFixed(2))
}

/**
 * 获取BMI状态（中国标准）
 * @param {number} bmi - BMI值
 * @returns {object} { status, color, description }
 */
export const getBMIStatus = (bmi) => {
  if (bmi < 18.5) {
    return { status: '偏瘦', color: '#3498db', description: '建议适当增加营养摄入' }
  }
  if (bmi < 24) {
    return { status: '正常', color: '#2ecc71', description: '继续保持健康饮食' }
  }
  if (bmi < 28) {
    return { status: '超重', color: '#f39c12', description: '建议控制饮食，增加运动' }
  }
  return { status: '肥胖', color: '#e74c3c', description: '建议咨询医生，科学减重' }
}

/**
 * 计算BMR（基础代谢率）- Mifflin-St Jeor公式
 * @param {number} weightKg - 体重(kg)
 * @param {number} heightCm - 身高(cm)
 * @param {number} age - 年龄
 * @param {number} gender - 性别 0=男,1=女
 * @returns {number} BMR(kcal/天)
 */
export const calculateBMR = (weightKg, heightCm, age, gender) => {
  if (gender === 0) {
    // 男性
    return Math.round(10 * weightKg + 6.25 * heightCm - 5 * age + 5)
  }
  // 女性
  return Math.round(10 * weightKg + 6.25 * heightCm - 5 * age - 161)
}

/**
 * 活动系数
 */
export const activityFactors = {
  1: 1.2,    // 久坐
  2: 1.375,  // 轻度活动
  3: 1.55,   // 中度活动
  4: 1.725   // 高强度活动
}

/**
 * 健康目标系数
 */
export const healthGoalFactors = {
  1: 1.0,   // 维持体重
  2: 0.85,  // 减脂
  3: 1.15   // 增肌
}

/**
 * 获取健康目标默认热量系数
 * @param {number} healthGoal - 健康目标 1-3
 * @returns {number} 热量系数
 */
export const getDefaultCalorieCoefficient = (healthGoal) => {
  return healthGoalFactors[healthGoal] || healthGoalFactors[1]
}

/**
 * 根据生日计算年龄
 * @param {string} birthday - 出生日期 YYYY-MM-DD
 * @returns {number|null} 年龄
 */
export const calculateAgeFromBirthday = (birthday) => {
  if (!birthday) return null

  const birthDate = new Date(birthday)
  if (Number.isNaN(birthDate.getTime())) return null

  const today = new Date()
  let age = today.getFullYear() - birthDate.getFullYear()
  const monthDiff = today.getMonth() - birthDate.getMonth()

  if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthDate.getDate())) {
    age -= 1
  }

  return age >= 0 ? age : null
}

/**
 * 计算每日推荐热量
 * @param {number} bmr - 基础代谢率
 * @param {number} activityLevel - 活动水平 1-4
 * @param {number} healthGoal - 健康目标 1-3
 * @param {number} calorieCoefficient - 自定义热量系数
 * @returns {number} 每日推荐热量(kcal)
 */
export const calculateDailyCalorie = (bmr, activityLevel, healthGoal, calorieCoefficient) => {
  const activityFactor = activityFactors[activityLevel] || 1.2
  const customGoalFactor = Number(calorieCoefficient)
  const goalFactor = Number.isFinite(customGoalFactor) && customGoalFactor > 0
    ? customGoalFactor
    : (healthGoalFactors[healthGoal] || 1.0)
  return Math.round(bmr * activityFactor * goalFactor)
}

/**
 * 计算推荐营养素摄入量
 * @param {number} dailyCalorie - 每日推荐热量
 * @returns {object} { protein, carb, fat } 单位：克
 */
export const calculateNutrientGoals = (dailyCalorie) => {
  return {
    protein: Math.round(dailyCalorie * 0.20 / 4),  // 20%热量来自蛋白质，1g蛋白=4kcal
    carb: Math.round(dailyCalorie * 0.55 / 4),     // 55%热量来自碳水，1g碳水=4kcal
    fat: Math.round(dailyCalorie * 0.25 / 9)       // 25%热量来自脂肪，1g脂肪=9kcal
  }
}

/**
 * 计算食物实际营养摄入
 * @param {object} food - 食物信息（每100g营养）
 * @param {number} weightG - 实际摄入重量(g)
 * @returns {object} 实际营养摄入
 */
export const calculateNutrientIntake = (food, weightG) => {
  const ratio = weightG / 100
  return {
    calorie: Math.round(food.calorie_per_100g * ratio),
    protein: parseFloat((food.protein_per_100g * ratio).toFixed(2)),
    carb: parseFloat((food.carb_per_100g * ratio).toFixed(2)),
    fat: parseFloat((food.fat_per_100g * ratio).toFixed(2))
  }
}

/**
 * 计算膳食平衡评分 (0-100分)
 * @param {object} actual - 实际摄入 { calorie, protein, carb, fat }
 * @param {object} target - 目标摄入 { calorie, protein, carb, fat }
 * @returns {number} 评分
 */
export const calculateDietScore = (actual, target) => {
  if (!target.calorie) return 0

  // 热量评分 (权重40%)
  const calorieRatio = actual.calorie / target.calorie
  let calorieScore
  if (calorieRatio >= 0.9 && calorieRatio <= 1.1) {
    calorieScore = 100
  } else if (calorieRatio >= 0.8 && calorieRatio <= 1.2) {
    calorieScore = 80
  } else {
    calorieScore = Math.max(0, 100 - Math.abs(calorieRatio - 1) * 100)
  }

  // 营养素评分
  const getNutrientScore = (actual, target) => {
    if (!target) return 0
    const ratio = actual / target
    if (ratio >= 0.8 && ratio <= 1.2) return 100
    return Math.max(0, 100 - Math.abs(ratio - 1) * 80)
  }

  const proteinScore = getNutrientScore(actual.protein, target.protein)
  const carbScore = getNutrientScore(actual.carb, target.carb)
  const fatScore = getNutrientScore(actual.fat, target.fat)

  // 加权总分
  const totalScore = calorieScore * 0.4 + proteinScore * 0.2 + carbScore * 0.2 + fatScore * 0.2
  return Math.round(totalScore)
}

/**
 * 获取摄入状态
 * @param {number} actual - 实际摄入
 * @param {number} target - 目标摄入
 * @returns {object} { status, color, percent }
 */
export const getIntakeStatus = (actual, target) => {
  if (!target) return { status: '未设置目标', color: '#999', percent: 0 }
  
  const percent = Math.round((actual / target) * 100)
  
  if (percent < 80) {
    return { status: '不足', color: '#3498db', percent }
  }
  if (percent <= 100) {
    return { status: '正常', color: '#2ecc71', percent }
  }
  if (percent <= 120) {
    return { status: '轻度超标', color: '#f39c12', percent }
  }
  return { status: '严重超标', color: '#e74c3c', percent }
}

export default {
  calculateBMI,
  getBMIStatus,
  calculateBMR,
  calculateAgeFromBirthday,
  calculateDailyCalorie,
  calculateNutrientGoals,
  calculateNutrientIntake,
  calculateDietScore,
  getIntakeStatus,
  activityFactors,
  healthGoalFactors,
  getDefaultCalorieCoefficient
}
