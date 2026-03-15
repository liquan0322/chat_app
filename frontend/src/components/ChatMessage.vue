<template>
  <div class="message-container">
    <!-- 消息列表 -->
    <div class="message-list" ref="messageList">
      <div
        v-for="(msg, index) in messages"
        :key="index"
        :class="['message-item', msg.sender_type === 'user' ? 'user-message' : 'robot-message']"
      >
        <div class="message-sender">
          {{ msg.sender_type === 'user' ? '我' : `机器人${msg.sender_id}` }}
        </div>
        <div class="message-content">{{ msg.content }}</div>
        <div class="message-status" v-if="msg.status === 'failed'">
          <el-icon color="red"><Warning /></el-icon>
          <span>{{ msg.error_message || '发送失败' }}</span>
        </div>
        <div class="message-time">
          {{ formatTime(msg.created_at) }}
        </div>
      </div>
    </div>

    <!-- 消息输入框 -->
    <div class="message-input">
      <el-input
        v-model="messageContent"
        placeholder="请输入消息..."
        @keyup.enter="sendMessage"
      />
      <el-button type="primary" @click="sendMessage">发送</el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { ElMessage, ElIcon } from 'element-plus'
import { Warning } from '@element-plus/icons-vue'

const props = defineProps({
  messages: {
    type: Array,
    default: () => []
  },
  conversationId: {
    type: [String, Number],
    default: ''
  },
  groupId: {
    type: [String, Number],
    default: ''
  },
  isGroup: {
    type: Boolean,
    default: false
  },
  onSend: {
    type: Function,
    required: true
  }
})

const emit = defineEmits(['messageSent'])

const messageContent = ref('')
const messageList = ref(null)

// 格式化时间
const formatTime = (timeStr) => {
  if (!timeStr) return ''
  const date = new Date(timeStr)
  return date.toLocaleString()
}

// 发送消息
const sendMessage = async () => {
  if (!messageContent.value.trim()) {
    ElMessage.warning('请输入消息内容')
    return
  }

  if ((!props.conversationId && !props.isGroup) || (!props.groupId && props.isGroup)) {
    ElMessage.warning('请先选择对话/群组')
    return
  }

  try {
    await props.onSend(
      props.isGroup ? props.groupId : props.conversationId,
      messageContent.value
    )
    messageContent.value = ''
    emit('messageSent')
  } catch (error) {
    ElMessage.error('发送失败')
  }
}

// 监听消息变化，自动滚动到底部
watch(
  () => props.messages,
  () => {
    nextTick(() => {
      if (messageList.value) {
        messageList.value.scrollTop = messageList.value.scrollHeight
      }
    })
  },
  { deep: true }
)

onMounted(() => {
  if (messageList.value) {
    messageList.value.scrollTop = messageList.value.scrollHeight
  }
})
</script>

<style scoped>
.message-container {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.message-list {
  flex: 1;
  overflow-y: auto;
  padding: 10px;
  background-color: #f9f9f9;
  border-radius: 4px;
  margin-bottom: 10px;
}

.message-item {
  margin-bottom: 10px;
  padding: 8px 12px;
  border-radius: 8px;
  max-width: 80%;
}

.user-message {
  background-color: #e3f2fd;
  margin-left: auto;
}

.robot-message {
  background-color: #ffffff;
  border: 1px solid #eee;
}

.message-sender {
  font-size: 12px;
  color: #666;
  margin-bottom: 4px;
}

.message-content {
  word-wrap: break-word;
  line-height: 1.4;
}

.message-status {
  font-size: 12px;
  color: red;
  margin-top: 4px;
  display: flex;
  align-items: center;
  gap: 4px;
}

.message-time {
  font-size: 10px;
  color: #999;
  margin-top: 4px;
  text-align: right;
}

.message-input {
  display: flex;
  gap: 10px;
}

.message-input el-input {
  flex: 1;
}
</style>