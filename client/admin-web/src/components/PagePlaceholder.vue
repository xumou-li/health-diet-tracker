<template>
  <div class="page-shell">
    <section class="page-header">
      <div class="page-header__content">
        <div class="page-eyebrow">{{ eyebrow }}</div>
        <h1 class="page-title">{{ title }}</h1>
        <p class="page-description">{{ description }}</p>

        <div class="tag-row">
          <el-tag type="success" effect="light">后台基础骨架已接通</el-tag>
          <el-tag effect="plain">保持 snake_case 字段命名</el-tag>
          <el-tag effect="plain">预留真实 API 接入位</el-tag>
        </div>
      </div>

      <el-card class="panel-card" shadow="never">
        <template #header>
          <span>后端接口</span>
        </template>
        <div class="endpoint-card">
          <div class="endpoint-card__path">{{ endpoint }}</div>
          <p class="endpoint-card__text">{{ endpointDescription }}</p>
        </div>
      </el-card>
    </section>

    <section class="metric-grid">
      <article class="metric-card">
        <span class="metric-card__label">页面状态</span>
        <span class="metric-card__value">Ready</span>
        <span class="metric-card__hint">路由、布局、请求模块与占位内容均已就绪，可直接替换为业务实现。</span>
      </article>

      <article class="metric-card">
        <span class="metric-card__label">结构层级</span>
        <span class="metric-card__value">Domain</span>
        <span class="metric-card__hint">已按 api / store / utils / views 拆分，方便后续继续扩展。</span>
      </article>

      <article class="metric-card">
        <span class="metric-card__label">鉴权方式</span>
        <span class="metric-card__value">Bearer</span>
        <span class="metric-card__hint">自动附带 Authorization: Bearer &lt;token&gt;，并处理 401 跳转。</span>
      </article>

      <article class="metric-card">
        <span class="metric-card__label">代理前缀</span>
        <span class="metric-card__value">/api</span>
        <span class="metric-card__hint">Vite 已代理到 Flask 开发服务 http://127.0.0.1:5000。</span>
      </article>
    </section>

    <section class="panel-grid">
      <el-card class="panel-card section-card" shadow="never" style="grid-column: span 7;">
        <template #header>
          <div>
            <h2 class="section-title">字段与筛选预留</h2>
            <p class="section-description">这些字段和筛选条件已按现有后端接口整理，后续可直接接表格与表单。</p>
          </div>
        </template>

        <div class="tag-row">
          <el-tag v-for="field in fields" :key="field" effect="plain">{{ field }}</el-tag>
        </div>

        <div class="soft-divider"></div>

        <div class="tag-row">
          <el-tag v-for="filter in filters" :key="filter" type="success" effect="light">{{ filter }}</el-tag>
        </div>
      </el-card>

      <el-card class="panel-card section-card" shadow="never" style="grid-column: span 5;">
        <template #header>
          <div>
            <h2 class="section-title">下一步接入建议</h2>
            <p class="section-description">先把数据展示打通，再补充新增、编辑、审核、分页与权限边界。</p>
          </div>
        </template>

        <div class="info-list">
          <div v-for="(note, index) in notes" :key="note" class="info-list__item">
            <span class="info-list__bullet">{{ index + 1 }}</span>
            <div class="info-list__content">
              <span class="info-list__title">实施提示</span>
              <span class="info-list__text">{{ note }}</span>
            </div>
          </div>
        </div>
      </el-card>
    </section>
  </div>
</template>

<script setup>
defineProps({
  eyebrow: {
    type: String,
    default: '功能占位页'
  },
  title: {
    type: String,
    required: true
  },
  description: {
    type: String,
    required: true
  },
  endpoint: {
    type: String,
    required: true
  },
  endpointDescription: {
    type: String,
    required: true
  },
  fields: {
    type: Array,
    default: () => []
  },
  filters: {
    type: Array,
    default: () => []
  },
  notes: {
    type: Array,
    default: () => []
  }
})
</script>

<style scoped>
.endpoint-card {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  min-width: 320px;
}

.endpoint-card__path {
  padding: var(--space-4);
  border-radius: var(--radius-md);
  background: var(--admin-primary-soft);
  color: var(--admin-primary-deep);
  font-weight: 700;
}

.endpoint-card__text {
  margin: 0;
  color: var(--admin-text-secondary);
  line-height: 1.7;
}

@media (max-width: 960px) {
  .panel-grid :deep(.el-card) {
    grid-column: span 12 !important;
  }

  .endpoint-card {
    min-width: auto;
  }
}
</style>
