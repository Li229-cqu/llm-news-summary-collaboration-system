from fastapi import APIRouter, Depends

from app.common.auth import require_editor_or_admin
from app.common.response import ApiResponse, success_response
from app.modules.auth.schema import UserInfo

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/ping", response_model=ApiResponse[str])
async def ping_admin(_: UserInfo = Depends(require_editor_or_admin)) -> ApiResponse[str]:
    return success_response("admin module ok")
