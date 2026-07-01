# 阶段 H：遗留问题修复 — 五人并行任务分配

> 项目：基于大语言模型的智能新闻摘要与协同互动系统  
> 目标：在阶段 G 联调修复基础上，集中解决当前各模块遗留的 UI/功能/数据问题。  
> 原则：**按模块划分，最小化文件冲突，5 人可并行开工。**

---

## 任务总览

| 人员 | 负责模块 | 问题数 | 预估复杂度 |
|---|---|---|---|
| **成员 A** | 首页（Homepage） | 5 | ⭐⭐⭐ |
| **成员 B** | 详情页 + 个人中心 | 10 | ⭐⭐⭐⭐⭐ |
| **成员 C** | 评论系统 + 社区互动 | 5 | ⭐⭐⭐⭐ |
| **成员 D** | AI 生成 + 社区内容 | 5 | ⭐⭐⭐⭐ |
| **成员 E** | 管理员后台 | 2 | ⭐⭐⭐ |

---

## 1. 成员 A：首页模块（5 项）

### 涉及文件

```text
# 前端
frontend/src/views/home/HomeView.vue
frontend/src/components/news/NewsHotList.vue
frontend/src/components/news/NewsSearchBar.vue
frontend/src/components/profile/RecommendationPanel.vue
frontend/src/components/news/NewsList.vue
frontend/src/components/news/NewsCard.vue
frontend/src/api/news.ts

# 后端
backend/app/modules/news/router.py
backend/app/modules/news/service.py
backend/app/modules/news/schema.py
```

### 任务清单

#### A1. 热搜数据存疑 — 更换/删除热搜数据源
- **问题**：首页热搜榜数据可能来自 Mock 或不可靠数据源
- **方案**：
  1. 检查 `NewsHotList.vue` 中热搜数据的 API 调用链路
  2. 确认 `backend/app/modules/news/service.py` 中热搜接口是否查询真实数据库
  3. 若数据源不可靠，改为从 `news` 表按浏览量/点击量降序取 Top N
  4. 若短期内无法接入真实热榜算法，先改为"最新热榜"（按 `created_at` 降序 + 最低浏览量过滤）
  5. 前端保留 loading、空数据、错误兜底状态

#### A2. 首页右侧最下方 AI 工具入口和最近浏览模块删除
- **问题**：首页右侧栏底部有不必要的入口和模块
- **方案**：
  1. 在 `HomeView.vue` 中找到右侧栏底部的 AI 工具入口组件
  2. 找到"最近浏览"模块的渲染位置
  3. 删除这两块 UI（保留数据逻辑不动，仅注释/移除渲染）
  4. 确保删除后右侧栏布局不错位

#### A3. 订阅管理 + 个性化推荐 + 热榜决定首页推荐新闻
- **问题**：首页推荐新闻未综合用户订阅、偏好和热榜数据
- **方案**：
  1. 检查 `RecommendationPanel.vue` 的推荐逻辑
  2. 后端 `news/service.py` 新增/修改推荐接口，综合权重：
     - 用户订阅的分类/标签（权重 40%）
     - 个性化推荐（协同过滤/内容推荐，权重 35%）
     - 热榜新闻（权重 25%）
  3. 前端展示推荐来源标签（如"基于你的订阅"、"热门推荐"）
  4. 未登录用户默认展示热榜推荐

#### A4. 推荐"查看更多"功能失效
- **问题**：首页推荐模块的"查看更多"按钮点击无反应
- **方案**：
  1. 检查 `RecommendationPanel.vue` 或 `HomeView.vue` 中"查看更多"的点击事件
  2. 确认路由跳转是否指向正确的推荐聚合页（或滚动加载更多）
  3. 若采用分页加载，确保 `page` 参数正确递增
  4. 若跳转页面不存在，补充路由或改为当前页追加加载

#### A5. 搜索框只留主页
- **问题**：搜索框出现在多个页面，应只在首页展示
- **方案**：
  1. 检查 `NewsSearchBar.vue` 在哪些页面被引用
  2. 搜索框只保留在 `HomeView.vue`
  3. 从其他页面（如社区、详情页、个人中心）的模板中移除搜索框引用
  4. 确认 `AppHeader.vue` 中若有搜索框也一并移除（或改为仅首页显示）

### 冲突注意
- `news/router.py` 和 `news/service.py` 与成员 B 共享 → **约定：A 改列表/搜索/推荐接口，B 改详情接口，合并时注意 import 和函数定义不冲突**

---

## 2. 成员 B：详情页 + 个人中心（10 项）

### 涉及文件

```text
# 前端 — 详情页
frontend/src/views/news-detail/NewsDetailView.vue
frontend/src/components/news/NewsDetailSidePanel.vue
frontend/src/components/news/NewsDetailContent.vue
frontend/src/components/news/NewsRecommendPanel.vue
frontend/src/components/news/RelatedNewsList.vue
frontend/src/components/interaction/ShareButton.vue
frontend/src/api/news.ts

# 前端 — 个人中心
frontend/src/views/profile/ProfileView.vue
frontend/src/components/profile/ReadingTrajectory.vue
frontend/src/components/profile/ReadingTimeline.vue
frontend/src/components/profile/ReadingHeatmap.vue
frontend/src/components/layout/AppSidebar.vue
frontend/src/api/profile.ts
frontend/src/api/user.ts

# 后端 — 详情页
backend/app/modules/news/router.py
backend/app/modules/news/service.py

# 后端 — 个人中心
backend/app/modules/profile/router.py
backend/app/modules/profile/service.py
backend/app/modules/user/router.py
backend/app/modules/user/service.py
backend/app/modules/user/schema.py
```

### 任务清单

#### B1. 右侧 AI 工具入口删除，只保留新闻右上角 AI 生成标题和摘要
- **问题**：详情页右侧栏有冗余 AI 入口
- **方案**：
  1. 在 `NewsDetailSidePanel.vue` 中找到 AI 工具入口组件并删除
  2. 确认 `NewsDetailContent.vue` 或 `NewsDetailView.vue` 右上角的 AI 生成按钮保留
  3. 右上角 AI 按钮仅保留"生成标题"和"生成摘要"两个功能入口
  4. 点击后跳转 AI 生成页面并自动填充当前新闻内容

#### B2. 分享功能改为生成页面截图
- **问题**：当前分享功能可能是复制链接，需改为截图分享
- **方案**：
  1. 修改 `ShareButton.vue` 的分享逻辑
  2. 使用 `html2canvas` 或类似库截取新闻详情主体区域
  3. 生成截图后提供：复制到剪贴板 / 下载图片 / 调用系统分享 API
  4. 若项目未引入截图库，先在 `frontend/package.json` 添加依赖
  5. 截图需排除导航栏、侧边栏等非内容元素

#### B3. 推荐阅读（推荐和本篇新闻相关 / 热榜新闻）
- **问题**：详情页底部推荐阅读逻辑不准确
- **方案**：
  1. 修改 `NewsRecommendPanel.vue` 和 `RelatedNewsList.vue`
  2. 后端新增/修改推荐接口，基于当前新闻的分类 + 标签 + 关键词匹配相关新闻
  3. 推荐列表排除当前正在阅读的新闻
  4. 若无足够相关新闻（< 3 条），用热榜新闻补足至 5 条
  5. 推荐卡片展示：标题、摘要、封面图、发布时间

#### B4. 事件脉络改为：新闻 = 1 件时显示"新闻数量不足"，≥ 2 件时显示脉络
- **问题**：事件脉络（Timeline）在只有 1 条新闻时仍尝试展示
- **方案**：
  1. 在 `NewsDetailView.vue` 或 Timeline 相关组件中，判断关联新闻数量
  2. `count === 0`：不显示脉络入口
  3. `count === 1`：显示入口但标注"新闻数量不足，无法生成脉络"（灰色不可点击）
  4. `count >= 2`：正常显示脉络入口，点击可查看完整 Timeline
  5. 后端返回关联新闻数量字段

#### B5. 个人资料邮箱 / 手机号功能
- **问题**：个人资料编辑缺少邮箱和手机号字段
- **方案**：
  1. 在 `ProfileView.vue` 编辑资料表单中新增邮箱和手机号输入框
  2. 后端 `user/schema.py` 的 UpdateUser Schema 确保包含 `email`、`phone` 字段
  3. 前端添加基本格式校验（邮箱正则、手机号 11 位）
  4. 可选：发送验证码验证（先不做，预留接口）
  5. 保存后刷新个人资料显示

#### B6. 浏览 / 收藏历史改为新闻 / 帖子两类
- **问题**：当前浏览历史和收藏历史混在一起展示
- **方案**：
  1. 在 `ProfileView.vue` 的历史记录区域增加 Tab 切换：新闻 | 帖子
  2. 浏览历史按 Tab 分类展示：
     - 新闻 Tab：展示已浏览的新闻列表
     - 帖子 Tab：展示已浏览的社区帖子列表
  3. 收藏记录同理分为新闻收藏和帖子收藏两个子 Tab
  4. 后端 `profile/service.py` 新增/修改接口支持按类型过滤（`type=news|post`）

#### B7. 收藏/浏览/评论记录搜索栏优化 + 时间修复
- **问题**：
  - 搜索栏需要点击搜索按钮才触发，应改为实时过滤
  - 时间显示不正确，应按点击收藏时间而非其他时间
- **方案**：
  1. 移除搜索按钮，改为输入即过滤（`watch` + `computed` 实时过滤本地数据）
  2. 添加 300ms 防抖避免频繁计算
  3. 检查后端返回的时间字段：收藏记录用 `favorited_at`，浏览记录用 `viewed_at`，评论记录用 `commented_at`
  4. 前端展示时格式化时间为 `YYYY-MM-DD HH:mm`
  5. 若后端字段名不一致，先统一后端返回字段

#### B8. 账号设置放到编辑资料里面
- **问题**：账号设置（修改密码等）是独立入口，应整合进编辑资料页
- **方案**：
  1. 在 `ProfileView.vue` 的编辑资料弹窗/区域内新增"账号设置"区块
  2. 包含：修改密码（旧密码 + 新密码 + 确认新密码）、注销账号（二次确认）
  3. 删除独立的"账号设置"页面入口
  4. 侧边栏 `AppSidebar.vue` 中去掉"账号设置"菜单项
  5. 后端 `user/router.py` 确保有改密接口

#### B9. 阅读脉络图 + 阅读总结报告
- **问题**：阅读脉络图显示效果差，缺少阅读总结报告（类似年度报告）
- **方案**：
  1. **阅读脉络图优化**（`ReadingTrajectory.vue`）：
     - 修复 ECharts 容器宽度问题（参考阶段 G 的 F 线）
     - 节点大小按阅读次数差异化
     - 支持按时间范围筛选（7天/30天/全部）
     - 点击新闻节点跳转详情页
  2. **阅读总结报告**（新增组件或模块）：
     - 统计维度：总阅读量、阅读天数、最爱分类、阅读时段分布、Top 5 关键词
     - 生成可视化报告（柱状图/饼图/词云）
     - 参考年度报告设计风格（卡片式布局、数据突出）
     - 后端 `profile/service.py` 新增聚合统计接口
  3. 确保图表在 `width > 300px` 时才初始化（防止 64px 问题）

#### B10. 个人主页"概览"删除 + 订阅管理只留侧边栏
- **问题**：个人主页的"概览"Tab 和订阅管理模块需调整
- **方案**：
  1. 删除 `ProfileView.vue` 中的"概览"Tab（概览数据不再独立展示）
  2. 个人主页区块中的"订阅管理"模块删除
  3. 保留 `AppSidebar.vue` 侧边栏中的"订阅管理"入口（功能不变）
  4. 确认删除后个人主页的 Tab 布局正常

### 冲突注意
- `news/router.py` 和 `news/service.py` 与成员 A 共享 → **约定：B 只新增/修改详情 + 推荐阅读接口，不改动列表/搜索接口**
- `ShareButton.vue` 是独立组件，无冲突
- `ProfileView.vue` / `AppSidebar.vue` / `profile/` / `user/` 是个人中心专属文件，B 全权负责，无其他人修改
- `ProfileView.vue` 中引用了 `AIGenerateHistory.vue`（成员 D 负责）→ **B 只引用不改动 AI 组件，D 是 AI 组件负责人**

---

## 3. 成员 C：评论系统 + 社区互动（5 项）

### 涉及文件

```text
# 前端
frontend/src/components/interaction/CommentBox.vue
frontend/src/components/interaction/CommentItem.vue
frontend/src/components/interaction/CommentList.vue

# API
frontend/src/api/interaction.ts
frontend/src/api/community.ts

# 后端
backend/app/modules/interaction/router.py
backend/app/modules/interaction/service.py
backend/app/modules/interaction/schema.py
backend/app/modules/community/router.py          # 仅评论相关接口
backend/app/modules/community/service.py          # 仅评论相关函数
```

### 任务清单

#### C1. 详情页评论区发布图片失败（后端 422）
- **问题**：新闻详情页评论上传图片时后端返回 422 Unprocessable Entity
- **方案**：
  1. 检查前端 `CommentBox.vue` 中图片上传的请求体格式（FormData / JSON / Base64）
  2. 检查后端 `interaction/router.py` 评论接口的 Pydantic Schema 是否接受图片字段
  3. 确认图片大小限制、格式限制（jpg/png/gif/webp）是否合理
  4. 确认 `interaction/schema.py` 中图片字段类型正确（`UploadFile` 或 `str`）
  5. 修复后前后端联调确认图片能正常上传和回显
  6. 检查 `/uploads` 静态目录挂载是否正常（参考阶段 G 的 E 线）

#### C2. 表情框挪到评论框下面
- **问题**：表情选择器当前位置不合理，应移到评论输入框下方
- **方案**：
  1. 修改 `CommentBox.vue` 中表情选择器（emoji-picker）的 DOM 位置
  2. 将表情按钮和弹出框从评论框上方/侧方移到评论框下方
  3. 调整 CSS 定位，表情弹窗向上弹出（`bottom: 100%`）避免被遮挡
  4. 确保移动端也能正常使用

#### C3. 社区帖子评论区图片发送和显示问题
- **问题**：社区帖子的评论中图片无法正常发送或显示
- **方案**：
  1. 排查社区评论图片上传链路（前端 → API → 后端 → 数据库 → 回显）
  2. 确认社区评论接口是否复用 `interaction` 模块还是独立实现
  3. 若复用，检查是否与新闻评论共用同一上传逻辑
  4. 图片显示时检查 URL 拼接（相对路径 vs 绝对路径）
  5. 修复后确认社区帖子评论图片与新闻评论图片体验一致

#### C4. 评论区 AI 评论总结
- **问题**：社区帖子评论区缺少 AI 自动总结评论的功能
- **方案**：
  1. 在 `CommentList.vue` 或社区评论区域新增"AI 总结评论"按钮
  2. 点击后收集当前所有评论内容，发送给 ai-service
  3. ai-service 返回评论摘要（主要观点、情感倾向、讨论热点）
  4. 前端以卡片/Tooltip 形式展示总结结果
  5. 添加 loading 和错误兜底（参考阶段 G 的 D 线 AI 体验规范）
  6. 后端新增接口：`POST /api/community/comments/summary`

#### C5. 评论区回复折叠 + 两层回复功能
- **问题**：评论回复不支持折叠，且只支持一级回复
- **方案**：
  1. 修改 `CommentItem.vue`：
     - 添加"收起/展开"子评论按钮（超过 3 条子回复时默认折叠）
     - 支持对回复进行再回复（二层回复，即 `parent_comment_id` 可嵌套一层）
  2. 修改 `CommentList.vue`：递归渲染二层回复（缩进 + 左侧细线区分层级）
  3. 后端 `interaction/service.py` 确认评论表支持 `parent_comment_id` 和 `reply_to_user_id`
  4. 前端回复输入框支持 `@用户名` 提示
  5. 三层及以上回复不再嵌套，统一显示为对二层评论的回复

### 冲突注意
- `CommentBox.vue` / `CommentItem.vue` / `CommentList.vue` 被详情页（成员 B）和社区（成员 D）引用 → **C 是评论组件的唯一负责人，B 和 D 不修改这些文件**
- `community/router.py` 和 `community/service.py` 与成员 D 共享 → **约定：C 只新增/修改评论相关接口（comments/summary），D 负责帖子/标签相关接口**

---

## 4. 成员 D：AI 生成 + 社区内容（5 项）

### 涉及文件

```text
# 前端 — AI 生成
frontend/src/views/ai-generate/AIGenerateView.vue
frontend/src/components/ai/AIInputPanel.vue
frontend/src/components/ai/AIGenerateHistory.vue
frontend/src/components/ai/AIResultPanel.vue
frontend/src/api/ai.ts

# 前端 — 社区
frontend/src/views/community/CommunityView.vue
frontend/src/api/community.ts

# 后端 — AI
backend/app/modules/ai/router.py
backend/app/modules/ai/service.py
backend/app/modules/ai/schema.py

# 后端 — 社区
backend/app/modules/community/router.py          # 仅帖子/标签相关接口
backend/app/modules/community/service.py          # 仅帖子/标签相关函数
backend/app/modules/community/schema.py
```

### 任务清单

#### D1. AI 生成记录同步（AI 生成页 ↔ 个人后台 AI 生成记录）
- **问题**：AI 生成页面生成了摘要/标题，但个人后台的 AI 生成记录看不到
- **方案**：
  1. 检查 AI 生成保存逻辑（`ai/service.py`）：生成成功后是否写入数据库
  2. 确认个人后台 AI 生成记录（`ProfileView.vue` 中 AI 历史 Tab）是否从同一数据源读取
  3. 若两处调用不同接口，统一为一个数据源（表 `ai_generation_history`）
  4. 前端 `AIGenerateHistory.vue` 和 `ProfileView.vue` 中的 AI 记录组件使用相同 API
  5. 修复后：在 AI 生成页生成 → 刷新个人后台 → 记录应同步出现

#### D2. 上传文件功能开发
- **问题**：AI 生成页的上传文件功能未实现（用户需上传文档/图片让 AI 分析）
- **方案**：
  1. 在 `AIInputPanel.vue` 中添加文件上传按钮（支持 .txt / .pdf / .docx / 图片）
  2. 前端使用 `FormData` 上传，支持拖拽上传
  3. 后端新增 `POST /api/ai/upload` 接口：
     - 接收文件，解析文本内容（PDF 用 PyPDF2、DOCX 用 python-docx）
     - 返回解析后的文本内容
  4. 上传后文本自动填充到 AI 输入框
  5. 文件大小限制：10MB，上传时显示进度条
  6. 若不支持的文件格式，前端给出明确提示

#### D3. 首页跳转 AI 生成页面自动填充内容 —— 退出时自动清除
- **问题**：从新闻详情页跳转到 AI 生成页时，新闻正文被自动填充；但返回首页再次进入 AI 生成页时，上次填充的内容仍在
- **方案**：
  1. 在 `AIGenerateView.vue` 中使用路由 query 参数传递填充内容（`?content=xxx&news_id=xxx`）
  2. 在 `onMounted` 中读取 query 填充到输入框
  3. 在 `onUnmounted`（组件销毁时）清除输入框内容和 query 标记
  4. 使用 `sessionStorage` 记录"已填充过"，非首次进入不自动填充
  5. 或者：路由离开时使用 `router.replace` 清除 query 参数

#### D4. 社区热搜改为讨论帖子热度 Top 10，点击跳转具体帖子
- **问题**：社区热搜榜当前可能是 Mock 数据或展示新闻热搜
- **方案**：
  1. 修改 `CommunityView.vue` 中的热搜区域
  2. 改为从 `community_post` 表查询热度 Top 10（热度 = 浏览量 + 评论数 × 2 + 点赞数）
  3. 每个热搜项点击跳转到对应帖子详情（`/community/post/:id`）
  4. 样式参考首页热榜（排名数字、标题截断、热度数值），但数据源独立
  5. 确保跳转路由存在且有帖子详情展示

#### D5. 标签分类真实数据化
- **问题**：社区标签分类疑似为 Mock 数据，需使用真实分类
- **方案**：
  1. 检查 `community/service.py` 中标签/分类接口是否查询数据库
  2. 确认数据库有分类表或标签字段
  3. 标签归类为真实政治分类：时政、经济、科技、教育、军事、社会、国际、体育、娱乐、健康
  4. 若数据库无分类表，建表或在 `community_post` 表新增 `category` 字段
  5. 前端标签筛选改为调用后端接口，按分类过滤帖子
  6. 发帖时要求选择分类（必填）

### 冲突注意
- `community/router.py` 和 `community/service.py` 与成员 C 共享 → **约定：D 只修改帖子/标签/热搜相关接口，C 只修改评论相关接口**
- `AIGenerateHistory.vue` 被 `ProfileView.vue` 引用（成员 B 负责）→ **D 是 AI 组件的负责人，B 只引用不改动**

---

## 5. 成员 E：管理员后台（2 项）

### 涉及文件

```text
# 前端 — 管理员后台
frontend/src/views/admin/AdminView.vue
frontend/src/api/admin.ts

# 后端 — 管理员
backend/app/modules/admin/router.py
backend/app/modules/admin/service.py
backend/app/modules/admin/schema.py

# 后端 — 社区（发帖审核状态改造）
backend/app/modules/community/router.py          # 仅发帖审核状态相关
backend/app/modules/community/service.py          # 仅发帖审核状态相关
```

### 任务清单

#### E1. 帖子内容审核功能
- **问题**：管理员后台缺少帖子内容审核，用户发帖应显示"审核中"
- **方案**：
  1. **社区发帖流程改造**：
     - 用户发帖后 `status = 0`（待审核），前端提示"帖子已提交，正在审核中"
     - 帖子列表不展示 `status = 0` 的帖子
  2. **管理后台审核页**（`AdminView.vue`）：
     - 新增"帖子审核"Tab，列表展示待审核帖子（标题、作者、时间、内容摘要）
     - 操作按钮：通过（`status = 1`）、驳回（`status = 2`）、查看详情
     - 驳回时可选填写驳回理由
  3. **后端**（`admin/service.py`）：
     - `GET /api/admin/posts/pending`：待审核帖子列表（分页）
     - `POST /api/admin/posts/{id}/approve`：通过
     - `POST /api/admin/posts/{id}/reject`：驳回（含驳回理由）
  4. 审核通过后帖子即刻在社区可见

#### E2. 热搜话题维护
- **问题**：管理员无法管理热搜话题
- **方案**：
  1. 在 `AdminView.vue` 中新增"热搜管理"Tab
  2. 功能：
     - 查看当前热搜话题列表
     - 手动添加热搜话题（话题词 + 热度值）
     - 编辑话题热度值
     - 删除/下架话题
     - 置顶某些话题
  3. 后端（`admin/service.py`）新增 CRUD 接口：
     - `GET /api/admin/hot-topics`：热搜列表
     - `POST /api/admin/hot-topics`：添加热搜
     - `PUT /api/admin/hot-topics/{id}`：编辑热搜
     - `DELETE /api/admin/hot-topics/{id}`：删除热搜
  4. 若数据库无热搜表，新建 `hot_topic` 表（字段：id、keyword、heat、is_pinned、created_at、updated_at）

### 冲突注意
- `community/router.py` 和 `community/service.py` 与成员 C、D 共享 → **约定：E 只修改发帖 `status` 默认值相关逻辑（审核流程），C 改评论接口，D 改帖子/标签接口**
- `admin/` 模块无其他人修改，E 全权负责

---

## 6. 文件冲突矩阵与协作约定

### 6.1 共享文件冲突表

| 文件 | 涉及人员 | 冲突类型 | 约定 |
|---|---|---|---|
| `backend/app/modules/news/router.py` | A、B | 同文件不同接口 | A 改列表/搜索/推荐，B 改详情/推荐阅读，合并不覆盖 |
| `backend/app/modules/news/service.py` | A、B | 同文件不同函数 | A 新增搜索/推荐函数，B 新增详情函数，各自独立函数 |
| `backend/app/modules/community/router.py` | C、D、E | 同文件不同接口 | C 新增评论路由，D 改帖子/标签/热搜路由，E 改发帖审核状态 |
| `backend/app/modules/community/service.py` | C、D、E | 同文件不同函数 | C 新增评论函数，D 改帖子/标签函数，E 改发帖审核函数 |
| `frontend/src/views/profile/ProfileView.vue` | B、D | 引用关系 | B 负责修改，D 的 AIGenerateHistory 被引用但不修改 |
| `frontend/src/components/layout/AppSidebar.vue` | B | 个人中心专属 | B 全权负责，无其他人修改 |

### 6.2 分支命名

```text
fix/homepage-issues          # 成员 A：首页
fix/detail-profile-issues    # 成员 B：详情页 + 个人中心
fix/comment-system           # 成员 C：评论系统
feat/ai-community-content    # 成员 D：AI + 社区内容
fix/admin-backend             # 成员 E：管理员后台
```

### 6.3 合并顺序建议

```text
第 1 批（无依赖，可同时合并）：
  成员 A（首页）
  成员 D（AI + 社区内容）  ← 注意社区路由与 C 的协调

第 2 批（依赖第 1 批的评论基础设施）：
  成员 C（评论系统）  ← 依赖 interaction 模块稳定

第 3 批（依赖评论系统稳定 + 个人中心独立模块）：
  成员 B（详情页 + 个人中心）  ← 引用 C 修改后的评论组件；个人中心部分独立无依赖

第 4 批（独立模块，涉及 community 发帖流程）：
  成员 E（管理员后台）  ← 注意 community 发帖审核与 C、D 的协调
```

### 6.4 合并前检查清单

每人合并前必须执行：

```powershell
# 前端
cd frontend
npm run build

# 后端
python -m py_compile backend/app/modules/news/router.py
python -m py_compile backend/app/modules/news/service.py
python -m py_compile backend/app/modules/community/router.py
python -m py_compile backend/app/modules/community/service.py
python -m py_compile backend/app/modules/interaction/router.py
python -m py_compile backend/app/modules/interaction/service.py
python -m py_compile backend/app/modules/ai/router.py
python -m py_compile backend/app/modules/ai/service.py
python -m py_compile backend/app/modules/profile/router.py
python -m py_compile backend/app/modules/profile/service.py
python -m py_compile backend/app/modules/user/router.py
python -m py_compile backend/app/modules/user/service.py
python -m py_compile backend/app/modules/admin/router.py
python -m py_compile backend/app/modules/admin/service.py
```

---

## 7. 测试验证分工

| 人员 | 验证重点 |
|---|---|
| A | 首页热搜数据真实、推荐可查看更多、搜索框仅在首页、AI 入口和浏览模块已删除 |
| B | 详情页：AI 入口仅右上角、截图分享可用、推荐阅读准确、事件脉络条件显示；个人中心：邮箱/手机号可编辑、历史分新闻/帖子、搜索实时过滤、账号设置已整合、脉络图正常、阅读报告可生成、概览和订阅管理已清理 |
| C | 评论图片可发（不再 422）、表情框在评论框下方、社区评论图片正常、AI 总结可用、二层回复折叠正常 |
| D | AI 生成记录同步、文件上传可用、退出清空、社区热搜 Top 10 可跳转、标签为真实分类 |
| E | 帖子审核流程可用（发帖→待审核→通过/驳回）、热搜话题可 CRUD 维护 |

---

## 8. 整体时间建议

| 阶段 | 内容 | 建议时长 |
|---|---|---|
| 第 1-2 天 | 各人并行开发 | 2 天 |
| 第 3 天 | 第 1 批合并（A、D）→ 联调 | 0.5 天 |
| 第 3 天 | 第 2 批合并（C）→ 联调 | 0.5 天 |
| 第 4 天 | 第 3 批合并（B）→ 联调 + E 合并 | 1 天 |
| 第 5 天 | 全员联调 + 验收测试 | 1 天 |

> **总计：约 5 个工作日**，5 人并行开发 2 天 + 分批合并联调 3 天。
