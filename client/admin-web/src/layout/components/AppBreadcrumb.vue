<template>
  <el-breadcrumb separator=">">
    <el-breadcrumb-item
      v-for="item in breadcrumbItems"
      :key="item.path"
      :to="item.isLast ? undefined : item.path"
    >
      {{ item.title }}
    </el-breadcrumb-item>
  </el-breadcrumb>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

function buildFullPath(segments, index) {
  // 拼接从根到当前 segment 的完整路径
  const path = segments
    .slice(0, index + 1)
    .map((r) => r.path)
    .join('/')
    .replace(/\/+/g, '/')
  return path || '/'
}

const breadcrumbItems = computed(() => {
  const matched = route.matched.filter((item) => item.meta?.title && !item.meta?.hiddenBreadcrumb)

  return matched.map((item, index) => ({
    path: buildFullPath(matched, index),
    title: item.meta.title,
    isLast: index === matched.length - 1
  }))
})
</script>
