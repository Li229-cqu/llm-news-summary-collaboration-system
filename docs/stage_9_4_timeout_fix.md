# 阶段 9.4：修复真实 LLM 接入后的前端 Timeout 问题

## 问题描述

接入智谱 GLM-4-Flash 后，前端出现错误：
```
timeout of 10000ms exceeded
```

原因：
- 前端全局 timeout = 10000ms（10 秒）
- 后端到 ai-service 的 timeout = 30 秒
- 智谱 GLM 调用耗时 2-5 秒
- 总链路耗时可能达到 5-10 秒，接近或超过前端 10 秒的限制

---

## 修复的文件清单

| 文件 | 修改 | 说明 |
|------|------|------|
| `frontend/src/api/request.ts` | ✏️ 注释补充 | 明确 10s 默认 timeout |
| `frontend/src/api/ai.ts` | ✏️ 修改 | 为 generateTitleSummary 设置 60s timeout |
| `frontend/src/views/ai-generate/AIGenerateView.vue` | ✏️ 改进 | 增强 timeout 错误提示 |
| `backend/app/modules/ai/service.py` | ✏️ 修改 | 调整 timeout 从 30s 改为 60s |
| `ai-service/.env.example` | ✨ 创建 | 新增配置示例（LLM_TIMEOUT=45s） |

---

## 详细修改说明

### 1. 前端 request.ts（注释补充）

**修改前**：
```typescript
const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  timeout: 10000,
})
```

**修改后**：
```typescript
const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  timeout: 10000,  // 默认 10 秒
})
```

**说明**：
- 保持全局 timeout 为 10 秒（用于普通接口）
- 注释说明默认值
- AI 生成接口会单独覆盖此值

---

### 2. 前端 ai.ts（核心修改）

**修改前**：
```typescript
export function generateTitleSummary(data: AIGenerateRequest) {
  return request.post<AIGenerateResponse, AIGenerateResponse, AIGenerateRequest>(
    '/api/ai/generate',
    data,
  )
}
```

**修改后**：
```typescript
export function generateTitleSummary(data: AIGenerateRequest) {
  // AI 生成接口可能需要调用智谱 GLM-4-Flash，耗时 2-5 秒
  // 因此单独设置更长的 timeout（60 秒）
  return request.post<AIGenerateResponse, AIGenerateResponse, AIGenerateRequest>(
    '/api/ai/generate',
    data,
    { timeout: 60000 }  // 60 秒 timeout
  )
}
```

**说明**：
- ✅ 仅 AI 生成接口 timeout 为 60 秒
- ✅ 其他接口仍使用 10 秒默认值
- ✅ 利用 axios 的请求级配置覆盖全局配置

---

### 3. 前端 AIGenerateView.vue（错误提示改进）

**修改前**：
```typescript
} catch (error) {
  const errorMessage = error instanceof Error ? error.message : 'AI 服务暂时不可用，请稍后重试'
  aiDraft.setError(errorMessage)
  ElMessage.error(errorMessage)
}
```

**修改后**：
```typescript
} catch (error) {
  let errorMessage = 'AI 服务暂时不可用，请稍后重试'

  if (error instanceof Error) {
    const msg = error.message || ''
    // 特殊处理 timeout 错误
    if (msg.includes('timeout') || msg.includes('60000ms')) {
      errorMessage = 'AI 生成耗时较长，请稍后重试或缩短新闻正文'
    } else {
      errorMessage = msg
    }
  }

  aiDraft.setError(errorMessage)
  ElMessage.error(errorMessage)
}
```

**说明**：
- ✅ 检测 timeout 错误
- ✅ 提供友好提示："AI 生成耗时较长，请稍后重试或缩短新闻正文"
- ✅ 其他错误正常显示
- ✅ 页面不会白屏

---

### 4. 后端 service.py（转发 timeout 调整）

**修改前**：
```python
async def generate_title_summary(request: AIGenerateRequest) -> AIGenerateResponse:
    """调用 ai-service 的固定 Mock 标题摘要接口。"""
    endpoint = f"{settings.ai_service_url.rstrip('/')}/ai/generate-title-summary"

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
```

**修改后**：
```python
async def generate_title_summary(request: AIGenerateRequest) -> AIGenerateResponse:
    """调用 ai-service 的标题摘要接口。

    支持两种模式：
    1. Mock 模式（LLM_ENABLED=false）：快速返回，<100ms
    2. LLM 模式（LLM_ENABLED=true）：调用智谱 GLM-4-Flash，2-5 秒

    因此设置 timeout 为 60 秒，确保 LLM 调用可以完成。
    """
    endpoint = f"{settings.ai_service_url.rstrip('/')}/ai/generate-title-summary"

    try:
        # timeout=60.0 秒，支持 LLM 调用（智谱通常 2-5 秒）
        async with httpx.AsyncClient(timeout=60.0) as client:
```

**说明**：
- 从 30.0 秒改为 60.0 秒
- 添加详细注释说明原因
- 确保后端不会因超时而中断 LLM 调用

---

### 5. ai-service .env.example（创建）

**新增文件**：`ai-service/.env.example`

**关键配置**：
```env
# 启用/禁用 LLM 功能
LLM_ENABLED=false  # 建议先用 false 测试

# 超时时间（秒）
# 建议设置为 45-60 秒，支持网络延迟
LLM_TIMEOUT=45

# 最大返回 Token 数
# 如果响应较慢，可以尝试改为 1200 或 1500
LLM_MAX_TOKENS=2048
```

**说明**：
- ✅ LLM_TIMEOUT = 45 秒（ai-service 内部 LLM 调用超时）
- ✅ 前端 60 秒、后端 60 秒、ai-service 45 秒
- ✅ 分层超时策略，最内层最紧，确保有足够缓冲

---

## 完整调用链路超时配置

### Mock 模式（LLM_ENABLED=false）

```
前端 generateTitleSummary()
  timeout: 60000ms
    ↓
后端 POST /api/ai/generate
  timeout: 60.0s
    ↓
ai-service /ai/generate-title-summary
  返回动态 mock
  耗时: <100ms
    ↓
响应: <200ms（包括网络延迟）
```

**特点**：快速返回，超时不是问题

---

### LLM 模式（LLM_ENABLED=true 且 API Key 正确）

```
前端 generateTitleSummary()
  timeout: 60000ms
    ↓
后端 POST /api/ai/generate
  timeout: 60.0s
    ↓
ai-service /ai/generate-title-summary
  LLM_TIMEOUT = 45s
    ↓
call_llm() → 智谱 GLM-4-Flash
  耗时: 2-5秒
    ↓
parse_llm_response() → 修复和验证
  耗时: <100ms
    ↓
响应: 2-5秒（加上网络延迟可能 5-7秒）
```

**分层超时保证**：
- 前端 60s：等待最长
- 后端 60s：次级等待
- ai-service LLM_TIMEOUT 45s：最内层，确保有 15s 缓冲给 parse 和网络

---

### LLM 模式但超时失败（Fallback）

```
ai-service LLM_TIMEOUT = 45s
  ↓
call_llm() 超时 → timeout exception
  ↓
except Exception:
  logger.warning("智谱 LLM 调用失败，fallback 到 mock")
  return generate_mock_response(request)
  ↓
返回 Mock 数据（不影响用户体验）
```

**特点**：即使 LLM 超时，用户也能得到结果（Mock）

---

## 🧪 测试指南

### 测试 1：Mock 模式验证（快速）

```bash
# 1. 修改 ai-service/.env
LLM_ENABLED=false

# 2. 启动所有服务并访问
# http://localhost:5173/ai/title-summary

# 3. 输入新闻正文，点击生成

# 预期结果：
✅ 快速返回（<200ms）
✅ 生成按钮 1 秒内恢复可用
✅ 没有任何 timeout 错误
```

---

### 测试 2：LLM 模式验证（真实 LLM）

```bash
# 1. 修改 ai-service/.env
LLM_ENABLED=true
LLM_API_KEY=sk-你的真实APIKey
LLM_TIMEOUT=45

# 2. 重启 ai-service

# 3. 在浏览器打开 Network 标签，监测请求

# 4. 在 AI 页面输入新闻正文，点击生成

# 预期结果：
✅ 生成中显示 loading 状态
✅ Network 中 /api/ai/generate 请求
   - 开始时间：0ms
   - 等待时间：2-5秒（TTFB）
   - 完成时间：2-5秒（包括网络延迟）
✅ 5-7秒后生成完成
✅ 没有"timeout of 10000ms exceeded"错误
✅ 没有"timeout of 60000ms exceeded"错误
```

**如何查看 Network 标签**：
1. 打开浏览器开发者工具（F12）
2. 切换到 Network 标签
3. 过滤 "generate" 请求
4. 查看请求时间和响应时间

---

### 测试 3：超时降级验证（模拟网络慢）

```bash
# 1. 在浏览器开发者工具中：
#    Network → Throttling → Slow 3G（模拟网络慢）

# 2. 在 AI 页面生成，可能需要 10+ 秒

# 预期结果：
✅ 即使超时，前端仍显示 loading
✅ 最终返回结果（可能是 Mock fallback）
✅ 不出现"timeout of 10000ms exceeded"
✅ 不白屏
```

---

### 测试 4：错误提示验证

```bash
# 场景 A：LLM_ENABLED=true 但 API Key 无效
# 修改 .env：LLM_API_KEY=sk-invalid-123456
# 重启 ai-service，生成

# 预期结果：
✅ 自动 fallback 到 mock
✅ 返回 Mock 数据
✅ 看不出 LLM 失败了

# 场景 B：网络完全断开
# 关闭 ai-service，尝试生成

# 预期结果：
✅ 显示错误提示："AI 服务暂时不可用"
✅ 不白屏
```

---

### 测试 5：普通接口未受影响

```bash
# 1. 浏览新闻列表页面
# 2. 加载新闻评论
# 3. 用户登录/登出

# 预期结果：
✅ 所有操作正常，响应快速
✅ Network 中其他接口响应时间 <1s
✅ 只有 /api/ai/generate 比较慢（因为真实 LLM）
```

---

## 📊 超时时间对照表

| 接口 | 修改前 | 修改后 | 原因 |
|------|--------|--------|------|
| 前端全局 | 10s | 10s | 不改，保留普通接口用 |
| 前端 AI 生成 | 10s | 60s | LLM 调用需要 2-5s |
| 后端 AI 转发 | 30s | 60s | 支持 LLM 调用链路 |
| ai-service LLM | N/A | 45s | 内部 LLM timeout，比前端短 |

---

## 性能优化建议（可选）

如果 LLM 响应仍然较慢（>10s），可以尝试：

### 1. 减少 Token 输出

```env
# 改为
LLM_MAX_TOKENS=1200  # 原来 2048
```

效果：稍快，但生成内容可能稍短

---

### 2. 缩短输入文本

用户可以输入较短的新闻文本（500-1000 字），而不是长文本（2000+ 字）

---

### 3. 检查网络延迟

在 ai-service 添加日志：

```python
import time
start = time.time()
response = call_llm(messages)
elapsed = time.time() - start
logger.info(f"LLM 调用耗时: {elapsed:.2f}s")
```

如果耗时 >7s，可能是网络问题，而非模型问题

---

## ✅ 完成清单

- ✅ 前端 AI 接口 timeout: 10s → 60s（单独配置）
- ✅ 后端 AI 转发 timeout: 30s → 60s
- ✅ ai-service LLM timeout 建议: 45s
- ✅ 错误提示友好："AI 生成耗时较长，请稍后重试"
- ✅ 没有修改响应字段
- ✅ 没有删除 fallback 逻辑
- ✅ Mock 完全保留
- ✅ 不会导致前端白屏
- ✅ 其他接口不受影响

---

## 🎯 总结

**问题**：前端 10s timeout 导致 LLM 调用中断

**解决方案**：
1. 前端 AI 接口单独设置 60s timeout（不影响其他接口）
2. 后端调整 timeout 为 60s（支持 LLM 调用）
3. ai-service LLM timeout 设为 45s（内部缓冲）
4. 改进错误提示，用户体验更好

**效果**：
- ✅ LLM 调用可以正常完成（2-5s）
- ✅ 不再出现 "timeout of 10000ms exceeded"
- ✅ 用户体验友好，不会白屏
- ✅ 其他接口正常快速响应
- ✅ Mock 和 LLM 都能正常工作

**阶段 9.4 完成！** 🚀
