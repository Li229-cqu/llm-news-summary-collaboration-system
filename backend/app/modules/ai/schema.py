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
    issues: List[str]
    suggestions: List[str]


class EvidenceItem(BaseModel):
    news_id: int = 0
    source_name: str = ""
    text: str = ""
    position: str = ""
    confidence: int = 0
    similarity: float = 0.0


class SentenceEvidence(BaseModel):
    text: str = ""
    evidence: List[EvidenceItem] = []
    has_evidence: bool = False
    risk_level: int = 0


class EvidenceChain(BaseModel):
    sentences: List[SentenceEvidence] = []
    evidence_coverage: float = 0.0


class AIGenerateResponse(BaseModel):
    candidate_titles: List[str]
    summary_short: str
    summary_long: str
    summary_points: List[str]
    keywords: List[str]
    elements: NewsElement
    consistency: ConsistencyCheck
    source: Optional[Literal["mock", "llm"]] = "mock"
    evidence_chain: Optional[EvidenceChain] = None
    evidence_chain_short: Optional[EvidenceChain] = None
    evidence_chain_long: Optional[EvidenceChain] = None
    risk_level: Optional[Literal["low", "medium", "high"]] = None
    risk_details: Optional[str] = None
    evidence_coverage: Optional[float] = None


class AIGenerateRecordItem(BaseModel):
    id: Union[int, str]
    source: Literal["manual", "news"]
    source_news_id: Optional[Union[int, str]]
    source_title: str
    title_count: int
    risk_level: Literal["low", "medium", "high"]
    ai_source: Literal["mock", "llm", "demo"] = "mock"
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
