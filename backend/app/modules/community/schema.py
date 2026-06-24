from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class CommunityPost(BaseModel):
    id: int
    title: str
    content: str
    author: str
    author_id: int
    created_at: datetime
    updated_at: datetime
    likes: int = 0
    comments: int = 0
    views: int = 0
    tags: List[str] = []


class CreatePostRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="帖子标题")
    content: str = Field(..., min_length=1, max_length=5000, description="帖子内容")
    tags: Optional[List[str]] = Field([], description="标签列表")


class PostListResponse(BaseModel):
    list: List[CommunityPost]
    total: int
    page: int
    page_size: int


class CommentItem(BaseModel):
    id: int
    post_id: int
    content: str
    author: str
    author_id: int
    created_at: datetime
    likes: int = 0


class CreateCommentRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=1000, description="评论内容")


class CommentListResponse(BaseModel):
    list: List[CommentItem]
    total: int
    page: int
    page_size: int


class HotSearchItem(BaseModel):
    id: int
    keyword: str
    rank: int
    search_count: int
    trend: str = "up"


class AIHelperResponse(BaseModel):
    success: bool
    message: str
    answer: Optional[str] = None


class LikeResponse(BaseModel):
    success: bool
    liked: bool
    count: int