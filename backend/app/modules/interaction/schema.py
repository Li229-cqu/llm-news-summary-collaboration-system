"""新闻互动模块的请求与响应数据模型。"""

from typing import List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class InteractionTestData(BaseModel):
    """保留的模块连通性测试响应模型。"""

    module: str
    description: str


class InteractionResult(BaseModel):
    """新闻点赞、收藏等互动操作结果。"""

    target_id: int
    target_type: str
    action: str
    status: bool
    like_count: Optional[int] = None
    favorite_count: Optional[int] = None
    message: Optional[str] = None


class _CommentContentRequest(BaseModel):
    """评论文本请求的公共校验规则（归一化）。"""

    content: str

    @field_validator("content")
    @classmethod
    def normalize_content(cls, value: str) -> str:
        return value.strip() if value else ""


class CommentMediaJson(BaseModel):
    """评论中的媒体数据（图片、表情等）。"""

    images: Optional[List[str]] = None
    emojis: Optional[List[str]] = None


class CommentCreateRequest(_CommentContentRequest):
    """发布一级新闻评论的请求模型。"""

    media_json: Optional[CommentMediaJson] = None

    @model_validator(mode="after")
    def check_content_or_media(self) -> "CommentCreateRequest":
        content = (self.content or "").strip()
        has_images = bool(self.media_json and self.media_json.images)
        has_emojis = bool(self.media_json and self.media_json.emojis)
        if not content and not has_images and not has_emojis:
            raise ValueError("评论内容不能为空")
        return self


class CommentReplyRequest(_CommentContentRequest):
    """回复新闻评论的请求模型。"""

    media_json: Optional[CommentMediaJson] = None

    @model_validator(mode="after")
    def check_content_or_media(self) -> "CommentReplyRequest":
        content = (self.content or "").strip()
        has_images = bool(self.media_json and self.media_json.images)
        has_emojis = bool(self.media_json and self.media_json.emojis)
        if not content and not has_images and not has_emojis:
            raise ValueError("评论内容不能为空")
        return self


class CommentItem(BaseModel):
    """用于新闻评论列表展示的评论项。"""

    id: int
    news_id: int
    user_id: int
    username: str
    nickname: str
    avatar: str
    parent_id: Optional[int] = None
    content: str
    like_count: int
    status: int
    create_time: str
    is_liked: bool = False
    media_json: Optional[CommentMediaJson] = None
    replies: List["CommentItem"] = Field(default_factory=list)
    reply_to_user_id: Optional[int] = None
    reply_to_username: str = ""
    reply_to_nickname: str = ""
    reply_to_content: str = ""


class CommentListResponse(BaseModel):
    """评论列表响应数据。"""

    list: List[CommentItem] = Field(default_factory=list)
    total: int


class CommentLikeResult(BaseModel):
    """评论点赞操作结果。"""

    comment_id: int
    liked: bool
    like_count: int


class CommentMediaUploadResponse(BaseModel):
    """评论媒体上传响应。"""

    url: str
    filename: str
    size: int


CommentItem.model_rebuild()
