import service from './index'

// 获取个人对话列表
export const getConversations = (tag = '') => {
  return service({
    url: `/individual-conversations${tag ? `?tag=${tag}` : ''}`,
    method: 'get'
  })
}

// 创建新对话
export const createConversation = (title = '新对话') => {
  return service({
    url: '/individual-conversations',
    method: 'post',
    data: { title }
  })
}

// 更新对话标题
export const updateConversation = (id, title) => {
  return service({
    url: `/individual-conversations/${id}`,
    method: 'put',
    data: { title }
  })
}

// 删除对话
export const deleteConversation = (id) => {
  return service({
    url: `/individual-conversations/${id}`,
    method: 'delete'
  })
}

// 添加对话标签
export const addConversationTag = (conversationId, tagName) => {
  return service({
    url: `/individual-conversations/${conversationId}/tags`,
    method: 'post',
    data: { tag_name: tagName }
  })
}

// 获取对话消息
export const getConversationMessages = (id) => {
  return service({
    url: `/individual-conversations/${id}/messages`,
    method: 'get'
  })
}

// 发送消息
export const sendMessage = (conversationId, content) => {
  return service({
    url: `/individual-conversations/${conversationId}/messages`,
    method: 'post',
    data: { content }
  })
}