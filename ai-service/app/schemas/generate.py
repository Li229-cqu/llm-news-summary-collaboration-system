from __future__ import annotations
from typing import List, Literal

from pydantic import BaseModel


class GenerateRequest(BaseModel):
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


class GenerateResponse(BaseModel):
    candidate_titles: list[str]
    summary_short: str
    summary_long: str
    summary_points: list[str]
    keywords: list[str]
    elements: NewsElement
    consistency: ConsistencyCheck
    source: Literal["mock", "llm"] = "mock"
