<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import {
  type SystemConfigItem,
  type SystemConfigListResponse,
  getSystemConfig,
  updateSystemConfig,
} from '@/api/admin'

const emit = defineEmits<{ (e: 'changed'): void }>()

const loading = ref(false)
const saving = ref(false)
const items = ref<SystemConfigItem[]>([])

const formData = reactive<Record<string, string>>({})

const TYPE_LABELS: Record<string, string> = {
  string: '文本',
  int: '整数',
  float: '小数',
  boolean: '开关',
  json: 'JSON',
}

function isBoolean(item: SystemConfigItem): boolean {
  return item.config_type === 'boolean'
}

function isNumber(item: SystemConfigItem): boolean {
  return item.config_type === 'int' || item.config_type === 'float'
}

function isJson(item: SystemConfigItem): boolean {
  return item.config_type === 'json'
}

async function loadConfig() {
  loading.value = true
  try {
    const res: SystemConfigListResponse = await getSystemConfig()
    items.value = res.items
    for (const item of res.items) {
      formData[item.config_key] = item.config_value ?? ''
    }
  } finally {
    loading.value = false
  }
}

async function saveConfig() {
  saving.value = true
  try {
    const payloadItems = items.value
      .filter(item => item.editable)
      .map(item => ({ config_key: item.config_key, config_value: formData[item.config_key] ?? '' }))
    const res = await updateSystemConfig({ items: payloadItems })
    ElMessage.success(res.message || '配置已保存')
    emit('changed')
    loadConfig()
  } finally {
    saving.value = false
  }
}

function getBooleanValue(key: string): boolean {
  const v = formData[key]
  return v === 'true' || v === 'True' || v === '1' || v === 'yes'
}

function setBooleanValue(key: string, val: boolean) {
  formData[key] = val ? 'true' : 'false'
}

function getNumberValue(key: string): number {
  return Number(formData[key]) || 0
}

function setNumberValue(key: string, val: number | string) {
  formData[key] = String(val)
}

onMounted(loadConfig)
</script>

<template>
  <div class="system-config-page">
    <div class="panel-header">
      <h3>系统配置</h3>
      <el-button type="primary" :loading="saving" @click="saveConfig">保存配置</el-button>
    </div>

    <el-card v-loading="loading">
      <el-form label-width="180px" label-position="right">
        <el-form-item
          v-for="item in items"
          :key="item.config_key"
          :label="item.config_key"
        >
          <template v-if="isBoolean(item)">
            <el-switch
              :model-value="getBooleanValue(item.config_key)"
              @update:model-value="(v: boolean) => setBooleanValue(item.config_key, v)"
              :disabled="!item.editable"
            />
          </template>
          <template v-else-if="isNumber(item)">
            <el-input-number
              :model-value="getNumberValue(item.config_key)"
              @update:model-value="(v: number | undefined) => setNumberValue(item.config_key, v ?? 0)"
              :disabled="!item.editable"
              style="width: 200px"
            />
          </template>
          <template v-else-if="isJson(item)">
            <el-input
              :model-value="formData[item.config_key]"
              @update:model-value="(v: string) => formData[item.config_key] = v"
              type="textarea"
              :rows="3"
              :disabled="!item.editable"
            />
          </template>
          <template v-else>
            <el-input
              :model-value="formData[item.config_key]"
              @update:model-value="(v: string) => formData[item.config_key] = v"
              :disabled="!item.editable"
            />
          </template>
          <div class="field-info">
            <el-tag size="small" type="info">{{ TYPE_LABELS[item.config_type] || item.config_type }}</el-tag>
            <span v-if="item.description" class="desc-text">{{ item.description }}</span>
            <el-tag v-if="!item.editable" size="small" type="warning">只读</el-tag>
          </div>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<style scoped>
.system-config-page { padding: 0 4px; }
.panel-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.panel-header h3 { margin: 0; font-size: 18px; font-weight: 600; }
.field-info { display: flex; align-items: center; gap: 8px; margin-top: 4px; }
.desc-text { color: #909399; font-size: 13px; }
</style>
