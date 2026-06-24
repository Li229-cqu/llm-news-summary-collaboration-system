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


class AIGenerateResponse(BaseModel):
    candidate_titles: list[str]
    summary_short: str
    summary_long: str
    summary_points: list[str]
