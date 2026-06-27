# 项目待解决问题与并发任务分配

> 更新时间：2026-06-27（修订于日志系统部署后）
> 项目：基于大语言模型的智能新闻摘要与协同互动系统
> 状态：功能开发阶段，聚焦性能优化 + AI 能力完善 + 用户体验提升

---

## 一、待解决问题总览

### ✅ 已完成功能（本轮已交付）

- ✅ **新功能2**：社区评论富媒体支持（表情 + 图片上传）- taskC 完成
- ✅ **新功能3**：AI 评论区总结 - taskB 完成  
- ✅ **新功能4**：个性化推荐系统 - taskE 完成
- ✅ **新功能5**：用户阅读脉络可视化（F1-F5）- taskF 完成
- ✅ **日志系统**：AI 调用状态区分（mock vs real API）- 刚部署

---

## 二、待处理问题（5 个）

---

### 🔴 问题1：管理员后台数据全部来自 Mock，不反映真实数据库

**问题描述**

管理后台的概览数据（用户数、新闻数、待审核数）、用户列表、待审核帖子列表，全部读取进程内 Mock 数据，与数据库完全脱节。

**表现现象**

- 用户列表显示 Mock 数据，与真实注册用户不符
- 数据库 user 表有 `create_time` 列错误：`(1054, "Unknown column 'create_time' in 'field list'")` 导致数据库查询失败，自动回退 Mock
- 后台新闻数、待审核数等关键指标都是硬编码

**实现思路**

1. 修正 SQL 查询语句（`create_time` → `created_at` 或其他正确的列名）
2. `get_dashboard()` 改为执行真实 SQL 统计数据
3. `get_users()` 改为分页查询 `user` 表  
4. `get_pending_posts()` 改为查询 `community_post WHERE status=0`
5. 所有查询失败时保留 Mock 兜底逻辑

**涉及文件**

- `backend/app/modules/admin/service.py`
- `backend/app/modules/admin/schema.py`

**完成标准**：管理后台各数据来自数据库；数据库异常时自动回退 Mock；SQL 语句修正无错误。

---

### 🔴 问题2：数据库无连接池，每次请求都新建连接

**问题描述**

当前每个数据库操作都完整经历 TCP 连接→认证→执行→断开，在并发请求时连接建立耗时成为瓶颈，并发能力受限。

**实现思路**

1. 引入 `DBUtils` 库，使用 `PooledDB` 实现连接池
2. 在 `database.py` 中初始化全局连接池实例（参数：最小连接数 2、最大连接数 20）
3. `get_connection()` 改为从连接池取连接
4. 应用启动时初始化连接池，关闭时释放所有连接

**涉及文件**

- `backend/app/db/database.py`
- `backend/requirements.txt`

**完成标准**：连接池正常工作，支持 10+ 并发请求；测试无异常。

---

### 🟠 问题3：社区"AI 新闻助手"依赖固定关键词，无法真正理解问题

**问题描述**

社区页右侧 AI 助手只有 4 个硬编码关键词（"推荐"、"热点"、"要点"、"分析"），无论用户问什么都无法提供有意义的回答。

**表现现象**

- 用户提问："这条新闻的立场是什么？" → AI 返回："关键词：推荐"（无关）
- 用户提问："如何看待这个事件？" → AI 返回："我们有 4 个推荐理由..." （答非所问）
- ai-service 日志显示：`🤖 [MOCK MODE] 返回模拟 AI 回答（LLM 未启用）`

**根本原因**

1. 前端和后端都是关键词匹配逻辑，没有调用真实 AI
2. LLM_ENABLED=false，ai-service 返回 mock 数据而非真实回答

**实现思路**

1. 启用真实 LLM：设置环境变量 `LLM_ENABLED=true` 和 `LLM_API_KEY`（当前配置为智谱 GLM-4-Flash）
2. 后端 `ai_news_helper` 函数改为通过 `httpx` 调用 `ai-service` 的 `/ai/chat` 接口
3. 构造系统提示词限定 AI 回答范围为"新闻相关问题"
4. ai-service 关闭时 fallback 到关键词兜底

**前置条件**

- ai-service 启用 LLM（LLM_ENABLED=true）
- 配置有效的 LLM API Key

**涉及文件**

- `backend/app/modules/community/service.py`（改 `ai_news_helper` 函数）
- `.env` 文件（配置 LLM_ENABLED、LLM_API_KEY）

**完成标准**：启用 LLM 后，AI 助手能正确理解问题并给出相关回答；日志显示 `✅ [REAL API]`。

---

### 🟠 问题4：AI 摘要生成 Mock 模式内容质量差，影响演示

**问题描述**

`LLM_ENABLED=false` 时，标题生成使用硬编码的标题党模板（"震撼！…"、"万万没想到…"、"业界炸裂…"），造成页面展示质量低，容易被误认为是垃圾内容。

**表现现象**

- 任何文本都生成："震撼！ {随机片段}"
- 所有标题样式统一，缺乏多样性
- 视觉上显得很非正式

**实现思路**

1. 删除硬编码标题党模板
2. Mock 摘要改为：
   - 标题：提取新闻正文第一句，超过 30 字则裁剪
   - 短摘：从输入文本提取前两句（或按句号分割）
   - 长摘：拼接前三句
3. 增加 `source` 字段区分 `"mock"` vs `"llm"`
4. 修改前端 AIResultPanel，在 Mock 模式下展示 badge："[Mock 演示]"

**涉及文件**

- `ai-service/app/services/generate_service.py`
- `frontend/src/components/ai/AIResultPanel.vue`

**完成标准**：Mock 模式下标题不出现"震撼"、"炸裂"等标题党词汇；前端能识别并标记 Mock 结果。

---

### 🟠 问题5：爬虫封面图使用第三方外链，存在防盗链失效风险

**问题描述**

爬虫抓取的图片 URL 直接存入数据库，中国新闻网等来源有防盗链保护，图片在浏览器中显示为 403 损坏图标。

**表现现象**

- 首页/社区的新闻卡片显示"图片加载失败"
- 浏览器控制台：`403 Forbidden - 防盗链拒绝`
- 数据库 `news.cover_image_url` 存的都是外站 URL

**实现思路**

1. 爬虫下载步骤：在 `rss_news_crawler.py` 中增加图片下载逻辑
   - 请求时带 `User-Agent` 和 `Referer` 头伪装浏览器
   - 保存到 `backend/uploads/covers/{source}/{date}/` 目录
   - 文件名使用 URL 的 MD5 哈希避免重复下载
   
2. 数据库存本地相对路径：`/uploads/covers/xxx.jpg` （而非完整 URL）

3. 后端 FastAPI 挂载静态文件目录：在 `main.py` 中调用 `app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")`

4. 修改前端，统一使用 `/uploads/covers/` 路径拼接

**涉及文件**

- `scripts/crawlers/rss_news_crawler.py`
- `backend/app/main.py`（挂载 StaticFiles）
- `backend/app/modules/news/service.py`（查询时处理 URL 拼接）

**完成标准**：新闻封面图本地保存成功；浏览器正常加载本地图片（无 403）；原外链失效时不影响显示。

---

### 🟡 问题6：Timeline 生成过程无进度反馈，用户体验差

**问题描述**

Timeline 调用 AI 服务耗时超过 10 秒，前端没有任何进度提示，用户无法判断是否卡死，容易关闭页面。

**表现现象**

- 用户点击"生成时间线" → 页面卡住 10+ 秒 → 无任何加载动画
- 控制台无日志，用户以为系统崩溃

**实现思路**

1. 前端 TimelineDrawer.vue：打开时检查 `status`，若为 `generating` 则显示加载骨架屏
2. 前端轮询逻辑：每 2 秒调用一次 `/api/timeline/{topic_id}` 检查生成状态
3. 后端在生成中时返回 `status: "generating"`；完成时返回 `status: "completed"`
4. 前端设置 60 秒超时，超时后提示"生成超时，请重试"
5. 生成完成后停止轮询，展示完整 Timeline 数据

**涉及文件**

- `frontend/src/components/timeline/TimelineDrawer.vue`
- `backend/app/modules/timeline/router.py`
- `backend/app/modules/timeline/service.py`

**完成标准**：Timeline 生成中时展示加载进度；用户能清楚看到"正在生成中"的状态；完成或超时后正常提示。

---

### 🟢 新功能1：Timeline 数据模型结构升级，支持可视化和导出

**问题描述**

当前 Timeline 只是按时间排序的新闻摘要列表，缺乏结构化数据支撑后期的可视化流图和文档导出功能。如要支持"事件关系图"和"事件脉络 PDF"，需要丰富数据模型。

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

**C. 数据库存储**：
- 保留现有 `timeline_json` 存节点数组
- 新增 `metadata_json` 存 overview/key_figures/phases
- 新增 `relationships_json` 存图的边数据

**后期应用**：
- **可视化流图**：直接用 `relationships` 画有向图，`event_type` 定节点颜色，`importance` 定大小
- **文档导出**：用 `overview` 做引言 → 按 `phases` 分章节 → `event_detail` 做正文 → `source_news_id` 做参考文献

**涉及文件**

- `backend/app/modules/timeline/schema.py`（扩展字段）
- `backend/app/modules/timeline/service.py`（改 AI 提示词）
- `database/migrations/007_enhance_event_timeline.sql`（新增数据库列）

**完成标准**：Timeline schema 包含完整的 event_type/importance/overview/phases/relationships；后端能返回完整结构数据；数据库迁移成功应用。

---

## 三、并发任务分配（5 个）

---

### 👤 任务 A — 数据库性能 + 管理后台

**负责问题**：问题 2（连接池）、问题 1（管理后台改真实 DB）

**开发顺序**：连接池 → 修复 SQL 语句 → 管理后台改真实查询

**关键步骤**：
1. `backend/requirements.txt` 添加 `DBUtils`
2. `database.py` 实现连接池，修正 SQL 查询
3. `admin/service.py` 改为查询真实数据库

**涉及文件**：
```
backend/app/db/database.py
backend/app/modules/admin/service.py
backend/requirements.txt
```

**完成标准**：
- 连接池工作正常，支持并发请求
- 管理后台数据从数据库读取，无 SQL 错误
- 数据库异常时自动回退 Mock

---

### 👤 任务 B — AI 能力与摘要质量

**负责问题**：问题 3（AI 助手接真实 AI）、问题 4（Mock 摘要质量）

**开发顺序**：先改 Mock 质量（快速见效）→ 再接真实 AI 助手

**关键步骤**：
1. `generate_service.py` 删除标题党模板，改为提取文本
2. `AIResultPanel.vue` 标记 Mock 结果
3. `community/service.py` 的 `ai_news_helper` 改为调用 ai-service 真实接口
4. 配置 `.env` 启用 LLM

**涉及文件**：
```
ai-service/app/services/generate_service.py
frontend/src/components/ai/AIResultPanel.vue
backend/app/modules/community/service.py
.env
```

**完成标准**：
- Mock 摘要不出现"震撼"、"炸裂"等词汇
- AI 助手能调用真实 ai-service（LLM_ENABLED=true 时）
- 日志输出 `✅ [REAL API]` 或 `🤖 [MOCK MODE]`

---

### 👤 任务 C — 爬虫与媒体本地化

**负责问题**：问题 5（爬虫图片本地化）

**开发顺序**：爬虫图片下载 → 后端挂载静态文件 → 前端 URL 调整

**关键步骤**：
1. `rss_news_crawler.py` 增加图片下载逻辑，保存到 `backend/uploads/covers/`
2. `news/schema.py` 和 `service.py` 调整 URL 拼接逻辑
3. `main.py` 挂载 `/uploads` 静态目录
4. 前端统一使用本地路径

**涉及文件**：
```
scripts/crawlers/rss_news_crawler.py
backend/app/main.py
backend/app/modules/news/service.py
frontend/src/components/news/NewsCard.vue
```

**完成标准**：
- 爬虫图片保存到本地目录
- 浏览器正常加载本地图片（无 403）
- 原外链失效不影响展示

---

### 👤 任务 D — Timeline 用户体验与结构升级

**负责问题**：问题 6（进度反馈）、新功能 1（数据结构升级）

**开发顺序**：进度反馈（快速改进 UX）→ 结构升级（支持后期功能）

**关键步骤**：
1. `TimelineDrawer.vue` 实现轮询逻辑，显示加载进度
2. `timeline/service.py` 返回 `status: "generating"` 或 `"completed"`
3. 扩展 Timeline schema 字段（event_type、importance、overview 等）
4. 修改 AI 提示词，让 ai-service 生成新字段
5. 执行数据库迁移脚本

**涉及文件**：
```
frontend/src/components/timeline/TimelineDrawer.vue
backend/app/modules/timeline/router.py
backend/app/modules/timeline/service.py
backend/app/modules/timeline/schema.py
database/migrations/007_enhance_event_timeline.sql
```

**完成标准**：
- Timeline 生成过程有进度反馈
- 新 schema 包含完整字段（event_type、importance 等）
- 后端返回完整结构数据
- 数据库迁移正常应用

---

### 👤 任务 E — 预留（未来扩展或紧急支持）

当前五个任务已覆盖所有待处理问题。任务 E 作为预留资源：
- 协助其他任务的集成和测试
- 处理跨任务的依赖问题
- 性能测试和监控

---

## 四、并发协作规则

### ⚠️ 文件交叉点与沟通

| 交叉文件 | 涉及任务 | 建议 |
|---------|---------|------|
| `backend/app/main.py` | A（可能），C（挂载 StaticFiles），D（可能） | 各自保留现有代码，避免覆盖 |
| `backend/app/modules/community/service.py` | B（AI 助手改造） | B 独占，改动时通知其他人 |
| `backend/app/modules/timeline/service.py` | D（全部） | D 独占 |
| `database/migrations/` | D（007_enhance_event_timeline） | 编号确保唯一 |
| `.env` | B（LLM 配置） | 新增 LLM_ENABLED、LLM_API_KEY 配置 |

### 📋 开发节奏

```
第 1 阶段（可完全并发）：
  A: 数据库连接池实现
  B: Mock 摘要质量改进（不依赖其他）
  C: 爬虫图片本地化
  D: Timeline 进度反馈 + 结构升级规划
  E: 支持和测试

第 2 阶段（第 1 阶段完成后，继续并发）：
  A: 管理后台改真实数据库查询
  B: AI 助手接真实 ai-service（依赖 A 的连接池稳定）
  C: 前端 URL 调整（依赖 C 爬虫完成）
  D: 执行数据库迁移和 AI 提示词优化
  E: 集成测试和性能验证
```

### ✅ 完成标准

**任务完成的定义**：
1. 代码改动完成，无 TypeScript/Python 语法错误
2. 核心功能通过本地测试
3. 日志输出清晰（DEBUG 级别可判断执行路径）
4. 若涉及数据库，迁移脚本已成功应用
5. 向其他任务告知依赖更新（如有）

**交付清单**：
- 代码提交到 develop 分支
- 提交信息清晰描述改动范围
- 遗留问题（如有）在代码注释或 TODO 中标注

---

## 五、关键约束与注意事项

1. **问题 3（AI 助手）**：需要启用 LLM（LLM_ENABLED=true），否则仍是 Mock 回答
2. **问题 5（爬虫）**：下载图片时注意 Referer 和 User-Agent，避免被封
3. **任务 D**：数据库迁移需在所有测试通过后再执行，避免数据丢失
4. **日志输出**：用 `🤖 [MOCK MODE]`、`🚀 [REAL API]`、`❌ [ERROR]` 等符号标记状态，便于排查

---

**预计完成时间**：2-3 周（5 个任务并发）

**最后更新**：2026-06-27 UTC+8
