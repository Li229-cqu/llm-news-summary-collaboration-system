from pydantic import BaseModel


class UserTestData(BaseModel):
    module: str
    description: str


class UserInfo(BaseModel):
    id: int
    username: str
    nickname: str
    role: str
