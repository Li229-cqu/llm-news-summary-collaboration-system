from fastapi import APIRouter

from app.common.response import ApiResponse, success_response

router = APIRouter(prefix="/api/user", tags=["user"])


@router.get("/ping", response_model=ApiResponse[str])
async def ping_user() -> ApiResponse[str]:
    return success_response("user module ok")
