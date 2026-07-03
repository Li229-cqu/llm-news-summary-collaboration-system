# STEP 1 组件拆分变更报告

## 一、组件结构说明

### 原有结构
```
AIGenerateView.vue
├── AIInputPanel.vue       (输入面板)
├── AIParamPanel.vue       (参数面板)
├── AIResultPanel.vue      (结果面板)
└── AIGenerateHistory.vue  (历史记录)
```

### 重构后结构
```
AIGenerateView.vue          (布局容器)
├── LeftControlPanel.vue    (左侧参数控制面板)
├── MainWorkspace.vue       (中间主工作区)
│   ├── AIInputPanel.vue    (输入面板 - 内部引用)
│   ├── AIResultPanel.vue   (结果面板 - 内部引用)
│   └── AIGenerateHistory.vue (历史记录 - 内部引用)
└── HistoryPanel.vue        (占位组件，未实际使用)
```

### 组件职责划分

| 组件 | 职责 | 状态 |
|------|------|------|
| `AIGenerateView.vue` | 布局容器，负责整体布局和业务逻辑协调 | 修改 |
| `LeftControlPanel.vue` | 左侧参数控制面板，展示所有参数选项 | 新增 |
| `MainWorkspace.vue` | 中间主工作区，包含输入、操作按钮、结果展示 | 新增 |
| `HistoryPanel.vue` | 历史组件占位文件 | 新增 |
| `AIResultPanel.vue` | 生成结果展示，保持原有实现 | 未修改 |
| `AIParamPanel.vue` | 旧参数面板组件 | 未修改（保留兼容） |
| `AIInputPanel.vue` | 输入面板组件 | 未修改（被 MainWorkspace 引用） |
| `AIGenerateHistory.vue` | 历史记录组件 | 未修改（被 MainWorkspace 引用） |

---

## 二、Props 设计

### LeftControlPanel.vue

| Prop | 类型 | 必填 | 说明 |
|------|------|------|------|
| `params` | `Params` | 是 | 参数配置对象 |

**Params 接口定义：**
```typescript
interface Params {
  title_count: number
  summary_type: 'extract' | 'generate'
  title_style: string
  summary_style: string
  summary_length: 'short' | 'long' | 'both'
}
```

### MainWorkspace.vue

| Prop | 类型 | 必填 | 说明 |
|------|------|------|------|
| `loading` | `boolean` | 是 | 生成加载状态 |

---

## 三、Emits 设计

### LeftControlPanel.vue

| Event | 参数 | 说明 |
|-------|------|------|
| `update:params` | `(key: keyof Params, value: any)` | 参数变更事件 |
| `reset` | 无 | 重置参数事件 |

### MainWorkspace.vue

| Event | 参数 | 说明 |
|-------|------|------|
| `generate` | 无 | 触发生成事件 |
| `clear` | 无 | 清空内容事件 |
| `load-sample` | 无 | 加载示例事件 |

### 组件通信流程

```
用户操作              LeftControlPanel           AIGenerateView              MainWorkspace
    │                       │                          │                          │
    ├─修改参数────────────→│ emit('update:params')    │ handleParamUpdate()       │
    │                       │─────────────────────────→│                          │
    │                       │                          │ aiDraft.setParams()       │
    │                       │                          │                          │
    ├─重置参数────────────→│ emit('reset')            │ handleResetParams()       │
    │                       │─────────────────────────→│                          │
    │                       │                          │ aiDraft.resetParams()     │
    │                       │                          │                          │
    ├─点击生成─────────────────────────────────────────│                          │ emit('generate')
    │                                                  │←─────────────────────────│
    │                                                  │ handleGenerate()          │
    │                                                  │ 调用 API                  │
    │                                                  │ 更新 store                │
    │                                                  │                          │
    ├─点击清空─────────────────────────────────────────│                          │ emit('clear')
    │                                                  │←─────────────────────────│
    │                                                  │ handleClear()             │
    │                                                  │                          │
    └─加载示例─────────────────────────────────────────│                          │ emit('load-sample')
                                                       │←─────────────────────────│
                                                       │ handleLoadSample()        │
```

---

## 四、新增/修改文件列表

### 新增文件

| 文件路径 | 说明 |
|----------|------|
| `frontend/src/components/ai/LeftControlPanel.vue` | 左侧参数控制面板组件 |
| `frontend/src/components/ai/MainWorkspace.vue` | 中间主工作区组件 |
| `frontend/src/components/ai/HistoryPanel.vue` | 历史组件占位文件 |
| `CHANGE_REPORT_STEP1.md` | 变更报告文档 |

### 修改文件

| 文件路径 | 修改内容 |
|----------|----------|
| `frontend/src/views/ai-generate/AIGenerateView.vue` | 重构为布局容器，引入新组件，保留业务逻辑 |

### 未修改文件

| 文件路径 | 说明 |
|----------|------|
| `frontend/src/components/ai/AIParamPanel.vue` | 旧参数面板，保留兼容 |
| `frontend/src/components/ai/AIInputPanel.vue` | 输入面板，被 MainWorkspace 内部引用 |
| `frontend/src/components/ai/AIResultPanel.vue` | 结果面板，保持原有实现 |
| `frontend/src/components/ai/AIGenerateHistory.vue` | 历史记录组件，被 MainWorkspace 内部引用 |
| `frontend/src/api/ai.ts` | API 接口封装，未修改 |
| `frontend/src/stores/aiDraft.ts` | Pinia store，未修改 |
| `backend/app/modules/ai/*` | 后端接口，未修改 |

---

## 五、关键实现细节

### 5.1 AIGenerateView.vue 布局变更

**主要变化：**
- 移除直接引用 `AIInputPanel`、`AIParamPanel`、`AIResultPanel`、`AIGenerateHistory`
- 改为引用 `LeftControlPanel` 和 `MainWorkspace` 两个组件
- 业务逻辑（API 调用、store 操作）保留在 AIGenerateView.vue 中
- 通过 props/emits 实现组件间通信

**布局模板：**
```vue
<main class="ai-generate-container">
  <header class="page-header">...</header>
  <div class="main-content">
    <aside class="sidebar">
      <LeftControlPanel :params="aiDraft.params" @update:params="handleParamUpdate" @reset="handleResetParams" />
    </aside>
    <MainWorkspace ref="mainWorkspaceRef" :loading="aiDraft.loading" @generate="handleGenerate" @clear="handleClear" @load-sample="handleLoadSample" />
  </div>
</main>
```

### 5.2 LeftControlPanel.vue 参数通信

- 通过 `props.params` 接收当前参数状态
- 参数变更通过 `emit('update:params', key, value)` 通知父组件
- 重置操作通过 `emit('reset')` 通知父组件
- 内部保持与原 AIParamPanel.vue 相同的 UI 和交互逻辑

### 5.3 MainWorkspace.vue 事件转发

- 接收 `loading` prop 控制生成按钮状态
- 点击事件通过 emit 转发给父组件处理：
  - `@click="handleGenerate"` → `emit('generate')`
  - `@click="handleClear"` → `emit('clear')`
  - `@click="handleLoadSample"` → `emit('load-sample')`
- 内部引用原有组件：`AIInputPanel`、`AIResultPanel`、`AIGenerateHistory`
- 通过 `defineExpose` 暴露 `refreshHistory` 方法供父组件调用

---

## 六、约束确认

### 6.1 未修改内容

✅ 业务逻辑（API 调用、store 操作）保持不变  
✅ 接口调用（`generateTitleSummary`）保持不变  
✅ Pinia store（`useAIDraftStore`）保持不变  
✅ 数据结构（params、result）保持不变  
✅ UI 样式保持不变  
✅ 交互行为保持不变  

### 6.2 仅做组件拆分

✅ 只创建了新组件文件，未修改业务逻辑  
✅ 通过 props/emits 完成组件通信  
✅ 未新增任何业务逻辑  
✅ 未优化 UI  
✅ 未修改交互行为  

---

## 七、下一步建议

本步骤完成后，`AIGenerateView.vue` 已成为纯粹的布局容器，业务逻辑集中在顶层。后续可基于此结构进行：

1. **历史组件替换**：将 `MainWorkspace.vue` 中的 `AIGenerateHistory` 替换为 `HistoryPanel`
2. **参数面板独立**：`LeftControlPanel` 可进一步抽取为独立模块
3. **状态管理优化**：考虑将部分状态提升到组合式函数中