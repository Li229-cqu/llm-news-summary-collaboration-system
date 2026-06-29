from fastapi import APIRouter

from app.common.response import ApiResponse, success_response
from app.core.config import settings
from app.schemas.comment_summary import CommentSummaryRequest, CommentSummaryResponse
from app.services.comment_summary_service import summarize_comments

router = APIRouter(prefix=settings.api_prefix, tags=["评论总结"])


@router.post("/comment-summary", response_model=ApiResponse[CommentSummaryResponse])
async def summarize(request: CommentSummaryRequest) -> ApiResponse[CommentSummaryResponse]:
    return success_response(summarize_comments(request))