"""事件脉络话题润色 Schema。"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class PolishEventPoint(BaseModel):
    """单个事件点的简要信息，用于 LLM 润色。"""
    event_id: str = Field(description="事件点标识，兼容 int/str")
    event_title: str = Field(description="本地规则生成的事件标题")
    event_summary: Optional[str] = Field(default=None, description="本地规则生成的事件摘要")
    related_titles: list[str] = Field(default_factory=list, description="事件点关联的新闻标题（最多 3 条）")
    news_count: int = Field(default=1, description="该事件点包含的新闻数")


class PolishTimelineTopicRequest(BaseModel):
    """话题润色请求。"""
    topic_name: str = Field(description="本地规则生成的话题名称")
    category_name: Optional[str] = Field(default=None, description="话题主分类名称")
    keywords: list[str] = Field(default_factory=list, description="本地聚类提取的关键词")
    representative_titles: list[str] = Field(default_factory=list, description="话题代表新闻标题（最多 5 条）")
    summary: Optional[str] = Field(default=None, description="本地规则生成的话题摘要")
    event_points: list[PolishEventPoint] = Field(default_factory=list, description="话题内事件点列表")


class PolishTimelineTopicResponse(BaseModel):
    """话题润色响应。"""
    topic_name: str = Field(description="润色后的话题名称")
    summary: str = Field(description="润色后的话题摘要")
    keywords: list[str] = Field(default_factory=list, description="润色后的关键词")
    event_title_map: dict[str, str] = Field(default_factory=dict, description="event_id → 润色后事件标题")
    event_summary_map: dict[str, str] = Field(default_factory=dict, description="event_id → 润色后事件摘要")
    source: str = Field(default="fallback", description="llm | fallback")
    fallback_reason: Optional[str] = Field(default=None, description="fallback 原因")
