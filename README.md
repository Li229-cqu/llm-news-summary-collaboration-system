# 基于大语言模型的智能新闻摘要与协同互动系统

## 一、项目简介

基于大语言模型的智能新闻摘要与协同互动系统是一个面向新闻浏览、AI 标题摘要生成和社区互动的前后端分离系统。

系统规划包含首页新闻浏览、新闻详情、AI 标题摘要生成、社区互动、个人中心和管理后台等模块，现已完成 **AI 标题摘要生成模块全功能实现**（包括动态 Mock 和智谱 GLM-4-Flash 真实 LLM 调用），后续将继续完善其他模块。

## 二、项目定位

系统围绕”新闻浏览—新闻详情互动—AI 生成—社区交流—个人记录管理”的闭环展开，结合新闻内容消费、智能生成能力和用户协同互动，为用户提供连贯的新闻阅读与交流体验。

## 三、技术栈规划

### 前端

- Vue 3
- Vite
- TypeScript
- Vue Router
- Pinia
- Element Plus
- Axios

### 后端

- Python
- FastAPI
- Pydantic
- Uvicorn
- 后续接入 MySQL

### AI 服务

- FastAPI
- **当前支持**：动态 Mock（快速演示）+ 智谱 GLM-4-Flash（真实 AI）
- 可配置切换两种模式，LLM 调用失败时自动 fallback 到 Mock

### 部署

- 后续使用 Nginx
- 后续可使用 Docker / Docker Compose

## 四、目录结构

```text
llm-news-summary-collaboration-system/
├── frontend/     # 前端项目
├── backend/      # 后端业务服务
├── ai-service/   # AI 模型调用服务（支持 Mock + LLM）
├── docs/         # 项目文档（包含开发阶段说明）
├── deploy/       # 部署配置
├── scripts/      # 开发脚本
└── README.md     # 项目说明
```

| 目录 | 说明 |
| --- | --- |
| `frontend` | 前端项目，负责用户界面和前端交互。 |
| `backend` | 后端业务服务，提供 API 转发和业务逻辑。 |
| `ai-service` | AI 模型调用服务，支持 Mock 和智谱 GLM-4-Flash 两种模式。 |
| `docs` | 项目文档，包含需求、设计、接口和各阶段完成说明。 |
| `deploy` | 部署配置，后续存放 Nginx、Docker 等文件。 |
| `scripts` | 开发脚本，包含测试和工具脚本。 |

## 五、开发阶段

| 阶段 | 说明 | 状态 |
| --- | --- | --- |
| 第 0 阶段 | 项目总骨架搭建 | ✅ 已完成 |
| 第 1 阶段 | 前端基础框架搭建 | ✅ 已完成 |
| 第 2 阶段 | 后端 FastAPI 基础框架搭建 | ✅ 已完成 |
| 第 3 阶段 | AI 服务框架搭建 | ✅ 已完成 |
| 第 4 阶段 | 用户与权限 Mock 搭建 | ✅ 已完成 |
| **第 5 阶段** | **AI 标题摘要生成模块** | **✅ 已完成** |
| 第 6 阶段 | 数据库接入与联调 | 待开始 |

## 六、当前阶段说明

### ✅ 第 0-5 阶段已完成

**基础框架**：项目具备完整的目录骨架、Vue 3 前端框架、FastAPI 后端框架和独立 AI 服务框架。

**AI 标题摘要生成模块**（第 5 阶段，最新完成）：
- ✅ **前端 UI**：完整的输入、参数、结果、历史管理界面
- ✅ **Mock 模式**：动态生成标题、摘要、关键词、要素、一致性检查（快速返回，<100ms）
- ✅ **LLM 模式**：接入智谱 GLM-4-Flash，真实 AI 生成（2-5s）
- ✅ **Fallback 机制**：LLM 失败自动降级到 Mock，用户无感知
- ✅ **超时处理**：分层超时配置（前端 60s、后端 60s、ai-service LLM 45s）
- ✅ **新闻详情页集成**：一键导入正文，无缝跳转
- ✅ **生成历史管理**：查看、复用、删除历史记录
- ✅ **错误处理**：友好的超时提示和错误降级

**用户权限系统**（第 4 阶段）：Mock 登录、用户状态管理、路由守卫、角色权限控制。

### 🔐 测试账号

| 角色 | 用户名 | 密码 |
| --- | --- | --- |
| 普通用户 | `user` | `123456` |
| 审核编辑 | `editor` | `123456` |
| 管理员 | `admin` | `123456` |

## 七、快速开始

### 7.1 前端启动

```bash
cd frontend
npm install
npm run dev
```

访问 [http://localhost:5173](http://localhost:5173)

### 7.2 后端启动

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

启动后可访问：
- 健康检查：[http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)
- Swagger 文档：[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### 7.3 AI 服务启动（重要 ⭐）

```bash
cd ai-service

# 第 1 步：安装依赖
pip install -r requirements.txt

# 第 2 步：配置 .env 文件
cp .env.example .env

# 第 3 步：编辑 .env（可选）
# 如果要使用真实 LLM（智谱 GLM-4-Flash）：
#   1. 注册 https://open.bigmodel.cn/
#   2. 创建 API Key
#   3. 编辑 ai-service/.env：
#      LLM_ENABLED=true
#      LLM_API_KEY=sk-你的实际APIKey
# 
# 如果只想快速测试，保持默认配置：
#   LLM_ENABLED=false （使用动态 Mock）

# 第 4 步：启动 AI 服务
uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
```

### 7.4 访问应用

启动所有三个服务后，访问：

- **前端主页**：[http://localhost:5173](http://localhost:5173)
- **AI 生成页**：[http://localhost:5173/ai/title-summary](http://localhost:5173/ai/title-summary)
- **后端 API**：[http://127.0.0.1:8000](http://127.0.0.1:8000)
- **AI 服务**：[http://127.0.0.1:8001](http://127.0.0.1:8001)

---

## 八、AI 标题摘要生成模块说明

### 功能概览

在 `/ai/title-summary` 页面，用户可以：
1. 手动输入或从新闻详情页导入正文
2. 选择参数：标题数、摘要风格、摘要类型等
3. 点击生成，获得：
   - 多个候选标题
   - 短/长摘要
   - 摘要要点
   - 关键词
   - 新闻六要素（Who/What/When/Where/Why/How）
   - 一致性评分和改进建议
4. 查看和复用生成历史

### 工作模式

#### 模式 1：动态 Mock（推荐快速测试）

```bash
# .env 配置
LLM_ENABLED=false

# 特点
✅ 快速返回（<100ms）
✅ 无需配置 API Key
✅ 基于规则生成，效果演示
✅ 自动降级目标

# 用途
演示完整功能、快速原型验证、在线演示
```

#### 模式 2：真实 LLM（智谱 GLM-4-Flash）

```bash
# .env 配置
LLM_ENABLED=true
LLM_API_KEY=sk-你的实际APIKey

# 特点
✅ 真实 AI 生成（2-5秒）
✅ 更智能的标题和摘要
✅ 真实的关键词和要素提取
✅ 失败自动 fallback 到 Mock

# 要求
1. 拥有智谱 API Key（https://open.bigmodel.cn/）
2. 网络连接正常
3. 愿意等待 2-5 秒响应时间

# 用途
生产环境、真实应用、智能体验
```

### 配置详解

**ai-service/.env 关键配置**：

```env
# 启用/禁用 LLM
LLM_ENABLED=false      # false: Mock 模式, true: LLM 模式

# 智谱 API 配置（仅 LLM_ENABLED=true 时需要）
LLM_API_KEY=sk-你的APIKey          # 从 https://open.bigmodel.cn/ 获取
LLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4/  # 官方 API 地址
LLM_MODEL=glm-4-flash              # 使用的模型

# 超时和性能配置
LLM_TIMEOUT=45                     # LLM 调用超时时间（秒）
LLM_TEMPERATURE=0.3                # 生成温度（0=确定性，1=随机性）
LLM_MAX_TOKENS=2048                # 最大输出 Token 数

# 其他配置
LLM_THINKING_TYPE=disabled         # 思维链类型
```

**前端超时配置（自动，无需修改）**：
- AI 生成接口：60 秒
- 其他接口：10 秒

**后端超时配置（自动，无需修改）**：
- AI 转发：60 秒
- 其他接口：30 秒

### 如何获取智谱 API Key

1. 访问 [https://open.bigmodel.cn/](https://open.bigmodel.cn/)
2. 注册账号
3. 创建 API Key
4. 复制 Key 值到 `ai-service/.env`：`LLM_API_KEY=sk-...`

### 故障排查

| 问题 | 原因 | 解决方案 |
| --- | --- | --- |
| “timeout of 10000ms exceeded” | 前端超时 | 检查 ai-service 是否启动且网络正常 |
| “AI 服务暂时不可用” | LLM 调用失败 | 检查 API Key 或网络，fallback 到 Mock 应该有效 |
| 生成速度慢（>10s） | 网络延迟或 LLM 繁忙 | 属正常现象，可尝试缩短输入文本 |
| 返回 Mock 而不是 LLM | LLM 调用失败自动 fallback | 检查 API Key 和网络，或使用 LLM_ENABLED=false 模式 |

---

## 九、项目文档

详细的开发文档位于 `docs/` 目录：

- `README.md` - 项目概述
- `api.md` - 接口文档
- `development_plan.md` - 开发计划
- `development_standard.md` - 开发规范
- `ai_module_guide.md` - AI 模块使用指南
- `stage_9_3_summary.md` - 阶段 9.3 完成说明（LLM 接入）
- `stage_9_4_timeout_fix.md` - 阶段 9.4 完成说明（超时修复）
- `stage_9_4_quick_reference.md` - 快速参考卡片

## 十、特别说明

### ⚠️ .env 文件处理

**重要**：`ai-service/.env` 包含敏感信息（API Key），**不会被提交到 Git**。

使用此项目时：
1. 自动生成的 `.env.example` 包含配置模板
2. 克隆项目后，复制 `.env.example` 为 `.env`
3. 编辑 `.env`，填入你的 API Key（可选，默认使用 Mock）
4. `.env` 已在 `.gitignore` 中，不会被提交

### 🔄 工作流程

```
克隆项目
    ↓
cp ai-service/.env.example ai-service/.env
    ↓
编辑 ai-service/.env（可选）
    ↓
启动前端、后端、ai-service
    ↓
访问 http://localhost:5173
    ↓
测试 AI 生成功能
```

---

## 十一、后续计划

- 第 6 阶段：数据库接入与历史持久化
- 第 7 阶段：社区互动模块
- 第 8 阶段：用户中心和内容管理
- 支持更多 LLM 服务商（OpenAI、文心一言等）
- 生成结果缓存优化
- 用户反馈和评分系统

---

## 十二、许可证

项目采用 MIT 许可证。详见 LICENSE 文件。

---

**祝你使用愉快！** 🚀

有任何问题或建议，欢迎提交 Issue。
