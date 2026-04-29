<script setup>
import { computed, onMounted, ref } from 'vue'
import { fetchHealth } from './api/health'

const health = ref(null)
const loading = ref(false)
const error = ref('')

const serviceState = computed(() => {
  if (loading.value) return '检测中'
  if (health.value?.ok) return '后端已连接'
  if (error.value) return '后端未连接'
  return '等待检测'
})

async function checkBackend() {
  loading.value = true
  error.value = ''
  try {
    health.value = await fetchHealth()
  } catch (err) {
    health.value = null
    error.value = err instanceof Error ? err.message : '后端连接失败'
  } finally {
    loading.value = false
  }
}

onMounted(checkBackend)
</script>

<template>
  <main class="shell">
    <section class="hero">
      <div class="hero-copy">
        <p class="eyebrow">结构基线 v0.1.0</p>
        <h1>薯安智检</h1>
        <p class="summary">
          当前前端仅用于验证 Vue 开发入口和 FastAPI 连接状态。旧 Flask 应用仍保留在根目录，可继续独立启动。
        </p>
      </div>
      <div class="status-panel">
        <span class="status-dot" :class="{ online: health?.ok }"></span>
        <div>
          <p class="status-label">API 状态</p>
          <strong>{{ serviceState }}</strong>
        </div>
      </div>
    </section>

    <section class="grid">
      <article class="panel primary">
        <p class="panel-k">目标架构</p>
        <h2>Vue 前端 + FastAPI 后端</h2>
        <p>
          前端只负责页面和交互状态，后端只提供业务接口。后续识别、历史记录、用户系统和统计都按 API 合同逐步迁移。
        </p>
      </article>

      <article class="panel">
        <p class="panel-k">后端入口</p>
        <h2>{{ health?.app || '薯安智检 API' }}</h2>
        <p v-if="health?.timestamp">最近响应：{{ new Date(health.timestamp).toLocaleString() }}</p>
        <p v-else-if="error">{{ error }}</p>
        <p v-else>等待健康检查结果。</p>
        <button type="button" @click="checkBackend" :disabled="loading">
          {{ loading ? '检测中...' : '重新检测' }}
        </button>
      </article>

      <article class="panel">
        <p class="panel-k">迁移原则</p>
        <h2>小步替换，旧版可跑</h2>
        <p>
          本阶段不复制旧 Flask 页面，也不移动模型文件。所有新功能先进入新目录，验证通过后再替换旧路径。
        </p>
      </article>
    </section>
  </main>
</template>
