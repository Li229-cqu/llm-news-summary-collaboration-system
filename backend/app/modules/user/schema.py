from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class UserTestData(BaseModel):
    module: str
    description: str


class UserInfo(BaseModel):
    id: int
    username: str
    nickname: str
    role: str
    avatar: str = ""
    email: str = ""
    phone: str = ""
    status: int = 1


class UpdateProfileRequest(BaseModel):
    nickname: Optional[str] = None
    avatar: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str
    confirm_password: str
