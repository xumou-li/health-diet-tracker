import AdminLayout from '@/layout/AdminLayout.vue'

export const adminChildrenRoutes = [
  {
    path: 'dashboard',
    name: 'dashboard',
    component: () => import('@/views/dashboard/DashboardPage.vue'),
    meta: {
      title: '数据概览',
      icon: 'House',
      requiresAuth: true,
      menu: true,
      description: '后台首页与核心统计概览'
    }
  },
  {
    path: 'users',
    name: 'users',
    component: () => import('@/views/users/UsersPage.vue'),
    meta: {
      title: '用户管理',
      icon: 'User',
      requiresAuth: true,
      menu: true,
      description: '用户列表、状态筛选与详情入口'
    }
  },
  {
    path: 'foods',
    name: 'foods',
    component: () => import('@/views/foods/FoodsPage.vue'),
    meta: {
      title: '食物管理',
      icon: 'Dish',
      requiresAuth: true,
      menu: true,
      description: '食物资料、审核与营养字段维护'
    }
  },
  {
    path: 'categories',
    name: 'categories',
    component: () => import('@/views/categories/CategoriesPage.vue'),
    meta: {
      title: '分类管理',
      icon: 'Grid',
      requiresAuth: true,
      menu: true,
      description: '食物分类结构与排序管理'
    }
  },
  {
    path: 'system-config',
    name: 'system-config',
    component: () => import('@/views/system/SystemConfigPage.vue'),
    meta: {
      title: '系统配置',
      icon: 'Setting',
      requiresAuth: true,
      menu: true,
      description: 'AI 配置、公告与系统参数维护'
    }
  },
  {
    path: 'logs',
    name: 'logs',
    component: () => import('@/views/logs/LogsPage.vue'),
    meta: {
      title: '操作日志',
      icon: 'Document',
      requiresAuth: true,
      menu: true,
      description: '管理员操作记录与审计入口'
    }
  },
  {
    path: 'ai-stats',
    name: 'ai-stats',
    component: () => import('@/views/ai/AIStatsPage.vue'),
    meta: {
      title: 'AI 统计',
      icon: 'TrendCharts',
      requiresAuth: true,
      menu: true,
      description: 'AI 调用量、Token 与响应时间概览'
    }
  }
]

export const routes = [
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/auth/LoginPage.vue'),
    meta: {
      title: '管理员登录',
      guestOnly: true
    }
  },
  {
    path: '/init-admin',
    name: 'init-admin',
    component: () => import('@/views/auth/InitAdminPage.vue'),
    meta: {
      title: '初始化管理员',
      guestOnly: true
    }
  },
  {
    path: '/',
    component: AdminLayout,
    redirect: '/dashboard',
    meta: {
      title: '管理后台',
      requiresAuth: true,
      hiddenBreadcrumb: false
    },
    children: adminChildrenRoutes
  },
  {
    path: '/403',
    name: 'forbidden',
    component: () => import('@/views/error/ForbiddenPage.vue'),
    meta: {
      title: '无权限访问'
    }
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'not-found',
    component: () => import('@/views/error/NotFoundPage.vue'),
    meta: {
      title: '页面不存在'
    }
  }
]
