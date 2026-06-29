"""新闻互动模块的请求与响应数据模型。"""

from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


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
    """评论文本请求的公共校验规则。"""

    content: str

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str) -> str:
        normalized_content = value.strip()
        if not normalized_content:
            raise ValueError("评论内容不能为空")
        return normalized_content


class CommentMediaJson(BaseModel):
    """评论中的媒体数据（图片、表情等）。"""

    images: Optional[List[str]] = None
    emojis: Optional[List[str]] = None


class CommentCreateRequest(_CommentContentRequest):
    """发布一级新闻评论的请求模型。"""

    media_json: Optional[CommentMediaJson] = None


class CommentReplyRequest(_CommentContentRequest):
    """回复新闻评论的请求模型。"""

    media_json: Optional[CommentMediaJson] = None


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
