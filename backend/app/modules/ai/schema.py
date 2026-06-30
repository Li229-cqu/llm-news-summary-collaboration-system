from typing import List, Literal, Optional, Union

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
    source: Literal["manual", "news"] = "manual"
    source_news_id: Optional[Union[int, str]] = None
    source_title: str = ""


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
    issues: List[str]
    suggestions: List[str]


class AIGenerateResponse(BaseModel):
    candidate_titles: List[str]
    summary_short: str
    summary_long: str
    summary_points: List[str]
    keywords: List[str]
    elements: NewsElement
    consistency: ConsistencyCheck
    source: Optional[Literal["mock", "llm"]] = "mock"


class AIGenerateRecordItem(BaseModel):
    id: Union[int, str]
    source: Literal["manual", "news"]
    source_news_id: Optional[Union[int, str]]
    source_title: str
    title_count: int
    risk_level: Literal["low", "medium", "high"]
    ai_source: Literal["mock", "llm"] = "mock"
    created_at: str
    candidate_titles: list[str] = []
    summary_short: str = ""


class AIGenerateRecordDetail(BaseModel):
    id: Union[int, str]
    source: Literal["manual", "news"]
    source_news_id: Optional[Union[int, str]]
    source_title: str
    input_text: str
    params: dict
    result: AIGenerateResponse
    created_at: str


class AIRecordListResponse(BaseModel):
    records: List[AIGenerateRecordItem]
    total: int


class DeleteAIRecordResult(BaseModel):
    success: bool
    message: str


class FileUploadResponse(BaseModel):
    success: bool
    message: str
    content: str
    filename: str
