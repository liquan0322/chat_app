<template>
  <div class="chat-container">
    <div class="chat-sidebar">
      <ConversationList
        :current-conversation-id="chatStore.currentConversationId"
        @conversationSelected="handleConversationSelected"
      />
    </div>

    <div class="chat-main">
      <div v-if="!chatStore.currentConversationId" class="empty-chat">
        请选择或创建一个对话开始聊天
      </div>
      <ChatMessage
        v-else
        :messages="chatStore.messages"
        :conversation-id="chatStore.currentConversationId"
        :on-send="handleSendMessage"
        @messageSent="fetchMessages"
      />
    </div>

    <div class="chat-header">
      <el-button type="text" @click="userStore.logout()" class="logout-btn">
        退出登录 ({{ userStore.username }})
      </el-button>
      <el-button type="text" @click="$router.push('/group-chat')" class="group-btn">
        切换到群组聊天
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import ConversationList from '@/components/ConversationList.vue'
import ChatMessage from '@/components/ChatMessage.vue'
import { getConversationMessages, sendMessage } from '@/api/conversation'
import { useUserStore } from '@/store'
import { useChatStore } from '@/store'

const userStore = useUserStore()
const chatStore = useChatStore()

// 获取消息列表
const fetchMessages = async () => {
  if (!chatStore.currentConversationId) return

  try {
    const res = await getConversationMessages(chatStore.currentConversationId)
    chatStore.setMessages(res)
  } catch (error) {
    ElMessage.error('获取消息失败')
  }
}

// 选择对话
const handleConversationSelected = async (id) => {
  chatStore.setCurrentConversationId(id)
  await fetchMessages()
}

// 发送消息
const handleSendMessage = async (conversationId, content) => {
  await sendMessage(conversationId, content)
  await fetchMessages()
}

onMounted(() => {
  if (chatStore.currentConversationId) {
    fetchMessages()
  }
})
</script>

<style scoped>
.chat-container {
  display: flex;
  height: 100vh;
}

.chat-header {
  position: fixed;
  top: 0;
  right: 0;
  padding: 10px;
  display: flex;
  gap: 10px;
}

.chat-sidebar {
  width: 300px;
  border-right: 1px solid #eee;
  height: 100%;
  padding-top: 60px;
}

.chat-main {
  flex: 1;
  padding: 60px 20px 20px;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.empty-chat {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
  color: #999;
  font-size: 18px;
}

.logout-btn, .group-btn {
  color: #666;
}
</style>