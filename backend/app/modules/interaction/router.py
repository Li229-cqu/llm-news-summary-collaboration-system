"""新闻互动模块接口路由。"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, Header

from app.common.auth import require_login
from app.common.response import ApiResponse, success_response
from app.modules.auth.schema import UserInfo
from app.modules.auth.service import get_mock_user_by_token
from app.modules.interaction.schema import CommentCreateRequest, CommentReplyRequest
from app.modules.interaction.service import (
    create_news_comment,
    favorite_news,
    get_news_comments,
    like_comment,
    like_news,
    reply_comment,
    unfavorite_news,
    unlike_news,
)

router = APIRouter(tags=["interaction"])


def _get_optional_current_user(authorization: Optional[str]) -> Optional[UserInfo]:
    """解析可选 Mock Token；无效 Token 按未登录状态处理。"""
    if not isinstance(authorization, str) or not authorization.startswith("Bearer "):
        return None
    return get_mock_user_by_token(authorization.removeprefix("Bearer ").strip())


@router.get("/api/interaction/ping", response_model=ApiResponse[str])
async def ping_interaction() -> ApiResponse[str]:
    """互动模块基础连通性测试接口。"""
    return success_response("interaction module ok")


@router.post("/api/news/{news_id}/like")
async def like_news_route(
    news_id: int,
    current_user: UserInfo = Depends(require_login),
) -> ApiResponse[Any]:
    """点赞新闻，需要登录。"""
    return success_response(like_news(news_id=news_id, current_user=current_user))


@router.delete("/api/news/{news_id}/like")
async def unlike_news_route(
    news_id: int,
    current_user: UserInfo = Depends(require_login),
) -> ApiResponse[Any]:
    """取消点赞新闻，需要登录。"""
    return success_response(unlike_news(news_id=news_id, current_user=current_user))


@router.post("/api/news/{news_id}/favorite")
async def favorite_news_route(
    news_id: int,
    current_user: UserInfo = Depends(require_login),
) -> ApiResponse[Any]:
    """收藏新闻，需要登录。"""
    return success_response(favorite_news(news_id=news_id, current_user=current_user))


@router.delete("/api/news/{news_id}/favorite")
async def unfavorite_news_route(
    news_id: int,
    current_user: UserInfo = Depends(require_login),
) -> ApiResponse[Any]:
    """取消收藏新闻，需要登录。"""
    return success_response(unfavorite_news(news_id=news_id, current_user=current_user))


@router.get("/api/news/{news_id}/comments")
async def news_comments(
    news_id: int,
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
) -> ApiResponse[Any]:
    """获取新闻评论；登录状态仅用于标识评论点赞状态。"""
    current_user = _get_optional_current_user(authorization)
    return success_response(get_news_comments(news_id=news_id, current_user=current_user))


@router.post("/api/news/{news_id}/comments")
async def create_comment(
    news_id: int,
    request: CommentCreateRequest,
    current_user: UserInfo = Depends(require_login),
) -> ApiResponse[Any]:
    """发布一级新闻评论，需要登录。"""
    return success_response(
        create_news_comment(news_id=news_id, request=request, current_user=current_user)
    )


@router.post("/api/comments/{comment_id}/reply")
async def create_comment_reply(
    comment_id: int,
    request: CommentReplyRequest,
    current_user: UserInfo = Depends(require_login),
) -> ApiResponse[Any]:
    """回复评论，需要登录。"""
    return success_response(
        reply_comment(comment_id=comment_id, request=request, current_user=current_user)
    )


@router.post("/api/comments/{comment_id}/like")
async def like_comment_route(
    comment_id: int,
    current_user: UserInfo = Depends(require_login),
) -> ApiResponse[Any]:
    """点赞评论，需要登录。"""
    return success_response(like_comment(comment_id=comment_id, current_user=current_user))
