from __future__ import annotations

import logging
from typing import Any, Optional

from app.common.exceptions import AppException
from app.db.database import execute_one, execute_update
from app.modules.user.schema import UserInfo, UpdateProfileRequest

logger = logging.getLogger(__name__)


def get_test_data():
    from app.modules.user.schema import UserTestData
    return UserTestData(module="user", description="用户模块基础接口占位")


def _to_user_info(user: dict[str, Any]) -> UserInfo:
    return UserInfo(
        id=int(user["id"]),
        username=str(user["username"]),
        nickname=str(user.get("nickname") or ""),
        role=str(user["role"]),
        avatar=str(user.get("avatar") or ""),
        email=str(user.get("email") or ""),
        phone=str(user.get("phone") or ""),
        status=int(user.get("status", 1)),
    )


def get_user_by_id(user_id: int) -> Optional[dict[str, Any]]:
    return execute_one(
        """
        SELECT id, username, password, nickname, avatar, role, email, phone, status
        FROM user
        WHERE id = %s
        LIMIT 1
        """,
        (user_id,),
    )


def get_profile(current_user: Any) -> UserInfo:
    user_id = int(getattr(current_user, "id", 0) or 0)
    if user_id <= 0:
        raise AppException(code=401, message="未登录或登录状态已失效")

    db_user = get_user_by_id(user_id)
    if db_user is None:
        raise AppException(code=404, message="用户不存在")

    return _to_user_info(db_user)


def update_profile(current_user: Any, request: UpdateProfileRequest) -> UserInfo:
    user_id = int(getattr(current_user, "id", 0) or 0)
    if user_id <= 0:
        raise AppException(code=401, message="未登录或登录状态已失效")

    db_user = get_user_by_id(user_id)
    if db_user is None:
        raise AppException(code=404, message="用户不存在")

    update_fields = []
    params = []

    if request.nickname is not None:
        nickname = request.nickname.strip()
        if not nickname:
            raise AppException(code=400, message="昵称不能为空")
        update_fields.append("nickname = %s")
        params.append(nickname)

    if request.avatar is not None:
        avatar = request.avatar.strip() if request.avatar else ''
        if avatar and not avatar.startswith('data:image/') and ';base64,' not in avatar and len(avatar) <= 255:
            update_fields.append("avatar = %s")
            params.append(avatar)

    if request.email is not None:
        update_fields.append("email = %s")
        params.append(request.email)

    if request.phone is not None:
        update_fields.append("phone = %s")
        params.append(request.phone)

    if not update_fields:
        return _to_user_info(db_user)

    params.append(user_id)
    sql = f"UPDATE user SET {', '.join(update_fields)} WHERE id = %s"
    execute_update(sql, params)

    updated_user = get_user_by_id(user_id)
    if updated_user is None:
        raise AppException(code=500, message="更新失败，请重试")

    return _to_user_info(updated_user)


def change_password(current_user: Any, old_password: str, new_password: str, confirm_password: str) -> None:
    user_id = int(getattr(current_user, "id", 0) or 0)
    if user_id <= 0:
        raise AppException(code=401, message="未登录或登录状态已失效")

    if not new_password or not new_password.strip():
        raise AppException(code=400, message="新密码不能为空")

    if len(new_password) < 6:
        raise AppException(code=400, message="新密码长度不能少于6位")

    if new_password != confirm_password:
        raise AppException(code=400, message="两次输入的新密码不一致")

    db_user = get_user_by_id(user_id)
    if db_user is None:
        raise AppException(code=404, message="用户不存在")

    if str(db_user["password"]) != old_password:
        raise AppException(code=400, message="原密码错误")

    if old_password == new_password:
        raise AppException(code=400, message="新密码不能与原密码相同")

    execute_update(
        "UPDATE user SET password = %s WHERE id = %s",
        (new_password, user_id),
    )


ALLOWED_AVATAR_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
ALLOWED_AVATAR_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
MAX_AVATAR_SIZE = 2 * 1024 * 1024  # 2MB


def upload_avatar(current_user: Any, file: Any) -> dict:
    """上传用户头像，保存到 uploads/avatar/ 并更新 user.avatar。"""
    import os
    import uuid

    user_id = int(getattr(current_user, "id", 0) or 0)
    if user_id <= 0:
        raise AppException(code=401, message="未登录或登录状态已失效")

    # Validate file type
    content_type = getattr(file, "content_type", "") or ""
    if content_type not in ALLOWED_AVATAR_TYPES:
        raise AppException(code=400, message="仅支持 jpg/png/gif/webp 格式图片")

    # Validate extension
    filename = getattr(file, "filename", "") or ""
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_AVATAR_EXTENSIONS:
        raise AppException(code=400, message="仅支持 jpg/png/gif/webp 格式图片")

    # Read and validate size
    file.file.seek(0, os.SEEK_END)
    file_size = file.file.tell()
    file.file.seek(0)
    if file_size > MAX_AVATAR_SIZE:
        raise AppException(code=400, message="头像图片不能超过 2MB")

    # Generate safe filename
    safe_name = f"user_{user_id}_{uuid.uuid4().hex[:8]}{ext}"

    # Determine upload directory (relative to backend/)
    uploads_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "uploads", "avatar")
    os.makedirs(uploads_dir, exist_ok=True)

    # Write file
    file_path = os.path.join(uploads_dir, safe_name)
    contents = file.file.read()
    if isinstance(contents, str):
        contents = contents.encode("utf-8")
    with open(file_path, "wb") as f:
        f.write(contents)

    avatar_url = f"/uploads/avatar/{safe_name}"

    # Update user.avatar in database
    execute_update(
        "UPDATE user SET avatar = %s WHERE id = %s",
        (avatar_url, user_id),
    )

    logger.info("User %d avatar uploaded: %s", user_id, avatar_url)
    return {"avatar": avatar_url, "avatar_url": avatar_url}
