# 基于大语言模型的智能新闻摘要与协同互动系统：后端服务

## 一、后端项目说明

`backend` 是基于大语言模型的智能新闻摘要与协同互动系统的后端业务服务。

当前处于第 2 阶段：FastAPI 基础框架搭建。本阶段建立了后端公共配置、统一响应、异常处理、模块路由、Schema 和 Mock 数据基础，为后续业务模块开发与前后端联调提供支撑。

## 二、技术栈

- FastAPI
- Uvicorn
- Pydantic
- python-dotenv
- httpx

## 三、目录结构说明

```text
app/
├── main.py       # 后端服务入口
├── core/         # 配置文件
├── common/       # 统一响应和异常处理
├── modules/      # 业务模块
└── mock/         # 前期 Mock 数据
```

## 四、当前已完成内容

1. FastAPI 项目初始化。
2. CORS 配置。
3. 统一响应格式。
4. 统一异常处理。
5. 健康检查接口。
6. 业务模块路由占位。
7. Pydantic Schema 占位。
8. Mock 数据目录占位。
9. Mock 用户认证与权限校验。

## 五、运行方式

建议先启用本项目的独立虚拟环境：

```powershell
.\.venv\Scripts\Activate.ps1
```

安装依赖：

```bash
pip install -r requirements.txt
```

启动服务：

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

> `app.main:app` 中前半部分表示模块路径，后半部分表示 FastAPI 应用对象。

## 六、接口文档访问

- Swagger 文档：[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- ReDoc 文档：[http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- 健康检查：[http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)

## 七、当前注意事项

1. 当前不连接数据库。
2. 当前不实现真实登录。
3. 当前不实现真实新闻、AI、社区业务。
4. 当前不调用 AI 服务。
5. 当前只完成后端基础框架。

## 八、用户与权限 Mock

当前 `auth` 模块已支持 Mock 登录、退出登录、获取当前用户和角色权限校验。Token 为固定 Mock Token，不是真实 JWT；权限判断基于 Mock 用户数据，当前不连接数据库。

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| POST | `/api/auth/login` | Mock 登录。 |
| POST | `/api/auth/logout` | Mock 退出登录。 |
| GET | `/api/auth/me` | 获取当前 Mock 用户。 |
| GET | `/api/auth/check-login` | 登录状态校验。 |
| GET | `/api/auth/check-editor` | 审核编辑或管理员权限校验。 |
| GET | `/api/auth/check-admin` | 管理员权限校验。 |

## 九、下一阶段

下一阶段将搭建 `ai-service` 独立 AI 服务框架，先提供 Mock 接口，再逐步预留大语言模型 API 或本地模型服务接入能力。
