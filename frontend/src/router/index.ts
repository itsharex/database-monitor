/**
 * 路由配置
 */
import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: () => import('@/views/LoginView.vue'),
      meta: { requiresAuth: false },
    },
    {
      path: '/',
      name: 'Dashboard',
      component: () => import('@/views/DashboardView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/instance/:id',
      name: 'InstanceDetail',
      component: () => import('@/views/InstanceDetailView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/manage',
      name: 'Manage',
      component: () => import('@/views/ManageView.vue'),
      meta: { requiresAuth: true, requiresAdmin: true },
    },
  ],
})

// 路由守卫
router.beforeEach((to, _from, next) => {
  const authStore = useAuthStore()
  if (to.meta.requiresAuth !== false && !authStore.isLoggedIn) {
    next('/login')
  } else if (to.meta.requiresAdmin && authStore.role !== 'admin') {
    next('/')
  } else {
    next()
  }
})

export default router
