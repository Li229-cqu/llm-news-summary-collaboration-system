from typing import Optional

from fastapi import APIRouter, Body, Depends, Path, Query

from app.common.auth import require_admin, require_editor_or_admin
from app.common.response import ApiResponse, success_response
from app.modules.admin.schema import (
    AdminDashboard,
    AuditResponse,
    HotTopicCreate,
    HotTopicItem,
    HotTopicUpdate,
    RejectRequest,
    SimpleHotTopicCreate,
    SimpleHotTopicItem,
    SimpleHotTopicUpdate,
)
from app.modules.admin.service import (
    approve_post,
    create_hot_topic,
    create_simple_hot_topic,
    delete_hot_topic,
    delete_simple_hot_topic,
    get_dashboard,
    get_hot_topics,
    get_pending_posts,
    get_simple_hot_topics,
    get_system_config,
    get_users,
    reject_post,
    update_hot_topic,
    update_simple_hot_topic,
)
from app.modules.auth.schema import UserInfo

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/ping", response_model=ApiResponse[str])
async def ping_admin(_: UserInfo = Depends(require_editor_or_admin)) -> ApiResponse[str]:
    return success_response("admin module ok")


@router.get("/dashboard", response_model=ApiResponse[AdminDashboard])
async def dashboard(
    _: UserInfo = Depends(require_editor_or_admin),
) -> ApiResponse[AdminDashboard]:
    """获取后台概览数据。"""
    data = get_dashboard()
    return success_response(data)


@router.get("/pending-posts", response_model=ApiResponse[dict])
async def pending_posts(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    _: UserInfo = Depends(require_editor_or_admin),
) -> ApiResponse[dict]:
    """获取待审核帖子列表。"""
    data = get_pending_posts(page=page, page_size=page_size)
    return success_response(data)


# ==================== 帖子审核 ====================

@router.post("/posts/{post_id}/approve", response_model=ApiResponse[AuditResponse])
async def post_approve(
    post_id: int = Path(..., ge=1, description="帖子ID"),
    _: UserInfo = Depends(require_editor_or_admin),
) -> ApiResponse[AuditResponse]:
    """审核通过帖子。"""
    result = approve_post(post_id)
    return success_response(result)


@router.post("/posts/{post_id}/reject", response_model=ApiResponse[AuditResponse])
async def post_reject(
    post_id: int = Path(..., ge=1, description="帖子ID"),
    body: RejectRequest = Body(default=RejectRequest()),
    _: UserInfo = Depends(require_editor_or_admin),
) -> ApiResponse[AuditResponse]:
    """驳回帖子（可选驳回理由）。"""
    result = reject_post(post_id, reason=body.reason)
    return success_response(result)


# ==================== 新闻热搜榜管理（独立榜单） ====================

@router.get("/news-hot-ranking", response_model=ApiResponse[dict])
async def admin_news_hot_ranking(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    _: UserInfo = Depends(require_editor_or_admin),
) -> ApiResponse[dict]:
    """获取新闻热搜榜管理列表。"""
    data = get_hot_topics(target_type='news', page=page, page_size=page_size)
    return success_response(data)


@router.post("/news-hot-ranking", response_model=ApiResponse[dict])
async def admin_create_news_hot(
    data: HotTopicCreate = Body(...),
    _: UserInfo = Depends(require_editor_or_admin),
) -> ApiResponse[dict]:
    """添加新闻热搜。"""
    data.target_type = 'news'
    result = create_hot_topic(data)
    return success_response(result)


@router.put("/news-hot-ranking/{topic_id}", response_model=ApiResponse[dict])
async def admin_update_news_hot(
    topic_id: int = Path(..., ge=1),
    data: HotTopicUpdate = Body(...),
    _: UserInfo = Depends(require_editor_or_admin),
) -> ApiResponse[dict]:
    """编辑新闻热搜。"""
    result = update_hot_topic(topic_id, data)
    return success_response(result)


@router.delete("/news-hot-ranking/{topic_id}", response_model=ApiResponse[dict])
async def admin_delete_news_hot(
    topic_id: int = Path(..., ge=1),
    _: UserInfo = Depends(require_admin),
) -> ApiResponse[dict]:
    """删除新闻热搜（仅管理员）。"""
    result = delete_hot_topic(topic_id)
    return success_response(result)


# ==================== 社区热搜管理（独立榜单） ====================

@router.get("/community-hot-topics", response_model=ApiResponse[dict])
async def admin_community_hot_topics(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    _: UserInfo = Depends(require_editor_or_admin),
) -> ApiResponse[dict]:
    """获取社区热搜管理列表。"""
    data = get_hot_topics(target_type='community', page=page, page_size=page_size)
    return success_response(data)


@router.post("/community-hot-topics", response_model=ApiResponse[dict])
async def admin_create_community_hot(
    data: HotTopicCreate = Body(...),
    _: UserInfo = Depends(require_editor_or_admin),
) -> ApiResponse[dict]:
    """添加社区热搜。"""
    data.target_type = 'community'
    result = create_hot_topic(data)
    return success_response(result)


@router.put("/community-hot-topics/{topic_id}", response_model=ApiResponse[dict])
async def admin_update_community_hot(
    topic_id: int = Path(..., ge=1),
    data: HotTopicUpdate = Body(...),
    _: UserInfo = Depends(require_editor_or_admin),
) -> ApiResponse[dict]:
    """编辑社区热搜。"""
    result = update_hot_topic(topic_id, data)
    return success_response(result)


@router.delete("/community-hot-topics/{topic_id}", response_model=ApiResponse[dict])
async def admin_delete_community_hot(
    topic_id: int = Path(..., ge=1),
    _: UserInfo = Depends(require_admin),
) -> ApiResponse[dict]:
    """删除社区热搜（仅管理员）。"""
    result = delete_hot_topic(topic_id)
    return success_response(result)


# ==================== 简化热搜管理（E2） ====================

@router.get("/hot-topics", response_model=ApiResponse[dict])
async def list_hot_topics(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    _: UserInfo = Depends(require_editor_or_admin),
) -> ApiResponse[dict]:
    """获取热搜话题管理列表（简化版）。"""
    data = get_simple_hot_topics(page=page, page_size=page_size)
    return success_response(data)


@router.post("/hot-topics", response_model=ApiResponse[dict])
async def create_hot_topic_api(
    data: SimpleHotTopicCreate = Body(...),
    _: UserInfo = Depends(require_editor_or_admin),
) -> ApiResponse[dict]:
    """添加热搜话题。"""
    result = create_simple_hot_topic(data)
    return success_response(result)


@router.put("/hot-topics/{topic_id}", response_model=ApiResponse[dict])
async def update_hot_topic_api(
    topic_id: int = Path(..., ge=1),
    data: SimpleHotTopicUpdate = Body(...),
    _: UserInfo = Depends(require_editor_or_admin),
) -> ApiResponse[dict]:
    """编辑热搜话题。"""
    result = update_simple_hot_topic(topic_id, data)
    return success_response(result)


@router.delete("/hot-topics/{topic_id}", response_model=ApiResponse[dict])
async def delete_hot_topic_api(
    topic_id: int = Path(..., ge=1),
    _: UserInfo = Depends(require_admin),
) -> ApiResponse[dict]:
    """删除热搜话题（仅管理员）。"""
    result = delete_simple_hot_topic(topic_id)
    return success_response(result)


# ==================== 用户管理 ====================

@router.get("/users", response_model=ApiResponse[dict])
async def users(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    _: UserInfo = Depends(require_admin),
) -> ApiResponse[dict]:
    """获取用户管理列表（仅管理员）。"""
    data = get_users(page=page, page_size=page_size)
    return success_response(data)


@router.get("/system-config", response_model=ApiResponse[dict])
async def system_config(
    _: UserInfo = Depends(require_admin),
) -> ApiResponse[dict]:
    """获取系统配置（仅管理员）。"""
    data = get_system_config()
    return success_response(data)
