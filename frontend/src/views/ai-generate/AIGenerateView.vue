<script setup lang="ts">
import { nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import AIInputPanel from '@/components/ai/AIInputPanel.vue'
import AIParamPanel from '@/components/ai/AIParamPanel.vue'
import AIGenerateHistory from '@/components/ai/AIGenerateHistory.vue'
import AgentInlinePanel from '@/components/agent/AgentInlinePanel.vue'
import { useAIDraftStore } from '@/stores/aiDraft'
import { useNewsEditorAgentStore } from '@/stores/newsEditorAgent'

const aiDraft = useAIDraftStore()
const agentStore = useNewsEditorAgentStore()
const route = useRoute()

type PageState = 'input' | 'history-list' | 'history-detail'
const pageState = ref<PageState>('input')
const selectedRecordId = ref<number | null>(null)
const historyRef = ref<InstanceType<typeof AIGenerateHistory> | null>(null)

function navigateTo(target: 'history' | 'input') {
  if (target === 'history') {
    pageState.value = 'history-list'
    selectedRecordId.value = null
    nextTick(() => historyRef.value?.loadHistory?.())
  } else {
    pageState.value = 'input'
    selectedRecordId.value = null
  }
}
function viewDetail(id: number) { selectedRecordId.value = id; pageState.value = 'history-detail' }
function backToList() { pageState.value = 'history-list'; selectedRecordId.value = null; nextTick(() => historyRef.value?.loadHistory?.()) }
function backToInput() { pageState.value = 'input'; selectedRecordId.value = null }
function handleReuse() { pageState.value = 'input' }

function loadNewsDraftFromSession() {
  const raw = sessionStorage.getItem('ai_draft_from_news')
  if (!raw) return
  try {
    const d = JSON.parse(raw) as { source?: string; news_id?: number | string; title?: string; content?: string }
    if (d.source !== 'news' || !d.content?.trim()) return
    aiDraft.setFromNews({ id: d.news_id ?? '', title: d.title ?? '', content: d.content })
  } catch { /* */ }
}
function syncDraftFromNewsRoute() {
  if (String(route.query.source ?? '') !== 'news') return
  const rid = String(route.query.newsId ?? '').trim()
  const cur = String(aiDraft.sourceNewsId ?? '').trim()
  if (rid && cur === rid && aiDraft.inputText.trim()) return
  loadNewsDraftFromSession()
}
async function handleAgentDone() { await nextTick(); historyRef.value?.loadHistory?.() }

onMounted(() => { syncDraftFromNewsRoute() })
onUnmounted(() => { aiDraft.resetDraft(); agentStore.disconnect(); sessionStorage.removeItem('ai_draft_from_news') })
watch(() => [route.query.source, route.query.newsId], () => { syncDraftFromNewsRoute() })
</script>

<template>
  <div class="ai-wb">
    <div class="ai-wb__body">
      <aside class="ai-wb__side">
        <AIParamPanel @navigate="(t: 'history' | 'input') => navigateTo(t)" />
      </aside>
      <main class="ai-wb__main">
        <template v-if="pageState === 'input'">
          <AIInputPanel />
          <AgentInlinePanel :input-text="aiDraft.inputText" :params="aiDraft.params" :use-mock="false" @done="handleAgentDone" />
        </template>
        <template v-if="pageState === 'history-list'">
          <AIGenerateHistory ref="historyRef" mode="list" @back-to-input="backToInput" @view-detail="viewDetail" />
        </template>
        <template v-if="pageState === 'history-detail'">
          <AIGenerateHistory ref="historyRef" mode="detail" :record-id="selectedRecordId" @back-to-input="backToInput" @back-to-list="backToList" @reuse="handleReuse" />
        </template>
      </main>
    </div>
  </div>
</template>

<style scoped>
.ai-wb { height: calc(100vh - var(--header-height)); overflow: hidden; background: var(--color-bg); }
.ai-wb__body { display: flex; height: 100%; }
.ai-wb__side { width: 260px; flex-shrink: 0; overflow-y: auto; border-right: 1px solid var(--color-border); background: var(--color-bg-card); }
.ai-wb__main { flex: 1; min-width: 0; overflow-y: auto; padding: 24px 28px; display: flex; flex-direction: column; gap: 18px; }
@media (max-width: 900px) {
  .ai-wb__body { flex-direction: column; }
  .ai-wb__side { width: 100%; max-height: 40vh; border-right: none; border-bottom: 1px solid var(--color-border); }
  .ai-wb__main { padding: 16px; }
}
</style>
