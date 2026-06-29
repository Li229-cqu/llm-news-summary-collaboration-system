import { defineStore } from 'pinia'

export type ThemeMode = 'light' | 'dark'

const THEME_STORAGE_KEY = 'llm-news-theme'

function getStoredTheme(): ThemeMode {
  const storedTheme = localStorage.getItem(THEME_STORAGE_KEY)
  return storedTheme === 'dark' ? 'dark' : 'light'
}

export const useThemeStore = defineStore('theme', {
  state: () => ({
    theme: 'light' as ThemeMode,
  }),
  actions: {
    applyTheme(theme: ThemeMode) {
      this.theme = theme
      document.documentElement.classList.toggle('dark', theme === 'dark')
      localStorage.setItem(THEME_STORAGE_KEY, theme)
    },
    initializeTheme() {
      this.applyTheme(getStoredTheme())
    },
    toggleTheme() {
      this.applyTheme(this.theme === 'light' ? 'dark' : 'light')
    },
  },
})
