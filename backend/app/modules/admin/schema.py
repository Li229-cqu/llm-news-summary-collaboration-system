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


# ---------- 帖子审核 ----------

class RejectRequest(BaseModel):
    reason: Optional[str] = None


class AuditResponse(BaseModel):
    id: int
    status: int
    message: str
    reason: Optional[str] = None


# ---------- 热搜管理 ----------

class HotTopicCreate(BaseModel):
    title: str
    heat_score: int = 0
    target_type: str = "news"
    target_id: Optional[int] = None
    tag: Optional[str] = None
    rank_no: int = 0
    status: int = 1


class HotTopicUpdate(BaseModel):
    title: Optional[str] = None
    heat_score: Optional[int] = None
    target_type: Optional[str] = None
    target_id: Optional[int] = None
    tag: Optional[str] = None
    rank_no: Optional[int] = None
    status: Optional[int] = None


class HotTopicItem(BaseModel):
    id: int
    title: str
    heat_score: int
    target_type: Optional[str] = None
    target_id: Optional[int] = None
    tag: Optional[str] = None
    rank_no: int
    status: int
    create_time: Optional[str] = None
    update_time: Optional[str] = None


# ---------- 简化热搜管理（E2） ----------

class SimpleHotTopicCreate(BaseModel):
    keyword: str  # 话题词，映射到 hot_topic.title
    heat: int = 0  # 热度值，映射到 hot_topic.heat_score


class SimpleHotTopicUpdate(BaseModel):
    keyword: Optional[str] = None
    heat: Optional[int] = None
    is_pinned: Optional[bool] = None
    status: Optional[int] = None


class SimpleHotTopicItem(BaseModel):
    id: int
    keyword: str
    heat: int
    is_pinned: bool
    status: int
    create_time: Optional[str] = None
    update_time: Optional[str] = None
