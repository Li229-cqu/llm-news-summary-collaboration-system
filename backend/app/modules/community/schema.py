"""社区模块 Schema。"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class CommunityPost(BaseModel):
    id: int
    user_id: int
    username: str = ""
    nickname: str = ""
    avatar: str = ""
    title: str
    content: str
    related_news_id: int | None = None
    related_news_title: str = ""
    topic_id: int | None = None
    like_count: int = 0
    comment_count: int = 0
    favorite_count: int = 0
    heat_score: int = 0
    status: int = 1
    create_time: str | datetime
    update_time: str | datetime
    tags: list[str] = Field(default_factory=list)

    # 前端兼容字段
    author: str = ""
    author_id: int = 0
    created_at: str | datetime | None = None
    updated_at: str | datetime | None = None
    likes: int = 0
    comments: int = 0
    views: int = 0
    liked: bool = False
    is_liked: bool = False
    is_favorited: bool = False
    is_blocked: bool = False
    hot: bool = False
    official: bool = False


class CreatePostRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="帖子标题")
    content: str = Field(..., min_length=1, max_length=5000, description="帖子内容")
    related_news_id: int | None = Field(default=None, description="关联新闻 ID")
    topic_id: int | None = Field(default=None, description="关联话题 ID")
    tags: list[str] = Field(default_factory=list, description="标签列表")


class PostListResponse(BaseModel):
    list: list[CommunityPost]
    total: int
    page: int
    page_size: int


class CommentItem(BaseModel):
    id: int
    post_id: int
    user_id: int
    username: str = ""
    nickname: str = ""
    avatar: str = ""
    parent_id: int | None = None
    content: str
    like_count: int = 0
    status: int = 1
    create_time: str | datetime
    media_json: Any | None = None
    reply_to_user_id: int | None = None
    reply_to_username: str = ""
    reply_to_nickname: str = ""
    reply_to_content: str = ""

    # 前端兼容字段
    author: str = ""
    author_id: int = 0
    created_at: str | datetime | None = None
    likes: int = 0
    is_liked: bool = False
    replies: list["CommentItem"] = Field(default_factory=list)


class CreateCommentRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=1000, description="评论内容")
    media_json: Any | None = Field(default=None, description="评论富媒体数据")


class CommentListResponse(BaseModel):
    list: list[CommentItem]
    total: int
    page: int
    page_size: int


class HotSearchItem(BaseModel):
    id: int
    keyword: str
    rank: int
    search_count: int
    trend: Literal["up", "down", "stable"] = "up"

    # 数据库兼容字段
    title: str = ""
    target_type: str = ""
    target_id: int = 0
    tag: str = ""
    update_time: str | datetime | None = None
    create_time: str | datetime | None = None


class AIHelperResponse(BaseModel):
    success: bool
    message: str
    answer: str | None = None


class LikeResponse(BaseModel):
    success: bool
    liked: bool
    count: int


class FavoriteResponse(BaseModel):
    success: bool
    favorited: bool
    count: int


class BlockResponse(BaseModel):
    success: bool
    blocked: bool
    user_id: int


class CommentsSummaryRequest(BaseModel):
    comments: list[str] = Field(default_factory=list, description="评论内容列表")


class CommentsSummaryResponse(BaseModel):
    summary: str
    sentiment: Literal["positive", "negative", "neutral"] = "neutral"
    keyword: str = ""
    keywords: list[str] = Field(default_factory=list, description="讨论热点关键词")
    key_points: list[str] = Field(default_factory=list, description="主要观点")
    source: Literal["llm", "fallback"] = "fallback"


CommentItem.model_rebuild()
