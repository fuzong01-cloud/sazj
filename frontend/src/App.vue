<script setup>
import { computed, onMounted, ref } from 'vue'
import { fetchHealth } from './api/health'
import { predictImage } from './api/predict'

const health = ref(null)
const healthLoading = ref(false)
const healthError = ref('')
const selectedFile = ref(null)
const previewUrl = ref('')
const predictLoading = ref(false)
const predictError = ref('')
const predictResult = ref(null)

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
  } catch (err) {
    predictResult.value = null
    predictError.value = err instanceof Error ? err.message : '识别失败'
  } finally {
    predictLoading.value = false
  }
}

onMounted(checkBackend)
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
        </template>
        <template v-else>
          <h2>等待识别</h2>
          <p>
            请先在后端创建并启用 `provider_type=vision` 的模型配置。未配置时，预测接口会返回明确错误，不会调用任何内置模型。
          </p>
        </template>
      </article>
    </section>
  </main>
</template>
