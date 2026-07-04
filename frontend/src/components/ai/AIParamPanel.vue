<script setup lang="ts">
import { ref } from 'vue'
import { ArrowDown, Clock } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useAIDraftStore } from '@/stores/aiDraft'

const emit = defineEmits<{ (e: 'navigate', target: 'history' | 'input'): void }>()
const aiDraft = useAIDraftStore()

const OPTS: Record<string, { label: string; value: any }[]> = {
  title_count: [{ label: '1 个', value: 1 }, { label: '3 个', value: 3 }, { label: '5 个', value: 5 }],
  summary_type: [{ label: '生成式', value: 'generate' }, { label: '抽取式', value: 'extract' }],
  title_style: [{ label: '客观新闻型', value: '客观新闻型' }, { label: '吸引点击型', value: '吸引点击型' }, { label: '简洁概括型', value: '简洁概括型' }],
  summary_style: [{ label: '简明扼要', value: '简明扼要' }, { label: '客观正式', value: '客观正式' }, { label: '通俗易懂', value: '通俗易懂' }],
  summary_length: [{ label: '短摘要', value: 'short' }, { label: '长摘要', value: 'long' }, { label: '两者', value: 'both' }],
}
const LABELS: Record<string, string> = {
  title_count: '标题数量', summary_type: '摘要类型', title_style: '标题风格',
  summary_style: '摘要风格', summary_length: '摘要长度',
}

const openKey = ref<string | null>(null)
function toggle(k: string) { openKey.value = openKey.value === k ? null : k }
function curLabel(k: string): string {
  const v = (aiDraft.params as any)[k]
  return (OPTS[k] || []).find(o => o.value === v)?.label || ''
}
function setParam(k: string, v: any) {
  aiDraft.setParams({ [k]: k === 'title_count' ? Number(v) : v })
}
function resetAll() { aiDraft.resetParams(); ElMessage.success('已恢复默认参数') }
</script>

<template>
  <div class="ps">
    <div class="ps__title">参数选择</div>

    <div v-for="(opts, key) in OPTS" :key="key" class="ps__section" :class="{ 'is-open': openKey === key }">
      <button class="ps__trigger" @click="toggle(key)">
        <span class="ps__trigger-label">{{ LABELS[key] || key }}</span>
        <span class="ps__trigger-val">{{ curLabel(key) }}</span>
        <el-icon :size="12" class="ps__trigger-arrow"><ArrowDown /></el-icon>
      </button>
      <div class="ps__options" v-show="openKey === key">
        <button
          v-for="o in opts" :key="o.value"
          :class="{ active: (aiDraft.params as any)[key] === o.value }"
          class="ps__opt"
          @click="setParam(key, o.value)"
        >{{ o.label }}</button>
      </div>
    </div>

    <div class="ps__footer">
      <button class="ps__reset" @click="resetAll">恢复默认</button>
    </div>
    <div class="ps__history">
      <button class="ps__history-btn" @click="emit('navigate', 'history')">
        <el-icon :size="14"><Clock /></el-icon>
        <span>生成历史</span>
      </button>
    </div>
  </div>
</template>

<style scoped>
.ps { display: flex; flex-direction: column; padding-bottom: 16px; }
.ps__title {
  padding: 18px 20px 14px; font-size: 17px; font-weight: 700; color: var(--color-text-primary);
  border-bottom: 1px solid var(--color-border);
}

.ps__section { border-bottom: 1px solid #f3f4f6; }
.ps__trigger {
  width: 100%; display: flex; align-items: center; gap: 6px;
  padding: 13px 20px; background: none; border: none; cursor: pointer;
  font-size: 14px; text-align: left; color: var(--color-text-secondary);
  transition: background .15s;
}
.ps__trigger:hover { background: var(--color-bg-hover); }
.ps__trigger-label { font-weight: 500; flex-shrink: 0; }
.ps__trigger-val { flex: 1; text-align: right; color: var(--color-primary); font-weight: 500; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.ps__trigger-arrow { color: var(--color-text-muted); transition: transform .2s; flex-shrink: 0; }
.ps__section.is-open .ps__trigger-arrow { transform: rotate(180deg); }

.ps__options { padding: 0 20px 10px; display: flex; flex-direction: column; gap: 1px; }
.ps__opt {
  width: 100%; padding: 8px 10px 8px 20px; text-align: left; font-size: 13px; color: var(--color-text-secondary);
  background: none; border: none; border-radius: 6px; cursor: pointer; transition: all .12s;
}
.ps__opt:hover { background: var(--color-primary-soft); color: var(--color-primary); }
.ps__opt.active { background: var(--color-primary-soft); color: var(--color-primary); font-weight: 600; }

.ps__footer { padding: 12px 20px; border-top: 1px solid var(--color-border); }
.ps__reset {
  width: 100%; padding: 8px; font-size: 13px; color: var(--color-text-muted); background: var(--color-bg-hover);
  border: 1px solid var(--color-border); border-radius: 6px; cursor: pointer; transition: all .15s;
}
.ps__reset:hover { background: var(--color-primary-soft); border-color: var(--color-primary-light); color: var(--color-primary); }

.ps__history { padding: 0 20px 16px; }
.ps__history-btn {
  width: 100%; display: flex; align-items: center; justify-content: center; gap: 6px;
  padding: 10px; background: var(--color-primary-soft); border: 1px solid var(--color-primary-light);
  border-radius: 8px; font-size: 14px; font-weight: 600; color: var(--color-primary);
  cursor: pointer; transition: all .15s;
}
.ps__history-btn:hover { background: var(--color-primary-light); }
</style>
