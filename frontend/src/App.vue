<script setup>
import { computed, onMounted, ref } from 'vue'
import { fetchHealth } from './api/health'
import { fetchHistory } from './api/history'
import { predictImage } from './api/predict'

const health = ref(null)
const healthLoading = ref(false)
const healthError = ref('')
const selectedFile = ref(null)
const previewUrl = ref('')
const predictLoading = ref(false)
const predictError = ref('')
const predictResult = ref(null)
const historyLoading = ref(false)
const historyError = ref('')
const historyRecords = ref([])

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

async function loadHistory() {
  historyLoading.value = true
  historyError.value = ''

  try {
    historyRecords.value = await fetchHistory(20)
  } catch (err) {
    historyRecords.value = []
    historyError.value = err instanceof Error ? err.message : '历史记录获取失败'
  } finally {
    historyLoading.value = false
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

onMounted(() => {
  checkBackend()
  loadHistory()
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

    <section class="history-panel">
      <div class="history-head">
        <div>
          <p class="panel-k">识别历史</p>
          <h2>最近识别记录</h2>
        </div>
        <button type="button" class="ghost-button" @click="loadHistory" :disabled="historyLoading">
          {{ historyLoading ? '刷新中...' : '刷新' }}
        </button>
      </div>

      <p v-if="historyError" class="error-text">{{ historyError }}</p>

      <div v-else-if="historyRecords.length" class="history-table" aria-label="识别历史记录">
        <div class="history-row history-row-head">
          <span>时间</span>
          <span>病害</span>
          <span>风险</span>
          <span>Provider</span>
          <span>模型</span>
        </div>
        <div v-for="record in historyRecords" :key="record.id" class="history-row">
          <span>{{ formatTime(record.created_at) }}</span>
          <strong>{{ record.disease_name }}</strong>
          <span class="risk-pill">{{ record.risk_level }}</span>
          <span>{{ record.provider_name }}</span>
          <span>{{ record.model_name }}</span>
        </div>
      </div>

      <div v-else class="empty-history">
        <p>{{ historyLoading ? '正在读取历史记录...' : '暂无识别记录' }}</p>
      </div>
    </section>
  </main>
</template>
