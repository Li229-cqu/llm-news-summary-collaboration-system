import { defineStore } from 'pinia'
import type { AIGenerateResponse } from '@/api/ai'

export interface AIGenerateParams {
  title_count: number
  summary_type: 'extract' | 'generate'
  summary_style: string
  title_style: string
  summary_length: 'short' | 'long' | 'both'
}

export interface NewsSource {
  id: number | string
  title: string
  content: string
}

const DEFAULT_PARAMS: AIGenerateParams = {
  title_count: 3,
  summary_type: 'generate',
  summary_style: '简明扼要',
  title_style: '客观新闻型',
  summary_length: 'both',
}

export const useAIDraftStore = defineStore('aiDraft', {
  state: () => ({
    sourceNewsId: null as number | string | null,
    sourceTitle: '',
    sourceContent: '',
    inputText: '',
    params: { ...DEFAULT_PARAMS },
    result: null as AIGenerateResponse | null,
    loading: false,
    error: '',
  }),

  actions: {
    /** 从新闻详情导入新闻信息 */
    setFromNews(news: NewsSource) {
      this.sourceNewsId = news.id
      this.sourceTitle = news.title
      this.sourceContent = news.content
      this.inputText = news.content
    },

    /** 清空来源新闻信息 */
    clearSourceNews() {
      this.sourceNewsId = null
      this.sourceTitle = ''
      this.sourceContent = ''
    },

    /** 设置输入文本 */
    setInputText(text: string) {
      this.inputText = text
    },

    /** 合并更新参数 */
    setParams(params: Partial<AIGenerateParams>) {
      this.params = {
        ...this.params,
        ...params,
      }
    },

    /** 恢复默认参数 */
    resetParams() {
      this.params = { ...DEFAULT_PARAMS }
    },

    /** 保存生成结果 */
    setResult(result: AIGenerateResponse) {
      this.result = result
    },

    /** 清空生成结果 */
    clearResult() {
      this.result = null
    },

    /** 设置加载状态 */
    setLoading(loading: boolean) {
      this.loading = loading
    },

    /** 设置错误信息 */
    setError(error: string) {
      this.error = error
    },

    /** 重置草稿（清空所有输入、结果、错误，恢复默认参数） */
    resetDraft() {
      this.sourceNewsId = null
      this.sourceTitle = ''
      this.sourceContent = ''
      this.inputText = ''
      this.params = { ...DEFAULT_PARAMS }
      this.result = null
      this.error = ''
      this.loading = false
    },
  },
})
