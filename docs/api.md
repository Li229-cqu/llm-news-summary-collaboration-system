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
| GET | `/api/news/categories` | 获取新闻分类。 |
| GET | `/api/news` | 获取新闻列表。 |
| GET | `/api/news/hot` | 获取新闻热榜。 |
| GET | `/api/news/search` | 搜索新闻。 |
| GET | `/api/news/{news_id}` | 获取新闻详情。 |
| POST | `/api/news/{news_id}/browse` | 记录新闻浏览。 |

### 新闻互动模块 `interaction`

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| POST | `/api/news/{news_id}/like` | 点赞新闻。 |
| POST | `/api/news/{news_id}/favorite` | 收藏新闻。 |
| GET | `/api/news/{news_id}/comments` | 获取新闻评论。 |
| POST | `/api/news/{news_id}/comments` | 发布新闻评论。 |

### AI 生成模块 `ai`

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| POST | `/api/ai/generate` | 后端转发 AI 标题摘要生成请求。 |
| POST | `/api/ai/extract` | 抽取新闻要素。 |
| POST | `/api/ai/check` | 进行一致性质量校验。 |
| POST | `/api/ai/chat` | AI 新闻助手问答。 |

### 社区模块 `community`

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/community/posts` | 获取社区帖子流。 |
| POST | `/api/community/posts` | 发布社区帖子。 |
| GET | `/api/community/hot-topics` | 获取社区热门话题。 |
| GET | `/api/community/hot-search` | 获取社区热搜。 |
| POST | `/api/community/ai-chat` | 社区 AI 助手对话。 |

### 个人中心模块 `profile`

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/profile/overview` | 获取个人中心概览。 |
| GET | `/api/profile/browse-history` | 获取浏览记录。 |
| GET | `/api/profile/favorites` | 获取收藏记录。 |
| GET | `/api/profile/comments` | 获取评论记录。 |
| GET | `/api/profile/posts` | 获取发帖记录。 |
| GET | `/api/profile/ai-records` | 获取 AI 生成记录。 |

### 管理后台模块 `admin`

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/admin/dashboard` | 获取后台概览数据。 |
| GET | `/api/admin/pending-posts` | 获取待审核帖子。 |
| GET | `/api/admin/users` | 获取用户管理列表。 |
| GET | `/api/admin/system-config` | 获取系统配置。 |

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
