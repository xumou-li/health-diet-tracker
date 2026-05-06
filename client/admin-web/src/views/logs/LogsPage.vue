<template>
  <div class="page-shell">
    <section class="page-header">
      <div class="page-header__content">
        <div class="page-eyebrow">操作日志</div>
        <h1 class="page-title">管理员审计日志</h1>
        <p class="page-description">
          对接 <code>GET /api/admin/logs</code> 的分页列表，支持按 <code>action</code>
          精确筛选、翻页查看，并将 details 字段整理成可读的 JSON 详情弹窗。
        </p>
      </div>

      <el-button :loading="loading" @click="loadLogs">刷新日志</el-button>
    </section>

    <el-card class="panel-card section-card" shadow="never">
      <template #header>
        <div>
          <h2 class="section-title">筛选条件</h2>
          <p class="section-description">action 使用完全匹配，不做模糊搜索，和后端 filter_by(action=action) 行为保持一致。</p>
        </div>
      </template>

      <div class="logs-toolbar">
        <el-input
          v-model="filters.action"
          class="logs-toolbar__input"
          clearable
          placeholder="输入精确 action，例如 update_config"
          @keyup.enter="handleSearch"
        />
        <el-button type="primary" @click="handleSearch">查询</el-button>
        <el-button @click="handleReset">重置</el-button>
      </div>

      <div v-if="actionSuggestions.length" class="tag-row logs-tag-row">
        <el-tag
          v-for="action in actionSuggestions"
          :key="action"
          class="logs-action-tag"
          :effect="filters.action === action ? 'dark' : 'plain'"
          round
          @click="applyActionFilter(action)"
        >
          {{ action }}
        </el-tag>
      </div>
    </el-card>

    <el-card class="panel-card section-card" shadow="never">
      <template #header>
        <div class="section-headline">
          <div>
            <h2 class="section-title">日志列表</h2>
            <p class="section-description">共 {{ formatNumber(total) }} 条记录，当前展示第 {{ currentPage }} 页。</p>
          </div>
          <el-tag type="info" round>每页 {{ pageSize }} 条</el-tag>
        </div>
      </template>

      <el-table :data="logs" row-key="id" v-loading="loading" class="logs-table">
        <el-table-column prop="id" label="ID" min-width="88" />
        <el-table-column label="管理员" min-width="150">
          <template #default="scope">
            <div class="cell-stack">
              <span>{{ scope.row.admin_name || `管理员 #${scope.row.admin_id}` }}</span>
              <span class="cell-stack__hint">admin_id: {{ scope.row.admin_id }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="action" label="action" min-width="180" show-overflow-tooltip>
          <template #default="scope">
            <el-tag type="success" effect="plain" round>{{ scope.row.action }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="目标对象" min-width="160">
          <template #default="scope">
            <div class="cell-stack">
              <span>{{ scope.row.target_type || '—' }}</span>
              <span class="cell-stack__hint">target_id: {{ scope.row.target_id ?? '—' }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="ip_address" label="IP 地址" min-width="150" />
        <el-table-column label="创建时间" min-width="190">
          <template #default="scope">
            {{ formatDateTime(scope.row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="详情" min-width="132" fixed="right">
          <template #default="scope">
            <el-button text type="primary" @click="openDetails(scope.row)">
              {{ scope.row.details ? '查看 JSON' : '查看记录' }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="logs-pagination">
        <el-pagination
          :current-page="currentPage"
          :page-size="pageSize"
          background
          layout="total, sizes, prev, pager, next, jumper"
          :page-sizes="pageSizes"
          :total="total"
          @current-change="onPageChange"
          @size-change="onSizeChange"
        />
      </div>
    </el-card>

    <el-dialog v-model="detailsVisible" title="日志详情" width="760px">
      <template v-if="selectedLog">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="日志 ID">{{ selectedLog.id }}</el-descriptions-item>
          <el-descriptions-item label="管理员">{{ selectedLog.admin_name || `管理员 #${selectedLog.admin_id}` }}</el-descriptions-item>
          <el-descriptions-item label="action">{{ selectedLog.action }}</el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ formatDateTime(selectedLog.created_at) }}</el-descriptions-item>
          <el-descriptions-item label="target_type">{{ selectedLog.target_type || '—' }}</el-descriptions-item>
          <el-descriptions-item label="target_id">{{ selectedLog.target_id ?? '—' }}</el-descriptions-item>
          <el-descriptions-item label="IP 地址" :span="2">{{ selectedLog.ip_address || '—' }}</el-descriptions-item>
        </el-descriptions>

        <div class="details-panel">
          <div class="details-panel__header">
            <h3>details JSON</h3>
            <el-tag :type="selectedLog.details ? 'success' : 'info'" round>
              {{ selectedLog.details ? '有详情' : '无详情' }}
            </el-tag>
          </div>
          <div class="details-panel__body">
            <pre>{{ selectedLog.details ? formatJson(selectedLog.details) : '该日志没有 details 字段内容。' }}</pre>
          </div>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { getAdminLogs } from '@/api/logs'
import { formatDateTime, formatJson, formatNumber } from '@/utils/format'

const loading = ref(false)
const logs = ref([])
const total = ref(0)
const detailsVisible = ref(false)
const selectedLog = ref(null)
const pageSizes = [10, 20, 50]
const currentPage = ref(1)
const pageSize = ref(20)
const knownActions = [
  'update_config',
  'freeze_user',
  'unfreeze_user',
  'create_food',
  'update_food',
  'delete_food',
  'approve_food',
  'create_category',
  'update_category'
]

const filters = reactive({
  action: ''
})

const actionSuggestions = computed(() => {
  const set = new Set(knownActions)
  logs.value.forEach((item) => {
    if (item.action) set.add(item.action)
  })
  return Array.from(set)
})

async function loadLogs() {
  loading.value = true
  try {
    const data = await getAdminLogs({
      page: currentPage.value,
      per_page: pageSize.value,
      action: filters.action.trim() || undefined
    })
    logs.value = data?.items || []
    total.value = Number(data?.total) || 0
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  currentPage.value = 1
  loadLogs()
}

function handleReset() {
  filters.action = ''
  currentPage.value = 1
  pageSize.value = 20
  loadLogs()
}

function onPageChange(page) {
  currentPage.value = page
  loadLogs()
}

function onSizeChange(size) {
  pageSize.value = size
  currentPage.value = 1
  loadLogs()
}

function applyActionFilter(action) {
  filters.action = action
  handleSearch()
}

function openDetails(log) {
  selectedLog.value = log
  detailsVisible.value = true
}

onMounted(() => {
  loadLogs()
})
</script>

<style scoped>
.logs-toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-3);
}

.logs-toolbar__input {
  max-width: 360px;
}

.logs-tag-row {
  margin-top: var(--space-4);
}

.logs-action-tag {
  cursor: pointer;
}

.section-headline {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-4);
}

.logs-table {
  width: 100%;
}

.cell-stack {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.cell-stack__hint {
  color: var(--admin-text-tertiary);
  font-size: var(--font-size-xs);
}

.logs-pagination {
  display: flex;
  justify-content: flex-end;
  margin-top: var(--space-6);
}

.details-panel {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  margin-top: var(--space-6);
}

.details-panel__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
}

.details-panel__header h3 {
  margin: 0;
  font-size: var(--font-size-lg);
}

.details-panel__body {
  padding: var(--space-5);
  border-radius: var(--radius-md);
  background: rgba(17, 33, 23, 0.94);
  box-shadow: var(--shadow-card);
  overflow: auto;
}

.details-panel__body pre {
  margin: 0;
  color: var(--admin-text-light);
  font-size: var(--font-size-sm);
  line-height: 1.8;
  white-space: pre-wrap;
  word-break: break-word;
}

code {
  padding: 0 var(--space-2);
  border-radius: var(--radius-sm);
  background: var(--admin-primary-soft);
  color: var(--admin-primary-deep);
}

@media (max-width: 768px) {
  .section-headline,
  .logs-pagination {
    flex-direction: column;
    align-items: flex-start;
  }

  .logs-toolbar__input {
    max-width: none;
    width: 100%;
  }
}
</style>
