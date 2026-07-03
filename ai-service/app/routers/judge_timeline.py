from fastapi import APIRouter

from app.common.response import ApiResponse, success_response
from app.core.config import settings
from app.schemas.judge_timeline import JudgeTimelineRequest, JudgeTimelineResponse
from app.services.judge_timeline_service import judge_timeline

router = APIRouter(prefix=settings.api_prefix, tags=["时间线适配"])


@router.post("/judge-timeline-fit", response_model=ApiResponse[JudgeTimelineResponse])
async def judge_timeline_endpoint(request: JudgeTimelineRequest) -> ApiResponse[JudgeTimelineResponse]:
    return success_response(await judge_timeline(request))
