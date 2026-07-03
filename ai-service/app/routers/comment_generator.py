from fastapi import APIRouter
from pydantic import BaseModel

from app.common.response import ApiResponse, success_response
from app.services.comment_generator_service import generate_comment

router = APIRouter(prefix="/ai", tags=["AI评论生成"])


class GenerateCommentRequest(BaseModel):
    topic: str
    context: str = ""
    sentiment: str = "neutral"


class GenerateCommentResponse(BaseModel):
    comment: str
    source: str = "llm"


@router.post("/generate-comment", response_model=ApiResponse[GenerateCommentResponse])
async def generate_comment_route(request: GenerateCommentRequest) -> ApiResponse[GenerateCommentResponse]:
    comment = await generate_comment(request.topic, request.context, request.sentiment)
    return success_response(GenerateCommentResponse(comment=comment))
