<template>
  <div class="history-replay">
    <button class="toolbar-btn" :class="{ active: enabled }" @click="toggle">
      <el-icon><Clock /></el-icon>历史回放
    </button>
    <div v-if="enabled" class="replay-panel">
      <el-date-picker
        v-model="replayTime"
        type="datetime"
        placeholder="选择历史时间点"
        size="small"
        value-format="YYYY-MM-DDTHH:mm:ss"
        @change="loadHistory"
      />
      <button class="toolbar-btn" @click="exitReplay">返回实时</button>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * 历史回放：选择时间点查看当时的指标趋势
 */
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/api'

const emit = defineEmits<{
  replay: [series: any[]]
  exit: []
}>()

const props = defineProps<{ instanceId: number | null }>()

const enabled = ref(false)
const replayTime = ref('')

function toggle() {
  enabled.value = !enabled.value
  if (!enabled.value) exitReplay()
}

async function loadHistory() {
  if (!props.instanceId || !replayTime.value) return
  try {
    const res = await api.get(`/dashboard/history/${props.instanceId}`, {
      params: { at: replayTime.value },
    })
    emit('replay', res.data.data.series)
    ElMessage.success('已加载历史数据')
  } catch (e) {
    ElMessage.error('历史数据加载失败')
  }
}

function exitReplay() {
  enabled.value = false
  replayTime.value = ''
  emit('exit')
}
</script>

<style scoped lang="scss">
.history-replay {
  display: flex;
  align-items: center;
  gap: 8px;
}

.replay-panel {
  display: flex;
  align-items: center;
  gap: 6px;
}
</style>
