<template>
  <!-- 登录页面 -->
  <div class="login-page">
    <div class="login-theme">
      <ThemeToggle />
    </div>
    <div class="login-bg"></div>
    <div class="login-card glass-card">
      <h1 class="login-title">数据库监控大屏系统</h1>
      <p class="login-subtitle">Database Monitor Dashboard</p>
      <el-form :model="form" @submit.prevent="handleLogin" class="login-form">
        <el-form-item>
          <el-input
            v-model="form.username"
            placeholder="用户名"
            prefix-icon="User"
            size="large"
          />
        </el-form-item>
        <el-form-item>
          <el-input
            v-model="form.password"
            type="password"
            placeholder="密码"
            prefix-icon="Lock"
            size="large"
            show-password
          />
        </el-form-item>
        <el-form-item>
          <el-button
            type="primary"
            size="large"
            :loading="loading"
            native-type="submit"
            class="login-btn"
          >登 录</el-button>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * 登录视图
 */
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import ThemeToggle from '@/components/ThemeToggle.vue'

const router = useRouter()
const authStore = useAuthStore()
const loading = ref(false)
const form = reactive({ username: 'admin', password: 'admin123' })

async function handleLogin() {
  if (!form.username || !form.password) {
    ElMessage.warning('请输入用户名和密码')
    return
  }
  loading.value = true
  try {
    await authStore.login(form.username, form.password)
    router.push('/')
  } catch (e) {
    // 错误已在拦截器处理
  } finally {
    loading.value = false
  }
}
</script>

<style scoped lang="scss">
.login-page {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}

.login-theme {
  position: absolute;
  top: 20px;
  right: 24px;
  z-index: 2;
}

.login-bg {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(ellipse at 20% 50%, rgba(0, 212, 255, 0.08) 0%, transparent 50%),
    radial-gradient(ellipse at 80% 50%, rgba(123, 140, 255, 0.06) 0%, transparent 50%),
    var(--bg-primary);
}

.login-card {
  position: relative;
  width: 400px;
  padding: 48px 40px;
  z-index: 1;
}

.login-title {
  text-align: center;
  font-size: 24px;
  color: var(--accent-cyan);
  margin-bottom: 8px;
}

.login-subtitle {
  text-align: center;
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 32px;
}

.login-btn {
  width: 100%;
}
</style>
