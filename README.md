# 基于大语言模型的智能新闻摘要与协同互动系统

## 一、项目简介

基于大语言模型的智能新闻摘要与协同互动系统是一个面向新闻浏览、AI 标题摘要生成和社区互动的前后端分离系统。

系统规划包含首页新闻浏览、新闻详情、AI 标题摘要生成、社区互动、个人中心和管理后台等模块，后续将分阶段完成各项功能的设计、开发与联调。

## 二、项目定位

系统围绕“新闻浏览—新闻详情互动—AI 生成—社区交流—个人记录管理”的闭环展开，结合新闻内容消费、智能生成能力和用户协同互动，为用户提供连贯的新闻阅读与交流体验。

## 三、技术栈规划

### 前端

- Vue 3
- Vite
- TypeScript
- Vue Router
- Pinia
- Element Plus
- Axios

### 后端

- Python
- FastAPI
- Pydantic
- Uvicorn
- 后续接入 MySQL

### AI 服务

- FastAPI
- 当前阶段使用 Mock
- 后续可接入大语言模型 API 或本地模型服务

### 部署

- 后续使用 Nginx
- 后续可使用 Docker / Docker Compose

## 四、目录结构

```text
llm-news-summary-collaboration-system/
├── frontend/     # 前端项目
├── backend/      # 后端业务服务
├── ai-service/   # AI 模型调用服务
├── docs/         # 项目文档
├── deploy/       # 部署配置
├── scripts/      # 开发脚本
└── README.md      # 项目说明
```

| 目录 | 说明 |
| --- | --- |
| `frontend` | 前端项目，负责用户界面和前端交互。 |
| `backend` | 后端业务服务，提供公共配置、接口与服务端能力。 |
| `ai-service` | AI 模型调用服务，后续先使用 Mock，再接入模型能力。 |
| `docs` | 项目文档，存放需求、设计、接口和开发记录等资料。 |
| `deploy` | 部署配置，后续存放 Nginx、Docker 等部署相关文件。 |
| `scripts` | 开发脚本，后续存放开发、测试、构建和维护脚本。 |

## 五、开发阶段

1. 第 0 阶段：项目总骨架搭建。**已完成**
2. 第 1 阶段：前端基础框架搭建。**已完成**
3. 第 2 阶段：后端 FastAPI 基础框架搭建。**已完成**
4. 第 3 阶段：AI 服务框架搭建。**已完成**
5. 第 4 阶段：用户与权限 Mock 搭建。**已完成**
6. 第 5 阶段：模块并行开发。
7. 第 6 阶段：数据库接入与联调。

## 六、当前阶段说明

第 0、1、2、3、4 阶段已完成：项目已具备目录骨架、Vue 3 前端基础框架、FastAPI 后端基础框架、独立 AI 服务框架，以及用户与权限 Mock 能力。当前 AI 服务只提供固定 Mock 数据；系统尚未连接数据库、实现真实业务或调用真实大语言模型。

第 4 阶段已完成 Mock 登录、用户状态管理、路由守卫、角色权限控制，以及 `editor`、`admin` 管理后台入口控制。

测试账号：

| 角色 | 用户名 | 密码 |
| --- | --- | --- |
| 普通用户 | `user` | `123456` |
| 审核编辑 | `editor` | `123456` |
| 管理员 | `admin` | `123456` |

## 七、运行说明

### 前端

```bash
cd frontend
npm install
npm run dev
```

### 后端

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

后端启动后可访问 [健康检查接口](http://127.0.0.1:8000/api/health) 和 [Swagger 接口文档](http://127.0.0.1:8000/docs)。

### AI 服务

```bash
cd ai-service
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
```

### 三端服务地址

- frontend：[http://localhost:5173](http://localhost:5173)
- backend：[http://127.0.0.1:8000](http://127.0.0.1:8000)
- ai-service：[http://127.0.0.1:8001](http://127.0.0.1:8001)
