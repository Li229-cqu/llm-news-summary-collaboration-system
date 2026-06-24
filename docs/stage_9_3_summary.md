# 阶段 9.3：智谱 GLM-4-Flash 接入生成主流程 - 完成总结

## 📝 修改和新增的文件

### 新增文件（2 个）

1. **ai-service/app/services/prompt_builder.py**
   - 功能：为智谱 GLM 构造标题摘要生成 Prompt
   - 核心函数：`build_generate_prompt()` / `build_messages()`
   - 特点：自动参数化，支持多种风格和配置

2. **ai-service/app/services/llm_parser.py**
   - 功能：解析和修复 LLM 返回的 JSON 结果
   - 核心函数：`parse_llm_response()` 及多个修复函数
   - 特点：健壮的容错机制，确保能构造有效的 GenerateResponse

### 修改文件（1 个）

3. **ai-service/app/services/generate_service.py**
   - 变化：添加 LLM 调用主流程 + fallback 机制
   - 新增函数：`generate_mock_response()`
   - 修改函数：`generate_title_summary()`
   - 保留：所有原有的 mock 生成函数完整保留

---

## 🔄 调用链路详解

### 场景 1：LLM_ENABLED=false（使用 Mock）

```
generate_title_summary(request)
├─ 输入验证
├─ 检查 settings.llm_enabled = false
└─ 返回 generate_mock_response(request)
   ├─ _generate_dynamic_titles()
   ├─ _generate_summary_short()
   ├─ _generate_summary_long()
   ├─ _generate_summary_points()
   ├─ _extract_keywords()
   ├─ _extract_news_elements()
   └─ _check_consistency()
```

**响应时间**：<100ms（纯本地计算）

---

### 场景 2：LLM_ENABLED=true 且 API Key 正确（调用智谱）

```
generate_title_summary(request)
├─ 输入验证
├─ 检查 settings.llm_enabled = true
├─ build_messages(request)
│  └─ build_generate_prompt() → 完整 prompt 文本
├─ call_llm(messages)
│  ├─ 验证 API Key
│  ├─ 初始化 OpenAI 客户端（兼容模式）
│  ├─ client.chat.completions.create()
│  │  ├─ model: glm-4-flash
│  │  ├─ temperature: 0.3
│  │  ├─ max_tokens: 2048
│  │  └─ timeout: 30s
│  └─ 返回模型响应文本
├─ parse_llm_response(content, title_count, summary_length)
│  ├─ clean_markdown_json() - 移除 ```json 包裹
│  ├─ parse_json_safe() - 安全解析 JSON
│  ├─ repair_candidate_titles() - 确保数量正确
│  ├─ repair_summaries() - 根据 summary_length 修复
│  ├─ repair_summary_points() - 确保列表有效
│  ├─ repair_keywords() - 3-8 个关键词
│  ├─ repair_news_element() - 6 要素都有值
│  └─ repair_consistency_check() - score/risk_level 有效
└─ 返回 GenerateResponse（LLM 数据）
```

**响应时间**：2-5 秒（网络请求）

---

### 场景 3：LLM_ENABLED=true 但调用失败（自动 Fallback）

```
generate_title_summary(request)
├─ 输入验证
├─ 检查 settings.llm_enabled = true
├─ 尝试调用 LLM...
│  ❌ 以下任一情况触发 fallback：
│     - API Key 未配置
│     - 网络超时（>30s）
│     - 认证失败（401）
│     - 模型返回空内容
│     - 返回非 JSON
│     - JSON 无法修复
│     - GenerateResponse 校验失败
├─ 记录 WARNING 日志
└─ 返回 generate_mock_response(request)
```

**特点**：不会导致 500 错误，用户体验无中断

---

## 📋 Prompt 构造说明

### Prompt 内容（自动生成）

```text
你是一个专业的新闻编辑 AI。根据以下要求生成新闻标题、摘要和分析结果。

【输入新闻】
{input_text}

【生成要求】
1. 标题数量：{title_count} 个
   - 风格：{title_style}（客观新闻型/吸引点击型/简洁概括型）

2. 摘要类型：{summary_type}（抽取/生成）
   - 风格：{summary_style}（简明扼要/客观正式/通俗易懂）
   - 长度配置：{summary_length}（short/long/both）

3. 关键词提取：自动识别 3-8 个关键词
4. 新闻要素：识别 who、what、when、where、why、how
5. 一致性评估：评分 0-100，风险等级 low/medium/high

【返回格式】
只返回一个 JSON 对象，不要 markdown 包裹，不要代码块，不要任何解释文字。

{JSON 结构定义...}

【字段规则】
- candidate_titles 数量必须恰好等于 {title_count}
- risk_level 只能是 low、medium、high
- score 必须是 0-100 整数
- elements 所有字段都必须有实际内容
- summary_short/summary_long 必须根据 summary_length 决定是否为空
- 标题和摘要必须忠于原文，不要编造信息

【开始生成】
请直接返回 JSON。
```

### JSON 返回格式（固定结构）

```json
{
  "candidate_titles": ["标题1", "标题2", "标题3"],
  "summary_short": "短摘要（配置为 short/both 时有内容）",
  "summary_long": "长摘要（配置为 long/both 时有内容）",
  "summary_points": ["要点1", "要点2", "要点3"],
  "keywords": ["关键词1", "关键词2", "关键词3"],
  "elements": {
    "who": "新闻主体",
    "what": "新闻事件",
    "when": "新闻时间",
    "where": "新闻地点",
    "why": "新闻原因",
    "how": "新闻方式"
  },
  "consistency": {
    "score": 85,
    "risk_level": "low",
    "issues": ["潜在问题"],
    "suggestions": ["改进建议"]
  }
}
```

---

## 🔧 JSON 解析和修复策略

### 修复流程（llm_parser.py）

| 步骤 | 函数 | 功能 |
|------|------|------|
| 1 | `clean_markdown_json()` | 移除 ```json 和 ``` 包裹 |
| 2 | `parse_json_safe()` | 安全解析 JSON，失败返回 None |
| 3 | `repair_candidate_titles()` | 数量不足补充，过多截断到 title_count |
| 4 | `repair_summaries()` | 根据 summary_length 决定字段 |
| 5 | `repair_summary_points()` | 转列表，去重，限制数量 |
| 6 | `repair_keywords()` | 3-8 个关键词，不足补充 |
| 7 | `repair_news_element()` | 所有 6 个字段都有值 |
| 8 | `repair_consistency_check()` | score 限制 0-100，映射 risk_level |

### 具体修复规则

**标题数量修复**：
- 不足时：补充 "新闻标题 X" 样式的默认标题
- 过多时：截断到 title_count

**摘要长度修复**：
- `summary_length="short"`：summary_short 有内容，summary_long 置空
- `summary_length="long"`：summary_long 有内容，summary_short 置空
- `summary_length="both"`：两者都必须有内容，缺失则使用默认值

**风险等级映射**：
- "低风险" / "low" → "low"
- "中风险" / "中等" / "medium" → "medium"
- "高风险" / "high" → "high"

**得分修复**：
- 转换为整数（浮点数向下取整）
- 限制在 0-100 范围内
- 无法转换则使用默认值 80

---

## 🛡️ Fallback 机制详解

### 触发 Fallback 的所有场景

| 场景 | 检测点 | 日志 | 结果 |
|------|--------|------|------|
| LLM_ENABLED=false | 配置检查 | INFO | 直接返回 mock |
| API Key 未配置 | call_llm() | WARNING | Fallback 到 mock |
| 网络超时（>30s） | call_llm() | WARNING | Fallback 到 mock |
| 认证失败（401） | call_llm() | WARNING | Fallback 到 mock |
| 服务不可用（503） | call_llm() | WARNING | Fallback 到 mock |
| 返回空内容 | parse_json_safe() | WARNING | Fallback 到 mock |
| 返回非 JSON | parse_json_safe() | WARNING | Fallback 到 mock |
| JSON 格式错误 | repair_* 函数 | WARNING | Fallback 到 mock |
| 字段无法修复 | repair_* 函数 | WARNING | Fallback 到 mock |
| GenerateResponse 校验失败 | parse_llm_response() | WARNING | Fallback 到 mock |

### 关键特性

- **不会出现 500 错误**：所有异常都被捕获并 fallback
- **不会导致前端白屏**：总是返回有效的 GenerateResponse
- **用户体验无中断**：LLM 失败时自动降级，用户感知不到
- **日志完整**：每次 fallback 都记录详细警告日志

---

## 📋 本地配置步骤

### 步骤 1：创建 .env 文件

```bash
cd ai-service
cp .env.example .env
```

### 步骤 2：编辑 ai-service/.env

**选项 A：启用 LLM（推荐测试）**

```env
# 其他配置保持不变...

LLM_ENABLED=true
LLM_API_KEY=sk-你的真实智谱APIKey
# 其他配置使用默认值
```

**选项 B：禁用 LLM（使用 Mock）**

```env
LLM_ENABLED=false
# 其他配置可保持默认
```

### 步骤 3：安装依赖

```bash
cd ai-service
pip install -r requirements.txt
# 确认已安装：openai, python-dotenv, fastapi 等
```

### 步骤 4：验证配置

```bash
# 检查 .env 是否被 Git 忽略
git check-ignore ai-service/.env
# 输出：ai-service/.env（表示已被忽略，安全）
```

---

## 🧪 测试指南

### 测试 1：验证 Mock 模式（LLM_ENABLED=false）

```bash
# 修改 .env：LLM_ENABLED=false
# 启动所有服务（backend, ai-service, frontend）
# 在浏览器打开 http://localhost:5173/ai/title-summary
# 输入新闻正文，点击生成

# 预期结果：
# ✅ 快速返回（<100ms）
# ✅ 返回 Mock 数据
# ✅ ai-service 日志显示：
#    INFO: LLM 未启用，使用动态 mock 生成响应
```

### 测试 2：验证 LLM 调用（LLM_ENABLED=true 且 API Key 正确）

```bash
# 修改 .env：LLM_ENABLED=true
# 填入真实 API Key：LLM_API_KEY=sk-你的真实APIKey
# 重启 ai-service（Ctrl+C 停止，重新运行 uvicorn）
# 在浏览器输入新闻正文，点击生成

# 预期结果：
# ✅ 响应延迟 2-5 秒（正常）
# ✅ 返回 LLM 生成的标题和摘要
# ✅ ai-service 日志显示：
#    INFO: LLM 已启用，准备调用智谱 GLM
#    INFO: 智谱 LLM 调用成功
#    INFO: 智谱 GLM 调用成功，返回有效响应
```

### 测试 3：验证 Fallback（LLM_ENABLED=true 但 API Key 错误）

```bash
# 修改 .env：LLM_ENABLED=true
# 使用错误的 API Key：LLM_API_KEY=sk-invalid-123456
# 重启 ai-service
# 在浏览器输入新闻正文，点击生成

# 预期结果：
# ✅ 仍然返回有效响应（不白屏、不报错）
# ✅ 返回 Mock 数据（不是 LLM 数据）
# ✅ ai-service 日志显示：
#    WARNING: 智谱 LLM 调用失败，fallback 到 mock: APIError: 401
```

### 测试 4：验证新闻详情页集成

```bash
# 1. 打开任意新闻详情页
# 2. 点击"✨ 用 AI 生成标题和摘要"按钮
# 3. 自动跳转到 AI 页面，正文已填充
# 4. 点击生成
# 5. 应该看到结果（LLM 或 Mock，取决于配置）
```

### 测试 5：验证历史记录功能

```bash
# 1. 生成几条记录（手动输入或导入新闻）
# 2. 下拉到"生成历史"区域
# 3. 看到历史列表
# 4. 点击"复用"按钮
# 5. 输入框和参数应该自动填充
# 6. 修改后重新生成应该可行
```

---

## 📊 配置和行为对照表

| LLM_ENABLED | API Key | 网络状态 | 结果来源 | 响应时间 | 特点 |
|------------|---------|--------|--------|--------|------|
| false | 任意 | 任意 | Mock | <100ms | 快速稳定 |
| true | 有效 | 正常 | LLM | 2-5s | 实时 AI |
| true | 有效 | 超时 | Mock | <100ms | 自动降级 |
| true | 无效/空 | 任意 | Mock | <100ms | 自动降级 |

---

## ✅ 安全和兼容性验证

| 项 | 状态 | 说明 |
|----|------|------|
| 是否修改 frontend？ | ❌ 否 | 前端完全不变 |
| 是否修改 backend？ | ❌ 否 | 后端完全不变 |
| 是否修改 API 路由？ | ❌ 否 | `/ai/generate-title-summary` 不变 |
| 是否修改响应结构？ | ❌ 否 | GenerateResponse 结构不变 |
| 是否接入数据库？ | ❌ 否 | 纯 LLM，无数据库操作 |
| 是否保留 Mock？ | ✅ 是 | 完整保留，作为 fallback |
| 是否在代码中硬编码 API Key？ | ❌ 否 | 从环境变量读取 |
| 是否在日志中暴露 API Key？ | ❌ 否 | 使用 mask_api_key() 脱敏 |
| 是否会产生 500 错误？ | ❌ 否 | 所有异常都自动处理 |
| 是否会导致前端白屏？ | ❌ 否 | 总是返回有效响应 |

---

## 📚 核心函数参考

### prompt_builder.py

```python
build_generate_prompt(request: GenerateRequest) -> str
  # 自动生成完整的 prompt 文本

build_messages(request: GenerateRequest) -> list[dict]
  # 构造消息列表 [{"role": "user", "content": "..."}]
```

### llm_parser.py

```python
parse_llm_response(content, title_count, summary_length) -> GenerateResponse | None
  # 完整的解析、修复、验证流程

clean_markdown_json(content: str) -> str
  # 清理 markdown 包裹（```json ... ```）

parse_json_safe(content: str) -> dict | None
  # 安全的 JSON 解析

# 内部修复函数（自动调用）
repair_candidate_titles(data, title_count)
repair_summaries(data, summary_length)
repair_summary_points(data)
repair_keywords(data)
repair_news_element(data)
repair_consistency_check(data)
map_risk_level(value)
ensure_integer(value, default)
```

### generate_service.py

```python
generate_mock_response(request: GenerateRequest) -> GenerateResponse
  # 纯 Mock 实现（所有原有逻辑）

generate_title_summary(request: GenerateRequest) -> GenerateResponse
  # 主流程：LLM 调用 + fallback 处理
```

---

## 🎯 阶段 9.3 完成清单

- ✅ 新增 prompt_builder.py（Prompt 构造）
- ✅ 新增 llm_parser.py（JSON 解析和修复）
- ✅ 修改 generate_service.py（LLM 接入和 fallback）
- ✅ 所有 Python 文件通过语法检查
- ✅ LLM_ENABLED=false 时使用 mock（快速响应）
- ✅ LLM_ENABLED=true 时调用智谱 GLM（实时 AI）
- ✅ 所有异常都自动 fallback 到 mock（稳定可靠）
- ✅ 没有修改 frontend、backend 任何代码
- ✅ 没有修改 API 路由和响应字段
- ✅ 没有接数据库
- ✅ Mock 完全保留，作为 fallback
- ✅ API Key 不在代码中硬编码
- ✅ API Key 不在日志中暴露
- ✅ 不会导致 500 错误或前端白屏

---

**阶段 9.3 完成！** 🚀

接下来可以进行单元测试和性能监测（阶段 9.4+）。
