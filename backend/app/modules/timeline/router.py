""""""

from __future__ import annotations

from typing import Any, List


from fastapi import APIRouter, Depends

from app.common.auth import require_editor_or_admin, require_login
from app.common.response import ApiResponse, success_response
from app.modules.auth.schema import UserInfo
from app.modules.timeline.schema import (
    AutoClusterRequest,
    TimelineGenerateResult,
    TimelineNewsListResponse,
    TimelineTopic,
)
from app.modules.timeline.service import (
    auto_cluster_timeline_topics,
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


@router.post("/topics/auto-cluster", response_model=ApiResponse[Any])
async def auto_cluster_topics(
    request: "AutoClusterRequest",
    current_user: UserInfo = Depends(require_editor_or_admin),
) -> ApiResponse[Any]:
    """后台批量自动聚类生成事件脉络话题。

    dry_run=true 时只返回预览结果，不写库。
    正式发布需要 dry_run=false + confirm=true。
    """
    return success_response(auto_cluster_timeline_topics(request))
