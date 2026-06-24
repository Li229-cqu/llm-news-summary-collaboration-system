# Phase-2 分支功能详解

## 📋 概述

**phase-2 分支** 由组员 C 和组员 D 开发，专注于实现系统的三大核心功能模块：
- 🔐 **管理后台系统**
- 💬 **社区互动平台**
- 👤 **用户资料中心**

这是完整的系统功能补充，使项目从 AI 专项工具扩展为完整的新闻社区平台。

---

## 🔐 **1. 管理后台模块（Admin）**

### 功能模块

#### 1.1 仪表盘（Dashboard）
- **概览数据**：系统整体统计信息
- **数据展示**：关键指标可视化
- **快速导航**：常用功能快捷访问

```
GET /api/admin/dashboard
└─ 返回：
   ├─ 总用户数
   ├─ 总新闻数
   ├─ 总社区贴子数
   ├─ 待审核内容数
   └─ 最近活跃数据
```

#### 1.2 待审核内容（Pending Posts）
- **内容审核**：查看待审核的新闻和社区贴子
- **批量管理**：支持批量操作（发布、拒绝、删除）
- **详情查看**：预览完整内容

```
GET /api/admin/pending-posts
└─ 返回：
   ├─ 待审核新闻列表
   ├─ 待审核社区贴子列表
   ├─ 提交人信息
   └─ 提交时间
```

#### 1.3 用户管理（Users）
- **用户列表**：查看系统所有用户
- **用户搜索**：按用户名、邮箱搜索
- **用户操作**：启用/禁用用户、查看用户信息、重置密码
- **权限管理**：分配用户角色（普通用户、编辑、管理员）

```
GET /api/admin/users
└─ 支持参数：
   ├─ page: 分页页码
   ├─ limit: 每页数量
   ├─ search: 搜索关键词
   ├─ status: 用户状态（active/inactive）
   └─ role: 用户角色筛选
```

#### 1.4 系统配置（System Config）
- **网站设置**：标题、描述、logo 等
- **功能开关**：启用/禁用特定功能
- **内容策略**：审核规则、限流配置等
- **系统参数**：超时、缓存等技术参数

```
GET /api/admin/system-config
POST /api/admin/system-config
└─ 支持修改系统参数
```

#### 1.5 权限控制
- **编辑权限**：`require_editor_or_admin` 拦截器
- **管理员权限**：`require_admin` 拦截器
- **操作日志**：记录管理员操作

---

## 💬 **2. 社区互动模块（Community）**

### 功能模块

#### 2.1 社区贴子（Posts）
- **创建贴子**：用户发布讨论贴子
- **浏览贴子**：查看所有贴子列表
- **贴子详情**：查看单个贴子完整内容
- **编辑/删除**：作者可修改或删除自己的贴子
- **搜索/筛选**：按标题、分类、热度搜索

```
API 端点：
GET    /api/community/posts              - 获取贴子列表
POST   /api/community/posts              - 创建贴子
GET    /api/community/posts/{post_id}    - 获取贴子详情
PUT    /api/community/posts/{post_id}    - 更新贴子
DELETE /api/community/posts/{post_id}    - 删除贴子

支持参数：
├─ page: 分页
├─ limit: 每页数量
├─ category: 分类筛选
├─ sort: 排序方式（热度/最新/评论数）
└─ search: 搜索关键词
```

#### 2.2 评论系统（Comments）
- **添加评论**：用户对贴子或评论进行评论
- **评论列表**：树形结构展示评论和回复
- **编辑评论**：作者可修改自己的评论
- **删除评论**：作者和管理员可删除评论
- **点赞评论**：用户点赞评论

```
API 端点：
POST   /api/community/posts/{post_id}/comments           - 添加评论
GET    /api/community/posts/{post_id}/comments           - 获取评论列表
PUT    /api/community/comments/{comment_id}              - 更新评论
DELETE /api/community/comments/{comment_id}              - 删除评论
POST   /api/community/comments/{comment_id}/like         - 点赞评论
GET    /api/community/posts/{post_id}/comments/tree      - 获取树形评论
```

#### 2.3 贴子标签和分类
- **自动分类**：支持多个分类标签
- **标签管理**：创建、编辑、删除标签
- **热门标签**：显示热门讨论话题

```
支持的分类：
├─ 新闻讨论 - 针对新闻内容的讨论
├─ AI 生成 - 讨论 AI 生成功能
├─ 用户交流 - 用户之间的交流
├─ 问题反馈 - 系统问题和反馈
└─ 其他 - 其他话题
```

#### 2.4 社区规则
- **审核机制**：管理员审核敏感内容
- **举报机制**：用户可举报违规内容
- **禁言机制**：管理员可禁言违规用户

```
API 端点：
POST /api/community/posts/{post_id}/report        - 举报贴子
POST /api/community/comments/{comment_id}/report  - 举报评论
```

---

## 👤 **3. 用户资料模块（Profile）**

### 功能模块

#### 3.1 个人概览（Overview）
- **用户基本信息**：头像、用户名、签名、个人简介
- **统计数据**：
  - 发布的新闻数
  - 发布的社区贴子数
  - 获得的点赞数
  - 获得的评论数
- **等级和成就**：用户等级、勋章、成就系统
- **最近活动**：最近浏览、点赞、评论的内容

```
GET /api/profile/overview
└─ 返回：
   ├─ username: 用户名
   ├─ avatar: 头像
   ├─ bio: 个人简介
   ├─ level: 用户等级
   ├─ stats: {
   │   ├─ posts_count: 贴子数
   │   ├─ comments_count: 评论数
   │   ├─ likes_received: 获赞数
   │   └─ followers: 粉丝数
   │ }
   └─ recent_activity: 最近活动
```

#### 3.2 浏览历史（Browse History）
- **历史记录**：用户浏览过的所有新闻
- **按时间排序**：最近浏览的优先
- **清空历史**：一键清空浏览记录
- **导出记录**：支持导出历史列表

```
GET /api/profile/browse-history
└─ 支持参数：
   ├─ page: 分页
   ├─ limit: 每页数量
   ├─ start_date: 开始日期
   ├─ end_date: 结束日期
   └─ search: 搜索标题

DELETE /api/profile/browse-history      - 清空历史
DELETE /api/profile/browse-history/{id} - 删除单条记录
```

#### 3.3 收藏夹（Favorites）
- **收藏新闻**：将喜欢的新闻加入收藏
- **收藏管理**：查看、分类、删除收藏
- **创建分类**：创建自定义收藏夹
- **批量管理**：支持批量移动、删除

```
GET /api/profile/favorites
POST /api/profile/favorites                 - 添加收藏
DELETE /api/profile/favorites/{favorite_id} - 删除收藏

支持参数：
├─ page: 分页
├─ category: 分类筛选
└─ search: 搜索
```

#### 3.4 AI 生成记录（AI Records）
- **历史记录**：用户使用 AI 生成功能的历史
- **查看详情**：查看生成的标题和摘要
- **重新使用**：基于历史记录重新生成
- **导出记录**：支持导出生成记录

```
GET /api/profile/ai-records
└─ 支持参数：
   ├─ page: 分页
   ├─ limit: 每页数量
   ├─ start_date: 开始日期
   ├─ end_date: 结束日期
   ├─ sort: 排序方式
   └─ search: 搜索

GET /api/profile/ai-records/{record_id}  - 获取单条记录
DELETE /api/profile/ai-records/{record_id} - 删除记录
```

#### 3.5 账户设置（Account Settings）
- **修改头像**：上传或选择头像
- **修改用户名**：修改昵称
- **修改密码**：更改登录密码
- **修改邮箱**：更改绑定邮箱（需验证）
- **隐私设置**：控制个人信息可见性
- **通知设置**：设置通知偏好

```
PUT /api/profile/settings
└─ 支持修改：
   ├─ avatar
   ├─ username
   ├─ bio
   ├─ privacy_settings
   └─ notification_settings
```

#### 3.6 粉丝系统（Followers）
- **关注用户**：关注感兴趣的用户
- **粉丝列表**：查看粉丝和关注者
- **取消关注**：移除不需要的关注

```
GET /api/profile/followers          - 获取粉丝列表
GET /api/profile/following          - 获取关注列表
POST /api/profile/follow/{user_id}  - 关注用户
DELETE /api/profile/follow/{user_id} - 取消关注
```

---

## 📱 **4. 前端实现**

### 新增前端视图

#### 4.1 管理后台视图（AdminView.vue）
```
/admin
├─ 仪表盘
├─ 待审核内容
├─ 用户管理
└─ 系统设置
```

#### 4.2 社区页面（CommunityView.vue）
```
/community
├─ 社区贴子列表
├─ 创建贴子对话框
├─ 贴子详情页
├─ 评论区
└─ 搜索和筛选
```

#### 4.3 个人中心（ProfileView.vue）
```
/profile
├─ 个人概览
├─ 浏览历史
├─ 收藏夹
├─ AI 生成记录
├─ 账户设置
└─ 粉丝和关注
```

### 前端 API 文件（新增）
```
frontend/src/api/
├─ admin.ts         - 管理后台 API 封装
├─ community.ts     - 社区互动 API 封装
└─ profile.ts       - 用户资料 API 封装
```

---

## 🔄 **5. 后端整合情况**

### 路由整合

在 `backend/app/main.py` 中，phase-2 的三个模块已通过路由注册：

```python
# 管理后台路由
app.include_router(admin_router, prefix="/api/admin", tags=["管理后台"])

# 社区互动路由
app.include_router(community_router, prefix="/api/community", tags=["社区互动"])

# 用户资料路由
app.include_router(profile_router, prefix="/api/profile", tags=["用户资料"])
```

### 权限控制

- **管理员模块**：需要 `editor` 或 `admin` 权限
- **社区互动**：普通用户可发布，编辑可审核
- **用户资料**：用户可查看自己的数据，管理员可查看所有数据

---

## 📊 **6. 数据模型**

### 管理员相关
```
AdminDashboard
├─ total_users: 总用户数
├─ total_posts: 总贴子数
├─ pending_count: 待审核数
└─ recent_stats: 最近统计

PendingPost
├─ id: 贴子 ID
├─ title: 标题
├─ content: 内容
├─ author: 作者
├─ submit_time: 提交时间
└─ status: 状态（pending/approved/rejected）
```

### 社区相关
```
CommunityPost
├─ id: 贴子 ID
├─ title: 标题
├─ content: 内容
├─ author: 作者
├─ category: 分类
├─ tags: 标签
├─ comments_count: 评论数
├─ likes_count: 点赞数
└─ created_at: 创建时间

CommentItem
├─ id: 评论 ID
├─ post_id: 贴子 ID
├─ content: 内容
├─ author: 作者
├─ parent_id: 父评论 ID（用于嵌套）
├─ likes_count: 点赞数
└─ created_at: 创建时间
```

### 用户资料相关
```
ProfileOverview
├─ user_id: 用户 ID
├─ username: 用户名
├─ avatar: 头像
├─ bio: 个人简介
├─ level: 用户等级
├─ stats: {
│   ├─ posts_count
│   ├─ comments_count
│   ├─ likes_received
│   └─ followers_count
│ }
└─ joined_at: 注册时间

BrowseHistory
├─ id: 记录 ID
├─ user_id: 用户 ID
├─ news_id: 新闻 ID
├─ news_title: 新闻标题
└─ visited_at: 浏览时间

UserFavorite
├─ id: 收藏 ID
├─ user_id: 用户 ID
├─ news_id: 新闻 ID
├─ category: 收藏分类
└─ created_at: 创建时间

AIRecord
├─ id: 记录 ID
├─ user_id: 用户 ID
├─ input_text: 输入文本
├─ result: 生成结果
└─ created_at: 创建时间
```

---

## 🎯 **7. Phase-2 的特点总结**

### 功能完整性
✅ 包含完整的三大核心功能：管理、社区、用户资料
✅ 每个功能都有完整的增删改查操作
✅ 支持权限控制和数据隔离

### 用户体验
✅ 直观的管理界面
✅ 便捷的社区互动
✅ 个性化的用户中心

### 扩展性
✅ 模块化设计，易于扩展
✅ 完整的 API 接口，支持二次开发
✅ 规范的数据模型

### 与 Develop 分支的整合
✅ 两个分支功能互补：develop 提供 AI 功能，phase-2 提供社区平台
✅ 合并后形成完整的新闻社区系统
✅ 用户可在一个平台中实现：浏览新闻 → 生成 AI 摘要 → 社区讨论 → 个人管理

---

## 📈 **8. 系统整体功能矩阵（合并后）**

| 功能 | 模块 | 来源 | 状态 |
|------|------|------|------|
| 新闻浏览 | 新闻 | 基础 | ✅ 完成 |
| 新闻详情 | 新闻 | 基础 | ✅ 完成 |
| AI 标题摘要 | AI 生成 | develop | ✅ 完成 |
| 管理后台 | 管理 | phase-2 | ✅ 完成 |
| 社区贴子 | 社区 | phase-2 | ✅ 完成 |
| 评论互动 | 社区 | phase-2 | ✅ 完成 |
| 个人中心 | 用户资料 | phase-2 | ✅ 完成 |
| 浏览历史 | 用户资料 | phase-2 | ✅ 完成 |
| 收藏夹 | 用户资料 | phase-2 | ✅ 完成 |
| 用户认证 | 认证 | 基础 | ✅ 完成 |

---

**结论**：phase-2 分支开发了完整的社区和内容管理功能，与 develop 分支的 AI 功能完美互补，使项目从一个专项工具扩展为一个完整的新闻社区平台。
