/** 统一图片 URL 解析：本地路径补全后端域名，外链直接返回。 */
const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export function resolveImageUrl(path: string | null | undefined): string {
  if (!path) return ''
  if (path.startsWith('http://') || path.startsWith('https://')) return path
  return API_BASE + path
}
