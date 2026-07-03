"""Agent Analysis — 只读分析层数据模型（Phase 4）。

为 Replay / Explain / Observability 提供响应模型。
不从 Phase 1-3 导入任何 schema，独立定义。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ── Replay 相关模型 ───────────────────────────────────────

class ReplayStep(BaseModel):
    """单步回放数据。"""
    step: str
    label: str
    order: int
    status: str  # pending | running | completed | failed
    latency_ms: int = 0
    tokens: int = 0
    provider: Optional[str] = None
    model: Optional[str] = None
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class TaskReplayResponse(BaseModel):
    """任务完整回放数据。"""
    task_id: int
    status: str
    total_steps: int = 0
    completed_steps: int = 0
    total_latency_ms: int = 0
    steps: List[ReplayStep] = Field(default_factory=list)


# ── Explain 相关模型 ─────────────────────────────────────

class ReasoningItem(BaseModel):
    """单条可解释推理。"""
    category: str = ""       # classification | timeline | consistency
    label: str = ""          # 人类可读标签
    detail: str = ""         # 推理细节
    confidence: float = 0.0  # 该推理的可信度


class ExplainResult(BaseModel):
    """AI 决策可解释性聚合结果。"""
    task_id: int
    summary: str = ""               # 一句话总结
    reasoning: List[ReasoningItem] = Field(default_factory=list)
    confidence: float = 0.0         # 综合置信度 0-1
    evidence: Dict[str, Any] = Field(default_factory=dict)


# ── Observability 相关模型 ───────────────────────────────

class ObservabilityOverview(BaseModel):
    """系统级概览统计。"""
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    success_rate: float = 0.0
    total_tokens: int = 0
    avg_latency_ms: float = 0.0
    total_steps: int = 0


class ProviderStat(BaseModel):
    """LLM 提供商分布。"""
    provider: str
    count: int = 0
    percentage: float = 0.0


class StepLatencyStat(BaseModel):
    """每步延迟统计。"""
    step_name: str
    step_label: str
    avg_ms: float = 0.0
    min_ms: int = 0
    max_ms: int = 0
    count: int = 0


class StepTokenStat(BaseModel):
    """每步 Token 统计。"""
    step_name: str
    step_label: str
    total_tokens: int = 0
    avg_tokens: float = 0.0
    count: int = 0


class ObservabilityResponse(BaseModel):
    """可观测面板完整响应。"""
    overview: ObservabilityOverview = Field(default_factory=ObservabilityOverview)
    provider_stats: List[ProviderStat] = Field(default_factory=list)
    latency_stats: List[StepLatencyStat] = Field(default_factory=list)
    token_stats: List[StepTokenStat] = Field(default_factory=list)
    trend_stats: List[TrendPoint] = Field(default_factory=list)


# ── 趋势图模型 ──────────────────────────────────────────

class TrendPoint(BaseModel):
    """每日成功/失败趋势数据点。"""
    date: str = ""                     # YYYY-MM-DD
    completed: int = 0
    failed: int = 0
    total: int = 0


# ── DAG 可视化模型 ───────────────────────────────────────

class DAGNode(BaseModel):
    """DAG 图中的单个节点。"""
    id: str                                # 步骤标识: clean, extract_keywords, ...
    label: str                             # 中文名: 正文清洗, 关键词提取, ...
    order: int                             # 执行顺序 1-8
    status: str = "pending"                # pending | running | completed | failed
    latency_ms: int = 0
    tokens: int = 0
    provider: Optional[str] = None
    model: Optional[str] = None


class DAGEdge(BaseModel):
    """DAG 图中的边（from → to）。"""
    source: str                            # 上游步骤标识
    target: str                            # 下游步骤标识


class TaskDAGResponse(BaseModel):
    """任务的 DAG 图结构（节点 + 边）。"""
    task_id: int
    status: str
    nodes: List[DAGNode] = Field(default_factory=list)
    edges: List[DAGEdge] = Field(default_factory=list)


class DAGStepData(BaseModel):
    """DAG 可视化所需的步骤数据（兼容旧端点）。"""
    step_name: str
    step_label: str
    step_order: int
    status: str
    latency_ms: int = 0
    tokens: int = 0
    provider: Optional[str] = None
    model: Optional[str] = None
