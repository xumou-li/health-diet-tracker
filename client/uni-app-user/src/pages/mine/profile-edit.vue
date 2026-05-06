<template>
  <view class="profile-edit-container">
    <scroll-view class="edit-scroll" scroll-y>
      <view class="form-section">
        <view class="form-item">
          <text class="label">身高(cm)</text>
          <input type="number" v-model="editForm.height_cm" placeholder="身高" />
        </view>
        <view class="form-item">
          <text class="label">体重(kg)</text>
          <input type="digit" v-model="editForm.weight_kg" placeholder="体重" />
        </view>
        <view class="form-item">
          <text class="label">活动水平</text>
          <picker mode="selector" :range="activityOptions" range-key="label" @change="onActivityChange">
            <view class="picker-value">{{ currentActivityText }}</view>
          </picker>
        </view>
        <view class="form-item">
          <text class="label">健康目标</text>
          <picker mode="selector" :range="goalOptions" range-key="label" @change="onGoalChange">
            <view class="picker-value">{{ currentGoalText }}</view>
          </picker>
        </view>
        <view class="form-item">
          <text class="label">热量系数</text>
          <view class="coefficient-field">
            <input
              class="coefficient-input"
              type="digit"
              :value="formattedCalorieCoefficient"
              placeholder="请输入热量系数"
              @input="onCalorieCoefficientInput"
            />
            <text class="coefficient-unit">倍</text>
          </view>
          <text class="form-tip">默认值会随目标切换：维持 1.00 / 减脂 0.85 / 增肌 1.15，可手动微调。</text>
        </view>
        <view class="form-item">
          <text class="label">每日热量预估</text>
          <view class="calorie-preview-card">
            <view class="preview-main">
              <text class="preview-value">{{ dailyCaloriePreviewText }}</text>
              <text class="preview-unit">kcal/天</text>
            </view>
            <text class="preview-detail">{{ dailyCaloriePreviewDetail }}</text>
          </view>
        </view>

        <!-- 营养素比例 -->
        <view class="form-item">
          <text class="label">营养素比例</text>
          <view class="ratio-edit-section">
            <view class="ratio-edit-item">
              <text class="edit-label">蛋白质</text>
              <text class="edit-percent">{{ ratioPercent('protein_ratio') }}%</text>
              <slider 
                :value="editForm.protein_ratio * 100" 
                @changing="onProteinChange"
                @change="onProteinChange"
                min="5" 
                max="50" 
                block-size="18"
              />
              <input
                class="ratio-input"
                type="number"
                :value="ratioPercent('protein_ratio')"
                @input="onRatioInput('protein_ratio', $event)"
              />
              <text class="ratio-unit">%</text>
            </view>
            <view class="ratio-edit-item">
              <text class="edit-label">脂肪</text>
              <text class="edit-percent">{{ ratioPercent('fat_ratio') }}%</text>
              <slider 
                :value="editForm.fat_ratio * 100" 
                @changing="onFatChange"
                @change="onFatChange"
                min="10" 
                max="45" 
                block-size="18"
              />
              <input
                class="ratio-input"
                type="number"
                :value="ratioPercent('fat_ratio')"
                @input="onRatioInput('fat_ratio', $event)"
              />
              <text class="ratio-unit">%</text>
            </view>
            <view class="ratio-edit-item">
              <text class="edit-label">碳水</text>
              <text class="edit-percent">{{ ratioPercent('carb_ratio') }}%</text>
              <slider 
                :value="editForm.carb_ratio * 100" 
                @changing="onCarbChange"
                @change="onCarbChange"
                min="20" 
                max="70" 
                block-size="18"
              />
              <input
                class="ratio-input"
                type="number"
                :value="ratioPercent('carb_ratio')"
                @input="onRatioInput('carb_ratio', $event)"
              />
              <text class="ratio-unit">%</text>
            </view>
            <view class="ratio-edit-total" :class="{ warning: !isRatioValid }">
              总计: {{ ratioTotal }}%
            </view>
          </view>
        </view>
      </view>
    </scroll-view>

    <!-- 底部按钮 -->
    <view class="bottom-bar">
      <button class="btn-cancel" @click="goBack">取消</button>
      <button class="btn-save" @click="saveProfile" :loading="saving">保存</button>
    </view>
  </view>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useUserStore } from '@/store/user'
import {
  calculateAgeFromBirthday,
  calculateBMR,
  calculateDailyCalorie,
  getDefaultCalorieCoefficient
} from '@/utils/nutrition'

const userStore = useUserStore()
const saving = ref(false)

const editForm = ref({
  height_cm: '',
  weight_kg: '',
  activity_level: 2,
  health_goal: 1,
  calorie_coefficient: 1,
  protein_ratio: 0.20,
  fat_ratio: 0.25,
  carb_ratio: 0.55
})

const defaultNutrientRatios = {
  1: { protein: 0.20, fat: 0.25, carb: 0.55 },
  2: { protein: 0.30, fat: 0.25, carb: 0.45 },
  3: { protein: 0.25, fat: 0.20, carb: 0.55 }
}

const activityOptions = [
  { value: 1, label: '久坐（几乎不运动）' },
  { value: 2, label: '轻度活动（每周1-3次）' },
  { value: 3, label: '中度活动（每周3-5次）' },
  { value: 4, label: '高强度（每周6-7次）' }
]

const goalOptions = [
  { value: 1, label: '维持体重' },
  { value: 2, label: '减脂' },
  { value: 3, label: '增肌' }
]

const profile = computed(() => userStore.profile)

const currentActivityText = computed(() => {
  const opt = activityOptions.find(o => o.value === editForm.value.activity_level)
  return opt?.label || '请选择'
})

const currentGoalText = computed(() => {
  const opt = goalOptions.find(o => o.value === editForm.value.health_goal)
  return opt?.label || '请选择'
})

const formattedCalorieCoefficient = computed(() => {
  const val = editForm.value.calorie_coefficient
  if (val === '' || val === null || val === undefined) return ''
  const numeric = Number(val)
  if (!Number.isFinite(numeric)) return ''
  return numeric.toFixed(2)
})

const dailyCaloriePreview = computed(() => {
  const heightCm = Number(editForm.value.height_cm)
  const weightKg = Number(editForm.value.weight_kg)
  const gender = Number(profile.value?.gender)
  const age = calculateAgeFromBirthday(profile.value?.birthday)
  const coefficient = Number(editForm.value.calorie_coefficient)

  if (!Number.isFinite(heightCm) || heightCm <= 0) return null
  if (!Number.isFinite(weightKg) || weightKg <= 0) return null
  if (!Number.isFinite(gender)) return null
  if (!Number.isFinite(age) || age <= 0) return null
  if (!Number.isFinite(coefficient) || coefficient <= 0) return null

  const bmr = calculateBMR(weightKg, heightCm, age, gender)
  const calorie = calculateDailyCalorie(
    bmr,
    editForm.value.activity_level,
    editForm.value.health_goal,
    coefficient
  )

  return {
    age,
    bmr,
    calorie,
    coefficient: coefficient.toFixed(2)
  }
})

const dailyCaloriePreviewText = computed(() => {
  if (!dailyCaloriePreview.value) return '--'
  return dailyCaloriePreview.value.calorie
})

const dailyCaloriePreviewDetail = computed(() => {
  if (!profile.value?.birthday || profile.value?.gender === undefined || profile.value?.gender === null) {
    return '缺少生日或性别信息，暂时无法预估每日热量。'
  }
  if (!dailyCaloriePreview.value) {
    return '请填写有效的身高、体重和热量系数后查看预估结果。'
  }
  const genderTextMap = { 0: '男性', 1: '女性', 2: '用户' }
  return `基于 ${dailyCaloriePreview.value.age} 岁${genderTextMap[profile.value.gender] || '用户'}、BMR ${dailyCaloriePreview.value.bmr} kcal、活动水平与系数 ${dailyCaloriePreview.value.coefficient} 实时计算。`
})

const isRatioValid = computed(() => {
  const total = editForm.value.protein_ratio + editForm.value.fat_ratio + editForm.value.carb_ratio
  return Math.abs(total - 1) < 0.01
})

const ratioTotal = computed(() => {
  return ratioPercent('protein_ratio') + ratioPercent('fat_ratio') + ratioPercent('carb_ratio')
})

const ratioPercent = (field) => {
  return Math.round((Number(editForm.value[field]) || 0) * 100)
}

const clampRatioPercent = (value, min, max) => {
  const numeric = Number(value)
  if (!Number.isFinite(numeric)) return min
  return Math.min(max, Math.max(min, Math.round(numeric)))
}

const goBack = () => {
  uni.navigateBack()
}

const onActivityChange = (e) => {
  editForm.value.activity_level = activityOptions[e.detail.value].value
}

const onGoalChange = (e) => {
  const goal = goalOptions[e.detail.value].value
  editForm.value.health_goal = goal
  editForm.value.calorie_coefficient = getDefaultCalorieCoefficient(goal)
  const ratios = defaultNutrientRatios[goal]
  editForm.value.protein_ratio = ratios.protein
  editForm.value.fat_ratio = ratios.fat
  editForm.value.carb_ratio = ratios.carb
}

const onCalorieCoefficientInput = (e) => {
  const inputValue = e?.detail?.value
  if (inputValue === '' || inputValue === null || inputValue === undefined) {
    editForm.value.calorie_coefficient = ''
    return
  }
  const numeric = Number(inputValue)
  if (!Number.isFinite(numeric)) return
  editForm.value.calorie_coefficient = Math.max(0.1, Math.min(3, Number(numeric.toFixed(2))))
}

const onProteinChange = (e) => {
  editForm.value.protein_ratio = clampRatioPercent(e.detail.value, 5, 50) / 100
}
const onFatChange = (e) => {
  editForm.value.fat_ratio = clampRatioPercent(e.detail.value, 10, 45) / 100
}
const onCarbChange = (e) => {
  editForm.value.carb_ratio = clampRatioPercent(e.detail.value, 20, 70) / 100
}

const onRatioInput = (field, e) => {
  const limits = {
    protein_ratio: [5, 50],
    fat_ratio: [10, 45],
    carb_ratio: [20, 70]
  }
  const [min, max] = limits[field]
  const inputValue = e?.detail?.value
  if (inputValue === '' || inputValue === null || inputValue === undefined) {
    editForm.value[field] = 0
    return
  }
  editForm.value[field] = clampRatioPercent(inputValue, min, max) / 100
}

const saveProfile = async () => {
  const {
    height_cm,
    weight_kg,
    activity_level,
    health_goal,
    calorie_coefficient,
    protein_ratio,
    fat_ratio,
    carb_ratio
  } = editForm.value

  if (!height_cm || height_cm < 100 || height_cm > 250) {
    return uni.showToast({ title: '请输入正确的身高', icon: 'none' })
  }
  if (!weight_kg || weight_kg < 30 || weight_kg > 300) {
    return uni.showToast({ title: '请输入正确的体重', icon: 'none' })
  }
  if (!isRatioValid.value) {
    return uni.showToast({ title: '营养素比例总计应为100%', icon: 'none' })
  }
  if (!calorie_coefficient || Number(calorie_coefficient) <= 0) {
    return uni.showToast({ title: '请输入正确的热量系数', icon: 'none' })
  }

  saving.value = true
  try {
    await userStore.updateUserProfile({
      height_cm: parseInt(height_cm),
      weight_kg: parseFloat(weight_kg),
      activity_level,
      health_goal,
      calorie_coefficient: Number(Number(calorie_coefficient).toFixed(2)),
      protein_ratio,
      fat_ratio,
      carb_ratio
    })

    uni.showToast({ title: '保存成功', icon: 'success' })
    await userStore.fetchProfile()
    setTimeout(() => {
      uni.navigateBack()
    }, 800)
  } catch (error) {
    console.error('保存失败:', error)
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  const profileGoal = profile.value?.health_goal || 1
  const storedCoefficient = Number(profile.value?.calorie_coefficient)
  const calorieCoefficient = Number.isFinite(storedCoefficient) && storedCoefficient > 0
    ? storedCoefficient
    : getDefaultCalorieCoefficient(profileGoal)

  editForm.value = {
    height_cm: profile.value?.height_cm || '',
    weight_kg: profile.value?.weight_kg || '',
    activity_level: profile.value?.activity_level || 2,
    health_goal: profileGoal,
    calorie_coefficient: calorieCoefficient,
    protein_ratio: profile.value?.protein_ratio ?? 0.20,
    fat_ratio: profile.value?.fat_ratio ?? 0.25,
    carb_ratio: profile.value?.carb_ratio ?? 0.55
  }
})
</script>

<style lang="scss" scoped>
.profile-edit-container {
  height: 100vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  background: #f5f5f5;
}

.edit-scroll {
  flex: 1;
  height: 0;
  padding: 20rpx 30rpx 40rpx;
  box-sizing: border-box;
}

.form-section {
  .form-item {
    background: #fff;
    border-radius: 16rpx;
    padding: 28rpx;
    margin-bottom: 20rpx;
    box-sizing: border-box;
    overflow: hidden;

    .label {
      display: block;
      font-size: 28rpx;
      font-weight: 500;
      color: #333;
      margin-bottom: 16rpx;
    }

    input {
      height: 72rpx;
      line-height: 72rpx;
      font-size: 28rpx;
      padding: 0 20rpx;
      background: #f5f5f5;
      border-radius: 12rpx;
      width: 100%;
      box-sizing: border-box;
    }

    .picker-value {
      height: 72rpx;
      line-height: 72rpx;
      font-size: 28rpx;
      padding: 0 20rpx;
      background: #f5f5f5;
      border-radius: 12rpx;
      color: #333;
    }

    .form-tip {
      display: block;
      font-size: 22rpx;
      color: #999;
      margin-top: 12rpx;
      line-height: 1.5;
    }
  }
}

.coefficient-field {
  display: flex;
  align-items: center;

  .coefficient-input {
    flex: 1;
    min-width: 0;
  }

  .coefficient-unit {
    flex-shrink: 0;
    margin-left: 12rpx;
    font-size: 28rpx;
    color: #666;
  }
}

.calorie-preview-card {
  background: linear-gradient(135deg, #e8f5e9 0%, #f1f8e9 100%);
  border-radius: 16rpx;
  padding: 24rpx;
  text-align: center;

  .preview-main {
    margin-bottom: 8rpx;

    .preview-value {
      font-size: 48rpx;
      font-weight: bold;
      color: #2e7d32;
    }

    .preview-unit {
      font-size: 24rpx;
      color: #4caf50;
      margin-left: 8rpx;
    }
  }

  .preview-detail {
    font-size: 22rpx;
    color: #666;
    line-height: 1.5;
  }
}

.ratio-edit-section {
  overflow: hidden;
  .ratio-edit-item {
    display: flex;
    align-items: center;
    margin-bottom: 20rpx;

    .edit-label {
      width: 90rpx;
      font-size: 24rpx;
      color: #333;
      font-weight: 500;
      flex-shrink: 0;
    }

    .edit-percent {
      width: 50rpx;
      font-size: 24rpx;
      color: #4caf50;
      font-weight: bold;
      text-align: center;
      flex-shrink: 0;
    }

    slider {
      flex: 1;
      min-width: 0;
      margin: 0 8rpx;
    }

    .ratio-input {
      width: 72rpx;
      flex-shrink: 0;
      font-size: 22rpx !important;
      height: 56rpx !important;
      line-height: 56rpx !important;
      padding: 0 !important;
      text-align: center;
    }

    .ratio-unit {
      font-size: 22rpx;
      color: #999;
      margin-left: 4rpx;
      flex-shrink: 0;
    }
  }

  .ratio-edit-total {
    text-align: center;
    font-size: 28rpx;
    font-weight: bold;
    color: #4caf50;
    padding: 16rpx 0 8rpx;
    border-top: 1rpx solid #f0f0f0;

    &.warning {
      color: #f44336;
    }
  }
}

.bottom-bar {
  flex-shrink: 0;
  display: flex;
  gap: 20rpx;
  padding: 20rpx 30rpx;
  padding-bottom: calc(20rpx + env(safe-area-inset-bottom));
  background: #fff;
  border-top: 1rpx solid #f0f0f0;
  box-sizing: border-box;

  button {
    flex: 1;
    height: 88rpx;
    border-radius: 44rpx;
    font-size: 30rpx;
    font-weight: 500;
    line-height: 88rpx;
    padding: 0;
    border: none;
  }

  .btn-cancel {
    background: #f5f5f5;
    color: #666;
  }

  .btn-save {
    background: linear-gradient(135deg, #4caf50 0%, #81c784 100%);
    color: #fff;
  }
}
</style>
