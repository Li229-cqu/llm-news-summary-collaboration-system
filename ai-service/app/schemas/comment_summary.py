from __future__ import annotations
from typing import List, Literal

from pydantic import BaseModel, Field


class CommentSummaryRequest(BaseModel):
    comments: List[str] = Field(..., description="评论内容列表")


class CommentSummaryResponse(BaseModel):
    summary: str = Field(..., description="评论摘要")
    sentiment: Literal["positive", "negative", "neutral"] = Field("neutral", description="情感倾向")
    keywords: List[str] = Field(default_factory=list, description="讨论热点关键词")
    key_points: List[str] = Field(default_factory=list, description="主要观点")
    source: Literal["llm", "fallback"] = Field("fallback", description="数据来源")