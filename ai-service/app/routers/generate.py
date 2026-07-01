from fastapi import APIRouter

from app.common.response import ApiResponse, success_response
from app.core.config import settings
from app.schemas.generate import GenerateRequest, GenerateResponse
from app.services.generate_service import generate_title_summary

router = APIRouter(prefix=settings.api_prefix, tags=["标题摘要生成"])


@router.post("/generate-title-summary", response_model=ApiResponse[GenerateResponse])
async def generate(request: GenerateRequest) -> ApiResponse[GenerateResponse]:
    return success_response(await generate_title_summary(request))
