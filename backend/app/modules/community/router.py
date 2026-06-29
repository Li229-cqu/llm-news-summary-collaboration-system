"""社区模块路由。"""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Body, Depends, Header, Path, Query

from app.common.auth import require_login
from app.common.exceptions import AppException
from app.common.response import ApiResponse, success_response
from app.modules.auth.schema import UserInfo
from app.modules.auth.service import get_mock_user_by_token
from app.modules.community.schema import (
    AIHelperResponse,
    BlockResponse,
    CommentItem,
    CommentListResponse,
    CommentsSummaryResponse,
    CommunityPost,
    CreateCommentRequest,
    CreatePostRequest,
    FavoriteResponse,
    HotSearchItem,
    LikeResponse,
    PostListResponse,
    TagCount,
)
from app.modules.community.service import (
    ai_news_helper,
    block_user,
    create_comment,
    delete_comment,
    create_post,
    get_available_tags,
    get_comments,
    get_comments_summary,
    get_hot_search,
    get_hot_tags,
    get_hot_topics,
    get_post_detail,
    get_post_list,
    reply_comment,
    unfavorite_post as unfavorite_post_service,
    unlike_post as unlike_post_service,
    toggle_comment_like,
    toggle_post_favorite,
    toggle_post_like,
    unblock_user,
)

router = APIRouter(prefix="/api/community", tags=["community"])


def _optional_current_user(authorization: Optional[str]) -> Optional[UserInfo]:
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.removeprefix("Bearer ").strip()
    try:
        return get_mock_user_by_token(token)
    except Exception:  # noqa: BLE001
        return None


@router.get("/posts", response_model=ApiResponse[PostListResponse])
async def list_posts(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    keyword: Optional[str] = Query(None, description="关键词"),
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
) -> ApiResponse[PostListResponse]:
    current_user = _optional_current_user(authorization)
    result = get_post_list(page=page, page_size=page_size, keyword=keyword, current_user=current_user)
    return success_response(result)


@router.post("/posts", response_model=ApiResponse[CommunityPost])
async def add_post(
    request: CreatePostRequest = Body(...),
    current_user: UserInfo = Depends(require_login),
) -> ApiResponse[CommunityPost]:
    return success_response(create_post(request, current_user=current_user))


@router.get("/posts/{post_id}", response_model=ApiResponse[CommunityPost])
async def get_post(
    post_id: int = Path(..., ge=1, description="帖子ID"),
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
) -> ApiResponse[CommunityPost]:
    current_user = _optional_current_user(authorization)
    post = get_post_detail(post_id, current_user=current_user)
    if post is None:
        raise AppException(code=404, message="帖子不存在")
    return success_response(post)


@router.post("/posts/{post_id}/comments", response_model=ApiResponse[CommentItem])
async def add_comment(
    post_id: int = Path(..., ge=1, description="帖子ID"),
    request: CreateCommentRequest = Body(...),
    current_user: UserInfo = Depends(require_login),
) -> ApiResponse[CommentItem]:
    return success_response(create_comment(post_id, request, current_user=current_user))


@router.post("/comments/{comment_id}/reply", response_model=ApiResponse[CommentItem])
async def reply_to_comment(
    comment_id: int = Path(..., ge=1, description="评论ID"),
    request: CreateCommentRequest = Body(...),
    current_user: UserInfo = Depends(require_login),
) -> ApiResponse[CommentItem]:
    return success_response(reply_comment(comment_id, request, current_user=current_user))


@router.get("/posts/{post_id}/comments", response_model=ApiResponse[CommentListResponse])
async def get_post_comments(
    post_id: int = Path(..., ge=1, description="帖子ID"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
) -> ApiResponse[CommentListResponse]:
    current_user = _optional_current_user(authorization)
    result = get_comments(post_id, page=page, page_size=page_size, current_user=current_user)
    return success_response(result)


@router.post("/posts/{post_id}/like", response_model=ApiResponse[LikeResponse])
async def like_post(
    post_id: int = Path(..., ge=1, description="帖子ID"),
    current_user: UserInfo = Depends(require_login),
) -> ApiResponse[LikeResponse]:
    return success_response(toggle_post_like(post_id, current_user=current_user))


@router.delete("/posts/{post_id}/like", response_model=ApiResponse[LikeResponse])
async def unlike_post_route(
    post_id: int = Path(..., ge=1, description="帖子ID"),
    current_user: UserInfo = Depends(require_login),
) -> ApiResponse[LikeResponse]:
    return success_response(unlike_post_service(post_id, current_user=current_user))


@router.post("/posts/{post_id}/favorite", response_model=ApiResponse[FavoriteResponse])
async def favorite_post(
    post_id: int = Path(..., ge=1, description="帖子ID"),
    current_user: UserInfo = Depends(require_login),
) -> ApiResponse[FavoriteResponse]:
    return success_response(toggle_post_favorite(post_id, current_user=current_user))


@router.delete("/posts/{post_id}/favorite", response_model=ApiResponse[FavoriteResponse])
async def unfavorite_post_route(
    post_id: int = Path(..., ge=1, description="帖子ID"),
    current_user: UserInfo = Depends(require_login),
) -> ApiResponse[FavoriteResponse]:
    return success_response(unfavorite_post_service(post_id, current_user=current_user))


@router.post("/comments/{comment_id}/like", response_model=ApiResponse[LikeResponse])
async def like_comment(
    comment_id: int = Path(..., ge=1, description="评论ID"),
    current_user: UserInfo = Depends(require_login),
) -> ApiResponse[LikeResponse]:
    return success_response(toggle_comment_like(comment_id, current_user=current_user))


@router.delete("/comments/{comment_id}", response_model=ApiResponse[dict])
async def delete_comment_route(
    comment_id: int = Path(..., ge=1, description="璇勮ID"),
    current_user: UserInfo = Depends(require_login),
) -> ApiResponse[dict]:
    return success_response(delete_comment(comment_id, current_user=current_user))


@router.post("/users/{user_id}/block", response_model=ApiResponse[BlockResponse])
async def block_target_user(
    user_id: int = Path(..., ge=1, description="被拉黑用户ID"),
    current_user: UserInfo = Depends(require_login),
) -> ApiResponse[BlockResponse]:
    return success_response(block_user(user_id, current_user=current_user))


@router.delete("/users/{user_id}/block", response_model=ApiResponse[BlockResponse])
async def unblock_target_user(
    user_id: int = Path(..., ge=1, description="被取消拉黑用户ID"),
    current_user: UserInfo = Depends(require_login),
) -> ApiResponse[BlockResponse]:
    return success_response(unblock_user(user_id, current_user=current_user))


@router.get("/hot-search", response_model=ApiResponse[list[HotSearchItem]])
async def hot_search(limit: int = Query(10, ge=1, le=20, description="数量限制")) -> ApiResponse[list[HotSearchItem]]:
    return success_response(get_hot_search(limit))


@router.get("/hot-topics", response_model=ApiResponse[list[HotSearchItem]])
async def hot_topics(limit: int = Query(10, ge=1, le=20, description="数量限制")) -> ApiResponse[list[HotSearchItem]]:
    return success_response(get_hot_topics(limit))


@router.get("/hot-tags", response_model=ApiResponse[list[TagCount]])
async def hot_tags(limit: int = Query(10, ge=1, le=20, description="数量限制")) -> ApiResponse[list[TagCount]]:
    return success_response(get_hot_tags(limit))


@router.get("/available-tags", response_model=ApiResponse[list[TagCount]])
async def available_tags() -> ApiResponse[list[TagCount]]:
    return success_response(get_available_tags())


@router.post("/ai-helper", response_model=ApiResponse[AIHelperResponse])
async def ai_helper(question: str = Body(..., embed=True, description="问题")) -> ApiResponse[AIHelperResponse]:
    return success_response(await ai_news_helper(question))


@router.get("/posts/{post_id}/comments-summary", response_model=ApiResponse[CommentsSummaryResponse])
async def get_post_comments_summary(
    post_id: int = Path(..., ge=1, description="帖子ID"),
) -> ApiResponse[CommentsSummaryResponse]:
    """获取帖子评论区的 AI 总结。"""
    summary = await get_comments_summary(post_id)
    return success_response(summary)
