from fastapi import APIRouter, Query, Path, Body
from typing import List, Optional

from app.common.response import ApiResponse, success_response, error_response
from app.modules.community.schema import (
    CommunityPost,
    CreatePostRequest,
    PostListResponse,
    CommentItem,
    CreateCommentRequest,
    CommentListResponse,
    HotSearchItem,
    AIHelperResponse,
    LikeResponse,
)
from app.modules.community.service import (
    create_post,
    get_post_list,
    get_post_detail,
    create_comment,
    get_comments,
    toggle_post_like,
    get_hot_search,
    ai_news_helper,
)

router = APIRouter(prefix="/api/community", tags=["community"])


@router.get("/posts", response_model=ApiResponse[PostListResponse])
async def get_posts(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
):
    result = get_post_list(page, page_size)
    return success_response(result)


@router.post("/posts", response_model=ApiResponse[CommunityPost])
async def add_post(request: CreatePostRequest = Body(...)):
    post = create_post(request)
    return success_response(post)


@router.get("/posts/{post_id}", response_model=ApiResponse[CommunityPost])
async def get_post(post_id: int = Path(..., ge=1, description="帖子ID")):
    post = get_post_detail(post_id)
    if post:
        return success_response(post)
    return error_response("帖子不存在", 404)


@router.post("/posts/{post_id}/comments", response_model=ApiResponse[CommentItem])
async def add_comment(
    post_id: int = Path(..., ge=1, description="帖子ID"),
    request: CreateCommentRequest = Body(...),
):
    comment = create_comment(post_id, request)
    return success_response(comment)


@router.get("/posts/{post_id}/comments", response_model=ApiResponse[CommentListResponse])
async def get_post_comments(
    post_id: int = Path(..., ge=1, description="帖子ID"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
):
    result = get_comments(post_id, page, page_size)
    return success_response(result)


@router.post("/posts/{post_id}/like", response_model=ApiResponse[LikeResponse])
async def like_post(post_id: int = Path(..., ge=1, description="帖子ID")):
    result = toggle_post_like(post_id)
    return success_response(result)


@router.get("/hot-search", response_model=ApiResponse[List[HotSearchItem]])
async def hot_search(limit: int = Query(10, ge=1, le=20, description="数量限制")):
    result = get_hot_search(limit)
    return success_response(result)


@router.post("/ai-helper", response_model=ApiResponse[AIHelperResponse])
async def ai_helper(question: str = Body(..., embed=True, description="问题")):
    result = ai_news_helper(question)
    return success_response(result)