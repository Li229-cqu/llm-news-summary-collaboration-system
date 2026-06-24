from typing import List, Optional

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


class AIRecordItem(BaseModel):
    id: int
    input_text: str
    candidate_titles: List[str]
    summary_short: str
    summary_long: Optional[str] = None
    create_time: Optional[str] = None


class PaginationResponse(BaseModel):
    list: List[dict]
    total: int
    page: int
    page_size: int
