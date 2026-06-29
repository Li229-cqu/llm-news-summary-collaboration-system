# 阶段 G：联调修复与演示可用性提升并发修改参考

> 项目：基于大语言模型的智能新闻摘要与协同互动系统  
> 目标：在已有核心功能基础上，集中修复“能不能用、数据是否真实、交互是否闭环、演示是否稳定”的问题。  
> 建议阶段定位：不是继续堆新功能，而是做一次主流程联调、数据库真实化、AI 能力完善和演示体验收口。

---

## 0. 当前问题归类

当前系统已具备新闻浏览、AI 标题摘要、社区互动、个人中心、Timeline、个性化推荐和阅读脉络等功能基础，但仍存在以下典型联调问题：

1. 社区无法发帖，发帖/评论后不能立即显示。
2. 新闻评论缺少删除键，点赞无法取消。
3. 社区热搜榜风格与首页不一致。
4. 管理后台页面跳转不稳定，快捷通道重复且无法对应。
5. 管理后台数据大量来自 Mock，没有真实连接数据库。
6. 首页“生成历史”入口跳转到个人中心，跳转语义需要重新规划。
7. 首页搜索框不能真正搜索。
8. 个人中心浏览记录等搜索功能未实现。
9. 社区 AI 助手没有接入真实 AI。
10. AI 响应慢，缺少清晰的 loading、超时和 mock/real 状态提示。
11. 爬虫封面图重复、外链图存在防盗链或失效风险。
12. 阅读脉络图显示效果不佳，节点跳转不稳定。
13. Timeline 生成过程缺少进度反馈，Timeline 关系图/可视化暂未完善。

因此，下一阶段建议拆成六条并发线：

| 并发线 | 主题 | 优先级 | 主要目标 |
|---|---|---:|---|
| A | 数据库性能 + 管理后台真实化 | 最高 | 连接池、后台真实数据、后台入口修复 |
| B | 社区主流程与互动闭环 | 最高 | 发帖、评论、删除、点赞/取消点赞、热搜风格 |
| C | 全站搜索专项 | 高 | 首页搜索、新闻搜索、社区搜索、个人记录搜索 |
| D | AI 体验与真实 AI 接入 | 高 | Mock 质量、社区 AI 助手、AI loading/超时 |
| E | 爬虫图片与媒体资源本地化 | 中高 | 过滤重复图、图片本地化、前端兜底 |
| F | Timeline + 阅读脉络可视化修复 | 中高 | Timeline 进度、结构升级、阅读脉络图修复 |

---

# 1. 并发线 A：数据库性能 + 管理后台真实化

## 1.1 要解决什么问题

本线主要解决两个问题：

### 问题 A1：管理后台数据不真实

当前管理后台的概览数据、用户列表、待审核帖子、快捷入口等存在以下问题：

- 后台统计可能仍来自 Mock 或硬编码。
- 用户列表和真实数据库不一致。
- 待审核帖子列表可能没有真正读取 `community_post` 表。
- 某些 SQL 字段名错误，例如使用 `create_time`，但数据库真实字段可能是 `created_at`。
- 管理后台页面跳转异常，快捷通道重复或无法对应真实页面。

### 问题 A2：数据库无连接池

当前数据库访问如果仍是每次请求都重新连接 MySQL，会影响并发性能。随着首页、社区、个人中心、管理后台、推荐、Timeline 等模块并发访问增多，数据库连接开销会成为明显瓶颈。

## 1.2 如何解决：详细步骤

### 第一步：检查数据库连接封装

1. 打开 `backend/app/db/database.py`。
2. 检查当前 `get_connection()` 是否每次都重新连接 MySQL。
3. 确认是否存在全局连接池。
4. 检查所有模块是否统一从 `get_connection()` 获取数据库连接。

### 第二步：引入连接池

1. 在 `backend/requirements.txt` 中加入：

```txt
DBUtils
```

2. 在 `backend/app/db/database.py` 中使用 `PooledDB` 初始化连接池。
3. 建议参数：
   - `mincached=2`
   - `maxcached=5`
   - `maxconnections=20`
   - `blocking=True`
4. `get_connection()` 改成从连接池取连接。
5. 确保连接使用完后 `conn.close()` 实际是归还连接池，而不是断开真实连接。

### 第三步：管理后台 Dashboard 接真实数据库

1. 打开 `backend/app/modules/admin/service.py`。
2. 找到 `get_dashboard()`。
3. 将用户数、新闻数、帖子数、待审核数等改为真实 SQL 统计。
4. 示例统计方向：
   - 用户总数：`SELECT COUNT(*) FROM user`
   - 新闻总数：`SELECT COUNT(*) FROM news`
   - 社区帖子数：`SELECT COUNT(*) FROM community_post`
   - 待审核帖子数：`SELECT COUNT(*) FROM community_post WHERE status = 0`
5. 数据库异常时保留 Mock 兜底，但日志必须明确输出 `[DB FALLBACK]`。

### 第四步：管理后台用户列表接真实数据库

1. 找到 `get_users()`。
2. 改为分页查询 `user` 表。
3. 检查字段名：如果数据库是 `created_at`，不要写 `create_time`。
4. 支持分页参数：`page`、`page_size`、`keyword`、`role`。
5. 返回结构要与前端页面一致。

### 第五步：待审核帖子接真实数据库

1. 找到 `get_pending_posts()`。
2. 查询 `community_post WHERE status = 0` 或项目实际待审核状态字段。
3. 返回帖子标题、作者、发布时间、状态、内容摘要。
4. 如果需要关联用户表，使用 `LEFT JOIN user ON community_post.user_id = user.id`。

### 第六步：修复管理后台页面跳转和快捷通道

1. 检查前端管理后台页面和路由。
2. 快捷通道只保留真实存在的页面入口。
3. 删除重复、无效、无法跳转的快捷入口。
4. 每个快捷入口必须与一个真实路由对应。

## 1.3 涉及修改文件

```text
backend/app/db/database.py
backend/requirements.txt
backend/app/modules/admin/service.py
backend/app/modules/admin/schema.py
frontend/src/views/admin/*.vue
frontend/src/router/index.ts
frontend/src/api/admin.ts
backend/app/main.py
database/migrations/*.sql
```

## 1.4 如何检查改动是否真实完成

### 后端检查

1. 启动后端。
2. 打开 Swagger：`http://127.0.0.1:8000/docs`。
3. 调用管理后台接口：dashboard、users、pending posts。
4. 修改数据库中 user/news/community_post 的数据，再刷新后台，看数字是否同步变化。
5. 关闭数据库或制造 SQL 异常，确认是否能 fallback mock，并输出明确日志。

### SQL 检查

```sql
SELECT COUNT(*) FROM user;
SELECT COUNT(*) FROM news;
SELECT COUNT(*) FROM community_post;
SELECT COUNT(*) FROM community_post WHERE status = 0;
```

后台显示数据应与 SQL 统计一致。

### 前端检查

1. 登录管理员账号。
2. 进入管理后台。
3. 检查 Dashboard、用户列表、待审核帖子和快捷通道是否真实可用。

### 构建检查

```powershell
cd frontend
npm run build
python -m py_compile backend/app/db/database.py
python -m py_compile backend/app/modules/admin/service.py
python -m py_compile backend/app/modules/admin/router.py
```

---

# 2. 并发线 B：社区主流程与互动闭环

## 2.1 要解决什么问题

1. 社区无法发帖。
2. 发帖成功后页面不立即显示新帖子。
3. 评论发布后不立即显示新评论。
4. 新闻评论没有删除键。
5. 点赞后无法取消点赞。
6. 社区热搜榜风格与首页热榜不一致。
7. 评论富媒体功能需要与现有评论链路真正打通。

## 2.2 如何解决：详细步骤

### 第一步：排查社区发帖链路

检查完整链路：

```text
CommunityView.vue
  → frontend/src/api/community.ts
  → backend/app/modules/community/router.py
  → backend/app/modules/community/service.py
  → community_post 表
```

重点确认前端请求、API 地址、请求体、token、当前用户、后端 INSERT、数据库新增和返回结构是否一致。

### 第二步：发帖后立即显示

建议先用可靠方式：

```text
发布成功 → page 重置为 1 → 调用 getPosts() → 刷新列表
```

后续可优化为：

```text
发布成功 → posts.unshift(newPost)
```

### 第三步：评论发布后立即显示

新闻详情评论和社区评论都要检查：

```text
评论框 → createComment API → 后端 INSERT → 返回新评论 → 前端刷新评论列表或插入评论
```

要求评论成功后输入框清空，新评论立即出现，富媒体评论能正确展示。

### 第四步：删除评论

权限建议：

| 用户 | 是否可删除 |
|---|---|
| 评论作者本人 | 可以 |
| 管理员 | 可以 |
| 审核/编辑 | 按权限设计决定 |
| 普通用户删除别人评论 | 不可以 |

后端提供删除接口，前端按权限显示删除按钮，删除成功后刷新列表或移除评论。

### 第五步：点赞/取消点赞

点赞要支持 toggle：

```text
第一次点击：插入 user_like，like_count + 1
再次点击：删除 user_like，like_count - 1
```

返回格式建议：

```json
{
  "liked": true,
  "like_count": 10
}
```

社区帖子点赞、新闻点赞都应遵循同一模式。

### 第六步：社区热搜榜风格统一

参考首页热榜样式：排名数字、标题截断、热度/评论数/浏览数、hover 样式。保证点击热搜项能跳转到对应帖子或新闻。

## 2.3 涉及修改文件

```text
frontend/src/views/community/CommunityView.vue
frontend/src/api/community.ts
frontend/src/api/interaction.ts
frontend/src/components/interaction/CommentBox.vue
frontend/src/components/interaction/CommentItem.vue
frontend/src/components/news/NewsCommentList.vue
backend/app/modules/community/router.py
backend/app/modules/community/service.py
backend/app/modules/community/schema.py
backend/app/modules/interaction/router.py
backend/app/modules/interaction/service.py
backend/app/modules/interaction/schema.py
backend/app/modules/news/router.py
backend/app/modules/news/service.py
database/migrations/*.sql
```

## 2.4 如何检查改动是否真实完成

### 社区发帖检查

1. 登录 `user / 123456`。
2. 打开社区页。
3. 发布帖子。
4. 预期：请求返回 200，数据库新增记录，页面立刻显示，刷新后仍存在。

SQL：

```sql
SELECT id, title, user_id, status, created_at
FROM community_post
ORDER BY id DESC
LIMIT 5;
```

### 评论检查

1. 打开新闻详情页。
2. 发布一条评论。
3. 评论立即显示，刷新后仍存在。
4. 删除自己的评论，页面和数据库同步。

### 点赞/取消点赞检查

1. 点赞一条新闻。
2. 再次点击取消点赞。
3. 刷新页面后状态正确，like_count 不会无限增加。

SQL：

```sql
SELECT * FROM user_like
WHERE user_id = 1 AND target_type = 'news'
ORDER BY id DESC
LIMIT 10;
```

---

# 3. 并发线 C：全站搜索专项

## 3.1 要解决什么问题

1. 首页搜索框无法真正搜索。
2. 新闻列表搜索未实现或只改了输入框，没有调用 API。
3. 社区搜索未实现。
4. 个人中心浏览历史、收藏记录、AI 生成记录等搜索功能未实现。
5. 搜索逻辑分散，容易每个页面各写一套。

## 3.2 如何解决：详细步骤

### 第一步：统一新闻搜索 API

推荐接口：

```text
GET /api/news/list?keyword=xxx&category_id=xxx&page=1&page_size=10
```

后端支持：

```sql
WHERE title LIKE %keyword%
   OR summary LIKE %keyword%
   OR content LIKE %keyword%
```

要求 keyword 为空时返回正常列表，支持分页和分类筛选，SQL 使用参数化查询。

### 第二步：首页搜索框接入新闻搜索

1. 输入关键词后回车或点击按钮触发。
2. 新闻列表更新为搜索结果。
3. URL 可带 `?keyword=xxx`。
4. 清空关键词后恢复默认新闻流。

### 第三步：社区搜索

接口建议：

```text
GET /api/community/posts?keyword=xxx&page=1&page_size=10
```

搜索范围：标题、内容、作者昵称。

### 第四步：个人中心搜索

浏览历史和收藏记录可先前端本地过滤；如果数据量大，再扩展后端 keyword 参数。AI 生成记录按原文片段、标题、摘要过滤。

### 第五步：搜索体验统一

所有搜索框统一具备：清空按钮、loading、空结果提示、失败提示、回车触发、防抖或显式搜索按钮。

## 3.3 涉及修改文件

```text
backend/app/modules/news/router.py
backend/app/modules/news/service.py
backend/app/modules/news/schema.py
frontend/src/api/news.ts
frontend/src/views/home/HomeView.vue
frontend/src/components/news/NewsList.vue
frontend/src/components/news/NewsCard.vue
frontend/src/views/community/CommunityView.vue
frontend/src/api/community.ts
frontend/src/views/profile/ProfileView.vue
frontend/src/router/index.ts
```

## 3.4 如何检查改动是否真实完成

### 首页搜索检查

1. 首页搜索“人工智能”。
2. Network 出现带 keyword 的请求。
3. 页面展示相关结果。
4. 空关键词恢复默认列表。

### 后端接口检查

```text
GET /api/news/list?keyword=人工智能&page=1&page_size=10
```

预期返回 200，结果与关键词相关。

### 社区和个人中心搜索检查

社区搜索更新帖子列表；个人中心浏览历史输入关键词后列表过滤，清空后恢复。

---

# 4. 并发线 D：AI 体验与真实 AI 接入

## 4.1 要解决什么问题

1. AI 摘要 Mock 模式内容质量差，标题党严重。
2. AIResultPanel 没有明确展示结果来自 Mock 还是真实 LLM。
3. 社区 AI 助手没有接入真实 AI，只做关键词匹配。
4. AI 响应慢，缺少 loading、超时和 fallback 提示。

## 4.2 如何解决：详细步骤

### 第一步：优化 AI 摘要 Mock 质量

修改 `ai-service/app/services/generate_service.py`：

1. 标题提取正文第一句，超过 30 字裁剪。
2. 不使用“震撼”“炸裂”“万万没想到”等词。
3. 短摘要取前两句，长摘要取前三到五句。
4. 要点按句子拆分成 3 条以内。

### 第二步：返回 source 字段

Mock 返回：

```json
{"source": "mock"}
```

真实 LLM 返回：

```json
{"source": "llm"}
```

日志保持：`🤖 [MOCK MODE]`、`🚀 [REAL API]`、`❌ [ERROR]`。

### 第三步：前端 AIResultPanel 标记 Mock/Real

`source = mock` 显示 `[Mock 演示]`，`source = llm` 显示 `[真实 AI]`。

### 第四步：社区 AI 助手接 ai-service

修改 `backend/app/modules/community/service.py` 中的 `ai_news_helper`：

1. 构造新闻相关 system prompt。
2. 用 `httpx` 调用 ai-service chat 接口。
3. ai-service 不可用时 fallback 关键词兜底。
4. 日志区分真实调用和 fallback。

### 第五步：AI loading 和超时

前端社区 AI 助手：提问后显示 loading，禁用重复提交，30-60 秒超时提示，后端失败显示友好错误。

## 4.3 涉及修改文件

```text
ai-service/app/services/generate_service.py
ai-service/app/routers/generate.py
ai-service/app/schemas/generate.py
frontend/src/components/ai/AIResultPanel.vue
backend/app/modules/community/service.py
backend/app/modules/community/router.py
frontend/src/views/community/CommunityView.vue
frontend/src/api/community.ts
.env.example
ai-service/.env.example
frontend/src/api/ai.ts
backend/app/modules/ai/service.py
```

## 4.4 如何检查改动是否真实完成

### Mock 检查

1. `LLM_ENABLED=false`。
2. 输入新闻正文。
3. AI 生成结果不出现标题党词汇，前端显示 `[Mock 演示]`。

### 真实 AI 检查

1. 配置 `LLM_ENABLED=true` 和有效 API Key。
2. 启动 ai-service。
3. 社区 AI 助手提问新闻相关问题。
4. 返回与问题相关，日志显示真实 API 调用。

### 超时检查

停掉 ai-service 后提问，前端不应卡死，后端应 fallback 或返回友好提示。

---

# 5. 并发线 E：爬虫图片与媒体资源本地化

## 5.1 要解决什么问题

1. 多条新闻共用同一张默认图。
2. 新闻原文无图或视频新闻被强行套默认图。
3. 爬虫保存第三方外链，浏览器可能 403。
4. 图片外链失效后页面损坏。
5. 评论图片、新闻封面等上传资源需要统一 `/uploads` 静态访问。

## 5.2 如何解决：详细步骤

### 第一步：调整封面图提取优先级

```text
正文主图 > 正文有效图片 > og:image > RSS media image > 空
```

不要优先使用 RSS 默认图，不要强行让每条新闻都有图。

### 第二步：过滤通用默认图

过滤 URL 包含：

```text
logo icon avatar default placeholder blank loading spacer video_default play app qr
```

### 第三步：重复图过滤

同一轮爬虫中，同一个 image_url 出现超过 3 次，则判定为通用图，不写入 `cover_image`。

### 第四步：识别视频新闻

标题、URL、页面结构包含“视频、video、播放、iframe、player”时，允许 `cover_image = null`。

### 第五步：图片下载本地化

1. 下载有效封面图。
2. 请求头带 User-Agent 和 Referer。
3. 保存到：`backend/uploads/covers/{source}/{date}/`。
4. 文件名使用 URL MD5。
5. 数据库存相对路径：`/uploads/covers/xxx.jpg`。

### 第六步：FastAPI 挂载 uploads

```python
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
```

### 第七步：前端图片路径处理

1. `/uploads/...` 直接使用。
2. http 外链兼容显示。
3. 空图显示分类占位图。
4. 不把默认图写回数据库。

## 5.3 涉及修改文件

```text
scripts/crawlers/rss_news_crawler.py
backend/app/main.py
backend/app/modules/news/service.py
frontend/src/components/news/NewsCard.vue
frontend/src/views/home/HomeView.vue
frontend/src/utils/media.ts
backend/app/modules/news/schema.py
database/migrations/*.sql
backend/uploads/
frontend/src/assets/placeholders/
```

## 5.4 如何检查改动是否真实完成

### 爬虫统计检查

重新爬取后输出：总新闻数、有真实封面图数、无图数、唯一图片数、重复图片 Top 10、过滤掉的重复图数量、过滤掉的视频默认图数量。

### 数据库检查

```sql
SELECT cover_image, COUNT(*) AS cnt
FROM news
WHERE cover_image IS NOT NULL AND cover_image != ''
GROUP BY cover_image
ORDER BY cnt DESC
LIMIT 10;
```

预期不再出现同一张图重复 20 多次。

### 浏览器检查

首页新闻卡片图片正常显示，Network 图片请求为 `/uploads/covers/...`，不再大量 403。

---

# 6. 并发线 F：Timeline + 阅读脉络可视化修复

## 6.1 要解决什么问题

1. Timeline 生成过程无进度反馈。
2. Timeline 结构数据不足，不支持后续关系图和导出。
3. Timeline 关系图或事件脉络图暂未实现。
4. 个人中心阅读脉络图显示不好看。
5. 阅读脉络图节点跳转不稳定。
6. 阅读脉络图存在 ECharts 容器宽度问题。

## 6.2 如何解决：详细步骤

### 第一步：Timeline 生成进度反馈

前端 `TimelineDrawer.vue`：

1. 打开 drawer 时请求 Timeline。
2. `status = generating` 时显示骨架屏。
3. 每 2 秒轮询 `/api/timeline/{topic_id}`。
4. 最长 60 秒。
5. 完成后停止轮询并展示结果。
6. 超时提示。

后端返回 `generating`、`completed`、`failed`。

### 第二步：Timeline 结构升级

扩展单节点：

```text
event_type
importance
event_detail
related_event_ids
keywords
```

扩展整体结果：

```text
overview
key_figures
phases
relationships
schema_version
```

数据库保留 `timeline_json`，新增 `metadata_json` 和 `relationships_json`。

### 第三步：Timeline 事件关系图规划

关系图数据来源：

```text
relationships: [{ from_id, to_id, type }]
```

`event_type` 定颜色，`importance` 定大小，`phases` 做分区。

### 第四步：阅读脉络图宽度修复

1. 用父级链路诊断找到哪一级宽度变成 64px。
2. 确保图表区域不在 grid 小列里。
3. `.chart-card` 单独占满一行。
4. `.trajectory-chart` 有正常宽度和高度。
5. `renderChart` 不应在 `width < 300` 时初始化。
6. 如果旧实例以 64px 初始化，应 dispose 后等待有效宽度再 init。

### 第五步：阅读脉络节点跳转修复

1. news 节点必须携带 `news_id`。
2. 点击 news 节点：`router.push(`/news/${news_id}`)`。
3. category/topic 节点不跳转，只显示提示或筛选。
4. 最近阅读列表点击必须跳转详情页。

### 第六步：阅读脉络图美化

1. 节点大小差异更明显。
2. 支持只看分类/话题、显示/隐藏新闻节点。
3. 增加最近 7 天/30 天筛选。
4. 增加“重置视图”按钮。
5. 图表旁保留 summary 和最近阅读列表。

## 6.3 涉及修改文件

Timeline：

```text
frontend/src/components/timeline/TimelineDrawer.vue
frontend/src/api/timeline.ts
backend/app/modules/timeline/router.py
backend/app/modules/timeline/service.py
backend/app/modules/timeline/schema.py
database/migrations/007_enhance_event_timeline.sql
```

阅读脉络：

```text
frontend/src/components/profile/ReadingTrajectory.vue
frontend/src/views/profile/ProfileView.vue
frontend/src/api/profile.ts
backend/app/modules/profile/router.py
backend/app/modules/profile/service.py
frontend/src/router/index.ts
frontend/src/components/timeline/TimelineGraph.vue
frontend/src/components/profile/ReadingTimeline.vue
frontend/src/components/profile/ReadingHeatmap.vue
```

## 6.4 如何检查改动是否真实完成

### Timeline 进度检查

打开某个话题 Timeline，触发生成。应立即显示“正在生成”，Network 每 2 秒轮询，完成后展示 timeline，超时有提示。

### Timeline 结构检查

接口返回应包含：`overview`、`phases`、`relationships`、`schema_version`，单节点包含 `event_type`、`importance`、`event_detail`、`related_event_ids`、`keywords`。

### 阅读脉络图检查

```js
const el = document.querySelector('.trajectory-chart')
console.log(el?.clientWidth, el?.clientHeight, el?.innerHTML.length)
```

预期：`clientWidth > 300`，`clientHeight ≈ 520`，`innerHTML.length > 0`。

Canvas 检查：

```js
document.querySelector('.trajectory-chart canvas, .trajectory-chart svg')
```

预期返回真实元素。

---

# 7. 总体先后顺序

## 7.1 必须先做的

最高优先级：

```text
B：社区发帖/评论/点赞闭环
A：数据库连接池和管理后台真实数据
C：首页搜索
```

原因：这些是用户最容易发现的基础问题。社区不能发帖、后台全是 mock、首页不能搜索，都会直接影响演示可信度。

## 7.2 可以完全并发的

```text
A：连接池
B：社区互动
C：搜索
D：Mock 摘要质量优化
E：爬虫图片过滤
F：Timeline 进度反馈
```

## 7.3 有依赖关系的

| 后做任务 | 依赖 |
|---|---|
| 管理后台真实 SQL | 建议等连接池完成后做 |
| 社区 AI 助手真实 AI | 依赖 ai-service chat 能力和 LLM 配置 |
| 评论图片上传 | 依赖 `/uploads` 静态目录挂载 |
| 爬虫图片本地化前端展示 | 依赖爬虫先保存本地路径 |
| Timeline 结构升级迁移 | 建议等当前 Timeline 查询稳定后执行 |
| 阅读脉络图美化 | 建议等容器宽度和跳转先修完 |
| PDF 导出 | 依赖 Timeline/阅读脉络数据结构稳定 |

## 7.4 建议开发批次

### 第 1 批：主流程可用性

```text
B1 社区发帖可用
B2 评论发布后立即显示
B3 点赞/取消点赞
C1 首页搜索
A1 数据库连接池
D1 Mock 摘要去标题党
```

### 第 2 批：后台与数据真实化

```text
A2 管理后台 dashboard 接数据库
A3 用户列表接数据库
A4 待审核帖子接数据库
A5 后台快捷入口修复
C2 社区搜索
C3 个人中心搜索
```

### 第 3 批：AI 与媒体体验

```text
D2 社区 AI 助手接 ai-service
D3 AI loading/超时/fallback
E1 重复默认图过滤
E2 图片下载本地化
E3 前端图片兜底
```

### 第 4 批：可视化与演示 polish

```text
F1 Timeline 生成进度
F2 Timeline 结构升级
F3 阅读脉络图宽度修复
F4 阅读脉络图美化和节点跳转
G1 首页生成历史入口重规划
G2 社区热搜榜风格统一
```

---

# 8. 并发协作注意事项

## 8.1 文件交叉点

| 文件 | 涉及并发线 | 注意事项 |
|---|---|---|
| `backend/app/main.py` | A、E、F | E 可能挂载 uploads；F 可能注册 timeline；合并时都保留 |
| `frontend/package.json` | D、E、F | 不要删掉 echarts、sass-embedded、emoji-picker-element |
| `frontend/src/router/index.ts` | A、C、F、G | 新增路由要合并，不要覆盖 |
| `frontend/src/views/community/CommunityView.vue` | B、D、G | 社区发帖、AI 助手、热搜风格可能同时改，需沟通 |
| `backend/app/modules/community/service.py` | B、D | B 改发帖/互动，D 改 AI 助手，避免互相覆盖 |
| `backend/app/modules/profile/service.py` | A、C、F | 保留推荐、阅读分析、个人中心搜索 |
| `frontend/src/views/profile/ProfileView.vue` | C、F | 保留阅读脉络 Tab，新增搜索时不要破坏已有 Tab |
| `database/migrations/` | A、E、F | 编号不要冲突，迁移执行前先备份 |

## 8.2 Git 合并规则

1. 每条并发线单独建分支。
2. 分支命名建议：
   - `fix/admin-db-real`
   - `fix/community-interaction`
   - `feat/global-search`
   - `feat/ai-real-helper`
   - `fix/crawler-local-images`
   - `fix/timeline-reading-visual`
3. 每次合并前必须：
   - `git status`
   - `npm run build`
   - 后端 `py_compile`
4. 不要直接覆盖核心文件。
5. 合并冲突时优先保留已完成主流程功能。
6. 不提交 `.env`、`node_modules`、`dist`、`__pycache__`、`*.pyc`、真实 API Key。

## 8.3 测试账号

| 角色 | 用户名 | 密码 | 用途 |
|---|---|---|---|
| 普通用户 | `user` | `123456` | 发帖、评论、搜索、推荐、阅读记录 |
| 审核编辑 | `editor` | `123456` | 审核、社区管理、Timeline 编辑 |
| 管理员 | `admin` | `123456` | 后台、用户管理、数据统计 |

---

# 9. 总体验收清单

## 9.1 前端

```powershell
cd frontend
npm install
npm run build
npm run dev
```

检查：

1. 首页新闻正常显示。
2. 首页搜索可用。
3. 推荐 Tab 可用。
4. 新闻详情评论可发、可删、可点赞/取消。
5. 社区可发帖，帖子立即显示。
6. 社区热搜风格统一。
7. 社区 AI 助手有 loading，有真实/兜底回答。
8. 个人中心浏览历史、收藏、AI 记录、阅读脉络可进入。
9. 管理后台能跳转，数据真实。

## 9.2 后端

```powershell
python -m py_compile backend/app/db/database.py
python -m py_compile backend/app/modules/admin/service.py
python -m py_compile backend/app/modules/community/service.py
python -m py_compile backend/app/modules/news/service.py
python -m py_compile backend/app/modules/profile/service.py
python -m py_compile backend/app/modules/timeline/service.py
```

检查：

1. Swagger 正常打开。
2. 数据库连接池正常。
3. 管理后台接口返回真实数据。
4. 搜索接口返回正确结果。
5. 社区发帖/评论/点赞接口正常。
6. Timeline 接口有 status。
7. AI 助手接口有 fallback。

## 9.3 数据库

```sql
SELECT COUNT(*) FROM user;
SELECT COUNT(*) FROM news;
SELECT COUNT(*) FROM community_post;
SELECT COUNT(*) FROM news_comment;
SELECT COUNT(*) FROM user_like;
```

## 9.4 AI 服务

检查：

1. Mock 模式可用。
2. LLM 模式有 key 时可用。
3. LLM 不可用时 fallback。
4. 日志能区分 MOCK MODE、REAL API、ERROR。

## 9.5 爬虫

检查：

1. 爬虫能正常运行。
2. 不再大量重复默认图。
3. 图片可保存到 `/uploads/covers/`。
4. 前端图片不再大量 403。

---

# 10. 最终建议

当前阶段不要继续盲目增加功能。最重要的是让系统形成稳定闭环：

```text
新闻能搜 → 新闻能看 → 评论能互动 → 社区能发帖 → AI 能辅助 → 后台能管理 → 数据能真实展示
```

六条线并发时，优先保证：

1. 社区主流程可用。
2. 管理后台真实数据。
3. 搜索功能打通。
4. AI 结果不假、不慢、不黑盒。
5. 爬虫图片不污染数据库。
6. Timeline 和阅读脉络先可用，再美化。
