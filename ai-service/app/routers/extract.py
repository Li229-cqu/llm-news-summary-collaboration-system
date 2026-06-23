from fastapi import APIRouter

from app.common.response import ApiResponse, success_response
from app.core.config import settings
from app.schemas.extract import ExtractRequest, ExtractResponse
from app.services.extract_service import extract_elements

router = APIRouter(prefix=settings.api_prefix, tags=["要素抽取"])


@router.post("/extract-elements", response_model=ApiResponse[ExtractResponse])
async def extract(request: ExtractRequest) -> ApiResponse[ExtractResponse]:
    return success_response(extract_elements(request))
