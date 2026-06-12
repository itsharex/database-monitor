/**
 * 认证状态管理
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/api'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || '')
  const username = ref(localStorage.getItem('username') || '')
  const role = ref(localStorage.getItem('role') || '')

  const isLoggedIn = computed(() => !!token.value)

  async function login(user: string, password: string) {
    const res = await api.post('/auth/login', { username: user, password })
    const data = res.data.data
    token.value = data.access_token
    username.value = data.username
    role.value = data.role
    localStorage.setItem('token', data.access_token)
    localStorage.setItem('username', data.username)
    localStorage.setItem('role', data.role)
  }

  function logout() {
    token.value = ''
    username.value = ''
    role.value = ''
    localStorage.removeItem('token')
    localStorage.removeItem('username')
    localStorage.removeItem('role')
  }

  return { token, username, role, isLoggedIn, login, logout }
})
