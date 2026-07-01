from __future__ import annotations
from typing import List, Literal

from pydantic import BaseModel


class EvidenceItem(BaseModel):
    """单条证据信息。"""
    news_id: int
    source_name: str
    text: str
    position: str
    confidence: int
    similarity: float = 0.0


class SentenceEvidence(BaseModel):
    """摘要中一句话的证据信息。"""
    text: str
    evidence: List[EvidenceItem]
    has_evidence: bool
    risk_level: int = 0


class EvidenceChain(BaseModel):
    """完整的证据链数据。"""
    sentences: List[SentenceEvidence]
    evidence_coverage: float = 0.0
    overall_confidence: int = 0


class EvidenceRequest(BaseModel):
    """证据评估请求。"""
    summary_text: str
    original_text: str
    news_id: int = 0
    summary_type: str = "generate"


class EvidenceResponse(BaseModel):
    """证据评估响应。"""
    evidence_chain: EvidenceChain
    risk_level: Literal["low", "medium", "high"] = "low"
    risk_details: str = ""
    source: Literal["mock", "llm"] = "mock"
