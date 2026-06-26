# 项目待解决问题与并发任务分配

> 更新时间：2026-06-26（修订于 18:00）
> 项目：基于大语言模型的智能新闻摘要与协同互动系统

---

## 一、待解决问题

---

### 🟠 P1 - 架构性问题

---

#### 问题1：管理员后台数据全部来自 Mock，不反映真实数据库

**问题描述**

管理后台的概览数据（用户数、新闻数、待审核数）、用户列表、待审核帖子列表，全部读取进程内 Mock 数据，与数据库完全脱节。

**实现思路**

1. `get_dashboard()` 改为执行真实 SQL
2. `get_users()` 改为分页查询 `user` 表
3. `get_pending_posts()` 改为查询 `community_post WHERE status=0`
4. 保留 Mock 兜底逻辑

**涉及文件**

- `backend/app/modules/admin/service.py`
- `backend/app/modules/admin/schema.py`

---

#### 问题2：数据库无连接池，每次请求都新建连接

**问题描述**

当前每个数据库操作都完整经历 TCP 连接→认证→执行→断开，在并发请求时连接建立耗时成为瓶颈。

**实现思路**

1. 引入 `DBUtils` 库，使用 `PooledDB` 实现连接池
2. 在 `database.py` 中初始化全局连接池实例
3. `get_connection()` 改为从连接池取连接

**涉及文件**

- `backend/app/db/database.py`
- `backend/requirements.txt`

---

#### 问题3：社区页"AI 新闻助手"未接入真实 AI，只是关键词字典

**问题描述**

社区页右侧 AI 助手只能匹配 4 个关键词，无论用户问什么都无法提供有意义的回答。

**实现思路**

1. 通过 `httpx` 调用 `ai-service` 的 chat 接口
2. 附带系统提示词限定回答范围为"新闻相关问题"
3. ai-service 未启动时回退关键词兜底

**涉及文件**

- `backend/app/modules/community/service.py`（只改 `ai_news_helper` 函数）

---

#### 问题4：AI 摘要生成 Mock 模式内容质量差，影响演示效果

**问题描述**

`LLM_ENABLED=false` 时，标题生成使用硬编码的标题党模板（"震撼！…"、"万万没想到…"）。

**实现思路**

1. 删除模板标题生成逻辑
2. 改为从输入文本提取前两句作为摘要
3. 标题改为提取新闻正文第一句，超过 30 字则裁剪
4. 增加 `source` 字段区分 `"mock"` vs `"llm"`

**涉及文件**

- `ai-service/app/services/generate_service.py`
- `frontend/src/components/ai/AIResultPanel.vue`

---

### 🟡 P2 - 功能性问题

---

#### 问题5：爬虫封面图使用第三方外链，存在防盗链失效风险

**问题描述**

爬虫抓取的图片 URL 直接存入数据库，中国新闻网等来源有防盗链保护，图片显示为损坏图标。

**实现思路**

1. 爬虫中增加图片下载步骤：保存到 `backend/uploads/covers/` 目录
2. 数据库存本地相对路径
3. 后端 FastAPI 挂载静态文件目录
4. 文件名使用 URL 的 MD5 哈希避免重复下载

**涉及文件**

- `scripts/crawlers/rss_news_crawler.py`
- `backend/app/main.py`（挂载 StaticFiles）

---

#### 问题8：Timeline 生成过程无进度反馈，用户体验差

**问题描述**

Timeline 调用 AI 服务耗时超过 10 秒，前端没有任何进度提示，容易误以为页面卡死。

**实现思路**

1. TimelineDrawer.vue 打开时，若 `status` 为 `generating`，展示加载骨架屏
2. 前端轮询 `/api/timeline/{topic_id}` 每 2 秒检查一次状态
3. 后端在生成中时返回 `status: "generating"`
4. 前端设置 60 秒超时

**涉及文件**

- `frontend/src/components/timeline/TimelineDrawer.vue`
- `backend/app/modules/timeline/router.py`
- `backend/app/modules/timeline/service.py`

---

#### 新功能1：Timeline 结构升级 + 数据模型丰富

**问题描述**

当前 Timeline 只是按时间排序的新闻摘要列表，缺乏结构化数据支撑后期的可视化流图和文档导出功能。

**实现思路**

**A. 丰富单个事件节点（TimelineNode）**：
- `event_type`: 节点类型（policy/reaction/breakthrough/outcome/background），决定可视化样式
- `importance`: 1-5 权重，影响可视化节点大小
- `event_detail`: 300 字长摘要，供文档导出正文用
- `related_event_ids`: 相关事件 ID 列表，用于画有向边
- `keywords`: 关键词列表，供可视化标签和文档索引

**B. 丰富整条脉络（TimelineResult）**：
- `overview`: 整个事件的执行摘要（文档引言）
- `key_figures`: 核心人物/机构列表
- `phases`: 事件阶段分组（[{name, start_event_id, end_event_id}]），可视化分区块
- `relationships`: 有向图的边数据（[{from_id, to_id, type: "causes"|"follows"|"parallel"}]）
- `schema_version`: 版本号，后期改格式时向后兼容

**C. 数据库拆分存储**（不破坏现有数据）：
- 保留 `timeline_json` 存节点数组
- 新增 `metadata_json` 存 overview/key_figures/phases
- 新增 `relationships_json` 存图的边数据

**后期支撑**：
- **可视化流图**：直接用 `relationships` 画有向图，`event_type` 定节点颜色，`importance` 定大小
- **文档导出**：用 `overview` 做引言 → 按 `phases` 分章节 → `event_detail` 做正文 → `source_news_id` 做参考文献

**涉及文件**

- `backend/app/modules/timeline/schema.py`（加新字段）
- `backend/app/modules/timeline/service.py`（改 AI 提示词，让 ai-service 生成新字段）
- `database/migrations/007_enhance_event_timeline.sql`（新增两列）

---

#### 新功能2：社区评论富媒体支持（表情 + 图片）

**问题描述**

评论区目前只支持纯文本，用户无法发表情和图片，降低了互动表现力。

**实现思路**

**A. 前端**：
- 评论框下方增加「表情」和「上传图片」按钮
- 表情使用开源库（如 emoji-picker-element），点击快速插入 emoji 码
- 图片上传：单选图片，预览后上传，附加到评论内容前

**B. 后端**：
- 扩展 `news_comment` 表：新增 `media_json` 列存储媒体数据
  ```json
  {
    "images": ["/uploads/comments/2026/06/abc123.jpg"],
    "emojis": ["😂", "🎉"]
  }
  ```
- 新建 API 上传端点：`POST /api/community/comment-media/upload` → 保存到 `backend/uploads/comments/` 目录
- 文件名格式：`{timestamp}_{random}.{ext}`，图片限制 5MB

**C. 数据库**：
- `backend/uploads/comments/` 目录需挂载到 FastAPI（复用 problem5 的 StaticFiles 挂载）
- 新增迁移脚本扩展 `news_comment` 表

**完成标准**：评论能包含 1 张图片和多个表情；页面正常显示；图片防盗链保护

**涉及文件**

- `frontend/src/components/community/CommentInput.vue`（新增表情和图片输入）
- `backend/app/modules/interaction/router.py`（新增媒体上传端点）
- `backend/app/modules/interaction/service.py`（存储和读取媒体数据）
- `database/migrations/008_add_comment_media.sql`（扩展表结构）

---

#### 新功能3：AI 评论区总结

**问题描述**

用户浏览评论区时需要逐条阅读，无法快速了解舆论核心观点。

**实现思路**

1. 新增 API 端点：`GET /api/community/posts/{post_id}/comments-summary`
2. 后端读取该帖子下所有评论（分页读取，总字数限制 10000 以内）
3. 构造提示词：「以下是用户对这条评论的所有回复，请总结主要观点」
4. 调用 ai-service 的 chat 接口，返回 200-300 字的总结
5. 前端在评论区顶部显示总结（可折叠）

**缓存策略**：缓存 1 小时，新增评论后清除缓存

**完成标准**：评论区显示 AI 总结面板；总结准确反映舆论方向；缓存生效

**涉及文件**

- `backend/app/modules/community/router.py`（新增路由）
- `backend/app/modules/community/service.py`（实现总结逻辑）
- `frontend/src/components/community/CommentsPanel.vue`（显示总结面板）

---

#### 新功能4：个性化推荐系统

**问题描述**

首页热榜对所有用户相同，没有基于个人阅读习惯的推荐，无法提升用户粘性。

**实现思路**

1. 新 API：`GET /api/profile/recommendations?limit=10`
2. 推荐算法：基于用户的浏览历史、收藏、点赞生成个性化新闻列表
   ```
   推荐分数 = (话题热度 * 用户相关度 * 新闻时新性)
   话题热度：该话题下所有新闻的互动总和
   用户相关度：用户在该话题下的浏览/收藏/点赞次数
   时新性：发布时间距今的天数（指数衰减）
   ```
3. 排序后取 Top N，返回给前端
4. 可选：缓存热门推荐结果（Redis），1 小时刷新一次

**数据来源**：
- `browse_history` → 用户关注话题
- `favorite` → 用户偏好
- `user_like` → 用户倾向

**完成标准**：推荐 API 返回 10 条符合用户偏好的新闻；首页推荐区正常展示

**涉及文件**

- `backend/app/modules/profile/router.py`（新增推荐端点）
- `backend/app/modules/profile/service.py`（推荐算法）
- `frontend/src/components/profile/RecommendationPanel.vue`（推荐展示组件）

---

#### 新功能5：用户阅读脉络可视化

**问题描述**

用户想了解自己的阅读轨迹和关注话题的演变，但只能逐条查看历史记录。

**实现思路**

**A. 后端数据组织**（核心）：
1. 话题关联计算：统计用户在短时间内（24 小时内）同时浏览的话题对
   ```sql
   SELECT n1.topic_id, n2.topic_id, COUNT(*) as co_browse_count
   FROM browse_history bh1, browse_history bh2, news n1, news n2
   WHERE bh1.user_id = bh2.user_id = ?
     AND bh1.news_id = n1.id AND bh2.news_id = n2.id
     AND ABS(TIMESTAMPDIFF(HOUR, bh1.browse_time, bh2.browse_time)) < 24
     AND n1.topic_id != n2.topic_id
   GROUP BY n1.topic_id, n2.topic_id
   ```
2. 话题热力数据：用户在各话题下的浏览/收藏次数
3. 时间轴数据：按日期聚合用户浏览各话题的频率

**B. 前端可视化**（3 种视图）：
1. **力导向图**：用 D3.js / ECharts Graph 展示话题关系网
   - 节点：用户浏览的话题（大小 = 浏览深度）
   - 边：话题关联（粗细 = 同时浏览频率）
   - 颜色：按分类区分
2. **时间轴视图**：按阅读时间展示话题演变过程
3. **热力图**：用户在各话题下的活跃度矩阵

**C. 导出功能**：
- 生成"我的阅读年报" PDF
  - 包含：关键话题、阅读时间、热门分类、关注演变
  - 样式：仿网易云年终报告

**完成标准**：
- 可视化脉络图正常显示，节点/边数据准确
- 前端支持 3 种视图切换
- PDF 导出正常生成

**涉及文件**

- `backend/app/modules/profile/router.py`（新增脉络和导出端点）
- `backend/app/modules/profile/service.py`（话题关联计算）
- `frontend/src/components/profile/ReadingTrajectory.vue`（力导向图）
- `frontend/src/components/profile/ReadingTimeline.vue`（时间轴）
- `frontend/src/components/profile/ReadingHeatmap.vue`（热力图）
- `frontend/src/utils/export-pdf.ts`（PDF 导出工具）

---

### 🔐 安全性问题（待功能完成后统一处理）

> 以下问题在内网开发和演示阶段风险可控，等核心功能全部开发完毕后，统一由一人负责实施。

---

#### 安全问题1：密码明文存储与明文比对

**实现思路**

1. 引入 `passlib[bcrypt]` 库
2. 注册/导入时调用 `bcrypt.hash(password)` 加密存储
3. 登录时调用 `bcrypt.verify(input_password, db_hash)` 比对

**涉及文件**

- `backend/app/modules/auth/service.py`
- `backend/requirements.txt`
- `database/seed.sql`

---

#### 安全问题2：Token 为固定字符串，任何人可伪造

**实现思路**

1. 引入 `python-jose[cryptography]` 实现 JWT
2. 登录时签发 JWT，payload 含 `user_id`、`role`、`exp`
3. `get_current_user` 改为解码并校验 JWT

**涉及文件**

- `backend/app/modules/auth/service.py`
- `backend/app/common/auth.py`
- `backend/requirements.txt`

---

#### 安全问题3：前端 Token 存储在 localStorage，存在 XSS 窃取风险

**实现思路**

- 方案A（推荐）：改为 HttpOnly Cookie
- 方案B（折中）：后端增加 Content-Security-Policy 限制外部脚本

**涉及文件**

- `frontend/src/stores/user.ts`
- `backend/app/modules/auth/router.py`

---

## 二、并发任务分配

---

### 👤 任务A — 数据库性能 + 管理后台接真实数据

**负责问题**：问题2（连接池）、问题1（管理后台改真实 DB）

**开发顺序**：连接池 → 管理后台改真实 SQL

**主要改动范围**：

```
backend/app/db/database.py
backend/requirements.txt
backend/app/modules/admin/service.py
backend/app/modules/admin/schema.py
```

**完成标准**：连接池正常工作；管理后台概览/用户列表/待审核从数据库实时读取；异常时回退 Mock。

---

### 👤 任务B — AI 能力接入 + 社区互动 AI 优化

**负责问题**：问题4（AI Mock 质量）、问题3（社区 AI 助手接真实 AI）、新功能3（AI 评论总结）

**开发顺序**：
1. 先改 Mock 质量（不依赖 ai-service）
2. 再接入社区 AI 助手（需 ai-service）
3. 最后做评论总结（复用 ai-service 调用逻辑）

**主要改动范围**：

```
ai-service/app/services/generate_service.py
frontend/src/components/ai/AIResultPanel.vue
backend/app/modules/community/service.py（ai_news_helper + comments_summary）
backend/app/modules/community/router.py（新增总结路由）
frontend/src/components/community/CommentsPanel.vue（显示总结）
```

**完成标准**：Mock 摘要不出现标题党；社区 AI 助手返回真实回答或兜底；评论总结准确。

---

### 👤 任务C — 爬虫图片本地化 + 社区评论富媒体

**负责问题**：问题5（封面图防盗链）、新功能2（评论富媒体）

**开发顺序**：
1. 先做爬虫图片本地化（不依赖其他）
2. 再做评论富媒体（复用 uploads 挂载）

**主要改动范围**：

```
scripts/crawlers/rss_news_crawler.py
backend/app/main.py（挂载 StaticFiles）
frontend/src/components/community/CommentInput.vue
backend/app/modules/interaction/router.py
backend/app/modules/interaction/service.py
database/migrations/008_add_comment_media.sql
```

**完成标准**：新闻封面图本地保存且正常显示；评论支持表情和图片；图片上传成功。

**⚠️ 注意**：`backend/app/main.py` 已有 startup 事件，添加 StaticFiles 时保留现有代码。

---

### 👤 任务D — Timeline 进度反馈 + 结构升级

**负责问题**：问题8（Timeline 加载进度）、新功能1（Timeline 结构升级）

**开发顺序**：
1. 先做进度反馈（无损改动，快速给用户反馈）
2. 再做结构升级（改 AI 提示词，丰富 schema）

**主要改动范围**：

```
frontend/src/components/timeline/TimelineDrawer.vue
backend/app/modules/timeline/router.py
backend/app/modules/timeline/service.py
backend/app/modules/timeline/schema.py
database/migrations/007_enhance_event_timeline.sql
```

**完成标准**：Timeline 生成中时显示进度提示；前端轮询检查状态；新 schema 包含 event_type/importance/overview/phases/relationships；后端能返回完整新数据。

---

### 👤 任务E — 个性化推荐系统

**负责问题**：新功能4（个性化推荐）

**开发顺序**：独立开发，无依赖

**主要改动范围**：

```
backend/app/modules/profile/router.py（新增推荐端点）
backend/app/modules/profile/service.py（推荐算法）
frontend/src/components/profile/RecommendationPanel.vue
```

**完成标准**：推荐 API 返回符合用户偏好的新闻列表；首页推荐区展示推荐新闻；算法正确计算用户相关度。

**⚠️ 可并发性**：**可完全并发**，与任务 A-D 无依赖关系。

---

### 👤 任务F — 用户阅读脉络可视化

**负责问题**：新功能5（阅读脉络可视化）

**开发分工**（5 个人）：
1. **F1 - 后端数据组织**（1 人）
   - 话题关联计算
   - 时间轴数据组织
   - 涉及文件：`backend/app/modules/profile/service.py` + `router.py`

2. **F2 - 前端力导向图**（1 人）
   - D3.js / ECharts Graph 实现
   - 涉及文件：`frontend/src/components/profile/ReadingTrajectory.vue`

3. **F3 - 前端时间轴视图**（1 人）
   - 按日期聚合展示
   - 涉及文件：`frontend/src/components/profile/ReadingTimeline.vue`

4. **F4 - 前端热力图**（1 人）
   - 话题活跃度矩阵
   - 涉及文件：`frontend/src/components/profile/ReadingHeatmap.vue`

5. **F5 - 导出功能**（1 人）
   - PDF 年报生成
   - 涉及文件：`frontend/src/utils/export-pdf.ts` + 导出路由

**开发顺序（关键路径）**：

```
第 1 阶段：F1 后端数据组织（必须最先）
  └─ 计算话题关联、时间轴数据、热力数据
  └─ 提供 3 个 API 端点：
     - GET /api/profile/reading-trajectory（脉络图数据）
     - GET /api/profile/reading-timeline（时间轴数据）
     - GET /api/profile/reading-heatmap（热力数据）

第 2 阶段（与 F1 并发）：F2、F3、F4 前端可视化
  ├─ F2 力导向图：消费 trajectory API
  ├─ F3 时间轴：消费 timeline API
  └─ F4 热力图：消费 heatmap API
  └─ 可用 mock 数据开发，等 F1 API 就绪后集成

第 3 阶段（等 F1 完成后）：F5 导出功能
  └─ 调用 F1 提供的 API 获取数据
  └─ 用 jspdf + html2canvas 生成 PDF 年报
```

**并发矩阵**：

| 阶段 | F1 | F2 | F3 | F4 | F5 | 说明 |
|------|----|----|----|----|----|----|
| **第1阶段** | ✅ | 💤 | 💤 | 💤 | 💤 | F1 必须先做 |
| **第2阶段** | ✅ | ✅ | ✅ | ✅ | 💤 | F2/F3/F4 并发，用 mock 数据 |
| **第3阶段** | ✅ | ✅ | ✅ | ✅ | ✅ | F5 等 F1 API 就绪 |

**临界路径**：F1 → F5（其他可并发）

**完成标准**：
- 脉络图节点/边数据准确
- 时间轴正确展示话题演变
- 热力图反映用户活跃度
- PDF 导出包含完整数据和美观样式

**⚠️ 可并发性**：
- ✅ F2、F3、F4 **可完全并发**（等 F1 API）
- ❌ F5 **必须等 F1 完成**（需要数据 API）
- ✅ 与任务 A-E **基本不冲突**（只涉及 profile 模块）

---

### 🔐 安全专项（功能全部完成后统一处理）

**负责问题**：安全问题1、安全问题2、安全问题3

**说明**：三个问题紧密相关，必须由**同一人**完成，改完后需通知所有人重新测试登录和注册。

---

## 三、并发协作说明

### ⚠️ 需要沟通的文件交叉点

| 交叉文件 | 涉及任务 | 处理建议 |
|---------|---------|---------|
| `backend/app/main.py` | C（挂载 StaticFiles）、D（可能调整） | 改动区域不同，可并发；合并时各自保留代码 |
| `backend/app/modules/community/service.py` | B（AI 助手 + 总结）、C（可能涉及） | B 先完成，C 不涉及此文件 |
| `backend/app/modules/profile/service.py` | E（推荐算法）、F1（脉络计算） | 可并发，两者独立实现各自算法 |
| `database/migrations/` | C（008）、D（007） | 执行顺序：007 → 008，编号确保序号不冲突 |

### 📋 推荐整体节奏

```
第1轮（可完全并发）：
  A: 连接池改造
  B: AI Mock 质量改进（去标题党）
  C: 爬虫图片本地化
  D: Timeline 进度反馈
  E: 个性化推荐系统
  F1: 阅读脉络后端数据组织（同步开始）

第2轮（第1轮完成后）：
  A: 管理后台改真实 SQL（依赖连接池稳定）
  B: 社区 AI 助手 + 评论总结
  C: 社区评论富媒体（依赖 uploads 挂载）
  D: Timeline 结构升级 + AI 提示词改造
  F2/F3/F4 (并发): 阅读脉络前端可视化（F2力导向图、F3时间轴、F4热力图）

第3轮（F1 完成后）：
  F5: 阅读脉络 PDF 导出

安全专项（所有功能完成后）：
  一人负责: 密码加密 + JWT + Token 存储
```

### 👥 人员配置建议

**总 6 个任务，分配给 8-9 人（建议）**：

```
A: 1 人（数据库）
B: 1 人（AI 能力）
C: 1 人（爬虫+富媒体）
D: 1 人（Timeline）
E: 1 人（推荐算法）
F: 5 人分工
  ├─ F1: 1 人（后端数据）
  ├─ F2: 1 人（力导向图）
  ├─ F3: 1 人（时间轴）
  ├─ F4: 1 人（热力图）
  └─ F5: 1 人（PDF导出）
```

**关键约束**：
1. **F1 必须最先完成**（其他前端人员可用 mock 数据并行开发）
2. **F5 必须等 F1**（但 F2/F3/F4 可同时进行）
3. **E 完全独立**（与其他任务无依赖）

---

**累计待做功能**：6 个问题 + 5 个新功能，分为 6 个任务（其中 F 分为 5 个人），三轮并发开发。预估 3-4 周完成全部功能。
