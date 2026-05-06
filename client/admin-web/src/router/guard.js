import { isAdminAuthenticated } from '@/utils/storage'

const APP_TITLE = '健康饮食管理后台'

function resolveDocumentTitle(to) {
  const routeTitle = to.meta?.title
  return routeTitle ? `${routeTitle} - ${APP_TITLE}` : APP_TITLE
}

export function setupRouterGuard(router) {
  router.beforeEach((to, from, next) => {
    document.title = resolveDocumentTitle(to)

    const isAuthenticated = isAdminAuthenticated()

    if (to.meta?.guestOnly && isAuthenticated) {
      next({ name: 'dashboard' })
      return
    }

    if (to.meta?.requiresAuth && !isAuthenticated) {
      next({
        name: 'login',
        query: {
          redirect: to.fullPath
        }
      })
      return
    }

    next()
  })

  router.afterEach((to) => {
    document.title = resolveDocumentTitle(to)
  })
}
