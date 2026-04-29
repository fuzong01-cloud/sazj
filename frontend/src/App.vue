<script setup>
import { computed, onMounted, ref } from 'vue'
import { fetchMe, getAccessToken, loginUser, registerUser, setAccessToken } from './api/auth'
import { askAssistant } from './api/chat'
import { fetchHealth } from './api/health'
import { deleteHistoryRecord, fetchHistory, fetchHistoryRecord } from './api/history'
import { predictImage } from './api/predict'

const health = ref(null)
const healthLoading = ref(false)
const healthError = ref('')
const selectedFile = ref(null)
const previewUrl = ref('')
const predictLoading = ref(false)
const predictError = ref('')
const predictResult = ref(null)
const currentUser = ref(null)
const authMode = ref('login')
const authUsername = ref('')
const authPassword = ref('')
const authLoading = ref(false)
const authError = ref('')
const historyLoading = ref(false)
const historyError = ref('')
const historyRecords = ref([])
const historyLimit = ref(10)
const historyOffset = ref(0)
const historyTotal = ref(0)
const selectedHistory = ref(null)
const historyDetailLoading = ref(false)
const historyDetailError = ref('')
const historyDeleteLoading = ref(false)
const chatQuestion = ref('')
const chatLoading = ref(false)
const chatError = ref('')
const chatMessages = ref([])

const historyPage = computed(() => Math.floor(historyOffset.value / historyLimit.value) + 1)
const historyPageCount = computed(() => Math.max(1, Math.ceil(historyTotal.value / historyLimit.value)))
const canPrevHistory = computed(() => historyOffset.value > 0)
const canNextHistory = computed(() => historyOffset.value + historyLimit.value < historyTotal.value)
const authTitle = computed(() => (authMode.value === 'login' ? '用户登录' : '用户注册'))

const serviceState = computed(() => {
  if (healthLoading.value) return '检测中'
  if (health.value?.ok) return '后端已连接'
  if (healthError.value) return '后端未连接'
  return '等待检测'
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

function onFileChange(event) {
  const [file] = event.target.files || []
  selectedFile.value = file || null
  predictResult.value = null
  predictError.value = ''

  if (previewUrl.value) {
    URL.revokeObjectURL(previewUrl.value)
    previewUrl.value = ''
  }

  if (file) {
    previewUrl.value = URL.createObjectURL(file)
  }
}

async function submitPredict() {
  if (!selectedFile.value) {
    predictError.value = '请先选择一张叶片图片'
    return
  }

  predictLoading.value = true
  predictError.value = ''

  try {
    predictResult.value = await predictImage(selectedFile.value)
    await loadHistory()
  } catch (err) {
    predictResult.value = null
    predictError.value = err instanceof Error ? err.message : '识别失败'
  } finally {
    predictLoading.value = false
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
    if (selectedHistory.value) {
      const current = historyRecords.value.find((record) => record.id === selectedHistory.value.id)
      if (current) selectedHistory.value = { ...selectedHistory.value, ...current }
    }
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

function buildChatContext() {
  if (!predictResult.value) return ''
  return [
    `最近识别病害：${predictResult.value.disease_name}`,
    `风险等级：${predictResult.value.risk_level}`,
    `摘要：${predictResult.value.summary}`,
    predictResult.value.suggestions?.length ? `建议：${predictResult.value.suggestions.join('；')}` : '',
  ]
    .filter(Boolean)
    .join('\n')
}

async function submitChat() {
  const question = chatQuestion.value.trim()
  if (!question || chatLoading.value) return

  chatMessages.value.push({ role: 'user', text: question })
  chatQuestion.value = ''
  chatLoading.value = true
  chatError.value = ''

  try {
    const result = await askAssistant({
      question,
      context: buildChatContext(),
    })
    chatMessages.value.push({
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

onMounted(async () => {
  checkBackend()
  await restoreSession()
  await loadHistory()
})
</script>

<template>
  <main class="shell">
    <section class="hero">
      <div class="hero-copy">
        <p class="eyebrow">API 驱动基线 v0.3.0</p>
        <h1>薯安智检</h1>
        <p class="summary">
          新系统不再使用本地 CNN。图片识别由平台后端配置的 Vision LLM API 完成，防治建议和问答由 Text LLM API 完成。
        </p>
      </div>
      <div class="status-panel">
        <span class="status-dot" :class="{ online: health?.ok }"></span>
        <div>
          <p class="status-label">API 状态</p>
          <strong>{{ serviceState }}</strong>
          <button type="button" @click="checkBackend" :disabled="healthLoading">
            {{ healthLoading ? '检测中...' : '重新检测' }}
          </button>
        </div>
      </div>
    </section>

    <section class="workbench">
      <article class="panel auth-panel">
        <p class="panel-k">用户身份</p>
        <template v-if="currentUser">
          <h2>{{ currentUser.username }}</h2>
          <p>当前历史记录会优先显示该用户的识别记录。退出后将回到全局演示视图。</p>
          <button type="button" class="ghost-button" @click="logout">退出登录</button>
        </template>
        <template v-else>
          <div class="auth-tabs" aria-label="认证方式">
            <button
              type="button"
              :class="{ active: authMode === 'login' }"
              @click="switchAuthMode('login')"
            >
              登录
            </button>
            <button
              type="button"
              :class="{ active: authMode === 'register' }"
              @click="switchAuthMode('register')"
            >
              注册
            </button>
          </div>
          <h2>{{ authTitle }}</h2>
          <form class="auth-form" @submit.prevent="submitAuth">
            <label>
              <span>用户名</span>
              <input v-model="authUsername" autocomplete="username" placeholder="tester" required />
            </label>
            <label>
              <span>密码</span>
              <input
                v-model="authPassword"
                type="password"
                :autocomplete="authMode === 'login' ? 'current-password' : 'new-password'"
                placeholder="至少 8 位"
                required
              />
            </label>
            <button type="submit" :disabled="authLoading">
              {{ authLoading ? '处理中...' : authTitle }}
            </button>
          </form>
          <p v-if="authError" class="error-text">{{ authError }}</p>
        </template>
      </article>

      <article class="panel uploader">
        <p class="panel-k">视觉模型识别</p>
        <h2>上传叶片图片</h2>
        <label class="drop-zone">
          <input type="file" accept="image/*" @change="onFileChange" />
          <span>{{ selectedFile?.name || '选择 JPG、PNG 或 WebP 图片' }}</span>
        </label>
        <img v-if="previewUrl" class="preview" :src="previewUrl" alt="待识别叶片" />
        <button type="button" @click="submitPredict" :disabled="predictLoading || !selectedFile">
          {{ predictLoading ? '识别中...' : '调用 Vision LLM 识别' }}
        </button>
        <p v-if="predictError" class="error-text">{{ predictError }}</p>
      </article>

      <article class="panel result-panel">
        <p class="panel-k">识别结果</p>
        <template v-if="predictResult">
          <h2>{{ predictResult.disease_name }}</h2>
          <div class="metric">
            <span>风险等级</span>
            <strong>{{ predictResult.risk_level }}</strong>
          </div>
          <p>{{ predictResult.summary }}</p>
          <div v-if="predictResult.confidence_percent !== null" class="prob-row">
            <span>模型置信度</span>
            <strong>{{ predictResult.confidence_percent }}%</strong>
          </div>
          <div class="prob-list">
            <div v-for="item in predictResult.suggestions" :key="item" class="prob-row">
              <span>{{ item }}</span>
            </div>
          </div>
          <p class="provider-note">
            Provider：{{ predictResult.provider_name }} / {{ predictResult.model_name }}
          </p>
          <p v-if="predictResult.record_id" class="provider-note">
            记录编号：#{{ predictResult.record_id }}
          </p>
        </template>
        <template v-else>
          <h2>等待识别</h2>
          <p>
            平台后端会使用管理员配置的 Vision LLM API。未配置时，预测接口会返回明确错误，不会调用任何内置模型。
          </p>
        </template>
      </article>
    </section>

    <section class="assistant-panel">
      <div class="assistant-head">
        <div>
          <p class="panel-k">AI 助手</p>
          <h2>病害问答与防治建议</h2>
        </div>
        <span>由后端 TextProvider 提供</span>
      </div>

      <div class="assistant-body">
        <div class="chat-log" aria-label="AI 助手对话记录">
          <div v-if="!chatMessages.length" class="chat-empty">
            <p>可以询问病害判断、防治建议、观察要点或后续管理措施。</p>
          </div>
          <article
            v-for="(message, index) in chatMessages"
            :key="`${message.role}-${index}`"
            class="chat-message"
            :class="message.role"
          >
            <p>{{ message.text }}</p>
            <span v-if="message.provider">{{ message.provider }}</span>
          </article>
        </div>

        <form class="chat-form" @submit.prevent="submitChat">
          <textarea
            v-model="chatQuestion"
            rows="3"
            placeholder="例如：晚疫病和早疫病在田间如何区分？"
            :disabled="chatLoading"
          ></textarea>
          <button type="submit" :disabled="chatLoading || !chatQuestion.trim()">
            {{ chatLoading ? '生成中...' : '发送问题' }}
          </button>
        </form>
        <p v-if="chatError" class="error-text">{{ chatError }}</p>
      </div>
    </section>

    <section class="history-panel">
      <div class="history-head">
        <div>
          <p class="panel-k">识别历史</p>
          <h2>{{ currentUser ? '我的识别记录' : '最近识别记录' }}</h2>
        </div>
        <button type="button" class="ghost-button" @click="loadHistory" :disabled="historyLoading">
          {{ historyLoading ? '刷新中...' : '刷新' }}
        </button>
      </div>

      <p v-if="historyError" class="error-text">{{ historyError }}</p>

      <div v-else-if="historyRecords.length" class="history-layout">
        <div class="history-table" aria-label="识别历史记录">
          <div class="history-row history-row-head">
            <span>时间</span>
            <span>病害</span>
            <span>风险</span>
            <span>Provider</span>
            <span>模型</span>
          </div>
          <button
            v-for="record in historyRecords"
            :key="record.id"
            type="button"
            class="history-row history-row-action"
            :class="{ active: selectedHistory?.id === record.id }"
            @click="selectHistory(record)"
          >
            <span>{{ formatTime(record.created_at) }}</span>
            <strong>{{ record.disease_name }}</strong>
            <span class="risk-pill">{{ record.risk_level }}</span>
            <span>{{ record.provider_name }}</span>
            <span>{{ record.model_name }}</span>
          </button>
        </div>

        <aside class="history-detail" aria-label="历史记录详情">
          <template v-if="selectedHistory">
            <div class="detail-title-row">
              <div>
                <p class="panel-k">记录 #{{ selectedHistory.id }}</p>
                <h3>{{ selectedHistory.disease_name }}</h3>
              </div>
              <span class="risk-pill">{{ selectedHistory.risk_level }}</span>
            </div>
            <button
              type="button"
              class="danger-button"
              @click="removeSelectedHistory"
              :disabled="historyDeleteLoading"
            >
              {{ historyDeleteLoading ? '删除中...' : '删除记录' }}
            </button>

            <p v-if="historyDetailError" class="error-text">{{ historyDetailError }}</p>
            <p v-else-if="historyDetailLoading" class="muted-text">正在读取详情...</p>

            <dl class="detail-grid">
              <div>
                <dt>识别时间</dt>
                <dd>{{ formatTime(selectedHistory.created_at) }}</dd>
              </div>
              <div>
                <dt>模型置信度</dt>
                <dd>
                  {{ selectedHistory.confidence_percent !== null ? `${selectedHistory.confidence_percent}%` : '未返回' }}
                </dd>
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

            <section class="detail-block">
              <h4>摘要</h4>
              <p>{{ selectedHistory.summary }}</p>
            </section>

            <section class="detail-block">
              <h4>建议</h4>
              <ul v-if="selectedHistory.suggestions?.length" class="suggestion-list">
                <li v-for="item in selectedHistory.suggestions" :key="item">{{ item }}</li>
              </ul>
              <p v-else class="muted-text">模型未返回建议</p>
            </section>

            <section class="detail-block">
              <h4>原始模型输出</h4>
              <pre>{{ selectedHistory.raw_text || '无原始输出' }}</pre>
            </section>
          </template>
          <div v-else class="empty-detail">
            <p>点击一条记录查看完整信息</p>
          </div>
        </aside>
      </div>

      <div v-if="!historyError && historyTotal" class="history-pager">
        <button type="button" class="ghost-button" @click="goHistoryPage(-1)" :disabled="!canPrevHistory || historyLoading">
          上一页
        </button>
        <span>第 {{ historyPage }} / {{ historyPageCount }} 页，共 {{ historyTotal }} 条</span>
        <button type="button" class="ghost-button" @click="goHistoryPage(1)" :disabled="!canNextHistory || historyLoading">
          下一页
        </button>
      </div>

      <div v-else-if="!historyError" class="empty-history">
        <p>{{ historyLoading ? '正在读取历史记录...' : '暂无识别记录' }}</p>
      </div>
    </section>
  </main>
</template>
