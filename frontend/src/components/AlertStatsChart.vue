<template>
  <div class="alert-stats glass-card">
    <div class="card-title">告警统计</div>
    <div class="stats-summary">
      <div class="stat-item">
        <span class="stat-num">{{ stats.today || 0 }}</span>
        <span class="stat-label">今日</span>
      </div>
      <div class="stat-item">
        <span class="stat-num critical">{{ stats.by_severity?.critical || 0 }}</span>
        <span class="stat-label">紧急</span>
      </div>
      <div class="stat-item">
        <span class="stat-num warning">{{ stats.by_severity?.warning || 0 }}</span>
        <span class="stat-label">警告</span>
      </div>
      <div class="stat-item">
        <span class="stat-num">{{ stats.total || 0 }}</span>
        <span class="stat-label">7日合计</span>
      </div>
    </div>
    <div ref="chartRef" class="chart-area"></div>
  </div>
</template>

<script setup lang="ts">
/**
 * 告警统计柱状图（近7天趋势）
 */
import { ref, onMounted, onUnmounted, watch } from 'vue'
import * as echarts from 'echarts'
import api from '@/api'
import { useChartTheme } from '@/composables/useChartTheme'

const chartRef = ref<HTMLElement>()
let chart: echarts.ECharts | null = null
const stats = ref<any>({})
const { colors, themeStore } = useChartTheme()

async function fetchStats() {
  const res = await api.get('/dashboard/alert-stats', { params: { days: 7 } })
  stats.value = res.data.data
  renderChart()
}

function renderChart() {
  if (!chart || !stats.value.daily) return
  const c = colors.value
  chart.setOption({
    backgroundColor: 'transparent',
    grid: { left: 40, right: 10, top: 10, bottom: 25 },
    xAxis: {
      type: 'category',
      data: stats.value.daily.map((d: any) => d.date),
      axisLabel: { color: c.label, fontSize: 10 },
    },
    yAxis: {
      type: 'value',
      minInterval: 1,
      splitLine: { lineStyle: { color: c.border } },
      axisLabel: { color: c.label, fontSize: 10 },
    },
    series: [{
      type: 'bar',
      data: stats.value.daily.map((d: any) => d.count),
      itemStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: c.cyan },
          { offset: 1, color: c.purple + '60' },
        ]),
        borderRadius: [4, 4, 0, 0],
      },
    }],
    tooltip: { trigger: 'axis' },
  }, true)
}

onMounted(() => {
  if (chartRef.value) {
    chart = echarts.init(chartRef.value, colors.value.isDark ? 'dark' : undefined)
    fetchStats()
    window.addEventListener('resize', () => chart?.resize())
  }
})

onUnmounted(() => {
  chart?.dispose()
})

watch(() => themeStore.mode, () => {
  if (chartRef.value) {
    chart?.dispose()
    chart = echarts.init(chartRef.value, colors.value.isDark ? 'dark' : undefined)
    renderChart()
  }
})
</script>

<style scoped lang="scss">
.alert-stats {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.stats-summary {
  display: flex;
  gap: 16px;
  margin-bottom: 8px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;

  .stat-num {
    font-size: 20px;
    font-weight: 700;
    color: var(--accent-cyan);

    &.critical { color: var(--accent-red); }
    &.warning { color: var(--accent-orange); }
  }

  .stat-label {
    font-size: 11px;
    color: var(--text-secondary);
  }
}

.chart-area {
  flex: 1;
  min-height: 100px;
}
</style>
