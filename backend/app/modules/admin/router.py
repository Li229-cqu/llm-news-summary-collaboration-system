from fastapi import APIRouter, Depends, Query

from app.common.auth import require_admin, require_editor_or_admin
from app.common.response import ApiResponse, success_response
from app.modules.admin.schema import AdminDashboard
from app.modules.admin.service import (
    get_dashboard,
    get_pending_posts,
    get_system_config,
    get_users,
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
