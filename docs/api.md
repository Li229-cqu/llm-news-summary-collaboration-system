# 《基于大语言模型的智能新闻摘要与协同互动系统》接口文档 V0.1

> 当前阶段说明：第 4 阶段已完成 mock 用户认证与权限接口， 第 5/6/7 阶段接口已逐步接入新闻、新闻详情与新闻交互能力。 当前新闻模块已经切换为数据库优先、mock 兜底；当数据库不可用时，接口仍可回退到 mock 数据，保证项目可演示。

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

新闻数据优先来自数据库；数据库不可用或查询异常时， 新闻模块会回退到 `backend/app/mock/news.py` 与 `backend/app/mock/comments.py`。 新闻列表和新闻详情允许未登录访问。

### 接口列表

| 方法 | 路径 | 是否需要登录 | 说明 | 当前 mock 数据来源 |
| --- | --- | --- | --- | --- |
| GET | `/api/news/categories` | 否 | 获取新闻分类 | 直接读取数据库 `news_category` |
| GET | `/api/news` | 否 | 获取新闻列表 | 直接读取数据库 `news` + `news_category` |
| GET | `/api/news/hot` | 否 | 获取新闻热榜 Top10 | 直接读取数据库真实新闻统计，不再回退 mock |
| GET | `/api/news/search` | 否 | 搜索新闻 | 直接读取数据库 `news` + `news_category` |
| GET | `/api/news/{news_id}` | 否 | 获取新闻详情 | 数据库 `news` + `news_category` + `user_like` + `favorite`，失败时回退 `backend/app/mock/news.py` + `backend/app/mock/comments.py` |
| POST | `/api/news/{news_id}/browse` | 否 | 记录浏览行为 | 数据库 `news` + `browse_history`，失败时回退 `backend/app/mock/news.py` |

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
- 当前数据来自 `MOCK_NEWS`。

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
- 当前数据来自 `MOCK_NEWS`。

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
- 当前新闻详情页已接入浏览记录 mock 接口。

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
- 页面加载后会调用浏览记录 mock 接口。
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
## A3 验收补充

- 后端数据库访问层使用 `DBUtils.PooledDB` 连接池。
- 管理后台接口当前优先读取真实数据库，数据库异常时回退 mock。
- `/api/admin/dashboard`、`/api/admin/users`、`/api/admin/pending-posts` 需要管理后台权限。
- 用户列表不会返回 `password` 字段。
- 管理后台待审核帖子接口实际路径为 `/api/admin/pending-posts`。
