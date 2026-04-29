<script setup>
import { computed, onMounted, ref } from 'vue'
import { fetchMe, getAccessToken, loginUser, registerUser, setAccessToken } from './api/auth'
import { askAssistant } from './api/chat'
import { fetchHealth } from './api/health'
import { deleteHistoryRecord, fetchHistory, fetchHistoryRecord } from './api/history'
import { predictImage } from './api/predict'
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

const historyLoading = ref(false)
const historyError = ref('')
const historyRecords = ref([])
const historyLimit = ref(12)
const historyOffset = ref(0)
const historyTotal = ref(0)
const selectedHistory = ref(null)
const historyDetailLoading = ref(false)
const historyDetailError = ref('')
const historyDeleteLoading = ref(false)

const composerText = ref('')
const chatLoading = ref(false)
const chatError = ref('')
const messages = ref([])

const predictLoading = ref(false)
const predictError = ref('')
const predictResult = ref(null)
const selectedImage = ref(null)
const selectedImagePreview = ref('')
const attachedFiles = ref([])

const locationLoading = ref(false)
const locationError = ref('')
const weatherContext = ref(null)

const plusMenuOpen = ref(false)
const imageInputRef = ref(null)
const fileInputRef = ref(null)

const historyPage = computed(() => Math.floor(historyOffset.value / historyLimit.value) + 1)
const historyPageCount = computed(() => Math.max(1, Math.ceil(historyTotal.value / historyLimit.value)))
const canPrevHistory = computed(() => historyOffset.value > 0)
const canNextHistory = computed(() => historyOffset.value + historyLimit.value < historyTotal.value)
const authTitle = computed(() => (authMode.value === 'login' ? '登录' : '注册'))
const environmentReady = computed(() => Boolean(weatherContext.value))
const isBusy = computed(() => chatLoading.value || predictLoading.value)

const serviceState = computed(() => {
  if (healthLoading.value) return '检测中'
  if (health.value?.ok) return '在线'
  if (healthError.value) return '离线'
  return '未知'
})

const composerPlaceholder = computed(() => {
  if (selectedImage.value) return '说明你想让 AI 重点判断什么，也可以直接发送图片识别'
  if (attachedFiles.value.length) return '输入问题，文件名会作为上下文提示发送给 AI'
  return '询问病害、上传图片识别，或通过 + 获取天气位置'
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

async function restoreSession() {
  if (!getAccessToken()) return
  authLoading.value = true
  authError.value = ''
  try {
    currentUser.value = await fetchMe()
  } catch (err) {
    setAccessToken('')
    currentUser.value = null
    authError.value = err instanceof Error ? err.message : '登录状态已失效'
  } finally {
    authLoading.value = false
  }
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
  historyOffset.value = 0
  await loadHistory()
}

function switchAuthMode(mode) {
  authMode.value = mode
  authError.value = ''
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
    const lastItemOnPage = historyRecords.value.length === 1
    if (lastItemOnPage && historyOffset.value > 0) {
      historyOffset.value = Math.max(0, historyOffset.value - historyLimit.value)
    }
    await loadHistory()
  } catch (err) {
    historyDetailError.value = err instanceof Error ? err.message : '历史记录删除失败'
  } finally {
    historyDeleteLoading.value = false
  }
}

function triggerImageUpload() {
  plusMenuOpen.value = false
  imageInputRef.value?.click()
}

function triggerFileUpload() {
  plusMenuOpen.value = false
  fileInputRef.value?.click()
}

function onImageChange(event) {
  const [file] = event.target.files || []
  if (!file) return

  selectedImage.value = file
  selectedImagePreview.value = URL.createObjectURL(file)
  predictError.value = ''
  selectedHistory.value = null
  event.target.value = ''
}

function onFileChange(event) {
  const files = Array.from(event.target.files || [])
  attachedFiles.value = files.map((file) => ({
    name: file.name,
    size: file.size,
    type: file.type || 'application/octet-stream',
  }))
  plusMenuOpen.value = false
  event.target.value = ''
}

function clearImage() {
  if (selectedImagePreview.value) URL.revokeObjectURL(selectedImagePreview.value)
  selectedImage.value = null
  selectedImagePreview.value = ''
}

function clearFiles() {
  attachedFiles.value = []
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
    context.push(`用户已在前端选择文件：${files.map((file) => file.name).join('、')}。当前版本尚未读取文件正文。`)
  }
  return context.join('\n')
}

async function submitComposer() {
  const text = composerText.value.trim()
  if (isBusy.value) return
  if (!text && !selectedImage.value && !attachedFiles.value.length) return

  chatError.value = ''
  predictError.value = ''
  selectedHistory.value = null

  if (selectedImage.value) {
    await submitImageMessage(text)
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
  clearFiles()
  chatLoading.value = true

  try {
    const result = await askAssistant({
      question: text,
      context,
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

async function submitImageMessage(text) {
  const imageFile = selectedImage.value
  const imagePreview = selectedImagePreview.value
  const prompt = text || '请识别这张马铃薯叶片图片，并结合环境给出防治建议。'

  messages.value.push({
    role: 'user',
    text: prompt,
    imageUrl: imagePreview,
    files: [...attachedFiles.value],
  })
  composerText.value = ''
  clearFiles()
  selectedImage.value = null
  selectedImagePreview.value = ''
  predictLoading.value = true

  try {
    const result = await predictImage(imageFile, weatherContext.value)
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
  await restoreSession()
  await loadHistory()
})
</script>

<template>
  <main class="chat-shell">
    <aside class="sidebar" aria-label="历史记录侧边栏">
      <div class="brand-row">
        <div class="brand-mark">薯</div>
        <div>
          <strong>薯安智检</strong>
          <span>马铃薯病害 AI 平台</span>
        </div>
      </div>

      <section class="auth-box">
        <template v-if="currentUser">
          <div class="user-card">
            <span>当前用户</span>
            <strong>{{ currentUser.username }}</strong>
          </div>
          <button type="button" class="secondary-button" @click="logout">退出登录</button>
        </template>
        <template v-else>
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
        </template>
      </section>

      <section class="history-section">
        <div class="sidebar-heading">
          <span>识别历史</span>
          <button type="button" class="icon-button" title="刷新历史" @click="loadHistory" :disabled="historyLoading">↻</button>
        </div>

        <p v-if="historyError" class="error-text">{{ historyError }}</p>
        <div v-else class="history-list">
          <button
            v-for="record in historyRecords"
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
          <p v-if="!historyRecords.length" class="empty-text">
            {{ historyLoading ? '正在读取历史...' : '暂无历史记录' }}
          </p>
        </div>

        <div v-if="historyTotal" class="pager">
          <button type="button" class="icon-button" title="上一页" @click="goHistoryPage(-1)" :disabled="!canPrevHistory || historyLoading">‹</button>
          <span>{{ historyPage }} / {{ historyPageCount }}</span>
          <button type="button" class="icon-button" title="下一页" @click="goHistoryPage(1)" :disabled="!canNextHistory || historyLoading">›</button>
        </div>
      </section>

      <div class="service-box">
        <span class="status-dot" :class="{ online: health?.ok }"></span>
        <div>
          <strong>后端 {{ serviceState }}</strong>
          <button type="button" @click="checkBackend" :disabled="healthLoading">
            {{ healthLoading ? '检测中...' : '重新检测' }}
          </button>
        </div>
      </div>
    </aside>

    <section class="conversation" aria-label="AI 对话区">
      <header class="conversation-header">
        <div>
          <p>API 驱动基线</p>
          <h1>马铃薯病害智能助手</h1>
        </div>
        <div v-if="weatherContext" class="weather-chip" title="当前环境上下文">
          <span>{{ weatherContext.climate_zone }}</span>
          <strong>{{ weatherContext.weather_text || '天气未知' }}</strong>
          <small>{{ weatherContext.temperature_c ?? '未知' }}°C / {{ weatherContext.relative_humidity_percent ?? '未知' }}%</small>
        </div>
      </header>

      <div class="message-scroll">
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
          <div class="welcome-mark">+</div>
          <h2>从一句问题或一张叶片图片开始</h2>
          <p>
            左侧保留识别历史。底部输入框左侧的 + 可上传图片、选择文件、获取位置和天气。
            图片识别会调用后端配置的 Vision LLM；普通问答会调用 Text LLM。
          </p>
        </section>

        <article v-for="(message, index) in messages" :key="index" class="message" :class="message.role">
          <div class="avatar">{{ message.role === 'user' ? '你' : 'AI' }}</div>
          <div class="message-content">
            <p v-if="message.text">{{ message.text }}</p>
            <img v-if="message.imageUrl" :src="message.imageUrl" alt="已上传图片预览" />
            <div v-if="message.files?.length" class="file-list">
              <span v-for="file in message.files" :key="file.name">{{ file.name }} · {{ formatFileSize(file.size) }}</span>
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
        <div v-if="selectedImage || attachedFiles.length || weatherContext" class="context-strip">
          <div v-if="selectedImage" class="attachment-pill">
            <img :src="selectedImagePreview" alt="待识别图片" />
            <span>{{ selectedImage.name }}</span>
            <button type="button" title="移除图片" @click="clearImage">×</button>
          </div>
          <div v-for="file in attachedFiles" :key="file.name" class="attachment-pill">
            <span>{{ file.name }}</span>
            <small>{{ formatFileSize(file.size) }}</small>
          </div>
          <button v-if="attachedFiles.length" type="button" class="text-button" @click="clearFiles">清空文件</button>
          <div v-if="weatherContext" class="attachment-pill">
            <span>{{ weatherContext.climate_zone }} · {{ weatherContext.weather_text || '天气未知' }}</span>
            <small>{{ formatCoordinate(weatherContext.latitude) }}, {{ formatCoordinate(weatherContext.longitude) }}</small>
          </div>
        </div>

        <form class="composer" @submit.prevent="submitComposer">
          <div class="plus-area">
            <button type="button" class="plus-button" aria-label="扩展功能" @click="plusMenuOpen = !plusMenuOpen">+</button>
            <div v-if="plusMenuOpen" class="plus-menu">
              <button type="button" @click="triggerImageUpload">上传图片识别</button>
              <button type="button" @click="triggerFileUpload">上传文件</button>
              <button type="button" @click="loadWeatherFromBrowser" :disabled="locationLoading">
                {{ locationLoading ? '获取中...' : environmentReady ? '更新位置和天气' : '获取位置和天气' }}
              </button>
            </div>
          </div>
          <input ref="imageInputRef" class="hidden-input" type="file" accept="image/*" @change="onImageChange" />
          <input ref="fileInputRef" class="hidden-input" type="file" multiple @change="onFileChange" />
          <textarea
            v-model="composerText"
            rows="1"
            :placeholder="composerPlaceholder"
            :disabled="isBusy"
            @keydown.enter.exact.prevent="submitComposer"
          ></textarea>
          <button type="submit" class="send-button" :disabled="isBusy || (!composerText.trim() && !selectedImage && !attachedFiles.length)">
            ↑
          </button>
        </form>
      </footer>
    </section>
  </main>
</template>
