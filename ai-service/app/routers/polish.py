"""事件脉络话题润色路由。"""

from fastapi import APIRouter

from app.common.response import ApiResponse, success_response
from app.core.config import settings
from app.schemas.polish import PolishTimelineTopicRequest, PolishTimelineTopicResponse
from app.services.polish_service import polish_timeline_topic

router = APIRouter(prefix=settings.api_prefix, tags=["Timeline Polish"])


@router.post("/polish-timeline-topic", response_model=ApiResponse[PolishTimelineTopicResponse])
async def polish_topic(request: PolishTimelineTopicRequest) -> ApiResponse[PolishTimelineTopicResponse]:
    """对事件脉络话题候选结果进行 LLM 文本润色。"""
    result = await polish_timeline_topic(request)
    return success_response(result)
