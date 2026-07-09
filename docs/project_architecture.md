# 项目架构图

本文档给出“基于大语言模型的智能新闻摘要与协同互动系统”的项目架构图。图中按访问层、业务服务层、AI 能力层、数据层和外部数据源划分，适合放入项目报告、README 或答辩材料。

```mermaid
flowchart LR
    %% ===== 用户与前端 =====
    U["用户<br/>普通用户 / 编辑 / 管理员"]

    subgraph FE["前端应用 frontend<br/>Vue 3 + Vite + TypeScript + Element Plus"]
        FEViews["页面视图<br/>首页 / 新闻详情 / AI 生成 / 社区 / 时间线 / 个人中心 / 管理后台"]
        FEState["状态与路由<br/>Pinia Store / Vue Router"]
        FEApi["API 封装<br/>Axios 请求拦截 / Token 注入 / 错误处理"]
    end

    %% ===== 后端 =====
    subgraph BE["后端服务 backend<br/>FastAPI + PyMySQL"]
        BEMain["应用入口<br/>app.main / CORS / 异常处理 / uploads 静态资源"]
        Auth["认证与用户<br/>auth / user / profile"]
        News["新闻业务<br/>news / interaction"]
        Community["社区协同<br/>community / 评论 / AI 会话"]
        Timeline["事件脉络<br/>timeline / 热点主题 / 聚类"]
        Admin["管理后台<br/>admin / 系统配置 / 操作日志 / 备份记录"]
        AIGateway["AI 业务网关<br/>ai / news_editor_agent / agent_analysis"]
        MockFallback["Mock 兜底数据<br/>数据库异常或本地演示"]
    end

    %% ===== AI 服务 =====
    subgraph AIS["AI 服务 ai-service<br/>FastAPI 独立服务"]
        AIRouters["AI 接口<br/>generate / extract / check / evidence / timeline / polish / chat"]
        AIServices["AI 编排服务<br/>Prompt Builder / LLM Client / Parser / Task Service"]
        AIMock["Mock 输出<br/>默认本地演示模式"]
    end

    %% ===== 数据层 =====
    subgraph DBL["数据层 database<br/>MySQL 8.0"]
        MySQL[("llm_news_system")]
        CoreTables["核心表<br/>user / news / news_category / news_topic"]
        InteractionTables["互动表<br/>news_comment / user_like / favorite / browse_history"]
        CommunityTables["社区表<br/>community_post / post_comment / community_ai_session / community_ai_message"]
        AITables["AI 与配置表<br/>ai_generate_record / system_config / profile_weekly_report_cache"]
        OpsTables["运维与扩展表<br/>crawl_log / upload_file / event_timeline / hot_topic"]
        Migrations["schema.sql / seed.sql / migrations"]
    end

    %% ===== 爬虫与外部服务 =====
    subgraph EXT["外部数据与模型"]
        RSS["光明网 RSS 新闻源<br/>时政 / 国际 / 财经 / 社会 / 娱乐 / 科技 / 体育"]
        LLM["真实大模型 API<br/>DeepSeek / 智谱等"]
    end

    subgraph CRAWLER["新闻爬虫 scripts/crawlers"]
        Crawler["RSS 爬虫<br/>增量抓取 / 正文解析 / 入库记录"]
    end

    %% ===== 主访问链路 =====
    U --> FEViews
    FEViews --> FEState
    FEState --> FEApi
    FEApi -- "HTTP /api/*" --> BEMain

    BEMain --> Auth
    BEMain --> News
    BEMain --> Community
    BEMain --> Timeline
    BEMain --> Admin
    BEMain --> AIGateway

    %% ===== 后端数据访问 =====
    Auth --> MySQL
    News --> MySQL
    Community --> MySQL
    Timeline --> MySQL
    Admin --> MySQL
    AIGateway --> MySQL
    BEMain -. "数据库不可用时" .-> MockFallback

    %% ===== AI 调用链路 =====
    AIGateway -- "HTTP /ai/*" --> AIRouters
    AIRouters --> AIServices
    AIServices -. "mock 模式" .-> AIMock
    AIServices -- "真实模型模式" --> LLM
    AIServices -. "读取 / 同步 AI 配置" .-> Admin
    AIRouters --> AITables

    %% ===== 爬虫入库链路 =====
    RSS --> Crawler
    Crawler --> MySQL
    Crawler --> OpsTables

    %% ===== 数据库结构关系 =====
    MySQL --> CoreTables
    MySQL --> InteractionTables
    MySQL --> CommunityTables
    MySQL --> AITables
    MySQL --> OpsTables
    Migrations --> MySQL

    %% ===== 样式 =====
    classDef user fill:#f4f4f5,stroke:#71717a,color:#111827
    classDef frontend fill:#ecfeff,stroke:#0891b2,color:#164e63
    classDef backend fill:#eef2ff,stroke:#4f46e5,color:#312e81
    classDef ai fill:#f0fdf4,stroke:#16a34a,color:#14532d
    classDef data fill:#fff7ed,stroke:#f97316,color:#7c2d12
    classDef external fill:#fdf2f8,stroke:#db2777,color:#831843

    class U user
    class FEViews,FEState,FEApi frontend
    class BEMain,Auth,News,Community,Timeline,Admin,AIGateway,MockFallback backend
    class AIRouters,AIServices,AIMock ai
    class MySQL,CoreTables,InteractionTables,CommunityTables,AITables,OpsTables,Migrations data
    class RSS,LLM,Crawler external
```

## 架构说明

1. 前端只调用后端 `backend` 的 `/api/*` 接口，不直接访问 `ai-service` 或数据库。
2. 后端负责统一认证、业务接口、数据库访问、文件上传资源和 AI 调用编排。
3. AI 能力独立部署为 `ai-service`，默认支持 mock 输出，也可以通过配置切换到真实大模型 API。
4. MySQL 是核心数据存储，承载用户、新闻、互动、社区、AI 生成记录、系统配置、爬虫日志和事件时间线等数据。
5. RSS 爬虫作为离线或定时任务运行，从光明网 RSS 源抓取新闻并写入 MySQL。
6. 后端检测数据库不可用时保留 mock fallback，便于本地演示和调试。

