/**
 * 带认证的文件下载工具
 */
import api from '@/api'

export async function downloadWithAuth(url: string, filename: string) {
  const res = await api.get(url, { responseType: 'blob' })
  const blob = new Blob([res.data])
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = filename
  link.click()
  URL.revokeObjectURL(link.href)
}

export async function postDownloadWithAuth(url: string, data: object, filename: string) {
  const res = await api.post(url, data, { responseType: 'blob' })
  const blob = new Blob([res.data])
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = filename
  link.click()
  URL.revokeObjectURL(link.href)
}
