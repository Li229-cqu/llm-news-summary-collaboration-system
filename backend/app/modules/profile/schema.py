from __future__ import annotations
from typing import List, Optional, Union

from pydantic import BaseModel


class ProfileTestData(BaseModel):
    module: str
    description: str


class ProfileOverview(BaseModel):
    user_id: int
    browse_count: int
    favorite_count: int
    comment_count: int
    ai_generate_count: int


class BrowseHistoryItem(BaseModel):
    news_id: int
    title: str
    category_name: str
    browse_time: str


class FavoriteItem(BaseModel):
    news_id: int
    title: str
    summary: str
    category_name: str
    source: str
    publish_time: str


class CommentRecordItem(BaseModel):
    comment_id: int
    news_id: int
    news_title: str
    category_name: str
    content: str
    like_count: int
    status: int
    create_time: str


class AIRecordItem(BaseModel):
    id: int
    source: str
    source_news_id: Optional[int | str] = None
    source_title: str
    input_text: str
    candidate_titles: List[str]
    summary_short: str
    summary_long: Optional[str] = None
    risk_level: str = "low"
    create_time: Optional[str] = None


class SubscriptionCategory(BaseModel):
    id: int
    name: str
    code: str
    subscribed: bool = False


class SubscriptionResponse(BaseModel):
    subscribed_category_ids: List[int]
    categories: List[SubscriptionCategory]


class SubscriptionUpdateRequest(BaseModel):
    category_ids: List[int]


class PaginationResponse(BaseModel):
    list: List[dict]
    total: int
    page: int
    page_size: int
