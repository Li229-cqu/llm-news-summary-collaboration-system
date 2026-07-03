<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Download } from '@element-plus/icons-vue'
import { useAIDraftStore } from '@/stores/aiDraft'
import { getAIHistory, getAIRecordDetail, deleteAIRecord, type AIGenerateRecordItem, type AIGenerateRecordDetail } from '@/api/ai'
import Step7AuditPanel from '@/components/agent/Step7AuditPanel.vue'
import { exportRecordToWord } from '@/utils/exportWord'

const props = defineProps<{ mode: 'list' | 'detail'; recordId?: number | null }>()
const emit = defineEmits<{ (e: 'back-to-input'): void; (e: 'back-to-list'): void; (e: 'view-detail', id: number): void; (e: 'reuse', record: AIGenerateRecordDetail): void }>()

const aiDraft = useAIDraftStore()

// list
const records = ref<AIGenerateRecordItem[]>([])
const listLoading = ref(false)
async function loadHistory() { listLoading.value = true; try { const r = await getAIHistory(); records.value = r.records || [] } catch { /* */ } finally { listLoading.value = false } }

// detail
const detail = ref<AIGenerateRecordDetail | null>(null)
const detailLoading = ref(false)
const detailError = ref('')
async function loadDetail(id: number) { detailLoading.value = true; detailError.value = ''; try { detail.value = await getAIRecordDetail(id) } catch (e: any) { detailError.value = e?.message || '加载失败' } finally { detailLoading.value = false } }

watch(() => props.recordId, (v) => { if (props.mode === 'detail' && v) loadDetail(v) })
onMounted(() => { if (props.mode === 'list') loadHistory(); if (props.mode === 'detail' && props.recordId) loadDetail(props.recordId) })
defineExpose({ loadHistory, loadDetail })

async function handleDelete(r: AIGenerateRecordItem) {
  try { await ElMessageBox.confirm('确定删除？', '删除', { type: 'warning' }); await deleteAIRecord(r.id); ElMessage.success('已删除'); await loadHistory() } catch { /* cancel */ }
}
async function handleReuse(r: AIGenerateRecordItem) {
  try { const d = await getAIRecordDetail(r.id); aiDraft.setInputText(d.input_text); aiDraft.setParams(d.params as any); ElMessage.success('已复用'); emit('reuse', d); emit('back-to-input') } catch { ElMessage.error('复用失败') }
}

// ── 导出 Word ──────────────────────────────────────────
const exportingId = ref<number | string | null>(null)
const exportingDetail = ref(false)

async function handleExport(r: AIGenerateRecordItem) {
  exportingId.value = r.id
  try {
    const d = await getAIRecordDetail(r.id)
    await exportRecordToWord(d)
    ElMessage.success('Word 文档已下载')
  } catch {
    ElMessage.error('导出失败')
  } finally {
    exportingId.value = null
  }
}

async function handleExportDetail() {
  if (!detail.value) return
  exportingDetail.value = true
  try {
    await exportRecordToWord(detail.value)
    ElMessage.success('Word 文档已下载')
  } catch {
    ElMessage.error('导出失败')
  } finally {
    exportingDetail.value = false
  }
}

function riskTag(l: string) { return { low: 'success', medium: 'warning', high: 'danger' }[l] || 'info' as any }
function riskText(l: string) { return { low: '低风险', medium: '中风险', high: '高风险' }[l] || l }
function fmt(s: string, n: number) { if (!s) return ''; return s.length > n ? s.slice(0, n) + '…' : s }
</script>

<template>
  <div class="gh">
    <!-- ═══ Top bar ═══ -->
    <div class="gh__bar" v-if="mode === 'list' || mode === 'detail'">
      <div class="gh__bar-left">
        <template v-if="mode === 'list'">
          <el-button text size="default" class="gh__back-btn" @click="emit('back-to-input')">← 返回编辑</el-button>
          <span class="gh__count" v-if="records.length">{{ records.length }} 条记录</span>
        </template>
        <template v-if="mode === 'detail'">
          <el-button text size="default" class="gh__back-btn" @click="emit('back-to-list')">← 历史记录</el-button>
          <el-button text size="default" class="gh__back-btn" @click="emit('back-to-input')">← 返回编辑</el-button>
        </template>
      </div>
      <div class="gh__bar-right">
        <el-button
          v-if="mode === 'detail' && detail"
          size="small"
          type="primary"
          plain
          :icon="Download"
          :loading="exportingDetail"
          @click="handleExportDetail"
        >
          导出 Word
        </el-button>
      </div>
    </div>

    <!-- ═══ List ═══ -->
    <template v-if="mode === 'list'">
      <el-skeleton v-if="listLoading" animated :rows="4" />
      <el-empty v-else-if="!records.length" description="暂无生成记录" />
      <div v-else class="gh__cards">
        <div v-for="r in records" :key="r.id" class="gh__card">
          <!-- 内容区 -->
          <div class="gh__card-body">
            <div class="gh__card-head">
              <span class="gh__card-src">{{ r.source_title || '手动输入' }}</span>
              <el-tag :type="riskTag(r.risk_level)" size="small" effect="light">{{ riskText(r.risk_level) }}</el-tag>
            </div>
            <p class="gh__card-sum" v-if="r.summary_short">{{ fmt(r.summary_short, 120) }}</p>
            <div class="gh__card-titles" v-if="(r.candidate_titles || []).length">
              <span v-for="(t, i) in r.candidate_titles!.slice(0, 2)" :key="i" class="gh__card-title">{{ t }}</span>
            </div>
            <span class="gh__card-time">{{ r.created_at }}</span>
          </div>

          <!-- 操作按钮 — 右侧纵向排列，全部带框 -->
          <div class="gh__card-acts">
            <el-button
              size="small"
              type="primary"
              plain
              @click="emit('view-detail', r.id)"
            >查看</el-button>
            <el-button
              size="small"
              plain
              @click="handleReuse(r)"
            >复用</el-button>
            <el-button
              size="small"
              plain
              :icon="Download"
              :loading="exportingId === r.id"
              @click="handleExport(r)"
            >下载</el-button>
            <el-button
              size="small"
              type="danger"
              plain
              @click="handleDelete(r)"
            >删除</el-button>
          </div>
        </div>
      </div>
    </template>

    <!-- ═══ Detail ═══ -->
    <template v-if="mode === 'detail'">
      <el-skeleton v-if="detailLoading" animated :rows="8" />
      <el-alert v-else-if="detailError" :title="detailError" type="error" show-icon />
      <template v-else-if="detail">
        <div class="gh__detail">
          <!-- input -->
          <section class="gh__sec">
            <h3 class="gh__sec-title">输入原文</h3>
            <p class="gh__text">{{ detail.input_text }}</p>
          </section>
          <!-- params -->
          <section class="gh__sec">
            <h3 class="gh__sec-title">生成参数</h3>
            <div class="gh__tags">
              <span class="gh__tag">标题 {{ detail.params.title_count }} 个</span>
              <span class="gh__tag">{{ detail.params.summary_type === 'extract' ? '抽取式' : '生成式' }}</span>
              <span class="gh__tag">{{ detail.params.title_style }}</span>
              <span class="gh__tag">{{ detail.params.summary_style }}</span>
              <span class="gh__tag">{{ detail.params.summary_length === 'short' ? '短' : detail.params.summary_length === 'long' ? '长' : '短+长' }}</span>
            </div>
          </section>
          <!-- titles -->
          <section class="gh__sec" v-if="(detail.result?.candidate_titles || []).length">
            <h3 class="gh__sec-title">候选标题</h3>
            <div class="gh__titles">
              <p v-for="(t, i) in detail.result!.candidate_titles" :key="i" class="gh__title-item">{{ i + 1 }}. {{ t }}</p>
            </div>
          </section>
          <!-- summary short -->
          <section class="gh__sec" v-if="detail.result?.summary_short">
            <h3 class="gh__sec-title">短摘要</h3>
            <p class="gh__text">{{ detail.result.summary_short }}</p>
          </section>
          <!-- summary long -->
          <section class="gh__sec" v-if="detail.result?.summary_long">
            <h3 class="gh__sec-title">长摘要</h3>
            <p class="gh__text">{{ detail.result.summary_long }}</p>
          </section>
          <!-- keywords -->
          <section class="gh__sec" v-if="(detail.result?.keywords || []).length">
            <h3 class="gh__sec-title">关键词</h3>
            <div class="gh__tags">
              <el-tag v-for="(k, i) in detail.result!.keywords" :key="i" size="small" :type="i === 0 ? '' : 'info'">
                {{ typeof k === 'string' ? k : ((k as any).word || k) }}
              </el-tag>
            </div>
          </section>
          <!-- elements 5W1H -->
          <section class="gh__sec" v-if="detail.result?.elements && detail.result.elements.what">
            <h3 class="gh__sec-title">六要素</h3>
            <div class="gh__elements">
              <div class="gh__el" v-if="detail.result.elements.who"><span class="gh__el-k">何人</span><span>{{ detail.result.elements.who }}</span></div>
              <div class="gh__el" v-if="detail.result.elements.what"><span class="gh__el-k">何事</span><span>{{ detail.result.elements.what }}</span></div>
              <div class="gh__el" v-if="detail.result.elements.when"><span class="gh__el-k">何时</span><span>{{ detail.result.elements.when }}</span></div>
              <div class="gh__el" v-if="detail.result.elements.where"><span class="gh__el-k">何地</span><span>{{ detail.result.elements.where }}</span></div>
              <div class="gh__el" v-if="detail.result.elements.why"><span class="gh__el-k">为何</span><span>{{ detail.result.elements.why }}</span></div>
              <div class="gh__el" v-if="detail.result.elements.how"><span class="gh__el-k">如何</span><span>{{ detail.result.elements.how }}</span></div>
            </div>
          </section>
          <!-- consistency（完整审计面板） -->
          <section class="gh__sec" v-if="detail.result?.consistency">
            <h3 class="gh__sec-title">一致性检查</h3>
            <Step7AuditPanel :consistency-data="detail.result.consistency" />
          </section>
        </div>
      </template>
    </template>
  </div>
</template>

<style scoped>
.gh { max-width: 100%; }

/* bar */
.gh__bar { display: flex; align-items: center; gap: 8px; margin-bottom: 14px; flex-wrap: wrap; justify-content: space-between; }
.gh__bar-left { display: flex; align-items: center; gap: 8px; }
.gh__bar-right { display: flex; align-items: center; gap: 8px; flex-shrink: 0; }
.gh__back-btn { font-size: 15px; font-weight: 500; }
.gh__count { font-size: 14px; color: var(--color-text-secondary); }

/* cards */
.gh__cards { display: flex; flex-direction: column; gap: 10px; }
.gh__card {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: 10px;
  padding: 16px 18px;
  display: flex;
  flex-direction: row;
  align-items: stretch;
  gap: 16px;
  transition: box-shadow .15s;
}
.gh__card:hover { box-shadow: 0 1px 6px rgba(0,0,0,.05); }
.gh__card-body { flex: 1; min-width: 0; }
.gh__card-head { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.gh__card-src {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.gh__card-sum { margin: 0 0 6px; font-size: 14px; color: var(--color-text-secondary); line-height: 1.6; }
.gh__card-titles { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 6px; }
.gh__card-title { padding: 2px 10px; background: #f3f4f6; border-radius: 4px; font-size: 13px; color: var(--color-text-secondary); }
.gh__card-time { font-size: 12px; color: var(--color-text-muted); }

/* ── 操作按钮 — 右侧纵向排列 ── */
.gh__card-acts {
  display: flex;
  flex-direction: column;
  gap: 8px;
  flex-shrink: 0;
  width: 80px;
}
.gh__card-acts .el-button {
  width: 100%;
  margin-left: 0;
}

/* detail */
.gh__detail { display: flex; flex-direction: column; gap: 14px; }
.gh__sec { background: var(--color-bg-card); border: 1px solid var(--color-border); border-radius: 10px; padding: 16px 20px; }
.gh__sec-title { margin: 0 0 8px; font-size: 15px; font-weight: 600; color: var(--color-text-primary); }
.gh__text { margin: 0; font-size: 14px; line-height: 1.75; color: var(--color-text-secondary); white-space: pre-line; }
.gh__tags { display: flex; flex-wrap: wrap; gap: 6px; }
.gh__tag { padding: 3px 10px; background: #f3f4f6; border-radius: 6px; font-size: 13px; color: var(--color-text-secondary); }
.gh__titles { display: flex; flex-direction: column; gap: 4px; }
.gh__title-item { margin: 0; padding: 6px 10px; background: var(--color-bg-hover); border-radius: 6px; font-size: 14px; color: var(--color-text-primary); }
.gh__elements { display: grid; grid-template-columns: 1fr 1fr; gap: 6px; }
.gh__el { font-size: 14px; color: var(--color-text-secondary); display: flex; gap: 6px; }
.gh__el-k { font-weight: 600; color: var(--color-text-primary); flex-shrink: 0; min-width: 32px; }
</style>
