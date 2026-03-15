import service from './index'

// 用户注册
export const register = (data) => {
  return service({
    url: '/auth/register',
    method: 'post',
    data
  })
}

// 用户登录
export const login = (data) => {
  return service({
    url: '/auth/login',
    method: 'post',
    data: new URLSearchParams(data)
  })
}