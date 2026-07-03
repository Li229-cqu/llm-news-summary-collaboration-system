"""News Editor Agent — Pydantic 数据模型。

新增 AgentContext 全流程上下文 + StepMeta 元信息。
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


# ── 状态枚举 ──────────────────────────────────────────────

AgentTaskStatus = Literal["pending", "running", "completed", "failed", "cancelled"]
StepStatus = Literal["pending", "running", "completed", "failed", "skipped"]


# ═══════════════════════════════════════════════════════════
# Phase 2 新增：AgentContext —— 全流程上下文
# ═══════════════════════════════════════════════════════════

class AgentContext(BaseModel):
    """贯穿 8 步流水线的共享上下文。

    每个步骤从 context 读取上游输出，并将自己的结果写回 context。
    """

    raw_text: str = ""
    cleaned_text: Optional[str] = None
    keywords: List[str] = Field(default_factory=list)
    news_elements: Dict[str, Any] = Field(default_factory=dict)
    title: Optional[str] = None
    summary: Optional[str] = None
    summary_long: Optional[str] = None
    topic: Optional[Dict[str, Any]] = None
    timeline: Optional[Dict[str, Any]] = None
    consistency: Optional[Dict[str, Any]] = None
    edit_suggestions: Optional[Dict[str, Any]] = None
    pipeline_params: Optional[Dict[str, Any]] = None   # 侧边栏传来的参数


class StepMeta(BaseModel):
    """步骤执行的 LLM 元信息。"""

    provider: Optional[str] = None   # deepseek | zhipu | local
    model: Optional[str] = None       # 模型名称
    tokens: int = 0                   # 消耗 token 数
    latency_ms: int = 0               # LLM 调用耗时（毫秒）


# ── Pipeline 参数 ─────────────────────────────────────────

class PipelineParams(BaseModel):
    """Agent 流水线可配置参数（从侧边栏传入）。"""
    title_count: int = 3                     # 候选标题数量 (1-5)
    summary_type: str = "generate"           # 摘要类型: generate(生成式) / extract(抽取式)
    summary_style: str = "简明扼要"           # 摘要风格: 简明扼要/客观正式/通俗易懂
    title_style: str = "客观新闻型"           # 标题风格: 客观新闻型/吸引点击型/简洁概括型
    summary_length: str = "both"             # 摘要长度: short(短50-100字)/long(长200-400字)/both
    temperature: float = 0.7                 # LLM 温度 (0-1)
    model: Optional[str] = None              # 指定模型（不传则用默认）


# ── 请求体 ────────────────────────────────────────────────

class RunTextRequest(BaseModel):
    """提交文本发起 Agent 处理请求。"""

    input_text: str
    news_id: Optional[int] = None
    task_type: str = "news_editor"
    pipeline_params: Optional[PipelineParams] = None


# ── 步骤结果（统一格式） ────────────────────────────────────

class StepResult(BaseModel):
    """单个 Agent 步骤的统一输出格式。

    Phase 2 新增 meta 字段，记录 LLM 调用元信息。
    """

    step: str
    status: StepStatus
    input: Dict[str, Any] = Field(default_factory=dict)
    output: Dict[str, Any] = Field(default_factory=dict)
    time_ms: int = 0
    meta: Optional[StepMeta] = None   # Phase 2 新增


# ── 任务响应 ──────────────────────────────────────────────

class AgentTaskResponse(BaseModel):
    """创建任务后返回的简要信息。"""

    task_id: int
    status: AgentTaskStatus
    message: str


class AgentStepLogResponse(BaseModel):
    """单条步骤日志。"""

    id: int
    task_id: int
    step_order: int
    step_name: str
    step_label: str
    status: StepStatus
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    llm_request_tokens: int = 0
    llm_response_tokens: int = 0
    response_ms: int = 0
    error_message: Optional[str] = None
    retry_count: int = 0
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    created_at: str = ""


class AgentTaskDetailResponse(BaseModel):
    """任务详情，包含所有步骤日志。"""

    id: int
    user_id: int
    news_id: Optional[int] = None
    task_type: str
    input_text: str
    cleaned_text: Optional[str] = None
    status: AgentTaskStatus
    progress: int
    current_step: Optional[str] = None
    result_json: Optional[Dict[str, Any]] = None
    total_steps: int = 8
    completed_steps: int = 0
    failed_step: Optional[str] = None
    error_message: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    created_at: str = ""
    updated_at: str = ""
    steps: List[AgentStepLogResponse] = Field(default_factory=list)
