/**
 * 饮食记录状态管理
 */
import { defineStore } from 'pinia'
import dayjs from 'dayjs'
import { getMealsByDate, addMeal, updateMeal, deleteMeal } from '@/api/meal'

export const useMealStore = defineStore('meal', {
  state: () => ({
    // 当前选中日期
    currentDate: dayjs().format('YYYY-MM-DD'),
    // 当前餐次 1=早餐,2=午餐,3=晚餐,4=加餐
    currentMealType: 1,
    // 当日饮食记录
    meals: [],
    // 加载状态
    loading: false
  }),

  getters: {
    // 餐次名称映射
    mealTypeNames: () => ({
      1: '早餐',
      2: '午餐',
      3: '晚餐',
      4: '加餐'
    }),

    // 当前餐次名称
    currentMealTypeName(state) {
      return this.mealTypeNames[state.currentMealType]
    },

    // 按餐次分组的记录
    mealsByType(state) {
      const grouped = { 1: [], 2: [], 3: [], 4: [] }
      state.meals.forEach(meal => {
        if (grouped[meal.meal_type]) {
          grouped[meal.meal_type].push(meal)
        }
      })
      return grouped
    },

    // 当前餐次的记录
    currentMeals(state) {
      return state.meals.filter(m => m.meal_type === state.currentMealType)
    },

    // 当日总营养摄入
    todayTotal(state) {
      return state.meals.reduce((total, meal) => ({
        calorie: total.calorie + (meal.calorie || 0),
        protein: total.protein + (meal.protein || 0),
        carb: total.carb + (meal.carb || 0),
        fat: total.fat + (meal.fat || 0)
      }), { calorie: 0, protein: 0, carb: 0, fat: 0 })
    },

    // 各餐次营养小计
    mealTypeTotal(state) {
      const totals = {}
      for (const type of [1, 2, 3, 4]) {
        totals[type] = state.meals
          .filter(m => m.meal_type === type)
          .reduce((total, meal) => ({
            calorie: total.calorie + (meal.calorie || 0),
            protein: total.protein + (meal.protein || 0),
            carb: total.carb + (meal.carb || 0),
            fat: total.fat + (meal.fat || 0)
          }), { calorie: 0, protein: 0, carb: 0, fat: 0 })
      }
      return totals
    }
  },

  actions: {
    // 设置当前日期
    setCurrentDate(date) {
      this.currentDate = date
    },

    // 设置当前餐次
    setCurrentMealType(type) {
      this.currentMealType = type
    },

    // 获取指定日期的饮食记录
    async fetchMeals(date = this.currentDate) {
      this.loading = true
      try {
        const data = await getMealsByDate(date)
        // 后端返回格式: { date, meals: {1:[], 2:[], 3:[], 4:[]}, summary }
        // 将按餐次分组的数据转为数组
        const mealsArray = []
        if (data.meals) {
          Object.entries(data.meals).forEach(([mealType, records]) => {
            records.forEach(record => {
              mealsArray.push({ ...record, meal_type: parseInt(mealType) })
            })
          })
        }
        this.meals = mealsArray
        return data
      } catch (error) {
        console.error('获取饮食记录失败:', error)
        throw error
      } finally {
        this.loading = false
      }
    },

    // 添加饮食记录
    async addMealRecord(data) {
      try {
        const result = await addMeal({
          ...data,
          date: this.currentDate,
          meal_type: this.currentMealType
        })
        // 重新获取列表
        await this.fetchMeals()
        return result
      } catch (error) {
        console.error('添加饮食记录失败:', error)
        throw error
      }
    },

    // 更新饮食记录
    async updateMealRecord(id, data) {
      try {
        const result = await updateMeal(id, data)
        // 更新本地数据
        const index = this.meals.findIndex(m => m.id === id)
        if (index !== -1) {
          this.meals[index] = { ...this.meals[index], ...result }
        }
        return result
      } catch (error) {
        console.error('更新饮食记录失败:', error)
        throw error
      }
    },

    // 删除饮食记录
    async deleteMealRecord(id) {
      try {
        await deleteMeal(id)
        // 从本地列表移除
        this.meals = this.meals.filter(m => m.id !== id)
      } catch (error) {
        console.error('删除饮食记录失败:', error)
        throw error
      }
    }
  }
})
