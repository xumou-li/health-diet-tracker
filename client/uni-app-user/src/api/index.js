/**
 * API统一导出
 */
export * from './auth'
export * from './user'
export * from './food'
export * from './meal'
export * from './stats'
export * from './ai'
export * from './recipe'

import auth from './auth'
import user from './user'
import food from './food'
import meal from './meal'
import stats from './stats'
import ai from './ai'
import recipe from './recipe'

export default {
  auth,
  user,
  food,
  meal,
  stats,
  ai,
  recipe
}
