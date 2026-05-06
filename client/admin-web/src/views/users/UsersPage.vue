<template>
  <div class="page-shell users-page">
    <section class="page-header">
      <div class="page-header__content">
        <div class="page-eyebrow">用户管理</div>
        <h1 class="page-title">用户运营工作台</h1>
        <p class="page-description">
          列表、筛选、分页、详情抽屉与冻结操作全部接入真实后台接口，便于课程演示和日常运营直接使用。
        </p>

        <div class="tag-row">
          <el-tag type="success" effect="light">GET /api/admin/users</el-tag>
          <el-tag effect="plain">GET /api/admin/users/:id</el-tag>
          <el-tag effect="plain">PUT /api/admin/users/:id/freeze</el-tag>
        </div>
      </div>

      <el-card class="panel-card users-page__summary" shadow="never">
        <template #header>
          <span>列表摘要</span>
        </template>

        <div class="users-page__summary-content">
          <div class="users-page__summary-item">
            <span class="users-page__summary-label">当前总量</span>
            <strong class="users-page__summary-value">{{ format_number(pagination.total) }}</strong>
          </div>

          <div class="users-page__summary-item">
            <span class="users-page__summary-label">冻结用户</span>
            <strong class="users-page__summary-value">{{ format_number(frozen_count) }}</strong>
          </div>

          <div class="users-page__summary-item">
            <span class="users-page__summary-label">本页均值 BMI</span>
            <strong class="users-page__summary-value">{{ average_bmi_text }}</strong>
          </div>
        </div>
      </el-card>
    </section>

    <el-card class="panel-card section-card" shadow="never">
      <template #header>
        <div class="users-page__toolbar-header">
          <div>
            <h2 class="section-title">用户列表</h2>
            <p class="section-description">仅使用当前后端支持的关键词和冻结状态筛选，字段保持 snake_case 直出。</p>
          </div>
          <el-button :loading="loading" @click="fetch_users">刷新列表</el-button>
        </div>
      </template>

      <el-form :inline="true" :model="filters" class="users-filters" @submit.prevent>
        <el-form-item label="关键词">
          <el-input
            v-model="filters.keyword"
            clearable
            placeholder="手机号或邮箱"
            @keyup.enter="handle_search"
            @clear="handle_search"
          />
        </el-form-item>

        <el-form-item label="状态">
          <el-select v-model="filters.status" clearable placeholder="全部状态" @change="handle_search">
            <el-option label="正常" value="active" />
            <el-option label="已冻结" value="frozen" />
          </el-select>
        </el-form-item>

        <el-form-item label="每页条数">
          <el-select v-model="pagination.per_page" @change="handle_per_page_change">
            <el-option :value="10" label="10 条/页" />
            <el-option :value="20" label="20 条/页" />
            <el-option :value="50" label="50 条/页" />
          </el-select>
        </el-form-item>

        <el-form-item>
          <div class="users-filters__actions">
            <el-button type="primary" :loading="loading" @click="handle_search">查询</el-button>
            <el-button @click="reset_filters">重置</el-button>
          </div>
        </el-form-item>
      </el-form>

      <el-table v-loading="loading" :data="users" class="users-table" empty-text="暂无用户数据">
        <el-table-column prop="id" label="ID" min-width="80" />

        <el-table-column label="账号信息" min-width="220">
          <template #default="scope">
            <div class="user-identity">
              <strong>{{ scope.row.phone || '未绑定手机号' }}</strong>
              <span>{{ scope.row.email || '未绑定邮箱' }}</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="身体信息" min-width="220">
          <template #default="scope">
            <div class="user-stats">
              <span>年龄 {{ scope.row.age || '--' }}</span>
              <span>身高 {{ scope.row.height_cm || '--' }} cm</span>
              <span>体重 {{ format_weight(scope.row.weight_kg) }}</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="BMI" min-width="120">
          <template #default="scope">
            <div class="bmi-chip" :class="`is-${resolve_bmi_level(scope.row.bmi).key}`">
              <strong>{{ format_bmi(scope.row.bmi) }}</strong>
              <span>{{ resolve_bmi_level(scope.row.bmi).label }}</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="目标热量" min-width="140">
          <template #default="scope">
            {{ format_number(scope.row.daily_calorie_goal) }} kcal
          </template>
        </el-table-column>

        <el-table-column label="状态" min-width="120">
          <template #default="scope">
            <el-tag :type="scope.row.is_frozen ? 'danger' : 'success'" effect="light">
              {{ scope.row.is_frozen ? '已冻结' : '正常' }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="注册时间" min-width="180">
          <template #default="scope">
            {{ format_datetime(scope.row.created_at) }}
          </template>
        </el-table-column>

        <el-table-column label="操作" fixed="right" min-width="220">
          <template #default="scope">
            <div class="users-table__actions">
              <el-button link type="primary" @click="open_user_detail(scope.row.id)">
                查看详情
              </el-button>
              <el-button
                link
                :type="scope.row.is_frozen ? 'success' : 'danger'"
                :loading="freeze_loading_id === scope.row.id"
                @click="handle_toggle_freeze(scope.row)"
              >
                {{ scope.row.is_frozen ? '解冻用户' : '冻结用户' }}
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <div class="users-pagination">
        <span class="users-pagination__summary">
          第 {{ pagination.page }} / {{ Math.max(pagination.pages, 1) }} 页，共 {{ format_number(pagination.total) }} 条
        </span>

        <el-pagination
          background
          layout="prev, pager, next"
          :current-page="pagination.page"
          :page-size="pagination.per_page"
          :total="pagination.total"
          @current-change="handle_page_change"
        />
      </div>
    </el-card>

    <el-drawer
      v-model="detail_drawer_visible"
      title="用户详情"
      size="520px"
      destroy-on-close
    >
      <div v-loading="detail_loading" class="detail-drawer">
        <template v-if="detail_user">
          <div class="detail-drawer__hero">
            <div>
              <div class="page-eyebrow">USER #{{ detail_user.id }}</div>
              <h3 class="detail-drawer__title">{{ detail_user.phone || detail_user.email || '未完善账号信息' }}</h3>
              <p class="detail-drawer__subtitle">{{ detail_user.email || '详情接口已对敏感联系方式脱敏展示' }}</p>
            </div>

            <el-tag :type="detail_user.is_frozen ? 'danger' : 'success'" effect="light">
              {{ detail_user.is_frozen ? '已冻结' : '正常' }}
            </el-tag>
          </div>

          <div class="detail-section-grid">
            <div v-for="item in detail_summary_items" :key="item.label" class="detail-stat-card">
              <span class="detail-stat-card__label">{{ item.label }}</span>
              <strong class="detail-stat-card__value">{{ item.value }}</strong>
              <span class="detail-stat-card__hint">{{ item.hint }}</span>
            </div>
          </div>

          <div class="soft-divider"></div>

          <div class="detail-list">
            <div v-for="item in detail_fields" :key="item.label" class="detail-list__item">
              <span class="detail-list__label">{{ item.label }}</span>
              <span class="detail-list__value">{{ item.value }}</span>
            </div>
          </div>

          <div class="soft-divider"></div>

          <div class="detail-drawer__footer">
            <el-button
              :type="detail_user.is_frozen ? 'success' : 'danger'"
              :loading="freeze_loading_id === detail_user.id"
              @click="handle_toggle_freeze(detail_user, true)"
            >
              {{ detail_user.is_frozen ? '解冻当前用户' : '冻结当前用户' }}
            </el-button>
          </div>
        </template>

        <el-empty v-else description="请选择要查看的用户" />
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessageBox } from 'element-plus'
import { getUserDetail, getUsers, toggleFreezeUser } from '@/api/users'

const loading = ref(false)
const users = ref([])
const freeze_loading_id = ref(null)
const detail_drawer_visible = ref(false)
const detail_loading = ref(false)
const detail_user = ref(null)

const filters = reactive({
  keyword: '',
  status: ''
})

const pagination = reactive({
  page: 1,
  per_page: 20,
  total: 0,
  pages: 0
})

const frozen_count = computed(() => users.value.filter((item) => item.is_frozen).length)

const average_bmi_text = computed(() => {
  const valid_items = users.value.filter((item) => Number(item.bmi) > 0)

  if (!valid_items.length) {
    return '--'
  }

  const total = valid_items.reduce((sum, item) => sum + Number(item.bmi || 0), 0)
  return (total / valid_items.length).toFixed(1)
})

const detail_summary_items = computed(() => {
  if (!detail_user.value) {
    return []
  }

  return [
    {
      label: 'BMI',
      value: format_bmi(detail_user.value.bmi),
      hint: resolve_bmi_level(detail_user.value.bmi).label
    },
    {
      label: '记录数',
      value: format_number(detail_user.value.record_count),
      hint: '累计饮食记录总条数'
    },
    {
      label: '目标热量',
      value: `${format_number(detail_user.value.daily_calorie_goal)} kcal`,
      hint: '用户当前每日推荐摄入'
    },
    {
      label: '基础代谢',
      value: `${format_number(detail_user.value.bmr)} kcal`,
      hint: '按详情接口原始字段展示'
    }
  ]
})

const detail_fields = computed(() => {
  if (!detail_user.value) {
    return []
  }

  return [
    {
      label: '手机号',
      value: detail_user.value.phone || '未绑定'
    },
    {
      label: '邮箱',
      value: detail_user.value.email || '未绑定'
    },
    {
      label: '性别',
      value: resolve_gender_text(detail_user.value.gender)
    },
    {
      label: '年龄',
      value: detail_user.value.age ? `${detail_user.value.age} 岁` : '--'
    },
    {
      label: '生日',
      value: format_date(detail_user.value.birthday)
    },
    {
      label: '身高',
      value: detail_user.value.height_cm ? `${detail_user.value.height_cm} cm` : '--'
    },
    {
      label: '体重',
      value: format_weight(detail_user.value.weight_kg)
    },
    {
      label: '活动水平',
      value: resolve_activity_level_text(detail_user.value.activity_level)
    },
    {
      label: '健康目标',
      value: resolve_health_goal_text(detail_user.value.health_goal)
    },
    {
      label: '饮食偏好',
      value: detail_user.value.diet_preference || '未填写'
    },
    {
      label: '蛋白质占比',
      value: format_ratio(detail_user.value.protein_ratio)
    },
    {
      label: '脂肪占比',
      value: format_ratio(detail_user.value.fat_ratio)
    },
    {
      label: '碳水占比',
      value: format_ratio(detail_user.value.carb_ratio)
    },
    {
      label: '最近更新体重',
      value: format_date(detail_user.value.last_weight_update)
    },
    {
      label: '注册时间',
      value: format_datetime(detail_user.value.created_at)
    }
  ]
})

function build_query_params() {
  const params = {
    page: pagination.page,
    per_page: pagination.per_page
  }

  if (filters.keyword.trim()) {
    params.keyword = filters.keyword.trim()
  }

  if (filters.status) {
    params.status = filters.status
  }

  return params
}

async function fetch_users() {
  loading.value = true

  try {
    const data = await getUsers(build_query_params())
    users.value = Array.isArray(data?.items) ? data.items : []
    pagination.total = Number(data?.total || 0)
    pagination.page = Number(data?.page || 1)
    pagination.per_page = Number(data?.per_page || pagination.per_page)
    pagination.pages = Number(data?.pages || 0)
  } finally {
    loading.value = false
  }
}

async function open_user_detail(user_id) {
  detail_drawer_visible.value = true
  detail_loading.value = true

  try {
    detail_user.value = await getUserDetail(user_id)
  } finally {
    detail_loading.value = false
  }
}

async function handle_toggle_freeze(row, from_detail = false) {
  const next_action_text = row.is_frozen ? '解冻' : '冻结'

  await ElMessageBox.confirm(
    `确认${next_action_text}用户 #${row.id} 吗？`,
    `${next_action_text}确认`,
    {
      type: 'warning',
      confirmButtonText: `确认${next_action_text}`,
      cancelButtonText: '取消'
    }
  )

  freeze_loading_id.value = row.id

  try {
    const result = await toggleFreezeUser(row.id)
    const next_is_frozen = Boolean(result?.is_frozen)

    users.value = users.value.map((item) => (
      item.id === row.id
        ? {
            ...item,
            is_frozen: next_is_frozen
          }
        : item
    ))

    if (detail_user.value?.id === row.id) {
      detail_user.value = {
        ...detail_user.value,
        is_frozen: next_is_frozen
      }

      if (from_detail) {
        detail_user.value = await getUserDetail(row.id)
      }
    }
  } finally {
    freeze_loading_id.value = null
  }
}

function handle_search() {
  pagination.page = 1
  fetch_users()
}

function reset_filters() {
  filters.keyword = ''
  filters.status = ''
  pagination.page = 1
  pagination.per_page = 20
  fetch_users()
}

function handle_page_change(page) {
  pagination.page = page
  fetch_users()
}

function handle_per_page_change() {
  pagination.page = 1
  fetch_users()
}

function format_number(value) {
  return Number(value || 0).toLocaleString('zh-CN')
}

function format_bmi(value) {
  return Number(value || 0) > 0 ? Number(value).toFixed(1) : '--'
}

function format_weight(value) {
  return Number(value || 0) > 0 ? `${Number(value).toFixed(1)} kg` : '--'
}

function format_ratio(value) {
  return Number(value || 0) > 0 ? `${Math.round(Number(value) * 100)}%` : '--'
}

function format_date(value) {
  if (!value) {
    return '--'
  }

  return String(value).slice(0, 10)
}

function format_datetime(value) {
  if (!value) {
    return '--'
  }

  const parsed = new Date(value)

  if (Number.isNaN(parsed.getTime())) {
    return value
  }

  return parsed.toLocaleString('zh-CN', {
    hour12: false,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function resolve_gender_text(value) {
  const gender_map = {
    0: '男',
    1: '女',
    2: '其他'
  }

  return gender_map[value] || '--'
}

function resolve_activity_level_text(value) {
  const activity_map = {
    1: '久坐',
    2: '轻度活动',
    3: '中度活动',
    4: '高强度活动'
  }

  return activity_map[value] || '--'
}

function resolve_health_goal_text(value) {
  const goal_map = {
    1: '维持',
    2: '减脂',
    3: '增肌'
  }

  return goal_map[value] || '--'
}

function resolve_bmi_level(value) {
  const bmi = Number(value || 0)

  if (!bmi) {
    return {
      key: 'unknown',
      label: '待评估'
    }
  }

  if (bmi < 18.5) {
    return {
      key: 'underweight',
      label: '偏瘦'
    }
  }

  if (bmi < 24) {
    return {
      key: 'normal',
      label: '正常'
    }
  }

  if (bmi < 28) {
    return {
      key: 'overweight',
      label: '超重'
    }
  }

  return {
    key: 'obese',
    label: '肥胖'
  }
}

onMounted(() => {
  fetch_users()
})
</script>

<style scoped>
.users-page__summary-content {
  display: grid;
  min-width: 320px;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: var(--space-4);
}

.users-page__summary-item {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.users-page__summary-label {
  color: var(--admin-text-secondary);
  font-size: var(--font-size-sm);
}

.users-page__summary-value {
  font-size: var(--font-size-xl);
}

.users-page__toolbar-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-4);
}

.users-filters {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  gap: var(--space-2);
  margin-bottom: var(--space-5);
}

.users-filters :deep(.el-form-item) {
  margin-bottom: 0;
}

.users-filters__actions {
  display: inline-flex;
  gap: var(--space-3);
}

.users-table {
  width: 100%;
}

.user-identity,
.user-stats,
.users-table__actions,
.detail-drawer,
.detail-drawer__hero,
.detail-drawer__footer,
.detail-list {
  display: flex;
}

.user-identity,
.user-stats {
  flex-direction: column;
  gap: var(--space-2);
}

.user-identity strong,
.detail-drawer__title {
  font-weight: 700;
}

.user-identity span,
.user-stats span,
.detail-drawer__subtitle,
.detail-list__label,
.detail-stat-card__label,
.detail-stat-card__hint {
  color: var(--admin-text-secondary);
  font-size: var(--font-size-sm);
}

.bmi-chip {
  display: inline-flex;
  flex-direction: column;
  gap: var(--space-1);
  width: fit-content;
  padding: var(--space-2) var(--space-3);
  border-radius: var(--radius-sm);
  background: rgba(255, 255, 255, 0.76);
}

.bmi-chip.is-underweight {
  color: var(--admin-info);
  background: rgba(43, 127, 255, 0.1);
}

.bmi-chip.is-normal {
  color: var(--admin-success);
  background: rgba(46, 125, 50, 0.12);
}

.bmi-chip.is-overweight {
  color: var(--admin-warning);
  background: rgba(196, 136, 19, 0.14);
}

.bmi-chip.is-obese {
  color: var(--admin-danger);
  background: rgba(217, 72, 65, 0.12);
}

.bmi-chip.is-unknown {
  color: var(--admin-text-secondary);
  background: rgba(81, 98, 85, 0.12);
}

.users-table__actions {
  gap: var(--space-3);
  flex-wrap: wrap;
}

.users-pagination {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-4);
  margin-top: var(--space-5);
}

.users-pagination__summary {
  color: var(--admin-text-secondary);
  font-size: var(--font-size-sm);
}

.detail-drawer {
  flex-direction: column;
  gap: var(--space-5);
  min-height: 100%;
}

.detail-drawer__hero {
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-4);
  padding: var(--space-5);
  border: 1px solid rgba(215, 228, 216, 0.92);
  border-radius: var(--radius-md);
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.92), rgba(232, 245, 233, 0.74));
}

.detail-drawer__title {
  margin: var(--space-3) 0 var(--space-2);
  font-size: var(--font-size-xl);
}

.detail-drawer__subtitle {
  margin: 0;
  line-height: 1.7;
}

.detail-section-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--space-4);
}

.detail-stat-card {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  padding: var(--space-4);
  border: 1px solid rgba(215, 228, 216, 0.92);
  border-radius: var(--radius-md);
  background: rgba(255, 255, 255, 0.72);
}

.detail-stat-card__value {
  font-size: var(--font-size-xl);
}

.detail-list {
  flex-direction: column;
  gap: var(--space-3);
}

.detail-list__item {
  display: grid;
  grid-template-columns: 112px minmax(0, 1fr);
  gap: var(--space-4);
  align-items: start;
  padding: var(--space-3) 0;
  border-bottom: 1px solid rgba(215, 228, 216, 0.72);
}

.detail-list__item:last-child {
  border-bottom: 0;
}

.detail-list__value {
  color: var(--admin-text-primary);
  line-height: 1.7;
  word-break: break-word;
}

.detail-drawer__footer {
  justify-content: flex-end;
}

@media (max-width: 960px) {
  .users-page__summary-content,
  .detail-section-grid {
    grid-template-columns: repeat(1, minmax(0, 1fr));
  }

  .users-page__summary-content {
    min-width: auto;
  }

  .users-page__toolbar-header,
  .users-pagination,
  .detail-drawer__hero,
  .detail-list__item {
    flex-direction: column;
    grid-template-columns: repeat(1, minmax(0, 1fr));
  }

  .users-pagination {
    align-items: flex-start;
  }
}
</style>
