""""""

from __future__ import annotations


from typing import List, Literal, Optional, Union

from pydantic import BaseModel, Field


class TimelineTopic(BaseModel):
    topic_id: int
    topic_name: str
    keyword_list: list[str] = Field(default_factory=list)
    heat_score: int
    summary: str
    news_count: int


class TimelineNewsItem(BaseModel):
    id: int
    title: str
    content: str
    source: str
    publish_time: str
    summary: str | None = None
    category_id: int | None = None
    category_name: str | None = None
    topic_id: int | None = None


class TimelineNode(BaseModel):
    event_id: int
    event_time: str
    event_title: str
    event_summary: str
    source_news_id: int
    source_title: str
    source_name: str


class TimelineResponse(BaseModel):
    topic_id: int
    topic_name: str
    timeline: list[TimelineNode] = Field(default_factory=list)
    source: Literal["cache", "ai-service", "mock"] = "mock"


class TimelineNewsListResponse(BaseModel):
    topic_id: int
    topic_name: str
    news_items: list[TimelineNewsItem] = Field(default_factory=list)


class TimelineGenerateRequest(BaseModel):
    topic_id: int
    topic_name: str | None = None
    news_items: list[TimelineNewsItem] = Field(default_factory=list)


class TimelineGenerateResult(TimelineResponse):
    generated_at: str | None = None
    updated_at: str | None = None
    generate_status: Literal["cached", "generated", "mock"] = "mock"
