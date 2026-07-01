from __future__ import annotations

from typing import Any, Dict, Optional, Union

from app.common.exceptions import AppException
from app.db.database import execute_insert, execute_one, execute_update
from app.mock.users import MOCK_USERS
from app.modules.auth.schema import LoginRequest, LoginResponse, RegisterRequest, RegisterResponse, ResetPasswordRequest, UserInfo

def _to_user_info(user: dict[str, Any]) -> UserInfo:
    """Convert a db/mock user row into API user info."""
    return UserInfo(
        id=int(user["id"]),
        username=str(user["username"]),
        nickname=str(user["nickname"]),
        role=str(user["role"]),
        avatar=str(user.get("avatar") or ""),
        email=str(user.get("email") or ""),
        phone=str(user.get("phone") or ""),
        status=int(user.get("status", 1)),
    )


def _get_token_for_user(user_id: int, role: str) -> str:
    """Generate a mock token that uniquely identifies the user by id and role."""
    return f"mock-token-{role}-{user_id}"


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
            token=_get_token_for_user(int(db_user["id"]), str(db_user["role"])),
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
    """Resolve a user by mock token, preferring the database user table.

    Token format: mock-token-{role}-{user_id}
    Falls back to legacy TOKEN_USERNAME_MAP for backward compatibility.
    """
    # New format: mock-token-{role}-{user_id}
    parts = token.rsplit("-", 1)
    if len(parts) == 2 and parts[1].isdigit():
        user_id = int(parts[1])
        try:
            db_user = execute_one(
                "SELECT id, username, password, nickname, avatar, role, status, email, phone FROM user WHERE id = %s AND status = 1 LIMIT 1",
                (user_id,),
            )
        except Exception:
            db_user = None
        if db_user is not None:
            return _to_user_info(db_user)

    # Legacy fallback: old role-based tokens
    legacy_map = {
        "mock-token-user": "user",
        "mock-token-editor": "editor",
        "mock-token-admin": "admin",
    }
    username = legacy_map.get(token)
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


def register_user(request: RegisterRequest) -> RegisterResponse:
    """Register a new user, prefer database storage."""
    if not request.username or len(request.username) < 3:
        raise AppException(code=400, message="用户名长度不能少于3位")
    if not request.password or len(request.password) < 6:
        raise AppException(code=400, message="密码长度不能少于6位")
    if request.password != request.confirm_password:
        raise AppException(code=400, message="两次输入的密码不一致")

    nickname = request.nickname or request.username

    try:
        existing = _get_db_user_by_username(request.username)
        if existing is not None:
            raise AppException(code=400, message="用户名已被注册")

        user_id = execute_insert(
            """
            INSERT INTO user (username, password, nickname, role, avatar, email, phone, status)
            VALUES (%s, %s, %s, 'user', '', %s, %s, 1)
            """,
            (request.username, request.password, nickname, request.email or None, request.phone or None),
        )
        return RegisterResponse(
            id=int(user_id),
            username=request.username,
            nickname=nickname,
        )
    except AppException:
        raise
    except Exception as e:
        raise AppException(code=500, message=f"注册失败：{str(e)}")


def reset_password(request: ResetPasswordRequest) -> dict[str, str]:
    """Reset password by username and email/phone."""
    if not request.username:
        raise AppException(code=400, message="用户名不能为空")
    if not request.new_password or len(request.new_password) < 6:
        raise AppException(code=400, message="新密码长度不能少于6位")
    if request.new_password != request.confirm_password:
        raise AppException(code=400, message="两次输入的新密码不一致")

    try:
        db_user = _get_db_user_by_username(request.username)
        if db_user is None:
            raise AppException(code=404, message="用户不存在")

        if request.email and str(db_user.get("email") or "") != request.email:
            raise AppException(code=400, message="邮箱与注册信息不匹配")
        if request.phone and str(db_user.get("phone") or "") != request.phone:
            raise AppException(code=400, message="手机号与注册信息不匹配")

        execute_update(
            """
            UPDATE user SET password = %s WHERE id = %s
            """,
            (request.new_password, db_user["id"]),
        )
        return {"message": "密码重置成功"}
    except AppException:
        raise
    except Exception as e:
        raise AppException(code=500, message=f"重置密码失败：{str(e)}")

