"""Agent Analysis — 只读分析服务层（Phase 4）。

提供 Replay / Explain / Observability 三个维度的只读分析能力。
所有方法均从 agent_task + agent_step_log 表读取，不做任何写操作。

遵循 admin/service.py 的查询模式：execute_query / execute_one + 参数化 SQL。
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from app.db.database import execute_one, execute_query
from app.modules.agent_analysis.schema import (
    DAGEdge,
    DAGNode,
    DAGStepData,
    ExplainResult,
    ObservabilityOverview,
    ObservabilityResponse,
    ProviderStat,
    ReasoningItem,
    ReplayStep,
    StepLatencyStat,
    StepTokenStat,
    TaskDAGResponse,
    TaskReplayResponse,
    TrendPoint,
)

logger = logging.getLogger(__name__)

# ── 步骤标签映射（与 pipeline.STEP_META 同源） ──────────

STEP_LABELS: Dict[str, str] = {
    "clean": "正文清洗",
    "extract_keywords": "关键词提取",
    "extract_elements": "六要素识别",
    "generate_title_summary": "标题摘要生成",
    "match_topic": "话题匹配",
    "judge_timeline": "时间线适配",
    "check_consistency": "一致性检查",
    "edit_suggestions": "编辑建议生成",
}

# ── DAG 拓扑边（与 pipeline.STEP_META 同源） ──────────
# clean → [keywords ∥ elements] → title_summary → [topic ∥ timeline] → consistency → edit_suggestions
DAG_EDGES: List[tuple] = [
    ("clean", "extract_keywords"),
    ("clean", "extract_elements"),
    ("extract_keywords", "generate_title_summary"),
    ("extract_elements", "generate_title_summary"),
    ("generate_title_summary", "match_topic"),
    ("generate_title_summary", "judge_timeline"),
    ("match_topic", "check_consistency"),
    ("judge_timeline", "check_consistency"),
    ("check_consistency", "edit_suggestions"),
]


def _step_label(name: str) -> str:
    return STEP_LABELS.get(name, name)


def _safe_json(value: Any) -> Any:
    """安全解析 JSON 字符串为 dict，失败时返回原值或空 dict。"""
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return {}
    return {}


# ═══════════════════════════════════════════════════════════
# Replay
# ═══════════════════════════════════════════════════════════

class AnalysisService:
    """Agent 分析服务（只读）。"""

    @staticmethod
    def get_task_replay(task_id: int) -> Optional[TaskReplayResponse]:
        """获取任务完整步骤回放数据。"""
        task = execute_one(
            "SELECT id, status, total_steps, completed_steps FROM agent_task WHERE id = %s",
            [task_id],
        )
        if task is None:
            return None

        rows = execute_query(
            """SELECT step_name, step_label, step_order, status,
                      response_ms, llm_provider, llm_model,
                      llm_request_tokens, llm_response_tokens,
                      input_data, output_data, error_message
               FROM agent_step_log
               WHERE task_id = %s
               ORDER BY step_order ASC""",
            [task_id],
        )
        if rows is None:
            rows = []

        steps: List[ReplayStep] = []
        total_latency = 0
        for row in rows:
            tokens = (row.get("llm_request_tokens", 0) or 0) + (row.get("llm_response_tokens", 0) or 0)
            latency = row.get("response_ms", 0) or 0
            total_latency += latency
            steps.append(ReplayStep(
                step=row.get("step_name", ""),
                label=row.get("step_label", ""),
                order=row.get("step_order", 0),
                status=row.get("status", "pending"),
                latency_ms=latency,
                tokens=tokens,
                provider=row.get("llm_provider"),
                model=row.get("llm_model"),
                input_data=_safe_json(row.get("input_data")),
                output_data=_safe_json(row.get("output_data")),
                error=row.get("error_message"),
            ))

        return TaskReplayResponse(
            task_id=task_id,
            status=task.get("status", "unknown"),
            total_steps=task.get("total_steps", 0) or 0,
            completed_steps=task.get("completed_steps", 0) or 0,
            total_latency_ms=total_latency,
            steps=steps,
        )

    # ═══════════════════════════════════════════════════════
    # Explain
    # ═══════════════════════════════════════════════════════

    @staticmethod
    def get_task_explain(task_id: int) -> Optional[ExplainResult]:
        """推导 AI 决策过程，生成可解释性结果。"""
        task = execute_one(
            "SELECT id, status, result_json FROM agent_task WHERE id = %s",
            [task_id],
        )
        if task is None:
            return None

        rows = execute_query(
            """SELECT step_name, step_order, output_data, status
               FROM agent_step_log
               WHERE task_id = %s
               ORDER BY step_order ASC""",
            [task_id],
        )
        if rows is None:
            rows = []

        # 按步骤名索引输出数据
        step_outputs: Dict[str, Dict[str, Any]] = {}
        for row in rows:
            step_outputs[row["step_name"]] = _safe_json(row.get("output_data"))

        reasoning: List[ReasoningItem] = []
        confidence_parts: List[float] = []

        # ── 分类推理（keywords → topic） ──────────────────
        keywords_data = step_outputs.get("extract_keywords", {})
        topic_data = step_outputs.get("match_topic", {})
        primary_topic = topic_data.get("primary_topic", "")
        topic_conf = topic_data.get("confidence", 0)

        keywords = keywords_data.get("keywords", [])
        kw_text = "、".join(keywords[:3]) if keywords else "无关键信息"

        reasoning.append(ReasoningItem(
            category="classification",
            label="话题分类推理",
            detail=f"关键词「{kw_text}」指向话题「{primary_topic}」，匹配置信度 {topic_conf:.0%}",
            confidence=topic_conf,
        ))
        if topic_conf > 0:
            confidence_parts.append(topic_conf)

        # ── 时间线推理（when → timeline fit） ─────────────
        elements_data = step_outputs.get("extract_elements", {})
        timeline_data = step_outputs.get("judge_timeline", {})

        when = elements_data.get("when", "未知时间")
        is_timely = timeline_data.get("is_timely", False)
        sensitivity = timeline_data.get("time_sensitivity", "未知")

        timeline_reason = f"事件时间「{when}」，时效判断: {'符合' if is_timely else '需更新'}，敏感度: {sensitivity}"
        reasoning.append(ReasoningItem(
            category="timeline",
            label="时间线适配推理",
            detail=timeline_reason,
            confidence=0.85 if is_timely else 0.4,
        ))
        confidence_parts.append(0.85 if is_timely else 0.4)

        # ── 一致性推理 ────────────────────────────────────
        consistency_data = step_outputs.get("check_consistency", {})
        risk_level = consistency_data.get("risk_level", "unknown")
        risk_label = consistency_data.get("risk_label", "未知风险")
        check_items = consistency_data.get("check_items", [])

        consistency_detail_parts = [f"一致性检查结果: {risk_label}"]
        for item in check_items:
            icon = "✅" if item.get("status") == "pass" else "⚠️"
            consistency_detail_parts.append(f"  {icon} {item.get('name', '')}: {item.get('message', '')}")

        consistency_conf = {"low": 0.95, "medium": 0.6, "high": 0.3, "unknown": 0.5}.get(risk_level, 0.5)

        reasoning.append(ReasoningItem(
            category="consistency",
            label="一致性检查推理",
            detail="\n".join(consistency_detail_parts),
            confidence=consistency_conf,
        ))
        confidence_parts.append(consistency_conf)

        # ── 综合置信度 ────────────────────────────────────
        overall_confidence = sum(confidence_parts) / max(len(confidence_parts), 1) if confidence_parts else 0.0

        # ── 一句话摘要 ────────────────────────────────────
        summary = (
            f"该新闻被归类为「{primary_topic or '未分类'}」话题，"
            f"时效性{'符合' if is_timely else '需要更新'}，"
            f"一致性风险等级: {risk_label}。"
        )

        return ExplainResult(
            task_id=task_id,
            summary=summary,
            reasoning=reasoning,
            confidence=round(overall_confidence, 4),
            evidence={
                "keywords": keywords,
                "topic": topic_data,
                "timeline": timeline_data,
                "consistency": consistency_data,
            },
        )

    # ═══════════════════════════════════════════════════════
    # DAG Graph
    # ═══════════════════════════════════════════════════════

    @staticmethod
    def get_task_dag(task_id: int) -> Optional[TaskDAGResponse]:
        """构建任务的 DAG 图结构（节点 + 边 + 实时状态）。

        返回 nodes（含步骤状态/耗时/token）和 edges（9 条依赖关系），
        前端可直接用于 SVG/Canvas DAG 渲染。
        """
        task = execute_one(
            "SELECT id, status FROM agent_task WHERE id = %s",
            [task_id],
        )
        if task is None:
            return None

        rows = execute_query(
            """SELECT step_name, step_label, step_order, status,
                      response_ms, llm_provider, llm_model,
                      llm_request_tokens, llm_response_tokens
               FROM agent_step_log
               WHERE task_id = %s
               ORDER BY step_order ASC""",
            [task_id],
        )
        if rows is None:
            rows = []

        # 构建节点（含实时状态）
        nodes: List[DAGNode] = []
        step_status_map: Dict[str, str] = {}
        for r in rows:
            name = r.get("step_name", "")
            tokens = (r.get("llm_request_tokens", 0) or 0) + (r.get("llm_response_tokens", 0) or 0)
            status = r.get("status", "pending")
            step_status_map[name] = status
            nodes.append(DAGNode(
                id=name,
                label=r.get("step_label", _step_label(name)),
                order=r.get("step_order", 0),
                status=status,
                latency_ms=r.get("response_ms", 0) or 0,
                tokens=tokens,
                provider=r.get("llm_provider"),
                model=r.get("llm_model"),
            ))

        # 补充 step_log 中没有的步骤（状态 = pending）
        existing_names = {n.id for n in nodes}
        for name, label in STEP_LABELS.items():
            if name not in existing_names:
                order = list(STEP_LABELS.keys()).index(name) + 1
                nodes.append(DAGNode(
                    id=name,
                    label=label,
                    order=order,
                    status="pending",
                ))

        # 按 order 排序
        nodes.sort(key=lambda n: n.order)

        # 构建边
        edges: List[DAGEdge] = []
        for source, target in DAG_EDGES:
            edges.append(DAGEdge(source=source, target=target))

        return TaskDAGResponse(
            task_id=task_id,
            status=task.get("status", "unknown"),
            nodes=nodes,
            edges=edges,
        )

    # ═══════════════════════════════════════════════════════
    # DAG Steps (legacy)
    # ═══════════════════════════════════════════════════════

    @staticmethod
    def get_task_steps(task_id: int) -> List[DAGStepData]:
        """获取任务步骤数据（DAG 可视化用）。"""
        rows = execute_query(
            """SELECT step_name, step_label, step_order, status,
                      response_ms, llm_provider, llm_model,
                      llm_request_tokens, llm_response_tokens
               FROM agent_step_log
               WHERE task_id = %s
               ORDER BY step_order ASC""",
            [task_id],
        )
        if rows is None:
            return []

        return [
            DAGStepData(
                step_name=r.get("step_name", ""),
                step_label=r.get("step_label", ""),
                step_order=r.get("step_order", 0),
                status=r.get("status", "pending"),
                latency_ms=r.get("response_ms", 0) or 0,
                tokens=(r.get("llm_request_tokens", 0) or 0) + (r.get("llm_response_tokens", 0) or 0),
                provider=r.get("llm_provider"),
                model=r.get("llm_model"),
            )
            for r in rows
        ]

    # ═══════════════════════════════════════════════════════
    # Observability
    # ═══════════════════════════════════════════════════════

    @staticmethod
    def get_observability(days: int = 7) -> ObservabilityResponse:
        """聚合系统级可观测数据。"""
        since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")

        # ── 概览 ──────────────────────────────────────────
        overview = AnalysisService._get_overview(since)

        # ── Provider 分布 ─────────────────────────────────
        provider_stats = AnalysisService._get_provider_stats(since)

        # ── 延迟统计（per step） ──────────────────────────
        latency_stats = AnalysisService._get_latency_stats(since)

        # ── Token 统计（per step） ────────────────────────
        token_stats = AnalysisService._get_token_stats(since)

        # ── 成功/失败趋势（daily） ────────────────────────
        trend_stats = AnalysisService._get_trend_stats(days)

        return ObservabilityResponse(
            overview=overview,
            provider_stats=provider_stats,
            latency_stats=latency_stats,
            token_stats=token_stats,
            trend_stats=trend_stats,
        )

    @staticmethod
    def _get_overview(since: str) -> ObservabilityOverview:
        """系统概览：任务数、成功率、总 tokens、平均延迟。"""
        try:
            row = execute_one(
                """SELECT
                     COUNT(*) AS total_tasks,
                     SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) AS completed,
                     SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) AS failed
                   FROM agent_task
                   WHERE created_at >= %s""",
                [since],
            )
        except Exception:
            return ObservabilityOverview()

        if not row:
            return ObservabilityOverview()

        total_tasks = row.get("total_tasks", 0) or 0
        completed = row.get("completed", 0) or 0
        failed = row.get("failed", 0) or 0

        # Token & latency 聚合
        try:
            agg = execute_one(
                """SELECT
                     SUM(llm_request_tokens + llm_response_tokens) AS total_tokens,
                     AVG(response_ms) AS avg_latency,
                     COUNT(*) AS total_steps
                   FROM agent_step_log
                   WHERE created_at >= %s""",
                [since],
            )
        except Exception:
            agg = None

        total_tokens = (agg.get("total_tokens", 0) or 0) if agg else 0
        avg_latency = round((agg.get("avg_latency", 0) or 0), 1) if agg else 0.0
        total_steps = (agg.get("total_steps", 0) or 0) if agg else 0

        return ObservabilityOverview(
            total_tasks=total_tasks,
            completed_tasks=completed,
            failed_tasks=failed,
            success_rate=round(completed / max(total_tasks, 1), 4),
            total_tokens=total_tokens,
            avg_latency_ms=avg_latency,
            total_steps=total_steps,
        )

    @staticmethod
    def _get_provider_stats(since: str) -> List[ProviderStat]:
        """Provider 分布统计。"""
        try:
            rows = execute_query(
                """SELECT llm_provider AS provider, COUNT(*) AS count
                   FROM agent_step_log
                   WHERE created_at >= %s AND llm_provider IS NOT NULL
                   GROUP BY llm_provider
                   ORDER BY count DESC""",
                [since],
            )
        except Exception:
            return []

        if not rows:
            return []

        total = sum(r.get("count", 0) or 0 for r in rows)
        return [
            ProviderStat(
                provider=r.get("provider", "unknown"),
                count=r.get("count", 0) or 0,
                percentage=round((r.get("count", 0) or 0) / max(total, 1), 4),
            )
            for r in rows
        ]

    @staticmethod
    def _get_latency_stats(since: str) -> List[StepLatencyStat]:
        """每步延迟统计。"""
        try:
            rows = execute_query(
                """SELECT step_name, step_order,
                          AVG(response_ms) AS avg_ms,
                          MIN(response_ms) AS min_ms,
                          MAX(response_ms) AS max_ms,
                          COUNT(*) AS count
                   FROM agent_step_log
                   WHERE created_at >= %s AND status = 'completed'
                   GROUP BY step_name, step_order
                   ORDER BY step_order ASC""",
                [since],
            )
        except Exception:
            return []

        if not rows:
            return []

        return [
            StepLatencyStat(
                step_name=r.get("step_name", ""),
                step_label=_step_label(r.get("step_name", "")),
                avg_ms=round(r.get("avg_ms", 0) or 0, 1),
                min_ms=r.get("min_ms", 0) or 0,
                max_ms=r.get("max_ms", 0) or 0,
                count=r.get("count", 0) or 0,
            )
            for r in rows
            if r.get("step_name")
        ]

    @staticmethod
    def _get_token_stats(since: str) -> List[StepTokenStat]:
        """每步 Token 统计。"""
        try:
            rows = execute_query(
                """SELECT step_name, step_order,
                          SUM(llm_request_tokens + llm_response_tokens) AS total_tokens,
                          AVG(llm_request_tokens + llm_response_tokens) AS avg_tokens,
                          COUNT(*) AS count
                   FROM agent_step_log
                   WHERE created_at >= %s
                   GROUP BY step_name, step_order
                   ORDER BY step_order ASC""",
                [since],
            )
        except Exception:
            return []

        if not rows:
            return []

        return [
            StepTokenStat(
                step_name=r.get("step_name", ""),
                step_label=_step_label(r.get("step_name", "")),
                total_tokens=r.get("total_tokens", 0) or 0,
                avg_tokens=round(r.get("avg_tokens", 0) or 0, 1),
                count=r.get("count", 0) or 0,
            )
            for r in rows
            if r.get("step_name")
        ]

    @staticmethod
    def _get_trend_stats(days: int) -> List[TrendPoint]:
        """每日成功/失败趋势数据（用于折线图）。"""
        try:
            rows = execute_query(
                """SELECT
                     DATE(created_at) AS day,
                     SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) AS completed,
                     SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) AS failed,
                     COUNT(*) AS total
                   FROM agent_task
                   WHERE created_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
                   GROUP BY DATE(created_at)
                   ORDER BY day ASC""",
                [days],
            )
        except Exception:
            return []

        if not rows:
            return []

        return [
            TrendPoint(
                date=str(r.get("day", "")),
                completed=r.get("completed", 0) or 0,
                failed=r.get("failed", 0) or 0,
                total=r.get("total", 0) or 0,
            )
            for r in rows
        ]
