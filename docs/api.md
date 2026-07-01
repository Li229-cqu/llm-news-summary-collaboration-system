# 《基于大语言模型的智能新闻摘要与协同互动系统》接口文档 V0.1

> 当前阶段说明：第 4 阶段已完成 mock 用户认证与权限接口， 第 5/6/7 阶段接口已逐步接入新闻、新闻详情与新闻交互能力。 当前新闻列表、新闻详情、首页热榜、搜索和推荐均以数据库 `news` 表为准，不再回退 mock 新闻数据。

## 一、统一响应格式

成功响应：

```json
{
  "code": 200,
  "message": "success",
  "data": {}
}
```

失败响应：

```json
{
  "code": 400,
  "message": "错误信息",
  "data": null
}
```

## 二、用户认证与权限 Mock

当前认证与权限接口的 mock 数据来源为 `backend/app/mock/users.py`。

### 角色说明

| 角色 | 说明 |
| --- | --- |
| `user` | 普通用户 |
| `editor` | 审核/编辑 |
| `admin` | 管理员 |

### 测试账号

| 角色 | 用户名 | 密码 | Mock Token |
| --- | --- | --- | --- |
| 普通用户 | `user` | `123456` | `mock-token-user` |
| 审核编辑 | `editor` | `123456` | `mock-token-editor` |
| 管理员 | `admin` | `123456` | `mock-token-admin` |

### 请求头

需要登录的接口，请携带：

```text
Authorization: Bearer mock-token-user
```

### POST `/api/auth/login`

请求示例：

```json
{
  "username": "user",
  "password": "123456"
}
```

成功响应示例：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "token": "mock-token-user",
    "user": {
      "id": 1,
      "username": "user",
      "nickname": "普通用户",
      "role": "user",
      "avatar": "",
      "status": 1
    }
  }
}
```

失败响应示例：

```json
{
  "code": 401,
  "message": "账号或密码错误",
  "data": null
}
```

### POST `/api/auth/logout`

退出登录成功后返回：

```json
{
  "code": 200,
  "message": "退出登录成功",
  "data": null
}
```

### GET `/api/auth/me`

需要请求头：

```text
Authorization: Bearer mock-token-user
```

### GET `/api/auth/check-login`

需要登录后访问。

### GET `/api/auth/check-editor`

仅允许 `editor` 或 `admin` 访问。

### GET `/api/auth/check-admin`

仅允许 `admin` 访问。

### GET `/api/admin/ping`

管理后台测试接口，仅允许 `editor` 或 `admin` 访问。

无权限响应示例：

```json
{
  "code": 403,
  "message": "当前账号无权限访问该资源",
  "data": null
}
```

## 三、系统健康检查

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/health` | 后端服务健康检查 |

## 四、新闻模块接口

新闻列表、新闻详情、首页热榜、搜索和推荐均直接读取数据库 `news` 表；数据库无数据时列表返回空，详情查不到时返回 404，不再回退 `backend/app/mock/news.py`。新闻列表和新闻详情允许未登录访问。

### 接口列表

| 方法 | 路径 | 是否需要登录 | 说明 | 当前 mock 数据来源 |
| --- | --- | --- | --- | --- |
| GET | `/api/news/categories` | 否 | 获取新闻分类 | 直接读取数据库 `news_category` |
| GET | `/api/news` | 否 | 获取新闻列表 | 直接读取数据库 `news` + `news_category` |
| GET | `/api/news/subscribed` | 是 | 获取当前登录用户订阅分类下的新闻列表 | 直接读取数据库 `news` + `news_category` + `user_category_subscription`，不回退 mock |
| GET | `/api/news/hot` | 否 | 获取新闻热榜 Top10 | 直接读取数据库真实新闻统计，不再回退 mock |
| GET | `/api/news/search` | 否 | 搜索新闻 | 直接读取数据库 `news` + `news_category` |
| GET | `/api/news/{news_id}` | 否 | 获取新闻详情 | 数据库 `news` + `news_category` + `user_like` + `favorite`，不存在时返回 404，不回退 mock |
| POST | `/api/news/{news_id}/browse` | 否 | 记录浏览行为 | 数据库 `news` + `browse_history`，不存在时返回 404，不回退 mock |

### GET `/api/news`

请求参数：

| 参数 | 说明 |
| --- | --- |
| `category` | 分类 code 或分类名称 |
| `keyword` | 关键词 |
| `page` | 页码 |
| `page_size` | 每页数量 |

返回说明：

- 返回新闻列表、总数、页码和每页数量。
- 当前数据来自数据库 `news` 表。

### GET `/api/news/subscribed`

请求参数：

| 参数 | 说明 |
| --- | --- |
| `page` | 页码 |
| `page_size` | 每页数量 |

返回说明：

- 需要登录，未登录返回 `401`。
- 根据当前用户在 `user_category_subscription` 中订阅的 `category_id` 查询 `news` 表。
- 仅返回 `status = 1` 的新闻，按 `publish_time DESC`、`updated_at DESC` 排序。
- 用户未订阅分类或订阅分类下暂无新闻时返回空列表，不回退 mock 新闻。

### GET `/api/news/hot`

请求参数：

| 参数 | 说明 |
| --- | --- |
| `limit` | 返回条数，默认 10 |

返回说明：

- 返回热榜列表，包含 `rank` 字段。
- 当前排序依据 `view_count`、`like_count`、`favorite_count`、`comment_count` 综合计算。

请求参数：

| 参数 | 说明 |
| --- | --- |
| `keyword` | 搜索关键词 |
| `page` | 页码 |
| `page_size` | 每页数量 |

返回说明：

- 返回与关键词匹配的新闻列表。
- 当前数据来自数据库 `news` 表。

### GET `/api/news/{news_id}`

返回字段包括：

| 字段 | 说明 |
| --- | --- |
| `content` | 新闻正文 |
| `related_news` | 相关文章 |
| `recommended_news` | 推荐阅读 |
| `is_liked` | 当前用户是否点赞 |
| `is_favorited` | 当前用户是否收藏 |

说明：

- 新闻详情允许未登录访问。
- `is_liked` 和 `is_favorited` 仅在携带有效 token 时才可能为 `true`。
- 当前新闻详情页已接入数据库浏览记录接口。

### POST `/api/news/{news_id}/browse`

请求参数：

| 参数 | 说明 |
| --- | --- |
| 无 | 浏览记录接口当前阶段不需要额外请求体 |

返回示例：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "news_id": 1,
    "recorded": true
  }
}
```

说明：

- 浏览记录当前为 mock 成功。
- 当前数据来自 `MOCK_BROWSE_HISTORY`。

## 五、新闻互动模块接口

互动数据优先来自数据库中的 `news_comment`、`user_like`、`favorite` 和 `news` 表；当数据库不可用或目标数据尚未同步时，后端会回退到 `backend/app/mock/news.py` 与 `backend/app/mock/comments.py`。点赞、收藏、评论当前已支持数据库读写，mock 仅作为兜底。未登录写操作返回 `401`，新闻或评论不存在返回 `404`。

### 接口列表

| 方法 | 路径 | 是否需要登录 | 说明 | 当前 mock 数据来源 |
| --- | --- | --- | --- | --- |
| POST | `/api/news/{news_id}/like` | 是 | 点赞新闻 | 数据库 `user_like` + `news`，失败时回退 `backend/app/mock/news.py` |
| DELETE | `/api/news/{news_id}/like` | 是 | 取消点赞新闻 | 数据库 `user_like` + `news`，失败时回退 `backend/app/mock/news.py` |
| POST | `/api/news/{news_id}/favorite` | 是 | 收藏新闻 | 数据库 `favorite` + `news`，失败时回退 `backend/app/mock/news.py` |
| DELETE | `/api/news/{news_id}/favorite` | 是 | 取消收藏新闻 | 数据库 `favorite` + `news`，失败时回退 `backend/app/mock/news.py` |
| GET | `/api/news/{news_id}/comments` | 否 | 获取新闻评论 | 数据库 `news_comment` + `user_like`，失败时回退 `backend/app/mock/comments.py` |
| POST | `/api/news/{news_id}/comments` | 是 | 发布新闻评论 | 数据库 `news_comment` + `news`，失败时回退 `backend/app/mock/comments.py` |
| POST | `/api/comments/{comment_id}/reply` | 是 | 回复评论 | 数据库 `news_comment` + `news`，失败时回退 `backend/app/mock/comments.py` |
| POST | `/api/comments/{comment_id}/like` | 是 | 点赞评论 | 数据库 `user_like` + `news_comment`，失败时回退 `backend/app/mock/comments.py` |
| DELETE | `/api/comments/{comment_id}` | ? | ???? | ??? `news_comment` + `news`?????? `backend/app/mock/comments.py` |

### 评论接口说明

- `GET /api/news/{news_id}/comments` 允许未登录访问，返回一级评论和 `replies` 树形结构。
- 评论列表优先从数据库 `news_comment` 表读取，失败时回退到 `MOCK_NEWS_COMMENTS` 组装。

请求示例：

```json
{
  "content": "评论内容"
}
```

回复请求示例：

```json
{
  "content": "回复内容"
}
```

### A7 新闻详情页互动说明

新闻详情页当前已支持：

1. 点赞和取消点赞。
2. 收藏和取消收藏。
3. 评论列表展示。
4. 发布评论。
5. 回复评论。
6. 评论点赞。
7. 未登录用户进行互动时自动跳转登录页。

当前互动状态优先写入数据库；数据库不可用时回退到进程内 mock，重启服务后 mock 内存态更新不会持久化。

## 六、Timeline 多源事件脉络接口

Timeline 数据来自 `backend/app/mock/news.py` 和 `backend/app/mock/timeline.py`。后端会优先读取缓存时间线；如果缓存不存在，会调用 ai-service 的 `/ai/generate-timeline`，调用失败时使用本地 mock fallback，避免演示中断。

### 接口列表

| 方法 | 路径 | 是否需要登录 | 说明 | 当前 mock 数据来源 |
| --- | --- | --- | --- | --- |
| GET | `/api/timeline/topics` | 否 | 获取可查看事件脉络的话题列表 | `backend/app/mock/timeline.py` |
| GET | `/api/timeline/topics/{topic_id}/news` | 否 | 获取指定话题下的相关新闻列表 | `backend/app/mock/news.py` |
| GET | `/api/timeline/topics/{topic_id}` | 否 | 获取指定话题的事件脉络时间线 | `backend/app/mock/timeline.py` + `backend/app/mock/news.py` |
| POST | `/api/timeline/topics/{topic_id}/generate` | 是 | 生成指定话题的事件脉络时间线 | `backend/app/mock/timeline.py` + `backend/app/mock/news.py` |

### GET `/api/timeline/topics`

返回字段包括：

| 字段 | 说明 |
| --- | --- |
| `topic_id` | 话题 ID |
| `topic_name` | 话题名称 |
| `keyword_list` | 关键词列表 |
| `heat_score` | 热度值 |
| `summary` | 话题摘要 |
| `news_count` | 当前话题下新闻数量 |

### GET `/api/timeline/topics/{topic_id}/news`

说明：

- 返回该 `topic_id` 下的相关新闻列表。
- 列表按 `publish_time` 升序返回。
- 若话题不存在，返回 `404`。

### GET `/api/timeline/topics/{topic_id}`

说明：

- 若已有缓存时间线，直接返回缓存结果。
- 若没有缓存，后端会自动尝试生成时间线。
- 适合首页或社区入口直接预览事件脉络。

### POST `/api/timeline/topics/{topic_id}/generate`

说明：

- 需要登录后访问。
- 后端优先检查缓存；缓存不存在时调用 ai-service 的 `/ai/generate-timeline`。
- 若 ai-service 不可用，后端使用本地规则 fallback：
  - 按 `publish_time` 升序
  - 每篇新闻生成一个事件节点
  - `event_title` 使用新闻标题
  - `event_summary` 使用新闻摘要或正文前 100 字

返回字段包括：

| 字段 | 说明 |
| --- | --- |
| `topic_id` | 话题 ID |
| `topic_name` | 话题名称 |
| `timeline` | 事件节点列表 |
| `source` | `cache` / `ai-service` / `mock` |
| `generated_at` | 生成时间 |
| `updated_at` | 更新时间 |
| `generate_status` | `cached` / `generated` / `mock` |

## 七、AI 服务接口

AI 服务当前为独立 mock 服务，前端不直接调用，由后端按需转发或预留。

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/ai/health` | AI 服务健康检查 |
| POST | `/ai/generate-title-summary` | 标题摘要生成 |
| POST | `/ai/extract-elements` | 关键词和新闻要素抽取 |
| POST | `/ai/check-consistency` | 一致性质量校验 |
| POST | `/ai/chat` | AI 新闻助手问答 |

## 八、首页模块接口

首页当前已接入的接口：

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/news/categories` | 获取新闻分类 |
| GET | `/api/news` | 获取新闻列表 |
| GET | `/api/news/hot` | 获取新闻热榜 Top10 |
| GET | `/api/news/search` | 搜索新闻 |

说明：

- 首页热榜数据来自后端数据库接口。
- 首页热榜不再回退 mock，数据库无数据时返回空列表。
- 首页不直接调用 ai-service。
- 点击新闻卡片会跳转到 `/news/:id`。
- AI 工具入口会跳转到 `/ai/title-summary`。

## 九、新闻详情页说明

新闻详情页当前已接入：

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/news/{news_id}` | 获取新闻详情 |
| POST | `/api/news/{news_id}/browse` | 记录新闻浏览 |

说明：

- 新闻详情支持未登录访问。
- 页面加载后会调用数据库浏览记录接口。
- 页面展示相关文章和推荐阅读。
- 点击“用 AI 生成标题和摘要”会先把新闻信息放入 `sessionStorage` 中的 `ai_draft_from_news`，再跳转到 `/ai/title-summary?source=news&newsId=xxx`。
- 当前不直接调用 `ai-service`。
- 点赞、收藏、评论真实交互由 A7 接入。

## 十、个人中心模块接口

个人中心当前接口优先读取数据库，数据库不可用或数据未同步时回退到 mock 数据。页面侧直接调用 backend，不直接连接数据库。

| 方法 | 路径 | 是否需要登录 | 说明 | 当前 mock 数据来源 |
| --- | --- | --- | --- | --- |
| GET | `/api/profile/overview` | 是 | 获取个人中心概览统计 | `backend/app/mock/profile.py`、`backend/app/mock/news.py`、`backend/app/mock/comments.py` |
| GET | `/api/profile/browse-history` | 是 | 获取浏览历史 | `backend/app/mock/profile.py`、`backend/app/mock/news.py` |
| GET | `/api/profile/favorites` | 是 | 获取收藏记录 | `backend/app/mock/profile.py`、`backend/app/mock/news.py` |
| GET | `/api/profile/comments` | 是 | 获取评论记录 | `backend/app/mock/profile.py`、`backend/app/mock/news.py`、`backend/app/mock/comments.py` |
| GET | `/api/profile/ai-records` | 是 | 获取 AI 生成记录 | `backend/app/mock/profile.py` |

### F1 阅读脉络接口

当前个人中心已新增 3 个只读接口，用于展示用户最近的阅读行为分析。三个接口都需要登录，且数据优先从 `browse_history`、`news`、`news_category`、`news_topic` 读取；当用户没有浏览历史时，返回空结构，不回退 mock 阅读脉络。

| 方法 | 路径 | 是否需要登录 | 说明 | 当前数据来源 |
| --- | --- | --- | --- | --- |
| GET | `/api/profile/reading-trajectory` | 是 | 获取阅读脉络图，返回 `summary / nodes / edges / top_categories / top_topics / recent_news` | `browse_history`、`news`、`news_category`、`news_topic` |
| GET | `/api/profile/reading-timeline` | 是 | 获取阅读时间线，按日期聚合返回 `summary / items` | `browse_history`、`news`、`news_category`、`news_topic` |
| GET | `/api/profile/reading-heatmap` | 是 | 获取阅读热力图，返回 `x_axis / y_axis / cells / summary` | `browse_history`、`news`、`news_category`、`news_topic` |

### F1 字段说明

- `reading-trajectory`：节点分为 `category / topic / news` 三类，边分为 `category_topic / topic_news / sequence` 三类。
- `reading-timeline`：`items` 按日期倒序展示，每日包含 `categories / topics / news`。
- `reading-heatmap`：`x_axis` 为日期，`y_axis` 为分类，`cells` 为日期 × 分类聚合结果。
- 三个接口都不会返回 `password` 等敏感字段。

### 个人中心字段说明

- 浏览历史展示：新闻标题、来源分类、浏览时间。
- 收藏记录展示：新闻标题、摘要、来源、收藏时间，并可跳转新闻详情。
- 评论记录展示：评论内容、新闻标题、评论时间，并可跳转原新闻。
- AI 生成记录展示：输入文本、候选标题、生成摘要、生成时间、风险等级等信息；若当前没有记录，则返回空列表，不报错。

### AI 生成记录补充说明

- `POST /api/ai/generate` 在生成成功后会同步写入 `ai_generate_record` 表。
- `GET /api/ai/records` 与 `GET /api/profile/ai-records` 都会优先读取数据库，数据库不可用时回退 mock。
- 如果从新闻详情页导入，记录会携带 `source=news`、`source_news_id`、`source_title`，方便在个人中心查看真实来源。

## 十一、Timeline 模块接口（数据库优先）

Timeline 话题、话题新闻和时间线缓存当前优先从数据库读取；数据库不可用或数据未同步时回退到 `backend/app/mock/timeline.py` 与 `backend/app/mock/news.py`。

| 方法 | 路径 | 是否需要登录 | 说明 | 当前 mock 数据来源 |
| --- | --- | --- | --- | --- |
| GET | `/api/timeline/topics` | 否 | 获取可查看事件脉络的话题列表 | `backend/app/mock/timeline.py`、`backend/app/mock/news.py` |
| GET | `/api/timeline/topics/{topic_id}/news` | 否 | 获取某个话题下的相关新闻列表 | `backend/app/mock/news.py` |
| GET | `/api/timeline/topics/{topic_id}` | 否 | 获取指定话题的事件脉络时间线；有缓存则直接返回 | `backend/app/mock/timeline.py`、`backend/app/mock/news.py` |
| POST | `/api/timeline/topics/{topic_id}/generate` | 是 | 生成指定话题的事件脉络时间线 | `backend/app/mock/timeline.py`、`backend/app/mock/news.py` |

### Timeline 字段说明

- `topic_id`：话题 ID，对应 `news_topic.id`
- `topic_name`：话题名称
- `keyword_list`：关键词数组
- `heat_score`：话题热度
- `summary`：话题简介
- `news_count`：该话题下的新闻数量
- `timeline`：按时间顺序排列的事件节点数组
- `source`：`cache` / `ai-service` / `mock`
- `generate_status`：`cached` / `generated` / `mock`

### 当前行为

- 首页、社区、新闻详情页可以打开 Timeline 抽屉。
- Timeline 抽屉会优先读取数据库中的话题、新闻和缓存时间线。
- 若数据库没有缓存，会尝试调用 ai-service 的 `/ai/generate-timeline`。
- ai-service 不可用时，后端会使用本地规则 fallback，保证演示不中断。

## 十二、社区模块接口

社区模块当前已切换为数据库优先、mock 兜底。社区帖子、评论、点赞、收藏、拉黑和热搜话题优先从 MySQL 读取；当数据库为空或异常时，后端会回退到 `backend/app/mock/community.py` 里的 mock 数据，保证页面仍可演示。

### 接口列表

| 方法 | 路径 | 是否需要登录 | 说明 | 当前数据来源 |
| --- | --- | --- | --- | --- |
| GET | `/api/community/posts` | 否 | 获取社区帖子列表，支持 `page`、`page_size`、`keyword` | `community_post`、`user`、`news`，失败时回退 mock |
| GET | `/api/community/posts/{post_id}` | 否 | 获取社区帖子详情 | `community_post`、`user`、`news`，失败时回退 mock |
| POST | `/api/community/posts` | 是 | 发布社区帖子 | 写入 `community_post`，失败时回退 mock |
| POST | `/api/community/posts/{post_id}/like` | 是 | 点赞帖子 | `user_like` + `community_post`，失败时回退 mock |
| DELETE | `/api/community/posts/{post_id}/like` | 是 | 取消点赞帖子 | `user_like` + `community_post`，失败时回退 mock |
| POST | `/api/community/posts/{post_id}/favorite` | 是 | 收藏帖子 | `favorite` + `community_post`，失败时回退 mock |
| DELETE | `/api/community/posts/{post_id}/favorite` | 是 | 取消收藏帖子 | `favorite` + `community_post`，失败时回退 mock |
| GET | `/api/community/posts/{post_id}/comments` | 否 | 获取帖子评论树 | `post_comment` + `user`，失败时回退 mock |
| POST | `/api/community/posts/{post_id}/comments` | 是 | 发布帖子评论 | 写入 `post_comment`，失败时回退 mock |
| POST | `/api/community/comments/{comment_id}/reply` | 是 | 回复帖子评论 | 写入 `post_comment`，失败时回退 mock |
| POST | `/api/community/comments/{comment_id}/like` | 是 | 点赞帖子评论 | `user_like` + `post_comment`，失败时回退 mock |
| DELETE | `/api/community/comments/{comment_id}` | ? | ?????? | `post_comment` + `community_post`?????? mock |
| POST | `/api/community/users/{user_id}/block` | 是 | 拉黑用户 | `user_block`，失败时回退 mock |
| DELETE | `/api/community/users/{user_id}/block` | 是 | 取消拉黑用户 | `user_block`，失败时回退 mock |
| GET | `/api/community/hot-search` | 否 | 获取社区热搜话题列表 | `hot_topic`，失败时回退 mock |
| GET | `/api/community/hot-topics` | 否 | 获取社区热搜话题列表（别名） | `hot_topic`，失败时回退 mock |

### 字段说明

帖子列表和详情当前会返回与前端兼容的字段：

| 字段 | 说明 |
| --- | --- |
| `id` | 帖子 ID |
| `user_id` | 发帖用户 ID |
| `username` / `nickname` / `avatar` | 用户信息 |
| `author` | 前端兼容的作者名称 |
| `title` | 帖子标题 |
| `content` | 帖子内容 |
| `related_news_id` | 关联新闻 ID |
| `related_news_title` | 关联新闻标题 |
| `topic_id` | 关联话题 ID |
| `like_count` / `likes` | 点赞数 |
| `comment_count` / `comments` | 评论数 |
| `favorite_count` | 收藏数 |
| `heat_score` / `views` | 热度/展示用阅读数 |
| `tags` | 标签数组 |
| `liked` / `is_liked` | 当前用户是否点赞 |
| `is_favorited` | 当前用户是否收藏 |
| `is_blocked` | 当前用户是否拉黑该作者 |

评论列表会返回树形结构，支持 `replies` 字段；前端当前版本仍可直接展示一级评论。

### 当前行为说明

- 社区页面仍然只调用 backend，不直接访问数据库。
- 当数据库中已有社区帖子时，社区列表、点赞、收藏、评论、回复、拉黑等写操作优先落库。
- 当数据库暂时为空或不可用时，页面会回退到 `backend/app/mock/community.py` 的 mock 数据。
- 热搜话题优先读取 `hot_topic` 表；若数据库中没有数据，则回退 mock。
- AI 帮助入口仍保持 mock 返回，不调用真实大模型。
## DB10 锛氱櫥褰曢壌鏉冩暟鎹簱浼樺厛璇存槑

- `POST /api/auth/login` 浼樺厛鏌ヨ `user` 琛ㄣ€?
- `GET /api/auth/me` 浼樺厛浠庢暟鎹簱鏌ヨ褰撳墠鐢ㄦ埛銆?
- `GET /api/auth/check-login`銆?`GET /api/auth/check-editor`銆?`GET /api/auth/check-admin` 浠嶇户缁吋瀹?mock token 鍒版暟鎹簱 user 琛ㄣ€?
- 濡傛灉鏁版嵁搴撴煡璇㈠け璐ワ紝浼氬洖閫€鍒?mock 鐢ㄦ埛锛屼繚璇佹紨绀哄彲鐢ㄣ€?
- 鐧诲綍鎴愬姛鍚庤繑鍥炵粨鏋勪繚鎸佷笉鍙橈細`token` 鍜?`user` 淇℃伅浠嶄繚鎸佸拰鍓嶇鍏煎銆?
## DB12.5 首页真实数据与订阅接口补充

### 首页分类与热榜

- `GET /api/news/categories`：首页左侧分类栏使用该接口读取数据库 `news_category`。
- `GET /api/news?category_id=xxx`：点击左侧分类后，首页新闻列表按数据库 `news.category_id` 筛选。
- `GET /api/news/hot?limit=10`：首页右侧 Top10 使用数据库真实新闻交互统计排序，不再使用 mock 回退。

热榜综合热度计算规则：

```text
heat_score = view_count + like_count * 5 + favorite_count * 4 + comment_count * 6
```

### 订阅管理接口

| 方法 | 路径 | 是否需要登录 | 说明 |
| --- | --- | --- | --- |
| GET | `/api/profile/subscriptions` | 是 | 获取当前用户的新闻分类订阅状态 |
| POST | `/api/profile/subscriptions` | 是 | 更新当前用户订阅的新闻分类 |

`POST /api/profile/subscriptions` 请求示例：

```json
{
  "category_ids": [4, 5]
}
```

当前订阅数据优先写入数据库 `user_category_subscription`；数据库不可用时后端保留 mock fallback，确保演示不中断。
## A3 管理后台数据库化说明

- 后端数据库访问层使用 `DBUtils.PooledDB` 连接池。
- 管理后台 dashboard 和用户列表保持数据库优先，数据库异常时保留 mock fallback。
- 管理后台待审核中心读取真实数据库，不再使用 mock 数据作为审核中心数据源。
- `GET /api/admin/pending-items`、`GET /api/admin/pending-items/{item_type}/{item_id}`、`POST /api/admin/pending-items/{item_type}/{item_id}/review` 需要 `editor` 或 `admin` 权限。
- `/api/admin/users` 需要 `admin` 权限，返回数据不会包含 `password` 字段。
- `/api/admin/pending-posts` 保留为兼容旧前端的待审核帖子接口。
- 待审核中心支持 `all/news/post/comment` 分类筛选，支持 `approve/reject/fold/delete/restore` 审核动作。

## M4 Admin News Content Management

- `GET /api/admin/news/options`: returns categories, topics, sources, and whether a featured field exists. Requires `editor` or `admin`.
- `GET /api/admin/news`: returns news rows from the real `news` table. It does not use mock news fallback.
- Supported filters: `keyword`, `category_id`, `source`, `status`, `is_featured`, `has_topic`, `start_time`, `end_time`, `page`, `page_size`.
- `GET /api/admin/news/{news_id}`: returns admin news detail.
- `PUT /api/admin/news/{news_id}`: updates title, summary, content, source, category, cover image, tags, and publish time.
- `POST /api/admin/news/{news_id}/review`: updates news status with `approve/reject/fold/delete/restore`.
- `POST /api/admin/news/{news_id}/topic`: binds, changes, or clears `topic_id`.
- `POST /api/admin/news/{news_id}/feature` and `DELETE /api/admin/news/{news_id}/feature`: available only when the real `news` table has a supported featured column.
- Normal `user` receives 403, unauthenticated requests receive 401.

## M5 Admin Community Post Management

The admin backend now exposes database-backed community post management APIs. These endpoints require editor or admin permission and read/write the `community_post` table directly. Empty database results return an empty list; post list/detail/action endpoints do not use mock post fallback.

| Method | Path | Permission | Description |
| --- | --- | --- | --- |
| GET | `/api/admin/posts/options` | editor/admin | Return status options, discovered post tags, and whether the table supports a featured field. |
| GET | `/api/admin/posts` | editor/admin | Paginated community post list. Supports `keyword`, `user_id`, `username`, `status`, `tag`, `related_news_id`, `is_featured`, `start_time`, `end_time`, `page`, `page_size`. |
| GET | `/api/admin/posts/{post_id}` | editor/admin | Community post detail with user, related news, tags, counters, status and up to 5 recent comments. |
| POST | `/api/admin/posts/{post_id}/review` | editor/admin | Change post status. Supported actions: `approve`, `reject`, `fold`, `delete`, `restore`. Soft delete only. |
| POST | `/api/admin/posts/{post_id}/feature` | editor/admin | Set featured flag when the real table has a supported featured column; otherwise returns 400. |
| DELETE | `/api/admin/posts/{post_id}/feature` | editor/admin | Cancel featured flag when the real table has a supported featured column; otherwise returns 400. |

Current `community_post` schema has no featured column, so featured operations are disabled and return a clear 400 error.

## M6 Admin Comment Review

The admin backend now exposes database-backed comment review APIs. These endpoints require editor or admin permission and read/write `news_comment` and `post_comment` directly. Empty database results return an empty list; comment list/detail/action endpoints do not use mock comment fallback.

| Method | Path | Permission | Description |
| --- | --- | --- | --- |
| GET | `/api/admin/comments/options` | editor/admin | Return comment type and status options. `report_supported` is false because the current schema has no comment report table. |
| GET | `/api/admin/comments` | editor/admin | Paginated comment list. Supports `type`, `keyword`, `user_id`, `username`, `status`, `news_id`, `post_id`, `has_parent`, `start_time`, `end_time`, `page`, `page_size`. |
| GET | `/api/admin/comments/{comment_type}/{comment_id}` | editor/admin | Comment detail with context information and child replies. `comment_type` is `news` or `post`. |
| POST | `/api/admin/comments/{comment_type}/{comment_id}/review` | editor/admin | Change comment status. Supported actions: `approve`, `reject`, `fold`, `delete`, `restore`. Soft delete only. |

Current database schema has no report table/field for comments, so reported comments are shown as unsupported empty state.

## M7 Admin hot search and topic management APIs

The admin backend now exposes database-backed hot search and topic management APIs. These endpoints require `editor` or `admin` permission. They read and write the real `hot_topic`, `news_topic`, `news`, and `community_post` tables directly. Empty database results return empty lists; these M7 endpoints do not use mock hot/topic fallback.

### Hot search management

| Method | Path | Permission | Description |
| -- | -- | -- | -- |
| GET | `/api/admin/hot-topics/options` | editor/admin | Return target type options, status options, and capability support. |
| GET | `/api/admin/hot-topics` | editor/admin | Paginated hot search list. Supports `keyword`, `hot_type`, `target_type`, `status`, `is_pinned`, `is_hidden`, `start_time`, `end_time`, `page`, `page_size`. |
| GET | `/api/admin/hot-topics/{hot_id}` | editor/admin | Hot search detail with related news/post/topic target summary. Missing target returns `target_missing=true`, not 500. |
| POST | `/api/admin/hot-topics/{hot_id}/rank` | editor/admin | Update `rank_no`. Requires positive integer `rank_no`. |
| POST | `/api/admin/hot-topics/{hot_id}/pin` | editor/admin | Pin hot item only when the real table has a supported pin column; otherwise returns 400. |
| DELETE | `/api/admin/hot-topics/{hot_id}/pin` | editor/admin | Cancel pin only when supported; otherwise returns 400. |
| POST | `/api/admin/hot-topics/{hot_id}/hide` | editor/admin | Hide hot item. Current schema uses `status=0` because no dedicated hidden column exists. |
| DELETE | `/api/admin/hot-topics/{hot_id}/hide` | editor/admin | Restore hot item. Current schema uses `status=1`. |
| POST | `/api/admin/hot-topics/{hot_id}/refresh-heat` | editor/admin | Recalculate heat from target counters where possible and update `hot_topic.heat_score`. |

Current `hot_topic` schema supports manual rank through `rank_no`. It does not include `is_pinned`, `pinned`, or `is_top`, so pin capability is reported as unsupported and direct pin calls return 400. Hide/restore is supported through the real `status` field.

### Topic management

| Method | Path | Permission | Description |
| -- | -- | -- | -- |
| GET | `/api/admin/topics/options` | editor/admin | Return topic status options and detected field support. |
| GET | `/api/admin/topics` | editor/admin | Paginated topic list. Supports `keyword`, `status`, `has_news`, `start_time`, `end_time`, `page`, `page_size`. |
| GET | `/api/admin/topics/{topic_id}` | editor/admin | Topic detail with recent related news. |
| POST | `/api/admin/topics` | editor/admin | Create topic. Body: `topic_name`, `summary`, `keyword_list`, `heat_score`, `status`. |
| PUT | `/api/admin/topics/{topic_id}` | editor/admin | Update topic fields. |
| POST | `/api/admin/topics/{topic_id}/status` | editor/admin | Enable or disable a topic through `news_topic.status`. |
| GET | `/api/admin/topics/{topic_id}/news` | editor/admin | Paginated related news list for one topic. Supports `keyword`, `status`, `page`, `page_size`. |
| GET | `/api/admin/topics/{topic_id}/candidate-news` | editor/admin | Candidate news list for binding to the topic. Supports `keyword`, `status`, `page`, `page_size`. |
| POST | `/api/admin/topics/{topic_id}/bind-news` | editor/admin | Batch bind existing news to `topic_id`. Body: `{ "news_ids": [1, 2] }`. |
| POST | `/api/admin/topics/{topic_id}/unbind-news` | editor/admin | Batch clear `news.topic_id` for selected news. Body: `{ "news_ids": [1, 2] }`. |

User role requests to `/api/admin/hot-topics` and `/api/admin/topics` return 403 through backend permission checks. Unauthenticated requests return 401.

## M8 Admin Timeline Management APIs

The admin backend now exposes database-backed timeline management APIs. These endpoints require `editor` or `admin` permission. They read and write the real `event_timeline` table, joining with `news_topic` to provide timeline generation status, cache validation, and regeneration capabilities.

### Timeline management

| Method | Path | Permission | Description |
| -- | -- | -- | -- |
| GET | `/api/admin/timelines/options` | editor/admin | Return status options, news count options, and support flags. |
| GET | `/api/admin/timelines` | editor/admin | Paginated timeline list with summary counts. Supports `keyword`, `generate_status`, `news_count_type`, `has_cache`, `cache_error`, `start_time`, `end_time`, `page`, `page_size`. |
| GET | `/api/admin/timelines/{topic_id}` | editor/admin | Full timeline detail with `timeline_nodes`, `source_news`, `cache_check` validation, and `raw_json`. |
| GET | `/api/admin/timelines/{topic_id}/source-news` | editor/admin | Paginated news items for a topic with `in_source_news_ids` indicator. Supports `keyword`, `status`, `page`, `page_size`. |
| POST | `/api/admin/timelines/{topic_id}/generate` | editor/admin | Generate timeline for a topic (requires ≥2 news). Uses AI service with local fallback. |
| POST | `/api/admin/timelines/{topic_id}/refresh` | editor/admin | Force re-generation of timeline (requires ≥2 news). |
| DELETE | `/api/admin/timelines/{topic_id}/cache` | editor/admin | Delete cached timeline from `event_timeline` table. |

### Cache validation

The `cache_check` field validates stored timeline data for consistency:
- `json_valid`: whether `timeline_json` parses as valid JSON
- `source_news_valid`: whether all `source_news_ids` exist in the `news` table
- `message`: human-readable validation summary

### Generate status values

| Value | Label | Description |
| -- | -- | -- |
| `generated` | 已生成（AI） | Successfully generated via AI service |
| `generated (fallback)` | 已生成（规则） | Generated via local rule-based fallback |
| `not_generated` | 未生成 | No timeline has been generated |
| `failed` | 生成失败 | Generation failed with error |
| `generating` | 生成中 | Generation is in progress |

### Filter news_count_type values

| Value | Description |
| -- | -- |
| `less_than_2` | Topics with fewer than 2 related news |
| `2_or_more` | Topics with 2 or more related news |

## M9 Admin User & Permission Management APIs

The admin module now exposes database-backed user management APIs with filtering, detail stats, role changes, and status management. These endpoints require `admin` permission only.

### User management

| Method | Path | Permission | Description |
| -- | -- | -- | -- |
| GET | `/api/admin/users/options` | admin | Return role options, status options, and capability info. `last_login_supported` is false because the current `user` table has no `last_login_time` column. |
| GET | `/api/admin/users` | admin | Paginated user list with summary counts. Supports `keyword`, `role`, `status`, `start_time`, `end_time`, `page`, `page_size`. No mock fallback. |
| GET | `/api/admin/users/{user_id}` | admin | User detail with behavior statistics (post count, comment count, AI generation count, browse count, favorite count). |
| POST | `/api/admin/users/{user_id}/role` | admin | Change user role. Allowed roles: `user`, `editor`, `admin`. Cannot change own role. Cannot remove the last active admin. |
| POST | `/api/admin/users/{user_id}/status` | admin | Enable (status=1) or disable (status=0) user account. Cannot disable self. Cannot disable the last active admin. |

### Behavior statistics

The detail endpoint aggregates activity counts from `community_post`, `news_comment`, `post_comment`, `ai_generate_record`, `browse_history`, and `favorite` tables grouped by `user_id`.

### Last login time

The current `user` schema does not include a `last_login_time` column. The `/users/options` endpoint reports `last_login_supported: false` to inform the frontend. The detail endpoint does not include this field.

### Password reset

Password reset is not yet implemented and will be added in a subsequent phase.

All M9 endpoints return 403 for non-admin roles and 401 for unauthenticated requests. There is no mock data fallback for any M9 endpoint.

## M10 System Config & AI Model Rules Management APIs

The admin module now exposes database-backed system configuration and AI model rules management APIs. All M10 endpoints require `admin` permission. The old hardcoded mock `get_system_config()` has been replaced by `system_config` table-backed endpoints.

### System Config

| Method | Path | Permission | Description |
| -- | -- | -- | -- |
| GET | `/api/admin/system-config` | admin | List all system config items from the `system_config` table. Returns `SystemConfigListResponse` with items and total. |
| PUT | `/api/admin/system-config` | admin | Update editable config items. Body: `{ items: [{ config_key, config_value }] }`. Only rows with `editable=1` are updated. |

### AI Config

| Method | Path | Permission | Description |
| -- | -- | -- | -- |
| GET | `/api/admin/ai-config` | admin | Get AI configuration aggregated from `system_config` table (`ai.*` keys). The `api_key` field is never returned; only `api_key_configured: bool` indicates whether a key is set. Also returns `risk_threshold_low`, `risk_threshold_medium`, `sensitive_words`, `risk_rules`, and `fallback_strategy`. |
| PUT | `/api/admin/ai-config` | admin | Update AI configuration fields. If `api_key` is provided and non-empty, it is stored; empty means no change. |
| POST | `/api/admin/ai-config/test` | admin | Test AI service connection by calling `{service_url}/health` with a 5s timeout. Returns status, latency_ms, and message. |

### Prompt Templates

| Method | Path | Permission | Description |
| -- | -- | -- | -- |
| GET | `/api/admin/prompt-templates/options` | admin | Return function type list for filter dropdown. |
| GET | `/api/admin/prompt-templates` | admin | Paginated list with filters: `function_type`, `status`, `keyword`, `page`, `page_size`. Backed by `ai_prompt_template` table. |
| GET | `/api/admin/prompt-templates/{id}` | admin | Single template detail. |
| POST | `/api/admin/prompt-templates` | admin | Create a new template. If `is_default=1`, clears default flag on other templates of same `function_type`. |
| PUT | `/api/admin/prompt-templates/{id}` | admin | Update an existing template. |
| POST | `/api/admin/prompt-templates/{id}/status` | admin | Enable (status=1) or disable (status=0) a template. |
| POST | `/api/admin/prompt-templates/{id}/default` | admin | Set a template as the default for its `function_type`; clears default on other templates of same type. Also forces `status=1`. |

### AI Call Records

| Method | Path | Permission | Description |
| -- | -- | -- | -- |
| GET | `/api/admin/ai-call-records` | admin | Paginated list of AI generation records from `ai_generate_record` JOIN `user`. Supports `function_type`, `status`, `risk_level`, `is_fallback`, `user_id`, `start_time`, `end_time`, `page`, `page_size`. Summary includes `total_count`, `today_count`, and `fallback_count`. |

All M10 endpoints return 403 for non-admin roles and 401 for unauthenticated requests. There is no mock data fallback for any M10 endpoint.

## M11 System Operations and Operation Log APIs

M11 adds admin-only system operation APIs. All endpoints below require `admin` permission. Unauthenticated requests return 401; `editor` and normal `user` return 403.

| Method | Path | Permission | Description |
| -- | -- | -- | -- |
| GET | `/api/admin/ops/status` | admin | Check backend availability, execute real database lightweight query `SELECT 1`, and return AI service as `unknown` unless a reliable health check is configured. |
| GET | `/api/admin/ops/database` | admin | Return database name, connection status, important table existence and row counts. Missing tables are returned with `exists=false` and `row_count=null`. |
| GET | `/api/admin/ops/backups` | admin | Paginated backup records from `backup_record`. Supports `status`, `backup_type`, `start_time`, `end_time`, `page`, `page_size`. |
| POST | `/api/admin/ops/backups` | admin | Record a manual backup request. If no backup script is configured, returns and records `unsupported`; it does not run restore or delete files. |
| GET | `/api/admin/ops/storage` | admin | Return upload storage statistics from `upload_file` if available; otherwise returns `supported=false`. It does not scan the whole disk. |
| GET | `/api/admin/ops/logs` | admin | Paginated operation logs from `admin_operation_log`. Supports `operator_keyword`, `module`, `action`, `result`, `start_time`, `end_time`, `page`, `page_size`. |
| GET | `/api/admin/ops/logs/{log_id}` | admin | Operation log detail. |

New migrations:

- `database/migrations/015_create_admin_operation_log.sql`
- `database/migrations/016_create_backup_record.sql`

M11 operation data is not frontend mock data. Runtime status comes from real checks or `unknown`; database table counts come from SQL; backup records come from `backup_record`; logs come from `admin_operation_log`.

---

## M12: Data Analytics & Content Overview APIs

M12 adds admin-only analytics dashboard APIs. All endpoints below require `admin` permission. Unauthenticated requests return 401; `editor` and normal `user` return 403.

### Endpoint Summary

| Method | Path | Permission | Description |
|--------|------|-----------|-------------|
| GET | `/api/admin/analytics/overview` | admin | Core metrics: total_users, active_users, total_news, total_posts, total_comments, ai_generate_count, timeline_count, pending_count |
| GET | `/api/admin/analytics/trends` | admin | Daily content growth trend (news/posts/comments) + AI usage trend (calls/fallback/high-risk) |
| GET | `/api/admin/analytics/top-content` | admin | Top news (by view_count) and top posts (by heat_score) |
| GET | `/api/admin/analytics/ai-risk` | admin | AI risk level distribution (low/medium/high/unknown) from ai_generate_record |
| GET | `/api/admin/analytics/review-summary` | admin | Pending counts per content type + processed counts from admin_operation_log |
| GET | `/api/admin/analytics/content-overview` | admin | Unified paginated content list across news, posts, comments, timelines, topics with jump-to support |

### Query Parameters

#### `GET /api/admin/analytics/overview`

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| start_time | string | No | Filter start (YYYY-MM-DD HH:mm:ss) |
| end_time | string | No | Filter end |

#### `GET /api/admin/analytics/trends`

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| start_time | string | No | Filter start |
| end_time | string | No | Filter end |

#### `GET /api/admin/analytics/top-content`

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| start_time | string | No | Filter start |
| end_time | string | No | Filter end |
| type | string | No | `all` (default), `news`, or `post` |
| limit | int | No | Max items (default 10, max 50) |

#### `GET /api/admin/analytics/ai-risk`

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| start_time | string | No | Filter start |
| end_time | string | No | Filter end |

#### `GET /api/admin/analytics/review-summary`

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| start_time | string | No | Filter start |
| end_time | string | No | Filter end |

#### `GET /api/admin/analytics/content-overview`

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| type | string | No | Content type filter: `news`, `post`, `comment`, `timeline`, `topic` |
| status | int | No | Status filter (0-4) |
| keyword | string | No | Keyword search on title/content |
| risk_level | string | No | Risk level filter |
| start_time | string | No | Filter start |
| end_time | string | No | Filter end |
| page | int | No | Page number (default 1) |
| page_size | int | No | Page size (default 10, max 100) |

### Response Examples

#### Overview
```json
{
  "code": 200,
  "data": {
    "total_users": 4,
    "active_users": 4,
    "total_news": 476,
    "total_posts": 56,
    "total_comments": 222,
    "ai_generate_count": 107,
    "timeline_count": 7,
    "pending_count": 15
  }
}
```

#### AI Risk
```json
{
  "code": 200,
  "data": {
    "items": [
      {"risk_level": "low", "count": 60},
      {"risk_level": "medium", "count": 20},
      {"risk_level": "high", "count": 10},
      {"risk_level": "unknown", "count": 17}
    ],
    "supported": true
  }
}
```

### Design Notes

1. All data comes from real database queries. No frontend mock data.
2. Empty tables return 0 counts or empty arrays, not errors.
3. Missing tables are handled gracefully (supported=false, count=0).
4. Content overview UNIONs across 5 tables (news, community_post, comments, event_timeline, news_topic) with unified columns for pagination.
5. Each content overview item includes a `target_tab` field for frontend jump-to-module navigation.

