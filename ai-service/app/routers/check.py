from fastapi import APIRouter

from app.common.response import ApiResponse, success_response
from app.core.config import settings
from app.schemas.check import CheckRequest, CheckResponse
from app.services.check_service import check_consistency

router = APIRouter(prefix=settings.api_prefix, tags=["一致性校验"])


@router.post("/check-consistency", response_model=ApiResponse[CheckResponse])
async def check(request: CheckRequest) -> ApiResponse[CheckResponse]:
    return success_response(check_consistency(request))
