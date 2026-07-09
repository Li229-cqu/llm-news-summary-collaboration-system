# 基于大语言模型的智能新闻摘要与协同互动系统

第 38 组，组长：徐子涵

本项目是一个前后端分离的智能新闻摘要与协同互动系统，覆盖新闻浏览、新闻互动、AI 标题摘要生成、新闻编辑 Agent、社区协同、事件脉络 Timeline、个人中心、管理后台、数据分析、RSS 新闻爬虫和系统运维等功能。

## 技术栈

| 层级 | 技术 |
| --- | --- |
| 前端 | Vue 3、Vite、TypeScript、Element Plus、Pinia、Vue Router、Axios、ECharts |
| 后端 | FastAPI、Uvicorn、PyMySQL、DBUtils、python-dotenv、httpx |
| AI 服务 | FastAPI、OpenAI SDK、sentence-transformers、可配置 DeepSeek / 智谱等兼容模型 |
| 数据库 | MySQL 8.0、schema.sql、seed.sql、migrations |
| 工具脚本 | 光明网 RSS 爬虫、新华网 news.cn 爬虫、数据库迁移脚本、架构图生成脚本 |

## 项目结构

```text
llm-news-summary-collaboration-system/
├── frontend/            # 前端应用，Vue 3 + Vite
├── backend/             # 后端 API 服务，统一暴露 /api/*
├── ai-service/          # 独立 AI 能力服务，统一暴露 /ai/*
├── database/            # schema、seed、migrations、迁移执行脚本
├── scripts/             # 辅助脚本
│   └── crawlers/        # RSS 新闻爬虫
├── docs/                # 接口、架构、阶段说明文档
├── deploy/              # 部署说明
├── plan/                # 阶段计划与分工
└── README.md
```

## 功能模块

- 新闻门户：新闻分类、列表、搜索、详情、热门新闻、订阅新闻流、浏览记录。
- 新闻互动：新闻点赞、收藏、评论、回复、评论点赞、评论媒体字段。
- AI 生成：标题摘要生成、要素抽取、一致性检查、证据评估、多源冲突检测、AI 生成历史。
- 新闻编辑 Agent：文本任务运行、SSE 任务流、步骤回放、解释面板、DAG 视图、可观测性面板。
- 社区协同：发帖、帖子详情、评论/回复、点赞收藏、屏蔽用户、热门话题、AI 助手、社区 AI 会话和流式回复。
- Timeline 事件脉络：话题列表、话题新闻、事件时间线生成、自动聚类、AI 生成失败时本地规则兜底。
- 个人中心：资料、浏览历史、收藏、评论、AI 记录、订阅分类、推荐、阅读轨迹、阅读时间线、阅读热力图、周报。
- 管理后台：仪表盘、待审核中心、新闻管理、帖子管理、评论审核、热榜/话题管理、Timeline 管理、用户权限、系统配置、AI 配置、Prompt 模板、AI 调用记录、系统运维、数据分析。
- 数据采集：光明网 RSS 爬虫和新华网 news.cn 爬虫，支持增量抓取、正文解析、图片过滤、去重入库和 7 天历史测试。

## 运行前准备

需要本机已安装：

- Python 3.10+，建议 3.11。
- Node.js 18+。
- MySQL 8.0。
- Git。

建议使用 Windows PowerShell。本文命令默认在项目根目录执行，数据库账号使用本地开发默认值：

```text
数据库名：llm_news_system
数据库用户：llm_news_user
数据库密码：123456
数据库地址：127.0.0.1:3306
```

## 首次启动

### 1. 拉取代码

```powershell
git clone git@github.com:Li229-cqu/llm-news-summary-collaboration-system.git
cd llm-news-summary-collaboration-system
git checkout develop
git pull origin develop
```

已有本地仓库时：

```powershell
git checkout develop
git pull origin develop
```

### 2. 创建 MySQL 数据库和用户

用 root 登录 MySQL 后执行：

```sql
CREATE DATABASE IF NOT EXISTS llm_news_system
DEFAULT CHARACTER SET utf8mb4
DEFAULT COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS 'llm_news_user'@'localhost'
IDENTIFIED BY '123456';

GRANT ALL PRIVILEGES ON llm_news_system.* TO 'llm_news_user'@'localhost';
FLUSH PRIVILEGES;
```

### 3. 初始化数据库

全新环境建议先导入最新表结构和基础数据：

```powershell
cmd /c "mysql --default-character-set=utf8mb4 -u llm_news_user -p llm_news_system < database\schema.sql"
cmd /c "mysql --default-character-set=utf8mb4 -u llm_news_user -p llm_news_system < database\seed.sql"
```

保留旧库升级时，执行全部迁移：

```powershell
cd database
python run_migrations.py
cd ..
```

`database/run_migrations.py` 会按文件名顺序执行 `database/migrations/*.sql`，并跳过可忽略的重复字段、重复索引、重复数据等错误。

### 4. 配置环境变量

项目根目录已有 `.env.example`。开发时可以复制为 `.env`，后端会读取 `backend/.env`，AI 服务会读取 `ai-service/.env`。如果只想快速本地运行，分别创建以下文件即可。

`backend/.env`：

```env
PROJECT_NAME=基于大语言模型的智能新闻摘要与协同互动系统
API_PREFIX=/api
BACKEND_HOST=127.0.0.1
BACKEND_PORT=8000
FRONTEND_URL=http://localhost:5173
AI_SERVICE_URL=http://localhost:8001
SECRET_KEY=dev_secret_key

DB_HOST=127.0.0.1
DB_PORT=3306
DB_NAME=llm_news_system
DB_USER=llm_news_user
DB_PASSWORD=123456
```

`ai-service/.env`：

```env
PROJECT_NAME=基于大语言模型的智能新闻摘要与协同互动系统
SERVICE_NAME=ai-service
AI_API_PREFIX=/ai
AI_SERVICE_HOST=127.0.0.1
AI_SERVICE_PORT=8001
BACKEND_URL=http://localhost:8000
FRONTEND_URL=http://localhost:5173
AI_MODE=mock

SUMMARY_LLM_ENABLED=false
SUMMARY_LLM_PROVIDER=deepseek
SUMMARY_LLM_API_KEY=
SUMMARY_LLM_BASE_URL=https://api.deepseek.com/v1
SUMMARY_LLM_MODEL=deepseek-chat
SUMMARY_LLM_TIMEOUT=60
SUMMARY_LLM_TEMPERATURE=0.3
SUMMARY_LLM_MAX_TOKENS=2048

EVIDENCE_LLM_ENABLED=false
EVIDENCE_LLM_PROVIDER=zhipu
EVIDENCE_LLM_API_KEY=
EVIDENCE_LLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4/
EVIDENCE_LLM_MODEL=GLM-5.2
EVIDENCE_LLM_TIMEOUT=45
EVIDENCE_LLM_TEMPERATURE=0.1
EVIDENCE_LLM_MAX_TOKENS=4096
LLM_THINKING_TYPE=disabled
```

不要提交真实数据库密码、模型 API Key 或生产密钥。

### 5. 启动后端

打开第一个 PowerShell：

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

后端地址：

```text
http://127.0.0.1:8000
http://127.0.0.1:8000/docs
```

### 6. 启动 AI 服务

打开第二个 PowerShell：

```powershell
cd ai-service
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
```

AI 服务地址：

```text
http://127.0.0.1:8001
http://127.0.0.1:8001/docs
```

默认关闭真实大模型，使用 mock 或规则兜底结果。要启用真实模型，将对应 `SUMMARY_LLM_ENABLED` 或 `EVIDENCE_LLM_ENABLED` 改为 `true`，并填写 API Key、Base URL 和模型名。

### 7. 启动前端

打开第三个 PowerShell：

```powershell
cd frontend
npm install
npm.cmd run dev
```

前端地址：

```text
http://localhost:5173
```

如果 5173 被占用，Vite 会自动切到 5174、5175 等端口，请以终端输出为准。

## 日常启动

数据库已初始化、依赖已安装后，每次只需要分别启动三个服务：

```powershell
# 终端 1：backend
cd backend
.\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

```powershell
# 终端 2：ai-service
cd ai-service
.\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
```

```powershell
# 终端 3：frontend
cd frontend
npm.cmd run dev
```

## 常用测试账号

| 角色 | 用户名 | 密码 |
| --- | --- | --- |
| 普通用户 | `user` | `123456` |
| 审核编辑 | `editor` | `123456` |
| 管理员 | `admin` | `123456` |

## 主要访问地址

| 服务 | 地址 |
| --- | --- |
| 前端 | `http://localhost:5173` |
| 后端 | `http://127.0.0.1:8000` |
| 后端 Swagger | `http://127.0.0.1:8000/docs` |
| AI 服务 | `http://127.0.0.1:8001` |
| AI Swagger | `http://127.0.0.1:8001/docs` |
| 后端健康检查 | `http://127.0.0.1:8000/api/health` |
| AI 健康检查 | `http://127.0.0.1:8001/ai/health` |

## 前端页面

| 路径 | 说明 |
| --- | --- |
| `/home` | 首页新闻流 |
| `/news/:id` | 新闻详情 |
| `/ai-generate` | AI 新闻智能编辑 |
| `/ai/news-editor` | 新闻编辑 Agent |
| `/ai/agent-observability` | Agent 可观测性面板 |
| `/ai-generate/history` | AI 生成历史 |
| `/community` | 社区 |
| `/community/create` | 发布帖子 |
| `/community/posts/:id` | 帖子详情 |
| `/timeline` | 事件脉络列表 |
| `/timeline/:topicId` | 事件脉络详情 |
| `/profile` | 个人中心 |
| `/admin` | 管理后台，需 editor/admin |
| `/login` | 登录 |

## 后端接口概览

后端统一由前端调用，前端不直接访问数据库或 AI 服务。

| 模块 | 前缀 | 说明 |
| --- | --- | --- |
| 认证 | `/api/auth` | 登录、注册、退出、当前用户、权限检查 |
| 用户 | `/api/user` | 用户资料、修改资料、修改密码、头像上传 |
| 新闻 | `/api/news` | 分类、列表、热门、搜索、订阅、详情、浏览 |
| 互动 | `/api/news/*`、`/api/comments/*` | 新闻点赞收藏、评论、回复、评论点赞 |
| AI 网关 | `/api/ai` | AI 健康检查、文件上传、生成记录查询和删除 |
| 新闻编辑 Agent | `/api/news-editor-agent` | 任务运行、任务详情、SSE 流 |
| Agent 分析 | `/api/agent-analysis` | 回放、解释、步骤、DAG、可观测性 |
| Timeline | `/api/timeline` | 话题、话题新闻、时间线生成、自动聚类 |
| 社区 | `/api/community` | 帖子、评论、互动、热搜、AI 助手、AI 会话 |
| 个人中心 | `/api/profile` | 概览、历史、收藏、评论、AI 记录、订阅、推荐、阅读统计 |
| 管理后台 | `/api/admin` | 审核、内容、用户、热榜、配置、运维、分析 |

管理后台细分能力包括：

- 待审核中心：`/pending-items`。
- 新闻管理：`/news`、新闻审核、话题绑定、置顶/推荐占位能力。
- 帖子管理：`/posts`、帖子审核。
- 评论审核：`/comments`。
- 热榜和话题：`/rankings/*`、`/hot-topics`、`/topics`。
- Timeline 管理：`/timelines`。
- 用户权限：`/users`。
- 系统配置和 AI 配置：`/system-config`、`/ai-config`。
- Prompt 模板和 AI 调用记录：`/prompt-templates`、`/ai-call-records`。
- 运维：`/ops/status`、`/ops/database`、`/ops/backups`、`/ops/storage`、`/ops/logs`。
- 数据分析：`/analytics/overview`、`/analytics/trends`、`/analytics/top-content`、`/analytics/ai-risk`、`/analytics/review-summary`、`/analytics/content-overview`。

## AI 服务接口概览

AI 服务默认监听 `http://127.0.0.1:8001`，由 backend 统一转发或编排调用。

| 接口 | 说明 |
| --- | --- |
| `GET /ai/health` | 健康检查 |
| `POST /ai/config/reload` | 重新加载 AI 配置 |
| `POST /ai/generate-title-summary` | 标题摘要生成 |
| `POST /ai/extract-elements` | 关键词和新闻要素抽取 |
| `POST /ai/check-consistency` | 一致性校验 |
| `POST /ai/evaluate-evidence` | 证据评估 |
| `POST /ai/evaluate-multisource-evidence` | 多源证据评估 |
| `POST /ai/detect-conflicts` | 多源冲突检测 |
| `POST /ai/match-topic` | 新闻话题匹配 |
| `POST /ai/judge-timeline-fit` | 时间线适配判断 |
| `POST /ai/edit-suggestions` | 使用建议生成 |
| `POST /ai/chat` | AI 对话 |
| `POST /ai/chat/stream` | AI 流式对话 |
| `POST /ai/generate-comment` | 评论生成 |
| `POST /ai/comment-summary` | 评论总结 |
| `POST /ai/profile-weekly-report` | 个人阅读周报 |
| `POST /ai/generate-timeline` | 事件时间线生成 |
| `POST /ai/polish-timeline-topic` | Timeline 话题润色 |
| `POST /ai/task/create`、`GET /ai/task/{task_id}` | AI 任务管理 |

## 数据库和迁移

全新环境优先导入：

```powershell
cmd /c "mysql --default-character-set=utf8mb4 -u llm_news_user -p llm_news_system < database\schema.sql"
cmd /c "mysql --default-character-set=utf8mb4 -u llm_news_user -p llm_news_system < database\seed.sql"
```

旧库升级执行：

```powershell
cd database
python run_migrations.py
```

当前迁移覆盖新闻来源、AI 生成记录、社区标签、订阅、全文索引、编辑字段、热榜状态、评论媒体字段、浏览历史目标字段、个人周报缓存、系统配置、Prompt 模板、操作日志、备份记录、社区 AI 会话、证据与风险字段、事件表、Agent 表、多模型配置和敏感配置清理等。

验证核心表是否有数据：

```powershell
cmd /c "mysql --default-character-set=utf8mb4 -u llm_news_user -p llm_news_system -e ""SELECT COUNT(*) AS user_count FROM user; SELECT COUNT(*) AS news_count FROM news; SELECT COUNT(*) AS post_count FROM community_post; SELECT COUNT(*) AS comment_count FROM post_comment;"""
```

## 新闻爬虫

爬虫脚本位于：

```text
scripts/crawlers/rss_news_crawler.py          # 光明网 RSS 爬虫
scripts/crawlers/news_cn_crawler.py           # 新华网 news.cn 频道页爬虫
scripts/crawlers/gmw_7days_test_crawler.py    # 光明网 7 天历史测试爬虫
```

当前主要抓取两个新闻网站：

| 网站 | 脚本 | 抓取方式 | 覆盖频道 |
| --- | --- | --- | --- |
| 光明网 `gmw.cn` | `rss_news_crawler.py` | RSS 源 + 详情页正文解析 | 时政、国际、财经、社会、文化/娱乐、科技、体育 |
| 新华网 `news.cn` | `news_cn_crawler.py` | 频道首页提取文章链接 + 详情页正文解析 | 时政、国际、财经、科技、健康、娱乐、地方、法治、评论 |

两个正式爬虫都会读取 `backend/.env` 中的数据库配置，写入 `news` 表，并优先使用 `source_url` 去重。光明网爬虫使用 RSS 源，新华网爬虫使用频道页静态 HTML 提取文章链接；部分 JS 动态渲染频道可能抓不到文章链接，脚本中已跳过这类频道。

光明网预览抓取，不入库：

```powershell
backend\.venv\Scripts\python.exe scripts\crawlers\rss_news_crawler.py --limit-per-source 30 --fetch-content --dry-run
```

光明网抓取并写入数据库：

```powershell
backend\.venv\Scripts\python.exe scripts\crawlers\rss_news_crawler.py --limit-per-source 30 --fetch-content
```

新华网预览抓取，不入库：

```powershell
backend\.venv\Scripts\python.exe scripts\crawlers\news_cn_crawler.py --limit-per-source 10 --dry-run
```

新华网抓取并写入数据库：

```powershell
backend\.venv\Scripts\python.exe scripts\crawlers\news_cn_crawler.py --limit-per-source 10
```

更新已有新闻的正文和图片：

```powershell
backend\.venv\Scripts\python.exe scripts\crawlers\rss_news_crawler.py --limit-per-source 30 --fetch-content --update-existing
backend\.venv\Scripts\python.exe scripts\crawlers\news_cn_crawler.py --limit-per-source 10 --update-existing
```

7 天历史测试预览：

```powershell
backend\.venv\Scripts\python.exe scripts\crawlers\gmw_7days_test_crawler.py --limit 50
```

写入 7 天历史测试数据：

```powershell
backend\.venv\Scripts\python.exe scripts\crawlers\gmw_7days_test_crawler.py --limit 100 --apply --reset
```

光明网详细说明见 `docs/gmw_crawler_usage.md`。`scripts/crawlers/README.md` 中的部分旧参数说明已经落后，当前以脚本 `--help` 输出和本 README 为准。

## 架构关系

```text
frontend  ->  backend  ->  ai-service
   |             |
   |             └── MySQL
   |
   └── 只访问 /api/*，不直连 AI 服务或数据库
```

- frontend 负责页面、路由、状态管理和 API 封装。
- backend 负责认证、业务接口、数据库访问、文件上传、AI 调用编排、mock fallback。
- ai-service 负责独立 AI 能力，默认可 mock/规则兜底，也可配置真实大模型。
- database 保存用户、新闻、互动、社区、AI 记录、系统配置、事件脉络、操作日志等数据。
- scripts/crawlers 作为离线或定时任务从光明网、新华网抓取新闻并写入 MySQL。

## 开发约定

- 前端只调用 backend 的 `/api/*` 接口。
- backend 可以调用 ai-service 的 `/ai/*` 接口，但前端不直接调用 ai-service。
- `.env`、真实 API Key、生产数据库密码不要提交到 Git。
- 全新建库优先使用 `schema.sql` + `seed.sql`；旧库升级使用 `database/run_migrations.py`。
- 数据库不可用时，部分模块保留 mock fallback 以便演示；新闻真实数据接口在无数据时可能返回空列表或 404。
- 管理后台接口按角色鉴权：`admin` 权限最高，`editor` 可访问部分审核和内容管理，普通用户不可访问后台。

## 常见问题

### PowerShell 提示 `<` 运算符不可用

PowerShell 不适合直接执行：

```powershell
mysql -u llm_news_user -p llm_news_system < database/schema.sql
```

请使用：

```powershell
cmd /c "mysql --default-character-set=utf8mb4 -u llm_news_user -p llm_news_system < database\schema.sql"
```

### 页面没有真实数据

依次检查：

1. MySQL 是否启动。
2. `backend/.env` 是否存在。
3. 数据库账号、密码、库名是否正确。
4. 是否导入了 `database/schema.sql` 和 `database/seed.sql`。
5. 是否执行了最新 migrations。
6. backend 是否已重启。

### AI 结果一直是 mock

检查 `ai-service/.env`：

- `SUMMARY_LLM_ENABLED` 或 `EVIDENCE_LLM_ENABLED` 是否为 `true`。
- API Key、Base URL、模型名是否正确。
- 是否重启了 ai-service，或调用了 `POST /ai/config/reload`。
- backend 管理后台 AI 配置是否覆盖了本地配置。

### 前端端口变成 5174

说明 5173 已被占用。直接访问 Vite 终端输出的新地址即可。

### `npm run build` 遇到 `.vite-temp` 权限问题

先关闭正在运行的前端服务，删除：

```text
frontend/node_modules/.vite-temp
```

再重新执行：

```powershell
npm.cmd run dev
```

## 相关文档

- `docs/api.md`：接口文档。
- `docs/api_offline.html`：离线接口文档。
- `docs/project_architecture.md`、`docs/project_architecture.png`：项目架构图。
- `docs/gmw_crawler_usage.md`：光明网爬虫说明。
- `docs/ai_module_guide.md`：AI 模块说明。
- `docs/development_standard.md`：开发规范。
- `deploy/README.md`：部署说明。
