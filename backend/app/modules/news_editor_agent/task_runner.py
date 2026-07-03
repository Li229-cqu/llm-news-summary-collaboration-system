"""News Editor Agent — Mock Task Runner（Phase 3 SSE 升级）。

轻量级 mock 任务状态推进器：
- 非 AI，仅模拟 8 步流水线状态推进
- 每步 sleep 800~1200ms → 写入 step_log → 更新 task progress
- Phase 3: 每步通过 SSEManager 推送实时事件（step_start → step_complete → task_complete）

安全规则：
- 不调用任何 AI 服务
- 不修改 pipeline.py
- 不修改数据库 schema
- 写入 agent_task + agent_step_log（复用 AgentService 内部方法）
"""

from __future__ import annotations

import asyncio
import json
import logging
import random
import time
from typing import Any, Dict, List, Optional

from app.modules.news_editor_agent.mock_api import MOCK_STEP_OUTPUTS, STEP_META_MOCK
from app.modules.news_editor_agent.service import AgentService
from app.modules.news_editor_agent.sse import SSEEvent, sse_manager

logger = logging.getLogger(__name__)


class MockTaskRunner:
    """Mock 任务状态机：按顺序推进 8 步，每步写入 step_log 并更新进度。

    使用方式：
        await MockTaskRunner.run(task_id, input_text)

    流程：
        pending → Step 1 running → Step 1 completed → Step 2 running → ...
        → Step 8 completed → task completed
    """

    # 每步间隔范围（毫秒），模拟真实 AI 延迟
    STEP_DELAY_MIN_MS = 800
    STEP_DELAY_MAX_MS = 1200

    @staticmethod
    async def run(task_id: int, input_text: str = "") -> None:
        """执行 mock 8 步流水线。

        Args:
            task_id: 已创建的 agent_task 记录 ID
            input_text: 原始输入文本（用于 step_log 记录）
        """
        now = _now_text()

        # ── 更新状态为 running ────────────────────────────
        AgentService._update_task(task_id, {
            "status": "running",
            "started_at": now,
            "updated_at": now,
        })

        logger.info("🧪 [MockTaskRunner] 启动 mock 流水线: task_id=%s", task_id)

        collected: List[Dict[str, Any]] = []

        for i, meta in enumerate(STEP_META_MOCK):
            step_order = meta["order"]
            step_name = meta["name"]
            step_label = meta["label"]

            # ── 步骤开始：更新 current_step + SSE 推送 ───────
            AgentService._update_task(task_id, {
                "current_step": step_name,
                "updated_at": _now_text(),
            })

            # Phase 3: SSE 推送 step_start 事件
            await sse_manager.push(task_id, SSEEvent(
                event_type="step_start",
                task_id=task_id,
                step=step_name,
                step_order=step_order,
                status="running",
                timestamp=int(time.time() * 1000),
            ))

            logger.info(
                "  🧪 [MockTaskRunner] Step %s/8: %s (%s) 开始执行...",
                step_order, step_name, step_label,
            )

            # ── 模拟执行延迟 ─────────────────────────────────
            delay_ms = random.randint(
                MockTaskRunner.STEP_DELAY_MIN_MS,
                MockTaskRunner.STEP_DELAY_MAX_MS,
            )
            await asyncio.sleep(delay_ms / 1000)

            # ── 获取 mock 输出 ──────────────────────────────
            mock_output = MOCK_STEP_OUTPUTS.get(step_name, {"result": f"{step_label} 完成"})

            # ── 写入步骤日志 ─────────────────────────────────
            step_start = _now_text()
            step_completed = _now_text()
            tokens = random.randint(200, 800)

            # 构建 input_data（上一步的输出）
            input_data = {}
            if i > 0:
                prev_meta = STEP_META_MOCK[i - 1]
                input_data = MOCK_STEP_OUTPUTS.get(prev_meta["name"], {})

            AgentService._insert_step_log(
                task_id=task_id,
                step_order=step_order,
                step_name=step_name,
                step_label=step_label,
                status="completed",
                input_data=input_data,
                output_data=mock_output,
                response_ms=delay_ms,
                llm_provider="mock",
                llm_model="mock/task-runner",
                llm_tokens=tokens,
                started_at=step_start,
                completed_at=step_completed,
            )

            collected.append({
                "step": step_name,
                "label": step_label,
                "order": step_order,
                "status": "completed",
                "output": mock_output,
                "latency_ms": delay_ms,
            })

            # Phase 3: SSE 推送 step_complete 事件
            await sse_manager.push(task_id, SSEEvent(
                event_type="step_complete",
                task_id=task_id,
                step=step_name,
                step_order=step_order,
                status="completed",
                timestamp=int(time.time() * 1000),
                data={
                    "latency_ms": delay_ms,
                    "tokens": tokens,
                    "provider": "mock",
                    "model": "mock/task-runner",
                },
            ))

            # ── 更新任务进度 ─────────────────────────────────
            progress = int(step_order / 8 * 100)
            AgentService._update_task(task_id, {
                "progress": progress,
                "completed_steps": step_order,
                "updated_at": _now_text(),
            })

            logger.info(
                "  ✅ [MockTaskRunner] Step %s/8 完成 (%s ms, progress=%s%%)",
                step_order, delay_ms, progress,
            )

        # ── 任务完成 ────────────────────────────────────────
        now = _now_text()
        result_json = json.dumps(collected, ensure_ascii=False, default=str)
        cleaned_text = MOCK_STEP_OUTPUTS.get("clean", {}).get("cleaned_text", input_text[:200])

        AgentService._update_task(task_id, {
            "status": "completed",
            "progress": 100,
            "current_step": None,
            "completed_steps": 8,
            "cleaned_text": cleaned_text,
            "result_json": result_json,
            "completed_at": now,
            "updated_at": now,
        })

        total_ms = sum(r.get("latency_ms", 0) for r in collected)
        logger.info(
            "🎉 [MockTaskRunner] 任务 %s mock 流水线完成，总耗时 ≈ %s ms",
            task_id, total_ms,
        )

        # Phase 3: SSE 推送 task_complete 事件
        await sse_manager.complete(task_id, {
            "result_json": result_json,
            "total_latency_ms": total_ms,
        })


def _now_text() -> str:
    """当前时间字符串，与 service.py 格式一致。"""
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def schedule_mock_task(task_id: int, input_text: str = "") -> None:
    """使用 asyncio.create_task 后台启动 MockTaskRunner。

    与 service.py 的 schedule_agent_task() 结构一致，
    Phase 3 可直接替换为真实 pipeline 调度。
    """

    async def _runner():
        try:
            await MockTaskRunner.run(task_id, input_text)
        except Exception as exc:
            logger.exception(
                "❌ [MockTaskRunner] 后台任务 %s 崩溃: %s", task_id, exc
            )
            # Phase 3: SSE 推送错误事件
            await sse_manager.error(task_id, str(exc))
            # 标记任务失败
            try:
                AgentService._update_task(task_id, {
                    "status": "failed",
                    "error_message": str(exc),
                    "completed_at": _now_text(),
                    "updated_at": _now_text(),
                })
            except Exception:
                pass

    asyncio.create_task(_runner())
    logger.info("📋 [MockTaskRunner] 后台 mock 任务已调度: task_id=%s", task_id)
