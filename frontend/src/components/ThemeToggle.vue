<template>
  <button class="theme-toggle-btn" :title="isDark ? '切换浅色模式' : '切换深色模式'" @click="themeStore.toggle()">
    <el-icon><component :is="isDark ? 'Sunny' : 'Moon'" /></el-icon>
  </button>
</template>

<script setup lang="ts">
/**
 * 主题切换按钮
 */
import { computed } from 'vue'
import { useThemeStore } from '@/stores/theme'

const themeStore = useThemeStore()
const isDark = computed(() => themeStore.mode === 'dark')
</script>

<style scoped lang="scss">
.theme-toggle-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: 1px solid var(--btn-border);
  border-radius: 8px;
  background: var(--btn-bg);
  color: var(--btn-text);
  cursor: pointer;
  transition: all 0.2s;

  &:hover {
    color: var(--btn-text-hover);
    background: var(--btn-bg-hover);
    border-color: var(--accent-cyan);
  }
}
</style>
