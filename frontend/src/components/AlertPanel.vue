<template>
  <!-- 告警面板 -->
  <div class="alert-panel glass-card">
    <div class="card-title">实时告警</div>
    <div class="alert-list" ref="listRef">
      <div
        v-for="alert in sortedAlerts"
        :key="alert.id"
        class="alert-item"
        :class="[alert.severity, { blink: alert.isNew }]"
        @click="acknowledgeAlert(alert)"
      >
        <div class="alert-time">{{ formatTime(alert.created_at) }}</div>
        <div class="alert-body">
          <span class="severity-tag" :class="alert.severity">
            {{ severityLabel(alert.severity) }}
          </span>
          <span class="alert-instance">{{ alert.instance_name }}</span>
        </div>
        <div class="alert-message">{{ alert.message }}</div>
      </div>
      <div v-if="alerts.length === 0" class="empty-tip">暂无告警</div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * 右侧告警滚动面板
 * 支持自动滚动、新告警闪烁、确认操作
 */
import { computed, ref, watch, onMounted, onUnmounted } from 'vue'
import dayjs from 'dayjs'
import api from '@/api'
import { useDashboardStore } from '@/stores/dashboard'
import type { AlertItem } from '@/stores/dashboard'

const store = useDashboardStore()
const listRef = ref<HTMLElement>()
let scrollTimer: ReturnType<typeof setInterval> | null = null
const newAlertIds = ref<Set<number>>(new Set())

const alerts = computed(() => store.alerts)

const sortedAlerts = computed(() => {
  const severityOrder: Record<string, number> = { critical: 0, warning: 1, info: 2 }
  return [...alerts.value]
    .sort((a, b) => (severityOrder[a.severity] ?? 9) - (severityOrder[b.severity] ?? 9))
    .map(a => ({ ...a, isNew: newAlertIds.value.has(a.id) }))
})

function formatTime(time: string) {
  return dayjs(time).format('HH:mm:ss')
}

function severityLabel(severity: string) {
  const map: Record<string, string> = { critical: '紧急', warning: '警告', info: '提示' }
  return map[severity] || severity
}

async function acknowledgeAlert(alert: AlertItem) {
  try {
    await api.post(`/alerts/${alert.id}/acknowledge`)
    store.fetchAlerts()
  } catch (e) { /* 忽略 */ }
}

// 检测新告警并闪烁
watch(alerts, (newAlerts, oldAlerts) => {
  const oldIds = new Set((oldAlerts || []).map(a => a.id))
  newAlerts.forEach(a => {
    if (!oldIds.has(a.id)) {
      newAlertIds.value.add(a.id)
      setTimeout(() => newAlertIds.value.delete(a.id), 3000)
    }
  })
})

// 自动滚动
onMounted(() => {
  scrollTimer = setInterval(() => {
    if (listRef.value) {
      const el = listRef.value
      if (el.scrollTop + el.clientHeight >= el.scrollHeight - 10) {
        el.scrollTop = 0
      } else {
        el.scrollTop += 60
      }
    }
  }, 3000)
})

onUnmounted(() => {
  if (scrollTimer) clearInterval(scrollTimer)
})
</script>

<style scoped lang="scss">
.alert-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.alert-list {
  flex: 1;
  overflow-y: auto;
  scroll-behavior: smooth;
}

.alert-item {
  padding: 10px 12px;
  border-radius: 6px;
  margin-bottom: 6px;
  border-left: 3px solid transparent;
  cursor: pointer;
  transition: background 0.2s;

  &.critical { border-left-color: #ff4757; }
  &.warning { border-left-color: #ff9f43; }
  &.info { border-left-color: #00d4ff; }

  &.blink { animation: alertBlink 0.5s ease-in-out 3; }

  &:hover { background: var(--btn-bg-hover); }
}

.alert-time {
  font-size: 11px;
  color: var(--text-secondary);
  margin-bottom: 4px;
}

.alert-body {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.severity-tag {
  font-size: 11px;
  padding: 1px 6px;
  border-radius: 3px;

  &.critical { background: rgba(255, 71, 87, 0.2); color: #ff4757; }
  &.warning { background: rgba(255, 159, 67, 0.2); color: #ff9f43; }
  &.info { background: rgba(0, 212, 255, 0.2); color: var(--accent-cyan); }
}

.alert-instance {
  font-size: 13px;
  font-weight: 500;
}

.alert-message {
  font-size: 12px;
  color: var(--text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.empty-tip {
  text-align: center;
  color: var(--text-secondary);
  padding: 40px 0;
}
</style>
