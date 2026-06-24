# 基于大语言模型的智能新闻摘要与协同互动系统：AI 服务

## 一、AI 服务说明

`ai-service` 是基于大语言模型的智能新闻摘要与协同互动系统的独立 AI 服务，负责标题摘要生成、关键词和新闻要素抽取、一致性质量校验、AI 新闻助手问答等能力。

## 二、当前阶段

当前处于第 3 阶段：AI 服务框架搭建。

当前所有结果均为 Mock 数据，不调用真实大语言模型 API；真实模型接入将在后续阶段完成。

## 三、技术栈

- FastAPI
- Uvicorn
- Pydantic
- python-dotenv
- httpx

## 四、目录结构说明

```text
app/
├── main.py       # AI 服务入口
├── core/         # 配置文件
├── common/       # 统一响应和异常处理
├── schemas/      # 请求和响应模型
├── services/     # AI 能力服务层
├── routers/      # 接口路由
└── mock/         # Mock 输出数据
```

## 五、当前已完成接口

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/ai/health` | AI 服务健康检查。 |
| POST | `/ai/generate-title-summary` | 标题摘要生成 Mock。 |
| POST | `/ai/extract-elements` | 关键词和新闻要素抽取 Mock。 |
| POST | `/ai/check-consistency` | 一致性质量校验 Mock。 |
| POST | `/ai/chat` | AI 新闻助手问答 Mock。 |
| POST | `/ai/generate-timeline` | 多源事件脉络时间线 Mock。 |

## 六、运行方式

在 `ai-service` 目录执行：

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
```

> `app.main:app` 中前半部分表示模块路径，后半部分表示 FastAPI 应用对象。

## 七、接口文档访问

- Swagger 文档：[http://127.0.0.1:8001/docs](http://127.0.0.1:8001/docs)
- ReDoc 文档：[http://127.0.0.1:8001/redoc](http://127.0.0.1:8001/redoc)
- 健康检查：[http://127.0.0.1:8001/ai/health](http://127.0.0.1:8001/ai/health)

## 八、当前注意事项

1. 当前不连接数据库。
2. 当前不调用真实大模型 API。
3. 当前不保存生成记录。
4. 当前只返回 Mock 数据。
5. 真实大模型接入放到后续阶段。
6. Timeline 接口会基于传入的 `news_items` 按发布时间排序生成事件脉络。

## 九、与 backend 的关系

前端不直接调用 `ai-service`。调用链如下：

```text
frontend → backend → ai-service
```

前端调用 `backend`，再由 `backend` 调用 `ai-service`。这样可以避免前端暴露大模型 API Key，也方便后续统一权限和生成记录管理。
