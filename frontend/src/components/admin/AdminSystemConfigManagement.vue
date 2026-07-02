<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getSystemConfig,
  updateSystemConfig,
  type SystemConfigItem,
  type SystemConfigListResponse,
} from '@/api/admin'

const emit = defineEmits<{ (e: 'changed'): void }>()

const loading = ref(false)
const saving = ref(false)
const errorMessage = ref('')
const items = ref<SystemConfigItem[]>([])
const formData = reactive<Record<string, string>>({})

const visibleItems = computed(() => items.value.filter(item => !item.config_key.startsWith('ai.')))

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
  errorMessage.value = ''
  try {
    const res: SystemConfigListResponse = await getSystemConfig()
    items.value = res.items
    for (const item of res.items) {
      formData[item.config_key] = item.config_value ?? ''
    }
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '系统配置加载失败'
    ElMessage.error(errorMessage.value)
  } finally {
    loading.value = false
  }
}

async function saveConfig() {
  try {
    await ElMessageBox.confirm('确认保存当前系统配置？该操作会立即影响后台运行参数。', '确认保存配置', {
      type: 'warning',
      confirmButtonText: '保存',
      cancelButtonText: '取消',
    })
  } catch {
    return
  }
  saving.value = true
  try {
    const payloadItems = visibleItems.value
      .filter(item => item.editable)
      .map(item => ({ config_key: item.config_key, config_value: formData[item.config_key] ?? '' }))
    const res = await updateSystemConfig({ items: payloadItems })
    ElMessage.success(res.message || '配置已保存')
    emit('changed')
    await loadConfig()
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '系统配置保存失败')
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
      <div>
        <h3>系统配置</h3>
        <p>维护非 AI 的系统级配置项，避免与 AI 配置页重复编辑同一批配置。</p>
      </div>
      <el-button type="primary" :loading="saving" @click="saveConfig">保存配置</el-button>
    </div>

    <el-card v-loading="loading">
      <el-alert v-if="errorMessage" class="config-alert" type="error" show-icon :closable="false" :title="errorMessage">
        <template #default>
          <el-button size="small" @click="loadConfig">重试</el-button>
        </template>
      </el-alert>

      <el-form label-width="180px" label-position="right">
        <el-form-item
          v-for="item in visibleItems"
          :key="item.config_key"
          :label="item.config_key"
        >
          <template v-if="isBoolean(item)">
            <el-switch
              :model-value="getBooleanValue(item.config_key)"
              :disabled="!item.editable"
              @update:model-value="(v: boolean) => setBooleanValue(item.config_key, v)"
            />
          </template>
          <template v-else-if="isNumber(item)">
            <el-input-number
              :model-value="getNumberValue(item.config_key)"
              :disabled="!item.editable"
              style="width: 200px"
              @update:model-value="(v: number | undefined) => setNumberValue(item.config_key, v ?? 0)"
            />
          </template>
          <template v-else-if="isJson(item)">
            <el-input
              :model-value="formData[item.config_key]"
              type="textarea"
              :rows="3"
              :disabled="!item.editable"
              @update:model-value="(v: string) => formData[item.config_key] = v"
            />
          </template>
          <template v-else>
            <el-input
              :model-value="formData[item.config_key]"
              :disabled="!item.editable"
              @update:model-value="(v: string) => formData[item.config_key] = v"
            />
          </template>
          <div class="field-info">
            <el-tag size="small" type="info">{{ TYPE_LABELS[item.config_type] || item.config_type }}</el-tag>
            <span v-if="item.description" class="desc-text">{{ item.description }}</span>
            <el-tag v-if="!item.editable" size="small" type="warning">只读</el-tag>
          </div>
        </el-form-item>
      </el-form>

      <el-empty v-if="!loading && visibleItems.length === 0" description="暂无可维护的系统配置" />
    </el-card>
  </div>
</template>

<style scoped>
.system-config-page { padding: 0 4px; }
.panel-header { display: flex; justify-content: space-between; align-items: flex-start; gap: 16px; margin-bottom: 16px; }
.panel-header h3 { margin: 0; font-size: 18px; font-weight: 600; }
.panel-header p { margin: 6px 0 0; color: #909399; font-size: 13px; }
.config-alert { margin-bottom: 16px; }
.field-info { display: flex; align-items: center; gap: 8px; margin-top: 4px; }
.desc-text { color: #909399; font-size: 13px; }
</style>
