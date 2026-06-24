"""新闻模块的请求与响应数据模型。

当前模型用于基于 Mock 数据的接口开发，后续接入数据库时可保持接口字段不变。
"""

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
    cover_image: str
    category_id: int
    category_name: str
    source: str
    author: str
    publish_time: str
    view_count: int
    like_count: int
    comment_count: int
    favorite_count: int
    status: int
    tags: List[str]


class NewsDetail(NewsItem):
    """新闻详情，包含关联与推荐新闻以及当前用户互动状态。"""

    content: str
    related_news: List[NewsItem] = Field(default_factory=list)
    recommended_news: List[NewsItem] = Field(default_factory=list)
    is_liked: bool = False
    is_favorited: bool = False


class NewsListQuery(BaseModel):
    """新闻列表查询参数。"""

    category: Optional[str] = None
    keyword: Optional[str] = None
    page: int = 1
    page_size: int = 10


class NewsListResponse(BaseModel):
    """新闻列表分页响应数据。"""

    list: List[NewsItem] = Field(default_factory=list)
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
    rank: int


class BrowseResult(BaseModel):
    """浏览记录结果。"""

    news_id: int
    recorded: bool
