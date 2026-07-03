"""时间线适配请求/响应模型。"""
from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel


class JudgeTimelineRequest(BaseModel):
    text: str = ""
    when: str = ""
    title: str = ""


class JudgeTimelineResponse(BaseModel):
    is_timely: bool = True
    recommended_position: str = ""
    time_sensitivity: str = ""
    related_events: List[str] = []
