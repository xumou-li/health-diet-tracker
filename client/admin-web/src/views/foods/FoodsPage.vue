<template>
  <div class="page-shell">
    <section class="page-header">
      <div class="page-header__content">
        <div class="page-eyebrow">食物管理</div>
        <h1 class="page-title">食物资料库与审核工作台</h1>
        <p class="page-description">
          支持关键字、一级分类和审核状态筛选，并直接在列表中完成新增、编辑、删除和审核通过操作。
          页面保留后端的 snake_case 字段结构，已兼容
          <code>is_approved</code>、<code>created_by</code>、<code>created_at</code>
          等管理端字段。
        </p>
      </div>

      <div class="page-header__actions">
        <el-button type="primary" @click="openCreateDialog">新增食物</el-button>
      </div>
    </section>

    <section class="metric-grid">
      <article class="metric-card">
        <span class="metric-card__label">食物总数</span>
        <span class="metric-card__value">{{ total }}</span>
        <span class="metric-card__hint">使用后端分页总数字段，便于管理员掌握食物库规模。</span>
      </article>

      <article class="metric-card">
        <span class="metric-card__label">当前页记录</span>
        <span class="metric-card__value">{{ foods.length }}</span>
        <span class="metric-card__hint">当前筛选条件下的页面结果数，可配合分页器快速翻页巡检。</span>
      </article>

      <article class="metric-card">
        <span class="metric-card__label">当前页待审核</span>
        <span class="metric-card__value">{{ pendingCount }}</span>
        <span class="metric-card__hint">未明确返回审核字段时会按待同步显示，避免界面因旧接口缺字段而失真。</span>
      </article>

      <article class="metric-card">
        <span class="metric-card__label">可用分类</span>
        <span class="metric-card__value">{{ rootCategories.length }}</span>
        <span class="metric-card__hint">筛选和表单都复用同一份分类数据，减少维护分叉。</span>
      </article>
    </section>

    <el-card class="panel-card section-card" shadow="never">
      <template #header>
        <div>
          <h2 class="section-title">筛选条件</h2>
          <p class="section-description">支持关键字、一级分类、审核状态和每页条数控制。</p>
        </div>
      </template>

      <el-form label-position="top" class="filter-form" @submit.prevent>
        <div class="filter-form__grid">
          <el-form-item label="关键字">
            <el-input
              v-model.trim="filters.keyword"
              clearable
              placeholder="按食物名称搜索"
              @keyup.enter="handleSearch"
            />
          </el-form-item>

          <el-form-item label="一级分类">
            <el-select v-model="filters.category_code" clearable filterable placeholder="全部分类">
              <el-option
                v-for="item in rootCategories"
                :key="item.code"
                :label="item.name"
                :value="item.code"
              />
            </el-select>
          </el-form-item>

          <el-form-item label="审核状态">
            <el-select v-model="filters.approved" placeholder="全部状态">
              <el-option label="全部" value="all" />
              <el-option label="仅已审核" value="true" />
              <el-option label="仅待审核" value="false" />
            </el-select>
          </el-form-item>

          <el-form-item label="每页条数">
            <el-select v-model="filters.per_page" placeholder="每页条数">
              <el-option v-for="size in pageSizes" :key="size" :label="`${size} 条`" :value="size" />
            </el-select>
          </el-form-item>
        </div>

        <div class="filter-form__actions">
          <el-button type="primary" :loading="loading" @click="handleSearch">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </div>
      </el-form>
    </el-card>

    <el-card class="panel-card section-card" shadow="never">
      <template #header>
        <div class="card-header">
          <div>
            <h2 class="section-title">食物列表</h2>
            <p class="section-description">操作列支持单条审核通过、编辑和删除，适合课程项目演示与实际录入。</p>
          </div>

          <el-button :loading="loading" @click="loadFoods">刷新列表</el-button>
        </div>
      </template>

      <el-table v-loading="loading" :data="foods" row-key="id" empty-text="暂无食物数据">
        <el-table-column label="食物信息" min-width="240">
          <template #default="{ row }">
            <div class="food-name-cell">
              <span class="food-name-cell__title">{{ row.name }}</span>
              <span class="food-name-cell__meta">ID {{ row.id }}</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="分类" min-width="220">
          <template #default="{ row }">
            <div class="category-cell">
              <el-tag v-if="row.category_code" effect="light">{{ getCategoryLabel(row.category_code) || row.category_code }}</el-tag>
              <el-tag v-if="row.sub_category_code" type="success" effect="light">
                {{ getCategoryLabel(row.sub_category_code) || row.sub_category_code }}
              </el-tag>
              <span class="table-muted">{{ getFoodCategoryPath(row) || '未分类' }}</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="每 100g 营养" min-width="260">
          <template #default="{ row }">
            <div class="nutrition-grid">
              <span>热量 {{ row.calorie_per_100g ?? '--' }} kcal</span>
              <span>蛋白 {{ formatNutrient(row.protein_per_100g) }} g</span>
              <span>碳水 {{ formatNutrient(row.carb_per_100g) }} g</span>
              <span>脂肪 {{ formatNutrient(row.fat_per_100g) }} g</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="可食部分" width="110">
          <template #default="{ row }">
            <span>{{ row.edible_portion ?? '--' }}%</span>
          </template>
        </el-table-column>

        <el-table-column label="审核状态" width="140">
          <template #default="{ row }">
            <el-tag :type="getApprovalTagType(row)" effect="light">{{ getApprovalLabel(row) }}</el-tag>
          </template>
        </el-table-column>

        <el-table-column label="创建信息" min-width="180">
          <template #default="{ row }">
            <div class="meta-stack">
              <span>管理员：{{ row.created_by ?? '--' }}</span>
              <span>{{ formatDateTime(row.created_at) }}</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <div class="action-group">
              <el-button link type="primary" @click="openEditDialog(row)">编辑</el-button>
              <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
              <el-button
                v-if="row.is_approved !== true"
                link
                type="success"
                @click="handleApprove(row)"
              >
                审核通过
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <div class="table-footer">
        <el-pagination
          background
          layout="total, sizes, prev, pager, next"
          :current-page="filters.page"
          :page-size="filters.per_page"
          :page-sizes="pageSizes"
          :total="total"
          @current-change="handlePageChange"
          @size-change="handleSizeChange"
        />
      </div>
    </el-card>

    <FoodFormDialog
      v-model="dialogVisible"
      :mode="dialogMode"
      :food="currentFood"
      :categories="categories"
      :saving="saving"
      @submit="handleSubmit"
    />
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getCategories } from '@/api/categories'
import { approveFood, createFood, deleteFood, getFoods, updateFood } from '@/api/foods'
import FoodFormDialog from '@/components/foods/FoodFormDialog.vue'
import { getCategoryName, getCategoryPathLabel, getRootCategories } from '@/utils/category'

const pageSizes = [10, 20, 50, 100]

const loading = ref(false)
const saving = ref(false)
const dialogVisible = ref(false)
const dialogMode = ref('create')
const currentFood = ref(null)
const foods = ref([])
const categories = ref([])
const total = ref(0)

const filters = reactive({
  keyword: '',
  category_code: '',
  approved: 'all',
  page: 1,
  per_page: 10
})

const rootCategories = computed(() => getRootCategories(categories.value))
const pendingCount = computed(() => foods.value.filter((item) => item.is_approved !== true).length)

function getCategoryLabel(code) {
  return getCategoryName(categories.value, code)
}

function getFoodCategoryPath(food) {
  if (food.sub_category_code) {
    return getCategoryPathLabel(categories.value, food.sub_category_code)
  }

  if (food.category_code) {
    return getCategoryPathLabel(categories.value, food.category_code)
  }

  return ''
}

function getApprovalLabel(food) {
  if (food.is_approved === true) {
    return '已审核'
  }

  if (food.is_approved === false) {
    return '待审核'
  }

  return '状态待同步'
}

function getApprovalTagType(food) {
  if (food.is_approved === true) {
    return 'success'
  }

  if (food.is_approved === false) {
    return 'warning'
  }

  return 'info'
}

function formatNutrient(value) {
  return value ?? 0
}

function formatDateTime(value) {
  if (!value) {
    return '--'
  }

  const date = new Date(value)

  if (Number.isNaN(date.getTime())) {
    return '--'
  }

  return date.toLocaleString('zh-CN', {
    hour12: false,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

async function loadCategories() {
  const data = await getCategories()
  categories.value = Array.isArray(data) ? data : []
}

async function loadFoods() {
  loading.value = true

  try {
    const data = await getFoods({
      keyword: filters.keyword || undefined,
      category_code: filters.category_code || undefined,
      approved: filters.approved,
      page: filters.page,
      per_page: filters.per_page
    })

    foods.value = Array.isArray(data?.items) ? data.items : []
    total.value = Number(data?.total) || 0
  } finally {
    loading.value = false
  }
}

function openCreateDialog() {
  dialogMode.value = 'create'
  currentFood.value = null
  dialogVisible.value = true
}

function openEditDialog(food) {
  dialogMode.value = 'edit'
  currentFood.value = food
  dialogVisible.value = true
}

async function handleSubmit(payload) {
  saving.value = true

  try {
    if (dialogMode.value === 'create') {
      await createFood(payload)
      ElMessage.success('食物创建成功')
      filters.page = 1
    } else {
      await updateFood(currentFood.value.id, payload)
      ElMessage.success('食物更新成功')
    }

    dialogVisible.value = false
    await loadFoods()
  } finally {
    saving.value = false
  }
}

async function handleDelete(food) {
  await ElMessageBox.confirm(`确认删除食物「${food.name}」吗？该操作不可撤销。`, '删除确认', {
    type: 'warning'
  })

  await deleteFood(food.id)
  ElMessage.success('食物删除成功')

  if (foods.value.length === 1 && filters.page > 1) {
    filters.page -= 1
  }

  await loadFoods()
}

async function handleApprove(food) {
  await approveFood(food.id)
  ElMessage.success(`已通过「${food.name}」的审核`)
  await loadFoods()
}

function handleSearch() {
  filters.page = 1
  loadFoods()
}

function handleReset() {
  filters.keyword = ''
  filters.category_code = ''
  filters.approved = 'all'
  filters.page = 1
  filters.per_page = 10
  loadFoods()
}

function handlePageChange(page) {
  filters.page = page
  loadFoods()
}

function handleSizeChange(size) {
  filters.per_page = size
  filters.page = 1
  loadFoods()
}

onMounted(async () => {
  await loadCategories()
  await loadFoods()
})
</script>

<style scoped>
.page-header__actions {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.filter-form {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.filter-form__grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: var(--space-4);
}

.filter-form__actions,
.card-header,
.table-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-4);
}

.food-name-cell,
.category-cell,
.meta-stack,
.action-group {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.food-name-cell__title {
  font-weight: 700;
}

.food-name-cell__meta,
.table-muted,
.meta-stack {
  color: var(--admin-text-secondary);
  font-size: var(--font-size-sm);
}

.category-cell {
  align-items: flex-start;
}

.nutrition-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--space-2);
  color: var(--admin-text-secondary);
  font-size: var(--font-size-sm);
}

.action-group {
  align-items: flex-start;
}

.table-footer {
  margin-top: var(--space-5);
}

.filter-form :deep(.el-select) {
  width: 100%;
}

@media (max-width: 1200px) {
  .filter-form__grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 768px) {
  .filter-form__grid {
    grid-template-columns: 1fr;
  }

  .filter-form__actions,
  .card-header,
  .table-footer {
    flex-direction: column;
    align-items: stretch;
  }

  .nutrition-grid {
    grid-template-columns: 1fr;
  }
}
</style>
