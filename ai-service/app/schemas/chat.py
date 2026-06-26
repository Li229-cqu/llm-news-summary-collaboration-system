from __future__ import annotations
from typing import List, Optional

from pydantic import BaseModel


class ChatRequest(BaseModel):
    question: str
    context: Optional[str] = None


class ChatResponse(BaseModel):
    answer: str
    recommended_questions: list[str]
