"""社区模块路由。"""

from __future__ import annotations

import os
import secrets
import time
from pathlib import Path as FilePath
from typing import List, Optional

from fastapi import APIRouter, Body, Depends, File, Header, Path, Query, UploadFile

from app.common.auth import require_login
from app.common.exceptions import AppException
from app.common.response import ApiResponse, success_response
from app.modules.auth.schema import UserInfo
from app.modules.auth.service import get_mock_user_by_token
from app.modules.community.schema import (
    AIHelperResponse,
    BlockResponse,
    CommentItem,
    CommentLikeResult,
    CommentListResponse,
    CommentsSummaryRequest,
    CommentsSummaryResponse,
    CommunityAiMessageCreate,
    CommunityAiMessageSendResponse,
    CommunityAiSessionCreate,
    CommunityAiSessionDetailResponse,
    CommunityAiSessionItem,
    CommunityAiSessionListResponse,
    CommunityPost,
    CreateCommentRequest,
    CreatePostRequest,
    FavoriteResponse,
    HotSearchItem,
    LikeResponse,
    MyCommunityPostListResponse,
    PostListResponse,
    PostMediaUploadResponse,
    ReceivedInteractionListResponse,
    TagCount,
)
from app.modules.community.service import (
    ai_news_helper,
    block_user,
    create_ai_session,
    create_comment,
    delete_ai_session,
    delete_comment,
    create_post,
    generate_comments_summary,
    get_ai_session_detail,
    get_ai_session_list,
    get_available_tags,
    get_comments,
    get_comments_summary,
    get_hot_search,
    get_hot_tags,
    get_hot_topics,
    get_my_posts,
    get_post_detail,
    get_post_list,
    get_received_likes,
    get_received_comments,
    get_received_favorites,
    reply_comment,
    send_ai_message,
    unfavorite_post as unfavorite_post_service,
    unlike_post as unlike_post_service,
    toggle_comment_like,
    toggle_post_favorite,
    toggle_post_like,
    unblock_user,
)

router = APIRouter(prefix="/api/community", tags=["community"])

MAX_UPLOAD_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}

BASE_DIR = FilePath(__file__).resolve().parents[3]
UPLOADS_DIR = BASE_DIR / "uploads" / "posts"


@router.post(
    "/posts/media/upload",
    response_model=ApiResponse[PostMediaUploadResponse],
)
async def upload_post_media(
    file: UploadFile = File(...),
    current_user: UserInfo = Depends(require_login),
) -> ApiResponse[PostMediaUploadResponse]:
    """上传帖子图片，需要登录。"""
    content_type = file.content_type or ""
    if content_type not in ALLOWED_IMAGE_TYPES:
        raise AppException(
            code=400,
            message=f"不支持的图片类型：{content_type}，仅支持 JPG/PNG/GIF/WebP",
        )

    ext = os.path.splitext(file.filename or ".jpg")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise AppException(
            code=400,
            message=f"不支持的图片格式：{ext}，仅支持 JPG/PNG/GIF/WebP",
        )

    contents = await file.read()
    if len(contents) > MAX_UPLOAD_SIZE:
        raise AppException(code=400, message="图片大小不能超过 5MB")

    month_dir = time.strftime("%Y/%m")
    target_dir = UPLOADS_DIR / month_dir
    target_dir.mkdir(parents=True, exist_ok=True)

    timestamp = int(time.time() * 1000)
    random_suffix = secrets.token_hex(4)
    filename = f"{timestamp}_{random_suffix}{ext}"
    file_path = target_dir / filename

    file_path.write_bytes(contents)

    url = f"/uploads/posts/{month_dir}/{filename}"
    return success_response(
        PostMediaUploadResponse(
            url=url,
            filename=filename,
            size=len(contents),
        )
    )


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
    tag: Optional[str] = Query(None, description="标签筛选"),
    sort: Optional[str] = Query("hot", description="排序方式：hot/latest"),
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
) -> ApiResponse[PostListResponse]:
    current_user = _optional_current_user(authorization)
    result = get_post_list(page=page, page_size=page_size, keyword=keyword, tag=tag, sort=sort, current_user=current_user)
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


@router.post("/posts/{post_id}/browse", response_model=ApiResponse[dict])
async def browse_post(
    post_id: int = Path(..., ge=1, description="帖子ID"),
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
) -> ApiResponse[dict]:
    """记录社区帖子浏览历史。"""
    from app.modules.community.service import record_post_browse
    current_user = _optional_current_user(authorization)
    result = record_post_browse(post_id, current_user=current_user)
    return success_response(result)


@router.get("/posts/{post_id}/favorite/status", response_model=ApiResponse[dict])
async def get_post_favorite_status(
    post_id: int = Path(..., ge=1, description="帖子ID"),
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
) -> ApiResponse[dict]:
    """查询当前用户是否收藏了该帖子。"""
    from app.modules.community.service import get_post_favorite_status as get_fav_status
    current_user = _optional_current_user(authorization)
    result = get_fav_status(post_id, current_user=current_user)
    return success_response(result)


@router.post("/comments/{comment_id}/like", response_model=ApiResponse[CommentLikeResult])
async def like_comment(
    comment_id: int = Path(..., ge=1, description="评论ID"),
    current_user: UserInfo = Depends(require_login),
) -> ApiResponse[CommentLikeResult]:
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


@router.post("/comments/summary", response_model=ApiResponse[CommentsSummaryResponse])
async def create_comments_summary(
    request: CommentsSummaryRequest = Body(..., description="评论总结请求"),
) -> ApiResponse[CommentsSummaryResponse]:
    """生成评论总结（接收评论列表，调用 AI 服务）。"""
    summary = await generate_comments_summary(request.comments)
    return success_response(summary)


# ─── AI 会话接口 ──────────────────────────────────────────────


@router.post("/ai-sessions", response_model=ApiResponse[CommunityAiSessionDetailResponse])
async def create_ai_session_route(
    request: CommunityAiSessionCreate = Body(...),
    current_user: UserInfo = Depends(require_login),
) -> ApiResponse[CommunityAiSessionDetailResponse]:
    """创建 AI 会话，可选携带首条问题。"""
    result = await create_ai_session(request, current_user)
    return success_response(result)


@router.get("/ai-sessions", response_model=ApiResponse[CommunityAiSessionListResponse])
async def list_ai_sessions(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: UserInfo = Depends(require_login),
) -> ApiResponse[CommunityAiSessionListResponse]:
    """获取当前用户的 AI 会话列表。"""
    result = get_ai_session_list(page=page, page_size=page_size, current_user=current_user)
    return success_response(result)


@router.get("/ai-sessions/{session_id}", response_model=ApiResponse[CommunityAiSessionDetailResponse])
async def get_ai_session_detail_route(
    session_id: int = Path(..., ge=1, description="会话ID"),
    current_user: UserInfo = Depends(require_login),
) -> ApiResponse[CommunityAiSessionDetailResponse]:
    """获取单个 AI 会话详情和消息列表。"""
    result = get_ai_session_detail(session_id, current_user=current_user)
    return success_response(result)


@router.post("/ai-sessions/{session_id}/messages", response_model=ApiResponse[CommunityAiMessageSendResponse])
async def send_ai_message_route(
    session_id: int = Path(..., ge=1, description="会话ID"),
    request: CommunityAiMessageCreate = Body(...),
    current_user: UserInfo = Depends(require_login),
) -> ApiResponse[CommunityAiMessageSendResponse]:
    """在已有会话中连续追问。"""
    result = await send_ai_message(session_id, request, current_user)
    return success_response(result)


@router.delete("/ai-sessions/{session_id}", response_model=ApiResponse[dict])
async def delete_ai_session_route(
    session_id: int = Path(..., ge=1, description="会话ID"),
    current_user: UserInfo = Depends(require_login),
) -> ApiResponse[dict]:
    """软删除 AI 会话。"""
    result = delete_ai_session(session_id, current_user=current_user)
    return success_response(result)


# ─── 我的帖子与互动接口 ──────────────────────────────────────────


@router.get("/me/posts", response_model=ApiResponse[MyCommunityPostListResponse])
async def my_posts(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=50, description="每页数量"),
    keyword: Optional[str] = Query(None, description="关键词"),
    current_user: UserInfo = Depends(require_login),
) -> ApiResponse[MyCommunityPostListResponse]:
    """获取当前登录用户自己的帖子列表。"""
    result = get_my_posts(page=page, page_size=page_size, keyword=keyword, current_user=current_user)
    return success_response(result)


@router.get("/me/interactions/likes", response_model=ApiResponse[ReceivedInteractionListResponse])
async def received_likes(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=50, description="每页数量"),
    current_user: UserInfo = Depends(require_login),
) -> ApiResponse[ReceivedInteractionListResponse]:
    """获取别人对我帖子的点赞。"""
    result = get_received_likes(page=page, page_size=page_size, current_user=current_user)
    return success_response(result)


@router.get("/me/interactions/comments", response_model=ApiResponse[ReceivedInteractionListResponse])
async def received_comments(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=50, description="每页数量"),
    current_user: UserInfo = Depends(require_login),
) -> ApiResponse[ReceivedInteractionListResponse]:
    """获取别人评论我帖子的记录。"""
    result = get_received_comments(page=page, page_size=page_size, current_user=current_user)
    return success_response(result)


@router.get("/me/interactions/favorites", response_model=ApiResponse[ReceivedInteractionListResponse])
async def received_favorites(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=50, description="每页数量"),
    current_user: UserInfo = Depends(require_login),
) -> ApiResponse[ReceivedInteractionListResponse]:
    """获取别人收藏我帖子的记录。"""
    result = get_received_favorites(page=page, page_size=page_size, current_user=current_user)
    return success_response(result)
