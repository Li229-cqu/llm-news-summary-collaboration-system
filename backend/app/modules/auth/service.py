from typing import Any, Optional

from app.common.exceptions import AppException
from app.mock.users import MOCK_USERS
from app.modules.auth.schema import LoginRequest, LoginResponse, UserInfo


def _to_user_info(user: dict[str, Any]) -> UserInfo:
    """将 Mock 用户数据转换为不含密码和 Token 的用户信息。"""
    return UserInfo(
        id=user["id"],
        username=user["username"],
        nickname=user["nickname"],
        role=user["role"],
        avatar=user["avatar"],
        status=user["status"],
    )


def login_mock_user(request: LoginRequest) -> LoginResponse:
    """验证固定 Mock 账号并返回固定 Token。"""
    for user in MOCK_USERS:
        if user["username"] == request.username and user["password"] == request.password:
            return LoginResponse(token=user["token"], user=_to_user_info(user))

    raise AppException(code=401, message="账号或密码错误")


def logout_mock_user() -> None:
    """Mock 阶段不保存登录状态，退出接口仅保留统一入口。"""
    return None


def get_mock_user_by_token(token: str) -> Optional[UserInfo]:
    """按固定 Mock Token 查询用户；后续可替换为 JWT 解析和用户表查询。"""
    for user in MOCK_USERS:
        if user["token"] == token:
            return _to_user_info(user)
    return None


def get_current_mock_user(authorization: Optional[str]) -> UserInfo:
    """根据 Bearer Token 查询固定 Mock 用户。"""
    if not authorization or not authorization.startswith("Bearer "):
        raise AppException(code=401, message="未登录或登录状态已失效")

    token = authorization.removeprefix("Bearer ").strip()
    user = get_mock_user_by_token(token)
    if user is not None:
        return user

    raise AppException(code=401, message="未登录或登录状态已失效")
