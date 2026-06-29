# 《基于大语言模型的智能新闻摘要与协同互动系统》后端服务

## 一、后端项目说明

`backend` ???????????????? FastAPI ???????????????????????????????????????????????????????????????mock ??????????? MySQL ?????????????? mock ???????????

## 二、技术栈

- FastAPI
- Uvicorn
- Pydantic
- python-dotenv
- httpx

## 三、目录结构说明

```text
app/
├─ main.py           # 后端服务入口
├─ core/             # 配置文件
├─ common/           # 统一响应和异常处理
├─ modules/          # 业务模块
└─ mock/             # 前期 mock 数据
```

## 四、当前已完成内容

1. FastAPI 项目初始化
2. CORS 配置
3. 统一响应格式
4. 统一异常处理
5. 健康检查接口
6. 业务模块路由占位
7. Pydantic Schema 占位
8. Mock 数据目录占位
9. Mock 用户认证与权限校验
10. 新闻 mock 数据
11. 新闻查询接口
12. 新闻互动接口（数据库优先，mock 兜底）
13. 个人中心接口（数据库优先，mock 兜底）

## 五、运行方式

建议先启用本项目的独立虚拟环境：

```powershell
.\.venv\Scripts\Activate.ps1
```

安装依赖：

```bash
pip install -r requirements.txt
```

启动服务：

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

## 六、接口文档访问

- Swagger 文档：<http://127.0.0.1:8000/docs>
- ReDoc 文档：<http://127.0.0.1:8000/redoc>
- 健康检查：<http://127.0.0.1:8000/api/health>

## 七、当前注意事项

1. 当前不连接数据库。
2. 当前不实现真实登录。
3. 当前不实现真实新闻、AI、社区业务。
4. 当前不调用 AI 服务。
5. 当前只完成后端基础框架与新闻模块 mock 联调。

## 八、成员 A 已完成的后端能力

成员 A 的新闻模块当前已具备：

- 新闻 mock 数据
- 新闻查询接口
- 新闻详情接口
- 浏览记录接口
- 新闻点赞接口
- 新闻取消点赞接口
- 新闻收藏接口
- 新闻取消收藏接口
- 评论列表接口
- 发布评论接口
- 回复评论接口
- 评论点赞接口

当前互动数据为进程内 mock，服务重启后不会持久化。

## 九、下一阶段

后续将继续完善 AI 服务联动、社区模块、个人中心模块和管理员后台，并逐步接入真实数据库。


## 个人中心模块补充说明

- 当前个人中心接口已支持浏览历史、收藏记录、评论记录和 AI 生成记录。
- 个人中心数据优先从数据库读取，数据库不可用时回退 mock。
- 个人中心新增 `/api/profile/comments` 接口用于评论记录展示。

## AI 生成记录补充说明

- `POST /api/ai/generate` 在调用 ai-service 成功后，会同步写入 `ai_generate_record` 表。
- `GET /api/ai/records`、`GET /api/profile/ai-records` 都会优先读取数据库，数据库异常时回退 mock。
- AI 生成记录中会保存 `source`、`source_news_id`、`source_title`、`input_text`、`candidate_titles`、`summary_short`、`summary_long` 等字段，便于个人中心查看真实历史。

## Timeline 模块补充说明

- Timeline 当前已切换为数据库优先、mock 兜底。
- 话题列表、话题新闻和时间线缓存均优先读取数据库表。
- ai-service 不可用时，后端会自动使用本地规则生成时间线，保证抽屉可展示。

## 社区模块补充说明

- 当前社区模块已经切换为数据库优先、mock 兜底。
- `community_post`、`post_comment`、`user_like`、`favorite`、`user_block`、`hot_topic` 优先从 MySQL 读取与写入。
- 数据库暂时为空或异常时，会自动回退到 `backend/app/mock/community.py` 的 mock 数据，便于课程项目演示。
- 社区评论接口当前支持 `media_json` 富媒体字段，可用于保存评论中的图片、表情等内容。
- 社区页面仍然通过 backend 访问，不直接连接数据库。
## DB10 登录鉴权数据库优先说明

- `POST /api/auth/login` 优先查询 `user` 表，查询失败或数据库异常时回退 mock 用户逻辑。
- `GET /api/auth/me` 优先从 `user` 表读取当前用户信息，数据库异常时回退 mock token 兼容逻辑。
- `GET /api/auth/check-login`、`GET /api/auth/check-editor`、`GET /api/auth/check-admin` 仍兼容 `mock-token-user`、`mock-token-editor`、`mock-token-admin`。
- 当前阶段仍然不引入真实 JWT，不修改前端存 token 的逻辑，不改变接口返回结构。
- 数据库异常时认证模块会自动 fallback 到 mock 用户，保证项目可演示。
## DB12 新闻真实数据字段说明

- `news.source_url` 用于保存 RSS 原文链接。
- `news.cover_image` 用于保存新闻封面图 URL，当前只保存远程图片地址，不下载图片文件。
- `news.content` 保存正文文本；爬虫会尽量过滤侧边栏、推荐阅读、广告、上一篇/下一篇等非正文内容。
- 新闻接口仍然保持数据库优先、mock 兜底；数据库异常时不会影响基础演示。
- 如果本地数据库缺少 `source_url` 字段，请先执行：

```powershell
cmd /c "mysql --default-character-set=utf8mb4 -u llm_news_user -p llm_news_system < database\migrations\001_add_news_source_url_and_crawl_log.sql"
```

- Timeline 当前依赖 `news.topic_id` 绑定；真实爬取新闻未完成话题归类时，可能暂时没有事件脉络。
## DB12.5 首页真实数据与订阅接口补充

- `GET /api/news/categories` 优先读取数据库 `news_category`，用于前端左侧分类栏。
- `GET /api/news` 支持 `category_id` 参数，前端点击分类后会按数据库分类筛选新闻。
- `GET /api/news/hot` 优先读取数据库真实新闻，并按 `view_count + like_count * 5 + favorite_count * 4 + comment_count * 6` 生成热榜。
- 新增 `user_category_subscription` 表，用于保存用户新闻分类订阅。
- 新增 `GET /api/profile/subscriptions` 和 `POST /api/profile/subscriptions`，均需要登录。
- 数据库不可用时继续保留 mock fallback，确保课程演示不被数据库异常阻断。
## A3 验收补充说明

- 后端数据库访问层已接入 `DBUtils.PooledDB` 连接池，`get_connection()` 从连接池获取连接，`close()` 时归还连接池。
- `admin` 模块的 dashboard、用户列表、待审核帖子列表已改为数据库优先，数据库异常时保留 mock fallback。
- 管理后台接口需要 `admin` 或 `editor` 权限，`/api/admin/users` 仅 `admin` 可访问。
- 用户列表不会返回 `password` 字段。
- 管理后台待审核帖子接口实际路径为 `/api/admin/pending-posts`。

## F1 阅读脉络接口补充

- 个人中心已新增 3 个阅读脉络接口：
  - `GET /api/profile/reading-trajectory`
  - `GET /api/profile/reading-timeline`
  - `GET /api/profile/reading-heatmap`
- 这 3 个接口都需要登录，数据优先读取 `browse_history`、`news`、`news_category`、`news_topic`。
- 如果用户没有浏览历史，接口返回空结构，不回退 mock 阅读脉络。
- 当前实现只负责后端数据结构准备，不新增前端页面。
