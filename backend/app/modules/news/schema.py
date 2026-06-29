"""新闻模块请求与响应模型。

当前模型兼容 mock 数据与数据库返回，后续只需切换 service 层数据源。
"""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class NewsCategory(BaseModel):
    """新闻分类。"""

    id: int
    name: str
    code: str
    sort: int
    status: int


class NewsItem(BaseModel):
    """新闻列表项。"""

    id: int
    title: str
    summary: str
    cover_image: str = ""
    category_id: int
    category_name: str = "未分类"
    topic_id: Optional[int] = None
    source: str
    editor: str = ""
    publish_time: str
    view_count: int
    like_count: int
    comment_count: int
    favorite_count: int
    status: int
    tags: list[str] = Field(default_factory=list)
    source_url: str = ""
    recommend_source: Optional[str] = None


class NewsDetail(NewsItem):
    """新闻详情。"""

    content: str
    related_news: list[NewsItem] = Field(default_factory=list)
    recommended_news: list[NewsItem] = Field(default_factory=list)
    is_liked: bool = False
    is_favorited: bool = False
    timeline_news_count: int = 0


class NewsListQuery(BaseModel):
    """新闻列表查询参数。"""

    category: Optional[str] = None
    category_id: Optional[int] = None
    keyword: Optional[str] = None
    page: int = 1
    page_size: int = 10


class NewsListResponse(BaseModel):
    """新闻分页响应。"""

    list: list[NewsItem] = Field(default_factory=list)
    total: int
    page: int
    page_size: int


class HotNewsItem(BaseModel):
    """新闻热榜项。"""

    id: int
    title: str
    category_name: str
    source: str
    view_count: int
    comment_count: int
    like_count: int = 0
    favorite_count: int = 0
    cover_image: str = ""
    publish_time: str = ""
    heat_score: int = 0
    rank: int


class BrowseResult(BaseModel):
    """浏览记录结果。"""

    news_id: int
    recorded: bool
