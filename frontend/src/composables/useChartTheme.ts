/**
 * ECharts 主题色读取（跟随深色/浅色切换）
 */
import { useThemeStore } from '@/stores/theme'
import { computed } from 'vue'

function getCssVar(name: string, fallback: string) {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim() || fallback
}

export function useChartTheme() {
  const themeStore = useThemeStore()

  const colors = computed(() => ({
    cyan: getCssVar('--accent-cyan', '#00d4ff'),
    blue: getCssVar('--accent-blue', '#4da6ff'),
    purple: getCssVar('--accent-purple', '#7b8cff'),
    orange: getCssVar('--accent-orange', '#ff9f43'),
    red: getCssVar('--accent-red', '#ff4757'),
    label: getCssVar('--chart-label', '#8e9aaf'),
    bg: getCssVar('--bg-primary', '#0a0f1a'),
    border: getCssVar('--border-color', 'rgba(0,180,255,0.25)'),
    isDark: themeStore.mode === 'dark',
  }))

  return { colors, themeStore }
}
