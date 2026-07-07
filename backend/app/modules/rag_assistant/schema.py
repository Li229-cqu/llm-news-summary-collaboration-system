"""RAG Assistant 请求/响应 Schema"""

from __future__ import annotations
from typing import List, Optional, Literal
from pydantic import BaseModel


# ── 请求 ────────────────────────────────────────────

class SearchContext(BaseModel):
    """用户当前浏览页面的上下文信息"""
    page: str = "other"  # home | news-detail | community | timeline | ai-generate | profile | other
    newsId: Optional[int] = None
    categoryId: Optional[int] = None
    topicId: Optional[int] = None
    searchKeyword: Optional[str] = None
    postId: Optional[int] = None


class SearchRequest(BaseModel):
    question: str
    context: SearchContext = SearchContext()


# ── 响应 ────────────────────────────────────────────

SearchResultType = Literal["news", "community_post", "news_comment", "post_comment", "news_topic"]
RelevanceType = Literal["current", "topic_match", "keyword_match"]


class SearchResultItem(BaseModel):
    type: SearchResultType
    id: int
    title: Optional[str] = None
    content: str
    summary: Optional[str] = None
    source: Optional[str] = None       # 来源名称 / 作者
    publishTime: Optional[str] = None
    relevance: RelevanceType
    # 关联字段，用于前端跳转
    newsId: Optional[int] = None       # 评论所属新闻 ID
    postId: Optional[int] = None       # 评论所属帖子 ID
    topicId: Optional[int] = None      # 新闻/帖子所属话题 ID
    categoryId: Optional[int] = None   # 新闻所属分类 ID


class SearchResponse(BaseModel):
    current: Optional[SearchResultItem] = None
    articles: List[SearchResultItem] = []


# ── 统一搜索（独立于 AI 助手）─────────────────────

class UnifiedSearchResult(BaseModel):
    news: List[SearchResultItem] = []
    posts: List[SearchResultItem] = []
    totalNews: int = 0
    totalPosts: int = 0
