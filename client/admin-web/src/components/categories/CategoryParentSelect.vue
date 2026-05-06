<template>
  <el-select
    :model-value="modelValue"
    :placeholder="placeholder"
    :disabled="disabled"
    :clearable="clearable"
    filterable
    @update:model-value="emit('update:modelValue', $event)"
  >
    <el-option
      v-for="option in availableOptions"
      :key="option.code"
      :label="getOptionLabel(option)"
      :value="option.code"
    >
      <div class="category-option">
        <span class="category-option__name">{{ getOptionLabel(option) }}</span>
        <span class="category-option__meta">{{ option.code }}</span>
      </div>
    </el-option>
  </el-select>
</template>

<script setup>
import { computed } from 'vue'
import { collectDescendantCodes, flattenCategoryTree } from '@/utils/category'

const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  },
  categories: {
    type: Array,
    default: () => []
  },
  excludeCode: {
    type: String,
    default: ''
  },
  placeholder: {
    type: String,
    default: '请选择父级分类'
  },
  disabled: {
    type: Boolean,
    default: false
  },
  clearable: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['update:modelValue'])

const unavailableCodes = computed(() => {
  if (!props.excludeCode) {
    return []
  }

  return [props.excludeCode, ...collectDescendantCodes(props.categories, props.excludeCode)]
})

const availableOptions = computed(() => flattenCategoryTree(props.categories).filter(
  (category) => !unavailableCodes.value.includes(category.code)
))

function getOptionLabel(option) {
  const indent = option.depth > 0 ? `${'— '.repeat(option.depth)}` : ''
  return `${indent}${option.name}`
}
</script>

<style scoped>
.category-option {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
}

.category-option__name {
  color: var(--admin-text-primary);
}

.category-option__meta {
  color: var(--admin-text-tertiary);
  font-size: var(--font-size-xs);
}
</style>
