"""Agent Analysis — 只读分析路由层（Phase 4）。

端点：
- GET /api/agent-analysis/task/{task_id}/replay     — 步骤回放数据
- GET /api/agent-analysis/task/{task_id}/explain     — AI 决策可解释性
- GET /api/agent-analysis/task/{task_id}/steps       — DAG 可视化步骤数据
- GET /api/agent-analysis/observability              — 系统级可观测面板
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Query

from app.common.auth import get_current_user
from app.common.exceptions import AppException
from app.common.response import ApiResponse, success_response
from app.modules.auth.schema import UserInfo
from app.modules.agent_analysis.schema import (
    DAGStepData,
    ExplainResult,
    ObservabilityResponse,
    TaskDAGResponse,
    TaskReplayResponse,
)
from app.modules.agent_analysis.service import AnalysisService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/agent-analysis", tags=["agent-analysis"])


@router.get("/task/{task_id}/replay", response_model=ApiResponse[TaskReplayResponse])
async def get_task_replay(
    task_id: int,
    current_user: UserInfo = Depends(get_current_user),
) -> ApiResponse[TaskReplayResponse]:
    """获取任务完整步骤回放数据（8 步按序排列，含时序/输入/输出）。"""
    _ = current_user
    data = AnalysisService.get_task_replay(task_id)
    if data is None:
        raise AppException(code=404, message="任务不存在")
    return success_response(data)


@router.get("/task/{task_id}/explain", response_model=ApiResponse[ExplainResult])
async def get_task_explain(
    task_id: int,
    current_user: UserInfo = Depends(get_current_user),
) -> ApiResponse[ExplainResult]:
    """获取 AI 决策可解释性结果（分类推理、时间线推理、一致性推理、综合置信度）。"""
    _ = current_user
    data = AnalysisService.get_task_explain(task_id)
    if data is None:
        raise AppException(code=404, message="任务不存在")
    return success_response(data)


@router.get("/task/{task_id}/steps", response_model=ApiResponse[list])
async def get_task_steps(
    task_id: int,
    current_user: UserInfo = Depends(get_current_user),
) -> ApiResponse[list]:
    """获取任务步骤数据（DAG 可视化用）。"""
    _ = current_user
    steps = AnalysisService.get_task_steps(task_id)
    return success_response([s.model_dump() for s in steps])


@router.get("/task/{task_id}/dag", response_model=ApiResponse[TaskDAGResponse])
async def get_task_dag(
    task_id: int,
    current_user: UserInfo = Depends(get_current_user),
) -> ApiResponse[TaskDAGResponse]:
    """获取任务 DAG 图结构（节点 + 边 + 实时状态）。

    返回完整的 DAG 拓扑图数据：
    - nodes: 8 个步骤节点（含状态/耗时/token/provider）
    - edges: 9 条依赖关系边（clean→[keywords∥elements]→title_summary→[topic∥timeline]→consistency→edit_suggestions）
    """
    _ = current_user
    data = AnalysisService.get_task_dag(task_id)
    if data is None:
        raise AppException(code=404, message="任务不存在")
    return success_response(data)


@router.get("/observability", response_model=ApiResponse[ObservabilityResponse])
async def get_observability(
    days: int = Query(default=7, ge=1, le=90, description="统计最近 N 天"),
    current_user: UserInfo = Depends(get_current_user),
) -> ApiResponse[ObservabilityResponse]:
    """获取系统级 Agent 可观测面板数据（token/latency/provider 聚合）。"""
    _ = current_user
    data = AnalysisService.get_observability(days=days)
    return success_response(data)
