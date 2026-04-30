<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import {
  changePassword,
  fetchMe,
  getAccessToken,
  loginUser,
  registerUser,
  setAccessToken,
  uploadAvatar,
  updateProfile,
} from './api/auth'
import { streamAssistant } from './api/chat'
import { API_BASE_URL, fetchHealth } from './api/health'
import { deleteHistoryRecord, fetchHistory, fetchHistoryRecord, renameHistoryRecord } from './api/history'
import { streamPredictImage } from './api/predict'
import { fetchEnabledProviders } from './api/providers'
import { fetchWeather } from './api/weather'

const toolIcons = {
  deepThink: '/deepthink.png',
  weather: '/weather.png',
  upload: '/link.png',
  webSearch: '/websearch.png',
}

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
const profileAvatarInputRef = ref(null)
const avatarUploading = ref(false)
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
const activeHistoryMenuId = ref(null)
const searchOpen = ref(false)
const searchKeyword = ref('')

const messages = ref([])
const currentConversationId = ref(null)
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
const pageDragActive = ref(false)
const attachmentError = ref('')
let dragDepth = 0

const locationLoading = ref(false)
const locationError = ref('')
const weatherContext = ref(null)
const webSearchEnabled = ref(false)

const plusMenuOpen = ref(false)
const sidebarCollapsed = ref(false)

const providers = ref([])
const providerError = ref('')
const selectedProviderId = ref('')
const deepThinking = ref(false)

const historyPage = computed(() => Math.floor(historyOffset.value / historyLimit.value) + 1)
const historyPageCount = computed(() => Math.max(1, Math.ceil(historyTotal.value / historyLimit.value)))
const canPrevHistory = computed(() => historyOffset.value > 0)
const canNextHistory = computed(() => historyOffset.value + historyLimit.value < historyTotal.value)
const isBusy = computed(() => chatLoading.value || predictLoading.value)
const authTitle = computed(() => (authMode.value === 'login' ? '登录' : '注册'))
const environmentReady = computed(() => Boolean(weatherContext.value))
const appLocked = computed(() => !currentUser.value)
const backendOrigin = computed(() => API_BASE_URL.replace(/\/api\/?$/, ''))

const modelProviders = computed(() => providers.value)
const activeProvider = computed(() =>
  modelProviders.value.find((provider) => String(provider.id) === String(selectedProviderId.value)),
)
const quickProviders = computed(() => modelProviders.value.filter((provider) => !provider.supports_reasoning))
const reasoningProviders = computed(() => modelProviders.value.filter((provider) => provider.supports_reasoning))

const filteredHistoryRecords = computed(() => {
  const keyword = searchKeyword.value.trim().toLowerCase()
  if (!keyword) return historyRecords.value
  return historyRecords.value.filter((record) => {
    return [record.title]
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
  if (appLocked.value) return '请先登录后使用'
  if (attachedFiles.value.length) return '输入问题，或直接发送图片进行识别'
  return '给马铃薯病害助手发送消息'
})

function resolveAssetUrl(value) {
  if (!value) return ''
  if (/^https?:\/\//i.test(value)) return value
  return `${backendOrigin.value}${value}`
}

watch(deepThinking, (enabled) => {
  if (!modelProviders.value.length) return
  const current = activeProvider.value
  if (enabled && current?.supports_reasoning) return
  if (!enabled && current && !current.supports_reasoning) return

  const pool = enabled ? reasoningProviders.value : quickProviders.value
  if (pool.length) selectedProviderId.value = String(pool[0].id)
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
    if (!selectedProviderId.value && modelProviders.value.length) {
      const preferred =
        quickProviders.value.find((provider) => provider.model_name === 'kimi-k2.6') ||
        quickProviders.value[0] ||
        modelProviders.value.find((provider) => provider.model_name === 'kimi-k2.6') ||
        modelProviders.value[0]
      selectedProviderId.value = String(preferred.id)
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
    currentConversationId.value = null
    messages.value = []
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
  currentConversationId.value = null
  messages.value = []
  selectedHistory.value = null
  profileModalOpen.value = false
  historyOffset.value = 0
  await loadHistory()
}

function requireLogin() {
  if (currentUser.value) return true
  openAuthModal('login')
  return false
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

async function onProfileAvatarChange(event) {
  const [file] = event.target.files || []
  event.target.value = ''
  if (!file || avatarUploading.value) return

  avatarUploading.value = true
  profileError.value = ''
  profileSuccess.value = ''

  try {
    currentUser.value = await uploadAvatar(file)
    syncProfileForm()
    profileSuccess.value = '头像已上传'
  } catch (err) {
    profileError.value = err instanceof Error ? err.message : '头像上传失败'
  } finally {
    avatarUploading.value = false
  }
}

function switchAuthMode(mode) {
  authMode.value = mode
  authError.value = ''
}

function newChat() {
  if (!requireLogin()) return
  messages.value = []
  currentConversationId.value = null
  selectedHistory.value = null
  chatError.value = ''
  predictError.value = ''
  attachmentError.value = ''
  composerText.value = ''
}

async function loadHistory() {
  if (!currentUser.value) {
    historyRecords.value = []
    historyTotal.value = 0
    return
  }

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
    currentConversationId.value = selectedHistory.value.id
    messages.value = (selectedHistory.value.messages || []).map((item) => {
      const payload = item.payload || {}
      if (item.message_type === 'prediction' && payload.provider_name) {
        return {
          role: item.role,
          type: 'prediction',
          result: payload,
          provider: payload.provider_name || '',
        }
      }
      return {
        role: item.role,
        text: item.content,
        reasoning: payload.reasoning_content || '',
        provider: item.provider_name || '',
      }
    })
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
    if (currentConversationId.value === selectedHistory.value.id) {
      currentConversationId.value = null
      messages.value = []
    }
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

function toggleHistoryMenu(recordId) {
  activeHistoryMenuId.value = activeHistoryMenuId.value === recordId ? null : recordId
}

async function removeHistoryByRecord(record) {
  if (!record || historyDeleteLoading.value) return
  historyDeleteLoading.value = true
  historyDetailError.value = ''
  activeHistoryMenuId.value = null

  try {
    await deleteHistoryRecord(record.id)
    if (currentConversationId.value === record.id) {
      currentConversationId.value = null
      messages.value = []
    }
    if (selectedHistory.value?.id === record.id) {
      selectedHistory.value = null
    }
    if (historyRecords.value.length === 1 && historyOffset.value > 0) {
      historyOffset.value = Math.max(0, historyOffset.value - historyLimit.value)
    }
    await loadHistory()
  } catch (err) {
    historyError.value = err instanceof Error ? err.message : '历史记录删除失败'
  } finally {
    historyDeleteLoading.value = false
  }
}

async function renameHistoryByRecord(record) {
  if (!record) return
  activeHistoryMenuId.value = null
  const nextTitle = window.prompt('重命名会话', record.title || '')
  if (nextTitle === null) return
  const normalized = nextTitle.trim()
  if (!normalized || normalized === record.title) return

  try {
    const updated = await renameHistoryRecord(record.id, normalized)
    historyRecords.value = historyRecords.value.map((item) => (item.id === updated.id ? updated : item))
    if (selectedHistory.value?.id === updated.id) {
      selectedHistory.value = { ...selectedHistory.value, title: updated.title, updated_at: updated.updated_at }
    }
  } catch (err) {
    historyError.value = err instanceof Error ? err.message : '历史记录重命名失败'
  }
}

function closeFloatingPanels() {
  plusMenuOpen.value = false
  activeHistoryMenuId.value = null
}

function enableWebSearch() {
  if (!requireLogin()) return
  webSearchEnabled.value = true
  plusMenuOpen.value = false
}

function clearWeatherContext() {
  weatherContext.value = null
  locationError.value = ''
}

function triggerFileUpload() {
  fileInputRef.value?.click()
}

function appendFiles(files, options = {}) {
  const { imagesOnly = false } = options
  const nextFiles = Array.from(files || [])
  if (!nextFiles.length) return

  nextFiles.forEach((file) => {
    const isImage = file.type?.startsWith('image/') || /\.(png|jpe?g|webp|gif)$/i.test(file.name)
    if (imagesOnly && !isImage) {
      attachmentError.value = '当前仅支持上传图片'
      return
    }
    attachmentError.value = ''
    attachedFiles.value.push({
      file,
      name: file.name,
      size: file.size,
      type: file.type || inferFileType(file.name),
      previewUrl: isImage ? URL.createObjectURL(file) : '',
    })
  })
  const firstImage = attachedFiles.value.find((item) => item.previewUrl)
  selectedImagePreview.value = firstImage?.previewUrl || ''
}

function onFileChange(event) {
  appendFiles(event.target.files, { imagesOnly: true })
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
  pageDragActive.value = false
  dragDepth = 0
  appendFiles(event.dataTransfer.files, { imagesOnly: true })
}

function onPageDragEnter(event) {
  event.preventDefault()
  dragDepth += 1
  pageDragActive.value = true
}

function onPageDragOver(event) {
  event.preventDefault()
  pageDragActive.value = true
}

function onPageDragLeave(event) {
  event.preventDefault()
  dragDepth = Math.max(0, dragDepth - 1)
  if (dragDepth === 0) {
    pageDragActive.value = false
  }
}

function onPageDrop(event) {
  event.preventDefault()
  dragDepth = 0
  pageDragActive.value = false
  dragActive.value = false
  appendFiles(event.dataTransfer.files, { imagesOnly: true })
}

function onPaste(event) {
  const items = Array.from(event.clipboardData?.items || [])
  const imageFiles = items
    .filter((item) => item.kind === 'file' && item.type.startsWith('image/'))
    .map((item) => item.getAsFile())
    .filter(Boolean)

  if (!imageFiles.length) return

  const text = event.clipboardData?.getData('text/plain') || ''
  const renamedFiles = imageFiles.map((file) => {
    const extension = file.type.split('/')[1] || 'png'
    return new File([file], `clipboard-${formatCompactTimestamp()}.${extension}`, {
      type: file.type || 'image/png',
    })
  })
  event.preventDefault()
  if (text && event.target?.tagName === 'TEXTAREA') {
    composerText.value = `${composerText.value}${text}`
  }
  appendFiles(renamedFiles, { imagesOnly: true })
}

async function loadWeatherFromBrowser() {
  plusMenuOpen.value = false
  if (!requireLogin()) return
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
  if (!requireLogin()) return
  const text = composerText.value.trim()
  if (isBusy.value) return
  if (!text && !attachedFiles.value.length) return
  if (!selectedProviderId.value) {
    chatError.value = '请先在后台配置并启用一个通用模型。'
    return
  }

  chatError.value = ''
  predictError.value = ''
  attachmentError.value = ''
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
  const assistantMessage = {
    role: 'assistant',
    text: '',
    reasoning: '',
    provider: '',
  }
  messages.value.push(assistantMessage)

  try {
    await streamAssistant(
      {
        question: text,
        context,
        provider_id: selectedProviderId.value ? Number(selectedProviderId.value) : null,
        conversation_id: currentConversationId.value,
        deep_thinking: deepThinking.value,
        web_search: webSearchEnabled.value,
      },
      {
        onMeta(event) {
          currentConversationId.value = event.conversation_id || currentConversationId.value
          assistantMessage.provider = event.provider_name || ''
        },
        onReasoning(chunk) {
          assistantMessage.reasoning += chunk
        },
        onContent(chunk) {
          assistantMessage.text += chunk
        },
        onDone(event) {
          currentConversationId.value = event.conversation_id || currentConversationId.value
        },
      },
    )
    if (!assistantMessage.text && assistantMessage.reasoning) {
      assistantMessage.text = '模型已返回推理过程，但尚未生成最终答案。请增大后台输出长度、关闭深度思考，或稍后重试。'
    }
    if (!assistantMessage.text) {
      assistantMessage.text = '模型未返回有效内容'
    }
    await loadHistory()
  } catch (err) {
    if (err?.conversationId) currentConversationId.value = err.conversationId
    chatError.value = normalizeModelError(err instanceof Error ? err.message : 'AI 助手调用失败')
    assistantMessage.text = chatError.value
    await loadHistory()
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
  const assistantMessage = {
    role: 'assistant',
    type: 'prediction',
    result: {
      provider_name: activeProvider.value?.provider_name || '',
      model_name: activeProvider.value?.model_name || '',
      disease_name: '模型回复',
      risk_level: '识别中',
      summary: '',
      content: '',
      raw_text: '',
      suggestions: [],
      reasoning_content: '',
    },
    provider: activeProvider.value?.provider_name || '',
  }
  messages.value.push(assistantMessage)

  try {
    await streamPredictImage(
      imageAttachment.file,
      weatherContext.value,
      selectedProviderId.value ? Number(selectedProviderId.value) : null,
      currentConversationId.value,
      prompt,
      deepThinking.value,
      webSearchEnabled.value,
      {
        onMeta(event) {
          currentConversationId.value = event.conversation_id || currentConversationId.value
          assistantMessage.provider = event.provider_name || ''
          assistantMessage.result.provider_name = event.provider_name
          assistantMessage.result.model_name = event.model_name
        },
        onReasoning(chunk) {
          assistantMessage.result.reasoning_content += chunk
        },
        onContent(chunk) {
          assistantMessage.result.content += chunk
          assistantMessage.result.raw_text = assistantMessage.result.content
          assistantMessage.result.summary = assistantMessage.result.content
        },
        onResult(result) {
          assistantMessage.result = result
          assistantMessage.provider = result.provider_name || ''
          predictResult.value = result
          if (result.weather) weatherContext.value = result.weather
        },
        onDone(event) {
          currentConversationId.value = event.conversation_id || currentConversationId.value
        },
      },
    )
    await loadHistory()
  } catch (err) {
    if (err?.conversationId) currentConversationId.value = err.conversationId
    predictError.value = normalizeModelError(err instanceof Error ? err.message : '图片识别失败')
    assistantMessage.type = ''
    assistantMessage.text = predictError.value
    await loadHistory()
  } finally {
    predictLoading.value = false
  }
}

function normalizeModelError(message) {
  const value = String(message || '')
  if (value.includes('429') || value.toLowerCase().includes('overloaded')) {
    return '当前模型过载，请切换到 kimi-k2.6 或稍后重试。'
  }
  return value
}

function escapeHtml(value) {
  return String(value ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

function renderMarkdown(value) {
  const source = String(value || '')
  const codeBlocks = []
  let html = escapeHtml(source).replace(/```([\s\S]*?)```/g, (_match, code) => {
    const index = codeBlocks.length
    codeBlocks.push(`<pre><code>${code.trim()}</code></pre>`)
    return `\n@@CODE_BLOCK_${index}@@\n`
  })

  html = html
    .replace(/^### (.*)$/gm, '<h3>$1</h3>')
    .replace(/^## (.*)$/gm, '<h2>$1</h2>')
    .replace(/^# (.*)$/gm, '<h1>$1</h1>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/\[([^\]]+)\]\((https?:\/\/[^)]+)\)/g, '<a href="$2" target="_blank" rel="noreferrer">$1</a>')

  html = html.replace(/(?:^|\n)((?:[-*] .+(?:\n|$))+)/g, (match, list) => {
    const items = list
      .trim()
      .split(/\n/)
      .map((line) => `<li>${line.replace(/^[-*] /, '')}</li>`)
      .join('')
    return `${match.startsWith('\n') ? '\n' : ''}<ul>${items}</ul>\n`
  })

  html = html
    .split(/\n{2,}/)
    .map((block) => {
      const trimmed = block.trim()
      if (!trimmed) return ''
      if (/^<(h1|h2|h3|ul|pre)/.test(trimmed) || /^@@CODE_BLOCK_\d+@@$/.test(trimmed)) {
        return trimmed
      }
      return `<p>${trimmed.replace(/\n/g, '<br>')}</p>`
    })
    .join('')

  codeBlocks.forEach((block, index) => {
    html = html.replace(`@@CODE_BLOCK_${index}@@`, block)
  })
  return html
}

function inferFileType(name) {
  const ext = name.split('.').pop()?.toLowerCase()
  if (!ext) return 'file'
  if (['png', 'jpg', 'jpeg', 'webp', 'gif'].includes(ext)) return `image/${ext}`
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

function predictionTitle(result) {
  const title = result?.disease_name || ''
  if (!title || title === '待确认' || title === '模型回复') return '模型识别结果'
  return title
}

function predictionStatus(result) {
  const status = result?.risk_level || ''
  if (!status || status === '待确认' || status === '未结构化') return '已返回'
  return status
}

function predictionContent(result) {
  return result?.content || result?.raw_text || result?.summary || '模型未返回有效内容'
}

function messageCopyText(message) {
  if (message.type === 'prediction') return predictionContent(message.result)
  return message.text || ''
}

async function copyMessage(message) {
  const text = messageCopyText(message)
  if (!text) return
  await navigator.clipboard?.writeText(text)
}

function previousUserMessage(index) {
  for (let cursor = index - 1; cursor >= 0; cursor -= 1) {
    if (messages.value[cursor]?.role === 'user') return messages.value[cursor]
  }
  return null
}

async function retryMessage(index) {
  if (isBusy.value) return
  const source = previousUserMessage(index)
  if (!source?.text) return

  const imageAttachment = source.files?.find((item) => item.file?.type?.startsWith('image/'))
  messages.value.splice(index, 1)
  if (imageAttachment) {
    await regenerateImageAnswer(index, source.text, imageAttachment)
    return
  }
  await regenerateTextAnswer(index, source.text, source.files || [])
}

async function regenerateTextAnswer(index, text, files = []) {
  const assistantMessage = {
    role: 'assistant',
    text: '',
    reasoning: '',
    provider: '',
  }
  messages.value.splice(index, 0, assistantMessage)
  chatLoading.value = true
  chatError.value = ''

  try {
    await streamAssistant(
      {
        question: text,
        context: buildChatContext(files),
        provider_id: selectedProviderId.value ? Number(selectedProviderId.value) : null,
        conversation_id: currentConversationId.value,
        deep_thinking: deepThinking.value,
        web_search: webSearchEnabled.value,
      },
      {
        onMeta(event) {
          currentConversationId.value = event.conversation_id || currentConversationId.value
          assistantMessage.provider = event.provider_name || ''
        },
        onReasoning(chunk) {
          assistantMessage.reasoning += chunk
        },
        onContent(chunk) {
          assistantMessage.text += chunk
        },
        onDone(event) {
          currentConversationId.value = event.conversation_id || currentConversationId.value
        },
      },
    )
    if (!assistantMessage.text && assistantMessage.reasoning) {
      assistantMessage.text = '模型已返回推理过程，但尚未生成最终答案。请增大后台输出长度、关闭深度思考，或稍后重试。'
    }
    if (!assistantMessage.text) assistantMessage.text = '模型未返回有效内容'
    await loadHistory()
  } catch (err) {
    if (err?.conversationId) currentConversationId.value = err.conversationId
    assistantMessage.text = normalizeModelError(err instanceof Error ? err.message : 'AI 助手调用失败')
    await loadHistory()
  } finally {
    chatLoading.value = false
  }
}

async function regenerateImageAnswer(index, text, imageAttachment) {
  const assistantMessage = {
    role: 'assistant',
    type: 'prediction',
    result: {
      provider_name: activeProvider.value?.provider_name || '',
      model_name: activeProvider.value?.model_name || '',
      disease_name: '模型回复',
      risk_level: '识别中',
      summary: '',
      content: '',
      raw_text: '',
      suggestions: [],
      reasoning_content: '',
    },
    provider: activeProvider.value?.provider_name || '',
  }
  messages.value.splice(index, 0, assistantMessage)
  predictLoading.value = true
  predictError.value = ''

  try {
    await streamPredictImage(
      imageAttachment.file,
      weatherContext.value,
      selectedProviderId.value ? Number(selectedProviderId.value) : null,
      currentConversationId.value,
      text,
      deepThinking.value,
      webSearchEnabled.value,
      {
        onMeta(event) {
          currentConversationId.value = event.conversation_id || currentConversationId.value
          assistantMessage.provider = event.provider_name || ''
          assistantMessage.result.provider_name = event.provider_name
          assistantMessage.result.model_name = event.model_name
        },
        onReasoning(chunk) {
          assistantMessage.result.reasoning_content += chunk
        },
        onContent(chunk) {
          assistantMessage.result.content += chunk
          assistantMessage.result.raw_text = assistantMessage.result.content
          assistantMessage.result.summary = assistantMessage.result.content
        },
        onResult(result) {
          assistantMessage.result = result
          assistantMessage.provider = result.provider_name || ''
          predictResult.value = result
        },
        onDone(event) {
          currentConversationId.value = event.conversation_id || currentConversationId.value
        },
      },
    )
    await loadHistory()
  } catch (err) {
    if (err?.conversationId) currentConversationId.value = err.conversationId
    assistantMessage.type = ''
    assistantMessage.text = normalizeModelError(err instanceof Error ? err.message : '图片识别失败')
    await loadHistory()
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

function formatCompactTimestamp(value = new Date()) {
  const pad = (number) => String(number).padStart(2, '0')
  return `${value.getFullYear()}${pad(value.getMonth() + 1)}${pad(value.getDate())}-${pad(value.getHours())}${pad(
    value.getMinutes(),
  )}`
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
    @dragenter="onPageDragEnter"
    @dragover="onPageDragOver"
    @dragleave="onPageDragLeave"
    @drop="onPageDrop"
    @paste="onPaste"
  >
    <div v-if="pageDragActive" class="drop-overlay">
      <div>释放以上传图片</div>
    </div>
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
          <div
            v-for="record in filteredHistoryRecords"
            :key="record.id"
            class="history-item"
            :class="{ active: selectedHistory?.id === record.id }"
          >
            <button type="button" class="history-main" @click="selectHistory(record)">
              <span>{{ formatTime(record.updated_at || record.created_at) }}</span>
              <strong>{{ record.title }}</strong>
              <small>会话记录</small>
            </button>
            <button
              v-if="!sidebarCollapsed"
              type="button"
              class="history-more"
              title="更多操作"
              @click.stop="toggleHistoryMenu(record.id)"
            >
              ···
            </button>
            <div v-if="activeHistoryMenuId === record.id && !sidebarCollapsed" class="history-menu" @click.stop>
              <button type="button" @click="renameHistoryByRecord(record)">重命名</button>
              <button type="button" class="danger-text" @click="removeHistoryByRecord(record)">删除</button>
            </div>
          </div>
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
          <img v-if="currentUser?.avatar_url" :src="resolveAssetUrl(currentUser.avatar_url)" alt="用户头像" />
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
            <span>模型</span>
            <select v-model="selectedProviderId">
              <option value="" disabled>请选择模型</option>
              <option v-for="provider in modelProviders" :key="provider.id" :value="String(provider.id)">
                {{ provider.provider_name }}
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

        <p v-if="historyDetailError" class="error-text inline-error">{{ historyDetailError }}</p>
        <p v-else-if="historyDetailLoading" class="empty-text inline-error">正在读取详情...</p>

        <section v-if="!messages.length && !selectedHistory" class="welcome-panel">
          <img src="/logo.png" alt="薯安智检" />
          <h1>今天要分析什么？</h1>
          <p>
            可以直接询问病害问题，也可以拖拽图片到聊天页面任意位置进行识别。
            天气和位置在输入框左侧的扩展菜单中获取。
          </p>
        </section>

        <article v-for="(message, index) in messages" :key="index" class="message" :class="message.role">
          <div class="message-content">
            <div v-if="message.text" class="markdown-body" v-html="renderMarkdown(message.text)"></div>
            <details v-if="message.reasoning" class="reasoning-block">
              <summary>推理过程</summary>
              <div class="markdown-body" v-html="renderMarkdown(message.reasoning)"></div>
            </details>
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
                    <h2>{{ predictionTitle(message.result) }}</h2>
                  </div>
                  <strong>{{ predictionStatus(message.result) }}</strong>
                </div>
                <div class="markdown-body" v-html="renderMarkdown(predictionContent(message.result))"></div>
                <details v-if="message.result.reasoning_content" class="reasoning-block">
                  <summary>推理过程</summary>
                  <div class="markdown-body" v-html="renderMarkdown(message.result.reasoning_content)"></div>
                </details>
                <ul v-if="message.result.suggestions?.length" class="suggestion-list">
                  <li v-for="item in message.result.suggestions" :key="item">{{ item }}</li>
                </ul>
                <small>{{ message.provider }}</small>
              </div>
            </template>
            <small v-else-if="message.provider">{{ message.provider }}</small>
            <div class="message-actions">
              <button type="button" @click="copyMessage(message)">复制</button>
              <button v-if="message.role === 'assistant'" type="button" :disabled="isBusy" @click="retryMessage(index)">重试</button>
            </div>
          </div>
        </article>

        <p v-if="chatError" class="error-text inline-error">{{ chatError }}</p>
        <p v-if="predictError" class="error-text inline-error">{{ predictError }}</p>
        <p v-if="attachmentError" class="error-text inline-error">{{ attachmentError }}</p>
        <p v-if="locationError" class="error-text inline-error">{{ locationError }}</p>
        <article v-if="isBusy" class="message assistant status-message">
          <div class="message-content">
            <p>{{ predictLoading ? '正在调用 Vision LLM 识别图片...' : '正在调用 Text LLM 生成回答...' }}</p>
          </div>
        </article>
      </div>

      <footer class="composer-wrap">
        <div
          class="composer"
          :class="{ dragging: dragActive }"
          @click.stop
          @dragover.stop="onDragOver"
          @dragleave.stop="onDragLeave"
          @drop.stop="onDrop"
        >
          <div v-if="attachedFiles.length" class="context-strip">
            <div v-for="(item, index) in attachedFiles" :key="`${item.name}-${index}`" class="attachment-card">
              <span class="file-badge">{{ fileIcon(item) }}</span>
              <span class="file-meta">
                <strong>{{ item.name }}</strong>
                <small>{{ item.type }} · {{ formatFileSize(item.size) }}</small>
              </span>
              <button type="button" title="取消上传" @click="removeAttachment(index)">×</button>
            </div>
          </div>

          <form class="composer-form" @submit.prevent="submitComposer">
            <input
              ref="fileInputRef"
              class="hidden-input"
              type="file"
              multiple
              accept="image/png,image/jpeg,image/webp,image/gif"
              @change="onFileChange"
            />
            <textarea
              v-model="composerText"
              rows="1"
              :placeholder="composerPlaceholder"
              :disabled="isBusy || appLocked"
              @keydown.enter.exact.prevent="submitComposer"
            ></textarea>
            <div class="composer-actions">
              <div class="plus-area">
                <button
                  type="button"
                  class="plus-button"
                  title="添加文件等/"
                  aria-label="添加文件等"
                  :disabled="appLocked"
                  @click.stop="requireLogin() && (plusMenuOpen = !plusMenuOpen)"
                >
                  +
                </button>
                <div v-if="plusMenuOpen" class="plus-menu" @click.stop>
                  <button
                    type="button"
                    class="has-tip"
                    data-tip="当前支持 png、jpg、jpeg、webp 图片"
                    @click="triggerFileUpload"
                  >
                    <span><img :src="toolIcons.upload" alt="" /></span>
                    上传图片/文件
                  </button>
                  <button type="button" @click="loadWeatherFromBrowser" :disabled="locationLoading">
                    <span><img :src="toolIcons.weather" alt="" /></span>
                    {{ locationLoading ? '获取中...' : environmentReady ? '更新位置和天气' : '获取位置和天气' }}
                  </button>
                  <button type="button" @click="enableWebSearch">
                    <span><img :src="toolIcons.webSearch" alt="" /></span>
                    网页搜索
                  </button>
                </div>
              </div>
              <button
                v-if="weatherContext"
                type="button"
                class="tool-chip"
                title="取消天气和位置"
                @click="clearWeatherContext"
              >
                <img :src="toolIcons.weather" alt="" />
                <span>天气与位置</span>
                <b>×</b>
              </button>
              <button
                v-if="webSearchEnabled"
                type="button"
                class="tool-chip"
                title="取消网页搜索"
                @click="webSearchEnabled = false"
              >
                <img :src="toolIcons.webSearch" alt="" />
                <span>网页搜索</span>
                <b>×</b>
              </button>
              <button
                type="button"
                class="thinking-button"
                :class="{ active: deepThinking }"
                :disabled="appLocked || isBusy"
                @click="deepThinking = !deepThinking"
              >
                <img :src="toolIcons.deepThink" alt="" />
                深度思考
              </button>
              <span class="composer-spacer"></span>
              <button type="submit" class="send-button" :disabled="appLocked || isBusy || (!composerText.trim() && !attachedFiles.length)">
                ↑
              </button>
            </div>
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
          <div class="avatar-upload-row">
            <span class="profile-avatar-preview">
              <img v-if="profileForm.avatarUrl" :src="resolveAssetUrl(profileForm.avatarUrl)" alt="头像预览" />
              <span v-else>{{ currentUser?.username?.slice(0, 1)?.toUpperCase() || 'U' }}</span>
            </span>
            <div>
              <button type="button" class="secondary-button" @click="profileAvatarInputRef?.click()" :disabled="avatarUploading">
                {{ avatarUploading ? '上传中...' : '上传头像' }}
              </button>
              <small>支持 PNG、JPG、WebP，文件保存到服务器 uploads 目录。</small>
            </div>
            <input
              ref="profileAvatarInputRef"
              class="hidden-input"
              type="file"
              accept="image/png,image/jpeg,image/webp"
              @change="onProfileAvatarChange"
            />
          </div>
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
