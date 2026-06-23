from pydantic import BaseModel


class AuthTestData(BaseModel):
    module: str
    description: str


class LoginRequest(BaseModel):
    username: str
    password: str


class UserInfo(BaseModel):
    id: int
    username: str
    nickname: str
    role: str
    avatar: str = ""
    status: int = 1


class LoginResponse(BaseModel):
    token: str
    user: UserInfo
