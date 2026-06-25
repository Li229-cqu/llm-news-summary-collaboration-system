from __future__ import annotations

from typing import Any, Optional

from app.common.exceptions import AppException
from app.db.database import execute_one
from app.mock.users import MOCK_USERS
from app.modules.auth.schema import LoginRequest, LoginResponse, UserInfo

TOKEN_USERNAME_MAP = {
    "mock-token-user": "user",
    "mock-token-editor": "editor",
    "mock-token-admin": "admin",
}


def _to_user_info(user: dict[str, Any]) -> UserInfo:
    """Convert a db/mock user row into API user info."""
    return UserInfo(
        id=int(user["id"]),
        username=str(user["username"]),
        nickname=str(user["nickname"]),
        role=str(user["role"]),
        avatar=str(user.get("avatar") or ""),
        status=int(user.get("status", 1)),
    )


def _get_token_for_role(role: str) -> str:
    return {
        "user": "mock-token-user",
        "editor": "mock-token-editor",
        "admin": "mock-token-admin",
    }.get(role, "mock-token-user")


def _get_db_user_by_username(username: str) -> dict[str, Any] | None:
    return execute_one(
        """
        SELECT id, username, password, nickname, avatar, role, status
        FROM user
        WHERE username = %s AND status = 1
        LIMIT 1
        """,
        (username,),
    )


def _get_mock_user_by_username(username: str, password: str | None = None) -> dict[str, Any] | None:
    for user in MOCK_USERS:
        if user["username"] != username:
            continue
        if password is not None and user["password"] != password:
            continue
        return user
    return None


def _get_mock_user_by_token(token: str) -> dict[str, Any] | None:
    for user in MOCK_USERS:
        if user["token"] == token:
            return user
    return None


def login_mock_user(request: LoginRequest) -> LoginResponse:
    """Prefer the database user table and fallback to mock users when needed."""
    try:
        db_user = _get_db_user_by_username(request.username)
    except Exception:
        db_user = None

    if db_user is not None:
        if db_user["password"] != request.password:
            raise AppException(code=401, message="账号或密码错误")
        return LoginResponse(
            token=_get_token_for_role(str(db_user["role"])),
            user=_to_user_info(db_user),
        )

    mock_user = _get_mock_user_by_username(request.username, request.password)
    if mock_user is not None:
        return LoginResponse(token=mock_user["token"], user=_to_user_info(mock_user))

    raise AppException(code=401, message="账号或密码错误")


def logout_mock_user() -> None:
    """Mock logout keeps the API shape only."""
    return None


def get_mock_user_by_token(token: str) -> Optional[UserInfo]:
    """Resolve a user by mock token, preferring the database user table."""
    username = TOKEN_USERNAME_MAP.get(token)
    if username is not None:
        try:
            db_user = _get_db_user_by_username(username)
        except Exception:
            db_user = None
        if db_user is not None:
            return _to_user_info(db_user)

    mock_user = _get_mock_user_by_token(token)
    if mock_user is not None:
        return _to_user_info(mock_user)
    return None


def get_current_mock_user(authorization: Optional[str]) -> UserInfo:
    """Resolve the current user from a Bearer token."""
    if not authorization or not authorization.startswith("Bearer "):
        raise AppException(code=401, message="未登录或登录状态已失效")

    token = authorization.removeprefix("Bearer ").strip()
    user = get_mock_user_by_token(token)
    if user is not None:
        return user

    raise AppException(code=401, message="未登录或登录状态已失效")

