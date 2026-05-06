<template>
  <div class="page-shell">
    <section class="page-header">
      <div class="page-header__content">
        <div class="page-eyebrow">分类管理</div>
        <h1 class="page-title">食物分类结构维护</h1>
        <p class="page-description">
          统一管理分类编码、父子关系和排序值。页面左侧提供完整列表编辑，右侧同步展示按
          <code>parent_code</code>
          推导的结构预览，便于在演示和日常维护时快速确认层级是否正确。
        </p>
      </div>

      <div class="page-header__actions">
        <el-button type="primary" @click="openCreateDialog">新增分类</el-button>
      </div>
    </section>

    <section class="metric-grid">
      <article class="metric-card">
        <span class="metric-card__label">分类总数</span>
        <span class="metric-card__value">{{ categories.length }}</span>
        <span class="metric-card__hint">按后端默认排序读取全部分类，适合直接做维护入口。</span>
      </article>

      <article class="metric-card">
        <span class="metric-card__label">一级分类</span>
        <span class="metric-card__value">{{ rootCategoryCount }}</span>
        <span class="metric-card__hint">父级为空或父级缺失的分类会归入顶层，避免树结构断链。</span>
      </article>

      <article class="metric-card">
        <span class="metric-card__label">子级分类</span>
        <span class="metric-card__value">{{ childCategoryCount }}</span>
        <span class="metric-card__hint">可直接在弹窗中切换父级，列表会同步反映新的层级位置。</span>
      </article>

      <article class="metric-card">
        <span class="metric-card__label">最大层级</span>
        <span class="metric-card__value">{{ maxDepthText }}</span>
        <span class="metric-card__hint">当前实现支持继续向下拓展，但后台演示场景优先以两级分类为主。</span>
      </article>
    </section>

    <section class="panel-grid">
      <el-card class="panel-card section-card" shadow="never" style="grid-column: span 8;">
        <template #header>
          <div class="card-header">
            <div>
              <h2 class="section-title">分类列表</h2>
              <p class="section-description">保留后端字段命名与排序规则，编辑时仅提交支持更新的字段。</p>
            </div>

            <el-button :loading="loading" @click="loadCategories">刷新列表</el-button>
          </div>
        </template>

        <el-table
          v-loading="loading"
          :data="tableRows"
          row-key="id"
          empty-text="暂无分类数据"
          :tree-props="{ children: 'children', hasChildren: 'hasChildren' }"
          default-expand-all
          :row-class-name="getRowClass"
        >
          <el-table-column label="分类名称" min-width="220">
            <template #default="{ row }">
              <div class="category-name-cell">
                <span class="category-name-cell__title">{{ row.name }}</span>
                <div class="category-name-cell__meta">
                  <el-tag effect="plain">{{ row.code }}</el-tag>
                  <el-tag :type="row.depth === 0 ? 'success' : 'info'" effect="light">
                    {{ getDepthLabel(row.depth) }}
                  </el-tag>
                </div>
              </div>
            </template>
          </el-table-column>

          <el-table-column label="父级分类" min-width="160">
            <template #default="{ row }">
              <span>{{ row.parent_code ? getParentName(row.parent_code) : '—' }}</span>
            </template>
          </el-table-column>

          <el-table-column label="层级路径" min-width="220">
            <template #default="{ row }">
              <span class="table-muted">{{ row.path_label || row.name }}</span>
            </template>
          </el-table-column>

          <el-table-column label="操作" width="100" align="center">
            <template #default="{ row }">
              <el-button link type="primary" size="small" @click="openEditDialog(row)">编辑</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>

      <el-card class="panel-card section-card" shadow="never" style="grid-column: span 4;">
        <template #header>
          <div>
            <h2 class="section-title">层级预览</h2>
            <p class="section-description">树形预览基于平铺列表即时计算，不依赖额外组件库。</p>
          </div>
        </template>

        <div class="tree-panel">
          <el-tree
            v-if="treeNodes.length"
            :data="treeNodes"
            node-key="code"
            default-expand-all
            :expand-on-click-node="false"
          >
            <template #default="{ data }">
              <div class="tree-node">
                <span class="tree-node__label">{{ data.name }}</span>
                <span class="tree-node__meta">{{ data.code }}</span>
              </div>
            </template>
          </el-tree>

          <el-empty v-else description="暂无分类结构" :image-size="120" />
        </div>
      </el-card>
    </section>

    <CategoryFormDialog
      v-model="dialogVisible"
      :mode="dialogMode"
      :category="currentCategory"
      :categories="categories"
      :saving="saving"
      @submit="handleSubmit"
    />
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { createCategory, getCategories, updateCategory } from '@/api/categories'
import CategoryFormDialog from '@/components/categories/CategoryFormDialog.vue'
import { buildCategoryTree, flattenCategoryTree, getCategoryName } from '@/utils/category'

const loading = ref(false)
const saving = ref(false)
const dialogVisible = ref(false)
const dialogMode = ref('create')
const currentCategory = ref(null)
const categories = ref([])

const tableRows = computed(() => buildCategoryTree(categories.value))
const flatRows = computed(() => flattenCategoryTree(categories.value))
const treeNodes = computed(() => buildCategoryTree(categories.value))
const rootCategoryCount = computed(() => flatRows.value.filter((item) => item.depth === 0).length)
const childCategoryCount = computed(() => flatRows.value.filter((item) => item.depth > 0).length)
const maxDepthText = computed(() => {
  if (!flatRows.value.length) {
    return '—'
  }
  return `第 ${Math.max(...flatRows.value.map((item) => item.depth + 1))} 级`
})

function getDepthLabel(depth) {
  return `第 ${depth + 1} 级`
}

function getRowClass({ row }) {
  if (row.depth === 0) return 'row--parent'
  if (row.depth === 1) return 'row--child'
  return ''
}

function getParentName(parentCode) {
  return getCategoryName(categories.value, parentCode) || parentCode
}

async function loadCategories() {
  loading.value = true

  try {
    const data = await getCategories()
    categories.value = Array.isArray(data) ? data : []
  } finally {
    loading.value = false
  }
}

function openCreateDialog() {
  dialogMode.value = 'create'
  currentCategory.value = null
  dialogVisible.value = true
}

function openEditDialog(category) {
  dialogMode.value = 'edit'
  currentCategory.value = category
  dialogVisible.value = true
}

async function handleSubmit(payload) {
  saving.value = true

  try {
    if (dialogMode.value === 'create') {
      await createCategory(payload)
      ElMessage.success('分类创建成功')
    } else {
      await updateCategory(currentCategory.value.id, {
        name: payload.name,
        parent_code: payload.parent_code,
        sort_order: payload.sort_order
      })
      ElMessage.success('分类更新成功')
    }

    dialogVisible.value = false
    await loadCategories()
  } finally {
    saving.value = false
  }
}

onMounted(loadCategories)
</script>

<style scoped>
.page-header__actions {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.card-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-4);
}

.category-name-cell {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.category-name-cell__title {
  font-weight: 700;
}

.category-name-cell__meta {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}

/* 一级/二级行样式区分 */
:deep(.row--parent) {
  background: rgba(76, 175, 80, 0.04);
}

:deep(.row--parent .category-name-cell__title) {
  font-weight: 800;
  font-size: var(--font-size-lg);
}

:deep(.row--child) {
  background: rgba(0, 0, 0, 0.01);
}

:deep(.row--child .category-name-cell__title) {
  color: var(--admin-text-secondary);
}

.table-muted {
  color: var(--admin-text-secondary);
}

.tree-panel {
  min-height: 420px;
}

.tree-node {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  width: 100%;
}

.tree-node__label {
  color: var(--admin-text-primary);
}

.tree-node__meta {
  color: var(--admin-text-tertiary);
  font-size: var(--font-size-xs);
}

@media (max-width: 1200px) {
  .panel-grid :deep(.el-card) {
    grid-column: span 12 !important;
  }
}

@media (max-width: 768px) {
  .card-header {
    flex-direction: column;
  }
}
</style>
