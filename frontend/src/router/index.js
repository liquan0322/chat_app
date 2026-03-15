import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '../store'
import Auth from '../views/Auth.vue'
import Chat from '../views/Chat.vue'
import GroupChat from '../views/GroupChat.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      redirect: '/auth'
    },
    {
      path: '/auth',
      name: 'Auth',
      component: Auth
    },
    {
      path: '/chat',
      name: 'Chat',
      component: Chat,
      meta: { requiresAuth: true }
    },
    {
      path: '/group-chat',
      name: 'GroupChat',
      component: GroupChat,
      meta: { requiresAuth: true }
    }
  ]
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const userStore = useUserStore()
  if (to.meta.requiresAuth && !userStore.token) {
    next('/auth')
  } else {
    next()
  }
})

export default router