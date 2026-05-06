<template>
  <view class="foods-container">
    <!-- 搜索栏 -->
    <view class="search-bar">
      <view class="search-input">
        <text class="search-icon">🔍</text>
        <input 
          v-model="keyword" 
          placeholder="搜索食物"
          @confirm="handleSearch"
          @input="onSearchInput"
        />
        <text v-if="keyword" class="clear-btn" @click="clearSearch">✕</text>
      </view>
    </view>

    <!-- 分类Tab -->
    <scroll-view class="category-tabs" scroll-x>
      <view 
        v-for="cat in categories" 
        :key="cat.code"
        class="tab-item"
        :class="{ active: currentCategory === cat.code }"
        @click="selectCategory(cat.code)"
      >
        {{ cat.name }}
      </view>
    </scroll-view>

    <!-- 食物列表 -->
    <view class="food-list-wrapper">
    <scroll-view 
      class="food-list" 
      scroll-y
      @scrolltolower="loadMore"
    >
      <view v-if="loading && foods.length === 0" class="loading-tip">
        加载中...
      </view>
      
      <view v-else-if="foods.length === 0" class="empty-tip">
        <text>暂无食物数据</text>
      </view>
      
      <view 
        v-for="food in foods" 
        :key="food.id" 
        class="food-item"
        @click="handleFoodClick(food)"
      >
        <view class="food-content">
          <view class="food-main">
            <text class="food-name">{{ food.name }}</text>
            <text class="food-calorie">{{ food.calorie_per_100g }} kcal/100g</text>
          </view>
          <view class="food-nutrients">
            <text class="nutrient">蛋白{{ food.protein_per_100g }}g</text>
            <text class="nutrient">碳水{{ food.carb_per_100g }}g</text>
            <text class="nutrient">脂肪{{ food.fat_per_100g }}g</text>
          </view>
        </view>
        <view class="food-action" v-if="isSelectMode">
          <text class="add-btn">+</text>
        </view>
      </view>
      
      <view v-if="loading && foods.length > 0" class="loading-more">
        加载更多...
      </view>
      
      <view v-if="!hasMore && foods.length > 0" class="no-more">
        没有更多了
      </view>
    </scroll-view>
    </view>

    <!-- 食物详情/添加弹窗 -->
    <uni-popup ref="foodPopup" type="bottom">
      <view class="food-popup">
        <view class="popup-header">
          <text class="popup-title">{{ selectedFood?.name }}</text>
          <text class="popup-close" @click="closePopup">✕</text>
        </view>
        
        <view class="popup-content">
          <!-- 营养信息 -->
          <view class="nutrition-grid">
            <view class="nutrition-item main">
              <text class="value">{{ selectedFood?.calorie_per_100g }}</text>
              <text class="label">热量(kcal)</text>
            </view>
            <view class="nutrition-item">
              <text class="value">{{ selectedFood?.protein_per_100g }}</text>
              <text class="label">蛋白质(g)</text>
            </view>
            <view class="nutrition-item">
              <text class="value">{{ selectedFood?.carb_per_100g }}</text>
              <text class="label">碳水(g)</text>
            </view>
            <view class="nutrition-item">
              <text class="value">{{ selectedFood?.fat_per_100g }}</text>
              <text class="label">脂肪(g)</text>
            </view>
          </view>
          
          <view class="nutrition-extra" v-if="selectedFood?.fiber_per_100g">
            <view class="extra-row">
              <text>膳食纤维: {{ selectedFood?.fiber_per_100g }}g</text>
              <text>胆固醇: {{ selectedFood?.cholesterol_per_100g || 0 }}mg</text>
            </view>
            <view class="extra-row">
              <text>钠: {{ selectedFood?.sodium_per_100g || 0 }}mg</text>
              <text>钙: {{ selectedFood?.calcium_per_100g || 0 }}mg</text>
            </view>
          </view>
          
          <!-- 添加记录区域 -->
          <view class="add-section" v-if="isSelectMode">
            <view class="weight-label">输入重量(克)</view>
            <view class="weight-input-wrap">
              <input 
                type="number" 
                v-model="inputWeight"
                placeholder="100"
              />
              <text class="unit">g</text>
            </view>
            <view class="quick-weights">
              <view 
                v-for="w in quickWeights" 
                :key="w"
                class="weight-tag"
                :class="{ active: inputWeight == w }"
                @click="inputWeight = w"
              >
                {{ w }}g
              </view>
            </view>
            <view class="preview" v-if="inputWeight">
              <text>预计摄入: {{ previewCalorie }} kcal</text>
            </view>
          </view>
        </view>
        
        <view class="popup-footer" v-if="isSelectMode">
          <button class="btn-add" @click="addToMeal">添加到{{ mealTypeName }}</button>
        </view>
      </view>
    </uni-popup>
  </view>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { searchFoods, getCategories, getFoodDetail } from '@/api/food'
import { addMeal } from '@/api/meal'

// 状态
const keyword = ref('')
const currentCategory = ref('')
const categories = ref([{ code: '', name: '全部' }])
const foods = ref([])
const loading = ref(false)
const page = ref(1)
const hasMore = ref(true)
const selectedFood = ref(null)
const inputWeight = ref(100)
const foodPopup = ref(null)

// 页面参数
const isSelectMode = ref(false)
const selectDate = ref('')
const selectMealType = ref(1)

const quickWeights = [50, 100, 150, 200, 250, 300]

// 计算属性
const mealTypeName = computed(() => {
  const names = { 1: '早餐', 2: '午餐', 3: '晚餐', 4: '加餐' }
  return names[selectMealType.value]
})

const previewCalorie = computed(() => {
  if (!selectedFood.value || !inputWeight.value) return 0
  return Math.round(selectedFood.value.calorie_per_100g * inputWeight.value / 100)
})

// 方法
const fetchCategories = async () => {
  try {
    const data = await getCategories()
    // 扁平化分类树，只取一级分类
    const cats = [{ code: '', name: '全部' }]
    data.forEach(cat => {
      cats.push({ code: cat.code, name: cat.name })
    })
    categories.value = cats
  } catch (error) {
    console.error('获取分类失败:', error)
  }
}

const fetchFoods = async (reset = false) => {
  if (loading.value) return
  if (!reset && !hasMore.value) return
  
  if (reset) {
    page.value = 1
    hasMore.value = true
    foods.value = []
  }
  
  loading.value = true
  try {
    const params = {
      page: page.value,
      per_page: 20
    }
    if (keyword.value) params.keyword = keyword.value
    if (currentCategory.value) params.category_code = currentCategory.value
    
    const data = await searchFoods(params)
    
    if (reset) {
      foods.value = data.items || []
    } else {
      foods.value = [...foods.value, ...(data.items || [])]
    }
    
    hasMore.value = page.value < (data.pages || 1)
    page.value++
  } catch (error) {
    console.error('获取食物列表失败:', error)
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  fetchFoods(true)
}

const onSearchInput = () => {
  // 防抖搜索
  clearTimeout(window.searchTimer)
  window.searchTimer = setTimeout(() => {
    fetchFoods(true)
  }, 500)
}

const clearSearch = () => {
  keyword.value = ''
  fetchFoods(true)
}

const selectCategory = (code) => {
  currentCategory.value = code
  fetchFoods(true)
}

const loadMore = () => {
  if (!loading.value && hasMore.value) {
    fetchFoods()
  }
}

const handleFoodClick = async (food) => {
  try {
    // 获取详情
    const detail = await getFoodDetail(food.id)
    selectedFood.value = detail
    inputWeight.value = 100
    foodPopup.value.open()
  } catch (error) {
    // 如果详情接口失败，使用列表数据
    selectedFood.value = food
    inputWeight.value = 100
    foodPopup.value.open()
  }
}

const closePopup = () => {
  foodPopup.value.close()
  selectedFood.value = null
}

const addToMeal = async () => {
  if (!inputWeight.value || inputWeight.value <= 0) {
    return uni.showToast({ title: '请输入正确的重量', icon: 'none' })
  }
  
  try {
    await addMeal({
      food_id: selectedFood.value.id,
      date: selectDate.value,
      meal_type: selectMealType.value,
      weight_g: parseFloat(inputWeight.value)
    })
    
    uni.showToast({ title: '添加成功', icon: 'success' })
    closePopup()
    
    // 通知记录页刷新
    uni.$emit('foodSelected')
    
    // 返回上一页
    setTimeout(() => {
      uni.navigateBack()
    }, 1000)
  } catch (error) {
    console.error('添加失败:', error)
  }
}

// 初始化
onMounted(async () => {
  // 获取页面参数
  const pages = getCurrentPages()
  const currentPage = pages[pages.length - 1]
  const options = currentPage.$page?.options || currentPage.options || {}
  
  if (options.mode === 'select') {
    isSelectMode.value = true
    selectDate.value = options.date || new Date().toISOString().split('T')[0]
    selectMealType.value = parseInt(options.mealType) || 1
  }
  
  await fetchCategories()
  await fetchFoods(true)
})
</script>

<style lang="scss" scoped>
.foods-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow: hidden;
  background: #f5f5f5;
}

.search-bar {
  flex-shrink: 0;
  padding: 20rpx 30rpx;
  background: #fff;
  
  .search-input {
    display: flex;
    align-items: center;
    background: #f5f5f5;
    border-radius: 40rpx;
    padding: 16rpx 24rpx;
    
    .search-icon {
      margin-right: 16rpx;
    }
    
    input {
      flex: 1;
      font-size: 28rpx;
    }
    
    .clear-btn {
      color: #999;
      font-size: 28rpx;
      padding: 0 10rpx;
    }
  }
}

.category-tabs {
  flex-shrink: 0;
  white-space: nowrap;
  background: #fff;
  padding: 20rpx;
  border-bottom: 1rpx solid #f0f0f0;
  
  .tab-item {
    display: inline-block;
    padding: 12rpx 28rpx;
    margin-right: 16rpx;
    font-size: 26rpx;
    color: #666;
    background: #f5f5f5;
    border-radius: 30rpx;
    
    &.active {
      background: #e8f5e9;
      color: #4caf50;
      font-weight: 500;
    }
  }
}

.food-list-wrapper {
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

.food-list {
  height: 100%;
  padding: 20rpx 30rpx;
  
  .loading-tip,
  .empty-tip {
    text-align: center;
    padding: 60rpx 0;
    color: #999;
    font-size: 28rpx;
  }
  
  .food-item {
    display: flex;
    align-items: center;
    background: #fff;
    border-radius: 16rpx;
    padding: 24rpx;
    padding-right: 32rpx;
    margin-bottom: 20rpx;
    box-sizing: border-box;
    
    .food-content {
      flex: 1;
      min-width: 0;
      overflow: hidden;
    }
        
    .food-main {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 12rpx;
      
      .food-name {
        font-size: 30rpx;
        color: #333;
        font-weight: 500;
        flex-shrink: 0;
      }
      
      .food-calorie {
        font-size: 28rpx;
        color: #4caf50;
        font-weight: 500;
        flex-shrink: 0;
      }
    }
    
    .food-nutrients {
      display: flex;
      gap: 24rpx;
      
      .nutrient {
        font-size: 24rpx;
        color: #999;
      }
    }
    
    .food-action {
      margin-left: 24rpx;
      flex-shrink: 0;
      
      .add-btn {
        width: 56rpx;
        height: 56rpx;
        background: #4caf50;
        color: #fff;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 32rpx;
        line-height: 1;
      }
    }
  }
  
  .loading-more,
  .no-more {
    text-align: center;
    padding: 30rpx 0;
    color: #999;
    font-size: 26rpx;
  }
}

.food-popup {
  background: #fff;
  border-radius: 24rpx 24rpx 0 0;
  max-height: 80vh;
  
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
    
    .nutrition-grid {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 20rpx;
      margin-bottom: 24rpx;
      
      .nutrition-item {
        text-align: center;
        padding: 20rpx;
        background: #f5f5f5;
        border-radius: 12rpx;
        
        &.main {
          background: #e8f5e9;
          
          .value {
            color: #4caf50;
          }
        }
        
        .value {
          display: block;
          font-size: 32rpx;
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
    
    .nutrition-extra {
      background: #fafafa;
      border-radius: 12rpx;
      padding: 20rpx;
      margin-bottom: 24rpx;
      
      .extra-row {
        display: flex;
        justify-content: space-between;
        font-size: 24rpx;
        color: #666;
        margin-bottom: 10rpx;
        
        &:last-child {
          margin-bottom: 0;
        }
      }
    }
    
    .add-section {
      .weight-label {
        font-size: 28rpx;
        color: #333;
        margin-bottom: 16rpx;
      }
      
      .weight-input-wrap {
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
        margin-top: 20rpx;
        
        .weight-tag {
          padding: 12rpx 24rpx;
          background: #f5f5f5;
          color: #666;
          border-radius: 20rpx;
          font-size: 26rpx;
          
          &.active {
            background: #e8f5e9;
            color: #4caf50;
          }
        }
      }
      
      .preview {
        margin-top: 20rpx;
        text-align: center;
        font-size: 28rpx;
        color: #4caf50;
        font-weight: 500;
      }
    }
  }
  
  .popup-footer {
    padding: 30rpx;
    
    .btn-add {
      width: 100%;
      height: 88rpx;
      background: #4caf50;
      color: #fff;
      font-size: 32rpx;
      border-radius: 44rpx;
      border: none;
    }
  }
}
</style>
