# 项目待解决问题与并发任务分配

> 更新时间：2026-06-26
> 项目：基于大语言模型的智能新闻摘要与协同互动系统

**已完成**：问题6（热度联动）、问题7（全文索引搜索）、问题9（editor 空值）、问题10（工具函数提取）、问题11（启动连通性检测）

---

## 一、待解决问题

---

### 🟠 P1 - 架构性问题

---

#### 问题1：管理员后台数据全部来自 Mock，不反映真实数据库

**问题描述**

管理后台的概览数据（用户数、新闻数、待审核数）、用户列表、待审核帖子列表，全部读取进程内 Mock 数据，与数据库完全脱节：

```python
# backend/app/modules/admin/service.py
user_count = len(MOCK_USERS)   # 永远是固定的3个mock用户
news_count = len(MOCK_NEWS)    # 永远是mock新闻数量
```

**实现思路**

1. `get_dashboard()` 改为执行真实 SQL：
   - `SELECT COUNT(*) FROM user WHERE status=1`
   - `SELECT COUNT(*) FROM news WHERE status=1`
   - `SELECT COUNT(*) FROM community_post WHERE status=0`
2. `get_users()` 改为分页查询 `user` 表，支持按角色/状态过滤
3. `get_pending_posts()` 改为查询 `community_post WHERE status=0`，联表查询发帖用户信息
4. 保留 Mock 兜底逻辑，数据库异常时回退
5. 管理端"审核通过/拒绝"操作同步更新数据库 `status` 字段

**涉及文件**

- `backend/app/modules/admin/service.py`
- `backend/app/modules/admin/schema.py`（按需扩展字段）

---

#### 问题2：数据库无连接池，每次请求都新建连接

**问题描述**

当前每个数据库操作都完整经历 TCP连接→认证→执行→断开的完整生命周期：

```python
# backend/app/db/database.py
def get_connection():
    return pymysql.connect(...)  # 每次都新建！
```

在并发请求时，连接建立本身的耗时（通常 5-20ms）会成为性能瓶颈，且 MySQL 的最大连接数会被快速耗尽。

**实现思路**

1. 引入 `DBUtils` 库（`pip install dbutils`），使用 `PooledDB` 实现连接池
2. 在 `database.py` 中初始化一个全局连接池实例（`mincached=2, maxcached=10, maxconnections=20`）
3. `get_connection()` 改为从连接池取连接，用完归还而不是关闭
4. 或改用 `SQLAlchemy` + `pymysql` 驱动（更主流，未来迁移成本低）

**涉及文件**

- `backend/app/db/database.py`
- `backend/requirements.txt`（新增 dbutils 或 sqlalchemy）

---

#### 问题3：社区页"AI 新闻助手"未接入真实 AI，只是关键词字典

**问题描述**

社区页右侧已有完整的对话 UI，前端调用 `/api/community/ai-helper`，但后端实现是关键词字典匹配，无论用户问什么，都只能命中以下 4 个词：

```python
# backend/app/modules/community/service.py
def ai_news_helper(question: str) -> AIHelperResponse:
    responses = {
        "新闻摘要": "AI 新闻摘要功能可以帮助用户...",
        "热点": "当前热点话题包括...",
        "推荐": "系统可以根据浏览习惯...",
        "帮助": "我是您的 AI 新闻助手...",
    }
```

**实现思路**

1. `ai_news_helper()` 改为通过 `httpx` 调用 `ai-service` 的 chat 接口（参考 `backend/app/modules/ai/service.py` 中已有的 `_call_ai_service()` 写法）
2. 调用时附带系统提示词，限定 AI 回答范围为"新闻相关问题"
3. `ai-service` 未启动或调用失败时，保留当前关键词字典作为兜底
4. 前端已实现完整对话 UI，**无需改动前端**

**涉及文件**

- `backend/app/modules/community/service.py`（只改 `ai_news_helper` 函数）

---

#### 问题4：AI 摘要生成 Mock 模式内容质量差，影响演示效果

**问题描述**

`LLM_ENABLED=false` 时，标题生成使用硬编码的标题党模板：

```python
# ai-service/app/services/generate_service.py
f"震撼！{main_topic}竟然这样发展"
f"万万没想到，{main_topic}居然..."
```

**实现思路**

1. 删除模板标题生成逻辑，改为从输入文本提取前两句作为摘要
2. 标题改为提取新闻正文第一句，超过 30 字则裁剪
3. 增加 `source` 字段区分（`"mock"` vs `"llm"`），前端据此展示"AI服务未启用，以下为文本提取结果"的提示

**涉及文件**

- `ai-service/app/services/generate_service.py`
- `frontend/src/components/ai/AIResultPanel.vue`（展示 source 提示）

---

### 🟡 P2 - 功能性问题

---

#### 问题5：爬虫封面图使用第三方外链，存在防盗链失效风险

**问题描述**

爬虫抓取的图片 URL 直接存入数据库，前端直接加载第三方图片。中国新闻网等来源有防盗链保护，图片在非来源域名下会返回 403，导致页面图片全部显示为损坏图标。

**实现思路**

1. 爬虫中增加图片下载步骤：抓取封面图后，将图片二进制内容保存到 `backend/uploads/covers/` 目录
2. 数据库 `cover_image` 字段改为存储本地相对路径，如 `/uploads/covers/2026/06/filename.jpg`
3. 后端 FastAPI 挂载静态文件目录：`app.mount("/uploads", StaticFiles(directory="uploads"))`
4. 文件名使用新闻 URL 的 MD5 哈希避免重复下载
5. 设置请求超时和图片大小限制，防止爬虫卡死

**涉及文件**

- `scripts/crawlers/rss_news_crawler.py`
- `backend/app/main.py`（挂载 StaticFiles）

---

#### 问题8：Timeline 生成过程无进度反馈，用户体验差

**问题描述**

用户点击"查看脉络"后，如果 Timeline 尚未生成，后端需要调用 AI 服务，耗时可能超过 10 秒。当前前端没有任何进度提示，容易误以为页面卡死。

**实现思路**

1. `TimelineDrawer.vue` 在打开时，若 `status` 为 `generating`，展示加载骨架屏和提示文字"正在分析相关新闻，生成事件脉络..."
2. 前端轮询方案：每 2 秒调用一次 `/api/timeline/{topic_id}` 检查 `status`，直到返回 `success`
3. 后端在生成中时返回 `status: "generating"`，生成完成写入数据库后返回数据
4. 前端设置最大等待时间（如 60 秒），超时后提示"生成超时，请稍后重试"

**涉及文件**

- `frontend/src/components/timeline/TimelineDrawer.vue`
- `backend/app/modules/timeline/router.py`
- `backend/app/modules/timeline/service.py`

---

### 🔐 安全性问题（待功能完成后统一处理）

> 以下问题在内网开发和演示阶段风险可控，等核心功能全部开发完毕后，统一由一人负责实施。

---

#### 安全问题1：密码明文存储与明文比对

**问题描述**

`database/seed.sql` 中密码为明文 `123456`，后端登录时直接字符串对比，数据库泄露后所有用户密码即刻暴露。注册（feature/module-d 已实现）同样写入明文。

**实现思路**

1. 引入 `passlib[bcrypt]` 库
2. 注册/导入时调用 `bcrypt.hash(password)` 加密存储
3. 登录时调用 `bcrypt.verify(input_password, db_hash)` 比对
4. 更新 `seed.sql` 中密码字段为 bcrypt 哈希值

**涉及文件**

- `backend/app/modules/auth/service.py`
- `backend/requirements.txt`
- `database/seed.sql`

---

#### 安全问题2：Token 为固定字符串，任何人可伪造

**问题描述**

系统 Token 是写死的字符串，任何人发送 `Authorization: Bearer mock-token-admin` 即可获得管理员权限。

**实现思路**

1. 引入 `python-jose[cryptography]` 实现 JWT
2. 登录时用 `settings.secret_key` 签发 JWT，payload 含 `user_id`、`role`、`exp`
3. `get_current_user` 改为解码并校验 JWT
4. `backend/.env` 中 `SECRET_KEY` 改为真实随机字符串（32位以上）

**涉及文件**

- `backend/app/modules/auth/service.py`
- `backend/app/common/auth.py`
- `backend/requirements.txt`

---

#### 安全问题3：前端 Token 存储在 localStorage，存在 XSS 窃取风险

**实现思路**

- 方案A（推荐）：改为 HttpOnly Cookie，需前后端配合
- 方案B（折中）：保留 localStorage，后端响应头增加 `Content-Security-Policy` 限制外部脚本

**涉及文件**

- `frontend/src/stores/user.ts`
- `backend/app/modules/auth/router.py`

---

## 二、并发任务分配

---

### 👤 任务A — 数据库性能 + 管理后台接真实数据

**负责问题**：问题2（连接池）、问题1（管理后台改真实DB）

**开发顺序**：连接池 → 管理后台改真实 SQL（管理后台依赖连接池稳定后再改）

**主要改动范围**：

```
backend/app/db/database.py
backend/requirements.txt
backend/app/modules/admin/service.py
backend/app/modules/admin/schema.py
```

**完成标准**：`database.py` 的 `get_connection()` 改为连接池取连接；管理后台概览数据、用户列表、待审核帖子从数据库实时读取；数据库异常时自动回退 Mock。

---

### 👤 任务B — AI 能力接入

**负责问题**：问题4（AI Mock 质量）、问题3（社区 AI 助手接真实 AI）

**开发顺序**：先改 Mock 质量（不依赖 ai-service 启动）→ 再接入真实 AI

**主要改动范围**：

```
ai-service/app/services/generate_service.py
frontend/src/components/ai/AIResultPanel.vue
backend/app/modules/community/service.py（只改 ai_news_helper 函数）
```

**完成标准**：Mock 模式摘要生成不出现标题党词汇，改为提取原文句子；社区 AI 助手在 ai-service 启动时返回真实 AI 回答，未启动时回退关键词兜底不报错。

---

### 👤 任务C — 爬虫图片本地化

**负责问题**：问题5（封面图防盗链）

**主要改动范围**：

```
scripts/crawlers/rss_news_crawler.py
backend/app/main.py（新增 StaticFiles 挂载，注意保留已有的 startup 事件）
```

**完成标准**：新爬取的新闻封面图保存到 `backend/uploads/covers/` 目录，数据库存本地路径，页面图片正常显示不出现 403。

> ⚠️ `backend/app/main.py` 已有启动连通性检测代码，添加 StaticFiles 时**不要删除** `@app.on_event("startup")` 事件。

---

### 👤 任务D — Timeline 进度反馈

**负责问题**：问题8（Timeline 加载状态）

**主要改动范围**：

```
frontend/src/components/timeline/TimelineDrawer.vue
backend/app/modules/timeline/router.py
backend/app/modules/timeline/service.py
```

**完成标准**：Timeline 抽屉打开时若处于生成中状态，显示骨架屏和提示文字；前端每 2 秒轮询一次状态，生成完成后自动展示；超过 60 秒提示"生成超时，请稍后重试"。

---

### 🔐 安全专项（功能全部完成后统一处理）

**负责问题**：安全问题1（密码加密）、安全问题2（JWT Token）、安全问题3（Token存储）

**说明**：三个问题紧密相关，必须由**同一人**完成，改完后需通知所有人重新测试登录和注册流程（feature/module-d 已实现的注册功能也需同步更新为 bcrypt 加密）。

**主要改动范围**：

```
backend/app/modules/auth/service.py
backend/app/common/auth.py
backend/requirements.txt
database/seed.sql（密码字段更新为哈希值）
frontend/src/stores/user.ts（可选）
```

---

## 三、并发协作说明

### ⚠️ 需要沟通的文件交叉点

| 交叉文件 | 涉及任务 | 处理建议 |
|---------|---------|---------|
| `backend/app/main.py` | A（可能调整启动逻辑）、C（挂载 StaticFiles） | 改动区域不同，可并发；合并时各自保留对方代码 |
| `backend/app/modules/auth/service.py` | 任务B（问题3 依赖登录态）、安全专项 | 安全专项**最后做**，不影响 B 的开发 |

### 📋 推荐整体节奏

```
第1轮（可完全并发）：
  A: 连接池改造
  B: AI Mock 质量改进（去标题党）
  C: 爬虫图片本地化
  D: Timeline 进度反馈

第2轮（第1轮完成后）：
  A: 管理后台改真实 SQL（依赖连接池稳定）
  B: 社区 AI 助手接入真实 AI

安全专项（所有功能完成后）：
  一人负责: 密码加密 + JWT + Token 存储
```
