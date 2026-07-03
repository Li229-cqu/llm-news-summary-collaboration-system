from fastapi import APIRouter

from app.common.response import ApiResponse, success_response
from app.core.config import settings
from app.schemas.edit_suggestions import EditSuggestionsRequest, EditSuggestionsResponse
from app.services.edit_suggestions_service import edit_suggestions

router = APIRouter(prefix=settings.api_prefix, tags=["编辑建议"])


@router.post("/edit-suggestions", response_model=ApiResponse[EditSuggestionsResponse])
async def edit_suggestions_endpoint(request: EditSuggestionsRequest) -> ApiResponse[EditSuggestionsResponse]:
    return success_response(await edit_suggestions(request))
