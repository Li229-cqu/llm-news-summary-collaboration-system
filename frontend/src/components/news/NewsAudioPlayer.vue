<template>
  <div class="news-audio-player">
    <div class="news-audio-player__main">
      <button
        class="news-audio-player__play-btn"
        :class="{ 'is-playing': currentStatus === 'playing' }"
        :disabled="!currentCanSpeak || currentStatus === 'finished'"
        @click="handlePlayPause"
      >
        <span class="news-audio-player__play-icon">
          {{ currentStatus === 'playing' ? '⏸' : '▶' }}
        </span>
      </button>

      <div class="news-audio-player__info">
        <div class="news-audio-player__status-text">
          <span v-if="currentStatus === 'idle'">点击播放</span>
          <span v-else-if="currentStatus === 'playing'">正在朗读</span>
          <span v-else-if="currentStatus === 'paused'">已暂停</span>
          <span v-else-if="currentStatus === 'finished'">朗读完成</span>
        </div>
        <div class="news-audio-player__progress-bar">
          <div
            class="news-audio-player__progress-fill"
            :style="{ width: `${currentProgress}%` }"
          ></div>
        </div>
      </div>

      <div class="news-audio-player__controls">
        <button class="news-audio-player__control-btn" @click="handleStop">
          <span>■</span>
        </button>

        <div class="news-audio-player__rate-control">
          <button
            class="news-audio-player__rate-btn"
            @click="adjustRate(-0.25)"
            :disabled="currentRate <= 0.5"
          >
            −
          </button>
          <span class="news-audio-player__rate-display">{{ currentRate.toFixed(1) }}x</span>
          <button
            class="news-audio-player__rate-btn"
            @click="adjustRate(0.25)"
            :disabled="currentRate >= 2"
          >
            +
          </button>
        </div>
      </div>
    </div>

    <div class="news-audio-player__settings">
      <div class="news-audio-player__voice-select">
        <el-select
          v-model="selectedVoiceName"
          placeholder="选择音色"
          class="news-audio-player__voice-select-input"
          size="small"
          @change="handleVoiceChange"
        >
          <el-option
            v-for="voice in filteredVoices"
            :key="voice.name"
            :label="getVoiceLabel(voice)"
            :value="voice.name"
          />
        </el-select>
      </div>

      <div class="news-audio-player__pitch-control">
        <span class="news-audio-player__pitch-label">音调</span>
        <el-slider
          v-model="currentPitch"
          :min="0"
          :max="2"
          :step="0.1"
          class="news-audio-player__pitch-slider"
          @change="handlePitchChange"
        />
        <span class="news-audio-player__pitch-value">{{ currentPitch.toFixed(1) }}</span>
      </div>
    </div>

    <el-tooltip
      v-if="currentError"
      class="news-audio-player__error-tooltip"
      :content="currentError"
      placement="bottom"
    >
      <span class="news-audio-player__error-indicator">!</span>
    </el-tooltip>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useSpeech, type SpeechSegment } from '@/composables/useSpeech'

interface NewsAudioPlayerProps {
  segments: SpeechSegment[]
}

const props = defineProps<NewsAudioPlayerProps>()

const getSegments = () => props.segments

const {
  status: getStatus,
  progress: getProgress,
  rate: getRate,
  pitch: getPitch,
  voices: getVoices,
  selectedVoice: getSelectedVoice,
  canSpeak: getCanSpeak,
  error: getError,
  play,
  pause,
  stop,
  setRate,
  setPitch,
  setVoice,
} = useSpeech(getSegments)

const currentStatus = computed(() => getStatus())
const currentProgress = computed(() => getProgress())
const currentRate = computed(() => getRate())
const currentPitch = ref(getPitch())
const currentVoices = computed(() => getVoices())
const currentSelectedVoice = computed(() => getSelectedVoice())
const currentCanSpeak = computed(() => getCanSpeak())
const currentError = computed(() => getError())

const selectedVoiceName = ref(currentSelectedVoice.value?.name || '')

const filteredVoices = computed(() => {
  return currentVoices.value.filter(v => 
    v.lang.startsWith('zh') || v.lang.startsWith('zh-CN') || v.lang.startsWith('en')
  )
})

function getVoiceLabel(voice: SpeechSynthesisVoice): string {
  const langMap: Record<string, string> = {
    'zh': '中文',
    'zh-CN': '中文',
    'zh-TW': '中文(台)',
    'zh-HK': '中文(港)',
    'en': '英文',
    'en-US': '英文(美)',
    'en-GB': '英文(英)',
  }
  const langLabel = langMap[voice.lang] || voice.lang
  const defaultLabel = voice.default ? '(默认)' : ''
  return `${voice.name} ${langLabel} ${defaultLabel}`.trim()
}

function handleVoiceChange(name: string) {
  const voice = currentVoices.value.find(v => v.name === name)
  if (voice) {
    setVoice(voice)
  }
}

function handlePitchChange(value: number) {
  setPitch(value)
}

watch(
  () => props.segments,
  () => {
    if (currentStatus.value === 'playing') {
      stop()
    }
  },
)

watch(
  () => getSelectedVoice(),
  (voice) => {
    selectedVoiceName.value = voice?.name || ''
  },
)

watch(
  () => getPitch(),
  (pitch) => {
    currentPitch.value = pitch
  },
)

function handlePlayPause() {
  if (currentStatus.value === 'playing') {
    pause()
  } else {
    play()
  }
}

function handleStop() {
  stop()
}

function adjustRate(delta: number) {
  setRate(currentRate.value + delta)
}
</script>

<style scoped>
.news-audio-player {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-card);
  background: var(--color-bg-card);
  flex-wrap: wrap;
}

.news-audio-player__main {
  display: flex;
  align-items: center;
  gap: 16px;
  flex: 1;
  min-width: 0;
}

.news-audio-player__play-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border: 2px solid var(--color-primary);
  border-radius: 50%;
  background: var(--color-bg-card);
  color: var(--color-primary);
  font-size: 16px;
  cursor: pointer;
  transition:
    background .2s ease,
    color .2s ease,
    border-color .2s ease;
  flex-shrink: 0;
}

.news-audio-player__play-btn:hover:not(:disabled) {
  background: var(--color-primary);
  color: #fff;
}

.news-audio-player__play-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.news-audio-player__play-btn.is-playing {
  background: var(--color-primary);
  color: #fff;
}

.news-audio-player__play-icon {
  margin-left: 2px;
}

.news-audio-player__info {
  display: flex;
  flex-direction: column;
  gap: 6px;
  flex: 1;
  min-width: 0;
}

.news-audio-player__status-text {
  color: var(--color-text-primary);
  font-size: 13px;
  font-weight: 500;
}

.news-audio-player__progress-bar {
  height: 4px;
  border-radius: 2px;
  background: var(--color-border);
  overflow: hidden;
}

.news-audio-player__progress-fill {
  height: 100%;
  border-radius: 2px;
  background: var(--color-primary);
  transition: width .3s ease;
}

.news-audio-player__controls {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}

.news-audio-player__control-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: 1px solid var(--color-border);
  border-radius: 6px;
  background: var(--color-bg-card);
  color: var(--color-text-secondary);
  font-size: 10px;
  cursor: pointer;
  transition:
    background .2s ease,
    color .2s ease,
    border-color .2s ease;
}

.news-audio-player__control-btn:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
}

.news-audio-player__rate-control {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 8px;
  border: 1px solid var(--color-border);
  border-radius: 6px;
  background: var(--color-bg);
}

.news-audio-player__rate-btn {
  width: 24px;
  height: 24px;
  border: none;
  border-radius: 4px;
  background: var(--color-bg-card);
  color: var(--color-text-secondary);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition:
    background .2s ease,
    color .2s ease;
}

.news-audio-player__rate-btn:hover:not(:disabled) {
  background: var(--color-primary);
  color: #fff;
}

.news-audio-player__rate-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.news-audio-player__rate-display {
  color: var(--color-text-primary);
  font-size: 13px;
  font-weight: 500;
  min-width: 40px;
  text-align: center;
}

.news-audio-player__settings {
  display: flex;
  align-items: center;
  gap: 16px;
  padding-left: 12px;
  border-left: 1px solid var(--color-border);
  flex-shrink: 0;
}

.news-audio-player__voice-select {
  min-width: 140px;
}

.news-audio-player__voice-select-input {
  width: 100%;
}

.news-audio-player__pitch-control {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 160px;
}

.news-audio-player__pitch-label {
  color: var(--color-text-secondary);
  font-size: 12px;
  font-weight: 500;
  white-space: nowrap;
}

.news-audio-player__pitch-slider {
  flex: 1;
  width: 100px;
}

.news-audio-player__pitch-value {
  color: var(--color-text-primary);
  font-size: 12px;
  font-weight: 500;
  min-width: 36px;
  text-align: right;
}

.news-audio-player__error-indicator {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #ef4444;
  color: #fff;
  font-size: 12px;
  font-weight: 700;
}

:root.dark .news-audio-player__control-btn {
  border-color: rgba(255,255,255,.1);
}

:root.dark .news-audio-player__rate-control {
  border-color: rgba(255,255,255,.1);
  background: rgba(255,255,255,.05);
}

:root.dark .news-audio-player__rate-btn {
  background: rgba(255,255,255,.08);
}

:root.dark .news-audio-player__settings {
  border-color: rgba(255,255,255,.1);
}

@media (max-width: 960px) {
  .news-audio-player__settings {
    width: 100%;
    justify-content: center;
    padding-left: 0;
    border-left: none;
    border-top: 1px solid var(--color-border);
    padding-top: 12px;
    margin-top: 8px;
  }
}
</style>