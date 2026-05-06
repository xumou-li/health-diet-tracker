<template>
  <el-dialog
    v-model="dialogVisible"
    :title="dialogTitle"
    width="860px"
    destroy-on-close
  >
    <el-form ref="formRef" :model="form" :rules="rules" label-position="top" class="food-form">
      <section class="food-form__section">
        <div class="food-form__section-title">基础信息</div>
        <div class="food-form__grid food-form__grid--two">
          <el-form-item label="食物名称" prop="name">
            <el-input v-model.trim="form.name" maxlength="100" placeholder="请输入食物名称" />
          </el-form-item>

          <el-form-item label="审核状态" prop="is_approved">
            <el-switch
              v-model="form.is_approved"
              inline-prompt
              active-text="已审核"
              inactive-text="待审核"
            />
          </el-form-item>

          <el-form-item label="一级分类" prop="category_code">
            <el-select
              v-model="form.category_code"
              clearable
              filterable
              placeholder="请选择一级分类"
              @change="handleCategoryChange"
            >
              <el-option
                v-for="item in rootCategories"
                :key="item.code"
                :label="item.name"
                :value="item.code"
              />
            </el-select>
          </el-form-item>

          <el-form-item label="二级分类" prop="sub_category_code">
            <el-select
              v-model="form.sub_category_code"
              clearable
              filterable
              :disabled="!form.category_code"
              placeholder="请先选择一级分类"
            >
              <el-option
                v-for="item in subCategoryOptions"
                :key="item.code"
                :label="item.name"
                :value="item.code"
              />
            </el-select>
          </el-form-item>

          <el-form-item label="可食部分 (%)" prop="edible_portion">
            <el-input-number v-model="form.edible_portion" :min="0" :max="100" :step="1" :precision="0" />
          </el-form-item>

          <el-form-item label="热量 (kcal / 100g)" prop="calorie_per_100g">
            <el-input-number v-model="form.calorie_per_100g" :min="0" :step="1" :precision="0" />
          </el-form-item>
        </div>
      </section>

      <section class="food-form__section">
        <div class="food-form__section-title">核心营养素</div>
        <div class="food-form__grid food-form__grid--three">
          <el-form-item label="蛋白质 (g)" prop="protein_per_100g">
            <el-input-number v-model="form.protein_per_100g" :min="0" :step="0.1" :precision="2" />
          </el-form-item>

          <el-form-item label="碳水 (g)" prop="carb_per_100g">
            <el-input-number v-model="form.carb_per_100g" :min="0" :step="0.1" :precision="2" />
          </el-form-item>

          <el-form-item label="脂肪 (g)" prop="fat_per_100g">
            <el-input-number v-model="form.fat_per_100g" :min="0" :step="0.1" :precision="2" />
          </el-form-item>
        </div>
      </section>

      <section class="food-form__section">
        <div class="food-form__section-title">扩展营养字段</div>
        <div class="food-form__grid food-form__grid--three">
          <el-form-item label="膳食纤维 (g)" prop="fiber_per_100g">
            <el-input-number v-model="form.fiber_per_100g" :min="0" :step="0.1" :precision="2" />
          </el-form-item>

          <el-form-item label="胆固醇 (mg)" prop="cholesterol_per_100g">
            <el-input-number v-model="form.cholesterol_per_100g" :min="0" :step="0.1" :precision="2" />
          </el-form-item>

          <el-form-item label="钠 (mg)" prop="sodium_per_100g">
            <el-input-number v-model="form.sodium_per_100g" :min="0" :step="0.1" :precision="2" />
          </el-form-item>

          <el-form-item label="钙 (mg)" prop="calcium_per_100g">
            <el-input-number v-model="form.calcium_per_100g" :min="0" :step="0.1" :precision="2" />
          </el-form-item>

          <el-form-item label="铁 (mg)" prop="iron_per_100g">
            <el-input-number v-model="form.iron_per_100g" :min="0" :step="0.1" :precision="2" />
          </el-form-item>

          <el-form-item label="维生素 C (mg)" prop="vitamin_c_per_100g">
            <el-input-number v-model="form.vitamin_c_per_100g" :min="0" :step="0.1" :precision="2" />
          </el-form-item>
        </div>
      </section>
    </el-form>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSubmit">保存食物</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { getChildCategories, getRootCategories } from '@/utils/category'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  mode: {
    type: String,
    default: 'create'
  },
  food: {
    type: Object,
    default: null
  },
  categories: {
    type: Array,
    default: () => []
  },
  saving: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue', 'submit'])

const formRef = ref(null)
const form = reactive({
  name: '',
  category_code: '',
  sub_category_code: '',
  edible_portion: 100,
  calorie_per_100g: 0,
  protein_per_100g: 0,
  carb_per_100g: 0,
  fat_per_100g: 0,
  fiber_per_100g: null,
  cholesterol_per_100g: null,
  sodium_per_100g: null,
  calcium_per_100g: null,
  iron_per_100g: null,
  vitamin_c_per_100g: null,
  is_approved: false
})

const rules = {
  name: [{ required: true, message: '请输入食物名称', trigger: 'blur' }],
  calorie_per_100g: [{ required: true, message: '请输入热量值', trigger: 'change' }]
}

const dialogVisible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const dialogTitle = computed(() => (props.mode === 'edit' ? '编辑食物' : '新增食物'))

const rootCategories = computed(() => getRootCategories(props.categories))
const subCategoryOptions = computed(() => getChildCategories(props.categories, form.category_code))

watch(
  () => [props.modelValue, props.food, props.mode],
  () => {
    if (!props.modelValue) {
      resetForm()
      return
    }

    const food = props.food || {}
    form.name = food.name || ''
    form.category_code = food.category_code || ''
    form.sub_category_code = food.sub_category_code || ''
    form.edible_portion = normalizeInteger(food.edible_portion, 100)
    form.calorie_per_100g = normalizeInteger(food.calorie_per_100g, 0)
    form.protein_per_100g = normalizeNumber(food.protein_per_100g, 0)
    form.carb_per_100g = normalizeNumber(food.carb_per_100g, 0)
    form.fat_per_100g = normalizeNumber(food.fat_per_100g, 0)
    form.fiber_per_100g = normalizeNullableNumber(food.fiber_per_100g)
    form.cholesterol_per_100g = normalizeNullableNumber(food.cholesterol_per_100g)
    form.sodium_per_100g = normalizeNullableNumber(food.sodium_per_100g)
    form.calcium_per_100g = normalizeNullableNumber(food.calcium_per_100g)
    form.iron_per_100g = normalizeNullableNumber(food.iron_per_100g)
    form.vitamin_c_per_100g = normalizeNullableNumber(food.vitamin_c_per_100g)
    form.is_approved = food.is_approved === true
  },
  { immediate: true }
)

function resetForm() {
  form.name = ''
  form.category_code = ''
  form.sub_category_code = ''
  form.edible_portion = 100
  form.calorie_per_100g = 0
  form.protein_per_100g = 0
  form.carb_per_100g = 0
  form.fat_per_100g = 0
  form.fiber_per_100g = null
  form.cholesterol_per_100g = null
  form.sodium_per_100g = null
  form.calcium_per_100g = null
  form.iron_per_100g = null
  form.vitamin_c_per_100g = null
  form.is_approved = false
}

function normalizeNullableNumber(value) {
  return value === '' || value === null || typeof value === 'undefined'
    ? null
    : Number(value)
}

function normalizeNumber(value, fallback) {
  const number = Number(value)
  return Number.isFinite(number) ? number : fallback
}

function normalizeInteger(value, fallback) {
  const number = Number(value)
  return Number.isFinite(number) ? Math.round(number) : fallback
}

function handleCategoryChange(value) {
  if (!value) {
    form.sub_category_code = ''
    return
  }

  const matchedSubCategory = subCategoryOptions.value.some((item) => item.code === form.sub_category_code)

  if (!matchedSubCategory) {
    form.sub_category_code = ''
  }
}

async function handleSubmit() {
  if (!formRef.value) {
    return
  }

  const valid = await formRef.value.validate().catch(() => false)

  if (!valid) {
    return
  }

  emit('submit', {
    name: form.name.trim(),
    category_code: form.category_code || null,
    sub_category_code: form.sub_category_code || null,
    edible_portion: normalizeInteger(form.edible_portion, 100),
    calorie_per_100g: normalizeInteger(form.calorie_per_100g, 0),
    protein_per_100g: normalizeNumber(form.protein_per_100g, 0),
    carb_per_100g: normalizeNumber(form.carb_per_100g, 0),
    fat_per_100g: normalizeNumber(form.fat_per_100g, 0),
    fiber_per_100g: normalizeNullableNumber(form.fiber_per_100g),
    cholesterol_per_100g: normalizeNullableNumber(form.cholesterol_per_100g),
    sodium_per_100g: normalizeNullableNumber(form.sodium_per_100g),
    calcium_per_100g: normalizeNullableNumber(form.calcium_per_100g),
    iron_per_100g: normalizeNullableNumber(form.iron_per_100g),
    vitamin_c_per_100g: normalizeNullableNumber(form.vitamin_c_per_100g),
    is_approved: Boolean(form.is_approved)
  })
}
</script>

<style scoped>
.food-form {
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
}

.food-form__section {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  padding: var(--space-5);
  border: 1px solid rgba(215, 228, 216, 0.9);
  border-radius: var(--radius-md);
  background: rgba(255, 255, 255, 0.7);
}

.food-form__section-title {
  font-size: var(--font-size-lg);
  font-weight: 700;
}

.food-form__grid {
  display: grid;
  gap: var(--space-4);
}

.food-form__grid--two {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.food-form__grid--three {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-3);
}

.food-form :deep(.el-select),
.food-form :deep(.el-input-number) {
  width: 100%;
}

@media (max-width: 900px) {
  .food-form__grid--two,
  .food-form__grid--three {
    grid-template-columns: 1fr;
  }
}
</style>
