<template>
  <view class="record-container">
    <scroll-view scroll-y class="record-scroll">
    <!-- 日期选择 -->
    <view class="date-bar">
      <view class="date-nav" @click="prevDay">‹</view>
      <picker mode="date" :value="currentDate" @change="onDateChange">
        <view class="date-display">
          <text class="date-text">{{ displayDate }}</text>
          <text class="date-icon">▼</text>
        </view>
      </picker>
      <view class="date-nav" @click="nextDay" :class="{ disabled: isToday }">›</view>
    </view>

    <!-- 餐次Tab -->
    <view class="meal-tabs">
      <view 
        v-for="meal in mealTypes" 
        :key="meal.type"
        class="tab-item"
        :class="{ active: currentMealType === meal.type }"
        @click="switchMealType(meal.type)"
      >
        <text class="tab-icon">{{ meal.icon }}</text>
        <text class="tab-name">{{ meal.name }}</text>
      </view>
    </view>

    <!-- 营养小计 -->
    <view class="summary-card">
      <view class="summary-item">
        <text class="value">{{ currentMealTotal.calorie }}</text>
        <text class="label">热量(kcal)</text>
      </view>
      <view class="summary-item">
        <text class="value">{{ currentMealTotal.protein.toFixed(1) }}</text>
        <text class="label">蛋白质(g)</text>
      </view>
      <view class="summary-item">
        <text class="value">{{ currentMealTotal.carb.toFixed(1) }}</text>
        <text class="label">碳水(g)</text>
      </view>
      <view class="summary-item">
        <text class="value">{{ currentMealTotal.fat.toFixed(1) }}</text>
        <text class="label">脂肪(g)</text>
      </view>
    </view>

    <!-- 已记录食物列表 -->
    <view class="food-list">
      <view class="list-header">
        <text class="title">已添加食物 ({{ currentMeals.length }})</text>
      </view>
      
      <view v-if="currentMeals.length === 0" class="empty-tip">
        <text>暂无记录，点击下方按钮添加食物</text>
      </view>
      
      <view 
        v-for="item in currentMeals" 
        :key="item.id" 
        class="food-item"
        @longpress="showActions(item)"
      >
        <view class="food-info">
          <text class="food-name">{{ item.food?.name || item.food_name || '未知' }}</text>
          <text class="food-weight" v-if="item.weight_g">{{ item.weight_g }}g</text>
          <text class="food-weight custom" v-else-if="item.is_custom">自定义</text>
        </view>
        <view class="food-nutrition">
          <text class="calorie">{{ item.calorie }} kcal</text>
        </view>
        <view class="food-actions">
          <text class="action-btn edit" v-if="!item.is_custom" @click.stop="editRecord(item)">编辑</text>
          <text class="action-btn delete" @click.stop="deleteRecord(item)">删除</text>
        </view>
      </view>
    </view>

    <!-- 底部双按钮 -->
    <view class="bottom-bar">
      <view class="add-btn secondary" @click="openRecipePicker">
        <text class="btn-icon">⭐</text>
        <text class="btn-text">从收藏添加</text>
      </view>
      <view class="add-btn primary" @click="goToFoods">
        <text class="btn-icon">+</text>
        <text class="btn-text">添加食物</text>
      </view>
    </view>

    <!-- 收藏选择弹窗 -->
    <uni-popup ref="recipePopup" type="bottom">
      <view class="recipe-popup">
        <view class="popup-header">
          <text class="popup-title">从收藏添加</text>
          <text class="popup-close" @click="closeRecipePicker">✕</text>
        </view>
        <scroll-view class="popup-body" scroll-y>
          <view v-if="recipeLoading" class="loading-tip">加载中...</view>
          <view v-else-if="recipes.length === 0" class="empty-tip">
            <text class="empty-icon">📋</text>
            <text>还没有收藏，去「我的 → 收藏」创建吧</text>
          </view>
          <view v-else class="recipe-list">
            <view
              v-for="recipe in recipes"
              :key="recipe.id"
              class="recipe-card"
              @click="selectRecipe(recipe)"
            >
              <view class="card-header">
                <text class="recipe-name">{{ recipe.name }}</text>
                <text class="recipe-count">{{ recipe.summary?.item_count || 0 }} 种食物</text>
              </view>
              <view class="card-preview" v-if="recipe.items && recipe.items.length > 0">
                <text
                  v-for="(item, idx) in recipe.items.slice(0, 5)"
                  :key="idx"
                  class="preview-tag"
                >{{ item.type === 'custom' ? item.name : (item.food?.name || '未知') }}</text>
                <text v-if="recipe.items.length > 5" class="preview-more">+{{ recipe.items.length - 5 }}</text>
              </view>
              <view class="card-summary" v-if="recipe.summary">
                <text class="sum-item">🔥 {{ recipe.summary.calorie }}kcal</text>
                <text class="sum-item">蛋白{{ recipe.summary.protein }}g</text>
                <text class="sum-item">脂肪{{ recipe.summary.fat }}g</text>
                <text class="sum-item">碳水{{ recipe.summary.carb }}g</text>
              </view>
            </view>
          </view>
        </scroll-view>
      </view>
    </uni-popup>

    <!-- 编辑弹窗 -->
    <uni-popup ref="editPopup" type="bottom">
      <view class="edit-popup">
        <view class="popup-header">
          <text class="popup-title">编辑重量</text>
          <text class="popup-close" @click="closeEditPopup">✕</text>
        </view>
        <view class="popup-content">
          <view class="food-name">{{ editingItem?.food?.name || editingItem?.food_name }}</view>
          <view class="weight-input">
            <input 
              type="number" 
              v-model="editWeight" 
              placeholder="输入重量"
              @input="onWeightInput"
            />
            <text class="unit">克</text>
          </view>
          <view class="quick-weights">
            <view 
              v-for="w in quickWeights" 
              :key="w" 
              class="weight-tag"
              @click="editWeight = w"
            >
              {{ w }}g
            </view>
          </view>
          <view class="preview-nutrition" v-if="editWeight">
            <text>预计: {{ previewCalorie }} kcal</text>
          </view>
        </view>
        <view class="popup-footer">
          <button class="btn-cancel" @click="closeEditPopup">取消</button>
          <button class="btn-confirm" @click="confirmEdit">确定</button>
        </view>
      </view>
    </uni-popup>
    </scroll-view>
  </view>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { onUnload } from '@dcloudio/uni-app'
import { useMealStore } from '@/store/meal'
import { getRecipes } from '@/api/recipe'
import { batchAddMeals } from '@/api/meal'
import dayjs from 'dayjs'

const mealStore = useMealStore()
const editPopup = ref(null)
const recipePopup = ref(null)
const editingItem = ref(null)
const editWeight = ref('')

// 收藏选择器状态
const recipes = ref([])
const recipeLoading = ref(false)

// 餐次配置
const mealTypes = [
  { type: 1, name: '早餐', icon: '🌅' },
  { type: 2, name: '午餐', icon: '☀️' },
  { type: 3, name: '晚餐', icon: '🌙' },
  { type: 4, name: '加餐', icon: '🍎' }
]

const quickWeights = [50, 100, 150, 200, 250, 300]

// 计算属性
const currentDate = computed(() => mealStore.currentDate)
const currentMealType = computed(() => mealStore.currentMealType)
const currentMeals = computed(() => mealStore.currentMeals)
const currentMealTotal = computed(() => mealStore.mealTypeTotal[currentMealType.value] || {
  calorie: 0, protein: 0, carb: 0, fat: 0
})

const displayDate = computed(() => {
  const d = dayjs(currentDate.value)
  const today = dayjs()
  if (d.isSame(today, 'day')) return '今天'
  if (d.isSame(today.subtract(1, 'day'), 'day')) return '昨天'
  return d.format('M月D日')
})

const isToday = computed(() => {
  return dayjs(currentDate.value).isSame(dayjs(), 'day')
})

const mealTypeName = computed(() => {
  const names = { 1: '早餐', 2: '午餐', 3: '晚餐', 4: '加餐' }
  return names[currentMealType.value] || '餐次'
})

const previewCalorie = computed(() => {
  if (!editingItem.value || !editWeight.value) return 0
  const item = editingItem.value
  if (item.is_custom || !item.food) return item.calorie || 0
  const ratio = editWeight.value / 100
  return Math.round((item.food.calorie_per_100g || 100) * ratio)
})

// 方法
const prevDay = () => {
  const newDate = dayjs(currentDate.value).subtract(1, 'day').format('YYYY-MM-DD')
  mealStore.setCurrentDate(newDate)
}

const nextDay = () => {
  if (isToday.value) return
  const newDate = dayjs(currentDate.value).add(1, 'day').format('YYYY-MM-DD')
  mealStore.setCurrentDate(newDate)
}

const onDateChange = (e) => {
  mealStore.setCurrentDate(e.detail.value)
}

const switchMealType = (type) => {
  mealStore.setCurrentMealType(type)
}

const goToFoods = () => {
  uni.navigateTo({ 
    url: `/pages/foods/foods?mode=select&date=${currentDate.value}&mealType=${currentMealType.value}` 
  })
}

// 收藏选择器
const openRecipePicker = async () => {
  recipeLoading.value = true
  recipePopup.value.open()
  try {
    const data = await getRecipes()
    recipes.value = data || []
  } catch (e) {
    console.error('获取收藏列表失败:', e)
    uni.showToast({ title: '加载收藏失败', icon: 'none' })
  } finally {
    recipeLoading.value = false
  }
}

const closeRecipePicker = () => {
  recipePopup.value.close()
}

const selectRecipe = (recipe) => {
  if (!recipe.items || recipe.items.length === 0) {
    return uni.showToast({ title: '该收藏没有食物', icon: 'none' })
  }

  const items = recipe.items.map(item => {
    if (item.type === 'custom') {
      return {
        type: 'custom',
        name: item.name,
        calorie: item.calorie || 0,
        protein: item.protein || 0,
        fat: item.fat || 0,
        carb: item.carb || 0
      }
    }
    return {
      type: 'food',
      food_id: item.food_id,
      weight_g: item.weight_g
    }
  })

  const msg = recipe.summary
    ? `共${items.length}项，热量约${recipe.summary.calorie}kcal，确定添加到${mealTypeName.value}？`
    : `共${items.length}项，确定添加？`

  uni.showModal({
    title: recipe.name,
    content: msg,
    success: async (res) => {
      if (res.confirm) {
        try {
          const result = await batchAddMeals({
            date: currentDate.value,
            meal_type: currentMealType.value,
            items: items
          })
          closeRecipePicker()
          uni.showToast({ title: `已添加${items.length}项`, icon: 'success' })
          await mealStore.fetchMeals()
        } catch (e) {
          console.error('批量添加失败:', e)
          uni.showToast({ title: '添加失败', icon: 'none' })
        }
      }
    }
  })
}

const editRecord = (item) => {
  editingItem.value = item
  editWeight.value = item.weight_g
  editPopup.value.open()
}

const closeEditPopup = () => {
  editPopup.value.close()
  editingItem.value = null
  editWeight.value = ''
}

const confirmEdit = async () => {
  if (!editWeight.value || editWeight.value <= 0) {
    return uni.showToast({ title: '请输入正确的重量', icon: 'none' })
  }
  
  try {
    await mealStore.updateMealRecord(editingItem.value.id, {
      weight_g: parseFloat(editWeight.value)
    })
    uni.showToast({ title: '修改成功', icon: 'success' })
    closeEditPopup()
    // 刷新数据
    await mealStore.fetchMeals()
  } catch (error) {
    console.error('修改失败:', error)
  }
}

const deleteRecord = (item) => {
  const name = item.food?.name || item.food_name || '未知'
  uni.showModal({
    title: '确认删除',
    content: `确定要删除"${name}"吗？`,
    success: async (res) => {
      if (res.confirm) {
        try {
          await mealStore.deleteMealRecord(item.id)
          uni.showToast({ title: '删除成功', icon: 'success' })
        } catch (error) {
          console.error('删除失败:', error)
        }
      }
    }
  })
}

const onWeightInput = (e) => {
  editWeight.value = e.detail.value
}

// 监听日期变化，重新获取数据
watch(currentDate, async (newDate) => {
  await mealStore.fetchMeals(newDate)
})

// 处理页面参数
onMounted(async () => {
  const pages = getCurrentPages()
  const currentPage = pages[pages.length - 1]
  const options = currentPage.$page?.options || currentPage.options || {}
  
  if (options.mealType) {
    mealStore.setCurrentMealType(parseInt(options.mealType))
  }
  if (options.date) {
    mealStore.setCurrentDate(options.date)
  }
  
  await mealStore.fetchMeals()
})

// 监听食物选择返回
uni.$on('foodSelected', async () => {
  await mealStore.fetchMeals()
})

onUnload(() => {
  uni.$off('foodSelected')
})
</script>

<style lang="scss" scoped>
.record-container {
  height: 100vh;
  overflow: hidden;
  background: #f5f5f5;
}

.record-scroll {
  height: 100%;
  padding-bottom: 180rpx;
}

.date-bar {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 30rpx;
  background: #fff;
  
  .date-nav {
    width: 60rpx;
    height: 60rpx;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 40rpx;
    color: #4caf50;
    
    &.disabled {
      color: #ccc;
    }
  }
  
  .date-display {
    display: flex;
    align-items: center;
    padding: 0 40rpx;
    
    .date-text {
      font-size: 32rpx;
      font-weight: bold;
      color: #333;
    }
    
    .date-icon {
      font-size: 20rpx;
      color: #999;
      margin-left: 10rpx;
    }
  }
}

.meal-tabs {
  display: flex;
  background: #fff;
  padding: 0 20rpx 20rpx;
  
  .tab-item {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 20rpx 0;
    border-radius: 16rpx;
    transition: all 0.2s;
    
    &.active {
      background: #e8f5e9;
      
      .tab-name {
        color: #4caf50;
        font-weight: bold;
      }
    }
    
    .tab-icon {
      font-size: 40rpx;
      margin-bottom: 8rpx;
    }
    
    .tab-name {
      font-size: 26rpx;
      color: #666;
    }
  }
}

.summary-card {
  display: flex;
  margin: 20rpx 30rpx;
  background: #fff;
  border-radius: 16rpx;
  padding: 30rpx;
  
  .summary-item {
    flex: 1;
    text-align: center;
    
    .value {
      display: block;
      font-size: 36rpx;
      font-weight: bold;
      color: #333;
    }
    
    .label {
      display: block;
      font-size: 22rpx;
      color: #999;
      margin-top: 8rpx;
    }
  }
}

.food-list {
  margin: 0 30rpx;
  background: #fff;
  border-radius: 16rpx;
  overflow: hidden;
  
  .list-header {
    padding: 24rpx 30rpx;
    border-bottom: 1rpx solid #f0f0f0;
    
    .title {
      font-size: 28rpx;
      color: #666;
    }
  }
  
  .empty-tip {
    padding: 60rpx 30rpx;
    text-align: center;
    color: #999;
    font-size: 28rpx;
  }
  
  .food-item {
    display: flex;
    align-items: center;
    padding: 24rpx 30rpx;
    border-bottom: 1rpx solid #f0f0f0;
    
    &:last-child {
      border-bottom: none;
    }
    
    .food-info {
      flex: 1;
      
      .food-name {
        font-size: 30rpx;
        color: #333;
        display: block;
      }
      
      .food-weight {
        font-size: 24rpx;
        color: #999;
        margin-top: 4rpx;
        
        &.custom {
          color: #2196f3;
          background: #e3f2fd;
          display: inline-block;
          padding: 2rpx 10rpx;
          border-radius: 6rpx;
        }
      }
    }
    
    .food-nutrition {
      margin-right: 20rpx;
      
      .calorie {
        font-size: 28rpx;
        color: #4caf50;
        font-weight: 500;
      }
    }
    
    .food-actions {
      display: flex;
      gap: 16rpx;
      
      .action-btn {
        font-size: 24rpx;
        padding: 8rpx 16rpx;
        border-radius: 8rpx;
        
        &.edit {
          color: #2196f3;
          background: #e3f2fd;
        }
        
        &.delete {
          color: #f44336;
          background: #ffebee;
        }
      }
    }
  }
}

.bottom-bar {
  position: fixed;
  bottom: 60rpx;
  left: 30rpx;
  right: 30rpx;
  display: flex;
  gap: 20rpx;
}

.add-btn {
  flex: 1;
  height: 88rpx;
  border-radius: 44rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  
  &.primary {
    background: #4caf50;
    box-shadow: 0 8rpx 20rpx rgba(76, 175, 80, 0.4);
    
    .btn-icon, .btn-text {
      color: #fff;
    }
  }
  
  &.secondary {
    background: #fff;
    border: 2rpx solid #4caf50;
    
    .btn-icon, .btn-text {
      color: #4caf50;
    }
  }
  
  .btn-icon {
    font-size: 36rpx;
    margin-right: 8rpx;
  }
  
  .btn-text {
    font-size: 28rpx;
  }
}

.edit-popup {
  background: #fff;
  border-radius: 24rpx 24rpx 0 0;
  
  .popup-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 30rpx;
    border-bottom: 1rpx solid #f0f0f0;
    
    .popup-title {
      font-size: 32rpx;
      font-weight: bold;
      color: #333;
    }
    
    .popup-close {
      font-size: 36rpx;
      color: #999;
    }
  }
  
  .popup-content {
    padding: 30rpx;
    
    .food-name {
      font-size: 30rpx;
      color: #333;
      margin-bottom: 30rpx;
    }
    
    .weight-input {
      display: flex;
      align-items: center;
      background: #f5f5f5;
      border-radius: 12rpx;
      padding: 20rpx;
      
      input {
        flex: 1;
        font-size: 36rpx;
        text-align: center;
      }
      
      .unit {
        font-size: 28rpx;
        color: #999;
      }
    }
    
    .quick-weights {
      display: flex;
      flex-wrap: wrap;
      gap: 16rpx;
      margin-top: 24rpx;
      
      .weight-tag {
        padding: 12rpx 24rpx;
        background: #e8f5e9;
        color: #4caf50;
        border-radius: 20rpx;
        font-size: 26rpx;
      }
    }
    
    .preview-nutrition {
      margin-top: 24rpx;
      text-align: center;
      color: #666;
      font-size: 28rpx;
    }
  }
  
  .popup-footer {
    display: flex;
    padding: 30rpx;
    gap: 20rpx;
    
    button {
      flex: 1;
      height: 80rpx;
      border-radius: 40rpx;
      font-size: 30rpx;
    }
    
    .btn-cancel {
      background: #f5f5f5;
      color: #666;
    }
    
    .btn-confirm {
      background: #4caf50;
      color: #fff;
    }
  }
}

// 收藏选择弹窗
.recipe-popup {
  background: #fff;
  border-radius: 24rpx 24rpx 0 0;
  max-height: 85vh;
  width: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;

  .popup-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 30rpx;
    border-bottom: 1rpx solid #f0f0f0;

    .popup-title {
      font-size: 32rpx;
      font-weight: bold;
      color: #333;
    }

    .popup-close {
      font-size: 36rpx;
      color: #999;
    }
  }

  .popup-body {
    padding: 20rpx 30rpx 40rpx;
    max-height: 60vh;
    overflow-y: auto;
    box-sizing: border-box;

    .loading-tip, .empty-tip {
      text-align: center;
      padding: 60rpx 0;
      color: #999;
      font-size: 28rpx;
    }

    .empty-tip .empty-icon {
      font-size: 80rpx;
      display: block;
      margin-bottom: 20rpx;
    }

    .recipe-list {
      .recipe-card {
        background: #f9f9f9;
        border-radius: 16rpx;
        padding: 24rpx;
        margin-bottom: 16rpx;
        box-sizing: border-box;
        overflow: hidden;

        .card-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 14rpx;
          min-width: 0;

          .recipe-name {
            font-size: 30rpx;
            font-weight: bold;
            color: #333;
            flex: 1;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            margin-right: 16rpx;
          }

          .recipe-count {
            flex-shrink: 0;
            font-size: 22rpx;
            color: #4caf50;
            background: #e8f5e9;
            padding: 4rpx 14rpx;
            border-radius: 20rpx;
          }
        }

        .card-preview {
          display: flex;
          flex-wrap: wrap;
          margin-bottom: 14rpx;
          min-width: 0;
          overflow: hidden;

          .preview-tag {
            font-size: 22rpx;
            padding: 4rpx 12rpx;
            background: #f0f0f0;
            color: #666;
            border-radius: 8rpx;
            margin-right: 10rpx;
            margin-bottom: 8rpx;
            max-width: 100%;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
          }

          .preview-more {
            font-size: 22rpx;
            color: #999;
            padding: 4rpx 0;
          }
        }

        .card-summary {
          display: flex;
          gap: 20rpx;
          flex-wrap: wrap;

          .sum-item {
            font-size: 24rpx;
            color: #666;
          }
        }
      }
    }
  }
}
</style>
