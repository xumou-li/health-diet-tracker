<script>
import { useUserStore } from '@/store/user'

export default {
  onLaunch: function () {
    console.log('App Launch')
    // H5 SSR hydration 后强制从 storage 恢复 token
    const userStore = useUserStore()
    userStore.initFromStorage()
  },
  onShow: function () {
    console.log('App Show')
  },
  onHide: function () {
    console.log('App Hide')
  },
}
</script>

<style>
/* #ifdef H5 */
/* H5 端保留全局锁定，避免浏览器页面和内部容器同时滚动 */
page {
  overflow: hidden;
}

/* uni-app H5 内部 wrapper 也可能产生滚动条 */
uni-page-body, uni-page-wrapper {
  height: 100%;
  overflow: hidden;
}
/* #endif */
</style>
