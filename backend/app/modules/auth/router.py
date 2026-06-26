from typing import Optional

from fastapi import APIRouter, Depends, Header

from app.common.auth import require_admin, require_editor_or_admin, require_login
from app.common.response import ApiResponse, success_response
from app.modules.auth.schema import LoginRequest, LoginResponse, RegisterRequest, RegisterResponse, ResetPasswordRequest, UserInfo
from app.modules.auth.service import get_current_mock_user, login_mock_user, logout_mock_user, register_user, reset_password

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.get("/ping", response_model=ApiResponse[str])
async def ping_auth() -> ApiResponse[str]:
    return success_response("auth module ok")


@router.post("/login", response_model=ApiResponse[LoginResponse])
async def login(request: LoginRequest) -> ApiResponse[LoginResponse]:
    return success_response(login_mock_user(request))


@router.post("/register", response_model=ApiResponse[RegisterResponse])
async def register(request: RegisterRequest) -> ApiResponse[RegisterResponse]:
    return success_response(register_user(request))


@router.post("/reset-password")
async def reset_password_endpoint(request: ResetPasswordRequest) -> ApiResponse[dict]:
    result = reset_password(request)
    return success_response(result, message=result.get("message", "密码重置成功"))


@router.post("/logout")
async def logout():
    logout_mock_user()
    return success_response(message="退出登录成功")


@router.get("/me", response_model=ApiResponse[UserInfo])
async def get_current_user(authorization: Optional[str] = Header(default=None, alias="Authorization")) -> ApiResponse[UserInfo]:
    return success_response(get_current_mock_user(authorization))


@router.get("/check-login", response_model=ApiResponse[UserInfo])
async def check_login(current_user: UserInfo = Depends(require_login)) -> ApiResponse[UserInfo]:
    return success_response(current_user)


@router.get("/check-editor", response_model=ApiResponse[UserInfo])
async def check_editor(current_user: UserInfo = Depends(require_editor_or_admin)) -> ApiResponse[UserInfo]:
    return success_response(current_user)


@router.get("/check-admin", response_model=ApiResponse[UserInfo])
async def check_admin(current_user: UserInfo = Depends(require_admin)) -> ApiResponse[UserInfo]:
    return success_response(current_user)
