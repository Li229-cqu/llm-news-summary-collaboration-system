"""话题匹配请求/响应模型。"""
from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel


class MatchTopicRequest(BaseModel):
    text: str = ""
    keywords: List[str] = []
    elements_what: str = ""
    title: str = ""


class MatchTopicResponse(BaseModel):
    primary_topic: str = ""
    secondary_topics: List[str] = []
    confidence: float = 0.0
    matched_from: str = ""
