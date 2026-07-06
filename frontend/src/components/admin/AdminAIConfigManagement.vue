<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  createPromptTemplate,
  getAICallRecords,
  getAIConfig,
  getPromptTemplateDetail,
  getPromptTemplateOptions,
  getPromptTemplates,
  setPromptTemplateDefault,
  testAIConnection,
  updateAIConfig,
  updatePromptTemplate,
  updatePromptTemplateStatus,
  type AdminAICallRecordListResponse,
  type AdminAICallRecordQueryParams,
  type AIConfigResponse,
  type AIConfigTestResult,
  type AIConfigUpdateRequest,
  type PromptTemplateItem,
  type PromptTemplateOptions,
  type PromptTemplatePayload,
} from '@/api/admin'

const emit = defineEmits<{ (e: 'changed'): void }>()

const activeTab = ref<'aiConfig' | 'prompt' | 'records' | 'risk'>('aiConfig')

const aiConfig = ref<AIConfigResponse | null>(null)
const aiConfigLoading = ref(false)
const aiConfigSaving = ref(false)
const aiConfigTesting = ref(false)
const aiConfigForm = reactive({
  service_url: '',
  model_name: '',
  timeout: 60,
  max_input_length: 8000,
  enable_real_llm: false,
  enable_fallback: true,
  risk_threshold_low: 0.3,
  risk_threshold_medium: 0.7,
})

const promptLoading = ref(false)
const promptList = ref<PromptTemplateItem[]>([])
const promptTotal = ref(0)
const promptOptions = ref<PromptTemplateOptions | null>(null)
const promptQuery = reactive({ function_type: '', status: null as number | null, keyword: '', page: 1, page_size: 10 })
const promptEditVisible = ref(false)
const promptEditMode = ref<'create' | 'edit'>('create')
const promptEditLoading = ref(false)
const promptEditId = ref<number | null>(null)
const promptEditForm = reactive<PromptTemplatePayload>({
  name: '',
  function_type: '',
  prompt_content: '',
  version: 'v1',
  status: 1,
  is_default: 0,
  remark: '',
})

const recordsLoading = ref(false)
const recordsData = ref<AdminAICallRecordListResponse | null>(null)
const recordsQuery = reactive<AdminAICallRecordQueryParams>({
  function_type: '',
  status: null,
  risk_level: '',
  is_fallback: null,
  user_id: null,
  start_time: '',
  end_time: '',
  page: 1,
  page_size: 10,
})

const FUNC_TYPE_LABELS: Record<string, string> = {
  title_generation: '标题生成',
  summary_generation: '摘要生成',
  keyword_extraction: '关键词提取',
  element_extraction: '要素提取',
  consistency_check: '一致性检查',
  timeline_generation: 'Timeline 生成',
  ai_chat: 'AI 对话',
}
const RISK_LEVEL_LABELS: Record<string, string> = { low: '高质量', medium: '中质量', high: '低质量' }
const RECORD_STATUS_LABELS: Record<number, string> = { 0: '失败', 1: '成功', 2: '处理中', 3: '待处理' }

async function loadAIConfig() {
  aiConfigLoading.value = true
  try {
    const cfg = await getAIConfig()
    aiConfig.value = cfg
    aiConfigForm.service_url = cfg.service_url
    aiConfigForm.model_name = cfg.model_name
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
  try {
    await ElMessageBox.confirm('确认保存当前 AI 配置？模型地址、开关和阈值变更会影响后续 AI 生成。', '确认保存 AI 配置', {
      type: 'warning',
      confirmButtonText: '保存',
      cancelButtonText: '取消',
    })
  } catch {
    return
  }
  aiConfigSaving.value = true
  try {
    const payload: AIConfigUpdateRequest = {
      service_url: aiConfigForm.service_url,
      model_name: aiConfigForm.model_name,
      timeout: aiConfigForm.timeout,
      max_input_length: aiConfigForm.max_input_length,
      enable_real_llm: aiConfigForm.enable_real_llm,
      enable_fallback: aiConfigForm.enable_fallback,
      risk_threshold_low: aiConfigForm.risk_threshold_low,
      risk_threshold_medium: aiConfigForm.risk_threshold_medium,
    }
    await updateAIConfig(payload)
    ElMessage.success('AI 配置已保存')
    emit('changed')
    await loadAIConfig()
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : 'AI 配置保存失败')
  } finally {
    aiConfigSaving.value = false
  }
}

async function testConnection() {
  aiConfigTesting.value = true
  try {
    const res: AIConfigTestResult = await testAIConnection()
    if (res.status === 'ok') ElMessage.success(res.message)
    else ElMessage.warning(res.message)
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
  Object.assign(aiConfigForm, {
    service_url: 'http://127.0.0.1:8001',
    model_name: 'glm-4-flash',
    timeout: 60,
    max_input_length: 8000,
    enable_real_llm: false,
    enable_fallback: true,
    risk_threshold_low: 0.3,
    risk_threshold_medium: 0.7,
  })
}

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
  Object.assign(promptEditForm, { name: '', function_type: '', prompt_content: '', version: 'v1', status: 1, is_default: 0, remark: '' })
  promptEditVisible.value = true
}

async function openPromptEdit(row: PromptTemplateItem) {
  promptEditMode.value = 'edit'
  promptEditId.value = row.id
  promptEditLoading.value = true
  promptEditVisible.value = true
  try {
    const detail = await getPromptTemplateDetail(row.id)
    Object.assign(promptEditForm, {
      name: detail.name,
      function_type: detail.function_type,
      prompt_content: detail.prompt_content,
      version: detail.version,
      status: detail.status,
      is_default: detail.is_default,
      remark: detail.remark,
    })
  } finally {
    promptEditLoading.value = false
  }
}

async function submitPromptEdit() {
  promptEditLoading.value = true
  try {
    if (promptEditMode.value === 'create') await createPromptTemplate(promptEditForm)
    else await updatePromptTemplate(promptEditId.value!, promptEditForm)
    ElMessage.success('Prompt 模板已保存')
    promptEditVisible.value = false
    await loadPromptTemplates()
    emit('changed')
  } finally {
    promptEditLoading.value = false
  }
}

async function togglePromptStatus(row: PromptTemplateItem) {
  const newStatus = row.status === 1 ? 0 : 1
  const label = newStatus === 1 ? '启用' : '停用'
  try {
    await ElMessageBox.confirm(`确定${label}该模板？`, '提示', { type: 'warning' })
  } catch {
    return
  }
  await updatePromptTemplateStatus(row.id, { status: newStatus })
  ElMessage.success(`模板已${label}`)
  await loadPromptTemplates()
}

async function setDefaultTemplate(row: PromptTemplateItem) {
  try {
    await ElMessageBox.confirm(`确定将“${row.name}”设为默认模板？同一功能类型的其他模板会取消默认。`, '提示', { type: 'warning' })
  } catch {
    return
  }
  await setPromptTemplateDefault(row.id)
  ElMessage.success('已设为默认模板')
  await loadPromptTemplates()
}

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

function onTabChange(tab: string) {
  if (tab === 'aiConfig' && !aiConfig.value) void loadAIConfig()
  else if (tab === 'prompt' && promptList.value.length === 0) void loadPromptTemplates()
  else if (tab === 'records' && !recordsData.value) void loadCallRecords()
}

const aiConfigStatusText = computed(() => {
  if (!aiConfig.value?.service_status) return '未检测'
  return aiConfig.value.service_status === 'ok' ? '正常' : '异常'
})
const aiConfigStatusType = computed(() => {
  if (!aiConfig.value?.service_status) return 'info'
  return aiConfig.value.service_status === 'ok' ? 'success' : 'danger'
})

onMounted(() => {
  void loadAIConfig()
  void loadPromptOptions()
  void loadPromptTemplates()
  void loadCallRecords()
})
</script>

<template>
  <div class="ai-config-page">
    <div class="panel-header">
      <div>
        <h3>AI 配置与记录</h3>
        <p>模型配置来自 system_config 的 ai.* 项，Prompt 模板来自 ai_prompt_template，生成记录来自 ai_generate_record。</p>
      </div>
    </div>

    <el-tabs v-model="activeTab" @tab-change="onTabChange">
      <el-tab-pane label="AI 模型配置" name="aiConfig">
        <el-alert class="section-alert" type="info" show-icon :closable="false" title="本区只维护 system_config 中的 ai.* 配置。系统配置页不再重复编辑这些配置。" />
        <el-row :gutter="24" v-loading="aiConfigLoading">
          <el-col :span="16">
            <el-form label-width="140px" label-position="right">
              <el-form-item label="AI 服务地址"><el-input v-model="aiConfigForm.service_url" placeholder="http://127.0.0.1:8001" /></el-form-item>
              <el-form-item label="模型名称"><el-input v-model="aiConfigForm.model_name" placeholder="glm-4-flash" /></el-form-item>
              <el-form-item label="API Key">
                <el-tag :type="aiConfig?.api_key_configured ? 'success' : 'info'">{{ aiConfig?.api_key_configured ? '已配置于 ai-service/.env' : '未配置' }}</el-tag>
              </el-form-item>
              <el-form-item label="超时时间(秒)"><el-input-number v-model="aiConfigForm.timeout" :min="5" :max="600" /></el-form-item>
              <el-form-item label="最大输入长度"><el-input-number v-model="aiConfigForm.max_input_length" :min="100" :max="100000" :step="100" /></el-form-item>
              <el-form-item label="启用真实 LLM"><el-switch v-model="aiConfigForm.enable_real_llm" /></el-form-item>
              <el-form-item label="启用规则兜底"><el-switch v-model="aiConfigForm.enable_fallback" /></el-form-item>
              <el-form-item v-if="aiConfig?.cache_supported" label="启用结果缓存"><el-switch :model-value="false" disabled /></el-form-item>
              <el-form-item v-else label="结果缓存">
                <el-alert title="当前后端暂未接入 AI 结果缓存，缓存配置作为二期功能处理。" type="info" show-icon :closable="false" />
              </el-form-item>
              <el-form-item label="高质量阈值"><el-input-number v-model="aiConfigForm.risk_threshold_low" :min="0" :max="1" :step="0.1" :precision="2" /></el-form-item>
              <el-form-item label="中质量阈值"><el-input-number v-model="aiConfigForm.risk_threshold_medium" :min="0" :max="1" :step="0.1" :precision="2" /></el-form-item>
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
                <el-descriptions-item label="连接状态"><el-tag :type="aiConfigStatusType">{{ aiConfigStatusText }}</el-tag></el-descriptions-item>
                <el-descriptions-item label="API Key"><el-tag :type="aiConfig?.api_key_configured ? 'success' : 'info'">{{ aiConfig?.api_key_configured ? '已配置' : '未配置' }}</el-tag></el-descriptions-item>
                <el-descriptions-item label="缓存支持"><el-tag type="info">{{ aiConfig?.cache_supported ? '已接入' : '二期功能' }}</el-tag></el-descriptions-item>
                <el-descriptions-item label="最后检测"><span>{{ aiConfig?.last_check_time || '未检测' }}</span></el-descriptions-item>
              </el-descriptions>
            </el-card>
          </el-col>
        </el-row>
      </el-tab-pane>

      <el-tab-pane label="Prompt 模板配置" name="prompt">
        <el-alert class="section-alert" type="info" show-icon :closable="false" title="本区维护 ai_prompt_template 表，用于不同 AI 功能的 Prompt 模板管理。" />
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
          <el-table-column label="功能类型" width="130"><template #default="scope">{{ FUNC_TYPE_LABELS[scope.row.function_type] || scope.row.function_type }}</template></el-table-column>
          <el-table-column prop="version" label="版本" width="80" />
          <el-table-column label="状态" width="90"><template #default="scope"><el-tag :type="scope.row.status === 1 ? 'success' : 'info'" size="small">{{ scope.row.status === 1 ? '启用' : '停用' }}</el-tag></template></el-table-column>
          <el-table-column label="默认" width="80"><template #default="scope"><el-tag v-if="scope.row.is_default" type="warning" size="small">默认</el-tag><span v-else class="hint-text">--</span></template></el-table-column>
          <el-table-column prop="updated_at" label="更新时间" width="170" />
          <el-table-column label="操作" width="280" fixed="right">
            <template #default="scope">
              <el-button link type="primary" size="small" @click="openPromptEdit(scope.row)">编辑</el-button>
              <el-button link :type="scope.row.status === 1 ? 'warning' : 'success'" size="small" @click="togglePromptStatus(scope.row)">{{ scope.row.status === 1 ? '停用' : '启用' }}</el-button>
              <el-button v-if="!scope.row.is_default" link type="warning" size="small" @click="setDefaultTemplate(scope.row)">设为默认</el-button>
            </template>
          </el-table-column>
        </el-table>
        <el-pagination v-if="promptTotal > promptQuery.page_size" v-model:current-page="promptQuery.page" layout="total, prev, pager, next" :total="promptTotal" :page-size="promptQuery.page_size" class="mt16" @current-change="loadPromptTemplates" />
      </el-tab-pane>

      <el-tab-pane label="AI 生成记录" name="records">
        <el-alert class="section-alert" type="info" show-icon :closable="false" title="本区读取 ai_generate_record 表。兜底筛选仅在后端确认 ai_source 字段可用时显示。" />
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
          <el-select v-model="recordsQuery.risk_level" placeholder="质量等级" clearable style="width: 110px" @change="recordsQuery.page=1;loadCallRecords()">
            <el-option label="高" value="low" />
            <el-option label="中" value="medium" />
            <el-option label="低" value="high" />
          </el-select>
          <el-select v-if="recordsData?.fallback_supported !== false" v-model="recordsQuery.is_fallback" placeholder="兜底标记" clearable style="width: 110px" @change="recordsQuery.page=1;loadCallRecords()">
            <el-option label="兜底" :value="true" />
            <el-option label="正常" :value="false" />
          </el-select>
          <el-date-picker v-model="recordsQuery.start_time" type="date" placeholder="开始日期" value-format="YYYY-MM-DD" style="width: 140px" />
          <el-date-picker v-model="recordsQuery.end_time" type="date" placeholder="截止日期" value-format="YYYY-MM-DD" style="width: 140px" />
          <el-button type="primary" @click="recordsQuery.page=1;loadCallRecords()">查询</el-button>
        </div>
        <div v-if="recordsData?.summary" class="summary-grid">
          <div class="summary-card"><span class="sc-label">总调用</span><span class="sc-value">{{ recordsData.summary.total_count }}</span></div>
          <div class="summary-card"><span class="sc-label">今日调用</span><span class="sc-value">{{ recordsData.summary.today_count }}</span></div>
          <div class="summary-card"><span class="sc-label">兜底次数</span><span class="sc-value">{{ recordsData.summary.fallback_count }}</span></div>
        </div>
        <el-table v-loading="recordsLoading" :data="recordsData?.items || []" border>
          <el-table-column prop="id" label="ID" width="70" />
          <el-table-column prop="username" label="用户" width="120" show-overflow-tooltip />
          <el-table-column label="功能类型" width="130"><template #default="scope">{{ FUNC_TYPE_LABELS[scope.row.function_type] || scope.row.function_type }}</template></el-table-column>
          <el-table-column prop="input_length" label="输入长度" width="90" />
          <el-table-column label="状态" width="90"><template #default="scope"><el-tag :type="scope.row.status === 1 ? 'success' : 'danger'" size="small">{{ RECORD_STATUS_LABELS[scope.row.status] || '未知' }}</el-tag></template></el-table-column>
          <el-table-column label="质量等级" width="90"><template #default="scope"><el-tag v-if="scope.row.risk_level" :type="scope.row.risk_level === 'high' ? 'danger' : scope.row.risk_level === 'medium' ? 'warning' : 'success'" size="small">{{ RISK_LEVEL_LABELS[scope.row.risk_level] || scope.row.risk_level }}</el-tag><span v-else class="hint-text">--</span></template></el-table-column>
          <el-table-column label="兜底" width="70"><template #default="scope"><el-tag v-if="scope.row.is_fallback" type="warning" size="small">是</el-tag><span v-else class="hint-text">--</span></template></el-table-column>
          <el-table-column prop="created_at" label="时间" width="170" />
        </el-table>
        <el-pagination v-if="recordsData && recordsData.total > (recordsQuery.page_size || 10)" v-model:current-page="recordsQuery.page" layout="total, prev, pager, next" :total="recordsData.total" :page-size="recordsQuery.page_size" class="mt16" @current-change="loadCallRecords" />
      </el-tab-pane>

      <el-tab-pane label="质量规则" name="risk">
        <el-alert class="section-alert" type="info" show-icon :closable="false" title="本区当前为只读说明，用于查看敏感词、质量阈值、降级策略和质量规则；编辑仍通过 AI 模型配置或后端配置完成。" />
        <el-row :gutter="20" v-loading="aiConfigLoading">
          <el-col :span="12"><el-card header="敏感词规则"><el-tag v-for="(word, i) in aiConfig?.sensitive_words || []" :key="i" class="mr8 mb8" type="danger">{{ word }}</el-tag><el-empty v-if="!aiConfig?.sensitive_words?.length" description="未配置敏感词" :image-size="80" /></el-card></el-col>
          <el-col :span="12"><el-card header="质量等级阈值"><el-descriptions :column="1" border size="small"><el-descriptions-item label="高质量阈值">&le; {{ aiConfig?.risk_threshold_low ?? '--' }}</el-descriptions-item><el-descriptions-item label="中质量阈值">&le; {{ aiConfig?.risk_threshold_medium ?? '--' }}</el-descriptions-item><el-descriptions-item label="低质量范围">&gt; {{ aiConfig?.risk_threshold_medium ?? '--' }}</el-descriptions-item></el-descriptions></el-card></el-col>
          <el-col :span="12" style="margin-top: 20px"><el-card header="降级策略"><pre v-if="aiConfig?.fallback_strategy && Object.keys(aiConfig.fallback_strategy).length" class="json-view">{{ JSON.stringify(aiConfig.fallback_strategy, null, 2) }}</pre><el-empty v-else description="未配置降级策略" :image-size="80" /></el-card></el-col>
          <el-col :span="12" style="margin-top: 20px"><el-card header="质量规则配置"><pre v-if="aiConfig?.risk_rules?.length" class="json-view">{{ JSON.stringify(aiConfig.risk_rules, null, 2) }}</pre><el-empty v-else description="未配置质量规则" :image-size="80" /></el-card></el-col>
        </el-row>
      </el-tab-pane>
    </el-tabs>

    <el-dialog v-model="promptEditVisible" :title="promptEditMode === 'create' ? '新增 Prompt 模板' : '编辑 Prompt 模板'" width="680px" :close-on-click-modal="false">
      <el-form label-width="100px" v-loading="promptEditLoading">
        <el-form-item label="模板名称" required><el-input v-model="promptEditForm.name" placeholder="输入模板名称" /></el-form-item>
        <el-form-item label="功能类型" required><el-select v-model="promptEditForm.function_type" placeholder="选择功能类型" style="width:100%"><el-option v-for="ft in promptOptions?.function_types || []" :key="ft.value" :label="ft.label" :value="ft.value" /></el-select></el-form-item>
        <el-form-item label="Prompt 内容" required><el-input v-model="promptEditForm.prompt_content" type="textarea" :rows="8" placeholder="输入 Prompt 模板内容" /></el-form-item>
        <el-form-item label="版本号"><el-input v-model="promptEditForm.version" placeholder="v1" /></el-form-item>
        <el-form-item label="状态"><el-switch v-model="promptEditForm.status" :active-value="1" :inactive-value="0" active-text="启用" inactive-text="停用" /></el-form-item>
        <el-form-item label="设为默认"><el-switch v-model="promptEditForm.is_default" :active-value="1" :inactive-value="0" active-text="是" inactive-text="否" /></el-form-item>
        <el-form-item label="备注"><el-input v-model="promptEditForm.remark" placeholder="备注说明" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="promptEditVisible = false">取消</el-button><el-button type="primary" :loading="promptEditLoading" @click="submitPromptEdit">保存</el-button></template>
    </el-dialog>
  </div>
</template>

<style scoped>
.ai-config-page { padding: 0 4px; }
.panel-header { margin-bottom: 16px; }
.panel-header h3 { margin: 0; font-size: 18px; font-weight: 600; }
.panel-header p { margin: 6px 0 0; color: var(--color-text-muted); font-size: 13px; }
.section-alert { margin-bottom: 16px; }
.filter-row { display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 16px; align-items: center; }
.summary-grid { display: flex; gap: 16px; margin-bottom: 16px; flex-wrap: wrap; }
.summary-card { background: var(--color-bg); border-radius: 6px; padding: 14px 20px; min-width: 120px; display: flex; flex-direction: column; align-items: center; gap: 4px; }
.sc-label { font-size: 13px; color: var(--color-text-muted); }
.sc-value { font-size: 24px; font-weight: 600; color: var(--color-text-primary); }
.hint-text { color: var(--color-text-muted); font-size: 13px; margin-left: 8px; }
.mt16 { margin-top: 16px; }
.mr8 { margin-right: 8px; }
.mb8 { margin-bottom: 8px; }
.json-view { background: var(--color-bg); padding: 12px; border-radius: 4px; font-size: 13px; max-height: 300px; overflow-y: auto; white-space: pre-wrap; word-break: break-all; }
</style>
