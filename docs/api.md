# 《基于大语言模型的智能新闻摘要与协同互动系统》接口文档 V0.1

> 当前阶段说明：第 4 阶段已完成 Mock 用户认证与权限接口。用户数据均来自 Mock，不连接数据库；其余业务接口仍处于规划或占位阶段。

## 一、统一响应格式

### 成功响应

```json
{
  "code": 200,
  "message": "success",
  "data": {}
}
```

### 失败响应

```json
{
  "code": 400,
  "message": "错误信息",
  "data": null
}
```

## 二、用户认证与权限 Mock

### 角色说明

| 角色 | 说明 |
| --- | --- |
| `user` | 普通用户。 |
| `editor` | 审核/编辑。 |
| `admin` | 管理员。 |

### 测试账号

| 角色 | 用户名 | 密码 | Mock Token |
| --- | --- | --- | --- |
| 普通用户 | `user` | `123456` | `mock-token-user` |
| 审核编辑 | `editor` | `123456` | `mock-token-editor` |
| 管理员 | `admin` | `123456` | `mock-token-admin` |

### 认证请求头

需要登录的接口应携带以下请求头：

```text
Authorization: Bearer mock-token-user
```

### POST `/api/auth/login`

用户 Mock 登录。

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

Mock 退出登录。当前不保存服务端会话状态，前端应清理本地 Token 与用户信息。

成功响应示例：

```json
{
  "code": 200,
  "message": "退出登录成功",
  "data": null
}
```

### GET `/api/auth/me`

获取当前登录用户信息。需要携带 `Authorization: Bearer <mock-token>` 请求头。

Token 缺失或无效时返回：

```json
{
  "code": 401,
  "message": "未登录或登录状态已失效",
  "data": null
}
```

### GET `/api/auth/check-login`

登录状态校验。需要已登录用户访问。

### GET `/api/auth/check-editor`

编辑权限校验。仅允许 `editor` 或 `admin` 访问。

### GET `/api/auth/check-admin`

管理员权限校验。仅允许 `admin` 访问。

### GET `/api/admin/ping`

管理模块路由注册测试。仅允许 `editor` 或 `admin` 访问。

无权限时返回：

```json
{
  "code": 403,
  "message": "当前账号无权限访问该资源",
  "data": null
}
```

## 三、系统健康检查接口

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/health` | 后端服务健康检查。 |

## 四、接口模块规划

以下接口作为当前或后续模块的路径规划。除认证 Mock、健康检查和模块 Ping 接口外，请求参数、响应字段和权限规则将在后续模块开发阶段完善。

### 新闻模块 `news`

| 方法 | 路径 | 说明 |
| --- | --- | --- |
> 当前新闻数据来自 `backend/app/mock/news.py`，不连接数据库。新闻列表和新闻详情允许未登录访问；只有携带有效 Mock Token 时，新闻详情中的 `is_liked`、`is_favorited` 才可能为 `true`。点赞、收藏、评论接口将在 A3 阶段实现。

### GET `/api/news/categories`

获取启用的新闻分类，并按分类排序值升序返回。

### GET `/api/news`

获取新闻列表，支持分类、关键词和分页查询。当前只返回 `status=1` 的新闻。

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `category` | string | 否 | 新闻分类编码或分类名称，例如 `technology`、`科技`。 |
| `keyword` | string | 否 | 关键词，可匹配标题、摘要、正文、分类和标签。 |
| `page` | integer | 否 | 页码，默认 `1`。 |
| `page_size` | integer | 否 | 每页数量，默认 `10`。 |

响应 `data` 包含 `list`、`total`、`page`、`page_size`。

### GET `/api/news/hot`

获取新闻热榜。当前根据浏览量、评论数和点赞数综合排序。

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `limit` | integer | 否 | 返回数量，默认 `10`。 |

每条热榜数据包含 `id`、`title`、`category_name`、`source`、`view_count`、`comment_count`、`rank`。

### GET `/api/news/search`

搜索新闻，复用新闻列表的关键词匹配规则。空关键词返回空分页结果。

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `keyword` | string | 是 | 搜索关键词。 |
| `page` | integer | 否 | 页码，默认 `1`。 |
| `page_size` | integer | 否 | 每页数量，默认 `10`。 |

### GET `/api/news/{news_id}`

获取新闻详情，允许未登录访问。响应 `data` 除新闻完整字段外，还包含：

| 字段 | 说明 |
| --- | --- |
| `content` | 新闻正文。 |
| `related_news` | 同分类相关文章，当前最多 3 条。 |
| `recommended_news` | 推荐阅读，当前最多 5 条。 |
| `is_liked` | 当前用户是否已点赞；无有效 Token 时为 `false`。 |
| `is_favorited` | 当前用户是否已收藏；无有效 Token 时为 `false`。 |

新闻不存在时返回：

```json
{
  "code": 404,
  "message": "新闻不存在",
  "data": null
}
```

### POST `/api/news/{news_id}/browse`

记录新闻浏览行为，允许未登录调用；当前阶段使用 Mock 数据并返回成功状态。

响应示例：

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

### 新闻互动模块 `interaction`

> 当前互动数据来自 `backend/app/mock/news.py` 和 `backend/app/mock/comments.py`，不连接数据库。点赞、收藏、评论操作仅做内存级 Mock 更新，服务重启后更新会丢失。未登录访问互动写操作返回 `401`；新闻或评论不存在返回 `404`。后续接入数据库时接口路径保持不变，主要替换 `service.py` 的数据来源。

### POST `/api/news/{news_id}/like`

点赞新闻，需要登录。

### DELETE `/api/news/{news_id}/like`

取消点赞新闻，需要登录。

### POST `/api/news/{news_id}/favorite`

收藏新闻，需要登录。

### DELETE `/api/news/{news_id}/favorite`

取消收藏新闻，需要登录。

### GET `/api/news/{news_id}/comments`

获取新闻评论，允许未登录访问。响应按一级评论和 `replies` 回复列表组成树形结构；有有效 Token 时，每条评论可返回当前用户的 `is_liked` 状态，无 Token 或无效 Token 时为 `false`。

### POST `/api/news/{news_id}/comments`

发布新闻一级评论，需要登录。

请求示例：

```json
{
  "content": "评论内容"
}
```

`content` 去除首尾空格后不能为空。

### POST `/api/comments/{comment_id}/reply`

回复评论，需要登录。

请求示例：

```json
{
  "content": "回复内容"
}
```

`content` 去除首尾空格后不能为空。

### POST `/api/comments/{comment_id}/like`

点赞评论，需要登录。

### AI 生成模块 `ai`

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| POST | `/api/ai/generate` | 后端转发 AI 标题摘要生成请求。 |
| POST | `/api/ai/extract` | 抽取新闻要素。 |
| POST | `/api/ai/check` | 进行一致性质量校验。 |
| POST | `/api/ai/chat` | AI 新闻助手问答。 |

### 社区模块 `community`

> 当前社区数据来自 Mock，不连接数据库。发帖、评论、点赞操作仅做内存级 Mock 更新，服务重启后更新会丢失。

#### GET `/api/community/posts`

获取社区帖子流，支持分页。

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `page` | integer | 否 | 页码，默认 `1`。 |
| `page_size` | integer | 否 | 每页数量，默认 `10`，最大 `100`。 |

成功响应示例：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "list": [
      {
        "id": 1,
        "title": "如何看待 AI 新闻摘要？",
        "content": "欢迎交流智能摘要在新闻阅读中的作用。",
        "author": "新闻读者",
        "author_id": 1,
        "created_at": "2026-06-23 10:30:00",
        "updated_at": "2026-06-23 10:30:00",
        "likes": 15,
        "comments": 5,
        "views": 120,
        "tags": ["AI", "新闻"]
      }
    ],
    "total": 2,
    "page": 1,
    "page_size": 10
  }
}
```

#### POST `/api/community/posts`

发布社区帖子。

请求示例：

```json
{
  "title": "我的新帖子",
  "content": "帖子内容",
  "tags": ["标签1", "标签2"]
}
```

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `title` | string | 是 | 帖子标题，1-200 字符。 |
| `content` | string | 是 | 帖子内容，1-5000 字符。 |
| `tags` | array | 否 | 标签列表。 |

#### GET `/api/community/posts/{post_id}`

获取帖子详情。

#### POST `/api/community/posts/{post_id}/comments`

发布评论。

请求示例：

```json
{
  "content": "评论内容"
}
```

#### GET `/api/community/posts/{post_id}/comments`

获取帖子评论列表，支持分页。

#### POST `/api/community/posts/{post_id}/like`

点赞/取消点赞帖子。

成功响应示例：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "success": true,
    "liked": true,
    "count": 16
  }
}
```

#### GET `/api/community/hot-search`

获取社区热搜 Top10。

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `limit` | integer | 否 | 返回数量，默认 `10`，最大 `20`。 |

成功响应示例：

```json
{
  "code": 200,
  "message": "success",
  "data": [
    {
      "id": 1,
      "keyword": "AI新闻摘要",
      "rank": 1,
      "search_count": 12580,
      "trend": "up"
    }
  ]
}
```

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `trend` | string | 趋势，`up` 上升、`down` 下降、`stable` 稳定。 |

#### POST `/api/community/ai-helper`

社区 AI 新闻助手问答。

请求示例：

```json
{
  "question": "什么是新闻摘要？"
}
```

成功响应示例：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "success": true,
    "message": "success",
    "answer": "AI新闻摘要功能可以帮助您快速了解新闻核心内容，节省阅读时间。"
  }
}
```

### 个人中心模块 `profile`

> 当前个人中心数据来自 Mock，需要登录用户访问。

#### GET `/api/profile/overview`

获取个人中心概览数据。

成功响应示例：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "user_id": 1,
    "browse_count": 12,
    "favorite_count": 3,
    "comment_count": 2,
    "ai_generate_count": 1
  }
}
```

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `user_id` | int | 用户 ID |
| `browse_count` | int | 浏览记录数 |
| `favorite_count` | int | 收藏数 |
| `comment_count` | int | 评论数 |
| `ai_generate_count` | int | AI 生成次数 |

#### GET `/api/profile/browse-history`

获取用户浏览历史，支持分页。

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `page` | integer | 否 | 页码，默认 `1`。 |
| `page_size` | integer | 否 | 每页数量，默认 `10`，最大 `50`。 |

成功响应示例：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "list": [
      {
        "news_id": 4,
        "title": "科研团队发布新型量子计算控制方案",
        "category_name": "科技",
        "browse_time": "2026-06-23 10:30:00"
      }
    ],
    "total": 1,
    "page": 1,
    "page_size": 10
  }
}
```

#### GET `/api/profile/favorites`

获取用户收藏列表，支持分页。

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `page` | integer | 否 | 页码，默认 `1`。 |
| `page_size` | integer | 否 | 每页数量，默认 `10`，最大 `50`。 |

成功响应示例：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "list": [
      {
        "news_id": 2,
        "title": "社区共享阅读空间扩容",
        "summary": "随着一批社区共享阅读空间完成升级开放...",
        "category_name": "社会",
        "source": "城市观察",
        "publish_time": "2026-06-23 10:10"
      }
    ],
    "total": 1,
    "page": 1,
    "page_size": 10
  }
}
```

#### GET `/api/profile/ai-records`

获取用户 AI 生成记录，支持分页。

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `page` | integer | 否 | 页码，默认 `1`。 |
| `page_size` | integer | 否 | 每页数量，默认 `10`，最大 `50`。 |

成功响应示例：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "list": [
      {
        "id": 1,
        "input_text": "人工智能技术应用持续拓展。",
        "candidate_titles": ["人工智能应用加速落地", "AI 技术拓展行业场景"],
        "summary_short": "人工智能应用范围持续扩大。",
        "summary_long": null,
        "create_time": null
      }
    ],
    "total": 1,
    "page": 1,
    "page_size": 10
  }
}
```

### 管理后台模块 `admin`

> 需要 `editor` 或 `admin` 权限访问，部分接口仅允许 `admin` 访问。

#### GET `/api/admin/dashboard`

获取后台概览数据。允许 `editor` 或 `admin` 访问。

成功响应示例：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "user_count": 3,
    "news_count": 12,
    "post_count": 5,
    "pending_count": 2
  }
}
```

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `user_count` | int | 用户总数 |
| `news_count` | int | 新闻数量 |
| `post_count` | int | 社区帖子数 |
| `pending_count` | int | 待审核数量 |

#### GET `/api/admin/pending-posts`

获取待审核帖子列表。允许 `editor` 或 `admin` 访问。

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `page` | integer | 否 | 页码，默认 `1`。 |
| `page_size` | integer | 否 | 每页数量，默认 `10`，最大 `50`。 |

#### GET `/api/admin/users`

获取用户管理列表。**仅允许 `admin` 访问**。

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `page` | integer | 否 | 页码，默认 `1`。 |
| `page_size` | integer | 否 | 每页数量，默认 `10`，最大 `50`。 |

成功响应示例：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "list": [
      {
        "id": 1,
        "username": "user",
        "nickname": "普通用户",
        "role": "user",
        "status": 1
      }
    ],
    "total": 3,
    "page": 1,
    "page_size": 10
  }
}
```

#### GET `/api/admin/system-config`

获取系统配置。**仅允许 `admin` 访问**。

成功响应示例：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "site_name": "智能新闻摘要系统",
    "site_description": "基于大语言模型的智能新闻摘要与协同互动系统",
    "max_upload_size": 10,
    "default_page_size": 10,
    "ai_service_enabled": true,
    "auto_approve_enabled": false
  }
}
```

## 五、AI 服务接口

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/ai/health` | AI 服务健康检查。 |
| POST | `/ai/generate-title-summary` | 标题摘要生成 Mock。 |
| POST | `/ai/extract-elements` | 关键词与新闻要素抽取 Mock。 |
| POST | `/ai/check-consistency` | 一致性质量校验 Mock。 |
| POST | `/ai/chat` | AI 新闻助手问答 Mock。 |

## 六、当前注意事项

1. 当前认证和权限接口仅使用 Mock 用户数据，不连接数据库。
2. 当前 AI 服务只返回 Mock 数据，不调用真实大语言模型。
3. 后续将逐步补充业务接口实现、数据库数据访问和真实权限机制。
