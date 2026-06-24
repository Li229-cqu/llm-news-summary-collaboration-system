from typing import List, Optional

from pydantic import BaseModel


class AdminTestData(BaseModel):
    module: str
    description: str


class AdminDashboard(BaseModel):
    user_count: int
    news_count: int
    post_count: int
    pending_count: int


class UserItem(BaseModel):
    id: int
    username: str
    nickname: str
    role: str
    status: int
    create_time: Optional[str] = None


class PaginationResponse(BaseModel):
    list: List[dict]
    total: int
    page: int
    page_size: int
