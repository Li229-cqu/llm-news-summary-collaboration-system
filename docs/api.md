# 《基于大语言模型的智能新闻摘要与协同互动系统》接口文档 V0.1

> 当前阶段说明：第 4 阶段已完成 mock 用户认证与权限接口，第 5/6/7 阶段接口已逐步接入新闻、新闻详情与新闻互动能力。当前所有数据均来自 mock，不连接数据库。

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

新闻数据来自 `backend/app/mock/news.py`，不连接数据库。新闻列表和新闻详情允许未登录访问。

### 接口列表

| 方法 | 路径 | 是否需要登录 | 说明 | 当前 mock 数据来源 |
| --- | --- | --- | --- | --- |
| GET | `/api/news/categories` | 否 | 获取新闻分类 | `backend/app/mock/news.py` |
| GET | `/api/news` | 否 | 获取新闻列表 | `backend/app/mock/news.py` |
| GET | `/api/news/hot` | 否 | 获取新闻热榜 Top10 | `backend/app/mock/news.py` |
| GET | `/api/news/search` | 否 | 搜索新闻 | `backend/app/mock/news.py` |
| GET | `/api/news/{news_id}` | 否 | 获取新闻详情 | `backend/app/mock/news.py` + `backend/app/mock/comments.py` |
| POST | `/api/news/{news_id}/browse` | 否 | 记录浏览行为 | `backend/app/mock/news.py` |

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
- 当前排序依据 `view_count`、`comment_count`、`like_count` 综合计算。

### GET `/api/news/search`

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

互动数据来自 `backend/app/mock/news.py` 和 `backend/app/mock/comments.py`。点赞、收藏、评论当前只做内存级 mock 更新，服务重启后会丢失。未登录写操作返回 `401`，新闻或评论不存在返回 `404`。

### 接口列表

| 方法 | 路径 | 是否需要登录 | 说明 | 当前 mock 数据来源 |
| --- | --- | --- | --- | --- |
| POST | `/api/news/{news_id}/like` | 是 | 点赞新闻 | `backend/app/mock/news.py` |
| DELETE | `/api/news/{news_id}/like` | 是 | 取消点赞新闻 | `backend/app/mock/news.py` |
| POST | `/api/news/{news_id}/favorite` | 是 | 收藏新闻 | `backend/app/mock/news.py` |
| DELETE | `/api/news/{news_id}/favorite` | 是 | 取消收藏新闻 | `backend/app/mock/news.py` |
| GET | `/api/news/{news_id}/comments` | 否 | 获取新闻评论 | `backend/app/mock/comments.py` |
| POST | `/api/news/{news_id}/comments` | 是 | 发布新闻评论 | `backend/app/mock/comments.py` |
| POST | `/api/comments/{comment_id}/reply` | 是 | 回复评论 | `backend/app/mock/comments.py` |
| POST | `/api/comments/{comment_id}/like` | 是 | 点赞评论 | `backend/app/mock/comments.py` |

### 评论接口说明

- `GET /api/news/{news_id}/comments` 允许未登录访问，返回一级评论和 `replies` 树形结构。
- 评论列表当前从 `MOCK_NEWS_COMMENTS` 组装而来。

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

当前互动状态来自 backend mock 接口，重启服务后内存态更新不会持久化。

## 六、AI 服务接口

AI 服务当前为独立 mock 服务，前端不直接调用，由后端按需转发或预留。

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/ai/health` | AI 服务健康检查 |
| POST | `/ai/generate-title-summary` | 标题摘要生成 |
| POST | `/ai/extract-elements` | 关键词和新闻要素抽取 |
| POST | `/ai/check-consistency` | 一致性质量校验 |
| POST | `/ai/chat` | AI 新闻助手问答 |

## 七、首页模块接口

首页当前已接入的接口：

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/news/categories` | 获取新闻分类 |
| GET | `/api/news` | 获取新闻列表 |
| GET | `/api/news/hot` | 获取新闻热榜 Top10 |
| GET | `/api/news/search` | 搜索新闻 |

说明：

- 首页数据来自 backend mock 接口。
- 当前不连接数据库。
- 首页不直接调用 ai-service。
- 点击新闻卡片会跳转到 `/news/:id`。
- AI 工具入口会跳转到 `/ai/title-summary`。

## 八、新闻详情页说明

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
