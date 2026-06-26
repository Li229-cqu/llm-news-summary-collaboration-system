from pydantic import BaseModel


class AuthTestData(BaseModel):
    module: str
    description: str


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    password: str
    confirm_password: str
    nickname: str = ""
    email: str = ""
    phone: str = ""


class ResetPasswordRequest(BaseModel):
    username: str
    email: str = ""
    phone: str = ""
    new_password: str
    confirm_password: str


class UserInfo(BaseModel):
    id: int
    username: str
    nickname: str
    role: str
    avatar: str = ""
    email: str = ""
    phone: str = ""
    status: int = 1


class LoginResponse(BaseModel):
    token: str
    user: UserInfo


class RegisterResponse(BaseModel):
    id: int
    username: str
    nickname: str
