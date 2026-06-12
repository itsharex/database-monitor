<template>
  <!-- 数据库实例列表 -->
  <div class="instance-list glass-card">
    <div class="card-title">数据库实例</div>

    <!-- 分组 + 状态筛选 -->
    <div class="filter-bar" v-if="groups.length">
      <select v-model="selectedGroup" class="group-select" @change="onGroupChange">
        <option :value="null">全部分组</option>
        <option v-for="g in groups" :key="g.id" :value="g.id">{{ g.name }}</option>
      </select>
    </div>
    <div class="filter-bar">
      <span
        v-for="s in statusOptions"
        :key="s.value"
        class="filter-tag"
        :class="{ active: statusFilter === s.value }"
        @click="setFilter(s.value)"
      >{{ s.label }}</span>
    </div>

    <!-- 实例列表 -->
    <div class="list-container">
      <div
        v-for="inst in instances"
        :key="inst.id"
        class="instance-item"
        :class="{ selected: selectedId === inst.id }"
        @click="selectInstance(inst)"
        @dblclick="goDetail(inst)"
      >
        <span class="status-dot" :class="inst.status"></span>
        <div class="inst-info">
          <div class="inst-name">{{ inst.name }}</div>
          <div class="inst-type">{{ dbTypeLabel(inst.db_type) }}</div>
        </div>
        <div class="inst-metrics">
          <span>连接: {{ inst.connections || 0 }}</span>
          <span>QPS: {{ inst.qps || 0 }}</span>
        </div>
      </div>
      <div v-if="instances.length === 0" class="empty-tip">暂无实例数据</div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * 左侧数据库实例列表组件
 */
import { computed, ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/api'
import { useDashboardStore } from '@/stores/dashboard'
import type { InstanceItem } from '@/stores/dashboard'

const store = useDashboardStore()
const router = useRouter()
const groups = ref<any[]>([])
const selectedGroup = ref<number | null>(null)

onMounted(async () => {
  try {
    const res = await api.get('/instances/groups')
    groups.value = res.data.data
  } catch (e) { /* */ }
})

function onGroupChange() {
  store.groupFilter = selectedGroup.value
  store.fetchInstances()
}

const instances = computed(() => store.instances)
const statusFilter = computed(() => store.statusFilter)
const selectedId = computed(() => store.selectedInstanceId)

const statusOptions = [
  { label: '全部', value: 'all' },
  { label: '正常', value: 'normal' },
  { label: '告警', value: 'warning' },
  { label: '故障', value: 'critical' },
]

function setFilter(value: string) {
  store.statusFilter = value
  store.fetchInstances()
}

function selectInstance(inst: InstanceItem) {
  store.selectedInstanceId = inst.id
}

function goDetail(inst: InstanceItem) {
  router.push(`/instance/${inst.id}`)
}

function dbTypeLabel(type: string) {
  const map: Record<string, string> = {
    mysql: 'MySQL', postgresql: 'PostgreSQL', redis: 'Redis', mongodb: 'MongoDB',
  }
  return map[type] || type
}
</script>

<style scoped lang="scss">
.instance-list {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.filter-bar {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
}

.group-select {
  width: 100%;
  height: 28px;
  padding: 0 8px;
  border-radius: 6px;
  border: 1px solid var(--border-color);
  background: var(--btn-bg);
  color: var(--text-secondary);
  font-size: 12px;
  outline: none;
  margin-bottom: 4px;
}

.filter-tag {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
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

.list-container {
  flex: 1;
  overflow-y: auto;
}

.instance-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.2s;
  margin-bottom: 4px;

  &:hover, &.selected {
    background: var(--btn-bg-hover);
  }
}

.inst-info { flex: 1; min-width: 0; }
.inst-name {
  font-size: 14px;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.inst-type {
  font-size: 11px;
  color: var(--text-secondary);
}

.inst-metrics {
  display: flex;
  flex-direction: column;
  font-size: 11px;
  color: var(--text-secondary);
  text-align: right;
}

.empty-tip {
  text-align: center;
  color: var(--text-secondary);
  padding: 40px 0;
}
</style>
