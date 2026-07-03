from fastapi import APIRouter, HTTPException

from app.common.response import ApiResponse, success_response
from app.schemas.generate import GenerateRequest
from app.services.task_service import (
    create_task,
    get_task,
    run_task_async,
    TASK_STATUS_PENDING,
    TASK_STATUS_RUNNING,
    TASK_STATUS_COMPLETED,
    TASK_STATUS_FAILED,
)

router = APIRouter(prefix="/task", tags=["任务管理"])


@router.post("/create")
async def create_generate_task(request: GenerateRequest):
    task_id = create_task(request)
    await run_task_async(task_id)
    return success_response({"task_id": task_id})


@router.get("/{task_id}")
async def get_task_status(task_id: str):
    task = get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    response_data = {
        "task_id": task_id,
        "status": task["status"],
    }

    if task["status"] == TASK_STATUS_COMPLETED and task["result"]:
        response_data["result"] = task["result"]
    elif task["status"] == TASK_STATUS_FAILED and task["error"]:
        response_data["error"] = task["error"]

    return success_response(response_data)