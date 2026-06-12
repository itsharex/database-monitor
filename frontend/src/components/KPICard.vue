<template>
  <!-- KPI 指标卡片 -->
  <div class="kpi-card glass-card">
    <div class="kpi-icon" :style="{ color: iconColor }">
      <el-icon :size="28"><component :is="icon" /></el-icon>
    </div>
    <div class="kpi-content">
      <div class="kpi-label">{{ label }}</div>
      <div class="kpi-value count-animate" :style="{ color: iconColor }">
        {{ formattedValue }}<span v-if="unit" class="kpi-unit">{{ unit }}</span>
      </div>
      <div v-if="trend !== undefined" class="kpi-trend" :class="trend >= 0 ? 'up' : 'down'">
        <el-icon><component :is="trend >= 0 ? 'Top' : 'Bottom'" /></el-icon>
        {{ Math.abs(trend).toFixed(1) }}%
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * KPI 卡片组件
 * 展示顶部 5 个核心指标，带数字滚动动画和环比趋势
 */
import { computed } from 'vue'

const props = defineProps<{
  label: string
  value: number
  unit?: string
  icon: string
  iconColor?: string
  trend?: number
}>()

const formattedValue = computed(() => {
  if (props.value >= 10000) return (props.value / 1000).toFixed(1) + 'k'
  if (Number.isInteger(props.value)) return props.value.toString()
  return props.value.toFixed(1)
})
</script>

<style scoped lang="scss">
.kpi-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  min-height: 100px;
  transition: transform 0.3s, box-shadow 0.3s;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 20px rgba(0, 212, 255, 0.15);
  }
}

.kpi-icon {
  flex-shrink: 0;
  width: 56px;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  background: var(--btn-bg-hover);
}

.kpi-content { flex: 1; }

.kpi-label {
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 4px;
}

.kpi-value {
  font-size: 28px;
  font-weight: 700;
  line-height: 1.2;
}

.kpi-unit {
  font-size: 14px;
  margin-left: 4px;
  opacity: 0.7;
}

.kpi-trend {
  font-size: 12px;
  margin-top: 4px;
  display: flex;
  align-items: center;
  gap: 2px;

  &.up { color: var(--accent-blue); }
  &.down { color: var(--accent-red); }
}
</style>
