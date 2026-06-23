from typing import Literal

from pydantic import BaseModel


class AITestData(BaseModel):
    module: str
    description: str


class AIGenerateRequest(BaseModel):
    input_text: str
    title_count: int = 3
    summary_type: Literal["extract", "generate"] = "generate"
    summary_style: str = "简明扼要"
    title_style: str = "客观新闻型"
    summary_length: Literal["short", "long", "both"] = "both"


class NewsElement(BaseModel):
    who: str
    what: str
    when: str
    where: str
    why: str
    how: str


class ConsistencyCheck(BaseModel):
    score: int
    risk_level: Literal["low", "medium", "high"]
    issues: list[str]
    suggestions: list[str]


class AIGenerateResponse(BaseModel):
    candidate_titles: list[str]
    summary_short: str
    summary_long: str
    summary_points: list[str]
    keywords: list[str]
    elements: NewsElement
    consistency: ConsistencyCheck


class AIGenerateRecordItem(BaseModel):
    id: int | str
    source: Literal["manual", "news"]
    source_news_id: int | str | None
    source_title: str
    title_count: int
    risk_level: Literal["low", "medium", "high"]
    created_at: str


class AIGenerateRecordDetail(BaseModel):
    id: int | str
    source: Literal["manual", "news"]
    source_news_id: int | str | None
    source_title: str
    input_text: str
    params: dict
    result: AIGenerateResponse
    created_at: str


class AIRecordListResponse(BaseModel):
    records: list[AIGenerateRecordItem]
    total: int


class DeleteAIRecordResult(BaseModel):
    success: bool
    message: str
