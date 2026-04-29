<script setup>
import { computed, onMounted, ref } from 'vue'
import { fetchMe, getAccessToken, loginUser, registerUser, setAccessToken } from './api/auth'
import { fetchHealth } from './api/health'
import { deleteHistoryRecord, fetchHistory, fetchHistoryRecord } from './api/history'
import {
  createModelConfig,
  deleteModelConfig,
  fetchModelConfigs,
  updateModelConfig,
} from './api/modelConfigs'
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
const modelConfigs = ref([])
const modelConfigLoading = ref(false)
const modelConfigSaving = ref(false)
const modelConfigDeletingId = ref(null)
const modelConfigError = ref('')
const modelConfigMessage = ref('')
const editingModelConfigId = ref(null)
const modelConfigForm = ref(defaultModelConfigForm())

const historyPage = computed(() => Math.floor(historyOffset.value / historyLimit.value) + 1)
const historyPageCount = computed(() => Math.max(1, Math.ceil(historyTotal.value / historyLimit.value)))
const canPrevHistory = computed(() => historyOffset.value > 0)
const canNextHistory = computed(() => historyOffset.value + historyLimit.value < historyTotal.value)
const authTitle = computed(() => (authMode.value === 'login' ? '用户登录' : '用户注册'))
const visionConfigs = computed(() => modelConfigs.value.filter((config) => config.provider_type === 'vision'))
const textConfigs = computed(() => modelConfigs.value.filter((config) => config.provider_type === 'text'))
const modelConfigFormTitle = computed(() => (editingModelConfigId.value ? '编辑模型配置' : '新增模型配置'))

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
    await loadModelConfigs()
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
  modelConfigs.value = []
  resetModelConfigForm()
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

function defaultModelConfigForm() {
  return {
    provider_name: '',
    provider_type: 'vision',
    base_url: '',
    api_key: '',
    model_name: '',
    enabled: true,
  }
}

async function loadModelConfigs() {
  if (!currentUser.value) {
    modelConfigs.value = []
    return
  }

  modelConfigLoading.value = true
  modelConfigError.value = ''

  try {
    modelConfigs.value = await fetchModelConfigs()
  } catch (err) {
    modelConfigs.value = []
    modelConfigError.value = err instanceof Error ? err.message : '模型配置获取失败'
  } finally {
    modelConfigLoading.value = false
  }
}

function resetModelConfigForm() {
  editingModelConfigId.value = null
  modelConfigForm.value = defaultModelConfigForm()
  modelConfigError.value = ''
  modelConfigMessage.value = ''
}

function editModelConfig(config) {
  editingModelConfigId.value = config.id
  modelConfigForm.value = {
    provider_name: config.provider_name,
    provider_type: config.provider_type,
    base_url: config.base_url,
    api_key: '',
    model_name: config.model_name,
    enabled: config.enabled,
  }
  modelConfigError.value = ''
  modelConfigMessage.value = '编辑时如不填写 API Key，将保留原密钥。'
}

function buildModelConfigPayload() {
  return {
    provider_name: modelConfigForm.value.provider_name.trim(),
    provider_type: modelConfigForm.value.provider_type,
    base_url: modelConfigForm.value.base_url.trim().replace(/\/$/, ''),
    model_name: modelConfigForm.value.model_name.trim(),
    enabled: modelConfigForm.value.enabled,
    api_key: modelConfigForm.value.api_key.trim(),
  }
}

async function saveModelConfig() {
  if (!currentUser.value) {
    modelConfigError.value = '请先登录后再配置模型。'
    return
  }

  const payload = buildModelConfigPayload()
  if (!payload.provider_name || !payload.base_url || !payload.model_name) {
    modelConfigError.value = '请填写 provider 名称、Base URL 和模型名称。'
    return
  }
  if (!editingModelConfigId.value && !payload.api_key) {
    modelConfigError.value = '新增配置时必须填写 API Key。'
    return
  }
  if (editingModelConfigId.value && !payload.api_key) {
    delete payload.api_key
  }

  modelConfigSaving.value = true
  modelConfigError.value = ''
  modelConfigMessage.value = ''

  try {
    if (editingModelConfigId.value) {
      await updateModelConfig(editingModelConfigId.value, payload)
      resetModelConfigForm()
      modelConfigMessage.value = '模型配置已更新。'
    } else {
      await createModelConfig(payload)
      resetModelConfigForm()
      modelConfigMessage.value = '模型配置已创建。'
    }
    await loadModelConfigs()
  } catch (err) {
    modelConfigError.value = err instanceof Error ? err.message : '模型配置保存失败'
  } finally {
    modelConfigSaving.value = false
  }
}

async function toggleModelConfig(config) {
  modelConfigError.value = ''
  modelConfigMessage.value = ''

  try {
    await updateModelConfig(config.id, { enabled: !config.enabled })
    await loadModelConfigs()
    modelConfigMessage.value = config.enabled ? '模型配置已停用。' : '模型配置已启用。'
  } catch (err) {
    modelConfigError.value = err instanceof Error ? err.message : '模型配置状态更新失败'
  }
}

async function removeModelConfig(config) {
  if (!window.confirm(`确认删除 ${config.provider_name}？删除后需要重新填写 API Key。`)) return

  modelConfigDeletingId.value = config.id
  modelConfigError.value = ''
  modelConfigMessage.value = ''

  try {
    await deleteModelConfig(config.id)
    if (editingModelConfigId.value === config.id) resetModelConfigForm()
    await loadModelConfigs()
    modelConfigMessage.value = '模型配置已删除。'
  } catch (err) {
    modelConfigError.value = err instanceof Error ? err.message : '模型配置删除失败'
  } finally {
    modelConfigDeletingId.value = null
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
  await loadModelConfigs()
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
          新系统不再使用本地 CNN。图片识别由用户配置的 Vision LLM API 完成，防治建议和问答由 Text LLM API 完成。
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
            请先在后端创建并启用 `provider_type=vision` 的模型配置。未配置时，预测接口会返回明确错误，不会调用任何内置模型。
          </p>
        </template>
      </article>
    </section>

    <section class="model-config-panel">
      <div class="model-config-head">
        <div>
          <p class="panel-k">模型配置</p>
          <h2>我的 Vision / Text Provider</h2>
        </div>
        <button
          type="button"
          class="ghost-button"
          @click="loadModelConfigs"
          :disabled="modelConfigLoading || !currentUser"
        >
          {{ modelConfigLoading ? '刷新中...' : '刷新配置' }}
        </button>
      </div>

      <div v-if="!currentUser" class="model-config-locked">
        <h3>登录后维护个人模型配置</h3>
        <p>VisionProvider 和 TextProvider 已按用户隔离。登录后创建的配置只会被当前用户的识别、建议和聊天接口使用。</p>
      </div>

      <template v-else>
        <div class="model-config-layout">
          <form class="model-config-form" @submit.prevent="saveModelConfig">
            <div class="form-title-row">
              <h3>{{ modelConfigFormTitle }}</h3>
              <button
                v-if="editingModelConfigId"
                type="button"
                class="ghost-button compact-button"
                @click="resetModelConfigForm"
              >
                取消编辑
              </button>
            </div>

            <label>
              <span>Provider 类型</span>
              <select v-model="modelConfigForm.provider_type">
                <option value="vision">VisionProvider</option>
                <option value="text">TextProvider</option>
              </select>
            </label>

            <label>
              <span>Provider 名称</span>
              <input v-model="modelConfigForm.provider_name" placeholder="例如：my-vision-api" required />
            </label>

            <label>
              <span>Base URL</span>
              <input v-model="modelConfigForm.base_url" placeholder="https://example.com/v1" required />
            </label>

            <label>
              <span>模型名称</span>
              <input v-model="modelConfigForm.model_name" placeholder="例如：vision-model-name" required />
            </label>

            <label>
              <span>API Key / Token</span>
              <input
                v-model="modelConfigForm.api_key"
                type="password"
                autocomplete="off"
                :placeholder="editingModelConfigId ? '留空则保留原密钥' : '只会加密后存入后端'"
                :required="!editingModelConfigId"
              />
            </label>

            <label class="toggle-line">
              <input v-model="modelConfigForm.enabled" type="checkbox" />
              <span>启用该配置</span>
            </label>

            <button type="submit" :disabled="modelConfigSaving">
              {{ modelConfigSaving ? '保存中...' : editingModelConfigId ? '保存修改' : '创建配置' }}
            </button>

            <p v-if="modelConfigError" class="error-text">{{ modelConfigError }}</p>
            <p v-if="modelConfigMessage" class="success-text">{{ modelConfigMessage }}</p>
          </form>

          <div class="model-config-lists">
            <section class="provider-column">
              <div class="provider-column-head">
                <h3>VisionProvider</h3>
                <span>{{ visionConfigs.length }} 个</span>
              </div>
              <div v-if="visionConfigs.length" class="provider-list">
                <article v-for="config in visionConfigs" :key="config.id" class="provider-card">
                  <div class="provider-card-head">
                    <div>
                      <strong>{{ config.provider_name }}</strong>
                      <span>{{ config.model_name }}</span>
                    </div>
                    <span class="status-badge" :class="{ enabled: config.enabled }">
                      {{ config.enabled ? '已启用' : '停用' }}
                    </span>
                  </div>
                  <p>{{ config.base_url }}</p>
                  <p class="provider-note">密钥：{{ config.api_key_masked }}</p>
                  <div class="provider-actions">
                    <button type="button" class="ghost-button compact-button" @click="editModelConfig(config)">
                      编辑
                    </button>
                    <button type="button" class="ghost-button compact-button" @click="toggleModelConfig(config)">
                      {{ config.enabled ? '停用' : '启用' }}
                    </button>
                    <button
                      type="button"
                      class="danger-button compact-button"
                      @click="removeModelConfig(config)"
                      :disabled="modelConfigDeletingId === config.id"
                    >
                      {{ modelConfigDeletingId === config.id ? '删除中' : '删除' }}
                    </button>
                  </div>
                </article>
              </div>
              <p v-else class="empty-provider">暂无视觉模型配置</p>
            </section>

            <section class="provider-column">
              <div class="provider-column-head">
                <h3>TextProvider</h3>
                <span>{{ textConfigs.length }} 个</span>
              </div>
              <div v-if="textConfigs.length" class="provider-list">
                <article v-for="config in textConfigs" :key="config.id" class="provider-card">
                  <div class="provider-card-head">
                    <div>
                      <strong>{{ config.provider_name }}</strong>
                      <span>{{ config.model_name }}</span>
                    </div>
                    <span class="status-badge" :class="{ enabled: config.enabled }">
                      {{ config.enabled ? '已启用' : '停用' }}
                    </span>
                  </div>
                  <p>{{ config.base_url }}</p>
                  <p class="provider-note">密钥：{{ config.api_key_masked }}</p>
                  <div class="provider-actions">
                    <button type="button" class="ghost-button compact-button" @click="editModelConfig(config)">
                      编辑
                    </button>
                    <button type="button" class="ghost-button compact-button" @click="toggleModelConfig(config)">
                      {{ config.enabled ? '停用' : '启用' }}
                    </button>
                    <button
                      type="button"
                      class="danger-button compact-button"
                      @click="removeModelConfig(config)"
                      :disabled="modelConfigDeletingId === config.id"
                    >
                      {{ modelConfigDeletingId === config.id ? '删除中' : '删除' }}
                    </button>
                  </div>
                </article>
              </div>
              <p v-else class="empty-provider">暂无文本模型配置</p>
            </section>
          </div>
        </div>
      </template>
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
