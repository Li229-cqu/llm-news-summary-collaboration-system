from fastapi import APIRouter

from app.common.response import ApiResponse, success_response
from app.core.config import settings
from app.schemas.match_topic import MatchTopicRequest, MatchTopicResponse
from app.services.match_topic_service import match_topic

router = APIRouter(prefix=settings.api_prefix, tags=["话题匹配"])


@router.post("/match-topic", response_model=ApiResponse[MatchTopicResponse])
async def match_topic_endpoint(request: MatchTopicRequest) -> ApiResponse[MatchTopicResponse]:
    return success_response(await match_topic(request))
