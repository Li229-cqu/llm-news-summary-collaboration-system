from fastapi import APIRouter

from app.common.response import ApiResponse, success_response

router = APIRouter(prefix="/api/community", tags=["community"])


@router.get("/ping", response_model=ApiResponse[str])
async def ping_community() -> ApiResponse[str]:
    return success_response("community module ok")
