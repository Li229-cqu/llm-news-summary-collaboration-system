# 基于大语言模型的智能新闻摘要与协同互动系统

## 一、项目简介

《基于大语言模型的智能新闻摘要与协同互动系统》是一个面向新闻浏览、AI 标题摘要生成、社区互动和个人中心管理的前后端分离系统。

当前系统已完成前后端基础框架、AI 服务、数据库接入、新闻浏览、新闻互动、AI 生成、个人中心、Timeline、社区互动和权限控制等核心功能。系统采用“数据库优先 + mock 兜底”的策略：MySQL 正常时优先读写数据库，数据库异常或演示数据不足时回退 mock，保证课程项目演示不断流。

AI 标题摘要生成模块保留动态 Mock 与 GLM-4-Flash 两种模式。LLM 调用失败时会自动 fallback 到 Mock，便于本地开发和课堂演示。

## 二、项目定位

系统围绕“新闻浏览 — 新闻详情互动 — AI 生成 — 社区交流 — 个人记录管理”的闭环展开，结合新闻内容消费、智能生成能力和用户协同互动，为用户提供连贯的新闻阅读与交流体验。

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
- MySQL 8.0
- PyMySQL
- python-dotenv
- 数据库优先 + mock 兜底

### AI 服务

- FastAPI
- 动态 Mock
- GLM-4-Flash
- LLM 调用失败 fallback 到 Mock

### 部署规划

- Nginx
- Docker / Docker Compose

## 四、目录结构

```text
llm-news-summary-collaboration-system/
├── frontend/       # 前端项目
├── backend/        # 后端业务服务
├── ai-service/     # AI 能力服务，支持 Mock + LLM
├── database/       # 数据库 schema、seed、migrations
├── scripts/        # RSS 新闻爬虫和工具脚本
├── docs/           # 项目文档
├── deploy/         # 部署配置
└── README.md       # 项目说明
```

| 目录 | 说明 |
| --- | --- |
| `frontend` | 前端项目，负责用户界面和前端交互 |
| `backend` | 后端业务服务，提供 API 和业务逻辑 |
| `ai-service` | AI 能力服务，支持 Mock 和 GLM-4-Flash |
| `database` | 数据库建表、种子数据和迁移脚本 |
| `scripts` | RSS 新闻爬虫和工具脚本 |
| `docs` | 项目文档，包含接口、开发计划和数据说明 |
| `deploy` | 部署配置，后续可存放 Nginx、Docker 等文件 |

## 五、开发阶段

| 阶段 | 说明 | 状态 |
| --- | --- | --- |
| 第 0 阶段 | 项目总骨架搭建 | 已完成 |
| 第 1 阶段 | 前端基础框架搭建 | 已完成 |
| 第 2 阶段 | 后端 FastAPI 基础框架搭建 | 已完成 |
| 第 3 阶段 | AI 服务框架搭建 | 已完成 |
| 第 4 阶段 | 用户与权限 mock 搭建 | 已完成 |
| 第 5 阶段 | 核心模块并行开发 | 已完成 |
| 第 6 阶段 | 数据库接入与联调 | 已完成 |

数据库化阶段补充：

- DB4：新闻模块数据库化，已完成。
- DB5：新闻互动与个人中心数据库化，已完成。
- DB7：AI 生成记录落库，已完成。
- DB8：Timeline 数据库化，已完成。
- DB9：社区模块数据库化，已完成。
- DB10：登录鉴权优先读取 `user` 表，已完成。
- DB11：全项目数据库化联调验收，已完成。
- DB12：真实新闻展示与爬虫质量修复，已完成。
- DB12.5：首页真实数据展示、侧边栏分类、热榜和订阅管理修复，已完成。

## 六、当前数据库化联调状态

- 新闻模块：数据库优先，mock 兜底。
- 新闻互动：数据库优先，mock 兜底。
- 个人中心：数据库优先，mock 兜底。
- AI 生成记录：生成成功后写入 `ai_generate_record`。
- Timeline：数据库优先，mock 兜底。
- 社区模块：数据库优先，mock 兜底。
- 登录鉴权：优先读取 `user` 表，同时兼容 `mock-token-user`、`mock-token-editor`、`mock-token-admin`。
- RSS 爬虫：支持 `source_url` 去重、正文解析、封面图提取、`crawl_log` 日志和旧新闻归档。

## 七、测试账号

| 角色 | 用户名 | 密码 |
| --- | --- | --- |
| 普通用户 | `user` | `123456` |
| 审核编辑 | `editor` | `123456` |
| 管理员 | `admin` | `123456` |

## 八、第一次完整操作流程

### 8.1 创建数据库和项目账号

先进入 MySQL：

```powershell
mysql -u root -p
```

说明：

- root 密码使用你自己本机 MySQL 的 root 密码。
- README 不记录 MySQL root 密码。

进入 MySQL 后执行：

```sql
CREATE DATABASE IF NOT EXISTS llm_news_system
DEFAULT CHARACTER SET utf8mb4
DEFAULT COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS 'llm_news_user'@'localhost'
IDENTIFIED BY '123456';

GRANT ALL PRIVILEGES ON llm_news_system.* TO 'llm_news_user'@'localhost';

FLUSH PRIVILEGES;

exit;
```

说明：

- `llm_news_user / 123456` 是本项目本地开发数据库账号。
- 该账号连接的是你本机的 MySQL 服务，不是额外安装的新数据库软件。

### 8.2 导入表结构和基础数据

PowerShell 中不要直接使用 `<`，请使用 `cmd /c` 包装：

```powershell
cmd /c "mysql --default-character-set=utf8mb4 -u llm_news_user -p llm_news_system < database\schema.sql"
cmd /c "mysql --default-character-set=utf8mb4 -u llm_news_user -p llm_news_system < database\seed.sql"
```

输入项目数据库密码：

```text
123456
```

注意：

- `seed.sql` 主要用于第一次初始化基础数据。
- 不建议在已有业务数据上随意反复执行 `seed.sql`。
- 如果确实需要重置数据库，建议先备份，再重新执行 `schema.sql`、`seed.sql` 和 migrations。

### 8.3 按顺序执行 migrations

请以 `database/migrations/` 目录中实际存在的文件为准，按编号顺序执行。例如：

```powershell
cmd /c "mysql --default-character-set=utf8mb4 -u llm_news_user -p llm_news_system < database\migrations\001_add_news_source_url_and_crawl_log.sql"
cmd /c "mysql --default-character-set=utf8mb4 -u llm_news_user -p llm_news_system < database\migrations\002_add_ai_generate_record_source_fields.sql"
cmd /c "mysql --default-character-set=utf8mb4 -u llm_news_user -p llm_news_system < database\migrations\003_add_community_post_tags.sql"
cmd /c "mysql --default-character-set=utf8mb4 -u llm_news_user -p llm_news_system < database\migrations\005_create_user_category_subscription.sql"
```

如果以后新增新的 migration 文件，请继续按编号顺序执行。

### 8.4 配置 backend/.env

在 `backend/.env` 中配置：

```env
DB_HOST=127.0.0.1
DB_PORT=3306
DB_NAME=llm_news_system
DB_USER=llm_news_user
DB_PASSWORD=123456
AI_SERVICE_URL=http://127.0.0.1:8001
```

注意：

- `backend/.env` 不要提交到 Git。
- 不要在 README 或代码中写 MySQL root 密码。
- 如果组员本地数据库账号密码不同，需要自行修改 `backend/.env`。

### 8.5 验证数据库

推荐使用下面这条 PowerShell 可运行命令：

```powershell
cmd /c "mysql --default-character-set=utf8mb4 -u llm_news_user -p llm_news_system -e ""SELECT COUNT(*) AS user_count FROM user; SELECT COUNT(*) AS news_count FROM news; SELECT COUNT(*) AS category_count FROM news_category; SELECT COUNT(*) AS topic_count FROM news_topic;"""
```

也可以进入 MySQL 后执行：

```sql
SELECT COUNT(*) FROM user;
SELECT COUNT(*) FROM news_category;
SELECT COUNT(*) FROM news_topic;
SELECT COUNT(*) FROM news;
SELECT COUNT(*) FROM ai_generate_record;
SELECT COUNT(*) FROM event_timeline;
```

## 九、三端启动方式

日常启动项目时，需要打开三个 PowerShell 窗口分别启动。不要把 backend、ai-service、frontend 写成一个连续命令，因为 `uvicorn` 和 `npm run dev` 会占用当前终端。

### 窗口 1：启动 backend

第一次启动：

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

第二次及以后启动：

```powershell
cd backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

访问：

- 后端健康检查：<http://127.0.0.1:8000/api/health>
- 后端 Swagger：<http://127.0.0.1:8000/docs>

### 窗口 2：启动 ai-service

第一次启动：

```powershell
cd ai-service
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
```

第二次及以后启动：

```powershell
cd ai-service
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
```

访问：

- AI 服务健康检查：<http://127.0.0.1:8001/ai/health>
- AI 服务 Swagger：<http://127.0.0.1:8001/docs>

### 窗口 3：启动 frontend

第一次启动：

```powershell
cd frontend
npm.cmd install
npm.cmd run dev
```

第二次及以后启动：

```powershell
cd frontend
npm.cmd run dev
```

访问：

- 前端页面：<http://localhost:5173>

## 十、操作过一次之后的常规流程

如果数据库、虚拟环境和依赖都已经配置过，日常启动通常只需要三个窗口：

```powershell
cd backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

```powershell
cd ai-service
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
```

```powershell
cd frontend
npm.cmd run dev
```

一般不需要每天重复执行 `schema.sql` 或 `seed.sql`。

## 十一、AI 标题摘要生成模块说明

在 `/ai/title-summary` 页面，用户可以：

1. 手动输入或从新闻详情页导入正文。
2. 选择标题数量、标题风格、摘要类型、摘要风格和摘要长度。
3. 点击生成，获得候选标题、短摘要、长摘要、要点摘要、关键词、新闻要素和一致性校验结果。
4. 查看并复用生成历史。

AI 服务支持两种工作模式：

- Mock 模式：快速返回，适合本地演示。
- LLM 模式：接入 GLM-4-Flash，适合真实生成体验。

AI 生成成功后，backend 会将生成记录保存到 `ai_generate_record` 表，个人中心可以查看生成历史。如果 ai-service 未启动，backend 会返回友好的 503 错误，不会导致 backend 崩溃。

## 十二、RSS 新闻爬虫说明

当前爬虫脚本：

```text
scripts/crawlers/rss_news_crawler.py
```

支持能力：

1. RSS 新闻解析。
2. `source_url` 去重。
3. 原文页正文解析。
4. 封面图 `cover_image` 提取。
5. `crawl_log` 爬取日志。
6. `--cleanup-days` 归档旧新闻。
7. `--update-existing-content` 补全已有新闻正文和封面图。

预览，不写入数据库：

```powershell
backend\.venv\Scripts\python.exe scripts\crawlers\rss_news_crawler.py --dry-run --max-items 3 --fetch-content
```

正式入库：

```powershell
backend\.venv\Scripts\python.exe scripts\crawlers\rss_news_crawler.py --max-items 5 --fetch-content
```

补全已有新闻正文和封面图：

```powershell
backend\.venv\Scripts\python.exe scripts\crawlers\rss_news_crawler.py --max-items 20 --fetch-content --update-existing-content
```

归档 30 天前旧新闻：

```powershell
backend\.venv\Scripts\python.exe scripts\crawlers\rss_news_crawler.py --max-items 5 --fetch-content --cleanup-days 30
```

说明：

- 当前只保存图片 URL，不下载图片文件。
- 正文解析失败时使用 RSS 摘要兜底。
- 不建议高频无限爬取。
- 建议每 15 分钟执行一次，每次每源 5 到 10 条。

## 十三、项目文档

详细文档位于 `docs/` 目录：

- `docs/api.md`：接口文档。
- `docs/development_plan.md`：开发计划。
- `docs/development_standard.md`：开发规范。
- `docs/mock_data_news.md`：新闻模块 mock 数据说明。
- `docs/ai_module_guide.md`：AI 模块使用指南。

## 十四、常见问题

### 1. 打开 http://127.0.0.1:8000/ 是 404

这是正常的。请访问：

- <http://127.0.0.1:8000/api/health>
- <http://127.0.0.1:8000/docs>

### 2. AI 服务暂时不可用

通常表示 ai-service 未启动，或 LLM 调用失败。请启动：

```powershell
cd ai-service
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
```

### 3. 页面仍显示 mock 数据

可能原因：

1. MySQL 未启动。
2. `backend/.env` 配置错误。
3. 对应数据库表为空。
4. backend 触发 mock fallback。

可检查：

```powershell
cmd /c "mysql --default-character-set=utf8mb4 -u llm_news_user -p llm_news_system -e ""SELECT COUNT(*) FROM news; SELECT COUNT(*) FROM community_post; SELECT COUNT(*) FROM news_category;"""
```

### 4. PowerShell 中 MySQL 导入失败

PowerShell 里不要直接执行：

```powershell
mysql -u llm_news_user -p llm_news_system < database\schema.sql
```

请使用：

```powershell
cmd /c "mysql --default-character-set=utf8mb4 -u llm_news_user -p llm_news_system < database\schema.sql"
```

## 十五、提交前检查

```powershell
git status
```

不要提交：

- `backend/.env`
- `ai-service/.env`
- `node_modules`
- `dist`
- `.vite-temp`
- `__pycache__`
- `*.pyc`
- 真实 API Key
- MySQL root 密码

检查冲突标记：

```powershell
Select-String -Path .\* -Pattern "<<<<<<<","=======",">>>>>>>" -Recurse
```

如需检查旧项目名称，请在本地将下面命令中的占位词替换为要检查的旧名称：

```powershell
Select-String -Path .\* -Pattern "旧项目名称关键词" -Recurse
```

## 十六、许可证

项目采用 MIT 许可证。详见 LICENSE 文件。
