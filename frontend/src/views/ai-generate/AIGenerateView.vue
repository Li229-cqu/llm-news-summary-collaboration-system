<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import AIInputPanel from '@/components/ai/AIInputPanel.vue'
import AIParamPanel from '@/components/ai/AIParamPanel.vue'
import AIGenerateHistory from '@/components/ai/AIGenerateHistory.vue'
import AIGenerateAgentPanel from '@/components/agent/AIGenerateAgentPanel.vue'
import type { AIGenerateResponse } from '@/api/ai'
import { useAIDraftStore } from '@/stores/aiDraft'
import { useNewsEditorAgentStore } from '@/stores/newsEditorAgent'

const aiDraft = useAIDraftStore()
const agentStore = useNewsEditorAgentStore()
const route = useRoute()

type PageState = 'input' | 'history-list' | 'history-detail'
const pageState = ref<PageState>('input')
const selectedRecordId = ref<number | null>(null)
const historyRef = ref<InstanceType<typeof AIGenerateHistory> | null>(null)
const activeRunSignature = ref<string | null>(null)
const inputCollapsed = ref(false)

const canCollapseInput = computed(() => agentStore.status === 'completed')

function buildDraftSignature() {
  return JSON.stringify({
    inputText: aiDraft.inputText.trim(),
    sourceNewsId: aiDraft.sourceNewsId ?? null,
    params: aiDraft.params,
  })
}

function clearGenerationState() {
  aiDraft.clearResult()
  agentStore.clearExecutionState()
  activeRunSignature.value = null
  inputCollapsed.value = false
}

watch(() => agentStore.status, (status) => {
  if (status === 'running') {
    activeRunSignature.value = buildDraftSignature()
    aiDraft.clearResult()
    inputCollapsed.value = false
  }
  if (status === 'idle' || status === 'failed') {
    activeRunSignature.value = null
    aiDraft.clearResult()
    inputCollapsed.value = false
  }
})

watch(
  () => [
    aiDraft.inputText,
    aiDraft.sourceNewsId,
    aiDraft.params.title_count,
    aiDraft.params.summary_type,
    aiDraft.params.summary_style,
    aiDraft.params.title_style,
    aiDraft.params.summary_length,
  ],
  () => {
    if (pageState.value !== 'input') return
    if (agentStore.status === 'running') return
    if (!aiDraft.result && agentStore.status === 'idle') return
    clearGenerationState()
  },
)

function navigateTo(target: 'history' | 'input') {
  if (target === 'history') {
    pageState.value = 'history-list'
    selectedRecordId.value = null
    clearGenerationState()
    nextTick(() => historyRef.value?.loadHistory?.())
    return
  }

  pageState.value = 'input'
  selectedRecordId.value = null
  clearGenerationState()
}

function viewDetail(id: number | string) {
  selectedRecordId.value = Number(id)
  pageState.value = 'history-detail'
}

function backToList() {
  pageState.value = 'history-list'
  selectedRecordId.value = null
  nextTick(() => historyRef.value?.loadHistory?.())
}

function backToInput() {
  pageState.value = 'input'
  selectedRecordId.value = null
  clearGenerationState()
}

function handleReuse() {
  pageState.value = 'input'
  aiDraft.clearSourceNews()
  clearGenerationState()
}

function loadNewsDraftFromSession() {
  const raw = sessionStorage.getItem('ai_draft_from_news')
  if (!raw) return
  try {
    const draft = JSON.parse(raw) as { source?: string; news_id?: number | string; title?: string; content?: string }
    if (draft.source !== 'news' || !draft.content?.trim()) return
    aiDraft.setFromNews({ id: draft.news_id ?? '', title: draft.title ?? '', content: draft.content })
  } catch {
    // ignore malformed draft payloads
  }
}

function syncDraftFromNewsRoute() {
  if (String(route.query.source ?? '') !== 'news') return
  const rid = String(route.query.newsId ?? '').trim()
  const current = String(aiDraft.sourceNewsId ?? '').trim()
  if (rid && current === rid && aiDraft.inputText.trim()) return
  clearGenerationState()
  loadNewsDraftFromSession()
}

async function handleAgentDone(result: AIGenerateResponse | null) {
  const currentSignature = buildDraftSignature()
  if (activeRunSignature.value && currentSignature !== activeRunSignature.value) {
    clearGenerationState()
    return
  }

  if (result) {
    aiDraft.setResult(result)
  } else {
    aiDraft.clearResult()
  }

  activeRunSignature.value = null
  await nextTick()
  historyRef.value?.loadHistory?.()
}

function handleToggleInputCollapse() {
  if (!canCollapseInput.value) return
  inputCollapsed.value = !inputCollapsed.value
}

onMounted(() => {
  syncDraftFromNewsRoute()
})

onUnmounted(() => {
  aiDraft.resetDraft()
  clearGenerationState()
  sessionStorage.removeItem('ai_draft_from_news')
})

watch(() => [route.query.source, route.query.newsId], () => {
  syncDraftFromNewsRoute()
})
</script>

<template>
  <div class="ai-shell">
    <div class="ai-shell__frame">
      <aside class="ai-shell__side">
        <AIParamPanel @navigate="(t: 'history' | 'input') => navigateTo(t)" />
      </aside>

      <main class="ai-shell__main">
        <template v-if="pageState === 'input'">
          <section class="main-stack">
            <AIInputPanel
              :collapsed="inputCollapsed"
              :can-collapse="canCollapseInput"
              @toggle-collapse="handleToggleInputCollapse"
            />
            <AIGenerateAgentPanel
              :input-text="aiDraft.inputText"
              :params="aiDraft.params"
              :use-mock="false"
              @done="handleAgentDone"
            />
          </section>
        </template>

        <template v-else-if="pageState === 'history-list'">
          <AIGenerateHistory
            ref="historyRef"
            mode="list"
            @back-to-input="backToInput"
            @view-detail="viewDetail"
          />
        </template>

        <template v-else>
          <AIGenerateHistory
            ref="historyRef"
            mode="detail"
            :record-id="selectedRecordId"
            @back-to-input="backToInput"
            @back-to-list="backToList"
            @reuse="handleReuse"
          />
        </template>
      </main>
    </div>
  </div>
</template>

<style scoped>
.ai-shell {
  height: calc(100vh - var(--header-height));
  overflow: hidden;
  background:
    radial-gradient(circle at top left, rgba(217, 45, 32, 0.08), transparent 28%),
    linear-gradient(180deg, #f6f7fb 0%, #f6f7fb 100%);
}

.ai-shell__frame {
  display: flex;
  height: 100%;
  min-width: 0;
}

.ai-shell__side {
  width: 270px;
  flex-shrink: 0;
  overflow-y: auto;
  border-right: 1px solid #f2c6c3;
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(10px);
}

.ai-shell__main {
  flex: 1;
  min-width: 0;
  overflow-y: auto;
  padding: 18px 22px 24px;
}

.main-stack {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

@media (max-width: 900px) {
  .ai-shell {
    height: auto;
    min-height: calc(100vh - var(--header-height));
    overflow: visible;
  }

  .ai-shell__frame {
    flex-direction: column;
    height: auto;
  }

  .ai-shell__side {
    width: 100%;
    max-height: 42vh;
    border-right: none;
    border-bottom: 1px solid #f2c6c3;
  }

  .ai-shell__main {
    padding: 16px;
    overflow: visible;
  }
}
</style>
