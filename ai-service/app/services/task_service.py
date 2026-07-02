from __future__ import annotations

import uuid
import asyncio
from typing import Dict, Optional, Any
import logging

from app.schemas.generate import GenerateRequest, GenerateResponse
from app.services.generate_service import generate_title_summary

logger = logging.getLogger(__name__)

TASK_STATUS_PENDING = "pending"
TASK_STATUS_RUNNING = "running"
TASK_STATUS_COMPLETED = "completed"
TASK_STATUS_FAILED = "failed"

tasks: Dict[str, Dict[str, Any]] = {}


def create_task(request: GenerateRequest) -> str:
    task_id = str(uuid.uuid4())
    tasks[task_id] = {
        "status": TASK_STATUS_PENDING,
        "request": request,
        "result": None,
        "error": None,
    }
    return task_id


def get_task(task_id: str) -> Optional[Dict[str, Any]]:
    return tasks.get(task_id)


def update_task(task_id: str, **kwargs):
    if task_id in tasks:
        tasks[task_id].update(kwargs)


async def execute_task_background(task_id: str):
    task = tasks.get(task_id)
    if not task:
        return

    try:
        update_task(task_id, status=TASK_STATUS_RUNNING)
        result = await generate_title_summary(task["request"])
        update_task(task_id, status=TASK_STATUS_COMPLETED, result=result)
        logger.info(f"✅ 任务 {task_id} 执行完成")
    except Exception as e:
        update_task(task_id, status=TASK_STATUS_FAILED, error=str(e))
        logger.error(f"❌ 任务 {task_id} 执行失败: {str(e)}")


async def run_task_async(task_id: str):
    asyncio.create_task(execute_task_background(task_id))