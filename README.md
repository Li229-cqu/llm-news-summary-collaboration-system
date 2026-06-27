# 基于大语言模型的智能新闻摘要与协同互动系统

**第38组-LCX组**

## 一、项目简介

《基于大语言模型的智能新闻摘要与协同互动系统》是一个面向新闻浏览、AI 标题摘要生成、社区互动和个人中心管理的前后端分离系统。系统采用"数据库优先 + mock 兜底"的策略，确保在数据库异常时仍能正常演示。

当前系统已完成 **11 个核心功能模块**，支持完整的新闻阅读、AI 生成、社区互动和个人管理的闭环体验。

## 二、核心功能模块（已实现）

### 📰 新闻浏览与管理
- ✅ **新闻首页**：热点新闻、分类筛选、订阅管理
- ✅ **新闻搜索**：按标题、分类、关键词搜索
- ✅ **新闻详情**：完整正文、封面图展示、相关推荐
- ✅ **分类导航**：多个新闻分类和主题导航
- ✅ **真实数据**：RSS 爬虫自动抓取新闻，数据库实时更新

### 💬 新闻互动与评论
- ✅ **评论系统**：一级评论、嵌套回复、点赞功能
- ✅ **评论富媒体**：支持表情选择器、图片上传和预览
- ✅ **互动统计**：评论数、点赞数、收藏数实时统计
- ✅ **评论媒体**：支持 emoji 表情和图片混合评论

### 🤖 AI 智能生成
- ✅ **标题生成**：AI 生成 3-5 个候选标题，支持多种风格
- ✅ **摘要生成**：短摘要、长摘要、要点摘要多维度生成
- ✅ **内容分析**：关键词提取、新闻要素识别、一致性校验
- ✅ **生成历史**：保存所有生成记录到个人中心，可复用
- ✅ **两种模式**：Mock 模式（快速演示）+ LLM 模式（真实生成）

### 👥 社区互动
- ✅ **社区帖子**：用户发帖、编辑、删除、置顶功能
- ✅ **热搜榜**：实时热搜话题排名
- ✅ **帖子评论**：多层次评论系统，支持富媒体内容
- ✅ **AI 评论总结**：智能总结评论区舆论核心观点
- ✅ **社区互动**：点赞、收藏、分享等互动功能

### 👤 个人中心管理
- ✅ **用户概览**：阅读统计、互动统计、收藏统计
- ✅ **浏览历史**：查看阅读过的所有新闻
- ✅ **收藏管理**：管理收藏的新闻和内容
- ✅ **评论记录**：查看发表过的所有评论
- ✅ **AI 生成记录**：查看所有 AI 生成的摘要和标题

### 📊 阅读数据分析
- ✅ **个性化推荐**：基于用户浏览、收藏、点赞的个性化新闻推荐
- ✅ **阅读脉络图**：力导向图展示用户关注的话题关联和演变
- ✅ **阅读时间线**：按时间展示用户的阅读轨迹和话题演变
- ✅ **阅读热力图**：矩阵形式展示用户在不同话题的活跃度

### ⏰ Timeline 事件脉络
- ✅ **事件时间线**：智能组织新闻为时间有序的事件脉络
- ✅ **进度反馈**：生成中实时显示进度，避免用户困惑
- ✅ **结构化数据**：事件包含类型、重要度、关键词等元数据
- ✅ **事件关系**：支持事件间的因果和时间关系建立

### 🔐 用户认证与权限
- ✅ **用户登录**：支持用户名密码登录，Token 认证
- ✅ **角色权限**：普通用户、审核编辑、管理员三种角色
- ✅ **受保护接口**：评论、收藏、生成等接口需要登录认证
- ✅ **权限控制**：编辑可审核社区帖子，管理员可管理后台

### 📋 管理后台
- ✅ **仪表板**：概览统计（用户数、新闻数、评论数、帖子数）
- ✅ **用户管理**：用户列表、用户信息查看
- ✅ **内容审核**：待审核帖子列表、审核和拒绝功能
- ✅ **数据统计**：各模块的实时数据统计

### 🔄 数据库与持久化
- ✅ **MySQL 数据库**：完整的数据库表结构和关系设计
- ✅ **数据库优先**：优先读写数据库，异常时回退 Mock
- ✅ **数据迁移**：支持版本化迁移脚本，自动升级表结构
- ✅ **爬虫集成**：RSS 爬虫自动抓取新闻并存入数据库

## 三、技术栈

### 前端
- Vue 3 + Vite
- TypeScript
- Element Plus UI 框架
- Pinia 状态管理
- Axios 网络请求
- ECharts 数据可视化
- emoji-picker-element 表情选择

### 后端
- Python FastAPI
- Pydantic 数据验证
- MySQL 8.0 数据库
- PyMySQL 数据库驱动
- python-multipart 文件上传支持

### AI 服务
- FastAPI 框架
- 智谱 GLM-4-Flash 大模型（支持）
- Mock 数据生成（快速演示）
- 流式响应支持

## 四、核心特性

### 🚀 性能优化
- 连接池支持（预留）
- 数据缓存策略
- 分页查询优化
- 异步操作支持

### 🛡️ 可靠性
- Mock 兜底机制：任何组件异常时自动回退到模拟数据
- 日志系统：清晰的日志标记（🤖 Mock | 🚀 Real API | ✅ Success | ❌ Error）
- 错误处理：友好的错误提示和异常恢复
- 数据备份：支持数据库完整备份和恢复

### 📈 可扩展性
- 模块化架构：各功能模块独立开发和测试
- API 版本化：支持多版本 API 兼容
- 插件体系：AI 服务可以轻松接入新的大模型
- Schema 版本化：数据模型支持版本管理

## 五、项目结构

```text
llm-news-summary-collaboration-system/
├── frontend/           # 前端 Vue 3 项目
├── backend/            # FastAPI 后端服务
├── ai-service/         # AI 生成服务（Mock + LLM）
├── database/           # 数据库 schema、seed、migrations
├── scripts/            # RSS 爬虫和工具脚本
├── docs/               # 项目文档和接口说明
├── plan/               # 项目规划和任务管理
└── README.md           # 本文件
```

## 六、快速开始

### 6.1 环境准备

需要安装：
- Node.js 16+
- Python 3.8+
- MySQL 8.0+
- Git

### 6.2 数据库初始化

```bash
# 创建数据库用户
mysql -u root -p < database/setup.sql

# 导入表结构
mysql -u llm_news_user -p llm_news_system < database/schema.sql

# 导入初始数据
mysql -u llm_news_user -p llm_news_system < database/seed.sql

# 执行迁移脚本（按顺序）
mysql -u llm_news_user -p llm_news_system < database/migrations/001_*.sql
mysql -u llm_news_user -p llm_news_system < database/migrations/002_*.sql
# ... 按编号顺序执行所有迁移
```

### 6.3 启动应用

**三个独立的终端窗口：**

**窗口 1 - 后端服务：**
```bash
cd backend
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt
.venv/Scripts/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

**窗口 2 - AI 服务：**
```bash
cd ai-service
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt
copy .env.example .env
.venv/Scripts/python -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
```

**窗口 3 - 前端应用：**
```bash
cd frontend
npm install
npm run dev
```

### 6.4 访问应用

- 前端：http://localhost:5173
- 后端 API：http://127.0.0.1:8000
- API 文档：http://127.0.0.1:8000/docs
- AI 服务：http://127.0.0.1:8001
- AI API 文档：http://127.0.0.1:8001/docs

## 七、默认账号

| 角色 | 用户名 | 密码 |
|------|--------|------|
| 普通用户 | `user` | `123456` |
| 审核编辑 | `editor` | `123456` |
| 管理员 | `admin` | `123456` |

## 八、AI 模型配置

### Mock 模式（默认）
- 快速返回，无需 API Key
- 适合本地开发和课堂演示
- 无需外部网络

### LLM 模式（可选启用）
配置 `.env` 环境变量：
```env
LLM_ENABLED=true
LLM_API_KEY=<你的 API Key>
LLM_PROVIDER=zhipu
LLM_MODEL=glm-4-flash
```

## 九、RSS 爬虫

自动抓取新闻并保存到数据库：

```bash
# 预览模式（不保存）
python scripts/crawlers/rss_news_crawler.py --dry-run --max-items 5

# 正式抓取
python scripts/crawlers/rss_news_crawler.py --max-items 10 --fetch-content

# 补全已有新闻内容
python scripts/crawlers/rss_news_crawler.py --fetch-content --update-existing-content

# 归档旧新闻
python scripts/crawlers/rss_news_crawler.py --cleanup-days 30
```

## 十、项目文档

详见 `docs/` 目录：
- `api.md` - REST API 接口文档
- `development_plan.md` - 开发计划和阶段总结
- `development_standard.md` - 代码规范和最佳实践
- `mock_data_news.md` - Mock 数据说明

以及 `plan/` 目录：
- `Fperiod` - 功能开发周期规划
- `issues-and-tasks.md` - 待办问题和并发任务

## 十一、部署

项目支持多种部署方式：

### Docker 部署
```bash
docker-compose up -d
```

### Nginx 配置
参考 `deploy/nginx.conf`

### 生产环境建议
- 使用 Gunicorn 或 uWSGI 替代 Uvicorn
- 启用 HTTPS
- 配置数据库连接池
- 实施速率限制
- 添加日志聚合

## 十二、常见问题

### Q: 页面仍显示 Mock 数据
A: 检查：
1. MySQL 是否启动
2. `backend/.env` 配置是否正确
3. 数据库表是否有数据

### Q: AI 服务不可用
A: 检查：
1. ai-service 是否启动（`http://127.0.0.1:8001/docs`）
2. `LLM_ENABLED` 配置
3. API Key 是否有效

### Q: 图片无法加载
A: 可能原因：
1. 外站防盗链（待优化为本地存储）
2. 网络连接问题
3. 爬虫未抓取封面图

## 十三、许可证

项目采用 MIT 许可证。详见 LICENSE 文件。

## 十四、贡献

欢迎提交 Issue 和 Pull Request。请遵循 `docs/development_standard.md` 中的代码规范。

---

**项目状态**：功能开发基本完成，正在进行性能优化和功能完善。

**最后更新**：2026-06-27 UTC+8
