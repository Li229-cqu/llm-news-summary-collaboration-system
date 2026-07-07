import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { logoutApi } from '@/api/auth'
import { getUserProfileApi } from '@/api/user'

const TOKEN_STORAGE_KEY = 'llm_news_token'
const USER_INFO_STORAGE_KEY = 'llm_news_user_info'

export interface UserInfo {
  id: number
  username: string
  nickname: string
  role: string
  avatar: string
  email: string
  phone: string
  status: number
}

function isValidUserInfo(value: unknown): value is UserInfo {
  if (typeof value !== 'object' || value === null) {
    return false
  }

  const user = value as Partial<UserInfo>
  return (
    typeof user.id === 'number' &&
    typeof user.username === 'string' &&
    typeof user.nickname === 'string' &&
    typeof user.role === 'string' &&
    typeof user.avatar === 'string' &&
    typeof user.email === 'string' &&
    typeof user.phone === 'string' &&
    typeof user.status === 'number'
  )
}

export const useUserStore = defineStore('user', () => {
  const token = ref('')
  const userInfo = ref<UserInfo | null>(null)

  const isLoggedIn = computed(() => Boolean(token.value && userInfo.value))
  const role = computed(() => userInfo.value?.role ?? '')
  const isAdmin = computed(() => role.value === 'admin')
  const isEditor = computed(() => role.value === 'editor')
  const isEditorOrAdmin = computed(() => isEditor.value || isAdmin.value)

  function setToken(value: string) {
    token.value = value
    localStorage.setItem(TOKEN_STORAGE_KEY, value)
  }

  function setUserInfo(user: UserInfo) {
    userInfo.value = user
    localStorage.setItem(USER_INFO_STORAGE_KEY, JSON.stringify(user))
  }

  function setLoginInfo(loginToken: string, user: UserInfo) {
    setToken(loginToken)
    setUserInfo(user)
  }

  function clearUser() {
    token.value = ''
    userInfo.value = null
    localStorage.removeItem(TOKEN_STORAGE_KEY)
    localStorage.removeItem(USER_INFO_STORAGE_KEY)
  }

  async function logout() {
    try {
      await logoutApi()
    } catch {
    }
    clearUser()
  }

  function loadFromStorage() {
    const storedToken = localStorage.getItem(TOKEN_STORAGE_KEY)
    const storedUserInfo = localStorage.getItem(USER_INFO_STORAGE_KEY)

    if (!storedToken || !storedUserInfo) {
      clearUser()
      return false
    }

    try {
      const parsedUserInfo = JSON.parse(storedUserInfo) as UserInfo
      if (!isValidUserInfo(parsedUserInfo)) {
        clearUser()
        return false
      }

      token.value = storedToken
      userInfo.value = parsedUserInfo
      return true
    } catch {
      clearUser()
      return false
    }
  }

  /**
   * 从服务器同步最新用户信息（头像、昵称等）。
   * 解决跨设备更新头像后其他设备仍显示旧头像的问题。
   */
  async function syncProfile() {
    if (!token.value) return
    try {
      const profile = await getUserProfileApi()
      setUserInfo(profile)
    } catch {
      // 请求失败时保留本地缓存数据
    }
  }

  return {
    token,
    userInfo,
    isLoggedIn,
    role,
    isAdmin,
    isEditor,
    isEditorOrAdmin,
    setToken,
    setUserInfo,
    setLoginInfo,
    clearUser,
    logout,
    loadFromStorage,
    syncProfile,
  }
})
