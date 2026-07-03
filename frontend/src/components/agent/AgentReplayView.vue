<script setup lang="ts">
/** AgentReplayView — 步骤回放播放器（Phase 4）。
 *
 * 支持 ▶ Play | ⏸ Pause | ⏹ Stop | Step-by-step 控制，
 * 按实际延迟时间（可加速）逐步回放 8 个步骤。
 */

import { ref, watch, onUnmounted, computed } from 'vue'
import { getTaskReplay, type ReplayStep } from '@/api/agentAnalysis'

const props = defineProps<{ taskId: number }>()

const steps = ref<ReplayStep[]>([])
const currentIndex = ref(-1)
const isPlaying = ref(false)
const speed = ref(1)   // 1x / 2x / 5x / 10x
const loading = ref(false)
const error = ref('')
const currentStep = computed(() => steps.value[currentIndex.value] ?? null)

let timer: ReturnType<typeof setTimeout> | null = null

async function loadReplay() {
  loading.value = true
  error.value = ''
  try {
    const data = await getTaskReplay(props.taskId)
    steps.value = data.steps
    currentIndex.value = -1
  } catch (e) {
    error.value = e instanceof Error ? e.message : '加载回放数据失败'
  } finally {
    loading.value = false
  }
}

function play() {
  if (steps.value.length === 0) return
  if (currentIndex.value >= steps.value.length - 1) {
    currentIndex.value = -1  // 重头开始
  }
  isPlaying.value = true
  advanceStep()
}

function pause() {
  isPlaying.value = false
  if (timer) { clearTimeout(timer); timer = null }
}

function stop() {
  pause()
  currentIndex.value = -1
}

function stepForward() {
  pause()
  if (currentIndex.value < steps.value.length - 1) {
    currentIndex.value++
  }
}

function stepBackward() {
  pause()
  if (currentIndex.value > -1) {
    currentIndex.value--
  }
}

function advanceStep() {
  if (!isPlaying.value) return
  currentIndex.value++
  if (currentIndex.value >= steps.value.length - 1) {
    isPlaying.value = false
    return
  }
  // 按实际延迟 + speed 倍速计算下一帧时间
  const delay = Math.max(100, (steps.value[currentIndex.value]?.latency_ms ?? 500) / speed.value)
  timer = setTimeout(advanceStep, delay)
}

// 切换 task 时重新加载
watch(() => props.taskId, () => { if (props.taskId) loadReplay() }, { immediate: true })

onUnmounted(() => { if (timer) clearTimeout(timer) })

// ── 格式化 ──
function formatMs(ms: number): string {
  return ms >= 1000 ? (ms / 1000).toFixed(1) + 's' : ms + 'ms'
}
function statusIcon(s: string): string {
  switch (s) { case 'completed': return '✔'; case 'failed': return '✖'; default: return '○' }
}
</script>

<template>
  <div class="replay-view">
    <!-- 加载状态 -->
    <el-skeleton v-if="loading" animated :rows="4" />

    <!-- 错误 -->
    <el-alert v-else-if="error" :title="error" type="error" show-icon :closable="false" />

    <template v-else>
      <!-- 控制栏 -->
      <div class="replay-controls">
        <div class="replay-transport">
          <el-button-group>
            <el-button size="small" @click="stop" :disabled="currentIndex === -1">⏹</el-button>
            <el-button size="small" @click="stepBackward" :disabled="currentIndex <= -1">⏮</el-button>
            <el-button size="small" :type="isPlaying ? 'warning' : 'primary'" @click="isPlaying ? pause() : play()">
              {{ isPlaying ? '⏸ 暂停' : '▶ 播放' }}
            </el-button>
            <el-button size="small" @click="stepForward" :disabled="currentIndex >= steps.length - 1">⏭</el-button>
          </el-button-group>
        </div>

        <div class="replay-speed">
          <span class="speed-label">速度:</span>
          <el-radio-group v-model="speed" size="small" :disabled="isPlaying">
            <el-radio-button :value="1">1×</el-radio-button>
            <el-radio-button :value="2">2×</el-radio-button>
            <el-radio-button :value="5">5×</el-radio-button>
            <el-radio-button :value="10">10×</el-radio-button>
          </el-radio-group>
        </div>

        <span class="replay-progress">
          {{ Math.max(0, currentIndex + 1) }} / {{ steps.length }}
        </span>
      </div>

      <!-- 进度条 -->
      <el-progress
        :percentage="steps.length ? Math.round((currentIndex + 1) / steps.length * 100) : 0"
        :stroke-width="6"
        :show-text="false"
        class="replay-bar"
      />

      <!-- 步骤列表 -->
      <div class="replay-steps">
        <div
          v-for="(step, i) in steps"
          :key="step.step"
          class="replay-step"
          :class="{
            'is-active': i === currentIndex,
            'is-past': i < currentIndex,
          }"
        >
          <div class="replay-step__icon">{{ statusIcon(step.status) }}</div>
          <div class="replay-step__info">
            <div class="replay-step__header">
              <span class="replay-step__order">Step {{ step.order }}</span>
              <span class="replay-step__label">{{ step.label }}</span>
              <span class="replay-step__latency">{{ formatMs(step.latency_ms) }}</span>
            </div>

            <!-- 当前步骤展示输入/输出 -->
            <div v-if="i === currentIndex && step.input_data" class="replay-step__detail">
              <div class="detail-block">
                <strong>输入:</strong>
                <pre>{{ JSON.stringify(step.input_data, null, 2).slice(0, 300) }}</pre>
              </div>
              <div class="detail-block">
                <strong>输出:</strong>
                <pre>{{ JSON.stringify(step.output_data, null, 2).slice(0, 300) }}</pre>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.replay-view { padding: 4px 0; }

/* 控制栏 */
.replay-controls {
  display: flex;
  align-items: center;
  gap: 18px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}
.replay-speed { display: flex; align-items: center; gap: 6px; }
.speed-label { font-size: 12px; color: var(--color-text-secondary); }
.replay-progress {
  margin-left: auto;
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-secondary);
  font-variant-numeric: tabular-nums;
}
.replay-bar { margin-bottom: 16px; }

/* 步骤列表 */
.replay-steps {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.replay-step {
  display: flex;
  gap: 12px;
  padding: 8px 12px;
  border-radius: 10px;
  border: 1px solid transparent;
  transition: all 0.25s ease;
}

.replay-step.is-active {
  background: color-mix(in srgb, var(--color-primary) 6%, var(--color-bg-card));
  border-color: color-mix(in srgb, var(--color-primary) 25%, var(--color-border));
}

.replay-step.is-past {
  opacity: 0.5;
}

.replay-step__icon {
  flex: 0 0 28px;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  font-size: 12px;
  font-weight: 700;
  background: #f3f4f6;
  color: var(--color-text-muted);
}
.replay-step.is-active .replay-step__icon {
  background: color-mix(in srgb, var(--color-primary) 15%, transparent);
  color: var(--color-primary);
}

.replay-step__info { flex: 1; min-width: 0; }
.replay-step__header {
  display: flex;
  align-items: center;
  gap: 8px;
}
.replay-step__order { font-size: 11px; font-weight: 600; color: var(--color-text-secondary); text-transform: uppercase; }
.replay-step__label { font-size: 13px; font-weight: 600; color: var(--color-text-primary); }
.replay-step__latency { margin-left: auto; font-size: 11px; color: var(--color-text-secondary); font-variant-numeric: tabular-nums; }

/* 详情 */
.replay-step__detail {
  margin-top: 8px;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}
.detail-block { font-size: 12px; }
.detail-block strong { color: var(--color-text-secondary); display: block; margin-bottom: 2px; }
.detail-block pre {
  margin: 0;
  padding: 6px 8px;
  background: var(--color-bg-hover);
  border-radius: 6px;
  font-size: 11px;
  line-height: 1.5;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: pre-wrap;
  word-break: break-all;
  color: var(--color-text-primary);
}

@media (max-width: 600px) {
  .replay-step__detail { grid-template-columns: 1fr; }
}
</style>
