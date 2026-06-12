/**
 * Axios HTTP 客户端配置
 */
import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

// 请求拦截器：附加 JWT 令牌
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 响应拦截器：统一错误处理
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      router.push('/login')
      ElMessage.error('登录已过期，请重新登录')
    } else {
      const detail = error.response?.data?.detail
      let msg = '请求失败'
      if (Array.isArray(detail)) {
        msg = detail.map((d: { msg?: string; loc?: string[] }) => {
          const field = d.loc?.slice(-1)[0] || ''
          return field ? `${field}: ${d.msg}` : (d.msg || '')
        }).join('；')
      } else if (typeof detail === 'string') {
        msg = detail
      } else if (error.response?.data?.message) {
        msg = error.response.data.message
      } else if (error.message) {
        msg = error.message
      }
      ElMessage.error(msg)
    }
    return Promise.reject(error)
  }
)

export default api
