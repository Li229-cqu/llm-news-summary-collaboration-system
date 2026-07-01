"""近 7 天阅读报告 AI 分析路由。"""

from fastapi import APIRouter

from app.common.response import ApiResponse, success_response
from app.core.config import settings
from app.schemas.profile_report import ProfileReportRequest, ProfileReportResponse
from app.services.profile_report_service import generate_profile_report

router = APIRouter(prefix=settings.api_prefix, tags=["阅读报告"])


@router.post("/profile-weekly-report", response_model=ApiResponse[ProfileReportResponse])
async def profile_weekly_report(request: ProfileReportRequest) -> ApiResponse[ProfileReportResponse]:
    """根据近 7 天聚合数据生成个性化周报文案。"""
    return success_response(generate_profile_report(request))
