<template>
  <!-- 底部负载分布热力图 -->
  <div class="treemap-chart glass-card">
    <div class="card-title">负载分布</div>
    <div ref="chartRef" class="chart-container"></div>
  </div>
</template>

<script setup lang="ts">
/**
 * ECharts 矩形树图 - 展示所有实例负载分布
 * 面积代表 QPS，颜色代表 CPU 使用率
 */
import { ref, watch, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'
import { useChartTheme } from '@/composables/useChartTheme'
import { useDashboardStore } from '@/stores/dashboard'

const store = useDashboardStore()
const { colors, themeStore } = useChartTheme()
const chartRef = ref<HTMLElement>()
let chart: echarts.ECharts | null = null

onMounted(() => {
  if (chartRef.value) {
    chart = echarts.init(chartRef.value, colors.value.isDark ? 'dark' : undefined)
    window.addEventListener('resize', () => chart?.resize())
    renderChart()
  }
})

onUnmounted(() => {
  chart?.dispose()
  window.removeEventListener('resize', () => chart?.resize())
})

function getColor(cpu: number): string {
  const c = colors.value
  if (cpu >= 80) return c.red
  if (cpu >= 50) return c.orange
  if (cpu >= 20) return c.cyan
  return c.blue
}

function renderChart() {
  if (!chart) return
  const data = store.treemap
  const c = colors.value

  const option: echarts.EChartsOption = {
    backgroundColor: 'transparent',
    tooltip: {
      formatter: (params: any) => {
        const d = params.data
        return `${d.name}<br/>QPS: ${d.value}<br/>CPU: ${d.cpu_usage?.toFixed(1)}%`
      },
    },
    series: [{
      type: 'treemap',
      width: '100%',
      height: '100%',
      roam: false,
      nodeClick: false,
      breadcrumb: { show: false },
      label: {
        show: true,
        formatter: '{b}\n{c} QPS',
        fontSize: 12,
        color: c.isDark ? '#c8d6e5' : '#1a2838',
      },
      itemStyle: {
        borderColor: c.bg,
        borderWidth: 2,
        gapWidth: 2,
      },
      data: data.map(item => ({
        name: item.name,
        value: Math.max(item.value, 1),
        cpu_usage: item.cpu_usage,
        itemStyle: { color: getColor(item.cpu_usage) },
      })),
    }],
  }
  chart.setOption(option, true)
}

watch(() => store.treemap, renderChart, { deep: true })
watch(() => themeStore.mode, () => {
  if (chartRef.value) {
    chart?.dispose()
    chart = echarts.init(chartRef.value, colors.value.isDark ? 'dark' : undefined)
    renderChart()
  }
})
</script>

<style scoped lang="scss">
.treemap-chart {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.chart-container {
  flex: 1;
  min-height: 150px;
}
</style>
