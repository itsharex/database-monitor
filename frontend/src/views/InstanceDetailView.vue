<template>
  <div class="detail-page">
    <header class="detail-header">
      <div class="header-left">
        <el-button @click="$router.back()" icon="ArrowLeft">返回大屏</el-button>
        <h2>{{ snapshot?.instance?.name || '实例详情' }}</h2>
        <span class="status-dot" :class="snapshot?.status"></span>
      </div>
      <ThemeToggle />
    </header>

    <div class="detail-grid" v-if="snapshot">
      <!-- 指标概览卡片 -->
      <div class="metric-cards">
        <div class="metric-card glass-card" v-for="m in metricCards" :key="m.key">
          <div class="metric-label">{{ m.label }}</div>
          <div class="metric-value">{{ formatMetric(m.key) }}</div>
        </div>
      </div>

      <!-- 指标趋势图 -->
      <div class="detail-card glass-card" v-for="metric in detailMetrics" :key="metric.name">
        <div class="card-title">{{ metric.label }}</div>
        <div :ref="(el) => setChartRef(metric.name, el as HTMLElement)" class="mini-chart"></div>
      </div>

      <!-- 慢查询列表 -->
      <div class="detail-card glass-card slow-query-card">
        <div class="card-title">慢查询记录（最近 {{ slowQueries.length }} 条）</div>
        <el-table :data="slowQueries" size="small" max-height="300" style="width: 100%">
          <el-table-column prop="query_time" label="耗时(s)" width="80" />
          <el-table-column prop="rows_examined" label="扫描行数" width="90" />
          <el-table-column prop="sql_text" label="SQL" show-overflow-tooltip />
        </el-table>
        <div v-if="slowQueries.length === 0" class="empty-tip">暂无慢查询数据</div>
      </div>

      <!-- 参数配置 -->
      <div class="detail-card glass-card params-card">
        <div class="card-title">实例参数</div>
        <div class="param-list">
          <div class="param-item" v-for="(v, k) in snapshot.params" :key="k">
            <span class="param-key">{{ k }}</span>
            <span class="param-val">{{ v }}</span>
          </div>
        </div>
      </div>

      <!-- 优化建议 -->
      <div class="detail-card glass-card suggestion-card">
        <div class="card-title">智能优化建议</div>
        <ul class="suggestion-list">
          <li v-for="(s, i) in snapshot.suggestions" :key="i">{{ s }}</li>
        </ul>
      </div>

      <!-- 最近告警 -->
      <div class="detail-card glass-card alerts-card">
        <div class="card-title">相关告警</div>
        <div v-for="a in relatedAlerts" :key="a.id" class="alert-row">
          <span class="severity-tag" :class="a.severity">{{ a.severity }}</span>
          <span>{{ a.message }}</span>
          <span class="alert-time">{{ formatTime(a.created_at) }}</span>
        </div>
        <div v-if="relatedAlerts.length === 0" class="empty-tip">暂无相关告警</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * 实例详情下钻页 — 指标、慢查询、参数、建议、告警
 */
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import dayjs from 'dayjs'
import * as echarts from 'echarts'
import api from '@/api'
import ThemeToggle from '@/components/ThemeToggle.vue'

const route = useRoute()
const snapshot = ref<any>(null)
const slowQueries = ref<any[]>([])
const relatedAlerts = ref<any[]>([])
const chartRefs: Record<string, HTMLElement> = {}
const charts: Record<string, echarts.ECharts> = {}

const detailMetrics = [
  { name: 'qps', label: 'QPS 趋势' },
  { name: 'connections', label: '连接数趋势' },
  { name: 'cpu_usage', label: 'CPU 使用率' },
  { name: 'slow_queries', label: '慢查询数' },
]

const metricCards = [
  { key: 'qps', label: 'QPS' },
  { key: 'connections', label: '连接数' },
  { key: 'cpu_usage', label: 'CPU %' },
  { key: 'slow_queries', label: '慢查询' },
]

function setChartRef(name: string, el: HTMLElement | null) {
  if (el) chartRefs[name] = el
}

function formatMetric(key: string) {
  const v = snapshot.value?.metrics?.[key]
  if (v === undefined) return '-'
  return Number.isInteger(v) ? v : v.toFixed(1)
}

function formatTime(t: string) {
  return dayjs(t).format('MM-DD HH:mm')
}

onMounted(async () => {
  const id = Number(route.params.id)
  try {
    const res = await api.get(`/instances/${id}/snapshot`)
    snapshot.value = res.data.data
    slowQueries.value = res.data.data.slow_queries || []
  } catch (e) { /* */ }

  try {
    const alertRes = await api.get('/alerts', { params: { limit: 10 } })
    relatedAlerts.value = (alertRes.data.data || []).filter(
      (a: any) => a.instance_id === id
    )
  } catch (e) { /* */ }

  for (const metric of detailMetrics) {
    try {
      const res = await api.get(`/dashboard/metrics/${id}`, {
        params: { metrics: metric.name, range: '-1h' },
      })
      const series = res.data.data[0]
      if (series && chartRefs[metric.name]) {
        const chart = echarts.init(chartRefs[metric.name], 'dark')
        charts[metric.name] = chart
        chart.setOption({
          backgroundColor: 'transparent',
          grid: { left: 40, right: 10, top: 10, bottom: 25 },
          xAxis: { type: 'time', axisLabel: { color: '#8e9aaf', fontSize: 10 } },
          yAxis: { type: 'value', splitLine: { lineStyle: { color: 'rgba(0,255,255,0.08)' } }, axisLabel: { color: '#8e9aaf', fontSize: 10 } },
          series: [{
            type: 'line', smooth: true, symbol: 'none',
            areaStyle: { color: 'rgba(0,212,255,0.15)' },
            lineStyle: { color: '#00d4ff' },
            data: series.points.map((p: any) => [p.timestamp, p.value]),
          }],
        })
      }
    } catch (e) { /* */ }
  }
})

onUnmounted(() => {
  Object.values(charts).forEach(c => c.dispose())
})
</script>

<style scoped lang="scss">
.detail-page {
  height: 100%;
  padding: 16px;
  overflow-y: auto;
}

.detail-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
  h2 { font-size: 20px; color: var(--accent-cyan); }
}

.metric-cards {
  grid-column: 1 / -1;
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}

.metric-card {
  text-align: center;
  padding: 16px;

  .metric-label { font-size: 12px; color: var(--text-secondary); margin-bottom: 4px; }
  .metric-value { font-size: 24px; font-weight: 700; color: var(--accent-cyan); }
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.detail-card { min-height: 200px; }
.slow-query-card, .suggestion-card, .params-card, .alerts-card { grid-column: span 1; }

.mini-chart { height: 160px; }

.param-list {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.param-item {
  display: flex;
  justify-content: space-between;
  padding: 8px 12px;
  background: var(--btn-bg-hover);
  border-radius: 6px;
  font-size: 13px;

  .param-key { color: var(--text-secondary); }
  .param-val { color: var(--accent-cyan); font-weight: 500; }
}

.suggestion-list {
  list-style: none;
  padding: 0;

  li {
    padding: 8px 12px;
    margin-bottom: 6px;
    border-left: 3px solid var(--accent-cyan);
    background: var(--btn-bg-hover);
    font-size: 13px;
    color: var(--text-secondary);
  }
}

.alert-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 0;
  border-bottom: 1px solid var(--border-color);
  font-size: 13px;
  color: var(--text-secondary);

  .alert-time { margin-left: auto; font-size: 11px; }
}

.severity-tag {
  font-size: 11px;
  padding: 1px 6px;
  border-radius: 3px;
  &.critical { background: rgba(255,71,87,0.2); color: var(--accent-red); }
  &.warning { background: rgba(255,159,67,0.2); color: var(--accent-orange); }
  &.info { background: rgba(0,212,255,0.2); color: var(--accent-cyan); }
}

.empty-tip {
  text-align: center;
  color: var(--text-secondary);
  padding: 20px;
  font-size: 13px;
}
</style>
