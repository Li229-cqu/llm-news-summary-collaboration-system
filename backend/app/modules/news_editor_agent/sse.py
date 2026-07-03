"""News Editor Agent — SSE 实时推送模块（Phase 3）。

通过 asyncio.Queue 实现按 task 隔离的事件广播，支持：
- 多客户端同时订阅同一个 task_id
- step_start / step_complete / step_error / task_complete 四种事件类型
- 客户端断开自动清理
- 任务完成/出错后自动关闭队列
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any, Dict, Optional, Literal

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════
# SSE 事件模型
# ═══════════════════════════════════════════════════════════

class SSEEvent(BaseModel):
    """统一 SSE 事件格式，向前端推送流水线每一步的实时状态。"""

    event_type: Literal["step_start", "step_complete", "step_error", "task_complete"]
    task_id: int
    step: Optional[str] = None       # 步骤标识（step_start / step_complete / step_error 时必填）
    step_order: int = 0              # 步骤序号 1-8
    status: str = "running"          # running | completed | failed
    timestamp: int = 0               # epoch 毫秒
    data: Dict[str, Any] = Field(default_factory=dict)
    # data 包含可观测字段：
    #   step_start:   {}
    #   step_complete: { latency_ms, tokens, provider, model }
    #   step_error:    { error }
    #   task_complete: { result_json, total_latency_ms }


# ═══════════════════════════════════════════════════════════
# SSE Manager —— 核心事件广播引擎
# ═══════════════════════════════════════════════════════════

class SSEManager:
    """按 task_id 管理的异步事件队列。

    每个 task_id 对应一个 asyncio.Queue，支持：
    - subscribe(task_id): 客户端订阅，返回事件队列
    - push(task_id, event): 广播事件到所有订阅者
    - complete(task_id) / error(task_id, msg): 发送终止事件
    - close(task_id): 清理队列资源

    使用 refcount 确保多客户端时不会提前清理。
    """

    def __init__(self):
        self._queues: Dict[int, asyncio.Queue] = {}
        self._refcounts: Dict[int, int] = {}
        self._lock = asyncio.Lock()

    async def subscribe(self, task_id: int) -> asyncio.Queue:
        """订阅 task 的事件流。每个调用获得独立消费者队列。

        返回该 task 的专属队列，供 StreamingResponse 的 event_generator 消费。
        """
        async with self._lock:
            if task_id not in self._queues:
                self._queues[task_id] = asyncio.Queue(maxsize=256)
                self._refcounts[task_id] = 0
                logger.info("📡 [SSE] 为 task_id=%s 创建事件队列", task_id)
            self._refcounts[task_id] += 1
            logger.debug("📡 [SSE] task_id=%s 新增订阅者，当前连接数=%s", task_id, self._refcounts[task_id])
            return self._queues[task_id]

    async def push(self, task_id: int, event: SSEEvent) -> None:
        """向指定 task 的所有订阅者广播事件。

        如果 task 还没有队列，自动创建（以便缓冲事件，等待客户端连接）。
        队列满时不阻塞，事件被丢弃（防止慢客户端拖慢流水线）。
        """
        async with self._lock:
            queue = self._queues.get(task_id)
            if queue is None:
                # 自动创建队列以缓冲事件（服务端先于客户端推送的场景）
                queue = asyncio.Queue(maxsize=256)
                self._queues[task_id] = queue
                self._refcounts[task_id] = 0
                logger.info("📡 [SSE] task_id=%s 自动创建事件队列（缓冲模式）", task_id)

        try:
            queue.put_nowait(event)
        except asyncio.QueueFull:
            logger.warning("⚠️ [SSE] task_id=%s 事件队列已满，丢弃事件: %s", task_id, event.event_type)

    async def complete(self, task_id: int, result_data: Optional[Dict[str, Any]] = None) -> None:
        """任务正常完成，发送 task_complete 事件。"""
        event = SSEEvent(
            event_type="task_complete",
            task_id=task_id,
            status="completed",
            timestamp=int(time.time() * 1000),
            data=result_data or {},
        )
        await self.push(task_id, event)
        logger.info("✅ [SSE] task_id=%s 发送 task_complete 事件", task_id)

    async def error(self, task_id: int, error_message: str) -> None:
        """任务执行失败，发送 task_complete（status=failed）事件。"""
        event = SSEEvent(
            event_type="task_complete",
            task_id=task_id,
            status="failed",
            timestamp=int(time.time() * 1000),
            data={"error": error_message},
        )
        await self.push(task_id, event)
        logger.error("❌ [SSE] task_id=%s 发送 task_complete (failed): %s", task_id, error_message)

    async def close(self, task_id: int) -> None:
        """客户端断开连接时调用，减少引用计数并在计数归零时清理队列。"""
        async with self._lock:
            if task_id not in self._refcounts:
                return
            self._refcounts[task_id] -= 1
            logger.debug("📡 [SSE] task_id=%s 断开一个订阅者，剩余连接数=%s", task_id, self._refcounts[task_id])
            if self._refcounts[task_id] <= 0:
                queue = self._queues.pop(task_id, None)
                self._refcounts.pop(task_id, None)
                if queue is not None:
                    # 清空队列中的剩余事件，防止内存泄漏
                    while not queue.empty():
                        try:
                            queue.get_nowait()
                        except asyncio.QueueEmpty:
                            break
                logger.info("🗑️ [SSE] task_id=%s 队列已清理（无活跃订阅者）", task_id)


# ═══════════════════════════════════════════════════════════
# 全局单例
# ═══════════════════════════════════════════════════════════

sse_manager = SSEManager()
