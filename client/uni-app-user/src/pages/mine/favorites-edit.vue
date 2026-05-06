<template>
  <view class="favorites-edit-container">
    <scroll-view class="favorites-edit-scroll" scroll-y>
    <!-- 名称输入 -->
    <view class="name-section">
      <text class="section-label">收藏名称</text>
      <input 
        class="name-input" 
        v-model="recipeName" 
        placeholder="例如：我的健身早餐"
        maxlength="50"
      />
    </view>

    <!-- 已添加的条目列表 -->
    <view class="items-section">
      <view class="section-header">
        <text class="section-label">食物列表 ({{ items.length }})</text>
      </view>

      <view v-if="items.length === 0" class="empty-items">
        <text class="empty-icon">🍽️</text>
        <text class="empty-text">还没有添加食物，点击下方按钮开始</text>
      </view>

      <view v-else class="items-list">
        <view 
          v-for="(item, index) in items" 
          :key="index" 
          class="item-card"
        >
          <view class="item-info">
            <view class="item-header">
              <text class="item-type-tag" :class="item.type">
                {{ item.type === 'food' ? '食物库' : '自定义' }}
              </text>
              <text class="item-name">{{ getItemName(item) }}</text>
              <text class="item-delete" @click="removeItem(index)">✕</text>
            </view>
            <view class="item-nutrients">
              <text class="nutrient">🔥 {{ getItemCalorie(item) }} kcal</text>
              <text class="nutrient">蛋白 {{ getItemProtein(item) }}g</text>
              <text class="nutrient">脂肪 {{ getItemFat(item) }}g</text>
              <text class="nutrient">碳水 {{ getItemCarb(item) }}g</text>
            </view>
            <view v-if="item.type === 'food'" class="item-weight">
              重量: {{ item.weight_g }}g
            </view>
          </view>
        </view>
      </view>

      <!-- 总营养汇总 -->
      <view v-if="items.length > 0" class="summary-bar">
        <text class="summary-item">总计: 🔥{{ totalCalorie }}kcal</text>
        <text class="summary-item">蛋白{{ totalProtein }}g</text>
        <text class="summary-item">脂肪{{ totalFat }}g</text>
        <text class="summary-item">碳水{{ totalCarb }}g</text>
      </view>
    </view>

    <!-- 底部操作按钮 -->
    <view class="bottom-actions">
      <button class="action-btn food-btn" @click="goToFoodLibrary">
        🥗 从食物库选择
      </button>
      <button class="action-btn custom-btn" @click="openCustomForm">
        ✏️ 手动输入
      </button>
    </view>

    <!-- 保存按钮 -->
    <view class="save-section">
      <button class="save-btn" @click="handleSave" :loading="saving">
        {{ isEdit ? '保存修改' : '创建收藏' }}
      </button>
      <button v-if="isEdit" class="delete-btn" @click="handleDelete">
        删除此收藏
      </button>
    </view>
    </scroll-view>

    <!-- 手动输入弹窗 -->
    <uni-popup ref="customPopup" type="bottom">
      <view class="custom-popup">
        <view class="popup-header">
          <text class="popup-title">手动输入食物</text>
          <text class="popup-close" @click="closeCustomForm">✕</text>
        </view>
        <scroll-view class="popup-body" scroll-y>
          <view class="form-item">
            <text class="form-label">食物名称</text>
            <input 
              v-model="customForm.name" 
              placeholder="例如：蛋白粉、牛奶"
              maxlength="30"
            />
          </view>
          <view class="form-row">
            <view class="form-item half">
              <text class="form-label">蛋白质(g)</text>
              <input type="digit" v-model="customForm.protein" placeholder="0" />
            </view>
            <view class="form-item half">
              <text class="form-label">脂肪(g)</text>
              <input type="digit" v-model="customForm.fat" placeholder="0" />
            </view>
          </view>
          <view class="form-row">
            <view class="form-item half">
              <text class="form-label">碳水(g)</text>
              <input type="digit" v-model="customForm.carb" placeholder="0" />
            </view>
            <view class="form-item half">
              <text class="form-label">热量(kcal)</text>
              <input type="digit" v-model="customForm.calorie" :placeholder="autoCalorie + ''" />
              <text class="form-hint">留空自动计算</text>
            </view>
          </view>
        </scroll-view>
        <view class="popup-footer">
          <button class="btn-cancel" @click="closeCustomForm">取消</button>
          <button class="btn-confirm" @click="addCustomItem">添加</button>
        </view>
      </view>
    </uni-popup>

    <!-- 食物库选择弹窗（内联食物选择器） -->
    <uni-popup ref="foodPickerPopup" type="bottom">
      <view class="food-picker-popup">
        <view class="popup-header">
          <text class="popup-title">从食物库选择</text>
          <text class="popup-close" @click="closeFoodPicker">✕</text>
        </view>
        <!-- 搜索栏 -->
        <view class="picker-search">
          <input 
            v-model="foodKeyword" 
            placeholder="搜索食物"
            @confirm="searchFoodsForPicker"
            @input="onFoodSearchInput"
          />
          <text v-if="foodKeyword" class="clear-btn" @click="clearFoodSearch">✕</text>
        </view>
        <!-- 分类标签 -->
        <scroll-view class="picker-tabs" scroll-x>
          <view 
            v-for="cat in foodCategories" 
            :key="cat.code"
            class="picker-tab"
            :class="{ active: foodCategory === cat.code }"
            @click="selectFoodCategory(cat.code)"
          >
            {{ cat.name }}
          </view>
        </scroll-view>
        <!-- 食物列表 -->
        <scroll-view class="picker-list" scroll-y @scrolltolower="loadMoreFoods">
          <view v-if="foodLoading" class="loading-tip">加载中...</view>
          <view v-else-if="foodList.length === 0" class="empty-tip">无匹配食物</view>
          <view 
            v-for="food in foodList" 
            :key="food.id"
            class="picker-food-item"
            @click="selectPickerFood(food)"
          >
            <view class="food-main">
              <text class="food-name">{{ food.name }}</text>
              <text class="food-calorie">{{ food.calorie_per_100g }} kcal/100g</text>
            </view>
            <view class="food-nutrients">
              <text>蛋白{{ food.protein_per_100g }}g</text>
              <text>碳水{{ food.carb_per_100g }}g</text>
              <text>脂肪{{ food.fat_per_100g }}g</text>
            </view>
          </view>
        </scroll-view>
      </view>
    </uni-popup>

    <!-- 选中的食物重量输入弹窗 -->
    <uni-popup ref="weightPopup" type="bottom">
      <view class="custom-popup">
        <view class="popup-header">
          <text class="popup-title">{{ weightForm.foodName }}</text>
          <text class="popup-close" @click="closeWeightForm">✕</text>
        </view>
        <view class="popup-body">
          <view class="nutrition-grid">
            <view class="nutrition-item">
              <text class="value">{{ weightForm.calorie }}</text>
              <text class="form-label">热量/100g</text>
            </view>
            <view class="nutrition-item">
              <text class="value">{{ weightForm.protein }}</text>
              <text class="form-label">蛋白/100g</text>
            </view>
            <view class="nutrition-item">
              <text class="value">{{ weightForm.fat }}</text>
              <text class="form-label">脂肪/100g</text>
            </view>
            <view class="nutrition-item">
              <text class="value">{{ weightForm.carb }}</text>
              <text class="form-label">碳水/100g</text>
            </view>
          </view>
          <view class="form-item">
            <text class="form-label">输入重量(克)</text>
            <view class="weight-input-wrap">
              <input type="number" v-model="weightForm.weight" placeholder="100" />
              <text class="unit">g</text>
            </view>
          </view>
          <view class="quick-weights">
            <view 
              v-for="w in quickWeights" 
              :key="w"
              class="weight-tag"
              :class="{ active: weightForm.weight == w }"
              @click="weightForm.weight = w"
            >
              {{ w }}g
            </view>
          </view>
        </view>
        <view class="popup-footer">
          <button class="btn-cancel" @click="closeWeightForm">取消</button>
          <button class="btn-confirm" @click="addFoodItem">添加</button>
        </view>
      </view>
    </uni-popup>
  </view>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { getRecipes, createRecipe, updateRecipe, deleteRecipe } from '@/api/recipe'
import { searchFoods, getCategories } from '@/api/food'

// === 状态 ===
const isEdit = ref(false)
const editId = ref(null)
const recipeName = ref('')
const items = ref([]) // [{type:'food', food_id, weight_g, food?} | {type:'custom', name, protein, fat, carb, calorie}]
const saving = ref(false)

// === 手动输入表单 ===
const customPopup = ref(null)
const customForm = ref({ name: '', protein: '', fat: '', carb: '', calorie: '' })

// === 食物库选择器 ===
const foodPickerPopup = ref(null)
const foodKeyword = ref('')
const foodCategory = ref('')
const foodCategories = ref([{ code: '', name: '全部' }])
const foodList = ref([])
const foodLoading = ref(false)
const foodPage = ref(1)
const foodHasMore = ref(true)

// === 重量输入 ===
const weightPopup = ref(null)
const weightForm = ref({
  foodId: null,
  foodName: '',
  calorie: 0,
  protein: 0,
  fat: 0,
  carb: 0,
  weight: 100
})

const quickWeights = [50, 100, 150, 200, 250, 300]

// === 自动计算热量 ===
const autoCalorie = computed(() => {
  const p = parseFloat(customForm.value.protein) || 0
  const f = parseFloat(customForm.value.fat) || 0
  const c = parseFloat(customForm.value.carb) || 0
  return Math.round(p * 4 + f * 9 + c * 4) || 0
})

// === 总营养汇总 ===
const totalCalorie = computed(() => {
  let sum = 0
  items.value.forEach(item => {
    if (item.type === 'custom') {
      sum += item.calorie || 0
    } else if (item.food) {
      sum += Math.round(item.food.calorie_per_100g * (item.weight_g || 100) / 100)
    }
  })
  return sum
})

const totalProtein = computed(() => {
  let sum = 0
  items.value.forEach(item => {
    if (item.type === 'custom') {
      sum += item.protein || 0
    } else if (item.food) {
      sum += (item.food.protein_per_100g || 0) * (item.weight_g || 100) / 100
    }
  })
  return Math.round(sum * 10) / 10
})

const totalFat = computed(() => {
  let sum = 0
  items.value.forEach(item => {
    if (item.type === 'custom') {
      sum += item.fat || 0
    } else if (item.food) {
      sum += (item.food.fat_per_100g || 0) * (item.weight_g || 100) / 100
    }
  })
  return Math.round(sum * 10) / 10
})

const totalCarb = computed(() => {
  let sum = 0
  items.value.forEach(item => {
    if (item.type === 'custom') {
      sum += item.carb || 0
    } else if (item.food) {
      sum += (item.food.carb_per_100g || 0) * (item.weight_g || 100) / 100
    }
  })
  return Math.round(sum * 10) / 10
})

// === 辅助函数 ===
const getItemName = (item) => {
  if (item.type === 'custom') return item.name
  if (item.food) return item.food.name
  return '未知食物'
}

const getItemCalorie = (item) => {
  if (item.type === 'custom') return item.calorie || 0
  if (item.food) return Math.round(item.food.calorie_per_100g * (item.weight_g || 100) / 100)
  return 0
}

const getItemProtein = (item) => {
  if (item.type === 'custom') return item.protein || 0
  if (item.food) return Math.round((item.food.protein_per_100g || 0) * (item.weight_g || 100) / 100 * 10) / 10
  return 0
}

const getItemFat = (item) => {
  if (item.type === 'custom') return item.fat || 0
  if (item.food) return Math.round((item.food.fat_per_100g || 0) * (item.weight_g || 100) / 100 * 10) / 10
  return 0
}

const getItemCarb = (item) => {
  if (item.type === 'custom') return item.carb || 0
  if (item.food) return Math.round((item.food.carb_per_100g || 0) * (item.weight_g || 100) / 100 * 10) / 10
  return 0
}

// === 手动输入 ===
const openCustomForm = () => {
  customForm.value = { name: '', protein: '', fat: '', carb: '', calorie: '' }
  customPopup.value.open()
}

const closeCustomForm = () => {
  customPopup.value.close()
}

const addCustomItem = () => {
  const name = (customForm.value.name || '').trim()
  if (!name) {
    return uni.showToast({ title: '请输入食物名称', icon: 'none' })
  }
  const protein = parseFloat(customForm.value.protein) || 0
  const fat = parseFloat(customForm.value.fat) || 0
  const carb = parseFloat(customForm.value.carb) || 0
  const calorieInput = customForm.value.calorie
  const calorie = (calorieInput === '' || calorieInput === null || calorieInput === undefined)
    ? autoCalorie.value
    : (parseFloat(calorieInput) || 0)

  items.value.push({
    type: 'custom',
    name,
    protein: Math.round(protein * 10) / 10,
    fat: Math.round(fat * 10) / 10,
    carb: Math.round(carb * 10) / 10,
    calorie
  })
  closeCustomForm()
}

// === 食物库选择器 ===
const fetchFoodCategories = async () => {
  try {
    const data = await getCategories()
    const cats = [{ code: '', name: '全部' }]
    data.forEach(cat => cats.push({ code: cat.code, name: cat.name }))
    foodCategories.value = cats
  } catch (e) {
    console.error('获取分类失败:', e)
  }
}

const fetchFoodsForPicker = async (reset = false) => {
  if (foodLoading.value) return
  if (!reset && !foodHasMore.value) return

  if (reset) {
    foodPage.value = 1
    foodHasMore.value = true
    foodList.value = []
  }

  foodLoading.value = true
  try {
    const params = { page: foodPage.value, per_page: 20 }
    if (foodKeyword.value) params.keyword = foodKeyword.value
    if (foodCategory.value) params.category_code = foodCategory.value

    const data = await searchFoods(params)
    if (reset) {
      foodList.value = data.items || []
    } else {
      foodList.value = [...foodList.value, ...(data.items || [])]
    }
    foodHasMore.value = foodPage.value < (data.pages || 1)
    foodPage.value++
  } catch (e) {
    console.error('搜索食物失败:', e)
  } finally {
    foodLoading.value = false
  }
}

const goToFoodLibrary = async () => {
  await fetchFoodCategories()
  fetchFoodsForPicker(true)
  foodPickerPopup.value.open()
}

const closeFoodPicker = () => {
  foodPickerPopup.value.close()
}

const onFoodSearchInput = () => {
  clearTimeout(window._foodSearchTimer)
  window._foodSearchTimer = setTimeout(() => {
    fetchFoodsForPicker(true)
  }, 500)
}

const searchFoodsForPicker = () => {
  fetchFoodsForPicker(true)
}

const clearFoodSearch = () => {
  foodKeyword.value = ''
  fetchFoodsForPicker(true)
}

const selectFoodCategory = (code) => {
  foodCategory.value = code
  fetchFoodsForPicker(true)
}

const loadMoreFoods = () => {
  if (!foodLoading.value && foodHasMore.value) {
    fetchFoodsForPicker()
  }
}

const selectPickerFood = (food) => {
  closeFoodPicker()
  weightForm.value = {
    foodId: food.id,
    foodName: food.name,
    calorie: food.calorie_per_100g,
    protein: food.protein_per_100g,
    fat: food.fat_per_100g,
    carb: food.carb_per_100g,
    weight: 100
  }
  weightPopup.value.open()
}

const closeWeightForm = () => {
  weightPopup.value.close()
}

const addFoodItem = () => {
  const food = foodList.value.find(f => f.id === weightForm.value.foodId)
  if (!food) return

  items.value.push({
    type: 'food',
    food_id: weightForm.value.foodId,
    weight_g: parseFloat(weightForm.value.weight) || 100,
    food: food
  })
  closeWeightForm()
}

// === 删除条目 ===
const removeItem = (index) => {
  items.value.splice(index, 1)
}

// === 保存 ===
const handleSave = async () => {
  const name = (recipeName.value || '').trim()
  if (!name) {
    return uni.showToast({ title: '请输入收藏名称', icon: 'none' })
  }
  if (items.value.length === 0) {
    return uni.showToast({ title: '请添加至少一种食物', icon: 'none' })
  }

  saving.value = true
  try {
    const payload = {
      name,
      items: items.value.map(item => {
        if (item.type === 'custom') {
          return {
            type: 'custom',
            name: item.name,
            protein: item.protein,
            fat: item.fat,
            carb: item.carb,
            calorie: item.calorie
          }
        }
        return {
          type: 'food',
          food_id: item.food_id,
          weight_g: item.weight_g
        }
      })
    }

    if (isEdit.value) {
      await updateRecipe(editId.value, payload)
    } else {
      await createRecipe(payload)
    }

    uni.showToast({ title: isEdit.value ? '保存成功' : '创建成功', icon: 'success' })
    setTimeout(() => {
      uni.navigateBack()
    }, 1000)
  } catch (e) {
    console.error('保存失败:', e)
  } finally {
    saving.value = false
  }
}

// === 删除 ===
const handleDelete = () => {
  uni.showModal({
    title: '确认删除',
    content: `确定要删除收藏「${recipeName.value}」吗？`,
    success: async (res) => {
      if (res.confirm) {
        try {
          await deleteRecipe(editId.value)
          uni.showToast({ title: '已删除', icon: 'success' })
          // 通知列表页刷新
          uni.$emit('favoritesChanged')
          setTimeout(() => {
            uni.navigateBack()
          }, 1000)
        } catch (e) {
          console.error('删除失败:', e)
        }
      }
    }
  })
}

// === 初始化 ===
onMounted(async () => {
  const pages = getCurrentPages()
  const currentPage = pages[pages.length - 1]
  const options = currentPage.$page?.options || currentPage.options || {}

  if (options.id) {
    // 编辑模式：加载已有收藏数据
    isEdit.value = true
    editId.value = parseInt(options.id)
    uni.setNavigationBarTitle({ title: '编辑收藏' })

    try {
      const recipes = await getRecipes()
      const found = recipes.find(r => r.id === editId.value)
      if (found) {
        recipeName.value = found.name
        items.value = found.items || []
      }
    } catch (e) {
      console.error('加载收藏失败:', e)
      uni.showToast({ title: '加载失败', icon: 'none' })
    }
  } else {
    uni.setNavigationBarTitle({ title: '新建收藏' })
  }
})
</script>

<style lang="scss" scoped>
.favorites-edit-container {
  height: 100vh;
  background: #f5f5f5;
  overflow: hidden;
}

.favorites-edit-scroll {
  height: 100%;
}

.name-section {
  margin: 20rpx 30rpx;
  background: #fff;
  border-radius: 16rpx;
  padding: 30rpx;

  .section-label {
    font-size: 28rpx;
    color: #666;
    margin-bottom: 16rpx;
    display: block;
  }

  .name-input {
    width: 100%;
    height: 80rpx;
    padding: 0 24rpx;
    background: #f5f5f5;
    border-radius: 12rpx;
    font-size: 30rpx;
    box-sizing: border-box;
  }
}

.items-section {
  margin: 0 30rpx 20rpx;
  flex: 1;

  .section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16rpx;

    .section-label {
      font-size: 28rpx;
      color: #666;
    }
  }

  .empty-items {
    background: #fff;
    border-radius: 16rpx;
    padding: 80rpx 30rpx;
    text-align: center;

    .empty-icon {
      font-size: 80rpx;
      display: block;
      margin-bottom: 20rpx;
    }

    .empty-text {
      font-size: 26rpx;
      color: #999;
    }
  }

  .items-list {
    .item-card {
      background: #fff;
      border-radius: 16rpx;
      padding: 24rpx;
      margin-bottom: 16rpx;

      .item-header {
        display: flex;
        align-items: center;
        margin-bottom: 16rpx;

        .item-type-tag {
          font-size: 22rpx;
          padding: 4rpx 12rpx;
          border-radius: 8rpx;
          margin-right: 12rpx;
          flex-shrink: 0;

          &.food {
            background: #e8f5e9;
            color: #4caf50;
          }

          &.custom {
            background: #e3f2fd;
            color: #2196f3;
          }
        }

        .item-name {
          flex: 1;
          font-size: 28rpx;
          font-weight: 500;
          color: #333;
        }

        .item-delete {
          font-size: 32rpx;
          color: #ccc;
          padding: 0 8rpx;
        }
      }

      .item-nutrients {
        display: flex;
        gap: 20rpx;
        flex-wrap: wrap;

        .nutrient {
          font-size: 24rpx;
          color: #888;
        }
      }

      .item-weight {
        margin-top: 12rpx;
        font-size: 24rpx;
        color: #999;
      }
    }
  }

  .summary-bar {
    background: linear-gradient(135deg, #4caf50, #81c784);
    border-radius: 16rpx;
    padding: 20rpx 24rpx;
    display: flex;
    flex-wrap: wrap;
    gap: 16rpx;

    .summary-item {
      font-size: 24rpx;
      color: #fff;
      font-weight: 500;
    }
  }
}

.bottom-actions {
  margin: 0 30rpx 20rpx;
  display: flex;
  gap: 20rpx;

  .action-btn {
    flex: 1;
    height: 80rpx;
    line-height: 80rpx;
    text-align: center;
    border-radius: 12rpx;
    font-size: 28rpx;
    border: none;
    background: #fff;
    color: #333;
    padding: 0;

    &.food-btn {
      border: 2rpx solid #4caf50;
      color: #4caf50;
    }

    &.custom-btn {
      border: 2rpx solid #2196f3;
      color: #2196f3;
    }
  }
}

.save-section {
  margin: 0 30rpx;

  .save-btn {
    width: 100%;
    height: 88rpx;
    background: linear-gradient(135deg, #4caf50, #81c784);
    color: #fff;
    font-size: 32rpx;
    border-radius: 44rpx;
    border: none;
  }

  .delete-btn {
    width: 100%;
    height: 88rpx;
    background: #fff;
    color: #f44336;
    font-size: 28rpx;
    border-radius: 44rpx;
    border: none;
    margin-top: 20rpx;
  }
}

// === 弹窗样式 ===
.custom-popup, .food-picker-popup {
  background: #fff;
  border-radius: 24rpx 24rpx 0 0;
  max-height: 85vh;
  display: flex;
  flex-direction: column;

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
    padding: 30rpx;
    max-height: 50vh;
    overflow-y: auto;
  }

  .popup-footer {
    display: flex;
    padding: 20rpx 30rpx;
    border-top: 1rpx solid #f0f0f0;
    gap: 20rpx;

    button {
      flex: 1;
      height: 80rpx;
      line-height: 80rpx;
      border-radius: 12rpx;
      font-size: 28rpx;
      border: none;
      padding: 0;
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

.form-item {
  margin-bottom: 24rpx;

  .form-label {
    display: block;
    font-size: 28rpx;
    color: #333;
    margin-bottom: 12rpx;
  }

  input {
    width: 100%;
    height: 80rpx;
    padding: 0 24rpx;
    background: #f5f5f5;
    border-radius: 12rpx;
    font-size: 28rpx;
    box-sizing: border-box;
  }

  .form-hint {
    font-size: 22rpx;
    color: #999;
    margin-top: 6rpx;
    display: block;
  }

  &.half {
    flex: 1;
    margin-bottom: 0;
  }
}

.form-row {
  display: flex;
  gap: 20rpx;
  margin-bottom: 24rpx;
}

.nutrition-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16rpx;
  margin-bottom: 24rpx;

  .nutrition-item {
    text-align: center;
    padding: 16rpx 0;
    background: #f5f5f5;
    border-radius: 12rpx;

    .value {
      display: block;
      font-size: 32rpx;
      font-weight: bold;
      color: #333;
    }

    .form-label {
      font-size: 20rpx;
      color: #999;
      margin-top: 6rpx;
    }
  }
}

.weight-input-wrap {
  display: flex;
  align-items: center;

  input {
    flex: 1;
    height: 80rpx;
    padding: 0 24rpx;
    background: #f5f5f5;
    border-radius: 12rpx;
    font-size: 28rpx;
  }

  .unit {
    margin-left: 16rpx;
    font-size: 28rpx;
    color: #666;
  }
}

.quick-weights {
  display: flex;
  gap: 16rpx;
  margin-top: 20rpx;
  flex-wrap: wrap;

  .weight-tag {
    padding: 12rpx 24rpx;
    background: #f5f5f5;
    border-radius: 20rpx;
    font-size: 24rpx;
    color: #666;

    &.active {
      background: #e8f5e9;
      color: #4caf50;
      font-weight: 500;
    }
  }
}

// === 食物选择器 ===
.picker-search {
  display: flex;
  align-items: center;
  margin: 20rpx;
  padding: 16rpx 24rpx;
  background: #f5f5f5;
  border-radius: 40rpx;

  input {
    flex: 1;
    font-size: 28rpx;
  }

  .clear-btn {
    font-size: 28rpx;
    color: #999;
    padding: 0 10rpx;
  }
}

.picker-tabs {
  white-space: nowrap;
  padding: 0 20rpx 20rpx;

  .picker-tab {
    display: inline-block;
    padding: 12rpx 24rpx;
    margin-right: 12rpx;
    font-size: 24rpx;
    color: #666;
    background: #f5f5f5;
    border-radius: 20rpx;

    &.active {
      background: #e8f5e9;
      color: #4caf50;
    }
  }
}

.picker-list {
  max-height: 50vh;
  padding: 0 20rpx;

  .loading-tip, .empty-tip {
    text-align: center;
    padding: 40rpx 0;
    color: #999;
    font-size: 26rpx;
  }

  .picker-food-item {
    background: #fff;
    border-radius: 12rpx;
    padding: 20rpx;
    margin-bottom: 16rpx;
    border: 1rpx solid #f0f0f0;

    .food-main {
      display: flex;
      justify-content: space-between;
      margin-bottom: 10rpx;

      .food-name {
        font-size: 28rpx;
        color: #333;
        font-weight: 500;
      }

      .food-calorie {
        font-size: 26rpx;
        color: #4caf50;
      }
    }

    .food-nutrients {
      display: flex;
      gap: 20rpx;
      font-size: 24rpx;
      color: #999;
    }
  }
}
</style>
