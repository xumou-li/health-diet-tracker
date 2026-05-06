<template>
  <view class="ai-container">
    <!-- AI状态卡片 -->
    <view class="status-card" v-if="aiStatus">
      <view class="status-info">
        <text class="status-label">今日剩余次数</text>
        <text class="status-value">{{ aiStatus.remaining_calls }} / {{ aiStatus.daily_limit }}</text>
      </view>
      <view class="disclaimer">{{ aiStatus.disclaimer }}</view>
    </view>

    <!-- 功能卡片 -->
    <view class="feature-section">
      <view class="feature-card" @click="getEvaluation">
        <view class="feature-icon">📊</view>
        <view class="feature-info">
          <text class="feature-title">今日饮食评价</text>
          <text class="feature-desc">AI分析今天的饮食情况</text>
        </view>
      </view>
      
      <view class="feature-card" @click="getSuggestion">
        <view class="feature-icon">💡</view>
        <view class="feature-info">
          <text class="feature-title">饮食建议</text>
          <text class="feature-desc">获取个性化饮食建议</text>
        </view>
      </view>
    </view>

    <!-- AI对话区域 -->
    <view class="chat-section">
      <view class="chat-header">
        <view>
          <view class="section-title">智能问答</view>
        </view>
        <view
          class="clear-history-btn"
          :class="{ disabled: messages.length === 0 || loading }"
          @click="clearChatHistory"
        >
          清空聊天记录
        </view>
      </view>
      
      <scroll-view class="chat-list" scroll-y :scroll-top="scrollTop">
        <view v-if="messages.length === 0" class="chat-empty">
          <text>有什么饮食问题可以问我哦~</text>
          <view class="quick-questions">
            <text class="quick-btn" @click="askQuestion('我今天还能吃什么？')">我今天还能吃什么？</text>
            <text class="quick-btn" @click="askQuestion('这周蛋白质够吗？')">这周蛋白质够吗？</text>
            <text class="quick-btn" @click="askQuestion('推荐一些低热量食物')">推荐一些低热量食物</text>
          </view>
        </view>
        
        <view v-for="(msg, index) in messages" :key="index" class="message-item" :class="msg.role">
          <view class="message-avatar" v-if="msg.role === 'assistant'">🤖</view>
          <view class="message-content">
            <text>{{ msg.content }}</text>
          </view>
          <view class="message-avatar" v-if="msg.role === 'user'">👤</view>
        </view>
        
      </scroll-view>
    </view>

    <!-- 输入区域 -->
    <view class="chat-input-bar">
      <view class="chat-input">
        <input 
          v-model="inputText" 
          placeholder="输入你的问题..."
          @confirm="sendMessage"
        />
        <button class="send-btn" @click="sendMessage" :disabled="!inputText || loading">
          发送
        </button>
      </view>
    </view>

  </view>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { getStatus, chatStream, getHistory, clearHistory } from '@/api/ai'

const aiStatus = ref(null)
const messages = ref([])
const inputText = ref('')
const loading = ref(false)
const scrollTop = ref(0)
const historyLoading = ref(false)

// 从后端加载聊天记录
const fetchChatHistory = async () => {
  historyLoading.value = true
  try {
    const res = await getHistory({ type: 'chat', per_page: 50 })
    const items = res?.items || []
    const loadedMessages = []

    // 后端按时间倒序返回，需要反转并按正序组装消息
    // 每条记录包含 question 和 content，对应前端的 user + assistant
    const sortedItems = [...items].reverse()

    sortedItems.forEach((item) => {
      if (item.question) {
        loadedMessages.push({ role: 'user', content: item.question })
      }
      if (item.content) {
        loadedMessages.push({ role: 'assistant', content: item.content })
      }
    })

    messages.value = loadedMessages
  } catch (error) {
    console.error('加载AI聊天记录失败:', error)
    messages.value = []
  } finally {
    historyLoading.value = false
  }
}


// 获取AI状态
const fetchStatus = async () => {
  try {
    aiStatus.value = await getStatus()
  } catch (error) {
    console.error('获取AI状态失败:', error)
  }
}

const appendMessage = (role, content) => {
  messages.value.push({ role, content })
  scrollToBottom()
}

const getErrorMessage = (error, fallback = '抱歉，我暂时无法回答，请稍后再试。') => {
  if (!error) return fallback

  if (typeof error === 'string' && error.trim()) {
    return error.trim()
  }

  if (typeof error.message === 'string' && error.message.trim()) {
    return error.message.trim()
  }

  if (typeof error.errMsg === 'string' && error.errMsg.trim()) {
    return error.errMsg.trim()
  }

  return fallback
}

// 通用流式对话（输入框和预设按钮共用）
const doStreamChat = async (question) => {
  if (loading.value) return

  appendMessage('user', question)
  
  const assistantIndex = messages.value.length
  messages.value.push({ role: 'assistant', content: '' })
  scrollToBottom()
  
  loading.value = true
  try {
    const response = await chatStream({ question })
    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      
      buffer += decoder.decode(value, { stream: true })
      
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''
      
      for (const line of lines) {
        const trimmed = line.trim()
        if (!trimmed.startsWith('data: ')) continue
        
        const payload = trimmed.slice(6)
        if (payload === '[DONE]') continue
        
        try {
          const parsed = JSON.parse(payload)
          if (parsed.error) {
            messages.value[assistantIndex].content = parsed.error
            return
          }
          if (parsed.content) {
            messages.value[assistantIndex].content += parsed.content
            scrollToBottom()
          }
        } catch (e) {
          // 忽略解析失败的行
        }
      }
    }
    
    fetchStatus()
  } catch (error) {
    console.error('流式对话失败:', error)
    messages.value[assistantIndex].content = getErrorMessage(error)
  } finally {
    loading.value = false
  }
}

// 今日饮食评价
const getEvaluation = () => {
  doStreamChat('请帮我评价一下今天的饮食情况。')
}

// 获取饮食建议
const getSuggestion = () => {
  doStreamChat('请给我一些饮食建议。')
}

// 发送消息（流式）
const sendMessage = async () => {
  if (!inputText.value.trim() || loading.value) return
  
  const question = inputText.value.trim()
  inputText.value = ''
  
  doStreamChat(question)
}

// 快捷提问
const askQuestion = (question) => {
  inputText.value = question
  sendMessage()
}

const clearChatHistory = () => {
  if (loading.value) {
    uni.showToast({ title: 'AI回复中，请稍后再试', icon: 'none' })
    return
  }

  if (messages.value.length === 0) {
    uni.showToast({ title: '暂无聊天记录', icon: 'none' })
    return
  }

  uni.showModal({
    title: '清空聊天记录',
    content: '确认清空所有AI问答记录吗？清空后将无法恢复。',
    confirmColor: '#667eea',
    success: async (res) => {
      if (!res.confirm) return

      try {
        await clearHistory({ type: 'chat' })
        messages.value = []
        scrollTop.value = 0
        uni.showToast({ title: '聊天记录已清空', icon: 'success' })
      } catch (error) {
        console.error('清空AI聊天记录失败:', error)
        uni.showToast({ title: '清空失败，请稍后重试', icon: 'none' })
      }
    },
  })
}

// 滚动到底部
const scrollToBottom = () => {
  nextTick(() => {
    scrollTop.value = 99999
  })
}

onMounted(() => {
  fetchChatHistory()
  scrollToBottom()
  fetchStatus()
})
</script>

<style lang="scss">
/* 锁定AI助手页面，禁止整体滚动 */
page {
  overflow: hidden;
}
</style>

<style lang="scss" scoped>
.ai-container {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: #f5f5f5;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-sizing: border-box;
  /* H5 端需要手动为导航栏(44px)和tabbar(50px)留空间 */
  /* #ifdef H5 */
  padding-top: 44px;
  padding-bottom: 50px;
  /* #endif */
}

.status-card {
  margin: 20rpx 30rpx;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 20rpx;
  padding: 30rpx;
  
  .status-info {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16rpx;
    
    .status-label {
      font-size: 28rpx;
      color: rgba(255,255,255,0.8);
    }
    
    .status-value {
      font-size: 32rpx;
      font-weight: bold;
      color: #fff;
    }
  }
  
  .disclaimer {
    font-size: 22rpx;
    color: rgba(255,255,255,0.6);
  }
}

.feature-section {
  display: flex;
  padding: 0 30rpx;
  gap: 20rpx;
  
  .feature-card {
    flex: 1;
    background: #fff;
    border-radius: 16rpx;
    padding: 24rpx;
    display: flex;
    align-items: center;
    
    .feature-icon {
      font-size: 48rpx;
      margin-right: 16rpx;
    }
    
    .feature-info {
      .feature-title {
        display: block;
        font-size: 28rpx;
        font-weight: bold;
        color: #333;
      }
      
      .feature-desc {
        display: block;
        font-size: 22rpx;
        color: #999;
        margin-top: 4rpx;
      }
    }
  }
}

.chat-section {
  flex: 1;
  display: flex;
  flex-direction: column;
   margin: 20rpx 30rpx 0;
   background: #fff;
   border-radius: 20rpx;
   overflow: hidden;
   min-height: 0;
  
  .chat-header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 20rpx;
    padding: 24rpx 24rpx 0;

    .section-title {
      font-size: 30rpx;
      font-weight: bold;
      color: #333;
    }

    .chat-note {
      margin-top: 8rpx;
      font-size: 22rpx;
      color: #999;
      line-height: 1.5;
    }

    .clear-history-btn {
      flex-shrink: 0;
      padding: 10rpx 20rpx;
      border-radius: 999rpx;
      background: #f5f5f5;
      font-size: 24rpx;
      line-height: 1.4;
      color: #666;

      &.disabled {
        color: #bbb;
        background: #f7f7f7;
      }
    }
  }
  
  .chat-list {
     flex: 1;
     height: 0;
     padding: 24rpx;
     padding-bottom: 40rpx;
     box-sizing: border-box;
     min-height: 0;
    
    .chat-empty {
      text-align: center;
      padding: 40rpx 0;
      
      text {
        font-size: 28rpx;
        color: #999;
      }
      
      .quick-questions {
        margin-top: 30rpx;
        display: flex;
        flex-direction: column;
        gap: 16rpx;
        
        .quick-btn {
          display: inline-block;
          padding: 16rpx 24rpx;
          background: #f0f0f0;
          border-radius: 30rpx;
          font-size: 26rpx;
          color: #666;
        }
      }
    }
    
    .message-item {
      display: flex;
      align-items: flex-start;
      margin-bottom: 20rpx;
      
      &.user {
        justify-content: flex-end;
        
        .message-content {
          background: #667eea;
          color: #fff;
          border-radius: 20rpx 20rpx 4rpx 20rpx;
          margin-right: 12rpx;
        }
        
        .message-avatar {
          margin-right: 0;
        }
      }
      
      &.assistant {
        .message-content {
          background: #f5f5f5;
          color: #333;
          border-radius: 20rpx 20rpx 20rpx 4rpx;
          margin-left: 12rpx;
          
          &.loading {
            color: #999;
          }
        }
      }
      
      .message-avatar {
        font-size: 40rpx;
        flex-shrink: 0;
        width: 50rpx;
        height: 50rpx;
        text-align: center;
        line-height: 50rpx;
      }
      
      .message-content {
        max-width: 60%;
        padding: 20rpx 24rpx;
        font-size: 28rpx;
        line-height: 1.5;
        word-break: break-all;
      }
    }
  }
  
}

.chat-input-bar {
  flex-shrink: 0;
  padding: 20rpx 30rpx;
  background: #f5f5f5;

  .chat-input {
    display: flex;
    padding: 20rpx 24rpx;
    background: #fff;
    border-radius: 20rpx;
    box-shadow: 0 -4rpx 20rpx rgba(0, 0, 0, 0.04);
    gap: 16rpx;

    input {
      flex: 1;
      height: 72rpx;
      padding: 0 24rpx;
      background: #f5f5f5;
      border-radius: 36rpx;
      font-size: 28rpx;
    }

    .send-btn {
      width: 120rpx;
      height: 72rpx;
      background: #667eea;
      color: #fff;
      font-size: 28rpx;
      border-radius: 36rpx;
      border: none;

      &[disabled] {
        background: #ccc;
      }
    }
  }
}

</style>
