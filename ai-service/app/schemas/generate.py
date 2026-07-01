from __future__ import annotations
from typing import List, Literal, Optional

from pydantic import BaseModel

from app.schemas.evidence import EvidenceChain


class GenerateRequest(BaseModel):
    input_text: str
    title_count: int = 3
    summary_type: Literal["extract", "generate"] = "generate"
    summary_style: str = "简明扼要"
    title_style: str = "客观新闻型"
    summary_length: Literal["short", "long", "both"] = "both"
    skip_evidence: bool = False


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
    evidence_chain: Optional[EvidenceChain] = None
    evidence_chain_short: Optional[EvidenceChain] = None
    evidence_chain_long: Optional[EvidenceChain] = None
    risk_level: Optional[Literal["low", "medium", "high"]] = None
    risk_details: Optional[str] = None
    evidence_coverage: Optional[float] = None
