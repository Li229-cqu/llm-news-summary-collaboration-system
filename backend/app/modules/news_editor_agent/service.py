"""News Editor Agent — 服务层（Phase 2：AgentContext + DAG 流水线）。

Phase 2 升级：
- run_task() 使用 AgentContext + run_pipeline() 替代 Phase 1 的 AgentPipeline.run()
- 步骤日志写入包含 LLM meta 信息（provider/model/tokens/latency）
- create_task() / get_task_detail() 保持 Phase 1 API 兼容
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.common.exceptions import AppException
from app.db.database import execute_insert, execute_one, execute_query, execute_update
from app.modules.news_editor_agent.pipeline import run_pipeline, STEP_META, _step_label, _step_order
from app.modules.news_editor_agent.sse import SSEEvent, sse_manager
from app.modules.news_editor_agent.schema import (
    AgentContext,
    AgentStepLogResponse,
    AgentTaskDetailResponse,
    AgentTaskResponse,
    AgentTaskStatus,
    StepMeta,
    StepResult,
    StepStatus,
)

logger = logging.getLogger(__name__)

# ── 内存 Mock 存储（DB 不可用时的回退） ──────────────────────

_mock_tasks: Dict[int, Dict[str, Any]] = {}
_mock_step_logs: Dict[int, List[Dict[str, Any]]] = {}
_mock_task_counter: int = 0

# ── 内存 Pipeline 参数存储（task_id → params） ──────────────

_pipeline_params_store: Dict[int, Dict[str, Any]] = {}


def _now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _dump_json(value: Any) -> Optional[str]:
    if value is None:
        return None
    return json.dumps(value, ensure_ascii=False, default=str)


# ═════════════════════════════════════════════════════════════
# AgentService
# ═════════════════════════════════════════════════════════════


class AgentService:
    """新闻智能编辑 Agent 服务。"""

    @staticmethod
    async def create_task(
        user_id: int,
        input_text: str,
        news_id: Optional[int] = None,
        task_type: str = "news_editor",
        pipeline_params: Optional[Dict[str, Any]] = None,
    ) -> AgentTaskResponse:
        """创建新的 Agent 任务记录（status=pending）。Phase 1 兼容。"""
        now = _now_text()

        try:
            task_id = execute_insert(
                """
                INSERT INTO agent_task (
                    user_id, news_id, task_type, input_text,
                    status, progress, total_steps, completed_steps,
                    created_at, updated_at
                ) VALUES (%s, %s, %s, %s, 'pending', 0, 8, 0, %s, %s)
                """,
                [user_id, news_id, task_type, input_text, now, now],
            )
            logger.info("📝 [AgentService] 任务创建成功 DB: task_id=%s, user_id=%s", task_id, user_id)
            # Store pipeline params for later retrieval
            if pipeline_params:
                _pipeline_params_store[task_id] = pipeline_params
            return AgentTaskResponse(
                task_id=task_id,
                status="pending",
                message="任务已创建，正在排队等待处理",
            )
        except Exception as exc:
            logger.warning("⚠️ [AgentService] DB 写入失败，回退内存 mock: %s", exc)
            global _mock_task_counter
            _mock_task_counter += 1
            task_id = _mock_task_counter
            _mock_tasks[task_id] = {
                "id": task_id,
                "user_id": user_id,
                "news_id": news_id,
                "task_type": task_type,
                "input_text": input_text,
                "cleaned_text": None,
                "status": "pending",
                "progress": 0,
                "current_step": None,
                "result_json": None,
                "total_steps": 8,
                "completed_steps": 0,
                "failed_step": None,
                "error_message": None,
                "started_at": None,
                "completed_at": None,
                "created_at": now,
                "updated_at": now,
            }
            _mock_step_logs[task_id] = []
            return AgentTaskResponse(
                task_id=task_id,
                status="pending",
                message="任务已创建（Mock 模式），正在排队等待处理",
            )

    @staticmethod
    async def run_task(task_id: int) -> None:
        """后台执行 DAG 流水线，通过 on_progress 回调实时更新进度。

        Phase 2 升级：
        - 构建 AgentContext 贯穿全流程
        - on_progress 回调在每步完成后立即写 DB（step_log + task progress）
        - 最终聚合 result_json 并更新 completed/failed 状态
        """
        now = _now_text()

        # ── 读取任务信息 ──────────────────────────────────
        task = AgentService._read_task(task_id)
        if task is None:
            logger.error("❌ [AgentService] 任务 %s 不存在，无法执行", task_id)
            return

        input_text = task.get("input_text", "")
        logger.info("🔄 [AgentService] Phase 2 DAG 流水线启动: task_id=%s", task_id)

        # ── 更新状态为 running ────────────────────────────
        AgentService._update_task(task_id, {
            "status": "running",
            "started_at": now,
            "updated_at": now,
        })

        # ── 构建 AgentContext ─────────────────────────────
        context = AgentContext(raw_text=input_text)
        # Inject pipeline params into context
        params = _pipeline_params_store.pop(task_id, None)
        if params:
            context.pipeline_params = params
            logger.info("📋 [AgentService] Pipeline params loaded: %s", params)

        # ── 进度跟踪 ──────────────────────────────────────
        collected: List[StepResult] = []
        failed = False
        failed_step: Optional[str] = None
        error_msg: Optional[str] = None

        async def _on_progress(result: StepResult, order: int) -> None:
            """每步完成后的实时回调：写 step_log + 更新 task 进度。"""
            nonlocal failed, failed_step, error_msg

            label = _step_label(result.step)
            meta = result.meta
            step_start = _now_text()

            if result.status == "failed":
                failed = True
                failed_step = result.step
                error_msg = f"步骤 {label} 执行失败"
                logger.error("  ❌ [AgentService] Step %s (%s) 失败", result.step, label)

            # 实时写入步骤日志
            AgentService._insert_step_log(
                task_id=task_id,
                step_order=order,
                step_name=result.step,
                step_label=label,
                status=result.status,
                input_data=result.input,
                output_data=result.output,
                response_ms=result.time_ms,
                llm_provider=meta.provider if meta else None,
                llm_model=meta.model if meta else None,
                llm_tokens=meta.tokens if meta else 0,
                started_at=step_start,
                completed_at=_now_text(),
            )

            # 实时更新任务进度
            AgentService._update_task(task_id, {
                "current_step": result.step,
                "progress": int(order / 8 * 100),
                "completed_steps": len(collected) + 1,
                "updated_at": _now_text(),
            })

            logger.info(
                "  ✅ [AgentService] Step %s/8: %s (%s ms, provider=%s)",
                order, result.step, result.time_ms,
                meta.provider if meta else "N/A",
            )

            # Phase 3: 推送 step_complete SSE 事件（含步骤输出）
            await sse_manager.push(task_id, SSEEvent(
                event_type="step_complete",
                task_id=task_id,
                step=result.step,
                step_order=order,
                status=result.status,
                timestamp=int(time.time() * 1000),
                data={
                    "latency_ms": result.time_ms,
                    "tokens": meta.tokens if meta else 0,
                    "provider": meta.provider if meta else "N/A",
                    "model": meta.model if meta else "N/A",
                    "output": result.output,  # 步骤输出数据 → 前端实时展示
                },
            ))

            collected.append(result)

        # ── Phase 3 SSE: 步骤事件回调 ──────────────────────
        async def _on_step_event(
            event_type: str,
            step_name: str,
            order: int,
            extra_data: Optional[Dict[str, Any]],
        ) -> None:
            """Pipeline hook: 将 step_start / step_error 事件推送到 SSE 广播。"""
            if event_type == "step_start":
                await sse_manager.push(task_id, SSEEvent(
                    event_type="step_start",
                    task_id=task_id,
                    step=step_name,
                    step_order=order,
                    status="running",
                    timestamp=int(time.time() * 1000),
                ))
            elif event_type == "step_error":
                await sse_manager.push(task_id, SSEEvent(
                    event_type="step_error",
                    task_id=task_id,
                    step=step_name,
                    step_order=order,
                    status="failed",
                    timestamp=int(time.time() * 1000),
                    data=extra_data or {},
                ))

        # ── 执行 DAG 流水线（带实时回调 + SSE 事件） ──────
        try:
            await run_pipeline(
                context,
                on_progress=_on_progress,
                on_step_event=_on_step_event,
            )
        except Exception as exc:
            logger.exception("❌ [AgentService] run_pipeline() 异常: %s", exc)
            failed = True
            error_msg = str(exc)
            await sse_manager.error(task_id, str(exc))

        # ── 最终状态更新 + SSE 完成事件 ───────────────────
        now = _now_text()
        if failed:
            AgentService._update_task(task_id, {
                "status": "failed",
                "progress": int(len(collected) / 8 * 100),
                "completed_steps": len(collected),
                "failed_step": failed_step,
                "error_message": error_msg,
                "completed_at": now,
                "updated_at": now,
            })
            logger.error("❌ [AgentService] 任务 %s 失败: %s", task_id, error_msg)
            if not error_msg or "run_pipeline" not in (error_msg or ""):
                await sse_manager.error(task_id, error_msg or "未知错误")
        else:
            result_json = _dump_json([r.model_dump() for r in collected])
            AgentService._update_task(task_id, {
                "status": "completed",
                "progress": 100,
                "current_step": None,
                "completed_steps": 8,
                "cleaned_text": context.cleaned_text or "",
                "result_json": result_json,
                "completed_at": now,
                "updated_at": now,
            })
            total_ms = sum(r.time_ms for r in collected)
            logger.info("🎉 [AgentService] 任务 %s DAG 流水线全部完成，总耗时 %s ms", task_id, total_ms)
            await sse_manager.complete(task_id, {
                "result_json": result_json,
                "total_latency_ms": total_ms,
            })
            # Phase 1: 同步 Agent 结果到 ai_generate_record（历史记录可见）
            try:
                AgentService._sync_to_ai_generate_record(task_id, collected, context)
            except Exception as sync_err:
                logger.warning("⚠️ [AgentService] 同步 ai_generate_record 失败: %s", sync_err)

    @staticmethod
    def get_task_detail(task_id: int) -> AgentTaskDetailResponse:
        """获取任务详情（含全部步骤日志）。Phase 1 兼容。"""
        try:
            task = AgentService._read_task(task_id)
            if task is None:
                raise AppException(code=404, message="任务不存在")

            steps = AgentService._read_step_logs(task_id)

            return AgentTaskDetailResponse(
                id=task["id"],
                user_id=task.get("user_id", 0),
                news_id=task.get("news_id"),
                task_type=task.get("task_type", "news_editor"),
                input_text=task.get("input_text", ""),
                cleaned_text=task.get("cleaned_text"),
                status=task.get("status", "pending"),
                progress=task.get("progress", 0),
                current_step=task.get("current_step"),
                result_json=task.get("result_json") if isinstance(task.get("result_json"), dict) else None,
                total_steps=task.get("total_steps", 8),
                completed_steps=task.get("completed_steps", 0),
                failed_step=task.get("failed_step"),
                error_message=task.get("error_message"),
                started_at=str(task.get("started_at", "")) if task.get("started_at") else None,
                completed_at=str(task.get("completed_at", "")) if task.get("completed_at") else None,
                created_at=str(task.get("created_at", "")),
                updated_at=str(task.get("updated_at", "")),
                steps=[
                    AgentStepLogResponse(
                        id=s["id"],
                        task_id=s["task_id"],
                        step_order=s["step_order"],
                        step_name=s["step_name"],
                        step_label=s["step_label"],
                        status=s["status"],
                        input_data=s.get("input_data") if isinstance(s.get("input_data"), dict) else None,
                        output_data=s.get("output_data") if isinstance(s.get("output_data"), dict) else None,
                        llm_provider=s.get("llm_provider"),
                        llm_model=s.get("llm_model"),
                        llm_request_tokens=s.get("llm_request_tokens", 0),
                        llm_response_tokens=s.get("llm_response_tokens", 0),
                        response_ms=s.get("response_ms", 0),
                        error_message=s.get("error_message"),
                        retry_count=s.get("retry_count", 0),
                        started_at=str(s.get("started_at", "")) if s.get("started_at") else None,
                        completed_at=str(s.get("completed_at", "")) if s.get("completed_at") else None,
                        created_at=str(s.get("created_at", "")),
                    )
                    for s in steps
                ],
            )
        except AppException:
            raise
        except Exception as exc:
            logger.exception("❌ [AgentService] 获取任务详情异常")
            raise AppException(code=500, message=f"获取任务详情失败: {str(exc)}")

    # ── 内部 DB/Mock 双通道方法 ───────────────────────────

    @staticmethod
    def _read_task(task_id: int) -> Optional[Dict[str, Any]]:
        """从 DB 或 Mock 存储读取任务。"""
        try:
            row = execute_one(
                "SELECT * FROM agent_task WHERE id = %s",
                [task_id],
            )
            return row
        except Exception as exc:
            logger.warning("⚠️ [AgentService] DB 读取任务失败，回退 mock: %s", exc)
            return _mock_tasks.get(task_id)

    @staticmethod
    def _update_task(task_id: int, updates: Dict[str, Any]) -> None:
        """更新任务字段（DB 优先，mock 兜底）。"""
        set_clauses = []
        params = []
        for key, value in updates.items():
            set_clauses.append(f"`{key}` = %s")
            params.append(value)
        params.append(task_id)

        try:
            execute_update(
                f"UPDATE agent_task SET {', '.join(set_clauses)} WHERE id = %s",
                params,
            )
        except Exception as exc:
            logger.warning("⚠️ [AgentService] DB 更新任务失败，回退 mock: %s", exc)
            if task_id in _mock_tasks:
                _mock_tasks[task_id].update(updates)

    @staticmethod
    def _insert_step_log(
        task_id: int,
        step_order: int,
        step_name: str,
        step_label: str,
        status: StepStatus,
        input_data: Dict[str, Any],
        output_data: Dict[str, Any],
        response_ms: int,
        llm_provider: Optional[str] = None,
        llm_model: Optional[str] = None,
        llm_tokens: int = 0,
        started_at: str = "",
        completed_at: str = "",
    ) -> None:
        """写入步骤日志（Phase 2：含 LLM meta 信息）。"""
        now = _now_text()
        input_json = _dump_json(input_data)
        output_json = _dump_json(output_data)

        try:
            step_id = execute_insert(
                """
                INSERT INTO agent_step_log (
                    task_id, step_order, step_name, step_label, status,
                    input_data, output_data, response_ms,
                    llm_provider, llm_model, llm_request_tokens, llm_response_tokens,
                    started_at, completed_at, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                [
                    task_id, step_order, step_name, step_label, status,
                    input_json, output_json, response_ms,
                    llm_provider, llm_model, llm_tokens, llm_tokens,
                    started_at, completed_at, now,
                ],
            )
            logger.debug("  📝 步骤日志写入 DB: step_log_id=%s", step_id)
        except Exception as exc:
            logger.warning("⚠️ [AgentService] DB 写入步骤日志失败，回退 mock: %s", exc)
            entry = {
                "id": len(_mock_step_logs.get(task_id, [])) + 1,
                "task_id": task_id,
                "step_order": step_order,
                "step_name": step_name,
                "step_label": step_label,
                "status": status,
                "input_data": input_data,
                "output_data": output_data,
                "llm_provider": llm_provider,
                "llm_model": llm_model,
                "llm_request_tokens": llm_tokens,
                "llm_response_tokens": llm_tokens,
                "response_ms": response_ms,
                "error_message": None,
                "retry_count": 0,
                "started_at": started_at,
                "completed_at": completed_at,
                "created_at": now,
            }
            _mock_step_logs.setdefault(task_id, []).append(entry)

    @staticmethod
    def _read_step_logs(task_id: int) -> List[Dict[str, Any]]:
        """从 DB 或 Mock 存储读取步骤日志。"""
        try:
            rows = execute_query(
                "SELECT * FROM agent_step_log WHERE task_id = %s ORDER BY step_order ASC",
                [task_id],
            )
            if rows is not None:
                return rows
        except Exception as exc:
            logger.warning("⚠️ [AgentService] DB 读取步骤日志失败，回退 mock: %s", exc)

        return _mock_step_logs.get(task_id, [])


    @staticmethod
    def _sync_to_ai_generate_record(
        task_id: int,
        collected: List[StepResult],
        context: AgentContext,
    ) -> None:
        """Phase 1: 将 Agent 管道结果同步写入 ai_generate_record 表。

        映射规则：
        - Step 4 (generate_title_summary) → candidate_titles + summary
        - Step 2 (extract_keywords)       → keywords
        - Step 3 (extract_elements)       → news_elements
        - Step 7 (check_consistency)      → check_result

        写入后，GET /api/ai/records 和前端 AI 生成历史即可看到 Agent 结果。
        """
        # 按步骤名索引输出
        step_outputs: Dict[str, Dict[str, Any]] = {}
        for r in collected:
            step_outputs[r.step] = r.output

        # 读取任务信息获取 input_text
        task = AgentService._read_task(task_id)
        input_text = task.get("input_text", "") if task else ""

        # 映射 Agent 步骤输出 → ai_generate_record 字段
        gen_output = step_outputs.get("generate_title_summary", {})
        kw_output = step_outputs.get("extract_keywords", {})
        elem_output = step_outputs.get("extract_elements", {})
        check_output = step_outputs.get("check_consistency", {})

        candidate_titles = gen_output.get("candidate_titles", [])
        summary_short = gen_output.get("summary_short", "")
        summary_long = gen_output.get("summary_long", "")
        keywords_raw = kw_output.get("keywords", [])
        keywords = [k.get("word", k) if isinstance(k, dict) else str(k) for k in keywords_raw]
        news_elements = {
            "who": elem_output.get("who", ""),
            "what": elem_output.get("what", ""),
            "when": elem_output.get("when", ""),
            "where": elem_output.get("where", ""),
            "why": elem_output.get("why", ""),
            "how": elem_output.get("how", ""),
        }
        check_result = {
            "risk_level": check_output.get("risk_level", "low"),
            "score": check_output.get("overall_score", 0),
            "issues": [],
            "suggestions": check_output.get("suggestions", []),
        }
        total_ms = sum(r.time_ms for r in collected)

        now = _now_text()
        user_id = task.get("user_id", 0) if task else 0

        try:
            execute_insert(
                """
                INSERT INTO ai_generate_record (
                    user_id, source, input_text, title_count, summary_type,
                    summary_style, title_style, summary_length,
                    candidate_titles, summary_short, summary_long,
                    keywords, news_elements, check_result,
                    ai_source, response_ms,
                    risk_level, risk_details, evidence_coverage,
                    evidence_json, evidence_status,
                    created_at, updated_at, status
                ) VALUES (
                    %s, %s, %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s,
                    %s, %s,
                    %s, %s, %s,
                    %s, %s,
                    %s, %s, %s
                )
                """,
                [
                    user_id,
                    "agent-pipeline",
                    input_text,
                    len(candidate_titles),
                    "generate",
                    "简明扼要",
                    "客观新闻型",
                    "both",
                    _dump_json(candidate_titles),
                    summary_short,
                    summary_long,
                    _dump_json(keywords),
                    _dump_json(news_elements),
                    _dump_json(check_result),
                    "llm",
                    total_ms,
                    check_output.get("risk_level", "low"),
                    "",
                    0.0,
                    None,
                    0,
                    now,
                    now,
                    1,
                ],
            )
            logger.info("✅ [AgentService] 任务 %s 结果已同步到 ai_generate_record", task_id)
        except Exception as exc:
            logger.warning("⚠️ [AgentService] 同步 ai_generate_record 失败（不影响主流程）: %s", exc)


# ═════════════════════════════════════════════════════════════
# 异步任务调度
# ═════════════════════════════════════════════════════════════


def schedule_agent_task(task_id: int) -> None:
    """使用 asyncio.create_task 在后台启动 Agent DAG 流水线。"""

    async def _runner():
        try:
            await AgentService.run_task(task_id)
        except Exception as exc:
            logger.exception("❌ [AgentService] 后台任务 %s 崩溃: %s", task_id, exc)

    asyncio.create_task(_runner())
    logger.info("📋 [AgentService] 后台 DAG 任务已调度: task_id=%s", task_id)
