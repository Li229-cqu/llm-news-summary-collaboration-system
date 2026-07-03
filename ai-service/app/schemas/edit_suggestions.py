"""编辑建议请求/响应模型。"""
from __future__ import annotations
from typing import List, Optional, Any, Dict
from pydantic import BaseModel


class EditSuggestionItem(BaseModel):
    type: str = ""
    original: str = ""
    suggested: str = ""
    reason: str = ""
    detail: str = ""
    priority: str = "中"


class EditSuggestionsRequest(BaseModel):
    text: str = ""
    title: str = ""
    summary: str = ""
    keywords: List[str] = []
    topic: Optional[Dict[str, Any]] = None
    timeline: Optional[Dict[str, Any]] = None
    consistency: Optional[Dict[str, Any]] = None


class EditSuggestionsResponse(BaseModel):
    suggestions: List[EditSuggestionItem] = []
    overall_score: int = 0
    ready_to_publish: bool = False
