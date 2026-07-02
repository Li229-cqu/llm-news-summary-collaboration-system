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
    source_type: str = "manual"
    auto_generated_at: str | None = None


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
    event_type: Literal["policy", "reaction", "breakthrough", "outcome", "background", "other"] = "other"
    importance: int = Field(ge=1, le=5, default=3)
    event_detail: str = ""
    related_event_ids: list[int] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)


class TimelinePhase(BaseModel):
    name: str
    start_event_id: int
    end_event_id: int


class TimelineRelationship(BaseModel):
    from_id: int
    to_id: int
    type: Literal["causes", "follows", "parallel"] = "follows"


class TimelineMetadata(BaseModel):
    overview: str = ""
    key_figures: list[str] = Field(default_factory=list)
    phases: list[TimelinePhase] = Field(default_factory=list)


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
    generate_status: Literal["cached", "generated", "mock", "generating"] = "mock"
    schema_version: str = "1.0"
    overview: str = ""
    key_figures: list[str] = Field(default_factory=list)
    phases: list[TimelinePhase] = Field(default_factory=list)
    relationships: list[TimelineRelationship] = Field(default_factory=list)


class AutoClusterRequest(BaseModel):
    """自动聚类生成事件脉络话题请求。"""
    days: int = Field(default=30, ge=1, le=90, description="最近多少天新闻参与聚类")
    max_news: int = Field(default=1000, ge=20, le=5000, description="最多参与聚类新闻数")
    max_write_topics: int = Field(default=8, ge=1, le=20, description="最多生成话题数")
    use_llm_polish: bool = Field(default=True, description="是否启用 LLM 润色")
    dry_run: bool = Field(default=True, description="是否只预览不写库")
    confirm: bool = Field(default=False, description="正式发布确认开关，dry_run=false 时必须为 true")
