"""社区模块 Schema。"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


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
    images: list[str] = Field(default_factory=list, description="帖子图片URL列表")
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
    images: list[str] = Field(default_factory=list, description="帖子图片URL列表", max_length=9)


class PostListResponse(BaseModel):
    list: list[CommunityPost]
    total: int
    page: int
    page_size: int


class CommentMediaJson(BaseModel):
    images: Optional[List[str]] = None
    emojis: Optional[List[str]] = None


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
    content: str = Field(..., max_length=1000, description="评论内容")
    media_json: Optional[CommentMediaJson] = None

    @field_validator("content")
    @classmethod
    def normalize_content(cls, value: str) -> str:
        return value.strip() if value else ""

    @model_validator(mode="after")
    def check_content_or_media(self) -> "CreateCommentRequest":
        content = (self.content or "").strip()
        has_images = bool(self.media_json and self.media_json.images)
        has_emojis = bool(self.media_json and self.media_json.emojis)
        if not content and not has_images and not has_emojis:
            raise ValueError("评论内容不能为空")
        return self


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
    view_count: int = 0


class TagCount(BaseModel):
    name: str
    count: int
    create_time: str | datetime | None = None


class PostMediaUploadResponse(BaseModel):
    url: str
    filename: str
    size: int


class AIHelperResponse(BaseModel):
    success: bool
    message: str
    answer: str | None = None


class LikeResponse(BaseModel):
    success: bool
    liked: bool
    count: int


class CommentLikeResult(BaseModel):
    comment_id: int
    liked: bool
    like_count: int


class FavoriteResponse(BaseModel):
    success: bool
    is_favorited: bool
    favorite_count: int


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


# ─── AI Session & Message ──────────────────────────────────────


class CommunityAiSessionCreate(BaseModel):
    question: str | None = Field(default=None, description="首条问题")
    source_type: str | None = Field(default=None, description="来源类型：post/news")
    source_post_id: int | None = Field(default=None, description="来源帖子ID")
    source_news_id: int | None = Field(default=None, description="来源新闻ID")


class CommunityAiMessageItem(BaseModel):
    id: int
    session_id: int
    user_id: int
    role: str  # user | assistant | system
    content: str
    status: str = "success"
    error_message: str | None = None
    created_at: str | datetime


class CommunityAiSessionItem(BaseModel):
    id: int
    title: str
    summary: str | None = None
    source_type: str | None = None
    source_post_id: int | None = None
    source_news_id: int | None = None
    status: str = "active"
    created_at: str | datetime
    updated_at: str | datetime
    last_message_at: str | datetime | None = None
    message_count: int = 0
    last_message_preview: str = ""


class CommunityAiSessionListResponse(BaseModel):
    list: list[CommunityAiSessionItem]
    total: int
    page: int
    page_size: int


class CommunityAiSessionDetailResponse(BaseModel):
    session: CommunityAiSessionItem
    messages: list[CommunityAiMessageItem]


class CommunityAiMessageCreate(BaseModel):
    question: str = Field(..., min_length=1, description="追问内容")


class CommunityAiMessageSendResponse(BaseModel):
    session: CommunityAiSessionItem
    user_message: CommunityAiMessageItem
    assistant_message: CommunityAiMessageItem


# ─── My Posts & Interactions ────────────────────────────────────


class MyCommunityPostItem(BaseModel):
    id: int
    title: str
    content: str
    summary: str = ""
    author_id: int = 0
    author: str = ""
    avatar: str = ""
    created_at: str | datetime | None = None
    updated_at: str | datetime | None = None
    tags: list[str] = Field(default_factory=list)
    images: list[str] = Field(default_factory=list, description="帖子图片URL列表")
    status: int = 1
    view_count: int = 0
    like_count: int = 0
    comment_count: int = 0
    favorite_count: int = 0
    likes: int = 0
    comments: int = 0
    views: int = 0
    related_news_id: int | None = None
    related_news_title: str = ""
    liked: bool = False
    favorited: bool = False


class MyCommunityPostListResponse(BaseModel):
    list: list[MyCommunityPostItem]
    total: int
    page: int
    page_size: int


class ReceivedInteractionItem(BaseModel):
    id: int
    actor_user_id: int
    actor_nickname: str = ""
    actor_avatar: str = ""
    action_type: str  # like | comment | favorite
    action_time: str | datetime | None = None
    target_post_id: int
    target_post_title: str = ""
    target_post_summary: str = ""
    target_post_created_at: str | datetime | None = None
    comment_id: int | None = None
    comment_content: str = ""
    related_news_id: int | None = None
    related_news_title: str = ""


class ReceivedInteractionListResponse(BaseModel):
    list: list[ReceivedInteractionItem]
    total: int
    page: int
    page_size: int
