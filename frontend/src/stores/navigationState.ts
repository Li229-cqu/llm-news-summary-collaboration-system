/** 跨路由导航状态记忆（仅运行时，不持久化，刷新丢失） */
import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useNavigationStateStore = defineStore('navigationState', () => {
  const communityLastState = ref<{
    routePath?: string
    activeFeedTab?: string
    contentMode?: string
    selectedPostId?: number | string | null
    aiActiveSessionId?: number | null
  }>({})

  const profileLastState = ref<{
    routePath?: string
    activeTab?: string
  }>({})

  function saveCommunityState(state: {
    routePath?: string; activeFeedTab?: string; contentMode?: string
    selectedPostId?: number | string | null; aiActiveSessionId?: number | null
  }) { communityLastState.value = { ...state } }

  function saveProfileState(state: { routePath?: string; activeTab?: string }) {
    profileLastState.value = { ...state }
  }

  function clearCommunityState() { communityLastState.value = {} }
  function clearProfileState() { profileLastState.value = {} }
  function clearAll() { clearCommunityState(); clearProfileState() }

  return { communityLastState, profileLastState, saveCommunityState, saveProfileState, clearCommunityState, clearProfileState, clearAll }
})
