from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Header

from app.common.auth import require_login
from app.common.response import ApiResponse, success_response
from app.modules.user.schema import (
    ChangePasswordRequest,
    UpdateProfileRequest,
    UserInfo,
)
from app.modules.user.service import change_password, get_profile, update_profile

router = APIRouter(prefix="/api/user", tags=["user"])


@router.get("/ping", response_model=ApiResponse[str])
async def ping_user() -> ApiResponse[str]:
    return success_response("user module ok")


@router.get("/profile", response_model=ApiResponse[UserInfo])
async def get_user_profile(current_user: UserInfo = Depends(require_login)) -> ApiResponse[UserInfo]:
    return success_response(get_profile(current_user))


@router.put("/profile", response_model=ApiResponse[UserInfo])
async def update_user_profile(
    request: UpdateProfileRequest,
    current_user: UserInfo = Depends(require_login),
) -> ApiResponse[UserInfo]:
    return success_response(update_profile(current_user, request))


@router.post("/change-password", response_model=ApiResponse[None])
async def change_user_password(
    request: ChangePasswordRequest,
    current_user: UserInfo = Depends(require_login),
) -> ApiResponse[None]:
    change_password(
        current_user,
        request.old_password,
        request.new_password,
        request.confirm_password,
    )
    return success_response(message="密码修改成功")
