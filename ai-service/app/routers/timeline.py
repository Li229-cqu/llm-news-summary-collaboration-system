from fastapi import APIRouter

from app.common.response import ApiResponse, success_response
from app.core.config import settings
from app.schemas.timeline import TimelineGenerateRequest, TimelineGenerateResponse
from app.services.timeline_service import generate_timeline

router = APIRouter(prefix=settings.api_prefix, tags=["Timeline"])


@router.post("/generate-timeline", response_model=ApiResponse[TimelineGenerateResponse])
async def generate_timeline_api(request: TimelineGenerateRequest) -> ApiResponse[TimelineGenerateResponse]:
    return success_response(generate_timeline(request))
