/**
 * Pinia Store入口
 */
import { createPinia } from 'pinia'

const pinia = createPinia()

export default pinia

// 导出各个Store
export * from './user'
export * from './meal'
