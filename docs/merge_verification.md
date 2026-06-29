# 分支合并验证指南

## 🚀 快速验证（5 分钟）

### 1. 验证分支状态

```bash
# 确认当前分支
git branch -a

# 应该看到：
# * develop（当前分支）
#   main
#   remotes/origin/develop
#   remotes/origin/main
#   remotes/origin/phase-2（已合并，可选删除）
```

### 2. 验证合并提交

```bash
# 查看合并日志
git log develop --oneline -5

# 应该看到顶部是合并提交：
# 9aa1113 merge: 合并 phase-2 分支到 develop
# 230a1e5 feat: 完成第二阶段任务 - 组员C和组员D任务
# ...
```

### 3. 验证文件结构

```bash
# 检查后端模块
ls -d backend/app/modules/*/

# 应该包含 8 个模块：
# admin/  ai/  auth/  community/  interaction/  news/  profile/  user/

# 检查前端 API
ls frontend/src/api/*.ts

# 应该包含 9 个 API 文件：
# admin.ts  ai.ts  auth.ts  community.ts  http.ts  interaction.ts  news.ts  profile.ts  request.ts

# 检查 AI 服务
ls ai-service/app/services/*.py

# 应该包含最新的 LLM 相关文件：
# llm_client.py  llm_parser.py  prompt_builder.py  generate_service.py  ...
```

---

## 📋 详细验证（15 分钟）

### 1. 安装依赖

```bash
# 前端
cd frontend
npm install

# 后端
cd ../backend
pip install -r requirements.txt

# AI 服务
cd ../ai-service
pip install -r requirements.txt
cp .env.example .env
```

### 2. 启动服务

```bash
# Terminal 1: Backend
cd backend
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

# Terminal 2: AI Service
cd ai-service
uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload

# Terminal 3: Frontend
cd frontend
npm run dev
```

### 3. 访问应用

打开浏览器访问：
- **前端主页**：http://localhost:5173
- **AI 生成页**：http://localhost:5173/ai/title-summary
- **后端 API 文档**：http://127.0.0.1:8000/docs

### 4. 测试各模块

#### AI 标题摘要生成（develop 提供）

```
✓ 访问 /ai/title-summary
✓ 输入新闻正文
✓ 选择参数（标题数、摘要风格等）
✓ 点击生成
✓ 验证返回结果（标题、摘要、关键词等）
✓ 检查生成历史
```

**预期**：快速返回结果（<200ms，使用 Mock 模式）或 2-5 秒（LLM 模式）

#### 管理后台（phase-2 提供）

```
✓ 导航到管理后台
✓ 检查管理员功能
✓ 验证权限控制
```

#### 社区互动（phase-2 提供）

```
✓ 导航到社区页面
✓ 检查互动功能
✓ 验证评论和讨论
```

#### 用户资料（phase-2 提供）

```
✓ 进入个人中心
✓ 检查资料编辑功能
✓ 验证个人信息显示
```

---

## ✅ 完整性检查清单

### 后端模块（backend/app/modules/）

- ✅ `admin/` - 管理功能
- ✅ `ai/` - AI 标题摘要生成
- ✅ `auth/` - 认证管理
- ✅ `community/` - 社区互动
- ✅ `interaction/` - 用户交互
- ✅ `news/` - 新闻管理
- ✅ `profile/` - 用户资料
- ✅ `user/` - 用户管理

### 前端 API（frontend/src/api/）

- ✅ `admin.ts` - 管理接口（新增）
- ✅ `ai.ts` - AI 生成接口
- ✅ `auth.ts` - 认证接口
- ✅ `community.ts` - 社区接口（新增）
- ✅ `http.ts` - HTTP 工具
- ✅ `interaction.ts` - 交互接口
- ✅ `news.ts` - 新闻接口
- ✅ `profile.ts` - 用户资料接口（新增）
- ✅ `request.ts` - 请求配置

### AI 服务（ai-service/app/services/）

- ✅ `chat_service.py` - 聊天服务
- ✅ `check_service.py` - 检查服务
- ✅ `extract_service.py` - 抽取服务
- ✅ `generate_service.py` - 生成服务（含 LLM）
- ✅ `llm_client.py` - LLM 客户端（新增）
- ✅ `llm_parser.py` - LLM 解析（新增）
- ✅ `prompt_builder.py` - Prompt 构造（新增）

### 前端视图（frontend/src/views/）

- ✅ `ai-generate/` - AI 生成页面
- ✅ `home/` - 首页
- ✅ `news-detail/` - 新闻详情
- ✅ `admin/` - 管理后台（来自 phase-2）
- ✅ `community/` - 社区页面（来自 phase-2）
- ✅ `profile/` - 个人中心（来自 phase-2）

---

## 🔍 冲突解决验证

### 确认冲突已全部解决

```bash
# 查看合并状态
git status

# 应该显示：
# On branch develop
# nothing to commit, working tree clean
```

### 确认新增文件已包含

```bash
# 检查来自 phase-2 的新 API 文件
ls -la frontend/src/api/{admin,community,profile}.ts

# 所有文件应该存在且有内容
```

### 确认开发分支逻辑已保留

```bash
# 检查 AI 模块的最新功能
grep -l "llm_client" ai-service/app/services/*.py
# 应该返回：generate_service.py

# 检查超时配置
grep "timeout" frontend/src/api/ai.ts
# 应该看到 60000ms 配置
```

---

## 📊 合并统计

```bash
# 查看合并前后的统计
git diff origin/develop...develop --stat | tail -5

# 应该显示合并增加了新文件和更新
```

---

## 🚀 推送到远程

### 更新远程分支

```bash
# 推送更新后的 develop
git push origin develop

# 验证推送成功
git log origin/develop --oneline -2
```

### 可选：清理远程 phase-2 分支

```bash
# 删除远程 phase-2 分支（如果不再需要）
git push origin --delete phase-2

# 删除本地远程跟踪分支
git remote prune origin
```

---

## ⚠️ 问题排查

### 问题 1：某个模块功能不工作

**检查清单**：
1. 确认后端服务已启动（:8000）
2. 确认 ai-service 已启动（:8001）
3. 确认前端已编译（:5173）
4. 检查 API 是否正确调用
5. 查看浏览器 Network 和后端日志

### 问题 2：AI 生成返回 Mock 而不是 LLM

**解决步骤**：
1. 检查 `ai-service/.env` 的 `LLM_ENABLED` 设置
2. 如果 `LLM_ENABLED=true`，检查 `LLM_API_KEY` 是否正确
3. 查看 ai-service 日志是否有 LLM 调用错误
4. 检查网络连接是否正常

### 问题 3：导入错误或类型错误

**解决步骤**：
1. 确认依赖已安装：`pip install -r requirements.txt`
2. 清除 Python 缓存：`find . -type d -name __pycache__ -exec rm -rf {} +`
3. 重启后端服务

### 问题 4：前端页面加载缓慢或 404

**解决步骤**：
1. 检查 npm 依赖是否完整：`npm install`
2. 清除构建缓存：`rm -rf dist node_modules/.vite`
3. 重启前端开发服务

---

## ✨ 验证成功标志

当你看到以下情况时，表明合并完全成功：

✅ **git status 显示工作区干净**
```
nothing to commit, working tree clean
```

✅ **所有 8 个后端模块都存在**
```
backend/app/modules/admin/
backend/app/modules/ai/
backend/app/modules/auth/
backend/app/modules/community/
backend/app/modules/interaction/
backend/app/modules/news/
backend/app/modules/profile/
backend/app/modules/user/
```

✅ **所有 9 个前端 API 都存在**
```
frontend/src/api/admin.ts
frontend/src/api/ai.ts
frontend/src/api/auth.ts
frontend/src/api/community.ts
frontend/src/api/http.ts
frontend/src/api/interaction.ts
frontend/src/api/news.ts
frontend/src/api/profile.ts
frontend/src/api/request.ts
```

✅ **AI 服务包含最新的 LLM 文件**
```
ai-service/app/services/llm_client.py
ai-service/app/services/llm_parser.py
ai-service/app/services/prompt_builder.py
```

✅ **所有服务启动无错误**
- 后端：http://127.0.0.1:8000 (Swagger 文档可访问)
- AI 服务：http://127.0.0.1:8001 (健康检查成功)
- 前端：http://localhost:5173 (加载成功)

✅ **AI 生成功能正常运行**
- 可以访问 /ai/title-summary
- 可以输入文本和生成结果
- 可以查看生成历史

✅ **新增模块功能可访问**
- 管理后台（如果有对应路由）
- 社区互动页面
- 用户资料页面

---

## 📞 后续支持

如遇问题，请：

1. 检查 `docs/merge_summary.md` 了解合并详情
2. 查看 `README.md` 了解配置说明
3. 查阅 `docs/stage_9_4_quick_reference.md` AI 模块参考
4. 查看各模块的 README 文件

---

**验证完成后，项目可以进行集成测试和部署！** 🚀
