import service from './index'

// 获取群组列表
export const getGroups = () => {
  return service({
    url: '/group-conversations',
    method: 'get'
  })
}

// 创建群组
export const createGroup = (title = '新群组', robotIds = [1]) => {
  return service({
    url: '/group-conversations',
    method: 'post',
    data: { title, robot_ids: robotIds }
  })
}

// 发送群组消息
export const sendGroupMessage = (groupId, content) => {
  return service({
    url: `/group-conversations/${groupId}/messages`,
    method: 'post',
    data: { content }
  })
}

// 获取群组消息
export const getGroupMessages = (groupId) => {
  return service({
    url: `/group-conversations/${groupId}/messages`,
    method: 'get'
  })
}