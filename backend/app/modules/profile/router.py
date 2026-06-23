from fastapi import APIRouter

from app.common.response import ApiResponse, success_response

router = APIRouter(prefix="/api/profile", tags=["profile"])


@router.get("/ping", response_model=ApiResponse[str])
async def ping_profile() -> ApiResponse[str]:
    return success_response("profile module ok")
