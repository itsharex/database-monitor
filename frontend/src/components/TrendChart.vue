<template>
  <!-- 指标趋势图 -->
  <div class="trend-chart glass-card">
    <div class="chart-header">
      <div class="card-title">实时趋势</div>
      <div class="chart-actions">
        <HistoryReplay
          :instance-id="store.selectedInstanceId"
          @replay="onReplay"
          @exit="onExitReplay"
        />
        <div class="time-range">
          <span
            v-for="r in ranges"
            :key="r.value"
            class="range-btn"
            :class="{ active: currentRange === r.value && !isReplay }"
            @click="changeRange(r.value)"
          >{{ r.label }}</span>
        </div>
      </div>
    </div>
    <div ref="chartRef" class="chart-container"></div>
  </div>
</template>

<script setup lang="ts">
/**
 * ECharts 趋势图组件
 * 支持多指标折线图 + 面积渐变填充
 */
import { ref, watch, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'
import api from '@/api'
import { useChartTheme } from '@/composables/useChartTheme'
import { useDashboardStore } from '@/stores/dashboard'
import HistoryReplay from '@/components/HistoryReplay.vue'

const store = useDashboardStore()
const { colors, themeStore } = useChartTheme()
const lastSeries = ref<any[]>([])
const isReplay = ref(false)
const chartRef = ref<HTMLElement>()
let chart: echarts.ECharts | null = null
const currentRange = ref('-15m')

const ranges = [
  { label: '15m', value: '-15m' },
  { label: '1h', value: '-1h' },
  { label: '6h', value: '-6h' },
  { label: '24h', value: '-24h' },
]

const metricKeys = [
  { name: 'qps', label: 'QPS', key: 'cyan' as const },
  { name: 'connections', label: '连接数', key: 'purple' as const },
  { name: 'slow_queries', label: '慢查询', key: 'orange' as const },
  { name: 'cpu_usage', label: 'CPU%', key: 'red' as const },
]

onMounted(() => {
  if (chartRef.value) {
    chart = echarts.init(chartRef.value, colors.value.isDark ? 'dark' : undefined)
    window.addEventListener('resize', handleResize)
    fetchData()
  }
})

onUnmounted(() => {
  chart?.dispose()
  window.removeEventListener('resize', handleResize)
})

function handleResize() {
  chart?.resize()
}

async function fetchData() {
  const instanceId = store.selectedInstanceId
  if (!instanceId || !chart) return

  try {
    const res = await api.get(`/dashboard/metrics/${instanceId}`, {
      params: {
        metrics: 'qps,connections,slow_queries,cpu_usage',
        range: currentRange.value,
      },
    })
    lastSeries.value = res.data.data
    renderChart(lastSeries.value)
  } catch (e) {
    console.error('获取趋势数据失败', e)
  }
}

function renderChart(seriesData: any[]) {
  if (!chart) return
  const c = colors.value

  const option: echarts.EChartsOption = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' },
    },
    legend: {
      data: metricKeys.map(m => m.label),
      textStyle: { color: c.label },
      top: 0,
    },
    grid: { left: 50, right: 20, top: 40, bottom: 30 },
    xAxis: {
      type: 'time',
      axisLine: { lineStyle: { color: c.border } },
      axisLabel: { color: c.label },
    },
    yAxis: {
      type: 'value',
      splitLine: { lineStyle: { color: c.border } },
      axisLabel: { color: c.label },
    },
    series: seriesData.map((s: any) => {
      const config = metricKeys.find(m => m.name === s.metric_name)
      const color = config ? c[config.key] : c.cyan
      return {
        name: config?.label || s.metric_name,
        type: 'line',
        smooth: true,
        symbol: 'none',
        lineStyle: { width: 2, color },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: color + '40' },
            { offset: 1, color: color + '05' },
          ]),
        },
        data: s.points.map((p: any) => [p.timestamp, p.value]),
      }
    }),
  }
  chart.setOption(option, true)
}

function changeRange(range: string) {
  isReplay.value = false
  currentRange.value = range
  fetchData()
}

function onReplay(series: any[]) {
  isReplay.value = true
  lastSeries.value = series
  renderChart(series)
}

function onExitReplay() {
  isReplay.value = false
  fetchData()
}

watch(() => store.selectedInstanceId, () => fetchData())
watch(() => themeStore.mode, () => {
  if (chartRef.value) {
    chart?.dispose()
    chart = echarts.init(chartRef.value, colors.value.isDark ? 'dark' : undefined)
    if (lastSeries.value.length) renderChart(lastSeries.value)
  }
})
</script>

<style scoped lang="scss">
.trend-chart {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chart-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.time-range {
  display: flex;
  gap: 4px;
}

.range-btn {
  padding: 2px 10px;
  font-size: 12px;
  border-radius: 4px;
  cursor: pointer;
  color: var(--text-secondary);
  border: 1px solid var(--border-color);
  background: var(--btn-bg);
  transition: all 0.2s;

  &.active, &:hover {
    color: var(--accent-cyan);
    border-color: var(--accent-cyan);
    background: var(--btn-bg-hover);
  }
}

.chart-container {
  flex: 1;
  min-height: 200px;
}
</style>
