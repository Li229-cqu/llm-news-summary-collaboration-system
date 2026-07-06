import { ref, onUnmounted } from 'vue'

export type SpeechStatus = 'idle' | 'playing' | 'paused' | 'finished'

export interface SpeechSegment {
  id: number
  text: string
  type: 'title' | 'summary' | 'paragraph'
}

export interface UseSpeechReturn {
  status: () => SpeechStatus
  currentSegmentIndex: () => number
  progress: () => number
  rate: () => number
  pitch: () => number
  voices: () => SpeechSynthesisVoice[]
  selectedVoice: () => SpeechSynthesisVoice | null
  canSpeak: () => boolean
  error: () => string | null
  play: () => void
  pause: () => void
  stop: () => void
  setRate: (rate: number) => void
  setPitch: (pitch: number) => void
  setVoice: (voice: SpeechSynthesisVoice | null) => void
  goToSegment: (index: number) => void
}

export function useSpeech(segments: () => SpeechSegment[]) {
  const status = ref<SpeechStatus>('idle')
  const currentSegmentIndex = ref(0)
  const progress = ref(0)
  const rate = ref(1)
  const pitch = ref(1)
  const canSpeak = ref(false)
  const error = ref<string | null>(null)
  const voices = ref<SpeechSynthesisVoice[]>([])
  const selectedVoice = ref<SpeechSynthesisVoice | null>(null)

  let utterance: SpeechSynthesisUtterance | null = null
  let currentUtteranceIndex = 0
  let isPaused = false

  function loadVoices() {
    voices.value = window.speechSynthesis.getVoices()
    canSpeak.value = voices.value.length > 0

    if (!selectedVoice.value && voices.value.length > 0) {
      selectedVoice.value = findDefaultChineseVoice()
    }
  }

  function findDefaultChineseVoice(): SpeechSynthesisVoice | null {
    if (voices.value.length === 0) return null

    const zhVoices = voices.value.filter(v =>
      v.lang.startsWith('zh') || v.lang.startsWith('zh-CN')
    )

    if (zhVoices.length > 0) {
      // 优先使用 Microsoft 晓晓 Online (Natural) 作为默认音色
      const xiaoxiao = zhVoices.find(v => {
        const name = v.name.toLowerCase()
        return name.includes('xiaoxiao') || v.name.includes('晓晓')
      })
      if (xiaoxiao) return xiaoxiao

      return zhVoices.find(v => v.default) || zhVoices[0]
    }

    return voices.value.find(v => v.default) || voices.value[0]
  }

  function getCurrentVoice(): SpeechSynthesisVoice | null {
    return selectedVoice.value || findDefaultChineseVoice()
  }

  function speakNextSegment() {
    if (isPaused) return

    const allSegments = segments()
    if (currentUtteranceIndex >= allSegments.length) {
      status.value = 'finished'
      currentSegmentIndex.value = -1
      progress.value = 100
      return
    }

    const segment = allSegments[currentUtteranceIndex]

    utterance = new SpeechSynthesisUtterance(segment.text)
    utterance.rate = rate.value
    utterance.pitch = pitch.value

    const voice = getCurrentVoice()
    if (voice) {
      utterance.voice = voice
    }

    utterance.onstart = () => {
      status.value = 'playing'
      currentSegmentIndex.value = currentUtteranceIndex
    }

    utterance.onend = () => {
      if (!isPaused) {
        currentUtteranceIndex++
        const total = allSegments.length
        progress.value = Math.round((currentUtteranceIndex / total) * 100)
        speakNextSegment()
      }
    }

    utterance.onerror = (e) => {
      error.value = '语音播放失败：' + e.error
      status.value = 'idle'
    }

    utterance.onpause = () => {
      status.value = 'paused'
    }

    utterance.onresume = () => {
      status.value = 'playing'
    }

    window.speechSynthesis.speak(utterance)
  }

  function play() {
    if (!canSpeak.value) {
      error.value = '当前浏览器不支持语音合成'
      return
    }

    const allSegments = segments()
    if (!allSegments.length) {
      error.value = '没有可朗读的内容'
      return
    }

    if (status.value === 'paused') {
      isPaused = false
      window.speechSynthesis.resume()
      return
    }

    if (status.value === 'finished') {
      currentUtteranceIndex = 0
      progress.value = 0
    }

    isPaused = false
    speakNextSegment()
  }

  function pause() {
    isPaused = true
    window.speechSynthesis.pause()
    status.value = 'paused'
  }

  function stop() {
    isPaused = false
    window.speechSynthesis.cancel()
    status.value = 'idle'
    currentSegmentIndex.value = -1
    currentUtteranceIndex = 0
    progress.value = 0
    error.value = null
  }

  function setRate(newRate: number) {
    rate.value = Math.max(0.5, Math.min(2, newRate))
    if (status.value === 'playing') {
      window.speechSynthesis.cancel()
      speakNextSegment()
    }
  }

  function setPitch(newPitch: number) {
    pitch.value = Math.max(0, Math.min(2, newPitch))
    if (status.value === 'playing') {
      window.speechSynthesis.cancel()
      speakNextSegment()
    }
  }

  function setVoice(voice: SpeechSynthesisVoice | null) {
    selectedVoice.value = voice
    if (status.value === 'playing') {
      window.speechSynthesis.cancel()
      speakNextSegment()
    }
  }

  function goToSegment(index: number) {
    const allSegments = segments()
    if (index < 0 || index >= allSegments.length) return

    currentUtteranceIndex = index
    progress.value = Math.round((index / allSegments.length) * 100)

    if (status.value === 'playing') {
      window.speechSynthesis.cancel()
      speakNextSegment()
    }
  }

  loadVoices()

  window.speechSynthesis.onvoiceschanged = loadVoices

  onUnmounted(() => {
    window.speechSynthesis.cancel()
  })

  return {
    status: () => status.value,
    currentSegmentIndex: () => currentSegmentIndex.value,
    progress: () => progress.value,
    rate: () => rate.value,
    pitch: () => pitch.value,
    voices: () => voices.value,
    selectedVoice: () => selectedVoice.value,
    canSpeak: () => canSpeak.value,
    error: () => error.value,
    play,
    pause,
    stop,
    setRate,
    setPitch,
    setVoice,
    goToSegment,
  }
}