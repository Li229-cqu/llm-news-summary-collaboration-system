# 基于大语言模型的智能新闻摘要与协同互动系统

本项目是一个前后端分离的新闻摘要与协同互动系统，包含新闻浏览、新闻互动、AI 标题摘要生成、社区互动、个人中心、管理后台、RSS 新闻爬虫、Timeline 事件脉络等模块。

当前项目采用：

- 前端：Vue 3 + Vite + TypeScript + Element Plus
- 后端：FastAPI + MySQL + PyMySQL
- AI 服务：FastAPI，默认支持 mock 结果，后续可切换真实大模型
- 数据库：MySQL 8.0
- 爬虫：RSS 新闻爬虫，支持增量抓取与正文解析

## 一、项目目录

```text
llm-news-summary-collaboration-system/
├─ frontend/            前端项目
├─ backend/             后端 API 服务
├─ ai-service/          AI 生成服务
├─ database/            数据库 schema、seed、migrations
├─ scripts/crawlers/    RSS 新闻爬虫
├─ docs/                项目文档和接口文档
├─ plan/                任务规划
└─ README.md
```

## 二、第一次运行完整流程

第一次拉取项目后，建议按下面顺序执行。

### 1. 拉取代码

```powershell
git clone git@github.com:Li229-cqu/llm-news-summary-collaboration-system.git
cd llm-news-summary-collaboration-system
git checkout develop
git pull origin develop
```

如果已经有本地仓库，只需要：

```powershell
git checkout develop
git pull origin develop
```

### 2. 准备 MySQL 数据库

先确认本机已经安装 MySQL 8.0，并且已经创建项目数据库用户：

```text
数据库名：llm_news_system
数据库用户：llm_news_user
数据库密码：123456
数据库地址：127.0.0.1:3306
```

如果还没有创建数据库和用户，请先用 root 登录 MySQL 后执行：

```sql
CREATE DATABASE IF NOT EXISTS llm_news_system
DEFAULT CHARACTER SET utf8mb4
DEFAULT COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS 'llm_news_user'@'localhost'
IDENTIFIED BY '123456';

GRANT ALL PRIVILEGES ON llm_news_system.* TO 'llm_news_user'@'localhost';
FLUSH PRIVILEGES;
```

注意：不要把 root 密码写进项目文件。

### 3. 导入数据库表结构和基础数据

PowerShell 不能直接使用 `< database/schema.sql` 这种写法，请使用 `cmd /c`。

如果是第一次初始化，或者本地数据库可以清空重建，建议先重建数据库。当前表结构已经统一使用 `created_at / updated_at`，不再使用 `create_time / update_time` 作为数据库字段。

```powershell
cmd /c "mysql --default-character-set=utf8mb4 -u root -p -e ""DROP DATABASE IF EXISTS llm_news_system; CREATE DATABASE llm_news_system DEFAULT CHARACTER SET utf8mb4 DEFAULT COLLATE utf8mb4_unicode_ci; GRANT ALL PRIVILEGES ON llm_news_system.* TO 'llm_news_user'@'localhost'; FLUSH PRIVILEGES;"""
```

在项目根目录执行：

```powershell
cmd /c "mysql --default-character-set=utf8mb4 -u llm_news_user -p llm_news_system < database\schema.sql"
```

输入密码：

```text
123456
```

然后导入基础数据：

```powershell
cmd /c "mysql --default-character-set=utf8mb4 -u llm_news_user -p llm_news_system < database\seed.sql"
```

输入密码：

```text
123456
```

### 4. 执行数据库迁移

如果你已经按当前最新版 `schema.sql` 重新建库并导入了 `seed.sql`，通常不需要再执行 migrations。

只有在保留旧数据库、不想清空重建时，才需要按编号执行 migrations。当前项目已将时间字段统一为 `created_at / updated_at`，旧库如果还保留 `create_time / update_time`，建议优先重建数据库，避免字段不一致。

按编号依次执行：

```powershell
cmd /c "mysql --default-character-set=utf8mb4 -u llm_news_user -p llm_news_system < database\migrations\001_add_news_source_url_and_crawl_log.sql"
cmd /c "mysql --default-character-set=utf8mb4 -u llm_news_user -p llm_news_system < database\migrations\002_add_ai_generate_record_source_fields.sql"
cmd /c "mysql --default-character-set=utf8mb4 -u llm_news_user -p llm_news_system < database\migrations\003_add_community_post_tags.sql"
cmd /c "mysql --default-character-set=utf8mb4 -u llm_news_user -p llm_news_system < database\migrations\005_create_user_category_subscription.sql"
cmd /c "mysql --default-character-set=utf8mb4 -u llm_news_user -p llm_news_system < database\migrations\006_add_fulltext_index.sql"
cmd /c "mysql --default-character-set=utf8mb4 -u llm_news_user -p llm_news_system < database\migrations\007_add_news_editor_column.sql"
cmd /c "mysql --default-character-set=utf8mb4 -u llm_news_user -p llm_news_system < database\migrations\008_add_hot_topic_status.sql"
cmd /c "mysql --default-character-set=utf8mb4 -u llm_news_user -p llm_news_system < database\migrations\010_add_post_comment_media_json.sql"
```

每条命令提示输入密码时，输入：

```text
123456
```

### 5. 配置后端环境变量

检查是否存在：

```text
backend/.env
```

如果没有，创建 `backend/.env`：

```env
DB_HOST=127.0.0.1
DB_PORT=3306
DB_NAME=llm_news_system
DB_USER=llm_news_user
DB_PASSWORD=123456

AI_SERVICE_URL=http://127.0.0.1:8001
```

确认 `.env` 不要提交到 Git。

### 6. 安装并启动 backend

打开第一个 PowerShell 窗口：

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

如果虚拟环境已经创建过，以后只需要：

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

后端地址：

```text
http://127.0.0.1:8000
```

后端 Swagger：

```text
http://127.0.0.1:8000/docs
```

### 7. 安装并启动 ai-service

打开第二个 PowerShell 窗口：

```powershell
cd ai-service
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
copy .env.example .env
python -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
```

如果虚拟环境已经创建过，以后只需要：

```powershell
cd ai-service
.\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
```

AI 服务地址：

```text
http://127.0.0.1:8001
```

AI 服务 Swagger：

```text
http://127.0.0.1:8001/docs
```

默认 `.env.example` 中 `LLM_ENABLED=false`，表示使用 mock AI 结果，方便本地演示。

### 8. 安装并启动 frontend

打开第三个 PowerShell 窗口：

```powershell
cd frontend
npm install
npm.cmd run dev
```

前端地址：

```text
http://localhost:5173
```

如果 5173 被占用，Vite 可能会自动切到 5174，请看终端输出的实际地址。

## 三、以后常规运行流程

如果你已经完成过第一次初始化，以后每天启动只需要开三个终端。

### 终端 1：启动 backend

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 终端 2：启动 ai-service

```powershell
cd ai-service
.\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
```

### 终端 3：启动 frontend

```powershell
cd frontend
npm.cmd run dev
```

然后访问：

```text
http://localhost:5173
```

## 四、常用测试账号

| 角色 | 用户名 | 密码 |
| --- | --- | --- |
| 普通用户 | `user` | `123456` |
| 审核编辑 | `editor` | `123456` |
| 管理员 | `admin` | `123456` |

## 五、RSS 新闻爬虫

爬虫脚本位置：

```text
scripts/crawlers/rss_news_crawler.py
```

预览，不入库：

```powershell
backend\.venv\Scripts\python.exe scripts\crawlers\rss_news_crawler.py --dry-run --max-items 3
```

抓取并写入数据库：

```powershell
backend\.venv\Scripts\python.exe scripts\crawlers\rss_news_crawler.py --max-items 5 --fetch-content
```

补全文章正文：

```powershell
backend\.venv\Scripts\python.exe scripts\crawlers\rss_news_crawler.py --fetch-content --update-existing-content
```

归档旧新闻：

```powershell
backend\.venv\Scripts\python.exe scripts\crawlers\rss_news_crawler.py --cleanup-days 30
```

推荐始终使用 backend 虚拟环境运行爬虫，因为依赖安装在 `backend/.venv` 里。如果直接使用系统 `python`，可能会出现 `ModuleNotFoundError: No module named 'feedparser'`。

```powershell
backend\.venv\Scripts\python.exe scripts\crawlers\rss_news_crawler.py --max-items 5 --fetch-content
```

如果刚更新代码后爬虫报字段不存在，通常是数据库还没有按最新 `schema.sql` 重建。请回到上面的“导入数据库表结构和基础数据”步骤，重建数据库后重新导入 `schema.sql` 和 `seed.sql`。

## 六、验证数据库是否有数据

PowerShell 中执行：

```powershell
cmd /c "mysql --default-character-set=utf8mb4 -u llm_news_user -p llm_news_system -e ""SELECT COUNT(*) AS user_count FROM user; SELECT COUNT(*) AS news_count FROM news; SELECT COUNT(*) AS post_count FROM community_post; SELECT COUNT(*) AS comment_count FROM post_comment;"""
```

输入密码：

```text
123456
```

也可以进入 MySQL 后执行：

```powershell
mysql --default-character-set=utf8mb4 -u llm_news_user -p llm_news_system
```

然后输入：

```sql
SELECT COUNT(*) FROM user;
SELECT COUNT(*) FROM news;
SELECT COUNT(*) FROM community_post;
SELECT COUNT(*) FROM post_comment;
```

## 七、常见问题

### 1. PowerShell 提示 `<` 运算符不可用

不要在 PowerShell 里直接写：

```powershell
mysql -u llm_news_user -p llm_news_system < database/schema.sql
```

请使用：

```powershell
cmd /c "mysql --default-character-set=utf8mb4 -u llm_news_user -p llm_news_system < database\schema.sql"
```

### 2. 页面仍然显示 mock 数据

优先检查：

1. MySQL 是否启动。
2. `backend/.env` 是否存在。
3. `backend/.env` 中数据库账号密码是否正确。
4. 是否已经按当前最新版 `schema.sql` 重新建库并导入 `seed.sql`。
5. backend 是否重新启动。

当前新建库表结构已经包含主要字段和社区富媒体评论字段；如果是全新重建库，通常不需要再额外执行 migrations。

### 3. 前端端口变成 5174

说明 5173 被占用。可以关闭占用 5173 的旧前端进程，或者直接访问终端显示的新地址。

### 4. `npm run build` 出现 `.vite-temp` 权限错误

这是 Windows 下 Vite 缓存文件偶发权限问题。可以先关闭正在运行的前端服务，再删除：

```text
frontend/node_modules/.vite-temp
```

然后重新执行：

```powershell
npm.cmd run dev
```

## 八、主要访问地址

| 服务 | 地址 |
| --- | --- |
| 前端 | `http://localhost:5173` |
| 后端 | `http://127.0.0.1:8000` |
| 后端 Swagger | `http://127.0.0.1:8000/docs` |
| AI 服务 | `http://127.0.0.1:8001` |
| AI Swagger | `http://127.0.0.1:8001/docs` |

## 九、开发说明

- 前端只调用 backend，不直接调用 ai-service。
- backend 优先读取数据库，数据库异常时保留 mock fallback。
- ai-service 默认使用 mock 结果，便于本地演示。
- `.env` 文件不要提交到 Git。
- 不要把 MySQL root 密码或真实 API Key 写进 README、代码或示例配置。
