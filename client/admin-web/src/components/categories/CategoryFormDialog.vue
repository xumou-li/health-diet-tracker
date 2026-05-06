<template>
  <el-dialog
    v-model="dialogVisible"
    :title="dialogTitle"
    width="560px"
    destroy-on-close
  >
    <el-form ref="formRef" :model="form" :rules="rules" label-position="top" class="category-form">
      <el-form-item label="分类编码" prop="code">
        <el-input
          v-model.trim="form.code"
          :disabled="isEdit"
          maxlength="10"
          placeholder="例如：fruit"
        />
      </el-form-item>

      <el-form-item label="分类名称" prop="name">
        <el-input v-model.trim="form.name" maxlength="50" placeholder="请输入分类名称" />
      </el-form-item>

      <el-form-item label="父级分类" prop="parent_code">
        <CategoryParentSelect
          v-model="form.parent_code"
          :categories="categories"
          :exclude-code="form.code"
          placeholder="不选择则创建为一级分类"
        />
      </el-form-item>

      <el-form-item label="排序值" prop="sort_order">
        <el-input-number v-model="form.sort_order" :min="0" :step="1" :precision="0" />
      </el-form-item>
    </el-form>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSubmit">保存分类</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import CategoryParentSelect from './CategoryParentSelect.vue'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  mode: {
    type: String,
    default: 'create'
  },
  category: {
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
  code: '',
  name: '',
  parent_code: '',
  sort_order: 0
})

const rules = {
  code: [{ required: true, message: '请输入分类编码', trigger: 'blur' }],
  name: [{ required: true, message: '请输入分类名称', trigger: 'blur' }]
}

const isEdit = computed(() => props.mode === 'edit')
const dialogTitle = computed(() => (isEdit.value ? '编辑分类' : '新增分类'))

const dialogVisible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

watch(
  () => [props.modelValue, props.category, props.mode],
  () => {
    const category = props.category || {}

    form.code = category.code || ''
    form.name = category.name || ''
    form.parent_code = category.parent_code || ''
    form.sort_order = Number(category.sort_order) || 0

    if (!props.modelValue) {
      form.code = ''
      form.name = ''
      form.parent_code = ''
      form.sort_order = 0
    }
  },
  { immediate: true }
)

async function handleSubmit() {
  if (!formRef.value) {
    return
  }

  const valid = await formRef.value.validate().catch(() => false)

  if (!valid) {
    return
  }

  emit('submit', {
    code: form.code.trim(),
    name: form.name.trim(),
    parent_code: form.parent_code || null,
    sort_order: Number(form.sort_order) || 0
  })
}
</script>

<style scoped>
.category-form {
  display: flex;
  flex-direction: column;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-3);
}

.category-form :deep(.el-input-number) {
  width: 100%;
}
</style>
