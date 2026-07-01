<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  type AIConfigResponse,
  type AIConfigUpdateRequest,
  type AIConfigTestResult,
  type PromptTemplateItem,
  type PromptTemplatePayload,
  type PromptTemplateOptions,
  type AdminAICallRecordListResponse,
  type AdminAICallRecordQueryParams,
  getAIConfig,
  updateAIConfig,
  testAIConnection,
  getPromptTemplateOptions,
  getPromptTemplates,
  getPromptTemplateDetail,
  createPromptTemplate,
  updatePromptTemplate,
  updatePromptTemplateStatus,
  setPromptTemplateDefault,
  getAICallRecords,
} from '@/api/admin'

const emit = defineEmits<{ (e: 'changed'): void }>()

// ── tab state ────────────────────────────────────────────────────
const activeTab = ref<'aiConfig' | 'prompt' | 'risk' | 'records'>('aiConfig')

// ── AI Config state ──────────────────────────────────────────────
const aiConfig = ref<AIConfigResponse | null>(null)
const aiConfigLoading = ref(false)
const aiConfigSaving = ref(false)
const aiConfigTesting = ref(false)
const aiConfigForm = reactive({
  service_url: '',
  model_name: '',
  api_key: '',
  timeout: 60,
  max_input_length: 8000,
  enable_real_llm: false,
  enable_fallback: true,
  risk_threshold_low: 0.3,
  risk_threshold_medium: 0.7,
})

// ── Prompt Template state ────────────────────────────────────────
const promptLoading = ref(false)
const promptList = ref<PromptTemplateItem[]>([])
const promptTotal = ref(0)
const promptOptions = ref<PromptTemplateOptions | null>(null)
const promptQuery = reactive({ function_type: '', status: null as number | null, keyword: '', page: 1, page_size: 10 })

const promptEditVisible = ref(false)
const promptEditMode = ref<'create' | 'edit'>('create')
const promptEditLoading = ref(false)
const promptEditForm = reactive<PromptTemplatePayload>({
  name: '',
  function_type: '',
  prompt_content: '',
  version: 'v1',
  status: 1,
  is_default: 0,
  remark: '',
})
const promptEditId = ref<number | null>(null)

const FUNC_TYPE_LABELS: Record<string, string> = {
  title_generation: '标题生成',
  summary_generation: '摘要生成',
  keyword_extraction: '关键词提取',
  element_extraction: '要素提取',
  consistency_check: '一致性检查',
  timeline_generation: '时间线生成',
  ai_chat: 'AI 对话',
}

// ── AI Call Records state ────────────────────────────────────────
const recordsLoading = ref(false)
const recordsData = ref<AdminAICallRecordListResponse | null>(null)
const recordsQuery = reactive<AdminAICallRecordQueryParams>({
  function_type: '', status: null, risk_level: '', is_fallback: null,
  user_id: null, start_time: '', end_time: '', page: 1, page_size: 10,
})

const RISK_LEVEL_LABELS: Record<string, string> = { low: '低', medium: '中', high: '高' }
const RECORD_STATUS_LABELS: Record<number, string> = { 0: '失败', 1: '成功', 2: '处理中', 3: '待处理' }

// ── load AI Config ───────────────────────────────────────────────
async function loadAIConfig() {
  aiConfigLoading.value = true
  try {
    const cfg = await getAIConfig()
    aiConfig.value = cfg
    aiConfigForm.service_url = cfg.service_url
    aiConfigForm.model_name = cfg.model_name
    aiConfigForm.api_key = ''
    aiConfigForm.timeout = cfg.timeout
    aiConfigForm.max_input_length = cfg.max_input_length
    aiConfigForm.enable_real_llm = cfg.enable_real_llm
    aiConfigForm.enable_fallback = cfg.enable_fallback
    aiConfigForm.risk_threshold_low = cfg.risk_threshold_low
    aiConfigForm.risk_threshold_medium = cfg.risk_threshold_medium
  } finally {
    aiConfigLoading.value = false
  }
}

async function saveAIConfig() {
  aiConfigSaving.value = true
  try {
    const payload: AIConfigUpdateRequest = {
      service_url: aiConfigForm.service_url,
      model_name: aiConfigForm.model_name,
      api_key: aiConfigForm.api_key || undefined,
      timeout: aiConfigForm.timeout,
      max_input_length: aiConfigForm.max_input_length,
      enable_real_llm: aiConfigForm.enable_real_llm,
      enable_fallback: aiConfigForm.enable_fallback,
      risk_threshold_low: aiConfigForm.risk_threshold_low,
      risk_threshold_medium: aiConfigForm.risk_threshold_medium,
    }
    await updateAIConfig(payload)
    ElMessage.success('AI 配置已保存')
    loadAIConfig()
  } finally {
    aiConfigSaving.value = false
  }
}

async function testConnection() {
  aiConfigTesting.value = true
  try {
    const res: AIConfigTestResult = await testAIConnection()
    if (res.status === 'ok') {
      ElMessage.success(res.message)
    } else {
      ElMessage.warning(res.message)
    }
    if (aiConfig.value) {
      aiConfig.value.service_status = res.status
      aiConfig.value.last_check_time = new Date().toISOString()
    }
  } finally {
    aiConfigTesting.value = false
  }
}

async function resetAIConfigDefaults() {
  await ElMessageBox.confirm('确定恢复默认 AI 配置？', '提示', { type: 'warning' })
  aiConfigForm.service_url = 'http://127.0.0.1:8001'
  aiConfigForm.model_name = 'glm-4-flash'
  aiConfigForm.api_key = ''
  aiConfigForm.timeout = 60
  aiConfigForm.max_input_length = 8000
  aiConfigForm.enable_real_llm = false
  aiConfigForm.enable_fallback = true
  aiConfigForm.risk_threshold_low = 0.3
  aiConfigForm.risk_threshold_medium = 0.7
}

// ── Prompt Template ──────────────────────────────────────────────
async function loadPromptTemplates() {
  promptLoading.value = true
  try {
    const res = await getPromptTemplates({
      function_type: promptQuery.function_type || undefined,
      status: promptQuery.status,
      keyword: promptQuery.keyword || undefined,
      page: promptQuery.page,
      page_size: promptQuery.page_size,
    })
    promptList.value = res.items
    promptTotal.value = res.total
  } finally {
    promptLoading.value = false
  }
}

async function loadPromptOptions() {
  promptOptions.value = await getPromptTemplateOptions()
}

function openPromptCreate() {
  promptEditMode.value = 'create'
  promptEditId.value = null
  promptEditForm.name = ''
  promptEditForm.function_type = ''
  promptEditForm.prompt_content = ''
  promptEditForm.version = 'v1'
  promptEditForm.status = 1
  promptEditForm.is_default = 0
  promptEditForm.remark = ''
  promptEditVisible.value = true
}

async function openPromptEdit(row: PromptTemplateItem) {
  promptEditMode.value = 'edit'
  promptEditId.value = row.id
  promptEditLoading.value = true
  promptEditVisible.value = true
  try {
    const detail = await getPromptTemplateDetail(row.id)
    promptEditForm.name = detail.name
    promptEditForm.function_type = detail.function_type
    promptEditForm.prompt_content = detail.prompt_content
    promptEditForm.version = detail.version
    promptEditForm.status = detail.status
    promptEditForm.is_default = detail.is_default
    promptEditForm.remark = detail.remark
  } finally {
    promptEditLoading.value = false
  }
}

async function submitPromptEdit() {
  promptEditLoading.value = true
  try {
    if (promptEditMode.value === 'create') {
      await createPromptTemplate(promptEditForm)
      ElMessage.success('模板已创建')
    } else {
      await updatePromptTemplate(promptEditId.value!, promptEditForm)
      ElMessage.success('模板已更新')
    }
    promptEditVisible.value = false
    loadPromptTemplates()
  } finally {
    promptEditLoading.value = false
  }
}

async function togglePromptStatus(row: PromptTemplateItem) {
  const newStatus = row.status === 1 ? 0 : 1
  const label = newStatus === 1 ? '启用' : '停用'
  try {
    await ElMessageBox.confirm(`确定${label}该模板？`, '提示', { type: 'warning' })
  } catch { return }
  await updatePromptTemplateStatus(row.id, { status: newStatus })
  ElMessage.success(`模板已${label}`)
  loadPromptTemplates()
}

async function setDefaultTemplate(row: PromptTemplateItem) {
  try {
    await ElMessageBox.confirm(`确定将"${row.name}"设为默认模板？同一功能类型的其他模板将取消默认。`, '提示', { type: 'warning' })
  } catch { return }
  await setPromptTemplateDefault(row.id)
  ElMessage.success('已设为默认模板')
  loadPromptTemplates()
}

// ── AI Call Records ──────────────────────────────────────────────
async function loadCallRecords() {
  recordsLoading.value = true
  try {
    recordsData.value = await getAICallRecords({
      function_type: recordsQuery.function_type || undefined,
      status: recordsQuery.status,
      risk_level: recordsQuery.risk_level || undefined,
      is_fallback: recordsQuery.is_fallback,
      user_id: recordsQuery.user_id,
      start_time: recordsQuery.start_time || undefined,
      end_time: recordsQuery.end_time || undefined,
      page: recordsQuery.page,
      page_size: recordsQuery.page_size,
    })
  } finally {
    recordsLoading.value = false
  }
}

// ── lifecycle ────────────────────────────────────────────────────
onMounted(() => {
  loadAIConfig()
  loadPromptOptions()
  loadPromptTemplates()
  loadCallRecords()
})

function onTabChange(tab: string) {
  if (tab === 'aiConfig' && !aiConfig.value) loadAIConfig()
  else if (tab === 'prompt' && promptList.value.length === 0) loadPromptTemplates()
  else if (tab === 'records' && !recordsData.value) loadCallRecords()
}

const aiConfigStatusText = computed(() => {
  if (!aiConfig.value?.service_status) return '未检测'
  return aiConfig.value.service_status === 'ok' ? '正常' : '异常'
})
const aiConfigStatusType = computed(() => {
  if (!aiConfig.value?.service_status) return 'info'
  return aiConfig.value.service_status === 'ok' ? 'success' : 'danger'
})
</script>

<template>
  <div class="ai-config-page">
    <div class="panel-header">
      <h3>AI 模型与规则</h3>
    </div>

    <el-tabs v-model="activeTab" @tab-change="onTabChange">
      <!-- Tab 1: AI 模型配置 -->
      <el-tab-pane label="模型配置" name="aiConfig">
        <el-row :gutter="24" v-loading="aiConfigLoading">
          <el-col :span="16">
            <el-form label-width="140px" label-position="right">
              <el-form-item label="AI 服务地址">
                <el-input v-model="aiConfigForm.service_url" placeholder="http://127.0.0.1:8001" />
              </el-form-item>
              <el-form-item label="模型名称">
                <el-input v-model="aiConfigForm.model_name" placeholder="glm-4-flash" />
              </el-form-item>
              <el-form-item label="API Key">
                <el-input v-model="aiConfigForm.api_key" type="password" show-password placeholder="留空则不修改" />
                <span v-if="aiConfig?.api_key_configured" class="hint-text">已配置</span>
              </el-form-item>
              <el-form-item label="超时时间(秒)">
                <el-input-number v-model="aiConfigForm.timeout" :min="5" :max="600" />
              </el-form-item>
              <el-form-item label="最大输入长度">
                <el-input-number v-model="aiConfigForm.max_input_length" :min="100" :max="100000" :step="100" />
              </el-form-item>
              <el-form-item label="启用真实 LLM">
                <el-switch v-model="aiConfigForm.enable_real_llm" />
              </el-form-item>
              <el-form-item label="启用规则兜底">
                <el-switch v-model="aiConfigForm.enable_fallback" />
              </el-form-item>
              <el-form-item label="启用结果缓存">
                <el-switch :model-value="false" disabled />
                <span class="hint-text">暂不支持</span>
              </el-form-item>
              <el-form-item label="低风险阈值">
                <el-input-number v-model="aiConfigForm.risk_threshold_low" :min="0" :max="1" :step="0.1" :precision="2" />
              </el-form-item>
              <el-form-item label="中风险阈值">
                <el-input-number v-model="aiConfigForm.risk_threshold_medium" :min="0" :max="1" :step="0.1" :precision="2" />
              </el-form-item>
              <el-form-item>
                <el-button type="primary" :loading="aiConfigSaving" @click="saveAIConfig">保存配置</el-button>
                <el-button :loading="aiConfigTesting" @click="testConnection">测试连接</el-button>
                <el-button @click="resetAIConfigDefaults">恢复默认</el-button>
              </el-form-item>
            </el-form>
          </el-col>
          <el-col :span="8">
            <el-card header="服务状态">
              <el-descriptions :column="1" border size="small">
                <el-descriptions-item label="连接状态">
                  <el-tag :type="aiConfigStatusType">{{ aiConfigStatusText }}</el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="API Key">
                  <el-tag :type="aiConfig?.api_key_configured ? 'success' : 'info'">
                    {{ aiConfig?.api_key_configured ? '已配置' : '未配置' }}
                  </el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="缓存支持">
                  <el-tag type="info">不支持</el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="最后检测">
                  <span v-if="aiConfig?.last_check_time">{{ aiConfig.last_check_time }}</span>
                  <span v-else class="hint-text">未检测</span>
                </el-descriptions-item>
              </el-descriptions>
            </el-card>
          </el-col>
        </el-row>
      </el-tab-pane>

      <!-- Tab 2: Prompt 模板 -->
      <el-tab-pane label="Prompt 模板" name="prompt">
        <div class="filter-row">
          <el-select v-model="promptQuery.function_type" placeholder="功能类型" clearable style="width: 160px" @change="promptQuery.page=1;loadPromptTemplates()">
            <el-option v-for="ft in promptOptions?.function_types || []" :key="ft.value" :label="ft.label" :value="ft.value" />
          </el-select>
          <el-select v-model="promptQuery.status" placeholder="状态" clearable style="width: 110px" @change="promptQuery.page=1;loadPromptTemplates()">
            <el-option label="启用" :value="1" />
            <el-option label="停用" :value="0" />
          </el-select>
          <el-input v-model="promptQuery.keyword" placeholder="搜索名称/备注" clearable style="width: 200px" @keyup.enter="promptQuery.page=1;loadPromptTemplates()" />
          <el-button type="primary" @click="promptQuery.page=1;loadPromptTemplates()">查询</el-button>
          <el-button type="success" @click="openPromptCreate">新增模板</el-button>
        </div>

        <el-table v-loading="promptLoading" :data="promptList" border>
          <el-table-column prop="id" label="ID" width="60" />
          <el-table-column prop="name" label="模板名称" min-width="160" show-overflow-tooltip />
          <el-table-column label="功能类型" width="130">
            <template #default="scope">
              {{ FUNC_TYPE_LABELS[scope.row.function_type] || scope.row.function_type }}
            </template>
          </el-table-column>
          <el-table-column prop="version" label="版本" width="80" />
          <el-table-column label="状态" width="90">
            <template #default="scope">
              <el-tag :type="scope.row.status === 1 ? 'success' : 'info'" size="small">
                {{ scope.row.status === 1 ? '启用' : '停用' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="默认" width="80">
            <template #default="scope">
              <el-tag v-if="scope.row.is_default" type="warning" size="small">默认</el-tag>
              <span v-else class="hint-text">--</span>
            </template>
          </el-table-column>
          <el-table-column prop="updated_at" label="更新时间" width="170" />
          <el-table-column label="操作" width="280" fixed="right">
            <template #default="scope">
              <el-button link type="primary" size="small" @click="openPromptEdit(scope.row)">编辑</el-button>
              <el-button link :type="scope.row.status === 1 ? 'warning' : 'success'" size="small" @click="togglePromptStatus(scope.row)">
                {{ scope.row.status === 1 ? '停用' : '启用' }}
              </el-button>
              <el-button link type="warning" size="small" @click="setDefaultTemplate(scope.row)" v-if="!scope.row.is_default">设为默认</el-button>
            </template>
          </el-table-column>
        </el-table>

        <el-pagination
          v-if="promptTotal > promptQuery.page_size"
          layout="total, prev, pager, next"
          :total="promptTotal"
          :page-size="promptQuery.page_size"
          v-model:current-page="promptQuery.page"
          @current-change="loadPromptTemplates"
          class="mt16"
        />

        <!-- Prompt Edit Dialog -->
        <el-dialog
          v-model="promptEditVisible"
          :title="promptEditMode === 'create' ? '新增 Prompt 模板' : '编辑 Prompt 模板'"
          width="680px"
          :close-on-click-modal="false"
        >
          <el-form label-width="100px" v-loading="promptEditLoading">
            <el-form-item label="模板名称" required>
              <el-input v-model="promptEditForm.name" placeholder="输入模板名称" />
            </el-form-item>
            <el-form-item label="功能类型" required>
              <el-select v-model="promptEditForm.function_type" placeholder="选择功能类型" style="width:100%">
                <el-option v-for="ft in promptOptions?.function_types || []" :key="ft.value" :label="ft.label" :value="ft.value" />
              </el-select>
            </el-form-item>
            <el-form-item label="Prompt 内容" required>
              <el-input v-model="promptEditForm.prompt_content" type="textarea" :rows="8" placeholder="输入 Prompt 模板内容" />
            </el-form-item>
            <el-form-item label="版本号">
              <el-input v-model="promptEditForm.version" placeholder="v1" />
            </el-form-item>
            <el-form-item label="状态">
              <el-switch v-model="promptEditForm.status" :active-value="1" :inactive-value="0" active-text="启用" inactive-text="停用" />
            </el-form-item>
            <el-form-item label="设为默认">
              <el-switch v-model="promptEditForm.is_default" :active-value="1" :inactive-value="0" active-text="是" inactive-text="否" />
            </el-form-item>
            <el-form-item label="备注">
              <el-input v-model="promptEditForm.remark" placeholder="备注说明" />
            </el-form-item>
          </el-form>
          <template #footer>
            <el-button @click="promptEditVisible = false">取消</el-button>
            <el-button type="primary" :loading="promptEditLoading" @click="submitPromptEdit">保存</el-button>
          </template>
        </el-dialog>
      </el-tab-pane>

      <!-- Tab 3: 风险规则 -->
      <el-tab-pane label="风险规则" name="risk">
        <el-row :gutter="20" v-loading="aiConfigLoading">
          <el-col :span="12">
            <el-card header="敏感词规则">
              <div v-if="aiConfig?.sensitive_words?.length">
                <el-tag v-for="(word, i) in aiConfig.sensitive_words" :key="i" class="mr8 mb8" type="danger">{{ word }}</el-tag>
              </div>
              <el-empty v-else description="未配置敏感词" :image-size="80" />
            </el-card>
          </el-col>
          <el-col :span="12">
            <el-card header="风险等级阈值">
              <el-descriptions :column="1" border size="small">
                <el-descriptions-item label="低风险阈值">&le; {{ aiConfig?.risk_threshold_low ?? '--' }}</el-descriptions-item>
                <el-descriptions-item label="中风险阈值">&le; {{ aiConfig?.risk_threshold_medium ?? '--' }}</el-descriptions-item>
                <el-descriptions-item label="高风险范围">&gt; {{ aiConfig?.risk_threshold_medium ?? '--' }}</el-descriptions-item>
              </el-descriptions>
            </el-card>
          </el-col>
          <el-col :span="12" style="margin-top: 20px">
            <el-card header="降级策略">
              <div v-if="aiConfig?.fallback_strategy && Object.keys(aiConfig.fallback_strategy).length">
                <pre class="json-view">{{ JSON.stringify(aiConfig.fallback_strategy, null, 2) }}</pre>
              </div>
              <el-empty v-else description="未配置降级策略" :image-size="80" />
            </el-card>
          </el-col>
          <el-col :span="12" style="margin-top: 20px">
            <el-card header="风险规则配置">
              <div v-if="aiConfig?.risk_rules?.length">
                <pre class="json-view">{{ JSON.stringify(aiConfig.risk_rules, null, 2) }}</pre>
              </div>
              <el-empty v-else description="未配置风险规则" :image-size="80" />
            </el-card>
          </el-col>
        </el-row>
      </el-tab-pane>

      <!-- Tab 4: AI 调用记录 -->
      <el-tab-pane label="AI 调用记录" name="records">
        <div class="filter-row">
          <el-select v-model="recordsQuery.function_type" placeholder="功能类型" clearable style="width: 150px" @change="recordsQuery.page=1;loadCallRecords()">
            <el-option v-for="ft in promptOptions?.function_types || []" :key="ft.value" :label="ft.label" :value="ft.value" />
          </el-select>
          <el-select v-model="recordsQuery.status" placeholder="状态" clearable style="width: 110px" @change="recordsQuery.page=1;loadCallRecords()">
            <el-option label="成功" :value="1" />
            <el-option label="失败" :value="0" />
            <el-option label="处理中" :value="2" />
            <el-option label="待处理" :value="3" />
          </el-select>
          <el-select v-model="recordsQuery.risk_level" placeholder="风险等级" clearable style="width: 110px" @change="recordsQuery.page=1;loadCallRecords()">
            <el-option label="低" value="low" />
            <el-option label="中" value="medium" />
            <el-option label="高" value="high" />
          </el-select>
          <el-select v-model="recordsQuery.is_fallback" placeholder="兜底标记" clearable style="width: 110px" @change="recordsQuery.page=1;loadCallRecords()">
            <el-option label="兜底" :value="true" />
            <el-option label="正常" :value="false" />
          </el-select>
          <el-date-picker v-model="recordsQuery.start_time" type="date" placeholder="开始日期" value-format="YYYY-MM-DD" style="width: 140px" />
          <el-date-picker v-model="recordsQuery.end_time" type="date" placeholder="截止日期" value-format="YYYY-MM-DD" style="width: 140px" />
          <el-button type="primary" @click="recordsQuery.page=1;loadCallRecords()">查询</el-button>
        </div>

        <!-- summary cards -->
        <div class="summary-grid" v-if="recordsData?.summary">
          <div class="summary-card"><span class="sc-label">总调用</span><span class="sc-value">{{ recordsData.summary.total_count }}</span></div>
          <div class="summary-card"><span class="sc-label">今日调用</span><span class="sc-value">{{ recordsData.summary.today_count }}</span></div>
          <div class="summary-card"><span class="sc-label">兜底次数</span><span class="sc-value">{{ recordsData.summary.fallback_count }}</span></div>
        </div>

        <el-table v-loading="recordsLoading" :data="recordsData?.items || []" border>
          <el-table-column prop="id" label="ID" width="70" />
          <el-table-column prop="username" label="用户" width="120" show-overflow-tooltip />
          <el-table-column label="功能类型" width="130">
            <template #default="scope">
              {{ FUNC_TYPE_LABELS[scope.row.function_type] || scope.row.function_type }}
            </template>
          </el-table-column>
          <el-table-column prop="input_length" label="输入长度" width="90" />
          <el-table-column label="状态" width="90">
            <template #default="scope">
              <el-tag :type="scope.row.status === 1 ? 'success' : 'danger'" size="small">
                {{ RECORD_STATUS_LABELS[scope.row.status] || '未知' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="风险等级" width="90">
            <template #default="scope">
              <el-tag v-if="scope.row.risk_level" :type="scope.row.risk_level === 'high' ? 'danger' : scope.row.risk_level === 'medium' ? 'warning' : 'success'" size="small">
                {{ RISK_LEVEL_LABELS[scope.row.risk_level] || scope.row.risk_level }}
              </el-tag>
              <span v-else class="hint-text">--</span>
            </template>
          </el-table-column>
          <el-table-column label="兜底" width="70">
            <template #default="scope">
              <el-tag v-if="scope.row.is_fallback" type="warning" size="small">是</el-tag>
              <span v-else class="hint-text">--</span>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="时间" width="170" />
        </el-table>

        <el-pagination
          v-if="recordsData && recordsData.total > (recordsQuery.page_size || 10)"
          layout="total, prev, pager, next"
          :total="recordsData.total"
          :page-size="recordsQuery.page_size"
          v-model:current-page="recordsQuery.page"
          @current-change="loadCallRecords"
          class="mt16"
        />
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<style scoped>
.ai-config-page { padding: 0 4px; }
.panel-header { margin-bottom: 16px; }
.panel-header h3 { margin: 0; font-size: 18px; font-weight: 600; }
.filter-row { display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 16px; align-items: center; }
.summary-grid { display: flex; gap: 16px; margin-bottom: 16px; flex-wrap: wrap; }
.summary-card { background: #f5f7fa; border-radius: 6px; padding: 14px 20px; min-width: 120px; display: flex; flex-direction: column; align-items: center; gap: 4px; }
.sc-label { font-size: 13px; color: #909399; }
.sc-value { font-size: 24px; font-weight: 600; color: #303133; }
.hint-text { color: #909399; font-size: 13px; margin-left: 8px; }
.mt16 { margin-top: 16px; }
.mr8 { margin-right: 8px; }
.mb8 { margin-bottom: 8px; }
.json-view { background: #f5f7fa; padding: 12px; border-radius: 4px; font-size: 13px; max-height: 300px; overflow-y: auto; white-space: pre-wrap; word-break: break-all; }
</style>
