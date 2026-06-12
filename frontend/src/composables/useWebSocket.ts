/**
 * WebSocket 连接 composable
 * 用于实时指标和告警推送
 */
import { onMounted, onUnmounted, ref } from 'vue'

export function useWebSocket(path: string, onMessage: (data: any) => void) {
  const connected = ref(false)
  let ws: WebSocket | null = null
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null

  function connect() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    ws = new WebSocket(`${protocol}//${host}${path}`)

    ws.onopen = () => {
      connected.value = true
    }

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data)
        onMessage(msg)
      } catch (e) {
        console.error('WebSocket 消息解析失败', e)
      }
    }

    ws.onclose = () => {
      connected.value = false
      // 5秒后自动重连
      reconnectTimer = setTimeout(connect, 5000)
    }

    ws.onerror = () => {
      ws?.close()
    }
  }

  onMounted(() => connect())

  onUnmounted(() => {
    if (reconnectTimer) clearTimeout(reconnectTimer)
    ws?.close()
  })

  return { connected }
}
