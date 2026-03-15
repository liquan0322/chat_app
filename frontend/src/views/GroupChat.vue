<template>
  <div class="group-chat-container">
    <div class="group-chat-sidebar">
      <GroupList
        :current-group-id="chatStore.currentGroupId"
        @groupSelected="handleGroupSelected"
      />
    </div>

    <div class="group-chat-main">
      <div v-if="!chatStore.currentGroupId" class="empty-chat">
        请选择或创建一个群组开始聊天
      </div>
      <ChatMessage
        v-else
        :messages="chatStore.groupMessages"
        :group-id="chatStore.currentGroupId"
        :is-group="true"
        :on-send="handleSendGroupMessage"
        @messageSent="fetchGroupMessages"
      />
    </div>

    <div class="group-chat-header">
      <el-button type="text" @click="userStore.logout()" class="logout-btn">
        退出登录 ({{ userStore.username }})
      </el-button>
      <el-button type="text" @click="$router.push('/chat')" class="chat-btn">
        切换到个人聊天
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import GroupList from '@/components/GroupList.vue'
import ChatMessage from '@/components/ChatMessage.vue'
import { getGroupMessages, sendGroupMessage } from '@/api/group'
import { useUserStore } from '@/store'
import { useChatStore } from '@/store'

const userStore = useUserStore()
const chatStore = useChatStore()

// 获取群组消息列表
const fetchGroupMessages = async () => {
  if (!chatStore.currentGroupId) return

  try {
    const res = await getGroupMessages(chatStore.currentGroupId)
    chatStore.setGroupMessages(res)
  } catch (error) {
    ElMessage.error('获取消息失败')
  }
}

// 选择群组
const handleGroupSelected = async (id) => {
  chatStore.setCurrentGroupId(id)
  await fetchGroupMessages()
}

// 发送群组消息
const handleSendGroupMessage = async (groupId, content) => {
  await sendGroupMessage(groupId, content)
  await fetchGroupMessages()
}

onMounted(() => {
  if (chatStore.currentGroupId) {
    fetchGroupMessages()
  }
})
</script>

<style scoped>
.group-chat-container {
  display: flex;
  height: 100vh;
}

.group-chat-header {
  position: fixed;
  top: 0;
  right: 0;
  padding: 10px;
  display: flex;
  gap: 10px;
}

.group-chat-sidebar {
  width: 300px;
  border-right: 1px solid #eee;
  height: 100%;
  padding-top: 60px;
}

.group-chat-main {
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

.logout-btn, .chat-btn {
  color: #666;
}
</style>