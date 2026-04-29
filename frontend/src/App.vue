<script setup>
import { computed, onMounted, ref } from 'vue'
import {
  changePassword,
  fetchMe,
  getAccessToken,
  loginUser,
  registerUser,
  setAccessToken,
  updateProfile,
} from './api/auth'
import { askAssistant } from './api/chat'
import { fetchHealth } from './api/health'
import { deleteHistoryRecord, fetchHistory, fetchHistoryRecord } from './api/history'
import { predictImage } from './api/predict'
import { fetchEnabledProviders } from './api/providers'
import { fetchWeather } from './api/weather'

const health = ref(null)
const healthLoading = ref(false)
const healthError = ref('')

const currentUser = ref(null)
const authMode = ref('login')
const authUsername = ref('')
const authPassword = ref('')
const authLoading = ref(false)
const authError = ref('')
const authModalOpen = ref(false)
const profileModalOpen = ref(false)
const profileLoading = ref(false)
const profileError = ref('')
const profileSuccess = ref('')
const profileForm = ref({
  username: '',
  email: '',
  avatarUrl: '',
  currentPassword: '',
  password: '',
})

const historyLoading = ref(false)
const historyError = ref('')
const historyRecords = ref([])
const historyLimit = ref(14)
const historyOffset = ref(0)
const historyTotal = ref(0)
const selectedHistory = ref(null)
const historyDetailLoading = ref(false)
const historyDetailError = ref('')
const historyDeleteLoading = ref(false)
const searchOpen = ref(false)
const searchKeyword = ref('')

const messages = ref([])
const composerText = ref('')
const chatLoading = ref(false)
const chatError = ref('')
const predictLoading = ref(false)
const predictError = ref('')
const predictResult = ref(null)

const attachedFiles = ref([])
const selectedImagePreview = ref('')
const fileInputRef = ref(null)
const dragActive = ref(false)

const locationLoading = ref(false)
const locationError = ref('')
const weatherContext = ref(null)

const plusMenuOpen = ref(false)
const sidebarCollapsed = ref(false)

const providers = ref([])
const providerError = ref('')
const selectedVisionProviderId = ref('')
const selectedTextProviderId = ref('')

const historyPage = computed(() => Math.floor(historyOffset.value / historyLimit.value) + 1)
const historyPageCount = computed(() => Math.max(1, Math.ceil(historyTotal.value / historyLimit.value)))
const canPrevHistory = computed(() => historyOffset.value > 0)
const canNextHistory = computed(() => historyOffset.value + historyLimit.value < historyTotal.value)
const isBusy = computed(() => chatLoading.value || predictLoading.value)
const authTitle = computed(() => (authMode.value === 'login' ? '登录' : '注册'))
const environmentReady = computed(() => Boolean(weatherContext.value))

const visionProviders = computed(() => providers.value.filter((provider) => provider.provider_type === 'vision'))
const textProviders = computed(() => providers.value.filter((provider) => provider.provider_type === 'text'))
const activeVisionProvider = computed(() =>
  visionProviders.value.find((provider) => String(provider.id) === String(selectedVisionProviderId.value)),
)
const activeTextProvider = computed(() =>
  textProviders.value.find((provider) => String(provider.id) === String(selectedTextProviderId.value)),
)

const filteredHistoryRecords = computed(() => {
  const keyword = searchKeyword.value.trim().toLowerCase()
  if (!keyword) return historyRecords.value
  return historyRecords.value.filter((record) => {
    return [record.disease_name, record.risk_level, record.provider_name, record.model_name]
      .filter(Boolean)
      .some((value) => String(value).toLowerCase().includes(keyword))
  })
})

const serviceState = computed(() => {
  if (healthLoading.value) return '检测中'
  if (health.value?.ok) return '后端在线'
  if (healthError.value) return '后端离线'
  return '状态未知'
})

const composerPlaceholder = computed(() => {
  if (attachedFiles.value.length) return '输入问题，或直接发送图片进行识别'
  return '给马铃薯病害助手发送消息'
})

async function checkBackend() {
  healthLoading.value = true
  healthError.value = ''
  try {
    health.value = await fetchHealth()
  } catch (err) {
    health.value = null
    healthError.value = err instanceof Error ? err.message : '后端连接失败'
  } finally {
    healthLoading.value = false
  }
}

async function loadProviders() {
  providerError.value = ''
  try {
    providers.value = await fetchEnabledProviders()
    if (!selectedVisionProviderId.value && visionProviders.value[0]) {
      selectedVisionProviderId.value = String(visionProviders.value[0].id)
    }
    if (!selectedTextProviderId.value && textProviders.value[0]) {
      selectedTextProviderId.value = String(textProviders.value[0].id)
    }
  } catch (err) {
    providerError.value = err instanceof Error ? err.message : '模型列表获取失败'
  }
}

async function restoreSession() {
  if (!getAccessToken()) return
  authLoading.value = true
  authError.value = ''
  try {
    currentUser.value = await fetchMe()
    syncProfileForm()
  } catch (err) {
    setAccessToken('')
    currentUser.value = null
    authError.value = err instanceof Error ? err.message : '登录状态已失效'
  } finally {
    authLoading.value = false
  }
}

function syncProfileForm() {
  profileForm.value = {
    username: currentUser.value?.username || '',
    email: currentUser.value?.email || '',
    avatarUrl: currentUser.value?.avatar_url || '',
    currentPassword: '',
    password: '',
  }
}

function openAuthModal(mode = 'login') {
  authMode.value = mode
  authError.value = ''
  authModalOpen.value = true
}

function openProfileModal() {
  if (!currentUser.value) {
    openAuthModal('login')
    return
  }
  syncProfileForm()
  profileError.value = ''
  profileSuccess.value = ''
  profileModalOpen.value = true
}

function closeModals() {
  authModalOpen.value = false
  profileModalOpen.value = false
}

async function submitAuth() {
  authLoading.value = true
  authError.value = ''
  try {
    const payload = {
      username: authUsername.value.trim(),
      password: authPassword.value,
    }
    const result = authMode.value === 'login' ? await loginUser(payload) : await registerUser(payload)
    currentUser.value = result.user
    authPassword.value = ''
    authModalOpen.value = false
    syncProfileForm()
    historyOffset.value = 0
    selectedHistory.value = null
    await loadHistory()
  } catch (err) {
    authError.value = err instanceof Error ? err.message : '认证失败'
  } finally {
    authLoading.value = false
  }
}

async function logout() {
  setAccessToken('')
  currentUser.value = null
  selectedHistory.value = null
  profileModalOpen.value = false
  historyOffset.value = 0
  await loadHistory()
}

async function submitProfile() {
  if (!currentUser.value || profileLoading.value) return

  profileLoading.value = true
  profileError.value = ''
  profileSuccess.value = ''

  try {
    currentUser.value = await updateProfile({
      username: profileForm.value.username.trim(),
      email: profileForm.value.email.trim() || null,
      avatar_url: profileForm.value.avatarUrl.trim() || null,
    })

    if (profileForm.value.password) {
      if (!profileForm.value.currentPassword) {
        throw new Error('修改密码需要填写当前密码')
      }
      await changePassword({
        current_password: profileForm.value.currentPassword,
        new_password: profileForm.value.password,
      })
      profileForm.value.currentPassword = ''
      profileForm.value.password = ''
    }

    syncProfileForm()
    profileSuccess.value = '资料已保存'
  } catch (err) {
    profileError.value = err instanceof Error ? err.message : '资料保存失败'
  } finally {
    profileLoading.value = false
  }
}

function switchAuthMode(mode) {
  authMode.value = mode
  authError.value = ''
}

function newChat() {
  messages.value = []
  selectedHistory.value = null
  chatError.value = ''
  predictError.value = ''
  composerText.value = ''
}

async function loadHistory() {
  historyLoading.value = true
  historyError.value = ''

  try {
    const page = await fetchHistory(historyLimit.value, historyOffset.value)
    historyRecords.value = page.items || []
    historyTotal.value = page.total || 0
  } catch (err) {
    historyRecords.value = []
    historyError.value = err instanceof Error ? err.message : '历史记录获取失败'
  } finally {
    historyLoading.value = false
  }
}

async function goHistoryPage(direction) {
  const nextOffset = historyOffset.value + direction * historyLimit.value
  historyOffset.value = Math.max(0, nextOffset)
  await loadHistory()
}

async function selectHistory(record) {
  selectedHistory.value = record
  historyDetailLoading.value = true
  historyDetailError.value = ''

  try {
    selectedHistory.value = await fetchHistoryRecord(record.id)
  } catch (err) {
    historyDetailError.value = err instanceof Error ? err.message : '历史详情获取失败'
  } finally {
    historyDetailLoading.value = false
  }
}

async function removeSelectedHistory() {
  if (!selectedHistory.value || historyDeleteLoading.value) return

  historyDeleteLoading.value = true
  historyDetailError.value = ''

  try {
    await deleteHistoryRecord(selectedHistory.value.id)
    selectedHistory.value = null
    if (historyRecords.value.length === 1 && historyOffset.value > 0) {
      historyOffset.value = Math.max(0, historyOffset.value - historyLimit.value)
    }
    await loadHistory()
  } catch (err) {
    historyDetailError.value = err instanceof Error ? err.message : '历史记录删除失败'
  } finally {
    historyDeleteLoading.value = false
  }
}

function closeFloatingPanels() {
  plusMenuOpen.value = false
}

function triggerFileUpload() {
  fileInputRef.value?.click()
}

function appendFiles(files) {
  const nextFiles = Array.from(files || [])
  if (!nextFiles.length) return

  nextFiles.forEach((file) => {
    attachedFiles.value.push({
      file,
      name: file.name,
      size: file.size,
      type: file.type || inferFileType(file.name),
      previewUrl: file.type.startsWith('image/') ? URL.createObjectURL(file) : '',
    })
  })
  const firstImage = attachedFiles.value.find((item) => item.previewUrl)
  selectedImagePreview.value = firstImage?.previewUrl || ''
}

function onFileChange(event) {
  appendFiles(event.target.files)
  event.target.value = ''
  plusMenuOpen.value = false
}

function removeAttachment(index) {
  const [removed] = attachedFiles.value.splice(index, 1)
  if (removed?.previewUrl) URL.revokeObjectURL(removed.previewUrl)
  const firstImage = attachedFiles.value.find((item) => item.previewUrl)
  selectedImagePreview.value = firstImage?.previewUrl || ''
}

function clearAttachments() {
  attachedFiles.value.forEach((item) => {
    if (item.previewUrl) URL.revokeObjectURL(item.previewUrl)
  })
  attachedFiles.value = []
  selectedImagePreview.value = ''
}

function onDragOver(event) {
  event.preventDefault()
  dragActive.value = true
}

function onDragLeave(event) {
  if (!event.currentTarget.contains(event.relatedTarget)) {
    dragActive.value = false
  }
}

function onDrop(event) {
  event.preventDefault()
  dragActive.value = false
  appendFiles(event.dataTransfer.files)
}

async function loadWeatherFromBrowser() {
  plusMenuOpen.value = false
  if (!navigator.geolocation) {
    locationError.value = '当前浏览器不支持定位。'
    return
  }

  locationLoading.value = true
  locationError.value = ''

  try {
    const position = await new Promise((resolve, reject) => {
      navigator.geolocation.getCurrentPosition(resolve, reject, {
        enableHighAccuracy: false,
        timeout: 10000,
        maximumAge: 10 * 60 * 1000,
      })
    })
    const { latitude, longitude } = position.coords
    weatherContext.value = await fetchWeather(latitude, longitude, '浏览器定位')
  } catch (err) {
    locationError.value = err instanceof Error ? err.message : '定位或天气获取失败'
  } finally {
    locationLoading.value = false
  }
}

function buildChatContext(files = attachedFiles.value) {
  const context = []
  if (predictResult.value) {
    context.push(`最近识别病害：${predictResult.value.disease_name}`)
    context.push(`风险等级：${predictResult.value.risk_level}`)
    context.push(`摘要：${predictResult.value.summary}`)
    if (predictResult.value.suggestions?.length) {
      context.push(`建议：${predictResult.value.suggestions.join('；')}`)
    }
  }
  if (weatherContext.value) {
    context.push(
      `环境：${weatherContext.value.climate_zone}，${weatherContext.value.weather_text || '天气未知'}，气温 ${
        weatherContext.value.temperature_c ?? '未知'
      }°C，湿度 ${weatherContext.value.relative_humidity_percent ?? '未知'}%。`,
    )
  }
  if (files.length) {
    context.push(`用户已在前端选择文件：${files.map((item) => item.name).join('、')}。当前版本尚未读取文件正文。`)
  }
  return context.join('\n')
}

async function submitComposer() {
  const text = composerText.value.trim()
  if (isBusy.value) return
  if (!text && !attachedFiles.value.length) return

  chatError.value = ''
  predictError.value = ''
  selectedHistory.value = null

  const imageAttachment = attachedFiles.value.find((item) => item.file?.type?.startsWith('image/'))
  if (imageAttachment) {
    await submitImageMessage(text, imageAttachment)
    return
  }

  await submitTextMessage(text || '请根据我上传的文件给出农业病害相关建议。')
}

async function submitTextMessage(text) {
  const files = [...attachedFiles.value]
  const context = buildChatContext(files)
  messages.value.push({
    role: 'user',
    text,
    files,
  })
  composerText.value = ''
  clearAttachments()
  chatLoading.value = true

  try {
    const result = await askAssistant({
      question: text,
      context,
      provider_id: selectedTextProviderId.value ? Number(selectedTextProviderId.value) : null,
    })
    messages.value.push({
      role: 'assistant',
      text: result.answer,
      provider: `${result.provider_name} / ${result.model_name}`,
    })
  } catch (err) {
    chatError.value = err instanceof Error ? err.message : 'AI 助手调用失败'
  } finally {
    chatLoading.value = false
  }
}

async function submitImageMessage(text, imageAttachment) {
  const files = [...attachedFiles.value]
  const prompt = text || '请识别这张马铃薯叶片图片，并结合环境给出防治建议。'

  messages.value.push({
    role: 'user',
    text: prompt,
    imageUrl: imageAttachment.previewUrl,
    files,
  })
  composerText.value = ''
  attachedFiles.value = []
  selectedImagePreview.value = ''
  predictLoading.value = true

  try {
    const result = await predictImage(
      imageAttachment.file,
      weatherContext.value,
      selectedVisionProviderId.value ? Number(selectedVisionProviderId.value) : null,
    )
    predictResult.value = result
    if (result.weather) weatherContext.value = result.weather
    messages.value.push({
      role: 'assistant',
      type: 'prediction',
      result,
      provider: `${result.provider_name} / ${result.model_name}`,
    })
    await loadHistory()
  } catch (err) {
    predictError.value = err instanceof Error ? err.message : '图片识别失败'
  } finally {
    predictLoading.value = false
  }
}

function inferFileType(name) {
  const ext = name.split('.').pop()?.toLowerCase()
  if (!ext) return 'file'
  if (['png', 'jpg', 'jpeg', 'webp'].includes(ext)) return `image/${ext}`
  if (['doc', 'docx'].includes(ext)) return 'word'
  if (['txt', 'md'].includes(ext)) return 'text'
  if (['pdf'].includes(ext)) return 'pdf'
  return ext
}

function fileIcon(file) {
  const type = file.type || ''
  if (type.startsWith('image/')) return '图'
  if (type.includes('word')) return 'W'
  if (type.includes('pdf')) return 'P'
  if (type.includes('text')) return 'T'
  return '文'
}

function formatTime(value) {
  if (!value) return '未知时间'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return new Intl.DateTimeFormat('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date)
}

function formatCoordinate(value) {
  if (value === null || value === undefined) return '未知'
  return Number(value).toFixed(4)
}

function formatFileSize(size) {
  if (!size) return '0 KB'
  if (size < 1024 * 1024) return `${Math.ceil(size / 1024)} KB`
  return `${(size / 1024 / 1024).toFixed(1)} MB`
}

onMounted(async () => {
  checkBackend()
  await loadProviders()
  await restoreSession()
  await loadHistory()
})
</script>

<template>
  <main
    class="chat-shell"
    :class="{ 'sidebar-collapsed': sidebarCollapsed }"
    @click="closeFloatingPanels"
  >
    <aside class="sidebar" aria-label="历史对话侧边栏">
      <div class="sidebar-top">
        <button type="button" class="brand-button" title="薯安智检">
          <img src="/logo.png" alt="薯安智检" />
          <span>薯安智检</span>
        </button>
        <button
          type="button"
          class="collapse-button"
          title="收起侧边栏"
          @click.stop="sidebarCollapsed = !sidebarCollapsed"
        >
          <span></span>
        </button>
      </div>

      <nav class="sidebar-nav" aria-label="对话操作">
        <button type="button" @click="newChat">
          <span class="nav-icon">＋</span>
          <span class="nav-text">新聊天</span>
        </button>
        <button type="button" @click="searchOpen = !searchOpen">
          <span class="nav-icon">⌕</span>
          <span class="nav-text">搜索聊天</span>
        </button>
        <button type="button" @click="loadHistory">
          <span class="nav-icon">≡</span>
          <span class="nav-text">历史对话</span>
        </button>
      </nav>

      <div v-if="searchOpen && !sidebarCollapsed" class="search-box">
        <input v-model="searchKeyword" placeholder="搜索历史记录" />
      </div>

      <section class="history-section">
        <div v-if="!sidebarCollapsed" class="sidebar-heading">
          <span>历史对话</span>
          <button type="button" title="刷新历史" @click="loadHistory" :disabled="historyLoading">刷新</button>
        </div>

        <p v-if="historyError && !sidebarCollapsed" class="error-text">{{ historyError }}</p>
        <div v-else class="history-list">
          <button
            v-for="record in filteredHistoryRecords"
            :key="record.id"
            type="button"
            class="history-item"
            :class="{ active: selectedHistory?.id === record.id }"
            @click="selectHistory(record)"
          >
            <span>{{ formatTime(record.created_at) }}</span>
            <strong>{{ record.disease_name }}</strong>
            <small>{{ record.risk_level }} · {{ record.provider_name }}</small>
          </button>
          <p v-if="!filteredHistoryRecords.length && !sidebarCollapsed" class="empty-text">
            {{ historyLoading ? '正在读取历史...' : '暂无历史记录' }}
          </p>
        </div>

        <div v-if="historyTotal && !sidebarCollapsed" class="pager">
          <button type="button" title="上一页" @click="goHistoryPage(-1)" :disabled="!canPrevHistory || historyLoading">‹</button>
          <span>{{ historyPage }} / {{ historyPageCount }}</span>
          <button type="button" title="下一页" @click="goHistoryPage(1)" :disabled="!canNextHistory || historyLoading">›</button>
        </div>
      </section>

      <button type="button" class="account-entry" @click="openProfileModal">
        <span class="account-avatar">
          <img v-if="currentUser?.avatar_url" :src="currentUser.avatar_url" alt="用户头像" />
          <span v-else>{{ currentUser?.username?.slice(0, 1)?.toUpperCase() || '登' }}</span>
        </span>
        <span class="account-copy">
          <strong>{{ currentUser?.username || '点击登录' }}</strong>
          <small>{{ currentUser ? '个人设置' : '登录 / 注册' }}</small>
        </span>
      </button>
    </aside>

    <section class="conversation" aria-label="AI 对话区">
      <header class="topbar">
        <div class="model-picker">
          <label>
            <span>文字模型</span>
            <select v-model="selectedTextProviderId">
              <option value="">默认 TextProvider</option>
              <option v-for="provider in textProviders" :key="provider.id" :value="String(provider.id)">
                {{ provider.provider_name }} / {{ provider.model_name }}
              </option>
            </select>
          </label>
          <label>
            <span>视觉模型</span>
            <select v-model="selectedVisionProviderId">
              <option value="">默认 VisionProvider</option>
              <option v-for="provider in visionProviders" :key="provider.id" :value="String(provider.id)">
                {{ provider.provider_name }} / {{ provider.model_name }}
              </option>
            </select>
          </label>
          <button type="button" title="刷新模型列表" @click="loadProviders">刷新</button>
        </div>

        <div class="topbar-status">
          <span class="status-dot" :class="{ online: health?.ok }"></span>
          <button type="button" @click="checkBackend" :disabled="healthLoading">
            {{ serviceState }}
          </button>
        </div>
      </header>

      <div class="message-scroll">
        <p v-if="providerError" class="error-text inline-error">{{ providerError }}</p>

        <section v-if="selectedHistory" class="history-detail-card">
          <div class="detail-head">
            <div>
              <span>历史记录 #{{ selectedHistory.id }}</span>
              <h2>{{ selectedHistory.disease_name }}</h2>
            </div>
            <strong>{{ selectedHistory.risk_level }}</strong>
          </div>
          <p v-if="historyDetailError" class="error-text">{{ historyDetailError }}</p>
          <p v-else-if="historyDetailLoading" class="empty-text">正在读取详情...</p>
          <template v-else>
            <p>{{ selectedHistory.summary }}</p>
            <dl class="detail-grid">
              <div>
                <dt>时间</dt>
                <dd>{{ formatTime(selectedHistory.created_at) }}</dd>
              </div>
              <div>
                <dt>置信度</dt>
                <dd>{{ selectedHistory.confidence_percent !== null ? `${selectedHistory.confidence_percent}%` : '未返回' }}</dd>
              </div>
              <div>
                <dt>Provider</dt>
                <dd>{{ selectedHistory.provider_name }}</dd>
              </div>
              <div>
                <dt>模型</dt>
                <dd>{{ selectedHistory.model_name }}</dd>
              </div>
            </dl>
            <ul v-if="selectedHistory.suggestions?.length" class="suggestion-list">
              <li v-for="item in selectedHistory.suggestions" :key="item">{{ item }}</li>
            </ul>
            <details class="raw-output">
              <summary>查看原始模型输出</summary>
              <pre>{{ selectedHistory.raw_text || '无原始输出' }}</pre>
            </details>
            <button type="button" class="danger-button" @click="removeSelectedHistory" :disabled="historyDeleteLoading">
              {{ historyDeleteLoading ? '删除中...' : '删除这条记录' }}
            </button>
          </template>
        </section>

        <section v-if="!messages.length && !selectedHistory" class="welcome-panel">
          <img src="/logo.png" alt="薯安智检" />
          <h1>今天要分析什么？</h1>
          <p>
            可以直接询问病害问题，也可以拖拽图片到输入框进行识别。
            天气和位置在输入框左侧的扩展菜单中获取。
          </p>
        </section>

        <article v-for="(message, index) in messages" :key="index" class="message" :class="message.role">
          <div class="avatar">{{ message.role === 'user' ? '你' : 'AI' }}</div>
          <div class="message-content">
            <p v-if="message.text">{{ message.text }}</p>
            <img v-if="message.imageUrl" :src="message.imageUrl" alt="已上传图片预览" />
            <div v-if="message.files?.length" class="file-list">
              <span v-for="file in message.files" :key="file.name">
                <b>{{ fileIcon(file) }}</b>{{ file.name }} · {{ formatFileSize(file.size) }}
              </span>
            </div>
            <template v-if="message.type === 'prediction'">
              <div class="prediction-result">
                <div class="detail-head">
                  <div>
                    <span>识别结果</span>
                    <h2>{{ message.result.disease_name }}</h2>
                  </div>
                  <strong>{{ message.result.risk_level }}</strong>
                </div>
                <p>{{ message.result.summary }}</p>
                <ul v-if="message.result.suggestions?.length" class="suggestion-list">
                  <li v-for="item in message.result.suggestions" :key="item">{{ item }}</li>
                </ul>
                <small>{{ message.provider }}</small>
              </div>
            </template>
            <small v-else-if="message.provider">{{ message.provider }}</small>
          </div>
        </article>

        <p v-if="chatError" class="error-text inline-error">{{ chatError }}</p>
        <p v-if="predictError" class="error-text inline-error">{{ predictError }}</p>
        <p v-if="locationError" class="error-text inline-error">{{ locationError }}</p>
        <p v-if="isBusy" class="empty-text inline-status">
          {{ predictLoading ? '正在调用 Vision LLM 识别图片...' : '正在调用 Text LLM 生成回答...' }}
        </p>
      </div>

      <footer class="composer-wrap">
        <div
          class="composer"
          :class="{ dragging: dragActive }"
          @click.stop
          @dragover="onDragOver"
          @dragleave="onDragLeave"
          @drop="onDrop"
        >
          <div v-if="attachedFiles.length || weatherContext" class="context-strip">
            <div v-for="(item, index) in attachedFiles" :key="`${item.name}-${index}`" class="attachment-card">
              <span class="file-badge">{{ fileIcon(item) }}</span>
              <span class="file-meta">
                <strong>{{ item.name }}</strong>
                <small>{{ item.type }} · {{ formatFileSize(item.size) }}</small>
              </span>
              <button type="button" title="取消上传" @click="removeAttachment(index)">×</button>
            </div>
            <div v-if="weatherContext" class="attachment-card weather-card">
              <span class="file-badge">天</span>
              <span class="file-meta">
                <strong>{{ weatherContext.climate_zone }} · {{ weatherContext.weather_text || '天气未知' }}</strong>
                <small>{{ formatCoordinate(weatherContext.latitude) }}, {{ formatCoordinate(weatherContext.longitude) }}</small>
              </span>
            </div>
          </div>

          <form class="composer-form" @submit.prevent="submitComposer">
            <div class="plus-area">
              <button
                type="button"
                class="plus-button"
                title="添加文件等/"
                aria-label="添加文件等"
                @click.stop="plusMenuOpen = !plusMenuOpen"
              >
                +
              </button>
              <div v-if="plusMenuOpen" class="plus-menu" @click.stop>
                <button
                  type="button"
                  class="has-tip"
                  data-tip="支持 png、jpg、txt、word 等格式"
                  @click="triggerFileUpload"
                >
                  <span>📎</span>
                  上传图片/文件
                </button>
                <button type="button" @click="loadWeatherFromBrowser" :disabled="locationLoading">
                  <span>⌖</span>
                  {{ locationLoading ? '获取中...' : environmentReady ? '更新位置和天气' : '获取位置和天气' }}
                </button>
              </div>
            </div>
            <input
              ref="fileInputRef"
              class="hidden-input"
              type="file"
              multiple
              accept=".png,.jpg,.jpeg,.webp,.txt,.md,.doc,.docx,.pdf,image/*,text/*"
              @change="onFileChange"
            />
            <textarea
              v-model="composerText"
              rows="1"
              :placeholder="composerPlaceholder"
              :disabled="isBusy"
              @keydown.enter.exact.prevent="submitComposer"
            ></textarea>
            <button type="submit" class="send-button" :disabled="isBusy || (!composerText.trim() && !attachedFiles.length)">
              ↑
            </button>
          </form>
        </div>
      </footer>
    </section>

    <div v-if="authModalOpen || profileModalOpen" class="modal-backdrop" @click.self="closeModals">
      <section v-if="authModalOpen" class="modal-card">
        <button type="button" class="modal-close" @click="closeModals">×</button>
        <h2>{{ authTitle }}</h2>
        <div class="segmented">
          <button type="button" :class="{ active: authMode === 'login' }" @click="switchAuthMode('login')">登录</button>
          <button type="button" :class="{ active: authMode === 'register' }" @click="switchAuthMode('register')">注册</button>
        </div>
        <form class="auth-form" @submit.prevent="submitAuth">
          <input v-model="authUsername" autocomplete="username" placeholder="用户名" required />
          <input
            v-model="authPassword"
            type="password"
            :autocomplete="authMode === 'login' ? 'current-password' : 'new-password'"
            placeholder="密码"
            required
          />
          <button type="submit" :disabled="authLoading">{{ authLoading ? '处理中...' : authTitle }}</button>
        </form>
        <p v-if="authError" class="error-text">{{ authError }}</p>
      </section>

      <section v-if="profileModalOpen" class="modal-card">
        <button type="button" class="modal-close" @click="closeModals">×</button>
        <h2>个人信息</h2>
        <form class="profile-form" @submit.prevent="submitProfile">
          <label>
            <span>用户名</span>
            <input v-model="profileForm.username" />
          </label>
          <label>
            <span>头像 URL</span>
            <input v-model="profileForm.avatarUrl" placeholder="https://..." />
          </label>
          <label>
            <span>邮箱</span>
            <input v-model="profileForm.email" type="email" placeholder="name@example.com" />
          </label>
          <label>
            <span>当前密码</span>
            <input v-model="profileForm.currentPassword" type="password" placeholder="修改密码时填写" />
          </label>
          <label>
            <span>新密码</span>
            <input v-model="profileForm.password" type="password" placeholder="留空则不修改" />
          </label>
          <button type="submit" :disabled="profileLoading">
            {{ profileLoading ? '保存中...' : '保存资料' }}
          </button>
          <button type="button" class="secondary-button" @click="logout">退出登录</button>
        </form>
        <p v-if="profileError" class="error-text">{{ profileError }}</p>
        <p v-if="profileSuccess" class="success-text">{{ profileSuccess }}</p>
      </section>
    </div>
  </main>
</template>
