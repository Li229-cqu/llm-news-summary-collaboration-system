from fastapi import APIRouter, Depends, Query

from app.common.auth import require_login
from app.common.response import ApiResponse, success_response
from app.modules.auth.schema import UserInfo
from app.modules.profile.schema import (
    AIRecordItem,
    BrowseHistoryItem,
    CommentRecordItem,
    FavoriteItem,
    ProfileOverview,
    SubscriptionResponse,
    SubscriptionUpdateRequest,
)
from app.modules.profile.service import (
    get_ai_records,
    get_browse_history,
    get_comments,
    get_favorites,
    get_profile_overview,
    get_subscriptions,
    update_subscriptions,
)

router = APIRouter(prefix="/api/profile", tags=["profile"])


@router.get("/ping", response_model=ApiResponse[str])
async def ping_profile() -> ApiResponse[str]:
    return success_response("profile module ok")


@router.get("/overview", response_model=ApiResponse[ProfileOverview])
async def get_overview(
    current_user: UserInfo = Depends(require_login),
) -> ApiResponse[ProfileOverview]:
    """获取个人中心概览数据。"""
    data = get_profile_overview(current_user)
    return success_response(data)


@router.get("/browse-history", response_model=ApiResponse[dict])
async def get_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    current_user: UserInfo = Depends(require_login),
) -> ApiResponse[dict]:
    """获取用户浏览历史。"""
    data = get_browse_history(current_user, page=page, page_size=page_size)
    return success_response(data)


@router.get("/favorites", response_model=ApiResponse[dict])
async def get_user_favorites(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    current_user: UserInfo = Depends(require_login),
) -> ApiResponse[dict]:
    """获取用户收藏列表。"""
    data = get_favorites(current_user, page=page, page_size=page_size)
    return success_response(data)


@router.get("/comments", response_model=ApiResponse[dict])
async def get_user_comments(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    current_user: UserInfo = Depends(require_login),
) -> ApiResponse[dict]:
    """获取用户评论记录。"""
    data = get_comments(current_user, page=page, page_size=page_size)
    return success_response(data)


@router.get("/ai-records", response_model=ApiResponse[dict])
async def get_user_ai_records(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    current_user: UserInfo = Depends(require_login),
) -> ApiResponse[dict]:
    """获取用户 AI 生成记录。"""
    data = get_ai_records(current_user, page=page, page_size=page_size)
    return success_response(data)


@router.get("/subscriptions", response_model=ApiResponse[SubscriptionResponse])
async def get_user_subscriptions(
    current_user: UserInfo = Depends(require_login),
) -> ApiResponse[SubscriptionResponse]:
    """获取当前用户新闻分类订阅。"""
    data = get_subscriptions(current_user)
    return success_response(data)


@router.post("/subscriptions", response_model=ApiResponse[SubscriptionResponse])
async def update_user_subscriptions(
    request: SubscriptionUpdateRequest,
    current_user: UserInfo = Depends(require_login),
) -> ApiResponse[SubscriptionResponse]:
    """更新当前用户新闻分类订阅。"""
    data = update_subscriptions(current_user, request)
    return success_response(data)
