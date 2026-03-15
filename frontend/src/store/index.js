import { defineStore } from 'pinia'

export const useUserStore = defineStore('user', {
  state: () => ({
    token: localStorage.getItem('token') || '',
    username: localStorage.getItem('username') || '',
    userId: localStorage.getItem('userId') || ''
  }),
  actions: {
    setUserInfo({ token, username, userId }) {
      this.token = token
      this.username = username
      this.userId = userId
      localStorage.setItem('token', token)
      localStorage.setItem('username', username)
      localStorage.setItem('userId', userId)
    },
    logout() {
      this.token = ''
      this.username = ''
      this.userId = ''
      localStorage.clear()
    }
  }
})

export const useChatStore = defineStore('chat', {
  state: () => ({
    currentConversationId: '',
    currentGroupId: '',
    messages: [],
    groupMessages: []
  }),
  actions: {
    setCurrentConversationId(id) {
      this.currentConversationId = id
    },
    setCurrentGroupId(id) {
      this.currentGroupId = id
    },
    setMessages(messages) {
      this.messages = messages
    },
    setGroupMessages(messages) {
      this.groupMessages = messages
    },
    addMessage(message) {
      this.messages.push(message)
    },
    addGroupMessage(message) {
      this.groupMessages.push(message)
    }
  }
})