import axios, { type InternalAxiosRequestConfig } from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'
import pinia from '@/stores'
import { useUserStore } from '@/stores/user'

interface ApiResponse<T = unknown> {
  code: number
  message: string
  data: T
}

interface HandledRequestError extends Error {
  handled?: boolean
}

const TOKEN_STORAGE_KEY = 'llm_news_token'
const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  timeout: 30000,  // 增加到 30 秒，AI 请求可能需要较长时间
})

let lastMessage = ''
let messageTimer: ReturnType<typeof setTimeout> | undefined
let isHandlingUnauthorized = false

function notifyError(message: string) {
  if (lastMessage === message) {
    return
  }

  lastMessage = message
  ElMessage.error(message)
  clearTimeout(messageTimer)
  messageTimer = setTimeout(() => {
    lastMessage = ''
  }, 500)
}

function createHandledError(message: string): HandledRequestError {
  const error: HandledRequestError = new Error(message)
  error.handled = true
  return error
}

function isLoginRequest(url?: string) {
  return url?.includes('/api/auth/login') ?? false
}

async function handleUnauthorized() {
  useUserStore(pinia).clearUser()

  if (isHandlingUnauthorized) {
    return
  }

  isHandlingUnauthorized = true
  notifyError('登录状态已失效，请重新登录')

  if (router.currentRoute.value.path !== '/login') {
    await router.push('/login')
  }

  setTimeout(() => {
    isHandlingUnauthorized = false
  }, 500)
}

async function handleApiError(code: number, message: string) {
  if (code === 401) {
    await handleUnauthorized()
    return
  }

  if (code === 403) {
    notifyError('当前账号无权限访问该资源')
    return
  }

  notifyError(message || '请求处理失败')
}

request.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem(TOKEN_STORAGE_KEY)

    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }

    return config
  },
  (error: unknown) => Promise.reject(error),
)

request.interceptors.response.use(
  async (response) => {
    const result = response.data as ApiResponse

    if (typeof result?.code === 'number') {
      if (result.code !== 200) {
        if (result.code === 401 && isLoginRequest(response.config.url)) {
          return Promise.reject(createHandledError(result.message))
        }

        await handleApiError(result.code, result.message)
        return Promise.reject(createHandledError(result.message))
      }

      return result.data
    }

    return response.data
  },
  async (error: unknown) => {
    if (error instanceof Error && (error as HandledRequestError).handled) {
      return Promise.reject(error)
    }

    if (axios.isAxiosError<ApiResponse>(error)) {
      const apiError = error.response?.data
      const code = apiError?.code ?? error.response?.status
      const message = apiError?.message || error.message || '网络请求失败'

      if (code === 401 && isLoginRequest(error.config?.url)) {
        return Promise.reject(createHandledError(message))
      }

      if (typeof code === 'number') {
        await handleApiError(code, message)
      } else {
        notifyError(message)
      }
    } else {
      notifyError(error instanceof Error ? error.message : '网络请求失败')
    }

    return Promise.reject(error)
  },
)

export default request
