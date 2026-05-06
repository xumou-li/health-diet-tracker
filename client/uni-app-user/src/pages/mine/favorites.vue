<template>
  <view class="favorites-container">
    <!-- 内容区域 -->
    <scroll-view 
      class="content-scroll" 
      scroll-y 
      @scrolltolower="loadMore"
      :refresher-enabled="true"
      @refresherrefresh="onRefresh"
      :refresher-triggered="refreshing"
    >
      <view class="scroll-inner">
      <!-- 加载中 -->
      <view v-if="loading && list.length === 0" class="loading-state">
        <text>加载中...</text>
      </view>

      <!-- 空状态 -->
      <view v-else-if="list.length === 0 && !loading" class="empty-state">
        <text class="empty-icon">📋</text>
        <text class="empty-title">还没有收藏</text>
        <text class="empty-desc">点击右下角 + 创建你的第一个收藏</text>
      </view>

      <!-- 收藏卡片列表 -->
      <view v-else class="recipe-list">
        <view 
          v-for="recipe in list" 
          :key="recipe.id"
          class="recipe-card"
          @click="goEdit(recipe)"
          @longpress="showDeleteConfirm(recipe)"
        >
          <view class="card-header">
            <text class="recipe-name">{{ recipe.name }}</text>
            <text class="recipe-count">{{ recipe.summary?.item_count || 0 }} 种食物</text>
          </view>

          <!-- 食物预览 -->
          <view class="food-preview" v-if="recipe.items && recipe.items.length > 0">
            <view 
              v-for="(item, idx) in recipe.items.slice(0, 4)" 
              :key="idx"
              class="preview-tag"
              :class="item.type"
            >
              <text v-if="item.type === 'custom'">{{ item.name }}</text>
              <text v-else>{{ item.food?.name || '未知' }}</text>
            </view>
            <text v-if="recipe.items.length > 4" class="more-tag">
              +{{ recipe.items.length - 4 }}
            </text>
          </view>

          <!-- 营养汇总 -->
          <view class="nutrition-summary" v-if="recipe.summary">
            <view class="summary-item">
              <text class="s-value">{{ recipe.summary.calorie }}</text>
              <text class="s-label">热量</text>
            </view>
            <view class="summary-item">
              <text class="s-value">{{ recipe.summary.protein }}g</text>
              <text class="s-label">蛋白质</text>
            </view>
            <view class="summary-item">
              <text class="s-value">{{ recipe.summary.fat }}g</text>
              <text class="s-label">脂肪</text>
            </view>
            <view class="summary-item">
              <text class="s-value">{{ recipe.summary.carb }}g</text>
              <text class="s-label">碳水</text>
            </view>
          </view>
        </view>

        <!-- 底部提示 -->
        <view v-if="list.length > 0" class="bottom-tip">
          <text v-if="!hasMore">没有更多了</text>
        </view>
      </view>
      </view>
    </scroll-view>

    <!-- 右下角添加按钮 -->
    <view class="fab-btn" @click="goCreate">
      <text class="fab-icon">+</text>
    </view>
  </view>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { getRecipes, deleteRecipe } from '@/api/recipe'

const list = ref([])
const loading = ref(false)
const refreshing = ref(false)
const hasMore = ref(false)

const fetchList = async () => {
  loading.value = true
  try {
    const data = await getRecipes()
    list.value = data || []
  } catch (e) {
    console.error('获取收藏列表失败:', e)
  } finally {
    loading.value = false
    refreshing.value = false
  }
}

const onRefresh = () => {
  refreshing.value = true
  fetchList()
}

const loadMore = () => {
  // 暂不分页，一次性加载所有
}

const goCreate = () => {
  uni.navigateTo({ url: '/pages/mine/favorites-edit' })
}

const goEdit = (recipe) => {
  uni.navigateTo({ url: `/pages/mine/favorites-edit?id=${recipe.id}` })
}

const showDeleteConfirm = (recipe) => {
  uni.showModal({
    title: '确认删除',
    content: `确定要删除收藏「${recipe.name}」吗？`,
    success: async (res) => {
      if (res.confirm) {
        try {
          await deleteRecipe(recipe.id)
          uni.showToast({ title: '已删除', icon: 'success' })
          fetchList()
        } catch (e) {
          console.error('删除失败:', e)
        }
      }
    }
  })
}

// 监听编辑页的变更事件
const onFavoritesChanged = () => {
  fetchList()
}

onMounted(() => {
  fetchList()
  uni.$on('favoritesChanged', onFavoritesChanged)
})

onUnmounted(() => {
  uni.$off('favoritesChanged', onFavoritesChanged)
})
</script>

<style lang="scss" scoped>
.favorites-container {
  height: 100vh;
  overflow: hidden;
  background: #f5f5f5;
}

.content-scroll {
  height: 100%;
  width: 100%;
  box-sizing: border-box;
}

.scroll-inner {
  padding: 20rpx 30rpx 140rpx;
  box-sizing: border-box;
}

.loading-state, .empty-state {
  text-align: center;
  padding: 120rpx 0;
}

.empty-state {
  .empty-icon {
    font-size: 100rpx;
    display: block;
    margin-bottom: 24rpx;
  }

  .empty-title {
    display: block;
    font-size: 32rpx;
    color: #333;
    font-weight: 500;
    margin-bottom: 12rpx;
  }

  .empty-desc {
    display: block;
    font-size: 26rpx;
    color: #999;
  }
}

.recipe-list {
  .recipe-card {
    background: #fff;
    border-radius: 20rpx;
    padding: 28rpx;
    margin-bottom: 24rpx;
    box-sizing: border-box;
    overflow: hidden;

    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 20rpx;

      .recipe-name {
        flex: 1;
        font-size: 32rpx;
        font-weight: bold;
        color: #333;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        margin-right: 16rpx;
      }

      .recipe-count {
        flex-shrink: 0;
        font-size: 24rpx;
        color: #4caf50;
        background: #e8f5e9;
        padding: 6rpx 16rpx;
        border-radius: 20rpx;
        white-space: nowrap;
      }
    }

    .food-preview {
      display: flex;
      flex-wrap: wrap;
      margin-bottom: 20rpx;

      .preview-tag {
        font-size: 22rpx;
        padding: 6rpx 14rpx;
        border-radius: 8rpx;
        margin-right: 12rpx;
        margin-bottom: 12rpx;

        &.food {
          background: #f0f9f0;
          color: #4caf50;
        }

        &.custom {
          background: #e8f0fe;
          color: #4285f4;
        }
      }

      .more-tag {
        font-size: 22rpx;
        color: #999;
        padding: 6rpx 14rpx;
        margin-right: 12rpx;
        margin-bottom: 12rpx;
      }
    }

    .nutrition-summary {
      display: flex;
      flex-wrap: wrap;
      padding-top: 20rpx;
      border-top: 1rpx solid #f5f5f5;

      .summary-item {
        flex: 0 0 25%;
        text-align: center;

        .s-value {
          display: block;
          font-size: 28rpx;
          font-weight: bold;
          color: #333;
        }

        .s-label {
          display: block;
          font-size: 20rpx;
          color: #999;
          margin-top: 4rpx;
        }
      }
    }
  }

  .bottom-tip {
    text-align: center;
    padding: 30rpx 0;
    font-size: 26rpx;
    color: #ccc;
  }
}

/* 右下角悬浮添加按钮 */
.fab-btn {
  position: fixed;
  right: 40rpx;
  bottom: 120rpx;
  width: 100rpx;
  height: 100rpx;
  border-radius: 50%;
  background: linear-gradient(135deg, #4caf50 0%, #81c784 100%);
  box-shadow: 0 8rpx 24rpx rgba(76, 175, 80, 0.35);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;

  .fab-icon {
    font-size: 52rpx;
    color: #fff;
    font-weight: 300;
    line-height: 1;
  }
}
</style>
