from fastapi import APIRouter

from app.common.response import ApiResponse, success_response

router = APIRouter(prefix="/api/news", tags=["news"])


@router.get("/ping", response_model=ApiResponse[str])
async def ping_news() -> ApiResponse[str]:
    return success_response("news module ok")
