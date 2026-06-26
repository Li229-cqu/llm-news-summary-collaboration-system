from __future__ import annotations
from typing import Callable, Optional, Set

from fastapi import Depends, Header

from app.common.exceptions import AppException
from app.modules.auth.schema import UserInfo
from app.modules.auth.service import get_mock_user_by_token


async def get_current_user(
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
) -> UserInfo:
    """从 Bearer Mock Token 解析当前用户；后续可替换为 JWT 校验。"""
    if not authorization or not authorization.startswith("Bearer "):
        raise AppException(code=401, message="未登录或登录状态已失效")

    token = authorization.removeprefix("Bearer ").strip()
    user = get_mock_user_by_token(token)
    if user is None:
        raise AppException(code=401, message="未登录或登录状态已失效")

    return user


async def require_login(current_user: UserInfo = Depends(get_current_user)) -> UserInfo:
    """要求当前请求具备有效登录状态。"""
    return current_user


def _ensure_role(current_user: UserInfo, allowed_roles: set[str]) -> UserInfo:
    if current_user.role not in allowed_roles:
        raise AppException(code=403, message="当前账号无权限访问该资源")
    return current_user


def require_role(*allowed_roles: str) -> Callable[..., UserInfo]:
    """创建指定角色校验依赖。"""
    allowed_role_set = set(allowed_roles)

    async def role_dependency(current_user: UserInfo = Depends(get_current_user)) -> UserInfo:
        return _ensure_role(current_user, allowed_role_set)

    return role_dependency


async def require_admin(current_user: UserInfo = Depends(get_current_user)) -> UserInfo:
    """只允许管理员访问。"""
    return _ensure_role(current_user, {"admin"})


async def require_editor_or_admin(current_user: UserInfo = Depends(get_current_user)) -> UserInfo:
    """允许审核/编辑和管理员访问。"""
    return _ensure_role(current_user, {"editor", "admin"})
