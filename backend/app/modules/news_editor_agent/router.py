"""News Editor Agent — 路由层。

Phase 1 端点：
- POST /api/news-editor-agent/run-text    — 提交文本发起 Agent 处理
- GET  /api/news-editor-agent/task/{task_id} — 查询任务状态与步骤日志

Phase 3 端点：
- GET  /api/news-editor-agent/task/{task_id}/stream — SSE 实时进度流

安全规则：
- 不修改任何已有 AI 服务端点
- 不调用任何已有 AI wrapper 函数
- 仅新增独立路由
"""

from __future__ import annotations

import asyncio
import logging
from typing import Optional

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.common.exceptions import AppException
from app.common.response import ApiResponse, success_response
from app.modules.auth.schema import UserInfo
from app.common.auth import get_current_user
from app.modules.news_editor_agent.schema import (
    AgentTaskDetailResponse,
    AgentTaskResponse,
    RunTextRequest,
)
from app.modules.news_editor_agent.service import AgentService, schedule_agent_task
from app.modules.news_editor_agent.mock_api import run_mock_task, get_mock_task_detail
from app.modules.news_editor_agent.sse import sse_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/news-editor-agent", tags=["news-editor-agent"])


def _get_user_id(current_user: Optional[UserInfo]) -> int:
    """从 UserInfo 中提取 user_id。"""
    if current_user is None:
        return 0
    if isinstance(current_user, dict):
        return int(current_user.get("id") or 0)
    return int(getattr(current_user, "id", 0) or 0)


@router.get("/ping", response_model=ApiResponse[str])
async def ping_agent() -> ApiResponse[str]:
    """健康检查。"""
    return success_response("news-editor-agent module ok")


@router.post("/run-text", response_model=ApiResponse[AgentTaskResponse])
async def run_text_agent(
    request: RunTextRequest,
    current_user: UserInfo = Depends(get_current_user),
) -> ApiResponse[AgentTaskResponse]:
    """提交自由文本，启动 8 步新闻智能编辑流水线。

    流程：
    1. 校验输入非空
    2. 创建 agent_task 记录
    3. 通过 asyncio.create_task 后台异步执行 8 步流水线
    4. 立即返回 task_id，前端通过 GET /task/{task_id} 轮询进度
    """
    input_text = (request.input_text or "").strip()
    if not input_text:
        raise AppException(code=400, message="输入文本不能为空")

    if len(input_text) < 10:
        raise AppException(code=400, message="输入文本至少需要 10 个字符")

    user_id = _get_user_id(current_user)
    logger.info("📨 [Router] 收到 Agent 请求: user_id=%s, text_len=%s", user_id, len(input_text))

    # 创建任务记录
    task_response = await AgentService.create_task(
        user_id=user_id,
        input_text=input_text,
        news_id=request.news_id,
        task_type=request.task_type,
        pipeline_params=request.pipeline_params.model_dump() if request.pipeline_params else None,
    )

    # 后台调度执行
    schedule_agent_task(task_response.task_id)

    return success_response(task_response)


@router.post("/run-text-mock", response_model=ApiResponse[dict])
async def run_text_agent_mock(
    request: RunTextRequest,
    current_user: UserInfo = Depends(get_current_user),
) -> ApiResponse[dict]:
    """Phase 2 Mock 端点：提交文本，启动 Mock TaskRunner 后台状态机。

    与 /run-text 的区别：
    - 不调用真实 AI 服务
    - 不执行 DAG pipeline
    - 使用 MockTaskRunner 模拟 8 步进度推进
    - 每步写入 step_log + 更新 task progress
    - 前端通过 polling GET /task/{task_id} 获取实时状态

    流程：
    1. 校验输入 → 创建 agent_task 记录
    2. 后台启动 MockTaskRunner → sleep(800~1200ms)/步 → 写入 step_log
    3. 立即返回 task_id
    """
    input_text = (request.input_text or "").strip()
    if not input_text:
        raise AppException(code=400, message="输入文本不能为空")

    if len(input_text) < 10:
        raise AppException(code=400, message="输入文本至少需要 10 个字符")

    user_id = _get_user_id(current_user)
    logger.info("🧪 [Router] 收到 Mock Agent 请求: user_id=%s, text_len=%s", user_id, len(input_text))

    result = await run_mock_task(
        user_id=user_id,
        input_text=input_text,
        news_id=request.news_id,
        task_type=request.task_type,
    )

    return success_response(result)


@router.get("/task/{task_id}", response_model=ApiResponse[AgentTaskDetailResponse])
async def get_agent_task(
    task_id: int,
    current_user: UserInfo = Depends(get_current_user),
) -> ApiResponse[AgentTaskDetailResponse]:
    """查询 Agent 任务状态与全部步骤日志。

    前端轮询此接口获取实时进度：
    - progress: 0-100
    - current_step: 当前步骤标识
    - status: pending/running/completed/failed
    - steps: 已完成步骤的日志列表
    """
    logger.debug("🔍 [Router] 查询任务: task_id=%s", task_id)
    detail = AgentService.get_task_detail(task_id)
    return success_response(detail)


@router.get("/task/{task_id}/stream")
async def stream_agent_task(
    task_id: int,
    current_user: UserInfo = Depends(get_current_user),
) -> StreamingResponse:
    """SSE 实时进度流（Phase 3）。

    客户端通过 EventSource / fetch ReadableStream 连接此端点，
    接收 step_start → step_complete → ... → task_complete 事件序列。

    SSE 格式：
        event: step_start
        data: {"event_type":"step_start","task_id":1,...}

    连接断开时自动清理队列资源。
    """
    _ = current_user  # 仅用于鉴权，不实际使用用户信息
    logger.info("📡 [SSE] 客户端订阅 task_id=%s 的实时事件流", task_id)

    queue = await sse_manager.subscribe(task_id)

    async def event_generator():
        try:
            while True:
                event = await queue.get()
                yield f"event: {event.event_type}\ndata: {event.model_dump_json()}\n\n"
                if event.event_type in ("task_complete", "step_error"):
                    # 发送终止事件后退出循环
                    if event.event_type == "task_complete":
                        logger.info("📡 [SSE] task_id=%s 事件流正常结束", task_id)
                    break
        except asyncio.CancelledError:
            logger.info("📡 [SSE] task_id=%s 客户端断开连接", task_id)
        finally:
            await sse_manager.close(task_id)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # 禁用 nginx 代理缓冲
        },
    )
