"""Timeline 模块接口路由。"""

from fastapi import APIRouter, Depends

from app.common.auth import require_login
from app.common.response import ApiResponse, success_response
from app.modules.auth.schema import UserInfo
from app.modules.timeline.schema import (
    TimelineGenerateResult,
    TimelineNewsListResponse,
    TimelineTopic,
)
from app.modules.timeline.service import (
    generate_timeline,
    get_timeline_detail,
    get_timeline_topics,
    get_timeline_topic_news,
)

router = APIRouter(prefix="/api/timeline", tags=["timeline"])


@router.get("/ping", response_model=ApiResponse[str])
async def ping_timeline() -> ApiResponse[str]:
    return success_response("timeline module ok")


@router.get("/topics", response_model=ApiResponse[list[TimelineTopic]])
async def list_topics() -> ApiResponse[list[TimelineTopic]]:
    return success_response(get_timeline_topics())


@router.get("/topics/{topic_id}/news", response_model=ApiResponse[TimelineNewsListResponse])
async def topic_news(topic_id: int) -> ApiResponse[TimelineNewsListResponse]:
    return success_response(get_timeline_topic_news(topic_id))


@router.get("/topics/{topic_id}", response_model=ApiResponse[TimelineGenerateResult])
async def topic_timeline(topic_id: int) -> ApiResponse[TimelineGenerateResult]:
    return success_response(await get_timeline_detail(topic_id))


@router.post("/topics/{topic_id}/generate", response_model=ApiResponse[TimelineGenerateResult])
async def generate_topic_timeline(
    topic_id: int,
    current_user: UserInfo = Depends(require_login),
) -> ApiResponse[TimelineGenerateResult]:
    return success_response(await generate_timeline(topic_id, current_user=current_user))
