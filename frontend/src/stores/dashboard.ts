/**
 * 大屏数据状态管理
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/api'

export interface KPI {
  total_instances: number
  abnormal_instances: number
  avg_qps: number
  total_connections: number
  today_alerts: number
  health_score: number
  total_instances_trend: number
  abnormal_instances_trend: number
  avg_qps_trend: number
  total_connections_trend: number
  today_alerts_trend: number
  health_score_trend: number
}

export interface InstanceItem {
  id: number
  name: string
  db_type: string
  status: string
  connections: number
  qps: number
  cpu_usage: number
  group_id?: number
  host: string
  port: number
}

export interface AlertItem {
  id: number
  instance_name: string
  severity: string
  title: string
  message: string
  created_at: string
}

export interface TreemapItem {
  name: string
  instance_id: number
  value: number
  cpu_usage: number
  status: string
}

export const useDashboardStore = defineStore('dashboard', () => {
  const kpi = ref<KPI>({
    total_instances: 0,
    abnormal_instances: 0,
    avg_qps: 0,
    total_connections: 0,
    today_alerts: 0,
    health_score: 100,
    total_instances_trend: 0,
    abnormal_instances_trend: 0,
    avg_qps_trend: 0,
    total_connections_trend: 0,
    today_alerts_trend: 0,
    health_score_trend: 0,
  })
  const instances = ref<InstanceItem[]>([])
  const alerts = ref<AlertItem[]>([])
  const treemap = ref<TreemapItem[]>([])
  const selectedInstanceId = ref<number | null>(null)
  const refreshInterval = ref(10) // 秒
  const statusFilter = ref('all')
  const groupFilter = ref<number | null>(null)

  async function fetchKPI() {
    const res = await api.get('/dashboard/kpi')
    kpi.value = res.data.data
  }

  async function fetchInstances() {
    const params: Record<string, string | number> = {}
    if (statusFilter.value !== 'all') params.status = statusFilter.value
    if (groupFilter.value) params.group_id = groupFilter.value
    const res = await api.get('/dashboard/instances', { params })
    instances.value = res.data.data
  }

  async function fetchTreemap() {
    const res = await api.get('/dashboard/treemap')
    treemap.value = res.data.data
  }

  async function fetchAlerts() {
    const res = await api.get('/alerts', { params: { limit: 20 } })
    alerts.value = res.data.data
  }

  function updateFromWebSocket(data: any) {
    if (data.kpi) kpi.value = data.kpi
    if (data.instances) instances.value = data.instances
    if (data.treemap) treemap.value = data.treemap
  }

  function updateAlertsFromWebSocket(data: AlertItem[]) {
    alerts.value = data
  }

  return {
    kpi, instances, alerts, treemap,
    selectedInstanceId, refreshInterval, statusFilter, groupFilter,
    fetchKPI, fetchInstances, fetchTreemap, fetchAlerts,
    updateFromWebSocket, updateAlertsFromWebSocket,
  }
})
