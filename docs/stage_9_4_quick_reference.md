# 阶段 9.4 快速参考卡片

## 一句话总结

**修复了 LLM 调用导致的前端超时问题，前端 AI 接口 timeout 从 10s 改为 60s（仅该接口），后端从 30s 改为 60s，ai-service 建议 45s，错误提示友好。**

---

## 文件修改一览

```
frontend/src/api/request.ts
  - 添加注释 (无实质改动)

frontend/src/api/ai.ts
  - generateTitleSummary() 添加 { timeout: 60000 }

frontend/src/views/ai-generate/AIGenerateView.vue
  - catch 块增加 timeout 特殊处理

backend/app/modules/ai/service.py
  - timeout=30.0 → timeout=60.0

ai-service/.env.example (新建)
  - LLM_TIMEOUT=45
```

---

## Timeout 修改汇总

| 层级 | 修改前 | 修改后 | 配置位置 |
|-----|--------|--------|---------|
| 前端全局 | 10s | 10s | request.ts 第 20 行 |
| 前端 AI | - | 60s | ai.ts 第 42 行 |
| 后端转发 | 30s | 60s | service.py 第 21 行 |
| ai-service LLM | - | 45s | .env 第 32 行 |

---

## 如何测试

### 方式 1：快速验证（Mock）
```bash
LLM_ENABLED=false
点击生成 → <200ms 返回 ✅
```

### 方式 2：完整验证（LLM）
```bash
LLM_ENABLED=true
LLM_API_KEY=sk-你的APIKey
Network 标签监测 /api/ai/generate
点击生成 → 2-5s 等待后成功 ✅
检查日志：没有"timeout of 10000ms"错误 ✅
```

### 方式 3：验证降级
```bash
LLM_ENABLED=true
LLM_API_KEY=sk-invalid（错误）
点击生成 → 自动 fallback 到 mock ✅
仍然返回结果（不是 LLM 数据） ✅
```

---

## 关键代码段

### 前端（ai.ts）
```typescript
// AI 生成接口单独设置 60 秒 timeout
return request.post<AIGenerateResponse>(
  '/api/ai/generate',
  data,
  { timeout: 60000 }  // ← 这是新增的
)
```

### 前端（AIGenerateView.vue）
```typescript
// 特殊处理 timeout 错误
if (msg.includes('timeout') || msg.includes('60000ms')) {
  errorMessage = 'AI 生成耗时较长，请稍后重试或缩短新闻正文'
}
```

### 后端（service.py）
```python
# timeout 改为 60 秒
async with httpx.AsyncClient(timeout=60.0) as client:
    response = await client.post(endpoint, json=request.model_dump())
```

---

## ⏱️ 调用链路耗时预期

### Mock 模式
```
前端发起 → 后端转发 → ai-service 返回 mock → 前端接收
总耗时: <200ms
```

### LLM 模式（成功）
```
前端发起 → 后端转发 → ai-service 调用智谱 2-5s → 返回 → 前端接收
总耗时: 2-7s（包括网络延迟）
```

### LLM 模式（超时 fallback）
```
前端 60s timeout 内 → ai-service LLM 45s 内 → 智谱超时 → fallback mock
返回: Mock 数据
用户体验: 无感知，以为就是 LLM 返回的
```

---

## 🚀 部署步骤

1. **Pull 最新代码**
   ```bash
   git pull origin develop
   ```

2. **验证前端修改**
   ```bash
   grep -n "timeout: 60000" frontend/src/api/ai.ts
   # 应该输出：42 行左右的配置
   ```

3. **验证后端修改**
   ```bash
   grep -n "timeout=60.0" backend/app/modules/ai/service.py
   # 应该输出：21 行左右的配置
   ```

4. **配置 ai-service**
   ```bash
   cd ai-service
   cp .env.example .env
   # 编辑 .env，填入 LLM_API_KEY
   # 可选：改 LLM_ENABLED=true 以启用实际 LLM
   ```

5. **启动服务**
   ```bash
   # Terminal 1: Backend
   cd backend
   uvicorn app.main:app --port 8000 --reload

   # Terminal 2: AI Service
   cd ai-service
   uvicorn app.main:app --port 8001 --reload

   # Terminal 3: Frontend
   cd frontend
   npm run dev
   ```

6. **测试**
   - 打开 http://localhost:5173/ai/title-summary
   - 输入新闻文本
   - 点击生成
   - 观察 Network 标签和 loading 状态
   - 应该 2-5s 后成功

---

## ❌ 常见问题排查

### 问题 1："timeout of 10000ms exceeded"
- **原因**：修改没有生效
- **解决**：检查 `ai.ts` 第 42 行是否有 `{ timeout: 60000 }`

### 问题 2：后端返回 503
- **原因**：后端 timeout 太短，ai-service 响应超过 30s
- **解决**：检查 `service.py` 是否改成 `timeout=60.0`

### 问题 3：ai-service 日志显示 timeout
- **原因**：ai-service 调用智谱时超时，但应该 fallback
- **解决**：检查 ai-service 是否有 fallback 逻辑（应该有）

### 问题 4：返回的是 Mock 而不是 LLM
- **原因**：可能 LLM 调用失败了，自动 fallback 了
- **解决**：检查 ai-service 日志看是否有 warning

---

## 📊 性能数据参考

| 操作 | 预期耗时 | 状态 |
|------|---------|------|
| Mock 生成 | <200ms | ✅ 快 |
| LLM 生成 | 2-5s | ✅ 可接受 |
| 前端超时 | 60s | ✅ 足够 |
| 后端超时 | 60s | ✅ 足够 |
| ai-service LLM | 45s | ✅ 缓冲 |

---

## 📝 注意事项

1. ✅ **只改了 AI 接口**：其他接口仍是 10s timeout
2. ✅ **保留了 fallback**：LLM 失败会自动降级到 mock
3. ✅ **没有硬编码 Key**：所有 Key 从环境变量读取
4. ✅ **错误提示友好**：用户能理解"AI 生成耗时较长"
5. ✅ **不会白屏**：所有路径都有错误处理

---

## 🎯 验收标准

- [ ] 前端 ai.ts 中 generateTitleSummary 有 `{ timeout: 60000 }`
- [ ] 后端 service.py 中 httpx timeout 改为 60.0
- [ ] ai-service .env.example 存在且包含 LLM_TIMEOUT=45
- [ ] LLM_ENABLED=false 时 mock 快速返回 <200ms
- [ ] LLM_ENABLED=true 时 LLM 调用成功，2-5s 返回
- [ ] Network 中 /api/ai/generate 不再出现"timeout of 10000ms"
- [ ] 错误时提示"AI 生成耗时较长..."
- [ ] 普通接口（新闻列表、评论等）不受影响

---

## 📚 相关文档

- 详细设计：[docs/stage_9_4_timeout_fix.md](stage_9_4_timeout_fix.md)
- 阶段 9.3：[docs/stage_9_3_summary.md](stage_9_3_summary.md)
- 项目根目录：[README.md](../README.md)

---

**阶段 9.4 完成！** 🚀

下一步：监测生产环境，收集真实用户的 LLM 调用耗时数据。
