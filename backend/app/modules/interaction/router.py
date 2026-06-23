from fastapi import APIRouter

from app.common.response import ApiResponse, success_response

router = APIRouter(prefix="/api/interaction", tags=["interaction"])


@router.get("/ping", response_model=ApiResponse[str])
async def ping_interaction() -> ApiResponse[str]:
    return success_response("interaction module ok")
